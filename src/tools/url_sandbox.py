"""
Módulo de Sandbox e Inspección de Enlaces (UrlSandbox)
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
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

_LEET_MAP = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "$": "s", "@": "a"})
_MIN_FUZZY_LEN = 5


def _normalize(label: str) -> str:
    """Reduce un token a su forma 'visual': leetspeak, 'rn'->'m' y letras repetidas colapsadas."""
    label = label.lower().translate(_LEET_MAP).replace("rn", "m")
    return re.sub(r"(.)\1+", r"\1", label)


def _edit_distance(a: str, b: str) -> int:
    """Distancia de Levenshtein clásica (programación dinámica por filas)."""
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = curr
    return prev[-1]


def _is_official(domain: str, official_domain: str) -> bool:
    return domain == official_domain or domain.endswith(f".{official_domain}")


def _detect_brand(domain: str):
    """
    Devuelve la marca bancaria imitada por `domain`, o None.
    Criterios: marca literal, marca tras normalizar leetspeak/repeticiones,
    o token a distancia de edición pequeña de la marca.
    """
    tokens = [t for t in re.split(r"[.\-_]", domain) if t]
    for brand, official_domain in OFFICIAL_BANKS.items():
        if _is_official(domain, official_domain):
            continue
        norm_brand = _normalize(brand)
        max_dist = 1 if len(brand) <= 8 else 2
        for token in tokens:
            if brand in token or norm_brand in _normalize(token):
                return brand
            norm_token = _normalize(token)
            if len(norm_token) >= _MIN_FUZZY_LEN and _edit_distance(norm_token, norm_brand) <= max_dist:
                return brand
    return None

def analyze_url(raw_url: str) -> Dict[str, Any]:
    """
    Inspecciona y calcula el nivel de riesgo de una URL sospechosa.
    
    Miguel implementa aquí:
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
    brand = _detect_brand(domain)
    if brand:
        is_typosquatting = True
        impersonated_brand = brand
        risk_score += 60
        findings.append(f"Alerta de Typosquatting: El dominio '{domain}' imita ilícitamente a '{brand}'")

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
