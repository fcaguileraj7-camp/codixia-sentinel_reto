"""
Pruebas de Integración para SentinelAgent Core y Blindaje de Presupuesto
Hito S2: Arquitectura Resiliente, Herramientas Reales y Tolerancia a Fallos
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
"""

import pytest
from unittest.mock import MagicMock, patch
from src.agent.sentinel import SentinelAgent
from src.client import GrokClient

# PNG mínimo válido (1x1) para pruebas locales deterministas de VisionParser
PNG_1x1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

def test_sentinel_process_legitimate():
    agent = SentinelAgent()
    res = agent.process_message("Hola mamá, ¿cómo estás? Ya voy saliendo del trabajo.")
    assert res["status"] == "success"
    assert "decision" in res
    assert res["decision"]["risk_level"] in ["BAJO", "MEDIO"]

def test_sentinel_process_phishing():
    agent = SentinelAgent()
    res = agent.process_message("Bancolombia informa: Su cuenta ha sido bloqueada. Urgente ingrese a http://banc0lombia-alerta.cc")
    assert res["status"] == "success"
    assert "decision" in res
    assert res["decision"]["risk_level"] in ["ALTO", "CRÍTICO"]

# ==============================================================================
# 1. Pruebas de Integración de VisionParser (Requisito 1)
# ==============================================================================

def test_sentinel_process_with_image_metadata(tmp_path):
    """Verifica que VisionParser se invoque cuando metadata['image_path'] está presente."""
    # Crear archivo temporal simulado de comprobante válido
    dummy_image = tmp_path / "comprobante_nequi_test.png"
    dummy_image.write_bytes(PNG_1x1)

    agent = SentinelAgent()
    res = agent.process_message(
        "Revisa este comprobante de transferencia que me enviaron por WhatsApp",
        metadata={"image_path": str(dummy_image)}
    )

    assert res["status"] == "success"
    assert "vision" in res["tool_results"]
    assert res["tool_results"]["vision"]["status"] == "success"
    assert res["tool_results"]["vision"]["is_receipt"] is True
    assert "Nequi" in res["tool_results"]["vision"]["bank_detected"]

def test_sentinel_process_without_image_backward_compatibility():
    """Confirma que la ausencia de image_path mantiene el comportamiento actual sin fallos."""
    agent = SentinelAgent()
    res = agent.process_message("Mensaje ordinario sin comprobantes adjuntos")
    assert res["status"] == "success"
    assert "vision" not in res["tool_results"]

# ==============================================================================
# 2. Pruebas de Manejo de Fallos sin Falsos Veredictos (Requisito 2)
# ==============================================================================

def test_sentinel_handles_invalid_json_without_dummy_verdict():
    """Verifica que una respuesta JSON inválida genere 'NO_ANALIZADO' y no active escalada."""
    simulated_client = GrokClient(simulated_response="[Error 500] Raw plain text string with no JSON syntax")
    agent = SentinelAgent(client=simulated_client)

    res = agent.process_message("Mensaje para prueba de fallo de formato")

    assert res["status"] == "error"
    assert res["decision"]["analysis_available"] is False
    assert res["decision"]["risk_level"] == "NO_ANALIZADO"
    assert res["decision"]["action"] == "MANUAL_REVIEW_REQUIRED"
    assert res["police_report"] is None
    assert res["escalation"] is None

def test_sentinel_handles_client_exception_gracefully():
    """Verifica que excepciones de red o timeout generen 'NO_ANALIZADO' explícito."""
    mock_client = MagicMock(spec=GrokClient)
    mock_client.chat_completion.side_effect = RuntimeError("Conexión interrumpida con el modelo")
    mock_client.last_usage = {}

    agent = SentinelAgent(client=mock_client)
    res = agent.process_message("Cualquier mensaje con timeout forzado")

    assert res["status"] == "error"
    assert res["decision"]["analysis_available"] is False
    assert res["decision"]["risk_level"] == "NO_ANALIZADO"
    assert res["police_report"] is None

# ==============================================================================
# 3. Pruebas de Blindaje Estructural de Presupuesto (Requisito 3)
# ==============================================================================

