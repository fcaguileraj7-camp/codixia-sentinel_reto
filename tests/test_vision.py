"""
Pruebas Unitarias para VisionParser y PoliceReporter
Rol 4: Nicolle (Detección de Engaño Psicológico, Visión & CAI Virtual) · Hito S2

Todas las pruebas son locales, deterministas y de costo $0.00.
El análisis semántico se ejercita mediante un adaptador SIMULADO: en ningún
momento se invoca Grok Vision ni se abre una conexión de red.
"""

import pytest

from src.tools.police_reporter import generate_police_report, NOT_AVAILABLE
from src.tools.vision_parser import (
    parse_receipt_image,
    SimulatedVisionAnalyzer,
    VisionAnalyzer,
    GrokVisionAnalyzer,
    MAX_FILE_SIZE_BYTES,
)

# PNG mínimo válido (1x1, transparente) para las pruebas de validación local.
PNG_1x1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def fake_png(tmp_path):
    """Crea una imagen PNG real en disco para validar las comprobaciones locales."""
    path = tmp_path / "comprobante_prueba.png"
    path.write_bytes(PNG_1x1)
    return str(path)


@pytest.fixture
def not_an_image(tmp_path):
    """Archivo con extensión de imagen pero contenido que no lo es."""
    path = tmp_path / "falso_comprobante.png"
    path.write_bytes(b"esto no es una imagen, es texto plano")
    return str(path)


@pytest.fixture
def empty_file(tmp_path):
    path = tmp_path / "vacio.png"
    path.write_bytes(b"")
    return str(path)


# ---------------------------------------------------------------------------
# PoliceReporter
# ---------------------------------------------------------------------------

def test_generate_police_report():
    evidence = {
        "sender_phone": "+57 300 111 2233",
        "incident_type": "Extorsión Carcelaria",
        "user_input": "Pague 2 millones o le hacemos atentado",
        "risk_level": "CRÍTICO",
        "findings": ["Amenaza explícita", "Exigencia de dinero"],
        "detected_urls": []
    }
    report = generate_police_report(evidence)
    assert report["status"] == "success"
    assert "CAI-COL-" in report["report_id"]
    assert "EXPEDIENTE DE DENUNCIA DIGITAL" in report["formatted_markdown"]
    assert "+57 300 111 2233" in report["formatted_markdown"]


def test_police_report_does_not_invent_missing_sender():
    """Un dato ausente debe marcarse explícitamente, nunca inventarse."""
    report = generate_police_report({"user_input": "Mensaje de amenaza", "risk_level": "ALTO"})
    assert report["status"] == "success"
    assert NOT_AVAILABLE in report["formatted_markdown"]
    assert "sender_phone" in report["missing_fields"]


def test_police_report_rejects_empty_evidence():
    """Sin contenido mínimo no se genera expediente ni veredicto."""
    report = generate_police_report({})
    assert report["status"] == "error"
    assert report["error"] == "evidencia_insuficiente"
    assert report["report_id"] is None
    assert report["formatted_markdown"] == ""


@pytest.mark.parametrize("bad_evidence", [None, "texto", 123, []])
def test_police_report_handles_malformed_evidence(bad_evidence):
    report = generate_police_report(bad_evidence)
    assert report["status"] == "error"
    assert report["report_id"] is None


def test_police_report_ids_are_unique():
    """Radicados consecutivos no deben colisionar."""
    evidence = {"user_input": "Evidencia de prueba", "risk_level": "ALTO"}
    ids = {generate_police_report(evidence)["report_id"] for _ in range(50)}
    assert len(ids) == 50


def test_police_report_normalizes_findings_and_urls():
    evidence = {
        "user_input": "Texto",
        "findings": "unico hallazgo",
        "detected_urls": ["https://ejemplo-malicioso.xyz"],
    }
    report = generate_police_report(evidence)
    assert "unico hallazgo" in report["formatted_markdown"]
    assert "https://ejemplo-malicioso.xyz" in report["formatted_markdown"]


# ---------------------------------------------------------------------------
# VisionParser: validación local real
# ---------------------------------------------------------------------------

