"""
Pruebas de saltos de red, redirecciones y lista negra para UrlSandbox.
Reto Agente 2026 - SentinelGuard AI - Equipo Codixia
"""

import src.tools.url_sandbox as sandbox


def _fake_head(routes):
    """Simula _head_request devolviendo tuplas (status, location) segun la URL."""
    def _head(url, timeout=3, **kwargs):
        return routes.get(url, (200, None))
    return _head


def test_intermediate_hop_in_blacklist(monkeypatch):
    """Un salto intermedio listado marca is_blacklisted=True, MALICIOSO y genera hallazgo especifico."""
    routes = {
        "http://rb.gy": (301, "https://listado.site/r"),
        "https://rb.gy": (301, "https://listado.site/r"),
        "https://listado.site/r": (301, "https://limpio.com/"),
        "https://limpio.com/": (200, None),
    }
    monkeypatch.setattr(sandbox, "_head_request", _fake_head(routes))

    res = sandbox.analyze_url("rb.gy", expand=True, blacklist=frozenset({"listado.site"}))

    assert res["status"] == "success"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    assert res["risk_score"] == 100
    assert "Salto intermedio en lista negra local (listado.site)" in res["findings"]
    assert res["expanded_url"] == "https://limpio.com/"
    assert res["redirect_chain"] == ["http://rb.gy", "https://listado.site/r", "https://limpio.com/"]


def test_intermediate_hop_empty_blacklist(monkeypatch):
    """Con lista negra vacia el salto intermedio no se marca como listado ni es MALICIOSO por esa causa."""
    routes = {
        "http://rb.gy": (301, "https://listado.site/r"),
        "https://rb.gy": (301, "https://listado.site/r"),
        "https://listado.site/r": (301, "https://limpio.com/"),
        "https://limpio.com/": (200, None),
    }
    monkeypatch.setattr(sandbox, "_head_request", _fake_head(routes))

    res = sandbox.analyze_url("rb.gy", expand=True, blacklist=frozenset())

    assert res["status"] == "success"
    assert res["is_blacklisted"] is False
    assert res["verdict"] == "SOSPECHOSO"
    assert "Salto intermedio en lista negra local (listado.site)" not in res["findings"]
    assert res["expanded_url"] == "https://limpio.com/"


def test_intermediate_hop_no_double_counting_when_final_also_listed(monkeypatch):
    """No duplica el reporte si el destino final pertenece al mismo dominio que el salto intermedio."""
    routes = {
        "http://rb.gy": (301, "https://listado.site/r"),
        "https://rb.gy": (301, "https://listado.site/r"),
        "https://listado.site/r": (301, "https://listado.site/final"),
        "https://listado.site/final": (200, None),
    }
    monkeypatch.setattr(sandbox, "_head_request", _fake_head(routes))

    res = sandbox.analyze_url("rb.gy", expand=True, blacklist=frozenset({"listado.site"}))

    assert res["status"] == "success"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    assert "Dominio en lista negra local de URLs fraudulentas (listado.site)" in res["findings"]
    assert "Salto intermedio en lista negra local (listado.site)" not in res["findings"]
    assert sum("lista negra" in f for f in res["findings"]) == 1


def test_intermediate_hop_different_final_both_listed(monkeypatch):
    """Reporta ambos dominios si el salto intermedio y el destino final estan listados y son distintos."""
    routes = {
        "http://rb.gy": (301, "https://intermedio.site/r"),
        "https://rb.gy": (301, "https://intermedio.site/r"),
        "https://intermedio.site/r": (301, "https://final.site/login"),
        "https://final.site/login": (200, None),
    }
    monkeypatch.setattr(sandbox, "_head_request", _fake_head(routes))

    res = sandbox.analyze_url(
        "rb.gy",
        expand=True,
        blacklist=frozenset({"intermedio.site", "final.site"}),
    )

    assert res["status"] == "success"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    assert "Dominio en lista negra local de URLs fraudulentas (final.site)" in res["findings"]
    assert "Salto intermedio en lista negra local (intermedio.site)" in res["findings"]


