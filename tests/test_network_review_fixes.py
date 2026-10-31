"""
Pruebas de regresión para las correcciones de revisión de red (F1, F3, F4, F5).
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
"""

import io
import pytest

import src.tools.url_sandbox as sandbox
from src.tools.url_sandbox import _head_request as real_head_request


def _fake_head(routes):
    """Simula _head_request devolviendo tuplas (status, location) según la URL."""
    def _head(url, timeout=3, **kwargs):
        return routes.get(url, (200, None))
    return _head


class FakeSocket:
    """Socket simulado para registrar peticiones HTTP sin red real."""

    def __init__(self, response_bytes: bytes = b"HTTP/1.1 200 OK\r\n\r\n") -> None:
        self.sent_bytes = bytearray()
        self.response_bytes = response_bytes
        self.is_closed = False

    def sendall(self, data: bytes) -> None:
        self.sent_bytes.extend(data)

    def makefile(self, mode: str = "r", *args, **kwargs) -> io.BytesIO:
        return io.BytesIO(self.response_bytes)

    def close(self) -> None:
        self.is_closed = True


# ============================================================================
# F1: Detección de saltos intermedios en bucles de redirección
# ============================================================================

def test_f1_redirect_loop_aba_detects_blacklisted_intermediate(monkeypatch):
    """Bucle A -> B -> A evalúa el salto intermedio B aunque expanded_url == start."""
    routes = {
        "http://bit.ly/loop": (301, "https://malicioso.org/hop"),
        "https://malicioso.org/hop": (301, "http://bit.ly/loop"),
    }
    monkeypatch.setattr(sandbox, "_head_request", _fake_head(routes))

    res = sandbox.analyze_url(
        "bit.ly/loop",
        expand=True,
        blacklist=frozenset({"malicioso.org"}),
    )

    assert res["status"] == "success"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    assert res["risk_score"] == 100
    assert "Salto intermedio en lista negra local (malicioso.org)" in res["findings"]
    assert res["expansion_error"] == "Bucle de redirecciones"
    assert res["redirect_chain"] == [
        "http://bit.ly/loop",
        "https://malicioso.org/hop",
    ]


def test_f1_redirect_loop_abcb_detects_last_intermediate(monkeypatch):
    """Bucle A -> B -> C -> B evalúa el salto C aunque vuelva a un salto previo B."""
    routes = {
        "http://bit.ly/start": (301, "https://limpio-b.com/hop"),
        "https://limpio-b.com/hop": (301, "https://malicioso-c.org/gate"),
        "https://malicioso-c.org/gate": (301, "https://limpio-b.com/hop"),
    }
    monkeypatch.setattr(sandbox, "_head_request", _fake_head(routes))

    res = sandbox.analyze_url(
        "bit.ly/start",
        expand=True,
        blacklist=frozenset({"malicioso-c.org"}),
    )

    assert res["status"] == "success"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    assert res["risk_score"] == 100
    assert "Salto intermedio en lista negra local (malicioso-c.org)" in res["findings"]
    assert res["expansion_error"] == "Bucle de redirecciones"
    assert res["redirect_chain"] == [
        "http://bit.ly/start",
        "https://limpio-b.com/hop",
        "https://malicioso-c.org/gate",
    ]


def test_f1_chain_without_loop_maintains_behavior(monkeypatch):
    """Cadena sin bucle sigue detectando saltos intermedios listados con normalidad."""
    routes = {
        "http://bit.ly/normal": (301, "https://intermedio.org/step"),
        "https://intermedio.org/step": (301, "https://final.com/dest"),
        "https://final.com/dest": (200, None),
    }
    monkeypatch.setattr(sandbox, "_head_request", _fake_head(routes))

    res = sandbox.analyze_url(
        "bit.ly/normal",
        expand=True,
        blacklist=frozenset({"intermedio.org"}),
    )

    assert res["status"] == "success"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    assert res["expanded_url"] == "https://final.com/dest"
    assert "Salto intermedio en lista negra local (intermedio.org)" in res["findings"]
    assert res["expansion_error"] is None


def test_f1_repeated_blacklisted_hop_counted_only_once(monkeypatch):
    """Un dominio intermedio listado repetido en la cadena solo puntúa y se reporta una vez."""
    routes = {
        "http://bit.ly/multi": (301, "https://repetido.org/1"),
        "https://repetido.org/1": (301, "https://repetido.org/2"),
        "https://repetido.org/2": (301, "https://final.com/end"),
        "https://final.com/end": (200, None),
    }
    monkeypatch.setattr(sandbox, "_head_request", _fake_head(routes))

    res = sandbox.analyze_url(
        "bit.ly/multi",
        expand=True,
        blacklist=frozenset({"repetido.org"}),
    )

    assert res["status"] == "success"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    finding = "Salto intermedio en lista negra local (repetido.org)"
    assert res["findings"].count(finding) == 1


# ============================================================================
# F3: Preservación de parámetros de matriz (;params) en HEAD request
# ============================================================================