def test_parse_receipt_image_nonexistent():
    res = parse_receipt_image("ruta/falsa/no_existe.jpg")
    assert res["status"] == "error"
    assert res["error"] == "archivo_no_encontrado"
    assert res["is_receipt"] is False
    # Un archivo inexistente NO puede producir un veredicto de autenticidad.
    assert res["is_fraudulent"] is None


def test_parse_receipt_image_rejects_non_image_content(not_an_image):
    """Extensión .png pero contenido de texto: la validación local lo rechaza."""
    res = parse_receipt_image(not_an_image)
    assert res["status"] == "error"
    assert res["error"] == "archivo_no_es_imagen_valida"
    assert res["local_checks"]["signature_valid"] is False


def test_parse_receipt_image_rejects_empty_file(empty_file):
    res = parse_receipt_image(empty_file)
    assert res["status"] == "error"
    assert "archivo_vacio" in res["local_checks"]["errors"]


def test_parse_receipt_image_rejects_corrupt_image_with_valid_signature(tmp_path):
    path = tmp_path / "corrupta.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"contenido truncado")
    result = parse_receipt_image(str(path))
    assert result["status"] == "error"
    assert result["is_fraudulent"] is None
    assert "imagen_corrupta_o_ilegible" in result["local_checks"]["errors"]


def test_parse_receipt_image_rejects_extension_format_mismatch(tmp_path):
    path = tmp_path / "comprobante.jpg"
    path.write_bytes(PNG_1x1)
    result = parse_receipt_image(str(path))
    assert result["status"] == "error"
    assert "extension_no_coincide_con_formato" in result["local_checks"]["errors"]


def test_parse_receipt_image_enforces_maximum_size(tmp_path):
    path = tmp_path / "grande.png"
    path.write_bytes(PNG_1x1 + b"\x00" * (MAX_FILE_SIZE_BYTES + 1 - len(PNG_1x1)))
    result = parse_receipt_image(str(path))
    assert result["status"] == "error"
    assert result["error"] == "archivo_demasiado_grande"
    assert result["is_fraudulent"] is None


def test_parse_receipt_image_validates_magic_bytes(fake_png):
    """Comprobación LOCAL real: el PNG generado sí supera la validación."""
    res = parse_receipt_image(fake_png)
    assert res["status"] == "success"
    assert res["local_checks"]["signature_valid"] is True
    assert res["is_receipt"] is True


def test_remote_analysis_is_refused(fake_png):
    """El transporte remoto está deshabilitado en el Hito S2."""
    res = parse_receipt_image(fake_png, allow_remote=True)
    assert res["status"] == "error"
    assert res["error"] == "transporte_remoto_no_permitido"


@pytest.mark.parametrize("bad_path", [None, "", 123, []])
def test_parse_receipt_image_handles_malformed_path(bad_path):
    res = parse_receipt_image(bad_path)
    assert res["status"] == "error"
    assert res["is_fraudulent"] is None


# ---------------------------------------------------------------------------
# VisionParser: adaptador simulado (sustituye a Grok Vision en esta fase)
# ---------------------------------------------------------------------------

def test_simulated_analyzer_default_scenario_is_authentic(fake_png):
    analyzer = SimulatedVisionAnalyzer()
    res = parse_receipt_image(fake_png, analyzer=analyzer)
    assert res["status"] == "success"
    assert res["is_fraudulent"] is False
    assert len(analyzer.calls) == 1


def test_simulated_analyzer_detects_forged_receipt(fake_png):
    """El test controla el escenario: aquí se simula un comprobante falsificado."""
    analyzer = SimulatedVisionAnalyzer(scenario="falsificado")
    res = parse_receipt_image(fake_png, analyzer=analyzer)
    assert res["status"] == "success"
    assert res["is_fraudulent"] is True
    assert len(res["fraud_reasons"]) > 0


def test_simulated_result_is_labelled_as_simulation(fake_png):
    """El origen debe ser identificable: nunca se confunde con un análisis real."""
    res = parse_receipt_image(fake_png, analyzer=SimulatedVisionAnalyzer(scenario="falsificado"))
    assert res["analysis_source"] == "simulado_local"
    assert "SIMULADO" in res["notes"]


