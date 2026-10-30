"""
Pruebas Unitarias para UrlSandbox
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
"""

import json

import src.tools.url_sandbox as sandbox
from src.tools.url_sandbox import (
    analyze_url,
    _head_request as real_head_request,
    _is_public_host as real_is_public_host,
)

def test_analyze_official_url():
    url = "https://www.bancolombia.com/personas"
    res = analyze_url(url)
    assert res["status"] == "success"
    assert res["is_typosquatting"] is False
    assert res["verdict"] == "SEGURO"

def test_analyze_typosquatting_url():
    url = "https://bancolombia-seguro-login.xyz/recuperar"
    res = analyze_url(url)
    assert res["status"] == "success"
    assert res["is_typosquatting"] is True
    assert res["impersonated_brand"] == "bancolombia"
    assert res["verdict"] == "MALICIOSO"

def test_analyze_shortener():
    url = "https://bit.ly/3xXyZ"
    res = analyze_url(url)
    assert res["status"] == "success"
    assert res["is_shortener"] is True


def test_typosquatting_leetspeak_zero():
    res = analyze_url("https://banc0lombia-seguridad.cc")
    assert res["is_typosquatting"] is True
    assert res["impersonated_brand"] == "bancolombia"
    assert res["verdict"] == "MALICIOSO"

def test_typosquatting_repeated_letters():
    res = analyze_url("https://nequii-pagos.com")
    assert res["is_typosquatting"] is True
    assert res["impersonated_brand"] == "nequi"

def test_typosquatting_brand_in_subdomain_of_foreign_domain():
    res = analyze_url("https://bancolombia.com.evil.xyz/login")
    assert res["is_typosquatting"] is True
    assert res["impersonated_brand"] == "bancolombia"

def test_typosquatting_edit_distance():
    res = analyze_url("https://davivienna.com")
    assert res["is_typosquatting"] is True
    assert res["impersonated_brand"] == "davivienda"

def test_official_domains_are_not_typosquatting():
    for url in (
        "https://www.bancolombia.com",
        "https://nequi.com.co",
        "https://app.davivienda.com/personas",
        "https://www.daviplata.com",
    ):
        res = analyze_url(url)
        assert res["is_typosquatting"] is False, url
        assert res["verdict"] == "SEGURO", url

def test_unrelated_domains_are_not_typosquatting():
    for url in ("https://google.com", "https://github.com", "https://banco.com", "https://lunes.com"):
        assert analyze_url(url)["is_typosquatting"] is False, url


def _fake_head(routes):
    """Simula _head_request: routes mapea url -> (status, location)."""
    def _head(url, timeout=3):
        return routes.get(url, (200, None))
    return _head

def test_shortener_exact_host_match():
    assert analyze_url("https://bit.ly/abc", expand=False)["is_shortener"] is True
    assert analyze_url("https://www.bit.ly/abc", expand=False)["is_shortener"] is True
    assert analyze_url("https://obit.lyrics.com", expand=False)["is_shortener"] is False

def test_expand_single_redirect_to_typosquatting(monkeypatch):
    monkeypatch.setattr(sandbox, "_head_request", _fake_head({
        "https://bit.ly/x": (301, "https://banc0lombia-seguro.xyz/login"),
    }))
    res = analyze_url("https://bit.ly/x")
    assert res["expanded_url"] == "https://banc0lombia-seguro.xyz/login"
    assert res["redirect_chain"] == ["https://bit.ly/x", "https://banc0lombia-seguro.xyz/login"]
    assert res["is_typosquatting"] is True
    assert res["impersonated_brand"] == "bancolombia"
    assert res["expansion_error"] is None
    assert res["verdict"] == "MALICIOSO"

def test_expand_two_hops(monkeypatch):
    monkeypatch.setattr(sandbox, "_head_request", _fake_head({
        "https://bit.ly/x": (302, "https://tinyurl.com/y"),
        "https://tinyurl.com/y": (301, "https://example.org/final"),
    }))
    res = analyze_url("https://bit.ly/x")
    assert res["expanded_url"] == "https://example.org/final"
    assert len(res["redirect_chain"]) == 3

