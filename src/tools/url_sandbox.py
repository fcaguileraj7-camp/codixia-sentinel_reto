"""
Módulo de Sandbox e Inspección de Enlaces (UrlSandbox)
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
"""

import http.client
import ipaddress
import json
import re
import socket
import ssl
import time
from functools import lru_cache
from pathlib import Path
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
EXPAND_BUDGET = 8
ALLOWED_PORTS = {80, 443, 8080, 8443}

BLACKLIST_PATH = Path(__file__).resolve().parents[2] / "data" / "url_blacklist.json"

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

def _resolve_public_ip(host: str) -> Optional[str]:
    """
    Resuelve `host` una sola vez. Devuelve la IP si TODAS las direcciones son públicas;
    None si alguna es privada, loopback, link-local o reservada (anti-SSRF), o si no resuelve.
    """
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError):
        return None
    if not infos:
        return None
    ips = [info[4][0].split("%")[0] for info in infos]
    if not all(ipaddress.ip_address(ip).is_global for ip in ips):
        return None
    return ips[0]


def _is_public_host(host: str) -> bool:
    return _resolve_public_ip(host) is not None


class _PinnedHTTPConnection(http.client.HTTPConnection):
    """Conecta a una IP ya validada, evitando una segunda resolución DNS (DNS rebinding)."""

    def __init__(self, host, ip, **kwargs):
        super().__init__(host, **kwargs)
        self._pinned_ip = ip

    def connect(self):
        self.sock = socket.create_connection((self._pinned_ip, self.port), self.timeout)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Igual que la HTTP, pero mantiene el nombre original en SNI y verificación del certificado."""

    def __init__(self, host, ip, **kwargs):
        super().__init__(host, context=ssl.create_default_context(), **kwargs)
        self._pinned_ip = ip

    def connect(self):
        sock = socket.create_connection((self._pinned_ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def _head_request(url: str, timeout: float = EXPAND_TIMEOUT) -> Tuple[int, Optional[str]]:
    """Una sola petición HEAD sin seguir redirecciones. Devuelve (status, cabecera Location)."""
    parsed = urlparse(url)
    ip = _resolve_public_ip(parsed.hostname)
    if ip is None:
        raise PermissionError("Host no público bloqueado (protección SSRF)")
    conn_cls = _PinnedHTTPSConnection if parsed.scheme == "https" else _PinnedHTTPConnection
    conn = conn_cls(parsed.hostname, ip, port=parsed.port, timeout=timeout)
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
    deadline = time.monotonic() + EXPAND_BUDGET
    try:
        for _ in range(MAX_REDIRECTS + 1):
            if time.monotonic() > deadline:
                return current, chain, f"Presupuesto de tiempo agotado (>{EXPAND_BUDGET}s)"
            parsed = urlparse(current)
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                return current, chain, "Esquema o host no permitido"
            if parsed.port is not None and parsed.port not in ALLOWED_PORTS:
                return current, chain, f"Puerto no permitido ({parsed.port})"
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


def _ensure_scheme(raw: str) -> str:
    """Devuelve la URL tal cual si ya trae esquema ("://"); si no, antepone http://."""
    return raw if "://" in raw else f"http://{raw}"


def _extract_domain(raw: str) -> str:
    """Extrae el dominio (host en minúsculas) de una URL; ante error, devuelve la entrada en minúsculas."""
    try:
        parsed = urlparse(_ensure_scheme(raw))
        # hostname descarta userinfo (user:pass@), puerto y corchetes IPv6
        return (parsed.hostname or parsed.path).lower()
    except Exception:
        return raw.lower()


