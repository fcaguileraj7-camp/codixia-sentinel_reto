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
import stringprep
import time
import unicodedata
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlparse
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

# Longitud máxima de un nombre de dominio (RFC 1035); por encima el host se marca inválido
# y no se ejecutan los chequeos costosos (lista negra y typosquatting).
MAX_DOMAIN_LEN = 253

# Longitud máxima de URL que se analiza a fondo: las URLs reales casi nunca pasan de 2-8 KB
# (enlaces con muchos parámetros de tracking o SAML pueden superarla y quedan marcados como
# sospechosos, lo cual se acepta en SMS). Acota el coste de unicodedata.normalize (NFKC), que es
# cuadrático con caracteres que se expanden mucho (U+FDFA): solo se lee el host de los primeros
# MAX_URL_LEN caracteres; una URL más larga suma riesgo y no se desenrolla, y si la autoridad no
# se cierra dentro de esa ventana el host también se marca como sospechoso.
MAX_URL_LEN = 8192

_LEET_MAP = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "$": "s", "@": "a"})
_MIN_FUZZY_LEN = 5
# Marcas cuya forma normalizada tiene menos caracteres que esto (bbva -> bva) no se buscan como
# subcadena del token normalizado (darían falsos positivos: bvasports.com). Solo coinciden por
# igualdad con el token normalizado, o si la marca literal aparece en el token tras el leetspeak
# (bbv4seguro.com).
_MIN_SUBSTRING_BRAND_LEN = 4

# Controles C0 (U+0000..U+001F) y espacio (U+0020): los navegadores los quitan del inicio y del
# final de la URL antes de leerla.
_C0_AND_SPACE = "".join(chr(i) for i in range(0x21))
# Esquemas que los navegadores aceptan con 0 o más "/" tras los dos puntos (https:evil.xyz).
_SPECIAL_SCHEME_RE = re.compile(r"(https?|ftp|wss?):/*", re.IGNORECASE)
_ANY_SCHEME_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*://")
# Puntos Unicode que un navegador trata como ".": U+3002, U+FF0E y U+FF61. NFKC ya lleva U+FF0E a "."
# y U+FF61 a U+3002, pero U+3002 no cambia con NFKC, por eso hace falta este mapeo; se conservan
# las tres entradas como defensa en profundidad.
_UNICODE_DOTS = str.maketrans({"\u3002": ".", "\uff0e": ".", "\uff61": "."})
# Puntuación ASCII que queda pegada al final del host cuando la URL se extrae de un texto
# ("https://sitio.com," / "(https://sitio.com)"); urlparse la deja dentro del hostname.
# _is_trailing_junk además quita cualquier puntuación o símbolo Unicode (comillas tipográficas,
# comillas angulares, rayas, emoji...). Ninguna de las dos incluye ":" para no romper las IPv6
# que terminan en "::". Las categorías P* y S* ya cubren estos caracteres ASCII; la constante
# los deja explícitos.
_TRAILING_PUNCTUATION = ".,;!)]}'" + '"'
# Espacios, delimitadores de URL, "%" residual y caracteres de control (Cc) no válidos en un host.
_INVALID_HOST_RE = re.compile(r"""[\s/\\?#@%<>^|\[\]{}"'`\x00-\x1f\x7f-\x9f]""")


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
        short_brand = len(norm_brand) < _MIN_SUBSTRING_BRAND_LEN
        for token in tokens:
            norm_token = _normalize(token)
            if short_brand:
                # igualdad, o la marca literal tras el leetspeak (bbv4seguro -> bbvaseguro)
                norm_match = norm_token == norm_brand or brand in token.lower().translate(_LEET_MAP)
            else:
                norm_match = norm_brand in norm_token
            if brand in token or norm_match:
                return brand
            if len(norm_token) >= _MIN_FUZZY_LEN and _edit_distance(norm_token, norm_brand) <= max_dist:
                return brand
    return None

# Redes IPv6 que `is_global` no siempre descarta y que pueden esconder una IPv4 interna:
# site-local (obsoleto), IPv4-compatible (::a.b.c.d) y los prefijos NAT64 completos.
_IPV6_SITE_LOCAL = ipaddress.ip_network("fec0::/10")
_IPV6_IPV4_COMPATIBLE = ipaddress.ip_network("::/96")
_IPV6_NAT64 = (ipaddress.ip_network("64:ff9b::/96"), ipaddress.ip_network("64:ff9b:1::/48"))


