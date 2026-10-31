"""
Pruebas Unitarias para UrlSandbox
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
"""

import json
import time
import types

import pytest

import src.tools.url_sandbox as sandbox
from src.tools.url_sandbox import (
    analyze_url,
    _head_request as real_head_request,
    _resolve_public_ip,
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
    def _fake_head(url, timeout=3):
        if url == "https://8.8.8.8/x":
            return (301, "http://127.0.0.1/admin")
        if url == "http://127.0.0.1/admin":
            raise PermissionError("Host no p\u00fablico bloqueado (protecci\u00f3n SSRF)")
        return (200, None)
    monkeypatch.setattr(sandbox, "_head_request", _fake_head)
    start, chain, err = sandbox._expand_url("https://8.8.8.8/x")
    assert "SSRF" in err
    assert chain == ["https://8.8.8.8/x", "http://127.0.0.1/admin"]

def test_is_public_host_literals():
    assert _resolve_public_ip("127.0.0.1") is None
    assert _resolve_public_ip("192.168.1.10") is None
    assert _resolve_public_ip("10.0.0.5") is None
    assert _resolve_public_ip("169.254.169.254") is None
    assert _resolve_public_ip("8.8.8.8") == "8.8.8.8"

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


# --- Telemetría de latencia (solo tipos y >= 0; los valores exactos usan un reloj falso) ---

def _assert_ms(value):
    assert isinstance(value, float) and value >= 0, value

def _one_hop_head():
    return _fake_head({"https://bit.ly/x": (301, "https://example.org/final")})

def test_telemetry_present_in_success_result():
    res = analyze_url("https://www.bancolombia.com", blacklist=frozenset())
    assert res["status"] == "success"
    _assert_ms(res["telemetry"]["latency_ms"])
    assert res["telemetry"]["expansion_ms"] is None

def test_telemetry_present_in_error_results():
    for bad in (None, "", "   ", 123):
        res = analyze_url(bad)
        assert res["status"] == "error", bad
        assert set(res["telemetry"]) == {"expansion_ms", "latency_ms"}, bad
        assert res["telemetry"]["expansion_ms"] is None, bad
        _assert_ms(res["telemetry"]["latency_ms"])

def test_telemetry_non_shortener_has_no_expansion_time(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("no debe hacer red")
    monkeypatch.setattr(sandbox, "_head_request", _boom)
    res = analyze_url("https://www.bancolombia.com", blacklist=frozenset())
    assert res["telemetry"]["expansion_ms"] is None
    assert res["expansion_error"] is None
    _assert_ms(res["telemetry"]["latency_ms"])

def test_telemetry_expanded_shortener_reports_expansion_time(monkeypatch):
    monkeypatch.setattr(sandbox, "_head_request", _one_hop_head())
    res = analyze_url("https://bit.ly/x", blacklist=frozenset())
    assert res["expanded_url"] == "https://example.org/final"
    _assert_ms(res["telemetry"]["expansion_ms"])
    _assert_ms(res["telemetry"]["latency_ms"])

def test_telemetry_failed_expansion_still_reports_expansion_time():
    # conftest bloquea la red: el desenrollado falla, pero sí se intentó y se midió
    res = analyze_url("https://bit.ly/3xXyZ", blacklist=frozenset())
    assert res["expansion_error"] is not None
    _assert_ms(res["telemetry"]["expansion_ms"])
    _assert_ms(res["telemetry"]["latency_ms"])

def test_telemetry_shortener_without_expand_has_no_expansion_time(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("no debe hacer red")
    monkeypatch.setattr(sandbox, "_head_request", _boom)
    res = analyze_url("https://bit.ly/x", expand=False, blacklist=frozenset())
    assert res["is_shortener"] is True
    assert res["telemetry"]["expansion_ms"] is None
    _assert_ms(res["telemetry"]["latency_ms"])

def test_telemetry_keys_are_exact(monkeypatch):
    monkeypatch.setattr(sandbox, "_head_request", _one_hop_head())
    res = analyze_url("https://bit.ly/x", blacklist=frozenset())
    assert set(res) >= {"status", "domain", "verdict", "risk_score", "findings", "telemetry"}
    assert set(res["telemetry"]) == {"expansion_ms", "latency_ms"}


def _use_clock(monkeypatch, read):
    """Reemplaza el `time` del sandbox (no el del proceso). monotonic se conserva porque
    _expand_url lo lee para su presupuesto de tiempo."""
    monkeypatch.setattr(
        sandbox, "time", types.SimpleNamespace(perf_counter=read, monotonic=time.monotonic)
    )

def test_telemetry_values_with_scripted_clock(monkeypatch):
    # Lecturas esperadas: inicio total, inicio de la red, fin de la red, fin total.
    ticks = iter([0.0, 1.0, 1.5, 4.0])
    _use_clock(monkeypatch, lambda: next(ticks))
    monkeypatch.setattr(sandbox, "_head_request", _one_hop_head())
    res = analyze_url("https://bit.ly/x", blacklist=frozenset())
    assert res["telemetry"] == {"expansion_ms": 500.0, "latency_ms": 4000.0}
    assert res["telemetry"]["latency_ms"] >= res["telemetry"]["expansion_ms"]
    assert next(ticks, None) is None  # se consumieron exactamente 4 lecturas

def test_telemetry_expansion_excludes_destination_reanalysis(monkeypatch):
    # Reloj con estado: avanza dentro de la red (cada HEAD tarda 0.5 s) y dentro del
    # re-análisis del destino (2 s). expansion_ms debe contar solo la red; latency_ms, todo.
    clock = {"t": 0.0}
    _use_clock(monkeypatch, lambda: clock["t"])
    def _head(url, timeout=3):
        clock["t"] += 0.5
        return (301, "https://example.org/final") if url == "https://bit.ly/x" else (200, None)
    real_detect_brand = sandbox._detect_brand
    def _detect_brand(domain):
        if domain == "example.org":  # solo ocurre al re-analizar el destino
            clock["t"] += 2.0
        return real_detect_brand(domain)
    monkeypatch.setattr(sandbox, "_head_request", _head)
    monkeypatch.setattr(sandbox, "_detect_brand", _detect_brand)
    res = analyze_url("https://bit.ly/x", blacklist=frozenset())
    assert res["expanded_url"] == "https://example.org/final"
    assert res["telemetry"] == {"expansion_ms": 1000.0, "latency_ms": 3000.0}

def test_telemetry_expansion_ms_is_rounded_to_two_decimals(monkeypatch):
    ticks = iter([0.0, 1.0, 1.123456, 2.0])
    _use_clock(monkeypatch, lambda: next(ticks))
    monkeypatch.setattr(sandbox, "_head_request", _one_hop_head())
    res = analyze_url("https://bit.ly/x", blacklist=frozenset())
    assert res["telemetry"] == {"expansion_ms": 123.46, "latency_ms": 2000.0}

def test_telemetry_latency_ms_is_rounded_to_two_decimals(monkeypatch):
    clock = {"t": 0.0}
    _use_clock(monkeypatch, lambda: clock["t"])
    def _detect_brand(domain):
        clock["t"] += 0.0012345  # 1.2345 ms: con 3 decimales saldría 1.234 o 1.235
        return None
    monkeypatch.setattr(sandbox, "_detect_brand", _detect_brand)
    res = analyze_url("https://www.bancolombia.com", blacklist=frozenset())
    assert res["telemetry"] == {"expansion_ms": None, "latency_ms": 1.23}

def test_telemetry_clock_without_network_and_on_error(monkeypatch):
    ticks = iter([5.0, 5.25, 7.0, 7.5])
    _use_clock(monkeypatch, lambda: next(ticks))
    ok = analyze_url("https://www.bancolombia.com", blacklist=frozenset())
    assert ok["telemetry"] == {"expansion_ms": None, "latency_ms": 250.0}
    err = analyze_url("")
    assert err["telemetry"] == {"expansion_ms": None, "latency_ms": 500.0}
    assert next(ticks, None) is None

def test_analyze_url_wrapper_does_not_mutate_core_result(monkeypatch):
    # Si el núcleo devolviera siempre el mismo objeto (p. ej. una caché futura), el envoltorio
    # no debe escribir latency_ms en él ni compartir su dict de telemetría.
    shared = {"status": "success", "telemetry": {"expansion_ms": None}}
    monkeypatch.setattr(sandbox, "_analyze_url", lambda *args, **kwargs: shared)
    first = analyze_url("https://www.bancolombia.com")
    second = analyze_url("https://www.bancolombia.com")
    assert shared["telemetry"] == {"expansion_ms": None}
    for res in (first, second):
        assert res is not shared
        assert res["telemetry"] is not shared["telemetry"]
        assert set(res["telemetry"]) == {"expansion_ms", "latency_ms"}
        _assert_ms(res["telemetry"]["latency_ms"])
    assert first["telemetry"] is not second["telemetry"]


# --- Endurecimiento del parseo del host (FQDN, esquemas, Unicode, host inválido, límites) ---

_EVIL = frozenset({"evil.xyz"})
_INVALID_HOST_FINDING = "Host inválido o con caracteres de evasión"

def _has_invalid_host_finding(res):
    return any(f.startswith(_INVALID_HOST_FINDING) for f in res["findings"])

def _fullwidth(text):
    """Letras a-z en su forma de ancho completo (U+FF41...), que NFKC lleva a ASCII."""
    return "".join(chr(ord(c) + 0xFEE0) if "a" <= c <= "z" else c for c in text)

# 1. Punto final del FQDN

def test_trailing_dot_fqdn_is_treated_like_the_bare_domain():
    for url in ("http://evil.xyz./", "http://evil.xyz../", "evil.xyz."):
        res = analyze_url(url, blacklist=frozenset())
        assert res["domain"] == "evil.xyz", url
        assert res["is_suspicious_tld"] is True, url
        assert res["verdict"] == "SOSPECHOSO", url

def test_trailing_dot_does_not_hide_shortener(monkeypatch):
    monkeypatch.setattr(sandbox, "_head_request", _fake_head({
        "https://bit.ly./abc": (301, "https://example.org/final"),
    }))
    res = analyze_url("https://bit.ly./abc", blacklist=frozenset())
    assert res["domain"] == "bit.ly"
    assert res["is_shortener"] is True
    assert res["expanded_url"] == "https://example.org/final"
    res = analyze_url("https://www.bit.ly../abc", expand=False, blacklist=frozenset())
    assert res["is_shortener"] is True

def test_trailing_dot_official_domain_is_not_a_false_positive():
    for url in ("https://www.bancolombia.com./", "https://nequi.com.co../x"):
        res = analyze_url(url, blacklist=frozenset())
        assert res["is_typosquatting"] is False, url
        assert res["verdict"] == "SEGURO", url

def test_trailing_dot_does_not_evade_blacklist():
    for url in ("https://listado.site./x", "https://login.listado.site../", "listado.site."):
        res = analyze_url(url, blacklist=_LISTADO)
        assert res["is_blacklisted"] is True, url
        assert res["verdict"] == "MALICIOSO", url

# 2. Reglas de esquema

def test_missing_or_odd_scheme_still_exposes_the_host():
    for url in (
        "evil.xyz/?q=http://x",
        "evil.xyz/#http://x",
        "//evil.xyz/x",
        "https:///evil.xyz/x",
        "https:evil.xyz/x",
        "HTTPS:evil.xyz/x",
        "wss:/evil.xyz",
        "ftp:////evil.xyz",
        "evil.xyz:8080/x",
        "\\\\evil.xyz\\x",
    ):
        res = analyze_url(url, blacklist=_EVIL)
        assert res["domain"] == "evil.xyz", url
        assert res["is_blacklisted"] is True, url
        assert res["verdict"] == "MALICIOSO", url

def test_well_formed_scheme_is_left_untouched():
    res = analyze_url("http://a.com", blacklist=frozenset())
    assert res["domain"] == "a.com"
    assert res["original_url"] == "http://a.com"
    assert res["verdict"] == "SEGURO"

def test_normalize_url_scheme_rules():
    cases = {
        "http://a.com": "http://a.com",
        "https:evil.xyz/x": "https://evil.xyz/x",
        "https:///evil.xyz/x": "https://evil.xyz/x",
        "HTTP:/evil.xyz": "HTTP://evil.xyz",
        "wss:evil.xyz": "wss://evil.xyz",
        "ftp:////evil.xyz": "ftp://evil.xyz",
        "//evil.xyz/x": "http://evil.xyz/x",
        "file:///etc/passwd": "file:///etc/passwd",
        "javascript://evil.xyz/x": "javascript://evil.xyz/x",
        "git+ssh://evil.xyz/x": "git+ssh://evil.xyz/x",
        "evil.xyz/?q=http://x": "http://evil.xyz/?q=http://x",
        "evil.xyz/#http://x": "http://evil.xyz/#http://x",
        "evil.xyz:8080/x": "http://evil.xyz:8080/x",
        "mailto:a@b.com": "http://mailto:a@b.com",
    }
    for raw, expected in cases.items():
        assert sandbox._normalize_url(raw) == expected, raw

def test_normalize_url_never_raises():
    raws = [
        "", "http:", "//", "///", "/evil.xyz", "://", "\\\\evil.xyz", "a\\b?c\\d#e", "https:\\\\evil.xyz",
        "\x00", " http://a.com", "WSS:::", "1abc://x", "evil.xyz/?q=http://x", "https:///evil.xyz",
        "?", "#", "http", "a" * 5000,
    ]
    for raw in raws:
        assert isinstance(sandbox._normalize_url(raw), str), raw
    # y las entradas degeneradas no se devuelven tal cual: se completan como cualquier otra
    for raw, expected in {"": "http://", "//": "http://", "http:": "http://", "a.com": "http://a.com"}.items():
        assert sandbox._normalize_url(raw) == expected, repr(raw)

def test_normalize_url_is_stable_on_well_formed_urls():
    # aplicarla de nuevo sobre una URL que ya trae esquema no la cambia
    for raw in (
        "http://a.com", "https:evil.xyz/x", "//evil.xyz/x", "evil.xyz/?q=http://x", "evil.xyz:8080/x",
        "a.com\\p?q=\\z#f\\g", "HTTP:/evil.xyz", "ftp:////evil.xyz", "file:///etc/passwd", "wss:evil.xyz",
    ):
        once = sandbox._normalize_url(raw)
        assert sandbox._normalize_url(once) == once, raw

def test_other_schemes_with_hyphen_dot_digit_or_uppercase_are_left_untouched():
    for url in ("view-source://evil.xyz/x", "a.b://evil.xyz/x", "s3://evil.xyz/x", "Git+SSH://evil.xyz/x"):
        assert sandbox._normalize_url(url) == url, url
        res = analyze_url(url, expand=False, blacklist=_EVIL)
        assert res["domain"] == "evil.xyz", url
        assert res["is_blacklisted"] is True, url

# 3. Puntos Unicode, caracteres invisibles y NFKC

def test_unicode_dots_are_read_as_dots():
    for dot in ("\u3002", "\uff0e", "\uff61"):
        res = analyze_url(f"http://listado{dot}site/", blacklist=_LISTADO)
        assert res["domain"] == "listado.site", repr(dot)
        assert res["is_blacklisted"] is True, repr(dot)
        res = analyze_url(f"http://evil{dot}xyz/", blacklist=frozenset())
        assert res["domain"] == "evil.xyz", repr(dot)
        assert res["is_suspicious_tld"] is True, repr(dot)

def test_invisible_and_control_chars_in_host_do_not_evade_filters():
    for ch in ("\u200b", "\u00ad", "\u2060", "\ufeff", "\x01", "\x7f"):
        res = analyze_url(f"http://listado{ch}.site/", blacklist=_LISTADO)
        assert res["domain"] == "listado.site", repr(ch)
        assert res["is_blacklisted"] is True, repr(ch)
        res = analyze_url(f"http://evil.x{ch}yz/", blacklist=frozenset())
        assert res["domain"] == "evil.xyz", repr(ch)
        assert res["is_suspicious_tld"] is True, repr(ch)

def test_fullwidth_host_is_normalized_with_nfkc():
    res = analyze_url("http://" + _fullwidth("listado") + ".site/", blacklist=_LISTADO)
    assert res["domain"] == "listado.site"
    assert res["is_blacklisted"] is True
    res = analyze_url("http://" + _fullwidth("evil") + ".xyz/", blacklist=frozenset())
    assert res["domain"] == "evil.xyz"
    assert res["is_suspicious_tld"] is True

def test_canonical_host():
    assert sandbox._canonical_host("www.bancolombia.com") == "www.bancolombia.com"
    assert sandbox._canonical_host("Evil\u3002XYZ.") == "evil.xyz"
    assert sandbox._canonical_host("a\u200bb\u00adc\u2060d\ufeffe\x01f\x7fg") == "abcdefg"
    assert sandbox._canonical_host(_fullwidth("evil") + "\uff0exyz...") == "evil.xyz"
    assert sandbox._canonical_host("") == ""
    assert sandbox._canonical_host("...") == ""

def test_dot_reached_through_nfkc_is_read_as_dot():
    # U+FE12 -> NFKC -> U+3002 -> "." (el translate debe ir después de NFKC)
    assert sandbox._canonical_host("evil\ufe12xyz") == "evil.xyz"
    res = analyze_url("http://evil\ufe12xyz/", expand=False, blacklist=_EVIL)
    assert res["domain"] == "evil.xyz"
    assert res["is_blacklisted"] is True

# Caracteres que nameprep "mapea a nada" (stringprep B.1) y que no son Cf/Cc: selectores de variación,
# CGJ y selectores/separador mongoles. Un navegador los descarta; aquí se eliminan y marcan el host.
_MAPPED_TO_NOTHING = ("\ufe00", "\ufe0f", "\u034f", "\u180b", "\u180c", "\u180d", "\u1806")

def test_chars_mapped_to_nothing_are_removed_and_flag_the_host():
    for ch in _MAPPED_TO_NOTHING:
        res = analyze_url(f"https://listado{ch}.site/", expand=False, blacklist=_LISTADO)
        assert res["domain"] == "listado.site", repr(ch)
        assert res["is_blacklisted"] is True, repr(ch)
        assert _has_invalid_host_finding(res), repr(ch)
        assert sandbox._parse_host(f"https://listado{ch}.site/") == ("listado.site", True), repr(ch)

def test_chars_mapped_to_nothing_do_not_hide_shortener_or_risky_tld():
    for ch in _MAPPED_TO_NOTHING:
        res = analyze_url(f"https://bit{ch}.ly/x", expand=False, blacklist=frozenset())
        assert res["domain"] == "bit.ly", repr(ch)
        assert res["is_shortener"] is True, repr(ch)
        res = analyze_url(f"https://evil.x{ch}yz/", expand=False, blacklist=frozenset())
        assert res["domain"] == "evil.xyz", repr(ch)
        assert res["is_suspicious_tld"] is True, repr(ch)
        assert res["verdict"] != "SEGURO", repr(ch)
        assert _has_invalid_host_finding(res), repr(ch)

def test_canonical_host_removes_chars_mapped_to_nothing_before_nfkc():
    assert sandbox._canonical_host("a\ufe0fb") == "ab"
    for ch in _MAPPED_TO_NOTHING:
        assert sandbox._canonical_host(f"a{ch}b") == "ab", repr(ch)
        # igual que con los Cf: no pueden quedar entre la letra y su marca combinante
        assert sandbox._canonical_host(f"a{ch}\u0301") == "á", repr(ch)

def test_is_ignorable():
    for ch in ("\u200b", "\u00ad", "\u2060", "\ufeff", "\u202e", "\x01", "\x7f") + _MAPPED_TO_NOTHING:
        assert sandbox._is_ignorable(ch) is True, repr(ch)
    for ch in ("a", "1", ".", "-", "\u0301", "\u3002", "”"):
        assert sandbox._is_ignorable(ch) is False, repr(ch)

# 4. Host inválido: falla cerrado

def test_invalid_hosts_fail_closed():
    for url in (
        "http://evil.xyz%2f.bancolombia.com/",
        "http://evil.xyz%00.bancolombia.com/",
        "http://[evil.xyz/",
        "http://a..b.com/",
        "http://a%09b.com/",
        "http://a b.com/",
        "http://evil.xyz\uff0f.com",
        "evil.xyz\uff0f.com",
    ):
        res = analyze_url(url, blacklist=frozenset())
        assert res["status"] == "success", url
        assert res["verdict"] != "SEGURO", url
        assert _has_invalid_host_finding(res), url

def test_invalid_host_alone_is_suspicious_not_malicious():
    res = analyze_url("http://[evil.xyz/", blacklist=frozenset())
    assert res["verdict"] == "SOSPECHOSO"
    assert res["risk_score"] == 40
    assert res["findings"] == [f"{_INVALID_HOST_FINDING} ('http://[evil.xyz/')"]

def test_percent_encoded_control_chars_flag_the_host_but_still_match_the_blacklist():
    # el navegador rechaza %00 en el host; para comparar se elimina, y además se marca inválido
    res = analyze_url("http://listado%00.site/", blacklist=_LISTADO)
    assert res["domain"] == "listado.site"
    assert res["is_blacklisted"] is True
    assert _has_invalid_host_finding(res)
    res = analyze_url("http://evil.xyz%00.bancolombia.com/", blacklist=frozenset())
    assert res["domain"] == "evil.xyz.bancolombia.com"
    assert _has_invalid_host_finding(res)

def test_valid_ipv6_hosts_are_not_invalid():
    for url in ("http://[::1]/x", "http://[2001:db8::1]:8080/p", "http://[::ffff:1.2.3.4]/"):
        res = analyze_url(url, blacklist=frozenset())
        assert not _has_invalid_host_finding(res), url
        assert res["verdict"] == "SEGURO", url
    assert analyze_url("http://[::1]/x", blacklist=frozenset())["domain"] == "::1"

def test_is_invalid_host():
    for ok in ("a.com", "localhost", "xn--80ak6aa92e.com", "::1", "2001:db8::1", "::ffff:1.2.3.4"):
        assert sandbox._is_invalid_host(ok) is False, ok
    for bad in (
        "a b.com", "a\tb.com", "a\u00a0b.com", "a/b", "a\\b", "a?b", "a#b", "a@b", "a%b", "a<b", "a>b",
        "a^b", "a|b", "a[b", "a]b", "a{b", "a}b", 'a"b', "a'b", "a`b", "a\x01b", "a\x7fb", "a\x85b",
        "a..b.com", "a:b", "1.2.3.4:80", "evil.xyz:8080", ":::",
    ):
        assert sandbox._is_invalid_host(bad) is True, repr(bad)

def test_is_invalid_host_is_an_allowlist_of_letters_marks_digits_and_host_punctuation():
    for ok in (
        "münchen.de", "bancolómbia.com", "e\u0301.com", "xn--abc.com", "a_b.com", "127.0.0.1",
        "::1", "2001:db8::", "a1-b2.co", "\u043f\u0440\u0438\u043c\u0435\u0440.\u0440\u0444",
    ):
        assert sandbox._is_invalid_host(ok) is False, repr(ok)
    for bad in (
        "ab\U0001F449cd.com", "a+b.com", "a~b.com", "a=b.com", "a*b.com", "a(b).com", "a,b.com", "a;b.com",
        "a”b.com",
    ):
        assert sandbox._is_invalid_host(bad) is True, repr(bad)

def test_symbols_and_punctuation_inside_the_host_are_flagged_but_idn_letters_are_not():
    for url in ("https://ab\U0001F449cd.com/", "https://a+b.com/", "https://a(b).com/", "https://a,b.com/"):
        res = analyze_url(url, expand=False, blacklist=frozenset())
        assert res["status"] == "success", url
        assert res["verdict"] != "SEGURO", url
        assert _has_invalid_host_finding(res), url
    res = analyze_url("https://münchen.de/", expand=False, blacklist=frozenset())
    assert res["domain"] == "münchen.de"
    assert res["verdict"] == "SEGURO"
    assert not _has_invalid_host_finding(res)

def test_is_invalid_host_length_limit_is_inclusive():
    at_limit = ".".join(["a" * 50] * 4 + ["a" * 49])
    assert len(at_limit) == sandbox.MAX_DOMAIN_LEN == 253
    assert sandbox._is_invalid_host(at_limit) is False
    assert sandbox._is_invalid_host("a" + at_limit) is True

def test_parse_host_flags_unreadable_hosts_and_keeps_the_input_as_domain():
    assert sandbox._extract_domain("http://[evil.xyz/") == "http://[evil.xyz/"
    assert sandbox._parse_host("http://[Evil.xyz/") == ("http://[evil.xyz/", True)
    assert sandbox._parse_host("http://A.com/x") == ("a.com", False)
    assert sandbox._parse_host("http://a%00.com/") == ("a.com", True)

def test_url_without_host_is_an_error_result():
    for url in ("http://", "https:///", "//", "http://./", "  http://  "):
        res = analyze_url(url, blacklist=frozenset())
        assert res["status"] == "error", url
        assert res["verdict"] == "NO_ANALIZADO", url
        assert res["risk_score"] == 0, url
        assert res["findings"] == ["No se pudo extraer un host de la entrada"], url
        assert res["domain"] == "" and res["is_blacklisted"] is False, url
        assert isinstance(res["original_url"], str) and isinstance(res["expanded_url"], str), url
        assert set(res["telemetry"]) == {"expansion_ms", "latency_ms"}, url

def test_error_result_keeps_the_text_it_received():
    res = analyze_url("http://", blacklist=frozenset())
    assert res["status"] == "error"
    assert res["original_url"] == "http://"
    assert res["expanded_url"] == "http://"

# 5. Cotas contra el coste cuadrático

def test_overlong_domain_skips_expensive_checks(monkeypatch):
    long_domain = ".".join(["a" * 50] * 6) + ".com"
    assert len(long_domain) > sandbox.MAX_DOMAIN_LEN
    calls = {"blacklist": 0, "brand": 0}
    real_is_blacklisted = sandbox._is_blacklisted
    real_detect_brand = sandbox._detect_brand
    def _count_blacklist(domain, blacklist):
        calls["blacklist"] += 1
        return real_is_blacklisted(domain, blacklist)
    def _count_brand(domain):
        calls["brand"] += 1
        return real_detect_brand(domain)
    monkeypatch.setattr(sandbox, "_is_blacklisted", _count_blacklist)
    monkeypatch.setattr(sandbox, "_detect_brand", _count_brand)
    # control: un dominio normal sí pasa por ambos chequeos
    analyze_url("https://www.bancolombia.com", blacklist=_LISTADO)
    assert calls == {"blacklist": 1, "brand": 1}
    calls.update(blacklist=0, brand=0)
    res = analyze_url(f"https://{long_domain}/x", blacklist=_LISTADO)
    assert calls == {"blacklist": 0, "brand": 0}
    assert res["is_blacklisted"] is False
    assert res["verdict"] == "SOSPECHOSO"
    assert _has_invalid_host_finding(res)
    assert long_domain not in " ".join(res["findings"])  # el hallazgo recorta el dominio

def test_is_blacklisted_returns_false_directly_above_the_limit():
    at_limit = "b" + "a." * 120 + "listado.site"
    assert len(at_limit) == sandbox.MAX_DOMAIN_LEN
    assert sandbox._is_blacklisted(at_limit, _LISTADO) is True
    assert sandbox._is_blacklisted("a" + at_limit, _LISTADO) is False

def test_huge_label_chain_is_handled_as_invalid_host():
    res = analyze_url("http://" + "a." * 10000 + "com", blacklist=_LISTADO)
    assert res["status"] == "success"
    assert res["is_blacklisted"] is False
    assert _has_invalid_host_finding(res)

# 6. Lista negra con BOM

def test_load_blacklist_accepts_utf8_bom(tmp_path):
    path = tmp_path / "blacklist.json"
    payload = {"entries": [{"domain": "Con-Bom.SITE"}]}
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps(payload).encode("utf-8"))
    assert sandbox._load_blacklist(path) == frozenset({"con-bom.site"})

def test_load_blacklist_only_removes_the_trailing_dot(tmp_path):
    path = tmp_path / "bl.json"
    path.write_text(json.dumps({"entries": [{"domain": " .Evil.XYZ. "}]}), encoding="utf-8")
    assert sandbox._load_blacklist(path) == frozenset({".evil.xyz"})

# 7. Marcas cortas: igualdad o marca literal tras el leetspeak, no subcadena normalizada

def test_short_brand_matches_by_equality_or_leet_substring_not_normalized_substring():
    # "bbva" se normaliza a "bva" (3 < 4): como subcadena normalizada daría falsos positivos (bvasports),
    # pero la marca literal sigue detectándose dentro de un token con leetspeak (bbv4seguro -> bbvaseguro)
    assert sandbox._detect_brand("bvasports.com") is None
    res = analyze_url("https://bvasports.com", blacklist=frozenset())
    assert res["is_typosquatting"] is False
    assert res["verdict"] == "SEGURO"
    for url in (
        "https://bbv4.com", "https://bbva-seguro.com", "https://bva.com",
        "https://bbv4seguro.com", "https://bbv4pagos.co",
    ):
        res = analyze_url(url, blacklist=frozenset())
        assert res["is_typosquatting"] is True, url
        assert res["impersonated_brand"] == "bbva", url
    res = analyze_url("https://www.bbva.com.co", blacklist=frozenset())
    assert res["is_typosquatting"] is False
    assert res["verdict"] == "SEGURO"

def test_four_char_normalized_brand_matches_by_substring(monkeypatch):
    # latente: hoy ninguna marca normalizada mide 4
    monkeypatch.setattr(sandbox, "OFFICIAL_BANKS", {"yape": "yape.com.pe"})
    res = analyze_url("http://y4pelogin.com/", expand=False, blacklist=frozenset())
    assert res["is_typosquatting"] is True
    assert res["impersonated_brand"] == "yape"
    # la letra repetida solo se colapsa en la forma normalizada: aquí no basta la marca tras el leetspeak
    res = analyze_url("http://yaapelogin.com/", expand=False, blacklist=frozenset())
    assert res["is_typosquatting"] is True
    assert res["impersonated_brand"] == "yape"

# 8. Entradas mal tipadas

def test_error_result_urls_are_always_str_and_json_safe():
    for bad in (b"http://x.com", None, 123, "", "   ", ["a"], {"a": 1}):
        res = analyze_url(bad, blacklist=frozenset())
        assert res["status"] == "error"
        assert isinstance(res["original_url"], str) and isinstance(res["expanded_url"], str)
        json.dumps(res)
    assert analyze_url(b"http://x.com")["original_url"] == ""

def test_results_with_odd_hosts_are_json_safe():
    for url in ("http://evil.xyz]", "http://a%00b.com/", "http://\u200b.xyz/", "http://" + "a." * 300 + "com"):
        res = analyze_url(url, blacklist=frozenset())
        json.dumps(res)
        assert res["status"] == "success", url[:40]
        assert res["verdict"] != "SEGURO", url[:40]

def test_expand_must_be_bool(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("no debe hacer red")
    monkeypatch.setattr(sandbox, "_head_request", _boom)
    for bad in ("false", "true", 0, 1, None, []):
        with pytest.raises(TypeError, match="expand debe ser bool"):
            analyze_url("https://bit.ly/x", expand=bad, blacklist=frozenset())

def test_blacklist_must_be_a_set_or_none():
    for bad in ("xa.comx", b"xa.comx", ["a.com"], ("a.com",), {"a.com": 1}, 5):
        with pytest.raises(TypeError, match="blacklist debe ser un set/frozenset de dominios o None"):
            analyze_url("https://a.com", blacklist=bad)

def test_blacklist_str_is_rejected_instead_of_matching_substrings():
    with pytest.raises(TypeError):
        analyze_url("https://a.com", blacklist="xa.comx")

def test_blacklist_accepts_a_plain_set_without_mutating_it():
    mine = {"listado.site"}
    res = analyze_url("https://listado.site", blacklist=mine)
    assert res["is_blacklisted"] is True
    assert type(mine) is set and mine == {"listado.site"}

def test_blacklist_set_is_converted_to_frozenset_before_the_core(monkeypatch):
    seen = []
    real_core = sandbox._analyze_url
    def _spy(raw_url, expand, blacklist):
        seen.append(blacklist)
        return real_core(raw_url, expand, blacklist)
    monkeypatch.setattr(sandbox, "_analyze_url", _spy)
    analyze_url("https://listado.site", blacklist={"listado.site"})
    assert len(seen) == 1 and type(seen[0]) is frozenset

def test_url_without_hostname_uses_the_path_and_is_still_flagged():
    # sin hostname el dominio sale de la ruta ("/etc/passwd"): no puede pasar por host válido
    for url in ("file:///etc/passwd", "file:///etc/\x01passwd", "https://@/"):
        res = analyze_url(url, blacklist=frozenset())
        assert res["status"] == "success", url
        assert res["verdict"] == "SOSPECHOSO", url
        assert _has_invalid_host_finding(res), url

def test_url_without_hostname_canonicalizes_the_path_domain():
    res = analyze_url("file:///EVIL.XYZ.", expand=False, blacklist=frozenset())
    assert res["domain"] == "/evil.xyz"
    assert res["is_suspicious_tld"] is True


# --- Cotas medidas sobre el dominio canónico (no sobre la entrada cruda) ---

def test_long_path_does_not_skip_the_blacklist():
    res = analyze_url("https://listado.site/" + "a" * 400, expand=False, blacklist=_LISTADO)
    assert res["is_blacklisted"] is True
    assert not _has_invalid_host_finding(res)

def test_domain_length_is_measured_after_removing_invisible_chars():
    res = analyze_url("https://" + "\u200b" * 300 + "listado.site/", expand=False, blacklist=_LISTADO)
    assert res["domain"] == "listado.site"
    assert res["is_blacklisted"] is True

def test_domain_of_exactly_max_length_is_still_checked_against_the_blacklist():
    at_limit = "b" + "a." * 120 + "listado.site"
    assert len(at_limit) == sandbox.MAX_DOMAIN_LEN == 253
    res = analyze_url(f"https://{at_limit}/", expand=False, blacklist=_LISTADO)
    assert res["domain"] == at_limit
    assert res["is_blacklisted"] is True
    assert not _has_invalid_host_finding(res)

def test_domain_over_max_length_is_not_checked_against_the_blacklist_and_is_flagged():
    over_limit = "a" + "b" + "a." * 120 + "listado.site"
    assert len(over_limit) == sandbox.MAX_DOMAIN_LEN + 1
    res = analyze_url(f"https://{over_limit}/", expand=False, blacklist=_LISTADO)
    assert res["is_blacklisted"] is False
    assert _has_invalid_host_finding(res)
    assert res["verdict"] == "SOSPECHOSO"


# --- Puertos inválidos: los navegadores rechazan esas URLs ---

def test_invalid_ports_fail_closed():
    for url in (
        "view-source:https://evil.xyz",
        "blob:https://evil.xyz",
        "javascript:alert(1)",
        "http://host:99999/",
        "http://host:65536/",
        "http://host:abc/",
        "http://[::1]:abc/",
    ):
        res = analyze_url(url, blacklist=frozenset())
        assert res["verdict"] != "SEGURO", url
        assert _has_invalid_host_finding(res), url
        assert sandbox._parse_host(url)[1] is True, url

def test_parse_host_flags_invalid_port_even_without_hostname():
    assert sandbox._parse_host("http://:99999")[1] is True
    assert sandbox._parse_host("http://:abc/")[1] is True

# sin hostname (file:///...) el dominio es la ruta y no se marca sospechoso por sí mismo
def test_parse_host_without_hostname_is_not_flagged_by_itself():
    assert sandbox._parse_host("file:///etc/passwd")[1] is False
    assert sandbox._parse_host("http://:99999/")[1] is True

def test_valid_or_empty_ports_are_not_flagged():
    for url in ("http://host:8080/", "http://host:/", "http://[::1]:8080/", "http://host:65535/"):
        res = analyze_url(url, blacklist=frozenset())
        assert not _has_invalid_host_finding(res), url
        assert res["verdict"] == "SEGURO", url


# --- Puntuación pegada al final del host (URL extraída de un texto) ---

def test_trailing_punctuation_does_not_hide_blacklisted_domain():
    for tail in (",", ")", ";", "!", ".,", "')", "}", '"', ".", "!!", ").", ",."):
        res = analyze_url(f"https://listado.site{tail}", expand=False, blacklist=_LISTADO)
        assert res["domain"] == "listado.site", tail
        assert res["is_blacklisted"] is True, tail
        assert res["verdict"] == "MALICIOSO", tail

def test_trailing_punctuation_is_not_a_false_positive_on_official_domains():
    for url in ("https://www.bancolombia.com,", "https://www.bancolombia.com).", "https://nequi.com.co!"):
        res = analyze_url(url, expand=False, blacklist=frozenset())
        assert res["is_typosquatting"] is False, url
        assert res["verdict"] == "SEGURO", url

def test_trailing_punctuation_does_not_hide_risky_tld():
    res = analyze_url("https://evil.xyz!", expand=False, blacklist=frozenset())
    assert res["domain"] == "evil.xyz"
    assert res["is_suspicious_tld"] is True

def test_punctuation_outside_the_end_of_the_host_is_untouched():
    res = analyze_url("https://listado.site/a,b", expand=False, blacklist=_LISTADO)
    assert res["domain"] == "listado.site"
    assert analyze_url("http://[::1]/", expand=False, blacklist=frozenset())["domain"] == "::1"
    res = analyze_url("http://[2001:db8::]/", expand=False, blacklist=frozenset())
    assert res["domain"] == "2001:db8::"
    assert not _has_invalid_host_finding(res)
    assert res["verdict"] == "SEGURO"

def test_canonical_host_strips_each_trailing_punctuation_char_only_at_the_end():
    for ch in ".,;!)]}'" + '"':
        assert sandbox._canonical_host("a.com" + ch) == "a.com", repr(ch)
        assert sandbox._canonical_host("a.com" + ch * 3) == "a.com", repr(ch)
        assert sandbox._canonical_host("a" + ch + ".com") == "a" + ch + ".com", repr(ch)
    # ":" no se quita: rompería las IPv6 que terminan en "::"
    assert sandbox._canonical_host("2001:db8::") == "2001:db8::"
    assert sandbox._canonical_host("a.com:") == "a.com:"

def test_canonical_host_keeps_leading_punctuation():
    for ch in ".,;!)]}'" + '"':
        assert sandbox._canonical_host(ch + "a.com") == ch + "a.com", repr(ch)
    res = analyze_url("http://'evil.xyz/", expand=False, blacklist=frozenset())
    assert res["domain"] == "'evil.xyz"
    assert _has_invalid_host_finding(res)


# --- Puntuación o símbolo no ASCII pegado al final (comillas tipográficas, emoji, "…") ---

# comilla doble y simple de cierre, comilla angular, corchete japonés, raya, "¡", emoji (So) y puntos suspensivos
_NON_ASCII_TAILS = ("”", "’", "»", "」", "—", "¡", "\U0001F449", "…")
# símbolos (S*) y puntuación (P*) ASCII que no están en _TRAILING_PUNCTUATION, y un símbolo de moneda
_OTHER_SYMBOL_TAILS = ("*", ">", "~", "^", "€")

def test_non_ascii_trailing_punctuation_does_not_hide_blacklisted_domain():
    for tail in _NON_ASCII_TAILS + _OTHER_SYMBOL_TAILS:
        res = analyze_url(f"https://listado.site{tail}", expand=False, blacklist=_LISTADO)
        assert res["domain"] == "listado.site", repr(tail)
        assert res["is_blacklisted"] is True, repr(tail)
        assert res["verdict"] == "MALICIOSO", repr(tail)

def test_non_ascii_trailing_punctuation_does_not_hide_risky_tld():
    res = analyze_url("https://dian-notificaciones.xyz”", expand=False, blacklist=frozenset())
    assert res["domain"] == "dian-notificaciones.xyz"
    assert res["is_suspicious_tld"] is True

def test_non_ascii_trailing_punctuation_is_not_a_false_positive_on_official_domains():
    for tail in ("”", "»"):
        res = analyze_url("https://www.bancolombia.com" + tail, expand=False, blacklist=frozenset())
        assert res["domain"] == "www.bancolombia.com", repr(tail)
        assert res["is_typosquatting"] is False, repr(tail)
        assert res["verdict"] == "SEGURO", repr(tail)

def test_inner_or_leading_non_ascii_punctuation_is_untouched():
    assert sandbox._canonical_host("a”b.com") == "a”b.com"
    assert sandbox._canonical_host("a\U0001F449b.com") == "a\U0001F449b.com"
    assert sandbox._canonical_host("”a.com") == "”a.com"
    res = analyze_url("https://”listado.site/", expand=False, blacklist=_LISTADO)
    assert res["domain"] == "”listado.site"
    assert res["is_blacklisted"] is False
    assert _has_invalid_host_finding(res)

def test_trailing_junk_stops_at_the_colon_of_an_ipv6_host():
    assert sandbox._canonical_host("2001:db8::”") == "2001:db8::"
    assert sandbox._canonical_host("a.com:”") == "a.com:"
    # un host hecho solo de puntuación no se borra: se conserva para que se marque inválido
    assert sandbox._canonical_host("””") == "””"

def test_host_made_only_of_punctuation_is_kept_and_flagged_but_dots_alone_are_empty():
    # solo los puntos solos se vacían (sin host => resultado de error NO_ANALIZADO)
    assert sandbox._canonical_host(".") == ""
    assert sandbox._canonical_host("..") == ""
    for url in ("https://%/", "https://@/", "https://”/"):
        res = analyze_url(url, expand=False, blacklist=frozenset())
        assert res["status"] == "success", url
        assert res["verdict"] == "SOSPECHOSO", url
        assert _has_invalid_host_finding(res), url
    for url in ("http://.", "http://..", "http://"):
        res = analyze_url(url, expand=False, blacklist=frozenset())
        assert res["status"] == "error", url
        assert res["verdict"] == "NO_ANALIZADO", url

def test_is_trailing_junk():
    for ch in _NON_ASCII_TAILS + _OTHER_SYMBOL_TAILS + (".", ",", "!", ")", "]", "'", '"'):
        assert sandbox._is_trailing_junk(ch) is True, repr(ch)
    for ch in (":", "a", "Z", "5", "ü"):
        assert sandbox._is_trailing_junk(ch) is False, repr(ch)

def test_trailing_junk_is_stripped_after_nfkc_not_before():
    # U+00A8 (Sk) pasa por NFKC a " " + U+0308: si la puntuación final se quitara ANTES de NFKC,
    # el símbolo desaparecería sin dejar rastro y el host quedaría limpio (SEGURO)
    res = analyze_url("http://example.com\u00a8/", expand=False, blacklist=frozenset())
    assert res["domain"] == "example.com \u0308"
    assert res["verdict"] == "SOSPECHOSO"
    assert _has_invalid_host_finding(res)
    # al revés: U+2488 es un número (No) que NFKC lleva a "1."; el punto resultante sí se quita
    assert sandbox._canonical_host("evil.xyz\u2488") == "evil.xyz1"

def test_host_made_only_of_ascii_trailing_junk_is_kept_and_flagged():
    for ch in ",;!)]}'" + '"':
        assert sandbox._canonical_host(ch) == ch, repr(ch)
        assert sandbox._canonical_host(ch * 2) == ch * 2, repr(ch)
    for url in ("https://,/", "https://;/", "https://!/", "https://'/", 'https://"/'):
        res = analyze_url(url, expand=False, blacklist=frozenset())
        assert res["status"] == "success", url
        assert res["verdict"] == "SOSPECHOSO", url
        assert _has_invalid_host_finding(res), url

def test_trailing_separator_in_the_host_is_flagged_not_stripped():
    # los separadores (Z*: espacio ideográfico, espacio de no separación) no son puntuación
    for sep in ("\u3000", "\u00a0"):
        res = analyze_url("http://example.com" + sep + "/x", expand=False, blacklist=frozenset())
        assert res["status"] == "success", repr(sep)
        assert res["verdict"] == "SOSPECHOSO", repr(sep)
        assert _has_invalid_host_finding(res), repr(sep)

def test_trailing_private_use_or_unassigned_char_in_the_host_is_flagged_not_stripped():
    # uso privado (Co) y sin asignar (Cn) tampoco son puntuación
    for ch in ("\ue000", "\u0378"):
        res = analyze_url("http://example.com" + ch + "/x", expand=False, blacklist=frozenset())
        assert res["status"] == "success", repr(ch)
        assert res["verdict"] == "SOSPECHOSO", repr(ch)
        assert _has_invalid_host_finding(res), repr(ch)

def test_trailing_combining_mark_is_part_of_the_label_not_junk():
    assert sandbox._is_trailing_junk("\u0330") is False
    assert sandbox._canonical_host("a.com\u0330") == "a.com\u0330"
    res = analyze_url("http://a.com\u0330/", expand=False, blacklist=frozenset({"a.com"}))
    assert res["is_blacklisted"] is False
    assert not _has_invalid_host_finding(res)


# --- Corchete final pegado (markdown): urlparse lanza y se reintenta sin la puntuación final ---

def test_trailing_bracket_does_not_hide_blacklisted_domain():
    for url in ("https://listado.site]", "https://listado.site)]"):
        res = analyze_url(url, expand=False, blacklist=_LISTADO)
        assert res["domain"] == "listado.site", url
        assert res["is_blacklisted"] is True, url
        assert res["verdict"] == "MALICIOSO", url
        assert not _has_invalid_host_finding(res), url
        assert sandbox._parse_host(url) == ("listado.site", False), url

def test_trailing_bracket_is_not_a_false_positive_on_official_domains():
    res = analyze_url("https://www.bancolombia.com]", expand=False, blacklist=frozenset())
    assert res["domain"] == "www.bancolombia.com"
    assert res["is_typosquatting"] is False
    assert res["verdict"] == "SEGURO"
    assert not _has_invalid_host_finding(res)

def test_unbalanced_bracket_that_the_retry_cannot_fix_keeps_the_suspicious_fallback():
    res = analyze_url("http://[evil.xyz/", expand=False, blacklist=_EVIL)
    assert res["domain"] == "http://[evil.xyz/"
    assert res["is_blacklisted"] is False
    assert res["verdict"] == "SOSPECHOSO"
    assert _has_invalid_host_finding(res)

def test_balanced_brackets_around_a_non_ip_host_are_never_safe():
    # "[Evil.xyz]" tiene los corchetes balanceados. Desde Python 3.11.4 urlparse valida lo que va entre
    # corchetes como IPv6 y lanza (el reintento sin el "]" final tampoco lo arregla: respaldo = entrada
    # en minúsculas, sospechosa); en versiones anteriores no lanza y el host es "evil.xyz". Solo se
    # afirma lo común a ambas, y el resultado exacto únicamente si urlparse lanza en este intérprete.
    url = "http://[Evil.xyz]"
    res = analyze_url(url, expand=False, blacklist=frozenset())
    assert res["status"] == "success"
    assert res["verdict"] != "SEGURO"
    assert "evil.xyz" in res["domain"]
    assert res["domain"] == res["domain"].lower()
    try:
        sandbox.urlparse(url)
    except ValueError:
        assert sandbox._parse_host(url) == ("http://[evil.xyz]", True)
        assert _has_invalid_host_finding(res)


# --- Orden de la canonicalización ---

def test_canonical_host_removes_invisibles_before_nfkc():
    # la marca combinante (U+0301) debe componerse con la "a" aunque hubiera un ZWSP en medio
    assert sandbox._canonical_host("a\u200b\u0301") == "á"

def test_canonical_host_is_idempotent():
    hosts = [
        "a\u200b\u0301", "EVIL\u3002XYZ.", _fullwidth("evil") + "\uff0exyz.", "listado\u00ad.site,", "..a..",
        "a.com).", "x\ufeff\u2060y.com!", "İstanbul.com", "e\u0301.com", "2001:db8::", "a.com:",
        "\u202eevil.xyz", "\x01a\x7f.com", "%41.com", "a" * 300, "\u3002\u3002a\u3002", "a\u200b.\u200b.b", "",
        "a\ufe0f\u0301.com", "evil.xyz\u201d", "a.com\U0001F449\u201d.", "\u201d\u201d", "evil\ufe12xyz",
    ]
    for host in hosts:
        once = sandbox._canonical_host(host)
        assert sandbox._canonical_host(once) == once, repr(host)


# --- Caracteres invisibles, de formato o de control marcan el host como sospechoso ---

def test_hidden_or_format_chars_in_host_mark_it_suspicious():
    for url in (
        "https://exa\u202emple.com",
        "https://exa\u200bmple.com",
        "https://exa\u00admple.com",
        "https://exa\u2060mple.com",
        "https://\ufeffexample.com",
    ):
        res = analyze_url(url, blacklist=frozenset())
        assert res["domain"] == "example.com", repr(url)
        assert res["verdict"] == "SOSPECHOSO", repr(url)
        assert _has_invalid_host_finding(res), repr(url)
        assert sandbox._parse_host(url) == ("example.com", True), repr(url)

def test_clean_host_is_not_marked_suspicious():
    res = analyze_url("https://example.com", blacklist=frozenset())
    assert res["verdict"] == "SEGURO"
    assert not _has_invalid_host_finding(res)
    assert sandbox._parse_host("https://example.com") == ("example.com", False)

def test_has_hidden_chars():
    for hidden in ("a\u200bb", "a\x00b", "a\u202eb", "a\u00adb", "a\ufeffb", "a\x7fb"):
        assert sandbox._has_hidden_chars(hidden) is True, repr(hidden)
    for visible in ("ab", "a.com", "á", "a b", "a\u3002b"):
        assert sandbox._has_hidden_chars(visible) is False, repr(visible)

def test_has_hidden_chars_includes_chars_mapped_to_nothing():
    for ch in _MAPPED_TO_NOTHING:
        assert sandbox._has_hidden_chars("a" + ch) is True, repr(ch)
    assert sandbox._has_hidden_chars("a\ufe0f") is True
    assert sandbox._has_hidden_chars("abc") is False


# --- Lectura manual de la autoridad cuando urlparse lanza y el reintento sin la cola no sirve ---

_DIAN = frozenset({"dian-notificaciones.xyz"})

def test_markdown_link_with_unbalanced_bracket_exposes_the_real_host():
    for url in (
        "https://dian-notificaciones.xyz](https://dian-notificaciones.xyz)",
        "[https://dian-notificaciones.xyz](https://dian-notificaciones.xyz)",
        "https://x]@dian-notificaciones.xyz/",
    ):
        res = analyze_url(url, expand=False, blacklist=_DIAN)
        assert res["domain"] == "dian-notificaciones.xyz", url
        assert res["is_blacklisted"] is True, url
        assert res["verdict"] == "MALICIOSO", url

_MARKDOWN_LIST = frozenset({"evil.xyz", "dian-notificaciones.xyz"})

def test_markdown_link_analyzes_the_destination_not_the_text():
    # se analizan ambos segmentos y gana el de mayor riesgo (destino malicioso o texto malicioso)
    res = analyze_url("[https://www.bancolombia.com](https://evil.xyz)", expand=False, blacklist=_MARKDOWN_LIST)
    assert res["domain"] == "evil.xyz"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    # al revés: si el texto es una URL maliciosa y el destino es oficial, gana el texto malicioso
    res = analyze_url("[https://evil.xyz](https://www.bancolombia.com)", expand=False, blacklist=_MARKDOWN_LIST)
    assert res["domain"] == "evil.xyz"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    # con varios "](" gana el segmento de mayor riesgo
    res = analyze_url(
        "[https://x.com](https://a.com)](https://dian-notificaciones.xyz)", expand=False, blacklist=_MARKDOWN_LIST
    )
    assert res["domain"] == "dian-notificaciones.xyz"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"

def test_userinfo_with_bracket_does_not_spoof_an_official_host():
    # el host real es www.bancolombia.com, pero urlparse no pudo leer la URL: se lee a mano y se marca
    res = analyze_url("https://x]@www.bancolombia.com/", expand=False, blacklist=frozenset())
    assert res["domain"] == "www.bancolombia.com"
    assert res["verdict"] != "SEGURO"
    assert _has_invalid_host_finding(res)

def test_manual_read_with_an_invalid_host_keeps_the_raw_input_as_domain():
    # urlparse lanza por el "]" y el host leído a mano ("c d.com", con espacio) tampoco es válido
    res = analyze_url("https://x]@c d.com/", expand=False, blacklist=frozenset())
    assert res["domain"] == "https://x]@c d.com/"
    assert res["verdict"] == "SOSPECHOSO"
    assert _has_invalid_host_finding(res)

def test_manual_host_reads_the_authority_by_hand():
    cases = {
        # enlace markdown [texto](destino): se lee el destino, es decir lo que sigue al ÚLTIMO "]("
        "https://dian-notificaciones.xyz](https://otro.com)": "otro.com",
        "dian-notificaciones.xyz](https://otro.com)": "otro.com",
        "[https://www.bancolombia.com](https://evil.xyz)": "evil.xyz",
        "[https://evil.xyz](https://www.bancolombia.com)": "www.bancolombia.com",
        "[https://x.com](https://a.com)](https://dian-notificaciones.xyz)": "dian-notificaciones.xyz",
        "[https://dian-notificaciones.xyz](https://dian-notificaciones.xyz)": "dian-notificaciones.xyz",
        # sin "](" se ignoran los "[" iniciales
        "[evil.xyz:8080/x": "evil.xyz",
        "https://x]@Evil.XYZ/p?q=1#f": "evil.xyz",
        "https://user:pa]ss@evil.xyz:8080/p": "evil.xyz",
        "http://%65vil.xyz]/": "evil.xyz",
        "http://evil.xyz.]": "evil.xyz",
        "": "",
    }
    for raw, expected in cases.items():
        assert sandbox._manual_host(raw) == expected, raw

def test_manual_host_never_raises():
    raws = (
        "", "](", "@", "@@", "http://@@", "[[[", "]]]", ":::", "http://:", "\x00", "\u202e", "\\\\", "](" * 50,
        "https://\U0001F449]", "a" * 10000, "http://" + "](" * 5000,
    )
    for raw in raws:
        assert isinstance(sandbox._manual_host(raw), str), repr(raw[:20])


def test_manual_host_strips_trailing_junk_before_the_port():
    # el ")" o "]" final se quita antes del ":puerto"; si no, "evil.xyz:8080)" conservaba el ":"
    assert sandbox._manual_host("[a](evil.xyz:8080)") == "evil.xyz"
    assert sandbox._manual_host("evil.xyz:8080]/x") == "evil.xyz"
    assert sandbox._manual_host("[a](https://evil.xyz:8080)") == "evil.xyz"
    assert sandbox._manual_host("[a](evil.xyz:)") == "evil.xyz"

def test_markdown_destination_with_port_still_reaches_the_blacklist():
    for url in ("[x](evil.xyz:8080)", "https://x]@evil.xyz:8080)", "[https://ok.com](https://evil.xyz:8080)"):
        res = analyze_url(url, expand=False, blacklist=frozenset({"evil.xyz"}))
        assert res["domain"] == "evil.xyz", url
        assert res["is_blacklisted"] is True, url
        assert res["verdict"] == "MALICIOSO", url


# --- La sospecha por caracteres ocultos ignora la cola final (emoji con VS16, ZWJ, ZWSP) ---

_INVISIBLE_OR_EMOJI_TAILS = (
    "\u26a0\ufe0f",
    "\u2714\ufe0f",
    "\U0001F468\u200d\U0001F469\u200d\U0001F467",
    "\u200b",
)

def test_emoji_or_invisible_tail_after_an_official_link_is_not_suspicious():
    for tail in _INVISIBLE_OR_EMOJI_TAILS:
        url = "https://www.nequi.com.co" + tail
        res = analyze_url(url, expand=False, blacklist=frozenset())
        assert res["domain"] == "www.nequi.com.co", repr(tail)
        assert res["verdict"] == "SEGURO", repr(tail)
        assert not _has_invalid_host_finding(res), repr(tail)
        assert sandbox._parse_host(url) == ("www.nequi.com.co", False), repr(tail)
    res = analyze_url("https://www.bancolombia.com\u200b", expand=False, blacklist=frozenset())
    assert res["verdict"] == "SEGURO"
    assert not _has_invalid_host_finding(res)

def test_emoji_tail_does_not_hide_a_blacklisted_domain():
    res = analyze_url("https://dian-notificaciones.xyz\u26a0\ufe0f", expand=False, blacklist=_DIAN)
    assert res["domain"] == "dian-notificaciones.xyz"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    assert not _has_invalid_host_finding(res)

def test_invisible_chars_inside_the_host_still_mark_it_suspicious_even_with_a_tail():
    for url in (
        "https://ex\u200bample.com/",
        "https://www.nequi\u200d.com.co",
        "https://ex\u200bample.com\u200b",
        "https://ex\ufe0fample.com\u26a0\ufe0f",
    ):
        res = analyze_url(url, expand=False, blacklist=frozenset())
        assert res["verdict"] == "SOSPECHOSO", repr(url)
        assert _has_invalid_host_finding(res), repr(url)
        assert sandbox._parse_host(url)[1] is True, repr(url)

def test_strip_trailing_tail():
    assert sandbox._strip_trailing_tail("a.com") == "a.com"
    assert sandbox._strip_trailing_tail("a.com\u200b") == "a.com"
    assert sandbox._strip_trailing_tail("a.com\u26a0\ufe0f") == "a.com"
    # ignorables y puntuación mezclados al final
    assert sandbox._strip_trailing_tail("a.com\u200d\u200b.\ufe0f,”") == "a.com"
    # lo interior y lo inicial no se tocan
    assert sandbox._strip_trailing_tail("ex\u200bample.com\u200b") == "ex\u200bample.com"
    assert sandbox._strip_trailing_tail("\u200ba.com") == "\u200ba.com"
    # ":" no es puntuación final (IPv6 que termina en "::")
    assert sandbox._strip_trailing_tail("a.com:") == "a.com:"
    assert sandbox._strip_trailing_tail("") == ""


# --- Un host sin ninguna letra ni dígito no puede ser real ---

def test_hosts_without_letters_or_digits_are_flagged():
    for url in ("https://-", "https://_", "https://-.-"):
        res = analyze_url(url, expand=False, blacklist=frozenset())
        assert res["status"] == "success", url
        assert res["verdict"] == "SOSPECHOSO", url
        assert _has_invalid_host_finding(res), url

def test_is_invalid_host_requires_a_letter_or_a_digit():
    for ok in ("a.com", "123.example.com", "::1", "2001:db8::", "xn--abc.com", "münchen.de"):
        assert sandbox._is_invalid_host(ok) is False, ok
    for bad in ("-", "_", "-.-", "::"):
        assert sandbox._is_invalid_host(bad) is True, bad


# --- Controles C0 y espacios al inicio de la URL ---

def test_leading_control_chars_and_spaces_do_not_hide_the_host():
    for url, domain, blacklist in (
        ("\x00https://listado.site/x", "listado.site", _LISTADO),
        ("\x01https://dian-notificaciones.xyz/x", "dian-notificaciones.xyz", _DIAN),
        ("  \x00 https://listado.site ", "listado.site", _LISTADO),
    ):
        res = analyze_url(url, expand=False, blacklist=blacklist)
        assert res["domain"] == domain, repr(url)
        assert res["is_blacklisted"] is True, repr(url)

def test_normalize_url_strips_c0_controls_and_spaces_at_both_ends():
    assert sandbox._normalize_url("\x00http://a.com") == "http://a.com"
    assert sandbox._normalize_url("\x01 //a.com \x1f") == "http://a.com"
    assert sandbox._normalize_url("  a.com\x00") == "http://a.com"


# --- El reintento de _parse_host solo vale si deja un dominio ---

def test_unreadable_host_whose_retry_is_empty_is_suspicious_not_an_error():
    for url in ("http://[", "http://]/"):
        res = analyze_url(url, expand=False, blacklist=frozenset())
        assert res["status"] == "success", url
        assert res["verdict"] == "SOSPECHOSO", url
        assert res["domain"] == url, url
        assert _has_invalid_host_finding(res), url
    # control: sin ningún carácter de host sigue siendo un error
    assert analyze_url("http://", expand=False, blacklist=frozenset())["status"] == "error"


# --- Barras iniciales de más: "//" y "///" abren el host igual que un navegador ---

def test_extra_leading_slashes_expose_the_host_like_a_scheme_relative_url():
    for blacklist in (_EVIL, frozenset()):
        reference = analyze_url("https:///evil.xyz", expand=False, blacklist=blacklist)
        assert reference["domain"] == "evil.xyz"
        for url in ("//evil.xyz", "///evil.xyz", "////evil.xyz"):
            res = analyze_url(url, expand=False, blacklist=blacklist)
            assert res["domain"] == "evil.xyz", url
            for key in ("is_blacklisted", "verdict", "risk_score", "findings"):
                assert res[key] == reference[key], (url, key)
    assert sandbox._normalize_url("///a.com") == "http://a.com"

def test_single_leading_slash_is_not_a_scheme_relative_url():
    res = analyze_url("/evil.xyz", expand=False, blacklist=_EVIL)
    assert res["domain"] == "/evil.xyz"
    assert res["is_blacklisted"] is False
    assert _has_invalid_host_finding(res)


# --- Cota de longitud de la URL: solo se lee el host de los primeros MAX_URL_LEN caracteres ---

def _spy_parse_host(monkeypatch):
    seen = []
    real = sandbox._parse_host
    def _spy(raw):
        seen.append(raw)
        return real(raw)
    monkeypatch.setattr(sandbox, "_parse_host", _spy)
    return seen

def _has_long_url_finding(res):
    return any(f.startswith("URL demasiado larga") for f in res["findings"])

def _padded_url(base, total):
    return base + "a" * (total - len(base))

def test_overlong_url_only_parses_the_first_max_url_len_chars_and_is_flagged(monkeypatch):
    seen = _spy_parse_host(monkeypatch)
    url = "http://" + "a" * 20000 + ".com"
    res = analyze_url(url, expand=False, blacklist=frozenset())
    assert seen and all(len(raw) <= sandbox.MAX_URL_LEN for raw in seen)
    assert f"URL demasiado larga ({len(url)} caracteres)" in res["findings"]
    assert res["verdict"] != "SEGURO"

def test_overlong_url_keeps_the_full_input_adds_40_and_still_checks_the_blacklist():
    url = "http://listado.site/" + "a" * 20000
    res = analyze_url(url, expand=False, blacklist=_LISTADO)
    assert res["is_blacklisted"] is True
    assert _has_long_url_finding(res)
    assert res["original_url"] == url
    assert res["expanded_url"] == url
    assert res["redirect_chain"] == [url]
    # con un dominio oficial no hay otro hallazgo: la URL larga suma exactamente 40
    res = analyze_url("https://www.bancolombia.com/" + "a" * 20000, expand=False, blacklist=frozenset())
    assert res["domain"] == "www.bancolombia.com"
    assert res["risk_score"] == 40
    assert res["verdict"] == "SOSPECHOSO"

def test_overlong_shortener_url_is_not_unrolled(monkeypatch):
    calls = []
    def _head(url, timeout=3):
        calls.append(url)
        return (301, "https://example.org/final")
    monkeypatch.setattr(sandbox, "_head_request", _head)
    url = "https://bit.ly/" + "a" * 20000
    res = analyze_url(url, blacklist=frozenset())
    assert res["is_shortener"] is True
    assert calls == []
    assert _has_long_url_finding(res)
    assert res["expanded_url"] == url
    assert res["redirect_chain"] == [url]
    assert res["telemetry"]["expansion_ms"] is None

def test_url_length_limit_is_inclusive(monkeypatch):
    calls = []
    def _head(url, timeout=3):
        calls.append(url)
        return (200, None)
    monkeypatch.setattr(sandbox, "_head_request", _head)
    exact = _padded_url("https://listado.site/", sandbox.MAX_URL_LEN)
    assert len(exact) == sandbox.MAX_URL_LEN
    assert not _has_long_url_finding(analyze_url(exact, expand=False, blacklist=_LISTADO))
    assert _has_long_url_finding(analyze_url(exact + "a", expand=False, blacklist=_LISTADO))
    # un acortador justo en el límite sí se desenrolla; con un carácter más, no
    shortener = _padded_url("https://bit.ly/", sandbox.MAX_URL_LEN)
    assert not _has_long_url_finding(analyze_url(shortener, blacklist=frozenset()))
    assert len(calls) == 1
    assert _has_long_url_finding(analyze_url(shortener + "a", blacklist=frozenset()))
    assert len(calls) == 1


# --- Segmentos "](" (markdown / ruta / fragmento) y autoridad no cerrada en la ventana ---

_UNCLOSED_AUTH_FINDING = (
    "Host inválido o con caracteres de evasión (autoridad más larga que la ventana de análisis)"
)

def test_markdown_or_path_bracket_paren_vectors_pick_highest_risk_segment():
    # Vector 1a: "](" en la ruta tras userinfo con "]" no tapa el host real de typosquatting
    u1 = "https://x]@banc0lombia-seguridad.cc/a](b"
    r1 = analyze_url(u1, expand=False, blacklist=frozenset())
    assert r1["domain"] == "banc0lombia-seguridad.cc"
    assert r1["is_typosquatting"] is True
    assert r1["impersonated_brand"] == "bancolombia"
    assert r1["verdict"] == "MALICIOSO"
    assert r1["original_url"] == u1 and r1["expanded_url"] == u1

    # Vector 1b: "](" en el fragmento hacia banco oficial no tapa el host real evil.xyz
    u2 = "https://x]@evil.xyz/#](https://www.bancolombia.com"
    r2_heur = analyze_url(u2, expand=False, blacklist=frozenset())
    assert r2_heur["domain"] == "evil.xyz"
    assert r2_heur["risk_score"] == 80
    assert r2_heur["verdict"] == "MALICIOSO"
    r2_bl = analyze_url(u2, expand=False, blacklist=frozenset({"evil.xyz"}))
    assert r2_bl["domain"] == "evil.xyz"
    assert r2_bl["is_blacklisted"] is True
    assert r2_bl["verdict"] == "MALICIOSO"

    # Vector 2: texto malicioso con destino oficial evalúa ambos y elige evil.xyz
    u3 = "https://evil.xyz](https://www.bancolombia.com)"
    r3 = analyze_url(u3, expand=False, blacklist=frozenset({"evil.xyz"}))
    assert r3["domain"] == "evil.xyz"
    assert r3["is_blacklisted"] is True
    assert r3["verdict"] == "MALICIOSO"
    assert r3["original_url"] == u3 and r3["expanded_url"] == u3

def test_markdown_with_two_official_urls_is_safe():
    for url in (
        "https://www.bancolombia.com](https://www.bancolombia.com)",
        "[https://www.bancolombia.com](https://www.bancolombia.com)",
    ):
        res = analyze_url(url, expand=False, blacklist=frozenset())
        assert res["domain"] == "www.bancolombia.com", url
        assert res["verdict"] == "SEGURO", url
        assert res["risk_score"] == 0, url
        assert res["findings"] == [], url
        assert res["original_url"] == url and res["expanded_url"] == url, url

def test_markdown_official_text_with_malicious_destination_is_malicious():
    url = "[https://www.bancolombia.com](https://evil.xyz)"
    res = analyze_url(url, expand=False, blacklist=frozenset({"evil.xyz"}))
    assert res["domain"] == "evil.xyz"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    assert res["original_url"] == url and res["expanded_url"] == url

def test_markdown_embedded_in_query_of_official_url_is_not_safe():
    url = "https://www.bancolombia.com/s?q=[a](https://evil.xyz)"
    res = analyze_url(url, expand=False, blacklist=frozenset({"evil.xyz"}))
    assert res["domain"] == "evil.xyz"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    assert res["verdict"] != "SEGURO"

def test_many_bracket_paren_segments_are_bounded_to_four(monkeypatch):
    seen = _spy_parse_host(monkeypatch)
    url = "https://www.bancolombia.com](" * 5000 + "https://evil.xyz"
    res = analyze_url(url, expand=False, blacklist=frozenset({"evil.xyz"}))
    assert len(seen) == 4
    assert res["domain"] == "evil.xyz"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    # todos los segmentos vacíos -> resultado de error NO_ANALIZADO
    empty_segs = analyze_url("](" * 5000, expand=False, blacklist=frozenset())
    assert empty_segs["status"] == "error"
    assert empty_segs["verdict"] == "NO_ANALIZADO"
    assert empty_segs["findings"] == ["No se pudo extraer un host de la entrada"]

def test_markdown_segment_preserves_expanded_url_when_shortener_unrolls(monkeypatch):
    monkeypatch.setattr(sandbox, "_head_request", _fake_head({
        "https://bit.ly/x": (301, "https://evil.xyz/login"),
    }))
    url = "[https://www.bancolombia.com](https://bit.ly/x)"
    res = analyze_url(url, expand=True, blacklist=frozenset({"evil.xyz"}))
    assert res["original_url"] == url
    assert res["expanded_url"] == "https://evil.xyz/login"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"

def test_overlong_url_with_unclosed_authority_in_window_is_malicious():
    for pad in ("\u200b" * 9000, "!" * 9000):
        url = "https://www.bancolombia.com" + pad + "@banc0lombia-seguridad.cc/"
        res = analyze_url(url, expand=False, blacklist=frozenset())
        assert res["verdict"] == "MALICIOSO", repr(pad[:4])
        assert res["risk_score"] >= 80, repr(pad[:4])
        assert _UNCLOSED_AUTH_FINDING in res["findings"], repr(pad[:4])
        assert _has_long_url_finding(res), repr(pad[:4])
    # control: URL larga cuya autoridad sí se cierra con "/" dentro de la ventana no recibe ese hallazgo extra
    ctrl = "https://www.bancolombia.com/" + "a" * 9000
    res_ctrl = analyze_url(ctrl, expand=False, blacklist=frozenset())
    assert _UNCLOSED_AUTH_FINDING not in res_ctrl["findings"]
    assert not _has_invalid_host_finding(res_ctrl)
    assert res_ctrl["risk_score"] == 40
    assert res_ctrl["verdict"] == "SOSPECHOSO"
    # tampoco se suma dos veces si el host ya era sospechoso dentro de la ventana
    already_susp = "https://www.bancol\u200bombia.com" + "\u200b" * 9000 + "@banc0lombia-seguridad.cc/"
    res_susp = analyze_url(already_susp, expand=False, blacklist=frozenset())
    assert res_susp["risk_score"] == 80
    assert res_susp["verdict"] == "MALICIOSO"
    assert sum(1 for f in res_susp["findings"] if f.startswith(_INVALID_HOST_FINDING)) == 1
