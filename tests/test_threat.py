"""
Pruebas Unitarias para ThreatInspector
Rol: Nicolle (Social Engineering & NLP Specialist)
"""

from src.tools.threat_inspector import inspect_threat

def test_inspect_legitimate_message():
    message = "Hola mamá, ¿cómo estás? Ya voy saliendo del trabajo."
    result = inspect_threat(message)
    assert result["status"] == "success"
    assert result["threat_level"] == "BAJO"
    assert result["risk_score"] < 30

def test_inspect_bancolombia_phishing():
    message = "Bancolombia informa: Su cuenta ha sido bloqueada. Urgente ingrese a http://banc0lombia-alerta.cc para evitar suspensión."
    result = inspect_threat(message)
    assert result["status"] == "success"
    assert result["threat_level"] in ["MEDIO", "CRÍTICO"]
    assert len(result["suspicious_urls"]) > 0
    assert result["risk_score"] >= 40

def test_inspect_urgency_triggers():
    message = "Urgente, inmediato haga clic para evitar embargo y orden de captura."
    result = inspect_threat(message)
    assert result["status"] == "success"
    assert len(result["matched_triggers"]) > 0
