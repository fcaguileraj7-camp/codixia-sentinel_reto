"""Escalado local de emergencias guardianas.

No se ejecutan acciones reales de llamadas, GPS ni notificaciones externas.
Se prepara un expediente local seguro para su uso futuro con integración
autorizada.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import uuid
from typing import Any, Dict, Iterable, List, Optional

_VALID_INCIDENT_TYPES = {
    "PHYSICAL_RISK",
    "DIGITAL_FRAUD",
    "EXTORTION",
    "THREAT",
    "SUSPICIOUS_ACTIVITY",
}

_SEEN_ALERTS: set[str] = set()


def _normalize_incident_type(incident_type: str) -> str:
    """Normaliza y valida los tipos soportados."""
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


def _normalize_contacts(contacts: Optional[Iterable[str]]) -> List[str]:
    """Normaliza la lista de contactos de confianza."""
    if contacts is None:
        return []
    if not isinstance(contacts, (list, tuple, set)):
        raise TypeError("contacts debe ser una lista de texto o None.")

    normalized: List[str] = []
    for contact in contacts:
        if contact is None:
            continue
        value = str(contact).strip()
        if value:
            normalized.append(value)
    return normalized


def _normalize_evidence(evidence_payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Normaliza la evidencia y la convierte en un diccionario seguro."""
    if evidence_payload is None:
        return {}
    if not isinstance(evidence_payload, dict):
        raise TypeError("evidence_payload debe ser un diccionario.")
    return {str(key): value for key, value in evidence_payload.items()}


def _classify_severity(incident_type: str, evidence_payload: Dict[str, Any]) -> str:
    """Clasifica la severidad con reglas deterministas."""
    decision = evidence_payload.get("decision", {}) if isinstance(evidence_payload, dict) else {}
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
) -> Dict[str, Any]:
    """Prepara una alerta local con expediente, severidad y script disuasorio."""
    normalized_type = _normalize_incident_type(incident_type)
    normalized_evidence = _normalize_evidence(evidence_payload)
    normalized_contacts = _normalize_contacts(contacts)

    payload_signature = json.dumps(
        {"incident_type": normalized_type, "evidence": normalized_evidence},
        sort_keys=True,
        ensure_ascii=False,
    )
    digest = hashlib.sha256(payload_signature.encode("utf-8")).hexdigest()
    if digest in _SEEN_ALERTS:
        return {
            "status": "duplicate",
            "alert_id": f"ALERT-DUP-{digest[:12]}",
            "incident_type": normalized_type,
            "severity": _classify_severity(normalized_type, normalized_evidence),
            "contacts_notified": normalized_contacts,
            "deterrent_audio_script": "Alerta ya registrada localmente; no se duplica el expediente.",
            "alert_message": "La alerta ya fue preparada y no se duplicará automáticamente.",
        }
    _SEEN_ALERTS.add(digest)

    now = dt.datetime.now()
    alert_id = f"ALERT-{int(now.timestamp())}-{uuid.uuid4().hex[:8]}"
    severity = _classify_severity(normalized_type, normalized_evidence)

    vehicle = normalized_evidence.get("vehicle") if isinstance(normalized_evidence, dict) else None
    if isinstance(vehicle, dict):
        plate = normalized_evidence.get("vehicle_plate") or normalized_evidence.get("plate") or vehicle.get("plate")
    else:
        plate = normalized_evidence.get("vehicle_plate") or normalized_evidence.get("plate")
    destination = normalized_evidence.get("destination")
    last_known_location = (
        normalized_evidence.get("last_known_location")
        or normalized_evidence.get("location")
        or normalized_evidence.get("origin")
    )

    if normalized_type == "PHYSICAL_RISK":
        dispatch_message = (
            "🚨 ALERTA DE EMERGENCIA: Se preparó una escalada preventiva para un riesgo físico durante el trayecto. "
            f"Placa: {plate or 'No registrada'}. Destino: {destination or 'No informado'}. "
            f"Última ubicación conocida: {last_known_location or 'No disponible'}."
        )
        script = (
            f"Aviso de seguridad: la unidad con placa {plate or 'sin placa registrada'} requiere atención preventiva; "
            "se activa una revisión local del caso y se prepara una respuesta formal."
        )
    else:
        dispatch_message = (
            "⚠️ ALERTA DE SEGURIDAD: Se consolidó evidencia de un posible incidente digital o de coacción. "
            "El expediente se prepara para revisión y escalamiento autorizados."
        )
        script = (
            "Mensaje disuasorio preparado: se activa una revisión local del caso y se reforzará la coordinación con contactos de respaldo."
        )

    incident_report = {
        "report_id": f"SOS-{int(now.timestamp())}",
        "timestamp": now.isoformat(),
        "type": normalized_type,
        "evidence": normalized_evidence,
        "police_complaint_ready": False,
        "status": "PREPARED",
        "severity": severity,
    }

    return {
        "status": "escalated",
        "alert_id": alert_id,
        "incident_type": normalized_type,
        "severity": severity,
        "contacts_notified": normalized_contacts,
        "deterrent_audio_script": script,
        "alert_message": dispatch_message,
        "incident_report": incident_report,
        "vehicle_plate": plate,
        "destination": destination,
        "last_known_location": last_known_location,
    }
