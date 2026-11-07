"""
Pruebas de cobertura para límites de tiempo y esquemas de redirección en UrlSandbox.
"""

import io
from typing import List, Optional
import pytest

import src.tools.url_sandbox as sandbox
from src.tools.url_sandbox import _head_request as real_head_request


class FakeSocket:
    """Socket simulado para responder peticiones HEAD sin tráfico de red."""

    def __init__(self, response_bytes: bytes = b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n") -> None:
        self.response_bytes = response_bytes
        self.sent_bytes = bytearray()
        self.closed = False

    def sendall(self, data: bytes) -> None:
        self.sent_bytes.extend(data)

    def makefile(self, *args, **kwargs) -> io.BytesIO:
        return io.BytesIO(self.response_bytes)

    def close(self) -> None:
        self.closed = True

    def settimeout(self, timeout: Optional[float]) -> None:
        pass


def test_head_request_passes_timeout_to_create_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verifica que _head_request propague el parámetro timeout especificado
    directamente a socket.create_connection.
    """
    monkeypatch.setattr(sandbox, "_head_request", real_head_request)
    monkeypatch.setattr(sandbox, "_resolve_public_ip", lambda host: "93.184.216.34")

    recorded_timeouts: List[Optional[float]] = []

    def _fake_create_connection(address, *args, **kwargs) -> FakeSocket:
        timeout = kwargs.get("timeout", args[0] if args else None)
        recorded_timeouts.append(timeout)
        return FakeSocket()

    monkeypatch.setattr(sandbox.socket, "create_connection", _fake_create_connection)

    status, location = sandbox._head_request("http://example.com/test", timeout=1.5)

    assert status == 200
    assert location is None
    assert len(recorded_timeouts) == 1
    assert recorded_timeouts[0] == 1.5


def test_expand_url_passes_positive_bounded_timeout_to_head_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verifica que _expand_url pase a _head_request un timeout positivo menor
    o igual a EXPAND_TIMEOUT en cada intento de salto.
    """
    recorded_timeouts: List[float] = []

    def _fake_head(url: str, timeout: float = sandbox.EXPAND_TIMEOUT):
        recorded_timeouts.append(timeout)
        if len(recorded_timeouts) == 1:
            return (301, "http://short.example.com/next")
        return (200, None)

    monkeypatch.setattr(sandbox, "_head_request", _fake_head)

    final_url, chain, err = sandbox._expand_url("http://short.example.com/start")

    assert err is None
    assert final_url == "http://short.example.com/next"
    assert len(recorded_timeouts) == 2
    for t in recorded_timeouts:
        assert 0 < t <= sandbox.EXPAND_TIMEOUT


def test_expand_url_rejects_non_http_location_without_second_head(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verifica que ante una redirección a un esquema no permitido como mailto:,
    _expand_url y analyze_url terminen con el error correspondiente sin intentar
    una segunda petición HEAD.
    """
    head_calls: List[str] = []

    def _fake_head(url: str, timeout: float = sandbox.EXPAND_TIMEOUT):
        head_calls.append(url)
        if len(head_calls) == 1:
            return (301, "mailto:x@y.com")
        return (200, None)

    monkeypatch.setattr(sandbox, "_head_request", _fake_head)

    res = sandbox.analyze_url("https://bit.ly/short")

    assert res["expansion_error"] == "Esquema o host no permitido"
    assert res["expanded_url"] == "mailto:x@y.com"
    assert res["redirect_chain"] == ["https://bit.ly/short", "mailto:x@y.com"]
    assert len(head_calls) == 1

    head_calls.clear()
    final_url, chain, err = sandbox._expand_url("https://bit.ly/short")

    assert err == "Esquema o host no permitido"
    assert final_url == "mailto:x@y.com"
    assert chain == ["https://bit.ly/short", "mailto:x@y.com"]
    assert len(head_calls) == 1


def test_markdown_with_one_oversized_segment_is_charged_only_once() -> None:
    """
    Si un segmento markdown ya supera MAX_URL_LEN por sí solo, el cargo de 40 puntos por
    URL demasiado larga se aplica una vez (no una por el segmento y otra por el total).
    """
    oversized = "https://www.sitio-largo.com/" + "a" * (sandbox.MAX_URL_LEN + 100)
    res = sandbox.analyze_url(f"[texto]({oversized})", expand=False, blacklist=frozenset())

    too_long = [f for f in res["findings"] if f.startswith("URL demasiado larga")]
    assert len(too_long) == 1
    assert res["risk_score"] == 40
    assert res["verdict"] == "SOSPECHOSO"
