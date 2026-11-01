"""Local trip companion with deterministic check-ins and explicit SOS state.

Trip data is process-local and is lost when the process exits. No scheduler,
GPS provider, external notification service, or durable storage is integrated.
"""

from __future__ import annotations

import copy
import datetime as dt
import math
import re
import uuid
from typing import Any, Dict, Optional

from src.tools.emergency_escalator import escalate_emergency

PANIC_KEYWORDS = [
    "ayuda",
    "socorro",
    "me siguen",
    "desvío",
    "bloqueado",
    "auxilio",
    "peligro",
    "no es la ruta",
    "no me deja",
    "tengo miedo",
    "miedo",
    "desaparecido",
]

_TRIPS: Dict[str, Dict[str, Any]] = {}


def _now() -> dt.datetime:
    """Return the local wall clock; patched in tests to avoid real-time waits."""
    return dt.datetime.now()


def _normalize_datetime(value: dt.datetime) -> dt.datetime:
    if not isinstance(value, dt.datetime):
        raise TypeError("El tiempo debe ser un datetime.")
    if value.tzinfo is not None and value.utcoffset() is not None:
        return value.astimezone().replace(tzinfo=None)
    return value


def _validate_trip_id(trip_id: str) -> str:
    if not isinstance(trip_id, str):
        raise TypeError("trip_id debe ser una cadena de texto.")
    cleaned = trip_id.strip()
    if not cleaned:
        raise ValueError("trip_id no puede estar vacío.")
    return cleaned


def _validate_plate(plate: str) -> str:
    """Normalize and validate a vehicle plate."""
    if not isinstance(plate, str):
        raise TypeError("La placa debe ser una cadena de texto.")

    clean_plate = re.sub(r"[^A-Za-z0-9]", "", plate).upper()
    if not clean_plate:
        raise ValueError("La placa es obligatoria.")
    if len(clean_plate) < 3 or len(clean_plate) > 12:
        raise ValueError("La placa debe tener entre 3 y 12 caracteres.")
    if not re.search(r"[A-Za-z]", clean_plate) or not re.search(r"\d", clean_plate):
        raise ValueError("La placa debe incluir letras y números.")
    return clean_plate


def _validate_text(value: Optional[str], field_name: str, optional: bool = False) -> Optional[str]:
    if value is None:
        if optional:
            return None
        raise ValueError(f"{field_name} es obligatorio.")
    if not isinstance(value, str):
        raise TypeError(f"{field_name} debe ser un texto.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} no puede estar vacío.")
    return cleaned


def _trip_payload(trip: Dict[str, Any]) -> Dict[str, Any]:
    """Return a detached, serializable view of the current trip state."""
    return {
        "status": trip["status"],
        "trip_id": trip["trip_id"],
        "vehicle_plate": trip["vehicle_plate"],
        "destination": trip["destination"],
        "origin": trip["origin"],
        "checkin_interval_minutes": trip["checkin_interval_minutes"],
        "started_at": trip["started_at"],
        "last_checkin_at": trip["last_checkin_at"],
        "next_checkin_scheduled": trip["next_checkin_scheduled"],
        "monitoring_active": trip["monitoring_active"],
        "checkin_count": trip["checkin_count"],
        "coordinates": copy.deepcopy(trip["coordinates"]),
        "alerts": copy.deepcopy(trip["alerts"]),
        "completed_at": trip.get("completed_at"),
        "completion_reason": trip.get("completion_reason"),
    }


def _trip_error(trip_id: str, error: str) -> Dict[str, Any]:
    return {"status": "error", "trip_id": trip_id, "error": error}


def register_trip(
    plate: str,
    destination: str,
    origin: Optional[str] = None,
    checkin_interval_minutes: int = 10,
) -> Dict[str, Any]:
    """Register a trip and return its initial state.

    The opaque trip identifier deliberately contains no plate or location data.
    """
    clean_plate = _validate_plate(plate)
    clean_destination = _validate_text(destination, "destination")
    clean_origin = _validate_text(origin, "origin", optional=True)

    if not isinstance(checkin_interval_minutes, int) or isinstance(checkin_interval_minutes, bool):
        raise TypeError("checkin_interval_minutes debe ser un entero.")
    if checkin_interval_minutes <= 0 or checkin_interval_minutes > 1440:
        raise ValueError("checkin_interval_minutes debe estar entre 1 y 1440 minutos.")

    started_at = _now()
    trip_id = f"TRIP-{uuid.uuid4().hex}"
    trip = {
        "status": "active",
        "trip_id": trip_id,
        "vehicle_plate": clean_plate,
        "destination": clean_destination,
        "origin": clean_origin,
        "checkin_interval_minutes": checkin_interval_minutes,
        "started_at": started_at.isoformat(),
        "last_checkin_at": None,
        "next_checkin_scheduled": (
            started_at + dt.timedelta(minutes=checkin_interval_minutes)
        ).isoformat(),
        "monitoring_active": True,
        "checkin_count": 0,
        "coordinates": None,
        "alerts": [],
    }
    _TRIPS[trip_id] = trip
    return _trip_payload(trip)


