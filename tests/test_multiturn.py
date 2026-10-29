"""
Pruebas de Integración para Conversaciones Multi-Turno y Persistencia Contextual
Hito S3: Reto Agente 2026 - SentinelGuard AI · Equipo Codixia

Rol 1: Fabián Aguilera (Lead Architect & Core Orchestrator)
Todas las pruebas operan en modo local con blindaje presupuestario ($0.00 USD).
"""

import pytest
from src.agent.sentinel import SentinelAgent
from src.agent.memory import ConversationMemory


def test_multiturn_phishing_followup():
    """
    Verifica que el agente mantenga el contexto de una estafa en turnos sucesivos.
    Turno 1: Se audita el mensaje fraudulento.
    Turno 2: El usuario pregunta si debe compartir el código que le piden.
    """
    agent = SentinelAgent()
    session_id = "test_scam_followup"

    # Turno 1: Detección inicial de phishing
    res1 = agent.process_message(
        "Bancolombia informa: Su cuenta ha sido bloqueada. Urgente ingrese a http://banc0lombia-alerta.cc",
        session_id=session_id
    )

    assert res1["status"] == "success"
    assert res1["turn_id"] == 1
    assert res1["decision"]["risk_level"] in ["ALTO", "CRÍTICO"]
    assert res1["police_report"] is not None

    # Turno 2: Pregunta de seguimiento sobre entregar códigos
    res2 = agent.process_message(
        "¿Y si me llaman y me piden el código que me llegó por SMS, se lo debo dar?",
        session_id=session_id
    )

    assert res2["status"] == "success"
    assert res2["turn_id"] == 2
    assert res2["decision"]["risk_level"] in ["ALTO", "CRÍTICO"]
    assert res2["decision"]["action"] == "BLOCK_AND_REPORT"
    # Debe recordar no entregar datos ni responder
    assert any(w in res2["decision"]["response_to_user"].lower() for w in ["recordatorio", "fraude", "no respondas", "bloqueo", "datos"])


def test_multiturn_taxi_trip_and_panic_escalation():
    """
    Verifica el flujo físico multi-turno de taxi:
    Turno 1: Registro del vehículo (placas y destino).
    Turno 2: Alerta de pánico/desvío donde el agente recuerda la placa sin que el usuario la repita.
    """
    agent = SentinelAgent()
    session_id = "test_taxi_trip"

    # Turno 1: Inicio del viaje
    res1 = agent.process_message(
        "Me subí a un taxi hacia Unicentro",
        metadata={"plate": "WTL999", "destination": "Unicentro"},
        session_id=session_id
    )

    assert res1["status"] == "success"
    assert res1["turn_id"] == 1
    assert res1["active_trip"] is not None
    assert res1["active_trip"]["vehicle_plate"] == "WTL999"
    assert res1["decision"]["mode"] == "route_companion"

    # Turno 2: El usuario reporta desvío y pánico (sin mencionar la placa nuevamente)
    res2 = agent.process_message(
        "¡Auxilio! El conductor se desvió por una trocha oscura y no quiere parar",
        session_id=session_id
    )

    assert res2["status"] == "success"
    assert res2["turn_id"] == 2
    assert res2["decision"]["risk_level"] == "CRÍTICO"
    assert res2["decision"]["action"] == "TRIGGER_ALARM"
    assert res2["escalation"] is not None
    assert res2["escalation"]["status"] == "escalated"
    # Se debe conservar la placa del turno 1
    assert res2["tool_results"]["route"]["vehicle_plate"] == "WTL999"


def test_multiturn_sessions_do_not_interfere():
    """Confirma que dos usuarios en sesiones separadas no compartan memoria ni estado de viaje."""
    agent = SentinelAgent()

    # Usuario A inicia un taxi
    res_a = agent.process_message(
        "Voy en taxi placas TAZ123",
        metadata={"plate": "TAZ123"},
        session_id="user_a"
    )
    # Usuario B consulta un mensaje benigno
    res_b = agent.process_message(
        "Hola amigo, ¿nos vemos a almorzar?",
        session_id="user_b"
    )

    assert res_a["active_trip"] is not None
    assert res_b["active_trip"] is None
    assert agent.memory.get_active_trip("user_a")["vehicle_plate"] == "TAZ123"
    assert agent.memory.get_active_trip("user_b") is None
