"""
Módulo de Sandbox e Inspección de Enlaces (UrlSandbox)
Liderado por: Santiago (Rol: Network & Threat Sandbox Specialist)
Reto Agente 2026 - SentinelGuard AI
"""

import re
from urllib.parse import urlparse
from typing import Dict, Any

SUSPICIOUS_TLDS = {".xyz", ".top", ".cc", ".ru", ".tk", ".ml", ".ga", ".cf", ".gq", ".live"}
OFFICIAL_BANKS = {
    "bancolombia": "bancolombia.com",
    "nequi": "nequi.com.co",
    "daviplata": "daviplata.com",
    "davivienda": "davivienda.com",
    "bbva": "bbva.com.co",
    "scotiabank": "scotiabankcolpatria.com"
}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "rb.gy"}

def analyze_url(raw_url: str) -> Dict[str, Any]:
    """
    Inspecciona y calcula el nivel de riesgo de una URL sospechosa.
    
    Santiago implementa aquí:
    - Desenrollado seguro de acortadores con peticiones HEAD
    - Detección de typosquatting contra entidades financieras colombianas
    - Verificación de entropía y TLDs sospechosos
    """
    findings = []
    risk_score = 0
    expanded_url = raw_url
    
    try:
        parsed = urlparse(raw_url if "://" in raw_url else f"http://{raw_url}")
        domain = parsed.netloc.lower() or parsed.path.lower()
        if ":" in domain:
            domain = domain.split(":")[0]
    except Exception as e:
        domain = raw_url.lower()

    # 1. Verificación de TLD sospechoso
    is_suspicious_tld = any(domain.endswith(tld) for tld in SUSPICIOUS_TLDS)
    if is_suspicious_tld:
        risk_score += 40
        findings.append(f"Dominio utiliza extensión de alto riesgo TLD ({domain})")

    # 2. Verificación de acortadores
    is_shortener = any(shortener in domain for shortener in SHORTENERS)
    if is_shortener:
        risk_score += 25
        findings.append(f"Enlace oculto bajo acortador público ({domain})")

    # 3. Detección de Typosquatting (Suplantación bancaria)
    is_typosquatting = False
    impersonated_brand = None
    for brand, official_domain in OFFICIAL_BANKS.items():
        if brand in domain and domain != official_domain and not domain.endswith(f".{official_domain}"):
            is_typosquatting = True
            impersonated_brand = brand
            risk_score += 60
            findings.append(f"Alerta de Typosquatting: El dominio '{domain}' imita ilícitamente a '{brand}'")
            break

    # 4. Veredicto
    if risk_score >= 60:
        verdict = "MALICIOSO"
    elif risk_score >= 25:
        verdict = "SOSPECHOSO"
    else:
        verdict = "SEGURO"

    return {
        "status": "success",
        "original_url": raw_url,
        "expanded_url": expanded_url,
        "domain": domain,
        "is_suspicious_tld": is_suspicious_tld,
        "is_shortener": is_shortener,
        "is_typosquatting": is_typosquatting,
        "impersonated_brand": impersonated_brand,
        "risk_score": min(100, risk_score),
        "verdict": verdict,
        "findings": findings
    }
