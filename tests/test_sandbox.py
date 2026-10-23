"""
Pruebas Unitarias para UrlSandbox
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
"""

from src.tools.url_sandbox import analyze_url

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
