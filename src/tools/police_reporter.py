"""
Módulo de Reportes Oficiales para CAI Virtual de Policía
Liderado por: Nicolle (Rol 4: Detección de Engaño Psicológico, Visión & CAI Virtual)
Reto Agente 2026 - SentinelGuard AI
"""

import datetime
from typing import Dict, Any

def generate_police_report(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compila un expediente de denuncia formal formateado para el portal
    del CAI Virtual de la Policía Nacional de Colombia (caivirtual.policia.gov.co).
    """
    report_id = f"CAI-COL-{int(datetime.datetime.now().timestamp())}"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    sender = evidence.get("sender_phone", "Número no identificado / Desconocido")
    incident_type = evidence.get("incident_type", "Tentativa de Estafa / Phishing")
    user_input = evidence.get("user_input", "")
    risk_level = evidence.get("risk_level", "ALTO")
    findings = evidence.get("findings", [])
    detected_urls = evidence.get("detected_urls", [])

    formatted_markdown = f"""# EXPEDIENTE DE DENUNCIA DIGITAL — POLICÍA NACIONAL DE COLOMBIA
**Radicado Técnico:** {report_id}
**Fecha y Hora:** {timestamp}
**Estado:** PENDIENTE DE RADICACIÓN JUDICIAL
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
- **Enlaces maliciosos/sospechosos:** {', '.join(detected_urls) if detected_urls else 'Ninguno'}
- **Hallazgos del Análisis:**
{chr(10).join(f'  * {f}' for f in findings) if findings else '  * Patrones de ingeniería social y presión psicológica.'}

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
        ]
    }
