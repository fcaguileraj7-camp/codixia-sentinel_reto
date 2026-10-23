"""
Módulo de Sandbox e Inspección de Enlaces (UrlSandbox)
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
"""

import http.client
import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse
from typing import Dict, Any, List, Optional, Tuple

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

MAX_REDIRECTS = 5
EXPAND_TIMEOUT = 3

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

def _is_public_host(host: str) -> bool:
    """False si el host resuelve a una IP privada, loopback, link-local o reservada (anti-SSRF)."""
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError):
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if not ip.is_global:
            return False
    return bool(infos)


def _head_request(url: str, timeout: float = EXPAND_TIMEOUT) -> Tuple[int, Optional[str]]:
    """Una sola petición HEAD sin seguir redirecciones. Devuelve (status, cabecera Location)."""
    parsed = urlparse(url)
    conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(parsed.hostname, parsed.port, timeout=timeout)
    try:
        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"
        conn.request("HEAD", path, headers={"User-Agent": "SentinelGuard-UrlSandbox/1.0"})
        resp = conn.getresponse()
        return resp.status, resp.getheader("Location")
    finally:
        conn.close()


def _expand_url(url: str) -> Tuple[str, List[str], Optional[str]]:
    """
    Desenrolla redirecciones con HEAD manual (máx. MAX_REDIRECTS saltos).
    Devuelve (url_final, cadena_de_saltos, error). Nunca lanza excepciones.
    """
    chain = [url]
    current = url
    try:
        for _ in range(MAX_REDIRECTS + 1):
            parsed = urlparse(current)
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                return current, chain, "Esquema o host no permitido"
            if not _is_public_host(parsed.hostname):
                return current, chain, "Host no público bloqueado (protección SSRF)"
            status, location = _head_request(current)
            if status not in (301, 302, 303, 307, 308) or not location:
                return current, chain, None
            if len(chain) > MAX_REDIRECTS:
                break
            current = urljoin(current, location)
            if current in chain:
                return current, chain, "Bucle de redirecciones"
            chain.append(current)
        return current, chain, f"Demasiadas redirecciones (>{MAX_REDIRECTS})"
    except Exception as e:
        return current, chain, f"No se pudo expandir el enlace: {type(e).__name__}"


def analyze_url(raw_url: str, expand: bool = True) -> Dict[str, Any]:
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
    redirect_chain = [raw_url]
    expansion_error = None

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
    is_shortener = domain.removeprefix("www.") in SHORTENERS
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

    # 3b. Desenrollado del acortador y análisis del destino real
    if is_shortener and expand:
        start = raw_url if "://" in raw_url else f"http://{raw_url}"
        expanded_url, redirect_chain, expansion_error = _expand_url(start)
        if expansion_error:
            findings.append(f"No se pudo verificar el destino del acortador: {expansion_error}")
        if expanded_url != start:
            findings.append(f"Acortador desenrollado: {expanded_url}")
            final = analyze_url(expanded_url, expand=False)
            risk_score += final["risk_score"]
            findings.extend(final["findings"])
            is_suspicious_tld = is_suspicious_tld or final["is_suspicious_tld"]
            if final["is_typosquatting"]:
                is_typosquatting = True
                impersonated_brand = final["impersonated_brand"]

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
        "findings": findings,
        "redirect_chain": redirect_chain,
        "expansion_error": expansion_error
    }
