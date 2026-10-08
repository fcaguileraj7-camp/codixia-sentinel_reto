"""
Pruebas de Integración para SentinelAgent Core
Rol: Fabián Aguilera (Lead Architect & Core Orchestrator)
"""

from src.agent.sentinel import SentinelAgent

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
