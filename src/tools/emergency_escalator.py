"""Prepare local SOS records without claiming external delivery.

No police, contact, telephony, GPS, or notification integration is configured.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import uuid
from typing import Any, Dict, Iterable, List, Optional

_VALID_INCIDENT_TYPES = {
    "PHYSICAL_RISK",
    "DIGITAL_FRAUD",
    "EXTORTION",
    "THREAT",
    "SUSPICIOUS_ACTIVITY",
}

_VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}


def _now() -> dt.datetime:
    """Return the local wall clock; patched in tests for deterministic records."""
    return dt.datetime.now()


def _normalize_incident_type(incident_type: str) -> str:
    """Normalize and validate supported incident types."""
    if not isinstance(incident_type, str):
        raise TypeError("incident_type debe ser una cadena de texto.")

    normalized = incident_type.strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "PHISHING": "DIGITAL_FRAUD",
        "SCAM": "DIGITAL_FRAUD",
        "FRAUD": "DIGITAL_FRAUD",
        "PHYSICAL": "PHYSICAL_RISK",
        "ROUTE_RISK": "PHYSICAL_RISK",
        "SECURITY_THREAT": "THREAT",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in _VALID_INCIDENT_TYPES:
        allowed = ", ".join(sorted(_VALID_INCIDENT_TYPES))
        raise ValueError(f"incident_type inválido. Tipos válidos: {allowed}")
    return normalized


def _normalize_severity(severity: Optional[str]) -> Optional[str]:
    if severity is None:
        return None
    if not isinstance(severity, str):
        raise TypeError("severity debe ser una cadena de texto o None.")
    normalized = severity.strip().upper()
    aliases = {"CRITICO": "CRITICAL", "ALTO": "HIGH", "MEDIO": "MEDIUM", "BAJO": "LOW"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in _VALID_SEVERITIES:
        allowed = ", ".join(sorted(_VALID_SEVERITIES))
        raise ValueError(f"severity inválida. Valores válidos: {allowed}")
    return normalized


def _normalize_contacts(contacts: Optional[Iterable[str]]) -> List[str]:
    """Validate supplied contact labels without retaining or claiming delivery."""
    if contacts is None:
        return []
    if not isinstance(contacts, (list, tuple, set)):
        raise TypeError("contacts debe ser una lista de texto o None.")

    normalized: List[str] = []
    for contact in contacts:
        if not isinstance(contact, str):
            raise TypeError("Cada contacto debe ser una cadena de texto.")
        value = contact.strip()
        if value:
            normalized.append(value)
    return normalized


def _normalize_evidence(evidence_payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Copy JSON-compatible evidence and reject values that cannot be audited."""
    if evidence_payload is None:
        return {}
    if not isinstance(evidence_payload, dict):
        raise TypeError("evidence_payload debe ser un diccionario.")
    normalized = {str(key): value for key, value in evidence_payload.items()}
    try:
        normalized_json = json.loads(
            json.dumps(normalized, sort_keys=True, ensure_ascii=False, allow_nan=False)
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("evidence_payload debe contener únicamente datos JSON válidos.") from exc

    coordinates = normalized_json.get("coordinates")
    if coordinates is not None:
        if not isinstance(coordinates, dict):
            raise ValueError("coordinates debe ser un objeto con latitud, longitud y fuente.")
        latitude = coordinates.get("latitude")
        longitude = coordinates.get("longitude")
        source = coordinates.get("source")
        if (
            isinstance(latitude, bool)
            or not isinstance(latitude, (int, float))
            or not -90 <= latitude <= 90
            or not math.isfinite(latitude)
        ):
            raise ValueError("coordinates.latitude debe estar entre -90 y 90.")
        if (
            isinstance(longitude, bool)
            or not isinstance(longitude, (int, float))
            or not -180 <= longitude <= 180
            or not math.isfinite(longitude)
        ):
            raise ValueError("coordinates.longitude debe estar entre -180 y 180.")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("coordinates.source debe indicar la procedencia.")
        coordinates["latitude"] = float(latitude)
        coordinates["longitude"] = float(longitude)
        coordinates["source"] = source.strip()
    return normalized_json


def _classify_severity(incident_type: str, evidence_payload: Dict[str, Any]) -> str:
    """Classify severity deterministically when the caller does not specify it."""
    decision = evidence_payload.get("decision", {})
    if isinstance(decision, dict):
        risk_level = str(decision.get("risk_level", "")).upper()
        if risk_level in {"CRITICAL", "CRITICO"}:
            return "CRITICAL"

    if incident_type in {"PHYSICAL_RISK", "EXTORTION", "THREAT"}:
        return "CRITICAL"
    if incident_type in {"DIGITAL_FRAUD", "SUSPICIOUS_ACTIVITY"}:
        return "HIGH"
    return "MEDIUM"


def escalate_emergency(
    incident_type: str,
    evidence_payload: Optional[Dict[str, Any]] = None,
    contacts: Optional[List[str]] = None,
    *,
    severity: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a unique local SOS record; this does not notify any contact.

    The legacy ``status`` value ``escalated`` is retained for compatibility and
    means only that the local record was prepared. Use ``notification_status``
    to determine whether an external delivery actually occurred.
    """
    normalized_type = _normalize_incident_type(incident_type)
    normalized_evidence = _normalize_evidence(evidence_payload)
    requested_contacts = _normalize_contacts(contacts)
    normalized_severity = _normalize_severity(severity)
    alert_id = f"ALERT-{uuid.uuid4().hex}"
    report_id = f"SOS-{uuid.uuid4().hex}"
    now = _now()
    effective_severity = normalized_severity or _classify_severity(
        normalized_type, normalized_evidence
    )

    vehicle = normalized_evidence.get("vehicle")
    if isinstance(vehicle, dict):
        plate = (
            normalized_evidence.get("vehicle_plate")
            or normalized_evidence.get("plate")
            or vehicle.get("plate")
        )
    else:
        plate = normalized_evidence.get("vehicle_plate") or normalized_evidence.get("plate")
    destination = normalized_evidence.get("destination")
    last_known_location = (
        normalized_evidence.get("last_known_location")
        or normalized_evidence.get("location")
    )
    coordinates = normalized_evidence.get("coordinates")

    if normalized_type == "PHYSICAL_RISK":
        dispatch_message = (
            "🚨 ALERTA DE EMERGENCIA: Se preparó localmente una escalada para un riesgo físico "
            f"durante el trayecto. Placa: {plate or 'No registrada'}. "
            f"Destino: {destination or 'No informado'}. "
            f"Última ubicación conocida: {last_known_location or 'No disponible'}."
        )
        script = (
            f"Aviso de seguridad: la unidad con placa {plate or 'sin placa registrada'} "
            "requiere atención preventiva; esta alerta está preparada localmente y "
            "no se ha notificado a servicios externos."
        )
    else:
        dispatch_message = (
            "⚠️ ALERTA DE SEGURIDAD: Se preparó localmente un expediente para revisión y "
            "escalamiento autorizado. No se enviaron notificaciones externas."
        )
        script = (
            "Mensaje disuasorio preparado localmente. No se ha contactado a terceros."
        )

    incident_report = {
        "report_id": report_id,
        "alert_id": alert_id,
        "timestamp": now.isoformat(),
        "type": normalized_type,
        "evidence": normalized_evidence,
        "police_complaint_ready": False,
        "status": "PREPARED",
        "severity": effective_severity,
        "notification_status": "not_sent",
    }

    return {
        "status": "escalated",
        "alert_status": "PREPARED",
        "notification_status": "not_sent",
        "contacts_notified": [],
        "contacts_requested_count": len(requested_contacts),
        "alert_id": alert_id,
        "incident_type": normalized_type,
        "severity": effective_severity,
        "deterrent_audio_script": script,
        "alert_message": dispatch_message,
        "incident_report": incident_report,
        "vehicle_plate": plate,
        "destination": destination,
        "last_known_location": last_known_location,
        "coordinates": coordinates,
    }
