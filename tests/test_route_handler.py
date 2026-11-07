"""
Pruebas del ciclo de vida del viaje en RouteCompanionHandler (Hito S4).

Cubren que el viaje se cierre cuando el pasajero llega, que el check-in quede
registrado en route_companion, y que la palabra segura nunca viaje a Grok.
"""

from unittest.mock import patch

import pytest

from src.agent.sentinel import SentinelAgent
from src.tools import route_companion

START_META = {"plate": "TRL981", "destination": "Chapinero"}
START_TEXT = "Voy en taxi placa TRL981 hacia Chapinero"


@pytest.fixture(autouse=True)
def _isolated_trips(monkeypatch):
    """Cada prueba parte de un almacén de viajes vacío (el estado de route_companion es global)."""
    monkeypatch.setattr(route_companion, "_TRIPS", {})


class RecordingClient:
    """Cliente que guarda los mensajes que recibiría Grok y responde un JSON fijo."""

    live_mode = False

    def __init__(self):
        self.prompts = []

    def chat_completion(self, messages, max_tokens=700):
        self.prompts.append("\n".join(m["content"] for m in messages))
        return '{"mode": "route_companion", "risk_level": "BAJO", "action": "ANALYZE_ONLY", "response_to_user": "ok"}'


def _tools_block(prompt):
    """Parte del prompt con la telemetría de las herramientas (lo que no escribió el usuario)."""
    return prompt.split("Telemetría y herramientas:", 1)[1].split("Analiza la situación", 1)[0]


def _start(agent, session_id, **extra):
    return agent.process_message(START_TEXT, metadata={**START_META, **extra}, session_id=session_id)


def test_safe_word_is_not_sent_to_the_model_but_is_kept_locally():
    client = RecordingClient()
    agent = SentinelAgent(client=client)
    first = _start(agent, "safe_word_prompt", safe_word="naranja-azul-77")
    second = agent.process_message("sigo en camino, naranja-azul-77", session_id="safe_word_prompt")

    assert len(client.prompts) == 2
    assert all("naranja-azul-77" not in _tools_block(prompt) for prompt in client.prompts)
    assert first["tool_results"]["route"]["safe_word"] == "naranja-azul-77"
    assert agent.memory.get_active_trip("safe_word_prompt")["safe_word"] == "naranja-azul-77"
    assert second["tool_results"]["route"]["event"] == "CHECKIN_NORMAL"


def test_arrival_closes_the_trip_and_the_next_digital_message_is_not_routed_to_the_taxi():
    agent = SentinelAgent()
    started = _start(agent, "arrival_closes")
    trip_id = started["tool_results"]["route"]["trip_id"]

    closed = agent.process_message("Ya llegué bien, finalizar viaje", session_id="arrival_closes")

    assert closed["tool_results"]["route"]["event"] == "TRIP_FINISHED"
    assert closed["tool_results"]["route"]["finalize_status"] == "completed"
    assert agent.memory.get_active_trip("arrival_closes") is None
    assert route_companion._TRIPS[trip_id]["status"] == "completed"
    assert route_companion._TRIPS[trip_id]["monitoring_active"] is False

    digital = agent.process_message(
        "Tu paquete de Servientrega está retenido, paga el envío en http://servientrega-pago.site",
        session_id="arrival_closes",
    )
    assert digital["decision"]["mode"] == "threat_inspection"
    assert "route" not in digital["tool_results"]


def test_arrival_without_the_expected_safe_word_does_not_close_the_trip():
    agent = SentinelAgent()
    started = _start(agent, "arrival_no_word", safe_word="naranja")
    trip_id = started["tool_results"]["route"]["trip_id"]

    res = agent.process_message("Ya llegué, finalizar viaje", session_id="arrival_no_word")

    assert res["tool_results"]["route"]["event"] == "CHECKIN_PENDING"
    assert agent.memory.get_active_trip("arrival_no_word") is not None
    assert route_companion._TRIPS[trip_id]["status"] != "completed"


def test_arrival_with_the_expected_safe_word_closes_the_trip():
    agent = SentinelAgent()
    started = _start(agent, "arrival_with_word", safe_word="naranja")
    trip_id = started["tool_results"]["route"]["trip_id"]

    res = agent.process_message("Ya llegué bien, naranja", session_id="arrival_with_word")

    assert res["tool_results"]["route"]["event"] == "TRIP_FINISHED"
    assert agent.memory.get_active_trip("arrival_with_word") is None
    assert route_companion._TRIPS[trip_id]["status"] == "completed"


def test_panic_has_priority_over_an_arrival_message():
    agent = SentinelAgent()
    started = _start(agent, "panic_priority")
    trip_id = started["tool_results"]["route"]["trip_id"]

    res = agent.process_message("Ya llegué pero me siguen, auxilio", session_id="panic_priority")

    assert res["tool_results"]["route"]["event"] == "PANIC_REPORTED"
    assert agent.memory.get_active_trip("panic_priority") is not None
    assert route_companion._TRIPS[trip_id]["status"] != "completed"


def test_ordinary_checkin_is_recorded_in_route_companion():
    agent = SentinelAgent()
    started = _start(agent, "ordinary_checkin")
    trip_id = started["tool_results"]["route"]["trip_id"]
    before = route_companion._TRIPS[trip_id]["checkin_count"]

    res = agent.process_message("Todo bien, sigo en camino", session_id="ordinary_checkin")

    assert route_companion._TRIPS[trip_id]["checkin_count"] == before + 1
    assert res["tool_results"]["route"]["event"] == "CHECKIN_NORMAL"
    assert res["tool_results"]["route"]["checkin_count"] == before + 1


def test_a_failing_finalize_tool_still_closes_the_conversation_trip():
    agent = SentinelAgent()
    _start(agent, "finalize_fails")

    with patch("src.agent.route_handler.finalize_trip", side_effect=RuntimeError("Falla de cierre")):
        res = agent.process_message("Ya llegué bien, finalizar viaje", session_id="finalize_fails")

    assert res["status"] == "success"
    assert res["tool_results"]["route"]["finalize_status"] == "error"
    assert "Falla de cierre" in res["tool_results"]["route"]["finalize_error"]
    assert agent.memory.get_active_trip("finalize_fails") is None


def test_a_failing_checkin_tool_never_breaks_the_turn():
    agent = SentinelAgent()
    _start(agent, "checkin_fails")

    with patch("src.agent.route_handler.confirm_checkin", side_effect=RuntimeError("Falla de check-in")):
        res = agent.process_message("Todo bien, sigo en camino", session_id="checkin_fails")

    assert res["status"] == "success"
    assert res["tool_results"]["route"]["event"] == "CHECKIN_NORMAL"
    assert agent.memory.get_active_trip("checkin_fails") is not None
