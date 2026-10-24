"""
Módulo de Reportes Oficiales para CAI Virtual de Policía
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
"""

"""
Módulo PoliceReporter (Hito S2)
Generación de expedientes estructurados para el CAI Virtual de la Policía.
Reto Agente 2026 · SentinelGuard AI · Equipo Codixia

Rol 4: Nicolle (Social Engineering NLP, Visión & CAI Virtual)

Principio rector: NUNCA inventar información. Todo lo que no conste en la
evidencia recibida se declara explícitamente como "NO DISPONIBLE EN LA EVIDENCIA".
"""

import datetime
import uuid
from typing import Dict, Any, List

#: Marcador explícito para datos ausentes. Evita fabricar contenido en el radicado.
NOT_AVAILABLE = "NO DISPONIBLE EN LA EVIDENCIA"

#: Campos cuyo contenido se vuelca textualmente al expediente.
REQUIRED_TEXT_FIELDS = ["user_input"]
#: Campos recomendados; su ausencia se reporta como advertencia, no como error.
RECOMMENDED_FIELDS = ["sender_phone", "incident_type", "risk_level"]


def _as_clean_list(value: Any) -> List[str]:
    """Normaliza cualquier entrada a una lista de cadenas no vacías."""
    if not value:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _validate_evidence(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Valida la evidencia sin descartarla: devuelve errores y advertencias."""
    validation = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "missing_fields": [],
    }

    if not isinstance(evidence, dict):
        validation["is_valid"] = False
        validation["errors"].append("la_evidencia_debe_ser_un_diccionario")
        return validation

    if not evidence:
        validation["is_valid"] = False
        validation["errors"].append("evidencia_vacia")
        return validation

    for field in REQUIRED_TEXT_FIELDS:
        value = evidence.get(field)
        if value is None or not str(value).strip():
            validation["errors"].append(f"campo_obligatorio_ausente:{field}")
            validation["missing_fields"].append(field)

    for field in RECOMMENDED_FIELDS:
        value = evidence.get(field)
        if value is None or not str(value).strip():
            validation["warnings"].append(f"campo_recomendado_ausente:{field}")
            validation["missing_fields"].append(field)

    # Un caso incompleto se marca como no válido solo cuando falta el contenido
    # mínimo que sustenta la denuncia.
    if any(err.startswith("campo_obligatorio_ausente") for err in validation["errors"]):
        validation["is_valid"] = False

    return validation

def generate_police_report(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compila un expediente de denuncia formal formateado para el portal
    del CAI Virtual de la Policía Nacional de Colombia (caivirtual.policia.gov.co).

    No inventa datos: los campos ausentes se marcan como NO DISPONIBLE EN LA
    EVIDENCIA y quedan listados en `missing_fields`.
    """
    validation = _validate_evidence(evidence)

    if not validation["is_valid"]:
        return {
            "status": "error",
            "error": "evidencia_insuficiente",
            "message": (
                "No es posible generar el expediente: la evidencia está vacía o "
                "carece del contenido mínimo requerido."
            ),
            "report_id": None,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "incident_category": NOT_AVAILABLE,
            "formatted_markdown": "",
            "suggested_actions": [],
            "missing_fields": validation["missing_fields"],
            "validation": validation,
        }
    # uuid corto: evita colisiones de radicado al generar varios en el mismo segundo.
    report_id = f"CAI-COL-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sender = str(evidence.get("sender_phone") or "").strip() or NOT_AVAILABLE
    incident_type = str(evidence.get("incident_type") or "").strip() or "Tentativa de Estafa / Phishing"
    user_input = str(evidence.get("user_input", "")).strip()
    risk_level = str(evidence.get("risk_level") or "").strip() or "POR DETERMINAR"
    findings = _as_clean_list(evidence.get("findings"))
    detected_urls = _as_clean_list(evidence.get("detected_urls"))

    urls_section = ", ".join(detected_urls) if detected_urls else "Ninguno"
    findings_section = (
        "\n".join(f"  * {f}" for f in findings)
        if findings
        else "  * Sin hallazgos técnicos adicionales en la evidencia recibida."
    )
    status_line = (
        "PENDIENTE DE RADICACIÓN JUDICIAL"
        if validation["is_valid"]
        else "INCOMPLETO — REQUIERE EVIDENCIA ADICIONAL"
    )

    formatted_markdown = f"""# EXPEDIENTE DE DENUNCIA DIGITAL — POLICÍA NACIONAL DE COLOMBIA
**Radicado Técnico:** {report_id}
**Fecha y Hora:** {timestamp}
**Estado:** {status_line}
**Tipo de Incidente:** {incident_type}
**Nivel de Amenaza:** {risk_level}

---

### 1. DATOS DEL EMISOR HOSTIL
- **Identificador / Teléfono:** {sender}
- **Canal de Contacto:** WhatsApp / Mensajería Instantánea

### 2. EVIDENCIA TEXTUAL Y CONTENIDO
```text
{user_input}
```

### 3. ELEMENTOS TÉCNICOS DETECTADOS
- **Enlaces maliciosos/sospechosos:** {urls_section}
- **Hallazgos del Análisis:**
{findings_section}

### 4. MEDIDAS PREVENTIVAS SUGERIDAS AL CIUDADANO
1. Bloquear inmediatamente al contacto emisor en WhatsApp.
2. No realizar transferencias ni suministrar tokens OTP.
3. Radicar formalmente con este código en https://caivirtual.policia.gov.co/
"""

    return {
        "status": "success",
        "report_id": report_id,
        "timestamp": timestamp,
        "incident_category": incident_type,
        "formatted_markdown": formatted_markdown,
        "suggested_actions": [
            "Bloquear contacto emisor",
            "No abrir enlaces ni compartir tokens",
            "Radicar denuncia formal en CAI Virtual"
        ],
        "risk_level": risk_level,
        "sender_phone": sender,
        "missing_fields": validation["missing_fields"],
        "validation": validation,
    }
