"""
Pruebas de Integración para SentinelAgent Core y Blindaje de Presupuesto
Hito S2: Arquitectura Resiliente, Herramientas Reales y Tolerancia a Fallos
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
"""

import pytest
from unittest.mock import MagicMock
from src.agent.sentinel import SentinelAgent
from src.client import GrokClient

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
    # Crear archivo temporal simulado de comprobante
    dummy_image = tmp_path / "comprobante_nequi_test.jpg"
    dummy_image.write_bytes(b"fake image data")

    agent = SentinelAgent()
    res = agent.process_message(
        "Revisa este comprobante de transferencia que me enviaron por WhatsApp",
        metadata={"image_path": str(dummy_image)}
    )

    assert res["status"] == "success"
    assert "vision" in res["tool_results"]
    assert res["tool_results"]["vision"]["status"] == "success"
    assert res["tool_results"]["vision"]["is_receipt"] is True
    assert res["tool_results"]["vision"]["bank_detected"] == "Nequi"

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