def test_expand_relative_location(monkeypatch):
    monkeypatch.setattr(sandbox, "_head_request", _fake_head({
        "https://bit.ly/x": (301, "/otra/ruta"),
    }))
    res = analyze_url("https://bit.ly/x")
    assert res["expanded_url"] == "https://bit.ly/otra/ruta"

def test_expand_redirect_loop(monkeypatch):
    monkeypatch.setattr(sandbox, "_head_request", _fake_head({
        "https://bit.ly/a": (301, "https://bit.ly/b"),
        "https://bit.ly/b": (301, "https://bit.ly/a"),
    }))
    res = analyze_url("https://bit.ly/a")
    assert res["expansion_error"] == "Bucle de redirecciones"

def test_expand_too_many_redirects(monkeypatch):
    monkeypatch.setattr(sandbox, "_head_request", lambda url, timeout=3: (301, url + "x"))
    res = analyze_url("https://bit.ly/a")
    assert "Demasiadas redirecciones" in res["expansion_error"]
    assert len(res["redirect_chain"]) == sandbox.MAX_REDIRECTS + 1

def test_expand_network_error_does_not_raise():
    # conftest bloquea la red: _head_request lanza OSError
    res = analyze_url("https://bit.ly/3xXyZ")
    assert res["status"] == "success"
    assert res["expanded_url"] == "http://bit.ly/3xXyZ" or res["expanded_url"] == "https://bit.ly/3xXyZ"
    assert "No se pudo expandir" in res["expansion_error"]
    assert res["verdict"] == "SOSPECHOSO"

def test_expand_timeout_does_not_raise(monkeypatch):
    def _timeout(url, timeout=3):
        raise TimeoutError("timeout")
    monkeypatch.setattr(sandbox, "_head_request", _timeout)
    res = analyze_url("https://bit.ly/x")
    assert "TimeoutError" in res["expansion_error"]
    assert res["verdict"] == "SOSPECHOSO"