def test_blacklisted_hops_direct_lengths_and_subdomains():
    """Verifica _blacklisted_hops directo con cadenas de longitud 0, 1, 2, 3 y 4 elementos."""
    blacklist = frozenset({"listado.site", "malicioso.org"})

    # Longitud 0: cadena vacia
    assert sandbox._blacklisted_hops([], blacklist) == []

    # Longitud 1: solo salto inicial (con skip no cuenta)
    assert sandbox._blacklisted_hops(["https://listado.site/"], blacklist, skip={"listado.site"}) == []
    # Sin skip evalúa todos los elementos
    assert sandbox._blacklisted_hops(["https://listado.site/"], blacklist) == ["listado.site"]

    # Longitud 2: salto inicial y salto final con skip no cuentan
    assert sandbox._blacklisted_hops(
        ["https://listado.site/inicio", "https://malicioso.org/fin"],
        blacklist,
        skip={"listado.site", "malicioso.org"},
    ) == []

    # Longitud 3: salto intermedio listado (cuenta con skip de extremos)
    assert sandbox._blacklisted_hops(
        ["https://rb.gy/x", "https://listado.site/r", "https://limpio.com/"],
        blacklist,
        skip={"rb.gy", "limpio.com"},
    ) == ["listado.site"]

    # Longitud 3: subdominios de un dominio listado cuentan
    assert sandbox._blacklisted_hops(
        ["https://rb.gy/x", "https://sub.listado.site/r", "https://limpio.com/"],
        blacklist,
        skip={"rb.gy", "limpio.com"},
    ) == ["sub.listado.site"]
    assert sandbox._blacklisted_hops(
        ["https://rb.gy/x", "https://a.b.listado.site/r", "https://limpio.com/"],
        blacklist,
        skip={"rb.gy", "limpio.com"},
    ) == ["a.b.listado.site"]

    # Longitud 3: salto intermedio limpio no cuenta aunque extremos esten listados
    assert sandbox._blacklisted_hops(
        ["https://listado.site/inicio", "https://limpio.com/r", "https://malicioso.org/fin"],
        blacklist,
        skip={"listado.site", "malicioso.org"},
    ) == []

    # Longitud 4: dos saltos intermedios listados en orden y sin extremos
    assert sandbox._blacklisted_hops(
        [
            "https://inicio.com/0",
            "https://listado.site/1",
            "https://sub.malicioso.org/2",
            "https://fin.com/3",
        ],
        blacklist,
        skip={"inicio.com", "fin.com"},
    ) == ["listado.site", "sub.malicioso.org"]

    # Longitud 4: extremos listados no cuentan, solo intermedios
    assert sandbox._blacklisted_hops(
        [
            "https://listado.site/inicio",
            "https://sub.listado.site/1",
            "https://limpio.com/2",
            "https://malicioso.org/fin",
        ],
        blacklist,
        skip={"listado.site", "malicioso.org"},
    ) == ["sub.listado.site"]

    # Longitud 4: desduplicacion de dominios repetidos en saltos intermedios
    assert sandbox._blacklisted_hops(
        [
            "https://inicio.com/0",
            "https://listado.site/1",
            "https://listado.site/2",
            "https://fin.com/3",
        ],
        blacklist,
        skip={"inicio.com", "fin.com"},
    ) == ["listado.site"]


def test_location_with_backslash_normalized(monkeypatch):
    """Location con barra invertida se normaliza y el siguiente _head_request recibe la URL limpia."""
    recorded_calls = []

    def mock_head(url, timeout=3, **kwargs):
        recorded_calls.append(url)
        if url == "https://bit.ly/x":
            return (301, "https://listado.site\\@atacante.com/")
        return (200, None)

    monkeypatch.setattr(sandbox, "_head_request", mock_head)

    expanded_url, chain, error = sandbox._expand_url("https://bit.ly/x")

    assert error is None
    assert recorded_calls == [
        "https://bit.ly/x",
        "https://listado.site/@atacante.com/",
    ]
    assert expanded_url == "https://listado.site/@atacante.com/"
    assert chain == [
        "https://bit.ly/x",
        "https://listado.site/@atacante.com/",
    ]


def test_location_scheme_relative_and_relative_path(monkeypatch):
    """Location scheme-relative (//host/ruta) y relativa (/ruta) se resuelven correctamente."""
    recorded_calls = []

    def mock_head(url, timeout=3, **kwargs):
        recorded_calls.append(url)
        if url == "https://bit.ly/scheme":
            return (301, "//listado.site/x")
        if url == "https://listado.site/x":
            return (301, "/ruta/final")
        return (200, None)

    monkeypatch.setattr(sandbox, "_head_request", mock_head)

    expanded_url, chain, error = sandbox._expand_url("https://bit.ly/scheme")

    assert error is None
    assert recorded_calls == [
        "https://bit.ly/scheme",
        "https://listado.site/x",
        "https://listado.site/ruta/final",
    ]
    assert expanded_url == "https://listado.site/ruta/final"
    assert chain == [
        "https://bit.ly/scheme",
        "https://listado.site/x",
        "https://listado.site/ruta/final",
    ]