def test_inconclusive_scenario_yields_no_verdict(fake_png):
    """Caso ambiguo: no se afirma autenticidad ni falsificación."""
    res = parse_receipt_image(fake_png, analyzer=SimulatedVisionAnalyzer(scenario="inconcluso"))
    assert res["status"] == "success"
    assert res["is_fraudulent"] is None


def test_analyzer_failure_does_not_become_safe_verdict(fake_png):
    """Un fallo del analizador NO debe degradarse a 'comprobante auténtico'."""
    analyzer = SimulatedVisionAnalyzer(raise_exception=True)
    res = parse_receipt_image(fake_png, analyzer=analyzer)
    assert res["status"] == "error"
    assert res["error"] == "fallo_analisis_semantico"
    assert res["is_fraudulent"] is None
    assert res["analysis_source"] == "no_disponible"


@pytest.mark.parametrize(
    "invalid_result",
    [
        None,
        "auténtico",
        {"is_receipt": True, "is_fraudulent": "false"},
        {"is_receipt": True, "is_fraudulent": False, "confidence_score": float("nan")},
        {"is_receipt": True, "is_fraudulent": False, "fraud_reasons": "ninguna"},
    ],
)
def test_invalid_analyzer_result_does_not_become_a_verdict(fake_png, invalid_result):
    class InvalidAnalyzer(VisionAnalyzer):
        source = "invalid_test"

        def analyze(self, image_path, local_checks):
            return invalid_result

    result = parse_receipt_image(fake_png, analyzer=InvalidAnalyzer())
    assert result["status"] == "error"
    assert result["error"] == "respuesta_analizador_invalida"
    assert result["is_fraudulent"] is None


def test_grok_vision_analyzer_uses_live_client_with_data_url(fake_png):
    import base64
    import json

    class LiveClient:
        live_mode = True
        last_simulated = False
        last_source = "grok_4.7"

        def __init__(self):
            self.messages = None
            self.options = None

        def vision_completion(self, messages, **options):
            self.messages = messages
            self.options = options
            return json.dumps(
                {
                    "is_receipt": True,
                    "bank_detected": "Nequi",
                    "detected_amount": None,
                    "reference_id": None,
                    "is_fraudulent": None,
                    "fraud_reasons": [],
                    "confidence_score": 0.2,
                }
            )

    client = LiveClient()
    result = parse_receipt_image(
        fake_png,
        analyzer=GrokVisionAnalyzer(client),
        allow_remote=True,
    )
    image_part = client.messages[1]["content"][1]["image_url"]["url"]
    encoded = image_part.split(",", 1)[1]

    assert result["status"] == "success"
    assert result["analysis_source"] == "grok_vision"
    assert result["is_fraudulent"] is None
    assert base64.b64decode(encoded) == PNG_1x1
    assert client.options["max_tokens"] == 300


def test_default_parser_uses_configured_live_client(fake_png, monkeypatch):
    import json

    class LiveClient:
        live_mode = True
        last_simulated = False
        last_source = "grok_4.7"

        def vision_completion(self, messages, **options):
            self.messages = messages
            self.options = options
            return json.dumps(
                {
                    "is_receipt": True,
                    "bank_detected": None,
                    "detected_amount": None,
                    "reference_id": None,
                    "is_fraudulent": None,
                    "fraud_reasons": [],
                    "confidence_score": 0.1,
                }
            )

    client = LiveClient()
    monkeypatch.setattr("src.client.GrokClient", lambda: client)
    result = parse_receipt_image(fake_png)

    assert result["status"] == "success"
    assert result["analysis_source"] == "grok_vision"
    assert result["is_fraudulent"] is None
    assert client.messages[1]["content"][1]["image_url"]["url"].startswith(
        "data:image/png;base64,"
    )


def test_default_parser_stays_simulated_when_client_is_not_live(fake_png, monkeypatch):
    class OfflineClient:
        live_mode = False

        def vision_completion(self, messages, **options):
            raise AssertionError("No debe solicitarse la API en modo simulado.")

    monkeypatch.setattr("src.client.GrokClient", OfflineClient)
    result = parse_receipt_image(fake_png)

    assert result["status"] == "success"
    assert result["analysis_source"] == "simulado_local"
    assert "SIMULADO" in result["notes"]


