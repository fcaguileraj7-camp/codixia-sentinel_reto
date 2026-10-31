"""
Pruebas para validación de direcciones IP y capa anti-SSRF en UrlSandbox.
SentinelGuard AI - Reto Agente 2026.
"""

import ipaddress
import socket
import pytest

import src.tools.url_sandbox as sandbox


@pytest.mark.parametrize(
    "ip_literal,expected",
    [
        ("8.8.8.8", "8.8.8.8"),
        ("2606:4700:4700::1111", "2606:4700:4700::1111"),
        ("2001:4860:4860::8888", "2001:4860:4860::8888"),
    ],
)
def test_resolve_public_ip_accepted_literals(ip_literal, expected):
    """Verifica que las IPs públicas globales sean aceptadas y devueltas sin cambio."""
    assert sandbox._resolve_public_ip(ip_literal) == expected


@pytest.mark.parametrize(
    "ip_literal",
    [
        "127.0.0.1",
        "10.0.0.1",
        "192.168.1.1",
        "169.254.169.254",
        "100.64.0.1",
        "::1",
        "::",
        "::ffff:127.0.0.1",
        "2002:7f00:1::",
        "64:ff9b::7f00:1",
        "64:ff9b::a9fe:a9fe",
        "64:ff9b:1::1",
        "::127.0.0.1",
        "224.0.0.1",
        "ff02::1",
        "fec0::1",
    ],
)
def test_resolve_public_ip_rejected_literals(ip_literal):
    """Verifica que IPs privadas, reservadas, multicast, site-local y NAT64 sean rechazadas (None)."""
    assert sandbox._resolve_public_ip(ip_literal) is None


@pytest.mark.parametrize(
    "teredo_literal",
    [
        "2001:0:a00:1::f7f7:f7f7",  # servidor privado (10.0.0.1), cliente público (8.8.8.8)
        "2001:0:808:808::3f57:fefe",  # servidor público (8.8.8.8), cliente privado (192.168.1.1)
        "2001:0:ac10:1::fefe:fefe",  # servidor privado (172.16.0.1), cliente público (1.1.1.1)
        "2001:0:101:101::f5f5:f5f5",  # servidor público (1.1.1.1), cliente privado (10.10.10.10)
    ],
)
def test_resolve_public_ip_teredo_private_embedded(teredo_literal):
    """Rechaza direcciones Teredo cuando el servidor o el cliente embebido es una IPv4 privada."""
    assert sandbox._resolve_public_ip(teredo_literal) is None


def test_resolve_public_ip_6to4_always_rejected():
    """6to4 (2002::/16) se rechaza entero, aunque la IPv4 embebida sea pública (2002:0808:0808:: -> 8.8.8.8): fail-closed."""
    assert sandbox._resolve_public_ip("2002:0808:0808::") is None


@pytest.mark.parametrize(
    "mock_addrinfo",
    [
        [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0)),
        ],
        [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0)),
        ],
        [
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2606:4700:4700::1111", 0, 0, 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.1", 0)),
        ],
        [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0)),
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", 0, 0, 0)),
        ],
    ],
)
def test_resolve_public_ip_mixed_responses(monkeypatch, mock_addrinfo):
    """Una resolución que devuelve al menos una IP privada o no pública debe fallar completa (None)."""
    monkeypatch.setattr(socket, "getaddrinfo", lambda host, port, *a, **k: mock_addrinfo)
    assert sandbox._resolve_public_ip("mixed.example.com") is None


@pytest.mark.parametrize(
    "scenario",
    ["empty", "gaierror", "unicode_error"],
)
def test_resolve_public_ip_resolution_errors(monkeypatch, scenario):
    """Comprueba que respuestas vacías o excepciones de resolución devuelvan None sin lanzar."""
    if scenario == "empty":
        monkeypatch.setattr(socket, "getaddrinfo", lambda host, port, *a, **k: [])
    elif scenario == "gaierror":
        def _gai(*a, **k):
            raise socket.gaierror(-2, "Name or service not known")
        monkeypatch.setattr(socket, "getaddrinfo", _gai)
    elif scenario == "unicode_error":
        def _unicode(*a, **k):
            raise UnicodeError("Etiqueta de dominio inválida")
        monkeypatch.setattr(socket, "getaddrinfo", _unicode)

    assert sandbox._resolve_public_ip("bad.domain.example") is None


@pytest.mark.parametrize(
    "ip_str,expected",
    [
        ("8.8.8.8", True),
        ("1.1.1.1", True),
        ("2606:4700:4700::1111", True),
        ("2001:4860:4860::8888", True),
        ("::ffff:8.8.8.8", True),
        ("127.0.0.1", False),
        ("10.0.0.1", False),
        ("172.16.0.1", False),
        ("192.168.1.1", False),
        ("169.254.169.254", False),
        ("100.64.0.1", False),
        ("224.0.0.1", False),
        ("255.255.255.255", False),
        ("0.0.0.0", False),
        ("::1", False),
        ("::", False),
        ("ff02::1", False),
        ("fec0::1", False),
        ("::127.0.0.1", False),
        ("::ffff:127.0.0.1", False),
        ("64:ff9b::7f00:1", False),
        ("64:ff9b::a9fe:a9fe", False),
        ("64:ff9b:1::1", False),
        ("2002:7f00:1::", False),
        ("2001:0:a00:1::f7f7:f7f7", False),
        ("2001:0:808:808::3f57:fefe", False),
    ],
)
def test_is_public_ip_direct_instances(ip_str, expected):
    """Test unitario directo de _is_public_ip usando instancias de ipaddress.ip_address."""
    ip_obj = ipaddress.ip_address(ip_str)
    assert sandbox._is_public_ip(ip_obj) is expected