def test_grok_client_default_operates_in_local_simulated_mode():
    """Confirma que GrokClient por defecto NO crea cliente HTTP y no consume presupuesto ($0.00)."""
    client = GrokClient()
    assert client.live_mode is False
    assert client.client is None

    response = client.chat_completion([{"role": "user", "content": "Verificación de costo cero"}])
    assert isinstance(response, str)
    assert client.last_usage["estimated_cost_usd"] == 0.0
    assert client.last_usage["mode"] == "simulated_local"

# ==============================================================================
# 4. Pruebas de Enrutamiento Preciso (Prevención de Falsos Negativos SIMIT/Placas)
# ==============================================================================

def test_sentinel_routing_simit_not_confused_with_taxi():
    """Verifica que mensajes de multas que mencionen 'placas' se procesen en Escudo Digital y no como taxi."""
    agent = SentinelAgent()
    simit_msg = (
        "SIMIT FOTOMULTAS: Su vehículo con placas registradas tiene un comparendo vigente por exceso "
        "de velocidad con 50% de descuento hoy. Pague en línea: https://simit-multas-colombia.site/pagos"
    )
    res = agent.process_message(simit_msg)
    assert res["status"] == "success"
    assert res["decision"]["mode"] == "threat_inspection"
    assert res["decision"]["risk_level"] in ["ALTO", "CRÍTICO"]
    assert "threat" in res["tool_results"]
    assert "url_sandbox" in res["tool_results"]
    assert "route" not in res["tool_results"]
    assert res["police_report"] is not None
    assert "CAI-COL-" in res["police_report"]["report_id"]

# ==============================================================================
# 5. Pruebas de Integración de Flujo de Taxi y Audio (Hito S3 - Integración Nicolle)
# ==============================================================================

def test_sentinel_taxi_flow_with_panic_audio_evaluation():
    """
    Verifica que en modo taxi se ejecute evaluate_trip_audio_response y el detector de amenazas,
    se propague risk_score=100 y threat_level=CRÍTICO, y se active escalada PHYSICAL_RISK.
    """
    agent = SentinelAgent()
    res = agent.process_message(
        "¡Auxilio! El taxista se desvió por una trocha oscura y no me deja bajar",
        metadata={"plate": "WDY452", "destination": "Centro"}
    )
    assert res["status"] == "success"
    assert "audio_eval" in res["tool_results"]
    assert res["tool_results"]["audio_eval"]["status"] == "alert"
    assert res["tool_results"]["audio_eval"]["escalation_required"] is True
    assert "threat" in res["tool_results"]

    # Propagación de score y niveles
    assert res["decision"]["risk_level"] == "CRÍTICO"
    assert res["decision"]["threat_level"] == "CRÍTICO"
    assert res["decision"]["risk_score"] == 100
    assert res["decision"]["action"] == "TRIGGER_ALARM"

    # Escalada de emergencia física
    assert res["escalation"] is not None
    assert res["escalation"]["incident_type"] == "PHYSICAL_RISK"
    assert res["escalation"]["status"] == "escalated"
    assert res["police_report"] is None  # CAI Virtual solo aplica a fraude digital

def test_sentinel_taxi_flow_normal_audio_response():
    """
    Verifica que un reporte normal en taxi mantenga status normal,
    risk_level BAJO, risk_score 0 y sin escalada de emergencia.
    """
    agent = SentinelAgent()
    res = agent.process_message(
        "Todo va bien, vamos por la avenida 30",
        metadata={"plate": "WDY452", "destination": "Centro"}
    )
    assert res["status"] == "success"
    assert "audio_eval" in res["tool_results"]
    assert res["tool_results"]["audio_eval"]["status"] == "normal"
    assert res["tool_results"]["audio_eval"]["is_safe"] is True
    assert res["decision"]["risk_level"] == "BAJO"
    assert res["decision"]["risk_score"] == 0
    assert res["escalation"] is None


# ==============================================================================
# 5. Pruebas de Desacoplamiento del Pipeline de Sentinel (Hito S3)
# ==============================================================================