def _is_public_ip(ip) -> bool:
    """
    Indica si `ip` (un ipaddress.ip_address) es una dirección pública de unicast.
    No es pública si no es global, si es multicast, o si es IPv6 site-local (fec0::/10),
    IPv4-compatible (::/96) o NAT64 (64:ff9b::/96 y 64:ff9b:1::/48; el prefijo entero se
    rechaza, sin mirar la IPv4 embebida). Una IPv6 que lleve una IPv4 embebida
    (IPv4-mapped, 6to4, Teredo con su servidor y su cliente) solo es pública si esa IPv4 lo es.
    """
    if not ip.is_global or ip.is_multicast:
        return False
    if ip.version == 4:
        return True
    if ip in _IPV6_SITE_LOCAL or ip in _IPV6_IPV4_COMPATIBLE or any(ip in net for net in _IPV6_NAT64):
        return False
    embedded = [ip.ipv4_mapped, ip.sixtofour]
    if ip.teredo is not None:
        embedded.extend(ip.teredo)
    return all(_is_public_ip(v4) for v4 in embedded if v4 is not None)


def _resolve_public_ip(host: str) -> Optional[str]:
    """
    Resuelve `host` una sola vez y es el ÚNICO validador anti-SSRF: la IP que devuelve es la
    que luego se fija para conectar (no hay una segunda resolución DNS que pueda cambiar).
    Devuelve la IP (la primera) si TODAS las direcciones resueltas cumplen _is_public_ip; None si
    alguna es privada, loopback, link-local, multicast, reservada, site-local o NAT64/IPv4
    embebida no pública, o si el host no resuelve. getaddrinfo no tiene timeout propio.
    """
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError):
        return None
    if not infos:
        return None
    ips = [info[4][0].split("%")[0] for info in infos]
    if not all(_is_public_ip(ipaddress.ip_address(ip)) for ip in ips):
        return None
    return ips[0]