def test_non_shortener_never_does_network(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("no debe hacer red")
    monkeypatch.setattr(sandbox, "_head_request", _boom)
    res = analyze_url("https://www.bancolombia.com")
    assert res["redirect_chain"] == ["https://www.bancolombia.com"]
    assert res["expansion_error"] is None

def test_ssrf_blocks_private_redirect_target(monkeypatch):
    monkeypatch.setattr(sandbox, "_is_public_host", real_is_public_host)
    monkeypatch.setattr(sandbox, "_head_request", _fake_head({
        "https://8.8.8.8/x": (301, "http://127.0.0.1/admin"),
    }))
    start, chain, err = sandbox._expand_url("https://8.8.8.8/x")
    assert "SSRF" in err
    assert chain == ["https://8.8.8.8/x", "http://127.0.0.1/admin"]

def test_is_public_host_literals():
    assert real_is_public_host("127.0.0.1") is False
    assert real_is_public_host("192.168.1.10") is False
    assert real_is_public_host("10.0.0.5") is False
    assert real_is_public_host("169.254.169.254") is False
    assert real_is_public_host("8.8.8.8") is True

def test_expand_rejects_non_http_scheme():
    _, _, err = sandbox._expand_url("file:///etc/passwd")
    assert err == "Esquema o host no permitido"


def test_userinfo_does_not_spoof_official_domain():
    res = analyze_url("https://www.bancolombia.com:pass@evil.xyz/login", expand=False)
    assert res["domain"] == "evil.xyz"
    assert res["verdict"] != "SEGURO"

def test_userinfo_with_official_name_as_user():
    res = analyze_url("https://www.bancolombia.com@evil.com/", expand=False)
    assert res["domain"] == "evil.com"

def test_domain_strips_port_and_ipv6_brackets():
    assert analyze_url("https://www.bancolombia.com:443/x", expand=False)["verdict"] == "SEGURO"
    assert analyze_url("http://[::1]/x", expand=False)["domain"] == "::1"

def test_expand_time_budget(monkeypatch):
    monkeypatch.setattr(sandbox, "EXPAND_BUDGET", -1)
    _, _, err = sandbox._expand_url("https://bit.ly/x")
    assert "Presupuesto de tiempo agotado" in err


def test_empty_input_is_not_safe():
    for bad in ("", "   ", None):
        res = analyze_url(bad)
        assert res["status"] == "error"
        assert res["verdict"] == "NO_ANALIZADO"

def test_non_web_port_blocked():
    _, chain, err = sandbox._expand_url("http://8.8.8.8:22/")
    assert err == "Puerto no permitido (22)"
    _, _, err = sandbox._expand_url("http://8.8.8.8:6379/")
    assert err == "Puerto no permitido (6379)"

def test_head_request_blocks_rebinding_to_private_ip(monkeypatch):
    # Segunda resolución devuelve IP privada: el request real debe abortar antes de conectar
    monkeypatch.setattr(sandbox, "_resolve_public_ip", lambda host: None)
    def _no_connect(*a, **k):
        raise AssertionError("no debe abrir socket")
    monkeypatch.setattr(sandbox.socket, "create_connection", _no_connect)
    try:
        real_head_request("http://evil.example/x")
        assert False, "debía lanzar PermissionError"
    except PermissionError as e:
        assert "SSRF" in str(e)

def test_head_request_connects_to_validated_ip_only(monkeypatch):
    seen = {}
    def _fake_connect(addr, timeout=None):
        seen["addr"] = addr
        raise OSError("stop")
    monkeypatch.setattr(sandbox, "_resolve_public_ip", lambda host: "93.184.216.34")
    monkeypatch.setattr(sandbox.socket, "create_connection", _fake_connect)
    try:
        real_head_request("http://rebind.example/x")
    except OSError:
        pass
    assert seen["addr"] == ("93.184.216.34", 80)


# --- Lista negra local ---

_LISTED = "simit-multas-colombia.site"
_BLACKLIST = frozenset({_LISTED})
_BLACKLIST_FINDING = f"Dominio en lista negra local de URLs fraudulentas ({_LISTED})"

def test_blacklist_exact_domain_is_malicious():
    res = analyze_url(f"https://{_LISTED}/pagos", blacklist=_BLACKLIST)
    assert res["status"] == "success"
    assert res["verdict"] == "MALICIOSO"
    assert res["is_blacklisted"] is True
    assert res["risk_score"] == 100
    assert _BLACKLIST_FINDING in res["findings"]
    assert res["findings"][0] == _BLACKLIST_FINDING

def test_blacklist_matches_subdomain_and_www():
    for url in (
        f"https://login.{_LISTED}/x",
        f"https://www.{_LISTED}",
        f"https://a.b.{_LISTED}",
        f"HTTPS://{_LISTED.upper()}/PAGOS",
        f"https://{_LISTED}./x",
        f"{_LISTED}:8443/x",
    ):
        res = analyze_url(url, blacklist=_BLACKLIST)
        assert res["is_blacklisted"] is True, url
        assert res["verdict"] == "MALICIOSO", url

def test_blacklist_requires_label_boundary():
    res = analyze_url("https://xsimit-multas-colombia.site/pagos", blacklist=_BLACKLIST)
    assert res["is_blacklisted"] is False
    assert not any("lista negra" in f for f in res["findings"])

def test_blacklist_empty_set_means_heuristics_only():
    res = analyze_url(f"https://{_LISTED}/pagos", blacklist=frozenset())
    assert res["is_blacklisted"] is False
    assert res["verdict"] == "SEGURO"
    assert res["findings"] == []

def test_blacklist_applies_to_shortener_destination(monkeypatch):
    monkeypatch.setattr(sandbox, "_head_request", _fake_head({
        "https://bit.ly/x": (301, f"https://{_LISTED}/pagos"),
    }))
    res = analyze_url("https://bit.ly/x", blacklist=_BLACKLIST)
    assert res["domain"] == "bit.ly"
    assert res["expanded_url"] == f"https://{_LISTED}/pagos"
    assert res["is_shortener"] is True
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    assert _BLACKLIST_FINDING in res["findings"]

def test_blacklist_shortener_destination_uses_the_same_injected_list(monkeypatch):
    # Con lista vacía el destino no se marca: la recursión reenvía la lista inyectada,
    # no vuelve a la lista por defecto (que sí contiene el dominio).
    monkeypatch.setattr(sandbox, "_get_blacklist", lambda: _BLACKLIST)
    monkeypatch.setattr(sandbox, "_head_request", _fake_head({
        "https://bit.ly/x": (301, f"https://{_LISTED}/pagos"),
    }))
    res = analyze_url("https://bit.ly/x", blacklist=frozenset())
    assert res["expanded_url"] == f"https://{_LISTED}/pagos"
    assert res["is_blacklisted"] is False
    assert res["verdict"] == "SOSPECHOSO"

def test_blacklist_default_is_resolved_once_and_wired(monkeypatch):
    calls = []
    def _fake_get():
        calls.append(1)
        return frozenset({"ejemplo-reportado.site"})
    monkeypatch.setattr(sandbox, "_get_blacklist", _fake_get)
    res = analyze_url("https://ejemplo-reportado.site")
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    assert calls == [1]

def test_blacklist_default_resolved_once_even_when_unrolling_shortener(monkeypatch):
    calls = []
    def _fake_get():
        calls.append(1)
        return frozenset({"ejemplo-reportado.site"})
    monkeypatch.setattr(sandbox, "_get_blacklist", _fake_get)
    monkeypatch.setattr(sandbox, "_head_request", _fake_head({
        "https://bit.ly/x": (301, "https://ejemplo-reportado.site/a"),
    }))
    res = analyze_url("https://bit.ly/x")
    assert res["is_blacklisted"] is True
    assert calls == [1]

def test_blacklist_flag_present_in_error_result():
    res = analyze_url("")
    assert res["status"] == "error"
    assert res["is_blacklisted"] is False

def test_blacklist_flag_false_for_clean_url():
    res = analyze_url("https://www.bancolombia.com/personas", blacklist=_BLACKLIST)
    assert res["is_blacklisted"] is False
    assert res["verdict"] == "SEGURO"


def _write_blacklist(tmp_path, payload):
    path = tmp_path / "blacklist.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path

def test_load_blacklist_valid_file_is_normalized(tmp_path):
    path = _write_blacklist(tmp_path, {
        "updated": "2026-10-30",
        "entries": [
            {"domain": "  Ejemplo-Uno.SITE. ", "origin": "x"},
            {"domain": "otro.xyz"},
            {"domain": "OTRO.xyz"},
        ],
    })
    result = sandbox._load_blacklist(path)
    assert isinstance(result, frozenset)
    assert result == frozenset({"ejemplo-uno.site", "otro.xyz"})

def test_load_blacklist_missing_file_returns_empty(tmp_path):
    assert sandbox._load_blacklist(tmp_path / "no_existe.json") == frozenset()

def test_load_blacklist_directory_returns_empty(tmp_path):
    assert sandbox._load_blacklist(tmp_path) == frozenset()

def test_load_blacklist_corrupt_json_returns_empty(tmp_path):
    path = tmp_path / "blacklist.json"
    path.write_text("{ esto no es json", encoding="utf-8")
    assert sandbox._load_blacklist(path) == frozenset()

def test_load_blacklist_invalid_encoding_returns_empty(tmp_path):
    path = tmp_path / "blacklist.json"
    path.write_bytes(b"\xff\xfe\x00{")
    assert sandbox._load_blacklist(path) == frozenset()

def test_load_blacklist_unexpected_structure_returns_empty(tmp_path):
    for payload in (
        [],
        ["a.site"],
        "texto",
        42,
        None,
        {},
        {"entries": "a.site"},
        {"entries": {"domain": "a.site"}},
        {"entries": None},
    ):
        path = _write_blacklist(tmp_path, payload)
        assert sandbox._load_blacklist(path) == frozenset(), payload

def test_load_blacklist_skips_invalid_entries_and_keeps_valid_ones(tmp_path):
    path = _write_blacklist(tmp_path, {"entries": [
        "texto",
        42,
        None,
        ["domain"],
        {"origin": "sin dominio"},
        {"domain": None},
        {"domain": 5},
        {"domain": ["a.site"]},
        {"domain": ""},
        {"domain": "   "},
        {"domain": "."},
        {"domain": "valido.site"},
        {"domain": " Otro-Valido.XYZ. "},
    ]})
    assert sandbox._load_blacklist(path) == frozenset({"valido.site", "otro-valido.xyz"})

def test_is_blacklisted_suffix_matching():
    bl = frozenset({"mala.site", "otra.co.xyz"})
    assert sandbox._is_blacklisted("mala.site", bl) is True
    assert sandbox._is_blacklisted("a.mala.site", bl) is True
    assert sandbox._is_blacklisted("a.b.mala.site", bl) is True
    assert sandbox._is_blacklisted("mala.site.", bl) is True
    assert sandbox._is_blacklisted("x.otra.co.xyz", bl) is True
    assert sandbox._is_blacklisted("xmala.site", bl) is False
    assert sandbox._is_blacklisted("mala.site.evil.com", bl) is False
    assert sandbox._is_blacklisted("co.xyz", bl) is False

def test_is_blacklisted_never_matches_bare_tld():
    assert sandbox._is_blacklisted("algo.site", frozenset({"site"})) is False
    assert sandbox._is_blacklisted("a.b.site", frozenset({"site"})) is False

def test_is_blacklisted_empty_set_and_degenerate_domains():
    assert sandbox._is_blacklisted("mala.site", frozenset()) is False
    assert sandbox._is_blacklisted("localhost", frozenset({"localhost"})) is False
    assert sandbox._is_blacklisted("::1", frozenset({"::1"})) is False
    assert sandbox._is_blacklisted("", frozenset({"mala.site"})) is False

def test_real_blacklist_file_sanity():
    bl = sandbox._get_blacklist()
    assert bl, "la lista negra real no debe estar vacía"
    assert _LISTED in bl
    for domain in bl:
        assert domain == domain.strip().lower().rstrip("."), domain
        assert "." in domain, domain
    assert bl == sandbox._load_blacklist(sandbox.BLACKLIST_PATH)


# --- Host tal como lo interpretaría un navegador (barra invertida y %XX) ---

_LISTADO = frozenset({"listado.site"})

def test_backslash_does_not_hide_blacklisted_host():
    res = analyze_url("https://listado.site\\@www.bancolombia.com/", blacklist=_LISTADO)
    assert res["domain"] == "listado.site"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"

def test_backslash_does_not_spoof_official_domain():
    res = analyze_url("https://evil.xyz\\@www.bancolombia.com/", blacklist=frozenset())
    assert res["domain"] == "evil.xyz"
    assert res["is_suspicious_tld"] is True
    assert res["verdict"] != "SEGURO"

def test_percent_encoded_dot_in_host_is_decoded():
    for url in ("https://listado%2esite/", "https://listado%2Esite/x", "http://listado%2esite:8080"):
        res = analyze_url(url, blacklist=_LISTADO)
        assert res["domain"] == "listado.site", url
        assert res["is_blacklisted"] is True, url

def test_backslash_in_query_or_fragment_is_untouched():
    for url in ("https://www.bancolombia.com/x?u=\\@evil.xyz", "https://www.bancolombia.com/#\\@evil.xyz"):
        res = analyze_url(url, blacklist=frozenset())
        assert res["domain"] == "www.bancolombia.com", url
        assert res["verdict"] == "SEGURO", url

def test_backslash_only_in_path_keeps_host():
    res = analyze_url("https://www.bancolombia.com\\login", blacklist=frozenset())
    assert res["domain"] == "www.bancolombia.com"
    assert res["verdict"] == "SEGURO"

def test_backslash_shortener_requests_the_browser_host(monkeypatch):
    seen = []
    def _head(url, timeout=3):
        seen.append(url)
        return (200, None)
    monkeypatch.setattr(sandbox, "_head_request", _head)
    res = analyze_url("https://bit.ly\\@evil.com/x", blacklist=frozenset())
    assert res["is_shortener"] is True
    assert res["domain"] == "bit.ly"
    assert res["original_url"] == "https://bit.ly\\@evil.com/x"
    assert seen == ["https://bit.ly/@evil.com/x"]

def test_percent_encoded_letter_in_host_is_decoded_to_lowercase():
    assert analyze_url("https://%41bc.site/", expand=False, blacklist=frozenset())["domain"] == "abc.site"
    assert analyze_url("https://EXAMPL%45.site", expand=False, blacklist=frozenset())["domain"] == "example.site"

def test_malformed_percent_escapes_in_host_do_not_raise():
    for url in ("https://a%zz.site/", "https://a%.site/", "https://a%ff.site/", "https://%/"):
        res = analyze_url(url, expand=False, blacklist=frozenset())
        assert res["status"] == "success", url

def test_percent_escapes_outside_host_are_not_decoded():
    res = analyze_url("https://www.bancolombia.com/%2e%2e/x?u=%2e", blacklist=frozenset())
    assert res["domain"] == "www.bancolombia.com"
    assert res["verdict"] == "SEGURO"

def test_normalize_url_only_rewrites_backslashes_before_query_or_fragment():
    assert sandbox._normalize_url("https://a.com\\p?q=\\z#f\\g") == "https://a.com/p?q=\\z#f\\g"
    assert sandbox._normalize_url("https://a.com\\p#f?x\\y") == "https://a.com/p#f?x\\y"
    assert sandbox._normalize_url("https://a.com/x?u=\\@b.xyz") == "https://a.com/x?u=\\@b.xyz"
    assert sandbox._normalize_url("https:\\\\a.com\\p") == "https://a.com/p"

def test_normalize_url_prepends_scheme_when_missing():
    assert sandbox._normalize_url("a.com/x") == "http://a.com/x"
    assert sandbox._normalize_url("a.com\\x") == "http://a.com/x"
    assert sandbox._normalize_url("https://a.com") == "https://a.com"
    once = sandbox._normalize_url("evil.xyz\\@b.com?q=\\")
    assert sandbox._normalize_url(once) == once

def test_normalize_url_fragment_without_query_is_untouched():
    assert sandbox._normalize_url("https://a.com/#f\\g") == "https://a.com/#f\\g"
    assert sandbox._normalize_url("https://a.com\\p#f\\g") == "https://a.com/p#f\\g"

def test_percent_encoded_slash_in_userinfo_does_not_hide_real_host():
    # el %2f pertenece al userinfo: el host real es listado.site, no www.bancolombia.com.
    # Falla si se decodifica toda la URL en vez de solo el host.
    res = analyze_url("https://www.bancolombia.com%2f@listado.site/", blacklist=_LISTADO)
    assert res["domain"] == "listado.site"
    assert res["is_blacklisted"] is True

def test_percent_encoded_hash_in_userinfo_does_not_cut_the_host():
    res = analyze_url("https://listado.site%23@www.bancolombia.com/", blacklist=_LISTADO)
    assert res["domain"] == "www.bancolombia.com"
    assert res["is_blacklisted"] is False
