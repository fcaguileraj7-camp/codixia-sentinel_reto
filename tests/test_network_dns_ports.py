"""
Pruebas para capa de red, DNS y puertos en UrlSandbox.
Cubre especificaciones N1, N2, N5 y eliminaci\u00f3n de _is_public_host.
"""

import socket
import ssl
import pytest
import src.tools.url_sandbox as sandbox
from src.tools.url_sandbox import _head_request as real_head_request


def test_single_dns_resolution_per_hop(monkeypatch):
    """
    T1: Verifica que cada salto de redirecci\u00f3n realice exactamente una sola
    resoluci\u00f3n DNS (socket.getaddrinfo).
    """
    monkeypatch.setattr(sandbox, "_head_request", real_head_request)
    dns_calls = []

    def _fake_getaddrinfo(host, port, *args, **kwargs):
        dns_calls.append((host, port))
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

    def _fake_create_connection(address, timeout=None):
        raise OSError("fallo de conexi\u00f3n simulado")

    monkeypatch.setattr(sandbox.socket, "getaddrinfo", _fake_getaddrinfo)
    monkeypatch.setattr(sandbox.socket, "create_connection", _fake_create_connection)

    url_final, chain, err = sandbox._expand_url("https://bit.ly/x")
    assert len(dns_calls) == 1
    assert dns_calls[0][0] == "bit.ly"
    assert "OSError" in err


def test_explicit_and_implicit_ports(monkeypatch):
    """
    T2: Verifica que _head_request asigne siempre puerto expl\u00edcito a http.client:
    80 para HTTP, 443 para HTTPS, o el puerto num\u00e9rico presente en la URL.
    """
    monkeypatch.setattr(sandbox, "_head_request", real_head_request)
    monkeypatch.setattr(sandbox, "_resolve_public_ip", lambda host: "2606:4700::22")

    recorded = []

    def _fake_create_connection(address, timeout=None):
        recorded.append(address)
        raise OSError("intercepci\u00f3n de conexi\u00f3n")

    monkeypatch.setattr(sandbox.socket, "create_connection", _fake_create_connection)

    # HTTP con puerto impl\u00edcito -> 80 (no toma :22 del final de la IPv6)
    with pytest.raises(OSError):
        sandbox._head_request("http://[2606:4700::22]/x")
    assert recorded[-1] == ("2606:4700::22", 80)

    # HTTPS con puerto impl\u00edcito -> 443
    with pytest.raises(OSError):
        sandbox._head_request("https://[2606:4700::22]/x")
    assert recorded[-1] == ("2606:4700::22", 443)

    # HTTP con puerto expl\u00edcito 8080 -> 8080
    with pytest.raises(OSError):
        sandbox._head_request("http://[2606:4700::22]:8080/x")
    assert recorded[-1] == ("2606:4700::22", 8080)

    # HTTP con IPv6 terminada en ::1 -> 80
    with pytest.raises(OSError):
        sandbox._head_request("http://[2606:4700::1]/x")
    assert recorded[-1] == ("2606:4700::22", 80)


class _CloseTrackingSocket:
    """Socket simulado para registrar llamadas al m\u00e9todo close."""

    def __init__(self):
        self.closed = False
        self.close_count = 0

    def close(self):
        self.closed = True
        self.close_count += 1

    def sendall(self, *args, **kwargs):
        raise OSError("fallo de env\u00edo HTTP")

    def send(self, *args, **kwargs):
        raise OSError("fallo de env\u00edo HTTP")


def test_head_request_closes_socket_on_ssl_error(monkeypatch):
    """
    T5 (HTTPS): Verifica que si wrap_socket lanza una excepci\u00f3n, el socket TCP
    se cierre antes de relanzar el error.
    """
    monkeypatch.setattr(sandbox, "_head_request", real_head_request)
    fake_sock = _CloseTrackingSocket()

    monkeypatch.setattr(sandbox, "_resolve_public_ip", lambda host: "93.184.216.34")
    monkeypatch.setattr(sandbox.socket, "create_connection", lambda addr, timeout=None: fake_sock)

    def _fake_wrap_socket(self, sock, *args, **kwargs):
        raise ssl.SSLError("Fallo simulado en handshake TLS")

    monkeypatch.setattr(ssl.SSLContext, "wrap_socket", _fake_wrap_socket)

    with pytest.raises(ssl.SSLError, match="Fallo simulado en handshake TLS"):
        sandbox._head_request("https://example.com/")

    assert fake_sock.closed is True
    assert fake_sock.close_count >= 1


def test_head_request_closes_socket_on_http_error(monkeypatch):
    """
    T5 (HTTP): Verifica que en la rama HTTP, ante errores de transmisi\u00f3n,
    el socket se cierre adecuadamente en el bloque finally.
    """
    monkeypatch.setattr(sandbox, "_head_request", real_head_request)
    fake_sock = _CloseTrackingSocket()

    monkeypatch.setattr(sandbox, "_resolve_public_ip", lambda host: "93.184.216.34")
    monkeypatch.setattr(sandbox.socket, "create_connection", lambda addr, timeout=None: fake_sock)

    with pytest.raises(OSError):
        sandbox._head_request("http://example.com/")

    assert fake_sock.closed is True
    assert fake_sock.close_count >= 1


def test_is_public_host_eliminated():
    """
    T8: Verifica que la funci\u00f3n _is_public_host haya sido eliminada de url_sandbox.
    """
    assert not hasattr(sandbox, "_is_public_host")