def test_f3_head_request_preserves_matrix_parameters(monkeypatch):
    """_head_request conserva ;params en la ruta usando urlsplit (/a;b=1?q=2)."""
    fake_sock = FakeSocket()
    monkeypatch.setattr(sandbox, "_head_request", real_head_request)
    monkeypatch.setattr(sandbox, "_resolve_public_ip", lambda host: "93.184.216.34")
    monkeypatch.setattr(sandbox.socket, "create_connection", lambda address, timeout=None: fake_sock)

    status, location = sandbox._head_request("http://x.com/a;b=1?q=2")

    assert status == 200
    req_line = bytes(fake_sock.sent_bytes).split(b"\r\n")[0]
    assert req_line == b"HEAD /a;b=1?q=2 HTTP/1.1"


# ============================================================================
# F4: Cierre explícito de la respuesta (resp.close()) antes de conn.close()
# ============================================================================

def test_f4_head_request_closes_response_on_success(monkeypatch):
    """Verifica que resp.close() se llame en el finally antes de conn.close() en caso exitoso."""
    events = []

    class MockResponse:
        def __init__(self):
            self.status = 200

        def getheader(self, name):
            events.append("getheader")
            return "https://destino.com"

        def close(self):
            events.append("resp.close")

    class MockConnection:
        def __init__(self, host, ip, **kwargs):
            pass

        def request(self, method, path, headers=None):
            events.append("request")

        def getresponse(self):
            events.append("getresponse")
            return MockResponse()

        def close(self):
            events.append("conn.close")

    monkeypatch.setattr(sandbox, "_head_request", real_head_request)
    monkeypatch.setattr(sandbox, "_resolve_public_ip", lambda host: "93.184.216.34")
    monkeypatch.setattr(sandbox, "_PinnedHTTPConnection", MockConnection)

    status, location = sandbox._head_request("http://example.com/check")

    assert status == 200
    assert location == "https://destino.com"
    assert "resp.close" in events
    assert "conn.close" in events
    assert events.index("resp.close") < events.index("conn.close")


def test_f4_head_request_closes_response_when_getheader_raises(monkeypatch):
    """Verifica que resp.close() se llame en el finally incluso cuando getheader lanza excepción."""
    events = []

    class FailingResponse:
        def __init__(self):
            self.status = 302

        def getheader(self, name):
            events.append("getheader_error")
            raise RuntimeError("Fallo simulado al leer cabecera")

        def close(self):
            events.append("resp.close")

    class MockConnection:
        def __init__(self, host, ip, **kwargs):
            pass

        def request(self, method, path, headers=None):
            pass

        def getresponse(self):
            events.append("getresponse")
            return FailingResponse()

        def close(self):
            events.append("conn.close")

    monkeypatch.setattr(sandbox, "_head_request", real_head_request)
    monkeypatch.setattr(sandbox, "_resolve_public_ip", lambda host: "93.184.216.34")
    monkeypatch.setattr(sandbox, "_PinnedHTTPConnection", MockConnection)

    with pytest.raises(RuntimeError, match="Fallo simulado al leer cabecera"):
        sandbox._head_request("http://example.com/error")

    assert "resp.close" in events
    assert "conn.close" in events
    assert events.index("resp.close") < events.index("conn.close")


# ============================================================================
# F5: Normalización de punto final (.rstrip('.')) en saltos de lista negra
# ============================================================================

def test_f5_blacklisted_hops_trailing_dot_deduplication():
    """Deduplicación considera idénticos dominios con y sin punto final (a.site. y a.site)."""
    chain = [
        "https://inicio.com/0",
        "https://malicioso.org./1",
        "https://malicioso.org/2",
        "https://fin.com/3",
    ]
    blacklist = frozenset({"malicioso.org"})
    skip = {"inicio.com", "fin.com"}

    hops = sandbox._blacklisted_hops(chain, blacklist, skip=skip)
    assert hops == ["malicioso.org"]


def test_f5_blacklisted_hops_trailing_dot_skip_matching():
    """La exclusión mediante skip reconoce dominios independientemente del punto final."""
    blacklist = frozenset({"salto.org", "otro.org"})

    # Salto con punto final excluido por skip sin punto
    chain_with_dot = ["https://salto.org./1", "https://otro.org/2"]
    hops1 = sandbox._blacklisted_hops(chain_with_dot, blacklist, skip={"salto.org"})
    assert hops1 == ["otro.org"]

    # Salto sin punto final excluido por skip con punto
    chain_without_dot = ["https://salto.org/1", "https://otro.org/2"]
    hops2 = sandbox._blacklisted_hops(chain_without_dot, blacklist, skip={"salto.org."})
    assert hops2 == ["otro.org"]


def test_f5_analyze_url_intermediate_hop_with_trailing_dot(monkeypatch):
    """analyze_url detecta y reporta salto intermedio con punto final normalizado."""
    routes = {
        "http://bit.ly/dot": (301, "https://malicioso.org./r"),
        "https://malicioso.org./r": (301, "https://destino.com/"),
        "https://destino.com/": (200, None),
    }
    monkeypatch.setattr(sandbox, "_head_request", _fake_head(routes))

    res = sandbox.analyze_url(
        "bit.ly/dot",
        expand=True,
        blacklist=frozenset({"malicioso.org"}),
    )

    assert res["status"] == "success"
    assert res["is_blacklisted"] is True
    assert res["verdict"] == "MALICIOSO"
    assert "Salto intermedio en lista negra local (malicioso.org)" in res["findings"]
