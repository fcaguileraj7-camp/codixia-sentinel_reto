"""
Pruebas de red y HTTP para UrlSandbox (rutas no ASCII y presupuesto de tiempo).
Reto Agente 2026 - SentinelGuard AI - Equipo Codixia
"""

import io
from types import SimpleNamespace
from typing import List, Optional

import pytest

import src.tools.url_sandbox as sandbox
from src.tools.url_sandbox import _head_request as real_head_request


class FakeSocket:
    """Socket simulado para registrar datos enviados sin conexion de red real."""

    def __init__(self, response_bytes: bytes = b"HTTP/1.1 200 OK\r\n\r\n") -> None:
        self.sent_bytes = bytearray()
        self.response_bytes = response_bytes
        self.is_closed = False
        self.timeout: Optional[float] = None

    def sendall(self, data: bytes) -> None:
        self.sent_bytes.extend(data)

    def makefile(self, mode: str = "r", *args, **kwargs) -> io.BytesIO:
        return io.BytesIO(self.response_bytes)

    def close(self) -> None:
        self.is_closed = True

    def settimeout(self, timeout: Optional[float]) -> None:
        self.timeout = timeout

    def shutdown(self, how: int) -> None:
        pass


def test_head_request_non_ascii_path_and_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que _head_request codifique ruta y query no ASCII en porcentaje sin lanzar."""
    fake_sock = FakeSocket()
    monkeypatch.setattr(sandbox, "_resolve_public_ip", lambda host: "93.184.216.34")
    monkeypatch.setattr(sandbox.socket, "create_connection", lambda address, timeout=None: fake_sock)
    monkeypatch.setattr(sandbox, "_head_request", real_head_request)

    status, location = sandbox._head_request("http://example.com/niño?q=á")

    assert status == 200
    assert location is None
    req_line = bytes(fake_sock.sent_bytes).split(b"\r\n")[0]
    assert b"/ni%C3%B1o?q=%C3%A1" in req_line


def test_head_request_preserves_existing_percent_encoding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que _head_request no re-escape secuencias %20 ya existentes."""
    fake_sock = FakeSocket()
    monkeypatch.setattr(sandbox, "_resolve_public_ip", lambda host: "93.184.216.34")
    monkeypatch.setattr(sandbox.socket, "create_connection", lambda address, timeout=None: fake_sock)
    monkeypatch.setattr(sandbox, "_head_request", real_head_request)

    status, _ = sandbox._head_request("http://example.com/foo%20bar?query=baz%20qux")

    assert status == 200
    req_line = bytes(fake_sock.sent_bytes).split(b"\r\n")[0]
    assert b"/foo%20bar?query=baz%20qux" in req_line
    assert b"%2520" not in bytes(fake_sock.sent_bytes)


def test_head_request_empty_path_defaults_to_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que una URL con ruta vacia use '/' como ruta en la peticion HTTP."""
    fake_sock_1 = FakeSocket()
    monkeypatch.setattr(sandbox, "_resolve_public_ip", lambda host: "93.184.216.34")
    monkeypatch.setattr(sandbox.socket, "create_connection", lambda address, timeout=None: fake_sock_1)
    monkeypatch.setattr(sandbox, "_head_request", real_head_request)

    status, _ = sandbox._head_request("http://example.com")
    assert status == 200
    req_line_1 = bytes(fake_sock_1.sent_bytes).split(b"\r\n")[0]
    assert req_line_1 == b"HEAD / HTTP/1.1"

    fake_sock_2 = FakeSocket()
    monkeypatch.setattr(sandbox.socket, "create_connection", lambda address, timeout=None: fake_sock_2)
    status, _ = sandbox._head_request("http://example.com?filter=active")
    assert status == 200
    req_line_2 = bytes(fake_sock_2.sent_bytes).split(b"\r\n")[0]
    assert req_line_2 == b"HEAD /?filter=active HTTP/1.1"


def test_expand_url_timeout_bounds_and_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que timeout sea <= EXPAND_TIMEOUT, <= restante y >= 0.1 en cada salto."""
    simulated_time = 100.0

    def fake_monotonic() -> float:
        return simulated_time

    fake_clock = SimpleNamespace(monotonic=fake_monotonic, perf_counter=fake_monotonic)
    monkeypatch.setattr(sandbox, "time", fake_clock)

    recorded_timeouts: List[float] = []

    def fake_head(url: str, timeout: float = sandbox.EXPAND_TIMEOUT):
        nonlocal simulated_time
        recorded_timeouts.append(timeout)
        if len(recorded_timeouts) == 1:
            simulated_time += 2.0
            return (302, "http://short.ly/hop2")
        elif len(recorded_timeouts) == 2:
            simulated_time += 4.0
            return (302, "http://short.ly/hop3")
        elif len(recorded_timeouts) == 3:
            simulated_time += 1.95
            return (302, "http://short.ly/hop4")
        return (200, None)

    monkeypatch.setattr(sandbox, "_head_request", fake_head)

    final_url, chain, err = sandbox._expand_url("http://short.ly/hop1")

    assert err is None
    assert final_url == "http://short.ly/hop4"
    assert chain == [
        "http://short.ly/hop1",
        "http://short.ly/hop2",
        "http://short.ly/hop3",
        "http://short.ly/hop4",
    ]
    assert recorded_timeouts == [3, 3, 2.0, 0.1]
    for recorded in recorded_timeouts:
        assert 0.1 <= recorded <= sandbox.EXPAND_TIMEOUT


