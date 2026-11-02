"""
Pruebas de Integración y Contrato: Evaluación de Respuestas de Audio en Flujo de Taxi
Hito S3: Reto Agente 2026 - SentinelGuard AI · Equipo Codixia

Integración solicitada por Nicolle (NLP, Visión & CAI Virtual):
1. Evaluar la transcripción de la respuesta del pasajero mediante evaluate_trip_audio_response.
2. Recuperar y propagar el score y nivel de amenaza (risk_score, threat_level, risk_level).
3. Aplicar la escalada correspondiente (PHYSICAL_RISK) ante situaciones de riesgo o pánico.
4. Verificar que la integración no altere el comportamiento del modo digital (Escudo Digital).
5. Validar flujos de check-in ordinario, palabra de seguridad pendiente y tolerancia a fallos.

Todas las pruebas operan en modo local con blindaje presupuestario estricto ($0.00 USD).
"""

import pytest
from unittest.mock import patch
from src.agent.sentinel import SentinelAgent
from src.client import GrokClient


def test_taxi_audio_evaluation_panic_in_user_input():
    """
    Verifica que una respuesta del pasajero con palabras de pánico invoque
    evaluate_trip_audio_response, marque 'alert', propague risk_score=100
    y active escalada PHYSICAL_RISK.
    """
    agent = SentinelAgent()
    session_id = "test_taxi_panic_input"

    # Turno 1: Abordaje normal
    res1 = agent.process_message(
        "Me subí a un taxi placas ABC123 hacia el Parque 93",
        metadata={"plate": "ABC123", "destination": "Parque 93"},
        session_id=session_id
    )
    assert res1["status"] == "success"
    assert res1["decision"]["mode"] == "route_companion"
    assert res1["decision"]["risk_level"] == "BAJO"
    assert res1["decision"]["risk_score"] == 0
    assert res1["escalation"] is None

    # Turno 2: Respuesta con situación de pánico en cabina
    res2 = agent.process_message(
        "¡Ayuda por favor, el conductor sacó un arma y tomó un desvío hacia una trocha!",
        session_id=session_id
    )

    assert res2["status"] == "success"
    assert "audio_eval" in res2["tool_results"]
    audio_eval = res2["tool_results"]["audio_eval"]
    assert audio_eval["status"] == "alert"
    assert audio_eval["is_safe"] is False
    assert audio_eval["escalation_required"] is True

    # Verificación de propagación de score y niveles
    decision = res2["decision"]
    assert decision["mode"] == "route_companion"
    assert decision["risk_level"] == "CRÍTICO"
    assert decision["threat_level"] == "CRÍTICO"
    assert decision["risk_score"] == 100
    assert decision["action"] == "TRIGGER_ALARM"

    # Verificación de escalada física
    assert res2["escalation"] is not None
    assert res2["escalation"]["status"] == "escalated"
    assert res2["escalation"]["incident_type"] == "PHYSICAL_RISK"
    assert res2["escalation"]["severity"] == "CRITICAL"
    assert "deterrent_audio_script" in res2["escalation"]
    assert res2["police_report"] is None  # Reportes CAI Virtual son exclusivos de fraude digital


def test_taxi_audio_evaluation_via_metadata_transcript():
    """
    Verifica que la transcripción provista en metadata['audio_transcript']
    sea evaluada por evaluate_trip_audio_response y determine el resultado.
    """
    agent = SentinelAgent()
    session_id = "test_taxi_audio_meta"

    res = agent.process_message(
        "Audio recibido del trayecto",
        metadata={
            "plate": "TLK789",
            "destination": "Aeropuerto El Dorado",
            "audio_transcript": "Auxilio, nos desviaron y el conductor no me responde"
        },
        session_id=session_id
    )

    assert res["status"] == "success"
    assert "audio_eval" in res["tool_results"]
    audio_eval = res["tool_results"]["audio_eval"]
    assert audio_eval["status"] == "alert"
    assert audio_eval["escalation_required"] is True

    assert res["decision"]["risk_level"] == "CRÍTICO"
    assert res["decision"]["risk_score"] == 100
    assert res["escalation"] is not None
    assert res["escalation"]["incident_type"] == "PHYSICAL_RISK"


def test_taxi_audio_evaluation_normal_checkin():
    """
    Verifica que una respuesta de check-in normal resulte en is_safe=True,
    score=0, risk_level=BAJO y sin escalada de emergencia.
    """
    agent = SentinelAgent()
    session_id = "test_taxi_normal_checkin"

    # Turno 1: Iniciar taxi
    agent.process_message(
        "Voy en taxi placas WDY452 hacia Chapinero",
        metadata={"plate": "WDY452", "destination": "Chapinero"},
        session_id=session_id
    )

    # Turno 2: Respuesta normal de check-in
    res2 = agent.process_message(
        "Todo va bien, tráfico tranquilo por la carrera séptima",
        session_id=session_id
    )

    assert res2["status"] == "success"
    assert "audio_eval" in res2["tool_results"]
    audio_eval = res2["tool_results"]["audio_eval"]
    assert audio_eval["status"] == "normal"
    assert audio_eval["is_safe"] is True
    assert audio_eval["escalation_required"] is False

    assert res2["decision"]["mode"] == "route_companion"
    assert res2["decision"]["risk_level"] == "BAJO"
    assert res2["decision"]["risk_score"] == 0
    assert res2["escalation"] is None