def test_redirect_loop_detected_with_normalized_url(monkeypatch):
    """Bucle de redirecciones se detecta inmediatamente comparando contra la URL normalizada."""
    recorded_calls = []

    def mock_head(url, timeout=3, **kwargs):
        recorded_calls.append(url)
        if url == "https://bit.ly/loop":
            return (301, "https://bit.ly\\loop")
        return (200, None)

    monkeypatch.setattr(sandbox, "_head_request", mock_head)

    expanded_url, chain, error = sandbox._expand_url("https://bit.ly/loop")

    assert error == "Bucle de redirecciones"
    assert recorded_calls == ["https://bit.ly/loop"]
    assert chain == ["https://bit.ly/loop"]
    assert expanded_url == "https://bit.ly/loop"


def test_redirect_loop_multi_hop_normalized(monkeypatch):
    """Bucle de varios saltos con contrabarra se detecta con URL normalizada en cadena."""
    routes = {
        "https://bit.ly/start": (301, "https://example.com/inter\\hop"),
        "https://example.com/inter/hop": (301, "https://bit.ly\\start"),
    }
    monkeypatch.setattr(sandbox, "_head_request", _fake_head(routes))

    expanded_url, chain, error = sandbox._expand_url("https://bit.ly/start")

    assert error == "Bucle de redirecciones"
    assert chain == [
        "https://bit.ly/start",
        "https://example.com/inter/hop",
    ]
    assert expanded_url == "https://example.com/inter/hop"


def test_location_with_leading_double_backslash(monkeypatch):
    """Location con dos barras invertidas iniciales resuelve a host y ruta en http(s)."""
    recorded_calls = []

    def mock_head(url, timeout=3, **kwargs):
        recorded_calls.append(url)
        if url == "http://bit.ly/x":
            loc = chr(92) * 2 + "host.cc" + chr(92) + "login"
            return (301, loc)
        return (200, None)

    monkeypatch.setattr(sandbox, "_head_request", mock_head)

    expanded_url, chain, error = sandbox._expand_url("http://bit.ly/x")

    assert error is None
    assert expanded_url == "http://host.cc/login"
    assert recorded_calls == ["http://bit.ly/x", "http://host.cc/login"]


def test_location_with_scheme_and_double_backslash(monkeypatch):
    """Location con 'https:<2 barras invertidas>host...' sigue funcionando correctamente."""
    recorded_calls = []

    def mock_head(url, timeout=3, **kwargs):
        recorded_calls.append(url)
        if url == "http://bit.ly/scheme":
            loc = "https:" + chr(92) * 2 + "host.cc" + chr(92) + "login"
            return (301, loc)
        return (200, None)

    monkeypatch.setattr(sandbox, "_head_request", mock_head)

    expanded_url, chain, error = sandbox._expand_url("http://bit.ly/scheme")

    assert error is None
    assert expanded_url == "https://host.cc/login"
    assert recorded_calls == ["http://bit.ly/scheme", "https://host.cc/login"]


def test_location_backslash_in_query_preserved(monkeypatch):
    """La barra invertida en la query de Location no se toca ni se reemplaza."""
    recorded_calls = []

    def mock_head(url, timeout=3, **kwargs):
        recorded_calls.append(url)
        if url == "http://bit.ly/query":
            loc = chr(92) * 2 + "host.cc" + chr(92) + "login?param=a" + chr(92) + "b"
            return (301, loc)
        return (200, None)

    monkeypatch.setattr(sandbox, "_head_request", mock_head)

    expanded_url, chain, error = sandbox._expand_url("http://bit.ly/query")

    assert error is None
    assert expanded_url == "http://host.cc/login?param=a" + chr(92) + "b"
    assert recorded_calls == [
        "http://bit.ly/query",
        "http://host.cc/login?param=a" + chr(92) + "b",
    ]


def test_blacklisted_hops_caps_hop_length_to_max_url_len(monkeypatch):
    """Verifica que _blacklisted_hops recorte el salto a MAX_URL_LEN antes de extraer el dominio."""
    recorded_lengths = []
    real_extract = sandbox._extract_domain

    def spy_extract(raw: str) -> str:
        recorded_lengths.append(len(raw))
        return real_extract(raw)

    monkeypatch.setattr(sandbox, "_extract_domain", spy_extract)

    overlong_hop = "https://malicioso.org/" + ("a" * (sandbox.MAX_URL_LEN + 10000))
    hops = sandbox._blacklisted_hops([overlong_hop], frozenset({"malicioso.org"}))

    assert len(recorded_lengths) == 1
    assert recorded_lengths[0] <= sandbox.MAX_URL_LEN
    assert recorded_lengths[0] == sandbox.MAX_URL_LEN
    assert hops == ["malicioso.org"]