def test_expand_url_budget_exhaustion_during_head(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que si el presupuesto se agota durante un HEAD, el salto devuelve error de presupuesto."""
    simulated_time = 100.0

    def fake_monotonic() -> float:
        return simulated_time

    fake_clock = SimpleNamespace(monotonic=fake_monotonic, perf_counter=fake_monotonic)
    monkeypatch.setattr(sandbox, "time", fake_clock)

    def fake_slow_head(url: str, timeout: float = sandbox.EXPAND_TIMEOUT):
        nonlocal simulated_time
        simulated_time += 8.5
        return (302, "http://example.com/unreachable")

    monkeypatch.setattr(sandbox, "_head_request", fake_slow_head)

    final_url, chain, err = sandbox._expand_url("http://bit.ly/slow")

    assert err is not None
    assert "Presupuesto de tiempo agotado" in err
    assert final_url == "http://bit.ly/slow"
    assert chain == ["http://bit.ly/slow"]


def test_expand_url_fast_head_does_not_exhaust_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que peticiones HEAD rapidas no agoten el presupuesto y completen la cadena."""
    simulated_time = 100.0

    def fake_monotonic() -> float:
        return simulated_time

    fake_clock = SimpleNamespace(monotonic=fake_monotonic, perf_counter=fake_monotonic)
    monkeypatch.setattr(sandbox, "time", fake_clock)

    def fake_fast_head(url: str, timeout: float = sandbox.EXPAND_TIMEOUT):
        nonlocal simulated_time
        simulated_time += 0.01
        if url == "http://bit.ly/fast":
            return (302, "http://bit.ly/fast2")
        elif url == "http://bit.ly/fast2":
            return (302, "http://example.com/destination")
        return (200, None)

    monkeypatch.setattr(sandbox, "_head_request", fake_fast_head)

    final_url, chain, err = sandbox._expand_url("http://bit.ly/fast")

    assert err is None
    assert final_url == "http://example.com/destination"
    assert chain == [
        "http://bit.ly/fast",
        "http://bit.ly/fast2",
        "http://example.com/destination",
    ]


def test_expand_url_budget_exhausted_before_head(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que si el tiempo restante es negativo antes de iniciar el salto, no se haga peticion."""
    simulated_time = 100.0

    def fake_monotonic() -> float:
        return simulated_time

    fake_clock = SimpleNamespace(monotonic=fake_monotonic, perf_counter=fake_monotonic)
    monkeypatch.setattr(sandbox, "time", fake_clock)
    monkeypatch.setattr(sandbox, "EXPAND_BUDGET", -1)

    def fake_uncalled_head(*args, **kwargs):
        raise AssertionError("No debe llamarse a _head_request cuando el presupuesto esta agotado")

    monkeypatch.setattr(sandbox, "_head_request", fake_uncalled_head)

    final_url, chain, err = sandbox._expand_url("http://bit.ly/expired")

    assert err is not None
    assert "Presupuesto de tiempo agotado" in err
    assert final_url == "http://bit.ly/expired"
    assert chain == ["http://bit.ly/expired"]
