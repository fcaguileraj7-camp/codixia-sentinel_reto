import re
from typing import Dict, Any

OFFICIAL_DOMAINS = [
    "bancolombia.com",
    "nequi.com.co",
    "daviplata.com",
    "davivienda.com",
    "bbva.com.co",
    "scotiabankcolpatria.com",
    "gob.co",
    "policia.gov.co"
]

SUSPICIOUS_KEYWORDS = [
    "bloqueada", "suspensión", "urgente", "inmediato", "haga clic",
    "transfiera", "premios", "sorteo", "felicidades", "código de seguridad",
    "actualice sus datos", "cai virtual", "embargo", "captura"
]

def inspect_threat(content: str) -> Dict[str, Any]:
    """
    Analiza un mensaje de texto, enlace o transcripción para detectar patrones de estafa o phishing.
    """
    findings = []
    risk_score = 0
    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)

    # 1. Análisis de URLs
    suspicious_urls = []
    for url in urls:
        clean_url = url.lower()
        is_official = any(domain in clean_url for domain in OFFICIAL_DOMAINS)
        if not is_official:
            suspicious_urls.append(url)
            risk_score += 40
            findings.append(f"Enlace no oficial sospechoso detectado: {url}")
        else:
            findings.append(f"Enlace hacia dominio oficial: {url}")

    # 2. Análisis de Disparadores Psicológicos (Ingeniería Social)
    content_lower = content.lower()
    matched_keywords = [kw for kw in SUSPICIOUS_KEYWORDS if kw in content_lower]
    if matched_keywords:
        risk_score += min(50, len(matched_keywords) * 15)
        findings.append(f"Disparadores de urgencia o alarma detectados: {', '.join(matched_keywords)}")

    # 3. Clasificación de Nivel de Riesgo
    if risk_score >= 60:
        threat_level = "CRÍTICO"
        recommendation = "No interactúe, no abra enlaces ni entregue códigos. Denuncie ante el CAI Virtual."
    elif risk_score >= 30:
        threat_level = "MEDIO"
        recommendation = "Precaución: verifique directamente en la aplicación oficial del banco."
    else:
        threat_level = "BAJO"
        recommendation = "No se identificaron patrones inmediatos de fraude conocido."

    return {
        "status": "success",
        "threat_level": threat_level,
        "risk_score": min(100, risk_score),
        "detected_urls": urls,
        "suspicious_urls": suspicious_urls,
        "matched_triggers": matched_keywords,
        "findings": findings,
        "recommendation": recommendation
    }
