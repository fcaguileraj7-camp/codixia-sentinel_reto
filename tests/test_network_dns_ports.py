"""
Pruebas para capa de red, DNS y puertos en UrlSandbox.
Cubre el conteo de DNS, los puertos, el cierre de sockets y la eliminación de _is_public_host.
"""

import io
import socket
import ssl
import pytest
import src.tools.url_sandbox as sandbox
from src.tools.url_sandbox import _head_request as real_head_request


class _FakeSocket:
    """Socket simulado para registrar operaciones y responder cabeceras HTTP."""

    def __init__(self, response_bytes: bytes) -> None:
        self.response_bytes = response_bytes
        self.sent_bytes = bytearray()
        self.closed = False

    def sendall(self, data: bytes) -> None:
        self.sent_bytes.extend(data)

    def makefile(self, *args, **kwargs) -> io.BytesIO:
        return io.BytesIO(self.response_bytes)

    def close(self) -> None:
        self.closed = True

    def settimeout(self, timeout) -> None:
        pass


def test_single_dns_resolution_per_hop(monkeypatch):
    """
    Verifica que cada salto en una cadena 301 -> 301 -> 200 realice exactamente una sola
    resolución DNS con socket.getaddrinfo y que socket.create_connection reciba como
    address[0] la IP devuelta por el DNS falso en cada salto.
    """
    monkeypatch.setattr(sandbox, "_head_request", real_head_request)

    dns_map = {
        "hop1.example.com": "93.184.216.31",
        "hop2.example.com": "93.184.216.32",
        "hop3.example.com": "93.184.216.33",
    }
    dns_calls = []

    def _fake_getaddrinfo(host, port, *args, **kwargs):
        dns_calls.append((host, port))
        ip = dns_map.get(host, "93.184.216.34")
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0))]

    responses = {
        "93.184.216.31": b"HTTP/1.1 301 Moved Permanently\r\nLocation: http://hop2.example.com/step2\r\nContent-Length: 0\r\n\r\n",
        "93.184.216.32": b"HTTP/1.1 301 Moved Permanently\r\nLocation: http://hop3.example.com/final\r\nContent-Length: 0\r\n\r\n",
        "93.184.216.33": b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n",
    }
    connection_calls = []

    def _fake_create_connection(address, timeout=None):
        connection_calls.append(address)
        ip = address[0]
        return _FakeSocket(responses[ip])

    monkeypatch.setattr(sandbox.socket, "getaddrinfo", _fake_getaddrinfo)
    monkeypatch.setattr(sandbox.socket, "create_connection", _fake_create_connection)

    url_final, chain, err = sandbox._expand_url("http://hop1.example.com/start")

    assert err is None
    assert url_final == "http://hop3.example.com/final"
    assert chain == [
        "http://hop1.example.com/start",
        "http://hop2.example.com/step2",
        "http://hop3.example.com/final",
    ]
    assert len(dns_calls) == len(chain)
    assert len(dns_calls) == 3
    assert len(connection_calls) == 3
    for call, expected_ip in zip(connection_calls, ["93.184.216.31", "93.184.216.32", "93.184.216.33"]):
        assert call[0] == expected_ip


def test_dns_resolution_aborted_on_connection_error(monkeypatch):
    """
    Verifica que ante un fallo de conexión durante el primer salto se registre una
    única resolución DNS y se devuelva el error de conexión.
    """
    monkeypatch.setattr(sandbox, "_head_request", real_head_request)
    dns_calls = []

    def _fake_getaddrinfo(host, port, *args, **kwargs):
        dns_calls.append((host, port))
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

    def _fake_create_connection(address, timeout=None):
        raise OSError("fallo de conexión simulado")

    monkeypatch.setattr(sandbox.socket, "getaddrinfo", _fake_getaddrinfo)
    monkeypatch.setattr(sandbox.socket, "create_connection", _fake_create_connection)

    url_final, chain, err = sandbox._expand_url("https://bit.ly/x")
    assert len(dns_calls) == 1
    assert dns_calls[0][0] == "bit.ly"
    assert "OSError" in err


def test_explicit_and_implicit_ports(monkeypatch):
    """
    Verifica que _head_request asigne siempre puerto explícito a http.client:
    80 para HTTP, 443 para HTTPS, o el puerto numérico presente en la URL.
    """
    monkeypatch.setattr(sandbox, "_head_request", real_head_request)
    monkeypatch.setattr(sandbox, "_resolve_public_ip", lambda host: host)

    recorded = []

    def _fake_create_connection(address, timeout=None):
        recorded.append(address)
        raise OSError("intercepción de conexión")

    monkeypatch.setattr(sandbox.socket, "create_connection", _fake_create_connection)

    # HTTP con puerto implícito -> 80 (no toma :22 del final de la IPv6)
    with pytest.raises(OSError):
        sandbox._head_request("http://[2606:4700::22]/x")
    assert recorded[-1] == ("2606:4700::22", 80)

    # HTTPS con puerto implícito -> 443
    with pytest.raises(OSError):
        sandbox._head_request("https://[2606:4700::22]/x")
    assert recorded[-1] == ("2606:4700::22", 443)

    # HTTP con puerto explícito 8080 -> 8080
    with pytest.raises(OSError):
        sandbox._head_request("http://[2606:4700::22]:8080/x")
    assert recorded[-1] == ("2606:4700::22", 8080)

    # HTTP con IPv6 terminada en ::1 -> 80
    with pytest.raises(OSError):
        sandbox._head_request("http://[2606:4700::1]/x")
    assert recorded[-1] == ("2606:4700::1", 80)


class _CloseTrackingSocket:
    """Socket simulado para registrar llamadas al método close."""

    def __init__(self):
        self.closed = False
        self.close_count = 0

    def close(self):
        self.closed = True
        self.close_count += 1

    def sendall(self, *args, **kwargs):
        raise OSError("fallo de envío HTTP")

    def send(self, *args, **kwargs):
        raise OSError("fallo de envío HTTP")


def test_head_request_closes_socket_on_ssl_error(monkeypatch):
    """
    (HTTPS) Verifica que si wrap_socket lanza una excepción, el socket TCP
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
    (HTTP) Verifica que en la rama HTTP, ante errores de transmisión,
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
    Verifica que la función _is_public_host haya sido eliminada de url_sandbox.
    """
    assert not hasattr(sandbox, "_is_public_host")