def _load_blacklist(path) -> frozenset[str]:
    """
    Carga los dominios de la lista negra desde un JSON {"entries": [{"domain": ...}, ...]}.
    Normaliza cada dominio (strip, minúsculas, sin punto final) y descarta entradas inválidas.
    Nunca lanza: ante archivo inexistente, JSON corrupto o estructura inesperada
    devuelve un conjunto vacío (el análisis sigue funcionando solo con heurística).
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = data.get("entries") if isinstance(data, dict) else None
        if not isinstance(entries, list):
            return frozenset()
        domains = set()
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            domain = entry.get("domain")
            if not isinstance(domain, str):
                continue
            domain = domain.strip().lower().rstrip(".")
            if domain:
                domains.add(domain)
        return frozenset(domains)
    except Exception:
        return frozenset()


@lru_cache(maxsize=1)
def _get_blacklist() -> frozenset[str]:
    """Lista negra local por defecto (BLACKLIST_PATH), leída una sola vez y cacheada en memoria."""
    return _load_blacklist(BLACKLIST_PATH)


def _is_blacklisted(domain: str, blacklist: frozenset) -> bool:
    """
    Indica si `domain` o alguno de sus sufijos de etiquetas está en `blacklist`
    (a.b.site se prueba como "a.b.site" y "b.site"). Nunca se prueba el TLD suelto.
    """
    if not blacklist:
        return False
    labels = domain.rstrip(".").split(".")
    return any(".".join(labels[i:]) in blacklist for i in range(len(labels) - 1))


def analyze_url(raw_url: str, expand: bool = True, blacklist: Optional[frozenset] = None) -> Dict[str, Any]:
    """
    Inspecciona una URL sospechosa y calcula su nivel de riesgo.

    Realiza cinco análisis:
    - Consulta de la lista negra local de URLs fraudulentas reportadas: un dominio listado
      (o cuyo sufijo de etiquetas esté listado) suma riesgo máximo y es MALICIOSO aunque
      su TLD y su nombre pasen los demás filtros. También se aplica al destino real de un
      acortador desenrollado.
    - Detección de TLDs de alto riesgo (por ejemplo .xyz, .top, .ru).
    - Detección de acortadores públicos (SHORTENERS); se hace siempre, con o sin `expand`.
    - Desenrollado de los acortadores detectados (solo si `expand` es True) con peticiones
      HEAD, sin seguir redirecciones automáticamente (cada salto se valida a mano). Incluye
      protección SSRF: la IP del destino se valida como pública y se fija para la conexión,
      solo se permiten los puertos de ALLOWED_PORTS, y la expansión se corta si se supera
      el presupuesto de tiempo, comprobado antes de cada salto. El destino real se vuelve
      a analizar sin expandir de nuevo.
    - Detección de typosquatting bancario contra entidades financieras colombianas,
      mediante normalización leetspeak y distancia de edición.

    Args:
        raw_url: URL o dominio a analizar (se acepta sin esquema).
        expand: si es True, desenrolla los acortadores detectados.
        blacklist: conjunto de dominios ya normalizados (minúsculas, sin punto final) contra
            el que se compara el dominio. Si es None se usa la lista local de
            data/url_blacklist.json (BLACKLIST_PATH), leída una vez y cacheada; si ese archivo
            falta o es inválido la lista queda vacía. Un frozenset vacío desactiva la
            consulta y deja solo la heurística.

    Returns:
        Diccionario con las claves:
        - status: "success", o "error" si la entrada está vacía o no es texto.
        - original_url / expanded_url: URL recibida (sin espacios en los extremos) y URL
          final tras el desenrollado.
        - domain: dominio analizado en minúsculas.
        - is_suspicious_tld / is_shortener / is_typosquatting: indicadores booleanos.
        - is_blacklisted: True si el dominio, o el destino de un acortador desenrollado,
          está en la lista negra.
        - impersonated_brand: entidad suplantada, o None.
        - risk_score: puntaje de riesgo entre 0 y 100.
        - verdict: "SEGURO", "SOSPECHOSO", "MALICIOSO" o "NO_ANALIZADO".
        - findings: lista de hallazgos legibles.
        - redirect_chain: cadena de URLs recorridas durante el desenrollado.
        - expansion_error: motivo del fallo al expandir, o None.
    """
    return _analyze_url(raw_url, expand, blacklist)


def _analyze_url(raw_url: str, expand: bool, blacklist: Optional[frozenset]) -> Dict[str, Any]:
    """Núcleo del análisis de URL; lo invocan analyze_url y la recursión del desenrollado."""
    if not isinstance(raw_url, str) or not raw_url.strip():
        return {
            "status": "error",
            "original_url": raw_url,
            "expanded_url": raw_url,
            "domain": "",
            "is_suspicious_tld": False,
            "is_shortener": False,
            "is_typosquatting": False,
            "is_blacklisted": False,
            "impersonated_brand": None,
            "risk_score": 0,
            "verdict": "NO_ANALIZADO",
            "findings": ["Entrada vacía o inválida: no hay URL para analizar"],
            "redirect_chain": [],
            "expansion_error": None
        }
    raw_url = raw_url.strip()
    if blacklist is None:
        blacklist = _get_blacklist()
    findings = []
    risk_score = 0
    expanded_url = raw_url
    redirect_chain = [raw_url]
    expansion_error = None

    domain = _extract_domain(raw_url)

    # 0. Lista negra local de URLs fraudulentas reportadas
    is_blacklisted = _is_blacklisted(domain, blacklist)
    if is_blacklisted:
        risk_score += 100
        findings.append(f"Dominio en lista negra local de URLs fraudulentas ({domain})")

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
        start = _ensure_scheme(raw_url)
        expanded_url, redirect_chain, expansion_error = _expand_url(start)
        if expansion_error:
            findings.append(f"No se pudo verificar el destino del acortador: {expansion_error}")
        if expanded_url != start:
            findings.append(f"Acortador desenrollado: {expanded_url}")
            final = _analyze_url(expanded_url, False, blacklist)
            risk_score += final["risk_score"]
            findings.extend(final["findings"])
            is_suspicious_tld = is_suspicious_tld or final["is_suspicious_tld"]
            is_blacklisted = is_blacklisted or final["is_blacklisted"]
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
        "is_blacklisted": is_blacklisted,
        "impersonated_brand": impersonated_brand,
        "risk_score": min(100, risk_score),
        "verdict": verdict,
        "findings": findings,
        "redirect_chain": redirect_chain,
        "expansion_error": expansion_error
    }