def test_sentinel_process_cyber_audit_strictly_isolated():
    """
    Verifica que el pipeline exclusivo de ciberseguridad (process_cyber_audit)
    no ejecute herramientas de ruta física y opere de forma 100% aislada.
    """
    agent = SentinelAgent()
    res = agent.process_cyber_audit(
        "Bancolombia informa: Clave bloqueada, ingrese a https://bancolombia-alerta.cc",
        metadata={"sender": "+573001234567"}
    )

    assert res["status"] == "success"
    assert res["decision"]["mode"] == "threat_inspection"
    assert res["decision"]["risk_level"] in ["ALTO", "CRÍTICO"]
    assert "threat" in res["tool_results"]
    assert "url_sandbox" in res["tool_results"]
    assert "audio_eval" not in res["tool_results"]
    assert "route" not in res["tool_results"]
    assert res["police_report"] is not None
    assert res["police_report"]["incident_category"] == "Tentativa de Estafa / Phishing"


def test_route_companion_handler_standalone():
    """
    Verifica que RouteCompanionHandler opere de forma autónoma y desacoplada
    del pipeline principal de ciberamenazas.
    """
    from src.agent.route_handler import RouteCompanionHandler

    handler = RouteCompanionHandler()
    res = handler.process_route_message(
        "Voy en taxi placas TRL981 hacia Chapinero",
        metadata={"plate": "TRL981", "destination": "Chapinero"},
        session_id="standalone_route_test"
    )

    assert res["status"] == "success"
    assert res["decision"]["mode"] == "route_companion"
    assert "audio_eval" in res["tool_results"]
    assert "route" in res["tool_results"]
    assert res["tool_results"]["route"]["vehicle_plate"] == "TRL981"
    assert res["police_report"] is None


def test_route_handler_shares_client_and_memory_with_agent():
    """
    El handler de ruta usa el mismo cliente y la misma memoria que el agente:
    el viaje registrado en modo ruta queda visible en la memoria del agente.
    """
    agent = SentinelAgent()
    assert agent.route_handler.client is agent.client
    assert agent.route_handler.memory is agent.memory

    res = agent.process_message(
        "Voy en taxi placa TRL981 hacia Chapinero",
        metadata={"plate": "TRL981", "destination": "Chapinero"},
        session_id="shared_memory_route_test"
    )

    assert res["decision"]["mode"] == "route_companion"
    active_trip = agent.memory.get_active_trip("shared_memory_route_test")
    assert active_trip is not None
    assert active_trip["vehicle_plate"] == "TRL981"


def test_route_handler_does_not_depend_on_sentinel_module():
    """
    El desacoplamiento es real: sentinel.py ya no expone las tools de ruta y
    el handler resuelve register_trip desde su propio módulo.
    """
    import src.agent.sentinel as sentinel_module

    assert not hasattr(sentinel_module, "register_trip")
    assert not hasattr(sentinel_module, "evaluate_trip_audio_response")

    agent = SentinelAgent()
    with patch("src.agent.route_handler.register_trip", side_effect=RuntimeError("Falla de registro")):
        res = agent.process_message(
            "Voy en taxi placa TRL981 hacia Chapinero",
            metadata={"plate": "TRL981", "destination": "Chapinero"},
            session_id="route_register_failure_test"
        )

    assert res["status"] == "success"
    assert res["tool_results"]["route"]["status"] == "error"
    assert "Falla de registro" in res["tool_results"]["route"]["error"]



def test_injected_route_handler_shares_agent_memory():
    """Un handler inyectado adopta la memoria del agente (o la aporta si el agente no trae una)."""
    from src.agent.memory import ConversationMemory
    from src.agent.route_handler import RouteCompanionHandler

    handler = RouteCompanionHandler()
    agent = SentinelAgent(route_handler=handler)
    assert agent.memory is handler.memory

    own_memory = ConversationMemory()
    agent_with_memory = SentinelAgent(memory=own_memory, route_handler=RouteCompanionHandler())
    assert agent_with_memory.route_handler.memory is own_memory

    agent.process_message(
        "Voy en taxi placa TRL981 hacia Chapinero",
        metadata={"plate": "TRL981", "destination": "Chapinero"},
        session_id="injected_handler_test"
    )
    res = agent.process_message("todo bien, sigo en camino", session_id="injected_handler_test")
    assert res["decision"]["mode"] == "route_companion"