def test_taxi_audio_evaluation_safeword_mismatch_checkin_pending():
    """
    Verifica que si se configuró palabra de seguridad y la respuesta no la incluye,
    se marque 'checkin_pending', risk_score intermedio (>= 50), nivel MEDIO y sin SOS.
    """
    agent = SentinelAgent()
    session_id = "test_taxi_safeword_pending"

    # Turno 1: Registrar viaje con palabra de seguridad
    res1 = agent.process_message(
        "Voy en taxi placas HKO112 a Salitre Plaza",
        metadata={"plate": "HKO112", "destination": "Salitre Plaza", "expected_safe_word": "manzana"},
        session_id=session_id
    )
    assert res1["status"] == "success"

    # Turno 2: Respuesta del pasajero que omite la palabra segura
    res2 = agent.process_message(
        "Sí, aquí sigo en el carro",
        metadata={"expected_safe_word": "manzana"},
        session_id=session_id
    )

    assert res2["status"] == "success"
    assert "audio_eval" in res2["tool_results"]
    audio_eval = res2["tool_results"]["audio_eval"]
    assert audio_eval["status"] == "checkin_pending"
    assert audio_eval["is_safe"] is False
    assert audio_eval["escalation_required"] is False

    assert res2["decision"]["risk_score"] >= 50
    assert res2["decision"]["risk_level"] in ["MEDIO", "ALTO"]
    # No debe disparar alarma SOS completa ante simple pendiente de confirmación
    assert res2["escalation"] is None


def test_taxi_flow_threat_score_propagation():
    """
    Confirma que en modo taxi los campos risk_score y threat_level se propagan
    íntegramente en la decisión final del agente y en el payload devuelto.
    """
    agent = SentinelAgent()
    res = agent.process_message(
        "Inicio trayecto en taxi placa BNA345 hacia mi oficina",
        metadata={"plate": "BNA345", "destination": "Oficina"}
    )

    assert res["status"] == "success"
    assert "decision" in res
    assert "risk_score" in res["decision"]
    assert "threat_level" in res["decision"]
    assert isinstance(res["decision"]["risk_score"], int)
    assert 0 <= res["decision"]["risk_score"] <= 100
    assert res["decision"]["threat_level"] in ["BAJO", "MEDIO", "ALTO", "CRÍTICO"]


def test_taxi_audio_evaluation_graceful_on_tool_failure():
    """
    Verifica tolerancia a fallos: si evaluate_trip_audio_response lanza excepción,
    el agente captura el error limpiamente, no aborta y reporta el incidente con fallback.
    """
    agent = SentinelAgent()

    with patch("src.agent.sentinel.evaluate_trip_audio_response", side_effect=RuntimeError("Falla de audio DSP")):
        res = agent.process_message(
            "Voy en taxi placa TAZ123 al terminal",
            metadata={"plate": "TAZ123", "destination": "Terminal"}
        )

        assert res["status"] == "success"
        assert "audio_eval" in res["tool_results"]
        assert res["tool_results"]["audio_eval"]["status"] == "error"
        assert "Falla de audio DSP" in res["tool_results"]["audio_eval"]["error"]


def test_digital_mode_strictly_isolated_from_taxi_evaluation():
    """
    Verifica que el modo digital (Escudo Digital) NO ejecute evaluate_trip_audio_response
    ni herramientas de ruta, manteniendo intacto su comportamiento original.
    """
    agent = SentinelAgent()

    # Mensaje de smishing bancario
    res = agent.process_message(
        "Bancolombia informa: Alerta de seguridad. Su clave vence hoy, actualice en https://bancolombia-seguridad.cc"
    )

    assert res["status"] == "success"
    assert res["decision"]["mode"] == "threat_inspection"
    assert res["decision"]["risk_level"] in ["ALTO", "CRÍTICO"]
    assert "threat" in res["tool_results"]
    assert "url_sandbox" in res["tool_results"]
    # Herramientas de ruta y audio NO deben ejecutarse en modo digital
    assert "audio_eval" not in res["tool_results"]
    assert "route" not in res["tool_results"]
    # Reporte policial generado para CAI Virtual
    assert res["police_report"] is not None
    assert "CAI-COL-" in res["police_report"]["report_id"]
