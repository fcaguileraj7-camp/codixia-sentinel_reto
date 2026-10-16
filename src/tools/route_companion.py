"""Módulo de acompañamiento físico para viajes.

Mantiene un registro en memoria de viajes activos para soportar chequeos,
validación de estados y escalada preventiva sin requerir base de datos.
"""

from __future__ import annotations

import datetime as dt
import re
import uuid
from typing import Any, Dict, Optional

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


def _validate_plate(plate: str) -> str:
    """Normaliza y valida una placa de vehículo."""
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


def _validate_text(value: Optional[str], field_name: str) -> Optional[str]:
    """Valida textos obligatorios para destino/origen."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} debe ser un texto.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} no puede estar vacío.")
    return cleaned


def _trip_payload(trip: Dict[str, Any]) -> Dict[str, Any]:
    """Crea una vista serializable del viaje."""
    return {
        "status": trip.get("status", "active"),
        "trip_id": trip["trip_id"],
        "vehicle_plate": trip["vehicle_plate"],
        "destination": trip["destination"],
        "origin": trip.get("origin"),
        "checkin_interval_minutes": trip["checkin_interval_minutes"],
        "started_at": trip["started_at"],
        "last_checkin_at": trip.get("last_checkin_at"),
        "next_checkin_scheduled": trip.get("next_checkin_scheduled"),
        "monitoring_active": bool(trip.get("monitoring_active", False)),
        "checkin_count": trip.get("checkin_count", 0),
    }


def register_trip(
    plate: str,
    destination: str,
    origin: Optional[str] = None,
    checkin_interval_minutes: int = 10,
) -> Dict[str, Any]:
    """Registra un nuevo viaje activo y devuelve el estado inicial."""
    clean_plate = _validate_plate(plate)
    clean_destination = _validate_text(destination, "destination")
    clean_origin = _validate_text(origin, "origin") if origin is not None else None

    if not isinstance(checkin_interval_minutes, int) or isinstance(checkin_interval_minutes, bool):
        raise TypeError("checkin_interval_minutes debe ser un entero.")
    if checkin_interval_minutes <= 0 or checkin_interval_minutes > 1440:
        raise ValueError("checkin_interval_minutes debe estar entre 1 y 1440 minutos.")

    started_at = dt.datetime.now()
    trip_id = f"TRIP-{clean_plate}-{int(started_at.timestamp())}-{uuid.uuid4().hex[:8]}"
    trip = {
        "status": "active",
        "trip_id": trip_id,
        "vehicle_plate": clean_plate,
        "destination": clean_destination,
        "origin": clean_origin,
        "checkin_interval_minutes": checkin_interval_minutes,
        "started_at": started_at.isoformat(),
        "last_checkin_at": None,
        "next_checkin_scheduled": (started_at + dt.timedelta(minutes=checkin_interval_minutes)).isoformat(),
        "monitoring_active": True,
        "checkin_count": 0,
    }
    _TRIPS[trip_id] = trip
    return _trip_payload(trip)


def get_trip_status(trip_id: str) -> Dict[str, Any]:
    """Devuelve el estado actual del viaje registrado."""
    trip = _TRIPS.get(trip_id)
    if trip is None:
        return {"status": "error", "trip_id": trip_id, "error": "trip_not_found"}
    return _trip_payload(trip)


def confirm_checkin(trip_id: str, timestamp: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """Registra un check-in del viaje y actualiza el próximo vencimiento."""
    trip = _TRIPS.get(trip_id)
    if trip is None:
        return {"status": "error", "trip_id": trip_id, "error": "trip_not_found"}
    if trip.get("status") == "completed":
        return {"status": "error", "trip_id": trip_id, "error": "trip_already_finished"}

    now = timestamp or dt.datetime.now()
    trip["last_checkin_at"] = now.isoformat()
    trip["checkin_count"] = int(trip.get("checkin_count", 0)) + 1
    trip["next_checkin_scheduled"] = (now + dt.timedelta(minutes=trip["checkin_interval_minutes"])).isoformat()
    trip["status"] = "active"
    trip["monitoring_active"] = True
    return {
        "status": "success",
        "trip_id": trip_id,
        "current_status": trip["status"],
        "last_checkin_at": trip["last_checkin_at"],
        "next_checkin_scheduled": trip["next_checkin_scheduled"],
        "checkin_count": trip["checkin_count"],
    }


def detect_overdue_checkins(now: Optional[dt.datetime] = None) -> list[str]:
    """Lista los viajes activos con check-ins vencidos."""
    reference = now or dt.datetime.now()
    due = []
    for trip_id, trip in _TRIPS.items():
        if trip.get("status") != "active":
            continue
        scheduled = trip.get("next_checkin_scheduled")
        if scheduled is None:
            continue
        if dt.datetime.fromisoformat(scheduled) <= reference:
            due.append(trip_id)
    return due


def finalize_trip(trip_id: str, reason: str = "completed") -> Dict[str, Any]:
    """Finaliza el viaje y desactiva el monitoreo."""
    trip = _TRIPS.get(trip_id)
    if trip is None:
        return {"status": "error", "trip_id": trip_id, "error": "trip_not_found"}
    if trip.get("status") == "completed":
        return {"status": "error", "trip_id": trip_id, "error": "trip_already_finished"}

    completed_at = dt.datetime.now()
    trip["status"] = "completed"
    trip["monitoring_active"] = False
    trip["completed_at"] = completed_at.isoformat()
    trip["completion_reason"] = reason
    return {
        "status": "completed",
        "trip_id": trip_id,
        "monitoring_active": False,
        "completed_at": trip["completed_at"],
        "completion_reason": reason,
    }


def evaluate_trip_audio_response(transcript: str, expected_safe_word: Optional[str] = None) -> Dict[str, Any]:
    """Evalúa la respuesta de audio o texto del usuario durante el viaje."""
    if not isinstance(transcript, str):
        raise TypeError("transcript debe ser una cadena de texto.")
    transcript_clean = transcript.strip().lower()
    if not transcript_clean:
        raise ValueError("transcript no puede estar vacío.")

    panic_detected = any(keyword in transcript_clean for keyword in PANIC_KEYWORDS)
    expected_word = expected_safe_word.strip().lower() if isinstance(expected_safe_word, str) and expected_safe_word.strip() else None
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