def get_trip_status(trip_id: str) -> Dict[str, Any]:
    """Return the current state of a registered trip."""
    clean_trip_id = _validate_trip_id(trip_id)
    trip = _TRIPS.get(clean_trip_id)
    if trip is None:
        return _trip_error(clean_trip_id, "trip_not_found")
    return _trip_payload(trip)


def confirm_checkin(trip_id: str, timestamp: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """Record a user check-in and schedule the next one from its timestamp."""
    clean_trip_id = _validate_trip_id(trip_id)
    trip = _TRIPS.get(clean_trip_id)
    if trip is None:
        return _trip_error(clean_trip_id, "trip_not_found")
    if trip["status"] == "completed":
        return _trip_error(clean_trip_id, "trip_already_finished")
    if trip["status"] == "emergency_pending":
        return _trip_error(clean_trip_id, "trip_emergency_pending")

    now = _normalize_datetime(timestamp if timestamp is not None else _now())
    trip["last_checkin_at"] = now.isoformat()
    trip["checkin_count"] += 1
    trip["next_checkin_scheduled"] = (
        now + dt.timedelta(minutes=trip["checkin_interval_minutes"])
    ).isoformat()
    trip["status"] = "active"
    trip["monitoring_active"] = True

    for alert in reversed(trip["alerts"]):
        if alert["type"] == "MISSED_CHECKIN" and alert["status"] == "pending":
            alert["status"] = "resolved"
            alert["resolved_at"] = now.isoformat()
            break

    return {
        "status": "success",
        "trip_id": clean_trip_id,
        "current_status": trip["status"],
        "last_checkin_at": trip["last_checkin_at"],
        "next_checkin_scheduled": trip["next_checkin_scheduled"],
        "checkin_count": trip["checkin_count"],
    }


def detect_overdue_checkins(now: Optional[dt.datetime] = None) -> list[str]:
    """Return IDs due for a check-in and record one non-emergency alert per due period."""
    reference = _normalize_datetime(now if now is not None else _now())
    due: list[str] = []
    for trip_id, trip in _TRIPS.items():
        if trip["status"] == "active":
            scheduled = dt.datetime.fromisoformat(trip["next_checkin_scheduled"])
            if scheduled <= reference:
                trip["status"] = "checkin_pending"
                trip["alerts"].append(
                    {
                        "alert_id": f"ALERT-{uuid.uuid4().hex}",
                        "trip_id": trip_id,
                        "type": "MISSED_CHECKIN",
                        "status": "pending",
                        "severity": "UNCONFIRMED",
                        "created_at": reference.isoformat(),
                        "notification_status": "not_sent",
                        "emergency_confirmed": False,
                        "message": (
                            "No se recibió la confirmación del viaje a tiempo. "
                            "Se requiere verificar el bienestar del pasajero."
                        ),
                    }
                )
        if trip["status"] == "checkin_pending":
            due.append(trip_id)
    return due


def finalize_trip(trip_id: str, reason: str = "completed") -> Dict[str, Any]:
    """Confirm arrival and permanently stop check-in monitoring for the trip."""
    clean_trip_id = _validate_trip_id(trip_id)
    clean_reason = _validate_text(reason, "reason")
    trip = _TRIPS.get(clean_trip_id)
    if trip is None:
        return _trip_error(clean_trip_id, "trip_not_found")
    if trip["status"] == "completed":
        return _trip_error(clean_trip_id, "trip_already_finished")

    completed_at = _now()
    trip["status"] = "completed"
    trip["monitoring_active"] = False
    trip["completed_at"] = completed_at.isoformat()
    trip["completion_reason"] = clean_reason
    for alert in trip["alerts"]:
        if alert["type"] == "MISSED_CHECKIN" and alert["status"] == "pending":
            alert["status"] = "resolved"
            alert["resolved_at"] = trip["completed_at"]
            alert["resolution"] = "trip_completed"
    return {
        "status": "completed",
        "trip_id": clean_trip_id,
        "monitoring_active": False,
        "completed_at": trip["completed_at"],
        "completion_reason": clean_reason,
    }


def record_trip_coordinates(
    trip_id: str,
    latitude: float,
    longitude: float,
    source: str,
    timestamp: Optional[dt.datetime] = None,
) -> Dict[str, Any]:
    """Record supplied coordinates with provenance; this function never obtains GPS."""
    clean_trip_id = _validate_trip_id(trip_id)
    trip = _TRIPS.get(clean_trip_id)
    if trip is None:
        return _trip_error(clean_trip_id, "trip_not_found")
    if trip["status"] == "completed":
        return _trip_error(clean_trip_id, "trip_already_finished")

    if isinstance(latitude, bool) or not isinstance(latitude, (int, float)):
        raise TypeError("latitude debe ser un número.")
    if isinstance(longitude, bool) or not isinstance(longitude, (int, float)):
        raise TypeError("longitude debe ser un número.")
    if not -90 <= latitude <= 90 or not math.isfinite(latitude):
        raise ValueError("latitude debe estar entre -90 y 90.")
    if not -180 <= longitude <= 180 or not math.isfinite(longitude):
        raise ValueError("longitude debe estar entre -180 y 180.")
    clean_source = _validate_text(source, "source")
    recorded_at = _normalize_datetime(timestamp if timestamp is not None else _now())

    trip["coordinates"] = {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "source": clean_source,
        "recorded_at": recorded_at.isoformat(),
    }
    return {
        "status": "success",
        "trip_id": clean_trip_id,
        "coordinates": copy.deepcopy(trip["coordinates"]),
    }


def get_trip_coordinates(trip_id: str) -> Dict[str, Any]:
    """Return stored coordinates and their source, or None when none were supplied."""
    clean_trip_id = _validate_trip_id(trip_id)
    trip = _TRIPS.get(clean_trip_id)
    if trip is None:
        return _trip_error(clean_trip_id, "trip_not_found")
    return {
        "status": "success",
        "trip_id": clean_trip_id,
        "coordinates": copy.deepcopy(trip["coordinates"]),
    }


def activate_trip_sos(
    trip_id: str,
    incident_type: str,
    evidence_payload: Optional[Dict[str, Any]] = None,
    contacts: Optional[list[str]] = None,
    severity: Optional[str] = None,
) -> Dict[str, Any]:
    """Manually prepare an SOS and move a non-finalized trip to emergency_pending."""
    clean_trip_id = _validate_trip_id(trip_id)
    trip = _TRIPS.get(clean_trip_id)
    if trip is None:
        return _trip_error(clean_trip_id, "trip_not_found")
    if trip["status"] == "completed":
        return _trip_error(clean_trip_id, "trip_already_finished")
    if trip["status"] == "emergency_pending":
        return _trip_error(clean_trip_id, "trip_emergency_already_pending")
    if evidence_payload is not None and not isinstance(evidence_payload, dict):
        raise TypeError("evidence_payload debe ser un diccionario.")

    evidence = copy.deepcopy(evidence_payload or {})
    if "coordinates" in evidence and trip["coordinates"] is None:
        raise ValueError(
            "Registre las coordenadas del viaje con su fuente antes de incluirlas en un SOS."
        )
    evidence["trip_id"] = clean_trip_id
    evidence["vehicle_plate"] = trip["vehicle_plate"]
    evidence["destination"] = trip["destination"]
    if trip["coordinates"] is not None:
        evidence["coordinates"] = copy.deepcopy(trip["coordinates"])

    result = escalate_emergency(
        incident_type=incident_type,
        evidence_payload=evidence,
        contacts=contacts,
        severity=severity,
    )
    emergency = result["incident_report"]
    trip["status"] = "emergency_pending"
    trip["monitoring_active"] = False
    trip["alerts"].append(
        {
            "alert_id": result["alert_id"],
            "trip_id": clean_trip_id,
            "type": "SOS",
            "status": "prepared",
            "severity": result["severity"],
            "created_at": emergency["timestamp"],
            "notification_status": result["notification_status"],
            "emergency_confirmed": True,
        }
    )
    result["trip_id"] = clean_trip_id
    result["trip_status"] = trip["status"]
    return result


def evaluate_trip_audio_response(
    transcript: str,
    expected_safe_word: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate an audio/text response without automatically dispatching an SOS."""
    if not isinstance(transcript, str):
        raise TypeError("transcript debe ser una cadena de texto.")
    if expected_safe_word is not None and not isinstance(expected_safe_word, str):
        raise TypeError("expected_safe_word debe ser una cadena de texto o None.")
    transcript_clean = transcript.strip().lower()
    if not transcript_clean:
        raise ValueError("transcript no puede estar vacío.")

    panic_detected = any(keyword in transcript_clean for keyword in PANIC_KEYWORDS)
    expected_word = (
        expected_safe_word.strip().lower()
        if expected_safe_word is not None and expected_safe_word.strip()
        else None
    )
    safe_word_present = bool(expected_word and expected_word in transcript_clean)

    if panic_detected:
        return {
            "status": "alert",
            "is_safe": False,
            "escalation_required": True,
            "reason": "Se detectaron palabras de alerta o auxilio en la comunicación del usuario.",
        }

    if expected_word and not safe_word_present:
        return {
            "status": "checkin_pending",
            "is_safe": False,
            "escalation_required": False,
            "reason": "La respuesta no confirma la palabra segura esperada.",
        }

    return {
        "status": "normal",
        "is_safe": True,
        "escalation_required": False,
        "reason": "Respuesta dentro de los parámetros esperados de normalidad.",
    }