class _PinnedHTTPConnection(http.client.HTTPConnection):
    """Conecta a una IP ya validada, evitando una segunda resolución DNS (DNS rebinding)."""

    def __init__(self, host, ip, **kwargs):
        super().__init__(host, **kwargs)
        self._pinned_ip = ip

    def connect(self):
        # create_connection cierra su propio socket si falla, y la asignación no puede fallar
        self.sock = socket.create_connection((self._pinned_ip, self.port), self.timeout)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Igual que la HTTP, pero mantiene el nombre original en SNI y verificación del certificado."""

    def __init__(self, host, ip, **kwargs):
        super().__init__(host, context=ssl.create_default_context(), **kwargs)
        self._pinned_ip = ip

    def connect(self):
        sock = socket.create_connection((self._pinned_ip, self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except BaseException:
            # fallo de handshake TLS (o similar): no dejar el socket TCP abierto
            sock.close()
            raise


_PATH_SAFE = "/%:@!$&'()*+,;=-._~"
_QUERY_SAFE = "/?%:@!$&'()*+,;=-._~"


def _head_request(url: str, timeout: float = EXPAND_TIMEOUT) -> Tuple[int, Optional[str]]:
    """
    Una sola petición HEAD sin seguir redirecciones. Devuelve (status, cabecera Location).
    Resuelve el host UNA vez (_resolve_public_ip) y conecta a esa IP validada; si el host no
    es público lanza PermissionError antes de abrir ningún socket. El puerto siempre es
    explícito (el de la URL, o 80/443 según el esquema): sin él, http.client toma el último
    grupo de una IPv6 sin corchetes como puerto. La ruta y la query se codifican en
    porcentaje (UTF-8; los %XX existentes no se re-escapan) porque http.client exige ASCII.
    `timeout` es por operación de socket (conexión, handshake, lectura), no el total.
    """
    parsed = urlparse(url)
    ip = _resolve_public_ip(parsed.hostname)
    if ip is None:
        raise PermissionError("Host no público bloqueado (protección SSRF)")
    conn_cls = _PinnedHTTPSConnection if parsed.scheme == "https" else _PinnedHTTPConnection
    port = parsed.port if parsed.port is not None else (443 if parsed.scheme == "https" else 80)
    conn = conn_cls(parsed.hostname, ip, port=port, timeout=timeout)
    try:
        path = quote(parsed.path or "/", safe=_PATH_SAFE)
        if parsed.query:
            path += "?" + quote(parsed.query, safe=_QUERY_SAFE)
        conn.request("HEAD", path, headers={"User-Agent": "SentinelGuard-UrlSandbox/1.0"})
        resp = conn.getresponse()
        return resp.status, resp.getheader("Location")
    finally:
        conn.close()


def _expand_url(url: str) -> Tuple[str, List[str], Optional[str]]:
    """
    Desenrolla redirecciones con HEAD manual (máx. MAX_REDIRECTS saltos).
    Devuelve (url_final, cadena_de_saltos, error). Nunca lanza excepciones.

    Cada salto hace UNA sola resolución DNS: la validación anti-SSRF vive en _head_request, que
    resuelve, valida y fija la IP; si el host no es público lanza PermissionError y aquí se
    informa como bloqueo SSRF. La cabecera Location se une con urljoin y se normaliza igual que
    la entrada (_normalize_url), de modo que "https://a.com\\@b.com/" se lee como en un
    navegador (host a.com).

    Presupuesto de tiempo (EXPAND_BUDGET): se comprueba antes de cada salto y también después de
    cada HEAD que pida seguir una redirección. A cada HEAD se le pasa un timeout de
    min(EXPAND_TIMEOUT, tiempo restante), con un mínimo de 0.1 s. No es un límite duro: el
    timeout es por operación de socket (conexión, handshake, lectura) y la resolución DNS
    (getaddrinfo) no tiene timeout propio, así que un servidor o un DNS lentos pueden exceder
    el presupuesto.
    """
    chain = [url]
    current = url
    deadline = time.monotonic() + EXPAND_BUDGET
    budget_error = f"Presupuesto de tiempo agotado (>{EXPAND_BUDGET}s)"
    try:
        for _ in range(MAX_REDIRECTS + 1):
            remaining = deadline - time.monotonic()
            if remaining < 0:
                return current, chain, budget_error
            parsed = urlparse(current)
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                return current, chain, "Esquema o host no permitido"
            if parsed.port is not None and parsed.port not in ALLOWED_PORTS:
                return current, chain, f"Puerto no permitido ({parsed.port})"
            status, location = _head_request(current, timeout=max(0.1, min(EXPAND_TIMEOUT, remaining)))
            if status not in (301, 302, 303, 307, 308) or not location:
                return current, chain, None
            if len(chain) > MAX_REDIRECTS:
                break
            if time.monotonic() > deadline:
                return current, chain, budget_error
            current = urljoin(current, location)
            # solo http/https: normalizar otro esquema (mailto:x@y) lo volvería http://mailto:x@y
            if urlparse(current).scheme in ("http", "https"):
                current = _normalize_url(current)
            if current in chain:
                return current, chain, "Bucle de redirecciones"
            chain.append(current)
        return current, chain, f"Demasiadas redirecciones (>{MAX_REDIRECTS})"
    except PermissionError:
        # _head_request lo lanza cuando el host (o su resolución) no es público
        return current, chain, "Host no público bloqueado (protección SSRF)"
    except Exception as e:
        return current, chain, f"No se pudo expandir el enlace: {type(e).__name__}"


def _normalize_url(raw: str) -> str:
    """
    Aproxima cómo lee un navegador la URL solo en lo que afecta al host: la barra invertida
    (aquí) y los %XX del host (en _parse_host). No emula el estándar WHATWG completo:
    por ejemplo IDNA/punycode no se cubren.
    Los navegadores tratan "\\" como "/" en la autoridad y la ruta de URLs http/https
    (https://evil.xyz\\@www.bancolombia.com/ abre evil.xyz), pero urlparse no, así que
    el host quedaría mal calculado. Se reemplaza solo antes del primer "?" o "#" (en la
    query y el fragmento la barra invertida se deja intacta), con cualquier esquema aunque
    solo es exacto para http/https.
    Primero quita del inicio y del final los controles C0 y los espacios (_C0_AND_SPACE), como
    hace el navegador ("\\x00https://sitio.com" se lee como "https://sitio.com").
    Después fija el esquema, en este orden:
    - http, https, ftp, ws o wss seguidos de cero o más "/": se reescribe como "<esquema>://"
      (https:evil.xyz y https:///evil.xyz se leen como https://evil.xyz).
    - empieza por "//": se reescribe como "http://" más el resto sin las "/" iniciales
      ("//", "///" y "////evil.xyz" se leen como http://evil.xyz). Una sola "/" inicial no
      entra aquí: es una ruta relativa, sin host, que _is_invalid_host marca inválida.
    - ya trae "<esquema>://" de otro tipo (file://, javascript://...): se deja igual.
    - cualquier otro caso: se antepone "http://" (aunque "://" aparezca más adelante, en la
      ruta, la query o el fragmento).
    No lanza con ningún str; aplicarla de nuevo sobre una URL bien formada no la cambia.
    """
    raw = raw.strip(_C0_AND_SPACE)
    cut = min((i for i in (raw.find("?"), raw.find("#")) if i != -1), default=len(raw))
    raw = raw[:cut].replace("\\", "/") + raw[cut:]
    special = _SPECIAL_SCHEME_RE.match(raw)
    if special:
        return f"{special.group(1)}://{raw[special.end():]}"
    if raw.startswith("//"):
        return "http://" + raw.lstrip("/")
    if _ANY_SCHEME_RE.match(raw):
        return raw
    return f"http://{raw}"


def _is_ignorable(ch: str) -> bool:
    """
    True si `ch` es invisible, de formato o de control: categoría Cf (U+200B, U+00AD, U+2060,
    U+FEFF...) o Cc, o un carácter que UTS46/nameprep "mapea a nada" (stringprep B.1: selectores
    de variación U+FE00..U+FE0F, U+034F, U+180B..U+180D, U+1806...), que no siempre es Cf.
    """
    return unicodedata.category(ch) in ("Cf", "Cc") or stringprep.in_table_b1(ch)


def _is_trailing_junk(ch: str) -> bool:
    """
    True si `ch` suele quedar pegado al final de una URL copiada de un texto: la puntuación ASCII
    de _TRAILING_PUNCTUATION o cualquier puntuación o símbolo Unicode (categorías P* y S*:
    comillas tipográficas, comillas angulares, rayas, signos invertidos, emoji...), salvo ":"
    (rompería las IPv6 como "2001:db8::").
    """
    return ch != ":" and (ch in _TRAILING_PUNCTUATION or unicodedata.category(ch)[0] in "PS")


def _strip_trailing_junk(text: str) -> str:
    """Quita del final de `text` todos los caracteres para los que _is_trailing_junk es True."""
    end = len(text)
    while end and _is_trailing_junk(text[end - 1]):
        end -= 1
    return text[:end]


def _canonical_host(host: str) -> str:
    """
    Forma canónica de un host para compararlo con listas y marcas, como la vería un navegador.
    En este orden: se eliminan los caracteres ignorables (_is_ignorable: invisibles, de formato
    o de control) para que no queden entre una letra y su marca combinante; NFKC (las letras de
    ancho completo pasan a ASCII); los puntos U+3002/U+FF0E/U+FF61 pasan a "."; minúsculas; y se
    quita la puntuación o símbolo final (_is_trailing_junk: el FQDN "evil.xyz." es "evil.xyz", y
    "evil.xyz,", "evil.xyz)" o "evil.xyz" seguido de una comilla tipográfica también). Solo afecta
    al final del host. No decodifica %XX (eso lo hace el llamador) ni cubre IDNA/punycode.
    """
    host = "".join(ch for ch in host if not _is_ignorable(ch))
    host = unicodedata.normalize("NFKC", host).translate(_UNICODE_DOTS).lower()
    stripped = _strip_trailing_junk(host)
    # Un host hecho solo de puntuación ("%", "/", comillas) no se borra: se conserva para que
    # _is_invalid_host lo marque sospechoso en vez de desaparecer como "sin host". Solo los puntos
    # solos ("." o "..") se vacían, y eso sigue dando el resultado de error NO_ANALIZADO.
    return stripped if stripped or not host.strip(".") else host


def _has_hidden_chars(text: str) -> bool:
    """True si `text` contiene algún carácter ignorable (invisible, de formato o de control; ver _is_ignorable)."""
    return any(_is_ignorable(ch) for ch in text)


def _strip_trailing_tail(text: str) -> str:
    """
    Quita del final de `text` la cola mixta de caracteres ignorables y de puntuación o símbolo
    (_is_ignorable o _is_trailing_junk), p. ej. un emoji con su selector de variación o un ZWSP.
    """
    end = len(text)
    while end and (_is_ignorable(text[end - 1]) or _is_trailing_junk(text[end - 1])):
        end -= 1
    return text[:end]


def _manual_host(raw: str) -> str:
    """
    Extrae el host a mano cuando urlparse no puede leer la URL (corchete desbalanceado o, en
    Python >= 3.11.4, host entre corchetes que no es IPv6 como http://[evil.xyz]). En un
    enlace markdown [texto](destino) pegado entero el navegador abre el DESTINO, no el texto:
    si hay "](" se usa lo que sigue al ÚLTIMO "](" (el ")" final lo quita la puntuación final);
    si no, se ignoran los "[" iniciales. Después quita el esquema, corta la autoridad en el
    primer "/", "?" o "#", descarta el userinfo (lo anterior al último "@", como hace el
    navegador: en https://x]@sitio.com/ el host es sitio.com) y el ":puerto", y lo
    canonicaliza. Devuelve "" si no hay host; no lanza.
    """
    try:
        s = raw.rsplit("](", 1)[1] if "](" in raw else raw.lstrip("[")
        s = _normalize_url(s)
        if "://" in s:
            s = s.split("://", 1)[1]
        authority = re.split(r"[/?#]", s, maxsplit=1)[0]
        # la puntuación final (el ")" del destino markdown) se quita ANTES del ":puerto": si no,
        # "evil.xyz:8080)" conserva el ":" y el host se rechaza como inválido
        host = re.sub(r":\d*$", "", _strip_trailing_junk(authority.rpartition("@")[2]))
        return _canonical_host(unquote(host))
    except Exception:
        return ""


def _parse_host_strict(raw: str) -> Tuple[str, bool]:
    """Núcleo de _parse_host: lee el host y puede lanzar (urlparse lanza ValueError con corchetes desbalanceados)."""
    parsed = urlparse(_normalize_url(raw))
    try:
        _ = parsed.port  # ValueError si el puerto no es numérico o está fuera de rango
        bad_port = False
    except ValueError:
        bad_port = True
    # hostname descarta userinfo (user:pass@), puerto y corchetes IPv6
    host = parsed.hostname
    if host:
        # el navegador decodifica %XX en el host (p. ej. %2e -> "."); solo se decodifica el host
        decoded = unquote(host)
        # los ignorables de la cola final (un emoji con su selector de variación, un ZWSP pegado
        # a un enlace copiado de un texto) no vuelven sospechoso el host; los interiores sí
        core = _strip_trailing_tail(decoded)
        return _canonical_host(decoded), bad_port or _has_hidden_chars(core)
    # sin hostname el dominio es la ruta (p. ej. file:///etc), que empieza por "/" y
    # _is_invalid_host rechaza; por eso aquí no hace falta marcarlo como sospechoso
    return _canonical_host(parsed.path), bad_port


def _parse_host(raw: str) -> Tuple[str, bool]:
    """
    Devuelve (dominio canónico, sospechoso). `sospechoso` es True si el host no se pudo leer
    (urlparse falló y el dominio es la entrada completa en minúsculas), si el puerto no es
    válido (no numérico o fuera de 0-65535; p. ej. "javascript:alert(1)" o "blob:https://x"
    se leen como host:puerto), o si el host decodificado traía caracteres ignorables (invisibles,
    de formato o de control; p. ej. un U+202E, un U+200B, un selector de variación o un %00
    decodificado). Un navegador elimina o rechaza esos caracteres, pero _canonical_host los
    elimina siempre para poder comparar contra la lista negra y las marcas.
    La cola final de ignorables y puntuación del host no lo vuelve sospechoso; los ignorables
    interiores sí.
    Si urlparse falla (típico: un "]" final de markdown deja el corchete desbalanceado) se reintenta
    UNA vez sin la puntuación final de la entrada; si el reintento funciona y deja un host no
    vacío se devuelve tal cual, sin marcar sospechoso solo por esa puntuación. Si tampoco así, se
    extrae el host a mano (_manual_host: enlace markdown [url](url), userinfo con "]") y, si es
    un host válido, se devuelve ese dominio como sospechoso (urlparse no pudo leerlo, pero la
    lista negra, el TLD y las marcas ven el host real). Último recurso: la entrada completa en
    minúsculas como dominio, sospechoso.
    """
    try:
        return _parse_host_strict(raw)
    except Exception:
        trimmed = _strip_trailing_junk(raw)
        if trimmed != raw:
            try:
                retried = _parse_host_strict(trimmed)
                if retried[0]:
                    return retried
            except Exception:
                pass
        manual = _manual_host(raw)
        if manual and not _is_invalid_host(manual):
            return manual, True
        return raw.lower(), True


def _extract_domain(raw: str) -> str:
    """Extrae el dominio canónico (host en minúsculas) de una URL; ante error, devuelve la entrada en minúsculas."""
    return _parse_host(raw)[0]


def _is_invalid_host(domain: str) -> bool:
    """
    True si `domain` no puede ser un host real y se usa para evadir filtros: más largo que
    MAX_DOMAIN_LEN; con espacios, caracteres de control o delimitadores (/ \\ ? # @ % < > ^ | [ ]
    { } " ' `); con una etiqueta vacía interna ("a..b"); con algún carácter que no sea letra,
    marca combinante o número (categorías L*, M*, N*) ni uno de "-._:" (emoji, símbolos, "+", "~",
    "=", "*", "(", ")", ",", ";" dentro del host); o con ":" sin ser una IPv6 válida (las IPv6
    llegan sin corchetes, p. ej. "::1"); o sin ninguna letra ni número (L* o N*: "-", "_", "-.-").
    Siguen siendo válidos "münchen.de", "xn--abc.com", "a_b.com", "123.example.com", "::1".
    """
    if len(domain) > MAX_DOMAIN_LEN or _INVALID_HOST_RE.search(domain) or ".." in domain:
        return True
    if not any(unicodedata.category(ch)[0] in "LN" for ch in domain):
        return True
    if any(ch not in "-._:" and unicodedata.category(ch)[0] not in "LMN" for ch in domain):
        return True
    if ":" in domain:
        try:
            ipaddress.ip_address(domain)
        except ValueError:
            return True
    return False


def _load_blacklist(path) -> frozenset[str]:
    """
    Carga los dominios de la lista negra desde un JSON {"entries": [{"domain": ...}, ...]}.
    Normaliza cada dominio (strip, minúsculas, sin punto final) y descarta entradas inválidas.
    Nunca lanza: ante archivo inexistente, JSON corrupto o estructura inesperada
    devuelve un conjunto vacío (el análisis sigue funcionando solo con heurística).
    """
    try:
        # utf-8-sig tolera el BOM que añade el Bloc de notas de Windows (con utf-8 el JSON no parsea)
        with open(path, "r", encoding="utf-8-sig") as f:
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
    Devuelve False sin trabajar si `domain` supera MAX_DOMAIN_LEN: así el coste queda acotado
    (armar los sufijos de un dominio enorme sería cuadrático).
    """
    if not blacklist or len(domain) > MAX_DOMAIN_LEN:
        return False
    labels = domain.rstrip(".").split(".")
    return any(".".join(labels[i:]) in blacklist for i in range(len(labels) - 1))


def _blacklisted_hops(chain: List[str], blacklist: frozenset) -> List[str]:
    """
    Dominios de los saltos INTERMEDIOS de `chain` (chain[1:-1]; el inicial y el final ya se
    analizan por separado) que están en `blacklist`, sin repetir y en orden de aparición.
    """
    hops: List[str] = []
    for hop in chain[1:-1]:
        domain = _extract_domain(hop)
        if _is_blacklisted(domain, blacklist) and domain not in hops:
            hops.append(domain)
    return hops


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
      protección SSRF: cada salto hace una sola resolución DNS, la IP del destino se valida
      como pública (se rechazan privadas, loopback, link-local, multicast, site-local y las
      NAT64 o IPv4 embebidas no públicas) y se fija para la conexión, solo se permiten los
      puertos de ALLOWED_PORTS (el puerto siempre se envía explícito), y la expansión se corta
      si se supera el presupuesto de tiempo (EXPAND_BUDGET), comprobado antes y después de cada
      HEAD y pasado como timeout al HEAD; no es un límite duro, porque el timeout es por
      operación de socket y el DNS (getaddrinfo) no tiene timeout propio. El destino real se
      vuelve a analizar sin expandir de nuevo, y los saltos intermedios de la cadena también
      se consultan en la lista negra local (el inicial y el final ya se analizan).
    - Detección de typosquatting bancario contra entidades financieras colombianas,
      mediante normalización leetspeak y distancia de edición.

    El host se lee de forma aproximada a como lo haría un navegador, solo en lo que afecta a
    los filtros (no es el estándar WHATWG completo; IDN/punycode no se cubren): "\\" antes de
    "?" o "#" equivale a "/", se completa el esquema (https:evil.xyz, //evil.xyz), se decodifican
    los %XX del host, se eliminan los caracteres ignorables (invisibles, de formato o de control,
    y los que UTS46 mapea a nada, como los selectores de variación), se aplica NFKC, los puntos
    Unicode (U+3002, U+FF0E, U+FF61) valen "." y se quita la puntuación o símbolo pegado al final
    del host (el punto del FQDN, y también , ; ! ) ] } ' " o comillas tipográficas, rayas o emoji
    cuando la URL viene de un texto); esa puntuación final, ASCII o tipográfica, se elimina antes
    de comparar. Un host inválido o con caracteres de evasión (delimitadores, espacios, %,
    caracteres ignorables, etiquetas vacías, más de 253 caracteres, ":" que no sea IPv6, un
    puerto no numérico o fuera de 0-65535, un carácter que no sea letra, marca combinante, número
    ni uno de "-._:" como emoji, símbolos o "+ ~ = * ( ) , ;" dentro del host, o un host que
    urlparse no puede leer) suma 40 puntos y añade un hallazgo; así queda al menos SOSPECHOSO
    (falla cerrado). Como los caracteres de formato se eliminan y dejan el host sospechoso, un
    dominio legítimo con ZWNJ/ZWJ (persa, hindi) o con puntuación interna (p. ej. U+00B7)
    también queda marcado: se acepta para el contexto de fraude en Colombia (SMS).
    Casos particulares:
    - la cola final de ignorables y puntuación (un emoji con su selector de variación, un ZWSP)
      no vuelve sospechoso el host; los ignorables interiores sí;
    - una entrada con "](" (enlace markdown [texto](destino) o "](" en ruta/fragmento) se divide en
      segmentos (hasta 4: los 2 primeros y los 2 últimos), se analiza cada segmento no vacío sin
      sumar puntos por ser markdown y se devuelve el resultado de mayor riesgo; un userinfo con "]"
      (https://x]@sitio.com/), que urlparse no puede leer, se analiza con el host real y queda
      sospechoso;
    - los controles C0 y espacios iniciales o finales se ignoran, como hace el navegador;
    - una URL de más de MAX_URL_LEN (8192) caracteres suma 40 puntos y no se desenrolla; el host se
      lee solo de los primeros 8192 caracteres, y si la autoridad no se cierra dentro de esa ventana
      el host también se marca como sospechoso.

    Args:
        raw_url: URL o dominio a analizar (se acepta sin esquema).
        expand: si es True, desenrolla los acortadores detectados. Debe ser bool.
        blacklist: conjunto (set o frozenset) de dominios ya normalizados (minúsculas, sin punto
            final) contra el que se compara el dominio; un set se convierte a frozenset. Si es
            None se usa la lista local de data/url_blacklist.json (BLACKLIST_PATH), leída una vez
            y cacheada; si ese archivo falta o es inválido la lista queda vacía. Un frozenset
            vacío desactiva la consulta y deja solo la heurística.

    Raises:
        TypeError: si `expand` no es bool, o si `blacklist` no es None, set ni frozenset.

    Returns:
        Diccionario con las claves:
        - status: "success", o "error" si la entrada está vacía, no es texto o no contiene
          un host (por ejemplo "http://"); en ese caso el veredicto es NO_ANALIZADO.
        - original_url / expanded_url: URL recibida (sin espacios en los extremos) y URL
          final tras el desenrollado; en un resultado de error siempre son str ("" si la
          entrada no era texto).
        - domain: dominio analizado, ya canonicalizado como se describe arriba.
        - is_suspicious_tld / is_shortener / is_typosquatting: indicadores booleanos.
        - is_blacklisted: True si el dominio, el destino de un acortador desenrollado o
          alguno de sus saltos intermedios está en la lista negra.
        - impersonated_brand: entidad suplantada, o None.
        - risk_score: puntaje de riesgo entre 0 y 100.
        - verdict: "SEGURO", "SOSPECHOSO", "MALICIOSO" o "NO_ANALIZADO".
        - findings: lista de hallazgos legibles.
        - redirect_chain: cadena de URLs recorridas durante el desenrollado.
        - expansion_error: motivo del fallo al expandir, o None.
        - telemetry: mediciones de esta llamada, en milisegundos (time.perf_counter, redondeadas
          a 2 decimales) y también presente cuando la entrada es inválida:
            - latency_ms: tiempo total de analyze_url (en la primera llamada incluye la carga
              de la lista negra por defecto).
            - expansion_ms: tiempo de la llamada a _expand_url (la parte de red), o None si no
              hubo desenrollado (no es acortador o expand es False). No incluye el re-análisis
              del destino.
    """
    if not isinstance(expand, bool):
        raise TypeError("expand debe ser bool")
    if blacklist is not None and not isinstance(blacklist, (set, frozenset)):
        # un str haría que `in` buscara subcadenas; list/tuple/bytes tampoco son un conjunto de dominios
        raise TypeError("blacklist debe ser un set/frozenset de dominios o None")
    if isinstance(blacklist, set):
        blacklist = frozenset(blacklist)
    # perf_counter mide duraciones; en Windows con Python < 3.13 monotonic tiene resolución de ~15 ms
    t0 = time.perf_counter()
    core = _analyze_url(raw_url, expand, blacklist)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    # No muta el resultado del núcleo, para que una caché futura sobre _analyze_url no se contamine.
    # Ojo: findings y redirect_chain siguen siendo listas compartidas (una caché deberá copiarlas).
    return {**core, "telemetry": {**core["telemetry"], "latency_ms": latency_ms}}


def _error_result(raw_url: Any, finding: str) -> Dict[str, Any]:
    """Resultado NO_ANALIZADO con las mismas claves que uno de éxito; las URLs siempre son str (JSON-seguro)."""
    url = raw_url if isinstance(raw_url, str) else ""
    return {
        "status": "error",
        "original_url": url,
        "expanded_url": url,
        "domain": "",
        "is_suspicious_tld": False,
        "is_shortener": False,
        "is_typosquatting": False,
        "is_blacklisted": False,
        "impersonated_brand": None,
        "risk_score": 0,
        "verdict": "NO_ANALIZADO",
        "findings": [finding],
        "redirect_chain": [],
        "expansion_error": None,
        "telemetry": {"expansion_ms": None}
    }


def _analyze_url(raw_url: str, expand: bool, blacklist: Optional[frozenset]) -> Dict[str, Any]:
    """Núcleo del análisis de URL; lo invocan analyze_url y la recursión del desenrollado."""
    if not isinstance(raw_url, str) or not raw_url.strip():
        return _error_result(raw_url, "Entrada vacía o inválida: no hay URL para analizar")
    raw_url = raw_url.strip()
    if "](" in raw_url:
        parts = raw_url.split("](")
        if len(parts) > 4:
            parts = parts[:2] + parts[-2:]
        segments = [s for p in parts if (s := p.rstrip(")] \t\r\n").lstrip("["))]
        if not segments:
            return _error_result(raw_url, "No se pudo extraer un host de la entrada")
        if blacklist is None:
            blacklist = _get_blacklist()
        results = [_analyze_url(seg, expand, blacklist) for seg in segments]
        best = max(results, key=lambda r: (r["status"] == "success", r["risk_score"]))
        expanded = (
            raw_url
            if best["expanded_url"] == best["original_url"]
            else best["expanded_url"]
        )
        return {
            **best,
            "original_url": raw_url,
            "expanded_url": expanded,
            "findings": list(best["findings"]),
        }
    # el recorte se usa SOLO para leer el host (acota el coste de NFKC); original_url,
    # redirect_chain y expanded_url conservan la URL completa
    url_too_long = len(raw_url) > MAX_URL_LEN
    window = raw_url[:MAX_URL_LEN]
    after_scheme = window.split("://", 1)[1] if "://" in window else window
    unclosed_authority = url_too_long and not any(c in after_scheme for c in "/?#\\")
    domain, suspicious_host = _parse_host(window)
    if not domain:
        return _error_result(raw_url, "No se pudo extraer un host de la entrada")
    if blacklist is None:
        blacklist = _get_blacklist()
    findings = []
    risk_score = 0
    expanded_url = raw_url
    redirect_chain = [raw_url]
    expansion_error = None
    expansion_ms = None  # None = no hubo red (distinto de 0 ms)
    # por encima del límite no se corren los chequeos costosos (lista negra y typosquatting)
    domain_too_long = len(domain) > MAX_DOMAIN_LEN

    # 0. Lista negra local de URLs fraudulentas reportadas
    is_blacklisted = not domain_too_long and _is_blacklisted(domain, blacklist)
    if is_blacklisted:
        risk_score += 100
        findings.append(f"Dominio en lista negra local de URLs fraudulentas ({domain})")

    # 0b. Host inválido o con caracteres de evasión: falla cerrado (sospechoso)
    if suspicious_host or _is_invalid_host(domain):
        risk_score += 40
        findings.append(f"Host inválido o con caracteres de evasión ({domain[:80]!r})")
    elif unclosed_authority:
        risk_score += 40
        findings.append(
            "Host inválido o con caracteres de evasión (autoridad más larga que la ventana de análisis)"
        )

    # 0c. URL demasiado larga: sospechosa y sin desenrollar (casi ninguna URL legítima de SMS supera MAX_URL_LEN)
    if url_too_long:
        risk_score += 40
        findings.append(f"URL demasiado larga ({len(raw_url)} caracteres)")

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
    brand = None if domain_too_long else _detect_brand(domain)
    if brand:
        is_typosquatting = True
        impersonated_brand = brand
        risk_score += 60
        findings.append(f"Alerta de Typosquatting: El dominio '{domain}' imita ilícitamente a '{brand}'")

    # 3b. Desenrollado del acortador y análisis del destino real
    if is_shortener and expand and not url_too_long:
        # misma cadena normalizada que usa _parse_host; los %XX del host no se decodifican
        # para el HEAD (un host con %XX no resuelve y la expansión falla cerrada)
        start = _normalize_url(raw_url)
        t_expand = time.perf_counter()
        expanded_url, redirect_chain, expansion_error = _expand_url(start)
        expansion_ms = round((time.perf_counter() - t_expand) * 1000, 2)
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
            # el inicial y el final ya puntuaron arriba: aquí solo los saltos del medio
            for hop in _blacklisted_hops(redirect_chain, blacklist):
                if hop not in (domain, final["domain"]):
                    is_blacklisted, risk_score = True, risk_score + 100
                    findings.append(f"Salto intermedio en lista negra local ({hop})")

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
        "expansion_error": expansion_error,
        # solo la red de ESTE nivel: la telemetría del destino (final) no se suma ni se propaga
        "telemetry": {"expansion_ms": expansion_ms}
    }
