"""
Pruebas Unitarias para el Módulo de Memoria Conversacional Multi-Turno
Hito S3: Reto Agente 2026 - SentinelGuard AI · Equipo Codixia

Rol 1: Fabián Aguilera (Lead Architect & Core Orchestrator)
Todas las pruebas operan en memoria local a costo $0.00 USD.
"""

import pytest
from src.agent.memory import ConversationMemory, ConversationTurn, ConversationSession


def test_memory_session_isolation():
    """Verifica que turnos de diferentes sesiones permanezcan completamente aislados."""
    mem = ConversationMemory()
    mem.add_turn(
        session_id="user_alpha",
        user_input="Mensaje de prueba usuario A",
        agent_decision={"mode": "threat_inspection", "risk_level": "BAJO", "action": "ANALYZE_ONLY", "response_to_user": "Todo seguro A"}
    )
    mem.add_turn(
        session_id="user_beta",
        user_input="Mensaje de prueba usuario B",
        agent_decision={"mode": "threat_inspection", "risk_level": "CRÍTICO", "action": "BLOCK_AND_REPORT", "response_to_user": "Alerta B"}
    )

    history_a = mem.get_history("user_alpha")
    history_b = mem.get_history("user_beta")

    assert len(history_a) == 1
    assert len(history_b) == 1
    assert history_a[0].user_input == "Mensaje de prueba usuario A"
    assert history_b[0].user_input == "Mensaje de prueba usuario B"
    assert history_a[0].risk_level == "BAJO"
    assert history_b[0].risk_level == "CRÍTICO"


def test_memory_sliding_window_limit():
    """Verifica que la ventana deslizante devuelva exactamente los últimos N turnos."""
    mem = ConversationMemory(max_turns_window=3)
    for i in range(1, 6):
        mem.add_turn(
            session_id="session_window",
            user_input=f"Pregunta {i}",
            agent_decision={"mode": "threat_inspection", "risk_level": "BAJO", "action": "ANALYZE_ONLY", "response_to_user": f"Respuesta {i}"}
        )

    # El historial completo debe tener 5 turnos
    full_history = mem.get_history("session_window")
    assert len(full_history) == 5

    # El contexto resumido solo debe contener los últimos 3 turnos (3, 4, 5)
    summary = mem.get_context_summary("session_window")
    assert "Pregunta 1" not in summary
    assert "Pregunta 2" not in summary
    assert "Pregunta 3" in summary
    assert "Pregunta 4" in summary
    assert "Pregunta 5" in summary


def test_memory_active_trip_lifecycle():
    """Verifica el ciclo de vida de un viaje en taxi: inicio, retención y finalización."""
    mem = ConversationMemory()
    trip_payload = {
        "status": "active",
        "trip_id": "TRIP-2026-X88",
        "vehicle_plate": "WTL456",
        "destination": "Chicó Norte",
        "monitoring_active": True,
    }

    # Turno 1: Se registra el viaje
    mem.add_turn(
        session_id="trip_user",
        user_input="Me subí al taxi WTL456 para Chicó Norte",
        agent_decision={"mode": "route_companion", "risk_level": "BAJO", "action": "SCHEDULE_CHECKIN", "response_to_user": "Acompañamiento iniciado"},
        tool_results={"route": trip_payload}
    )

    active = mem.get_active_trip("trip_user")
    assert active is not None
    assert active["vehicle_plate"] == "WTL456"

    # El resumen de contexto debe incluir la alerta del viaje activo
    summary = mem.get_context_summary("trip_user")
    assert "ESTADO ACTIVO: VIAJE EN CURSO" in summary
    assert "WTL456" in summary

    # Finalizar viaje
    cleared = mem.clear_active_trip("trip_user")
    assert cleared["vehicle_plate"] == "WTL456"
    assert mem.get_active_trip("trip_user") is None


def test_memory_threat_context_retention():
    """Verifica que una amenaza detectada guarde el contexto de incidente."""
    mem = ConversationMemory()
    mem.add_turn(
        session_id="victim_session",
        user_input="Bancolombia: su cuenta fue bloqueada",
        agent_decision={
            "mode": "threat_inspection",
            "risk_level": "CRÍTICO",
            "action": "BLOCK_AND_REPORT",
            "reasoning": "Phishing con URL fraudulenta",
            "response_to_user": "No abras el enlace"
        },
        police_report={"report_id": "CAI-COL-20261029-A1"}
    )

    summary = mem.get_context_summary("victim_session")
    assert "ALERTA PREVIA EN CURSO: Riesgo CRÍTICO" in summary
    assert "CAI-COL-20261029-A1" in summary


def test_memory_export_and_import_session():
    """Verifica la serialización y deserialización completa de una sesión."""
    mem = ConversationMemory()
    mem.add_turn(
        session_id="export_test",
        user_input="Hola SentinelGuard",
        agent_decision={"mode": "threat_inspection", "risk_level": "BAJO", "action": "ANALYZE_ONLY", "response_to_user": "Hola, ¿en qué te ayudo?"}
    )

    exported = mem.export_session("export_test")
    assert exported["session_id"] == "export_test"
    assert len(exported["turns"]) == 1

    # Importar en una nueva instancia de memoria
    new_mem = ConversationMemory()
    imported_session = new_mem.import_session(exported)

    assert imported_session.session_id == "export_test"
    assert len(new_mem.get_history("export_test")) == 1
    assert new_mem.get_history("export_test")[0].user_input == "Hola SentinelGuard"


def test_memory_clear_operations():
    """Verifica el vaciado de sesión y de todas las sesiones."""
    mem = ConversationMemory()
    mem.add_turn("s1", "m1", {"risk_level": "BAJO"})
    mem.add_turn("s2", "m2", {"risk_level": "BAJO"})

    mem.clear_session("s1")
    assert len(mem.get_history("s1")) == 0
    assert len(mem.get_history("s2")) == 1

    mem.clear_all()
    assert len(mem.get_history("s2")) == 0