def test_allow_remote_false_forces_local_even_with_live_grok_analyzer(fake_png):
    class LiveClient:
        live_mode = True

        def vision_completion(self, messages, **options):
            raise AssertionError("allow_remote=False no debe invocar el transporte remoto.")

    result = parse_receipt_image(
        fake_png,
        analyzer=GrokVisionAnalyzer(LiveClient()),
        allow_remote=False,
    )

    assert result["status"] == "success"
    assert result["analysis_source"] == "simulado_local"
    assert "SIMULADO" in result["notes"]


def test_grok_vision_analyzer_refuses_non_live_client_without_request(fake_png):
    class OfflineClient:
        live_mode = False

        def __init__(self):
            self.called = False

        def vision_completion(self, messages, **options):
            self.called = True
            raise AssertionError("No debe llamarse al cliente en modo simulado.")

    client = OfflineClient()
    result = parse_receipt_image(
        fake_png,
        analyzer=GrokVisionAnalyzer(client),
        allow_remote=True,
    )

    assert result["status"] == "error"
    assert result["error"] == "fallo_analisis_semantico"
    assert result["analysis_source"] == "no_disponible"
    assert result["is_fraudulent"] is None
    assert client.called is False


def test_grok_vision_analyzer_rejects_simulated_client_fallback(fake_png):
    import json

    class FallbackClient:
        live_mode = True
        last_simulated = True
        last_source = "simulated"

        def vision_completion(self, messages, **options):
            return json.dumps(
                {
                    "is_receipt": True,
                    "is_fraudulent": False,
                    "fraud_reasons": [],
                    "confidence_score": 0.9,
                }
            )

    result = parse_receipt_image(
        fake_png,
        analyzer=GrokVisionAnalyzer(FallbackClient()),
        allow_remote=True,
    )
    assert result["status"] == "error"
    assert result["is_fraudulent"] is None
    assert result["analysis_source"] == "no_disponible"


def test_grok_client_vision_completion_refuses_mock_mode_without_request():
    from src.client import GrokClient

    class UnusedCompletions:
        called = False

        def create(self, **kwargs):
            self.called = True
            raise AssertionError("No debe solicitarse la API en modo mock.")

    completions = UnusedCompletions()
    client = GrokClient.__new__(GrokClient)
    client.live_mode = False
    client.client = type(
        "SdkClient",
        (),
        {"chat": type("Chat", (), {"completions": completions})()},
    )()

    with pytest.raises(RuntimeError, match="modo en vivo"):
        client.vision_completion([])
    assert completions.called is False


def test_grok_client_vision_completion_uses_multimodal_payload_and_usage():
    from types import SimpleNamespace

    from src.client import GrokClient

    class Completions:
        def __init__(self):
            self.request = None

        def create(self, **kwargs):
            self.request = kwargs
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content='{"is_receipt": true}')
                    )
                ],
                usage=SimpleNamespace(
                    prompt_tokens=40,
                    completion_tokens=20,
                    total_tokens=60,
                ),
            )

    completions = Completions()
    client = GrokClient.__new__(GrokClient)
    client.live_mode = True
    client.client = SimpleNamespace(
        chat=SimpleNamespace(completions=completions)
    )

    result = client.vision_completion(
        [{"role": "user", "content": [{"type": "image_url"}]}],
        model="vision-test",
        max_tokens=123,
    )

    assert result == '{"is_receipt": true}'
    assert completions.request["model"] == "vision-test"
    assert completions.request["max_tokens"] == 123
    assert completions.request["messages"][0]["content"][0]["type"] == "image_url"
    assert client.last_simulated is False
    assert client.last_usage["total_tokens"] == 60
    assert client.last_usage["mode"] == "live_api"


def test_grok_client_vision_completion_propagates_provider_error_without_fallback():
    from src.client import GrokClient

    class Completions:
        def create(self, **kwargs):
            raise OSError("provider unavailable")

    client = GrokClient.__new__(GrokClient)
    client.live_mode = True
    client.client = type(
        "SdkClient",
        (),
        {"chat": type("Chat", (), {"completions": Completions()})()},
    )()

    with pytest.raises(OSError, match="provider unavailable"):
        client.vision_completion([])
    assert client.last_source == "unavailable"
    assert client.last_simulated is False


