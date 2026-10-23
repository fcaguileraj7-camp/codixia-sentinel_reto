"""
Pruebas Unitarias para UrlSandbox
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
"""

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