def test_custom_analyzer_can_be_injected(fake_png):
    """La interfaz desacoplada permite inyectar cualquier implementación."""

    class StubAnalyzer(VisionAnalyzer):
        source = "stub_prueba"

        def analyze(self, image_path, local_checks):
            return {
                "is_receipt": True,
                "bank_detected": "Banco de prueba",
                "detected_amount": 999.0,
                "reference_id": "STUB-1",
                "is_fraudulent": False,
                "fraud_reasons": [],
                "confidence_score": 0.0,
                "analysis_source": self.source,
                "notes": "stub",
            }

    res = parse_receipt_image(fake_png, analyzer=StubAnalyzer())
    assert res["status"] == "success"
    assert res["analysis_source"] == "stub_prueba"
    assert res["detected_amount"] == 999.0


def test_default_analyzer_is_simulated_not_remote(fake_png):
    """Sin adaptador inyectado, el análisis sigue siendo local y simulado."""
    res = parse_receipt_image(fake_png)
    assert res["analysis_source"] == "simulado_local"
    assert res["is_receipt"] is True


# ---------------------------------------------------------------------------
# Cumplimiento del contrato 6.3 del MASTER_PLAN
# ---------------------------------------------------------------------------

VISION_CONTRACT_FIELDS = [
    "status",
    "is_receipt",
    "detected_amount",
    "reference_id",
    "is_fraudulent",
    "fraud_reasons",
    "confidence_score",
]

REPORT_CONTRACT_FIELDS = [
    "status",
    "report_id",
    "timestamp",
    "formatted_markdown",
    "incident_category",
    "suggested_actions",
]


def test_vision_parser_fulfills_contract_6_3(fake_png):
    res = parse_receipt_image(fake_png)
    for field in VISION_CONTRACT_FIELDS:
        assert field in res, f"Falta el campo obligatorio del contrato 6.3: {field}"


def test_vision_parser_contract_6_3_on_error():
    """El contrato también se respeta en la rama de error."""
    res = parse_receipt_image("ruta/inexistente.jpg")
    for field in VISION_CONTRACT_FIELDS:
        assert field in res, f"Falta el campo del contrato 6.3 en la rama de error: {field}"


def test_police_reporter_fulfills_contract_6_3():
    evidence = {
        "sender_phone": "+57 300 111 2233",
        "incident_type": "Extorsión Carcelaria",
        "user_input": "Pague 2 millones o le hacemos atentado",
        "risk_level": "CRÍTICO",
        "findings": ["Amenaza explícita"],
        "detected_urls": [],
    }
    report = generate_police_report(evidence)
    for field in REPORT_CONTRACT_FIELDS:
        assert field in report, f"Falta el campo obligatorio del contrato 6.3: {field}"


# ---------------------------------------------------------------------------
# Aislamiento de red: las herramientas del Rol 4 nunca abren conexiones
# ---------------------------------------------------------------------------

def test_tools_do_not_import_http_clients():
    """Ninguna herramienta del Rol 4 debe depender de un cliente HTTP."""
    import sys

    for module_name in (
        "src.tools.threat_inspector",
        "src.tools.vision_parser",
        "src.tools.police_reporter",
    ):
        __import__(module_name)

    for forbidden in ("requests", "httpx", "urllib3", "aiohttp"):
        assert forbidden not in sys.modules, (
            f"{forbidden} no debería importarse en las herramientas del Rol 4"
        )


def test_vision_parser_never_opens_a_socket(fake_png, monkeypatch):
    """Blindaje puntual: cualquier intento de socket durante el análisis falla."""
    import socket

    def _blocked(*args, **kwargs):
        raise AssertionError("VisionParser no debe abrir conexiones de red")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)

    # Si el análisis requiriera red, esta prueba fallaría en lugar de gastar créditos.
    res = parse_receipt_image(fake_png, analyzer=SimulatedVisionAnalyzer(scenario="falsificado"))
    assert res["status"] == "success"
    assert res["is_fraudulent"] is True
