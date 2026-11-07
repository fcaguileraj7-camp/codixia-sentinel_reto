"""
Pruebas Unitarias e Integración para el Servidor Webhook de WhatsApp
SentinelGuard AI · Reto Agente 2026 - Platica.mx × Campuslands

Todas las pruebas operan en memoria local con TestClient ($0.00 USD).
"""

import pytest
from starlette.testclient import TestClient
from src.interfaces.whatsapp import app, format_whatsapp_reply
from src.config import WHATSAPP_VERIFY_TOKEN


@pytest.fixture
def client():
    return TestClient(app)


def test_whatsapp_health_check(client):
    """Verifica que el endpoint raíz responda con el estado del servicio."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["memory_active"] is True
    assert data["endpoint_webhook"] == "/webhook"


def test_whatsapp_webhook_verification_success(client):
    """Verifica el handshake exitoso con Meta usando el token configurado."""
    challenge = "1158201444"
    res = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": WHATSAPP_VERIFY_TOKEN,
        "hub.challenge": challenge
    })
    assert res.status_code == 200
    assert res.text == challenge


def test_whatsapp_webhook_verification_failure(client):
    """Verifica que Meta rechace intentos con tokens incorrectos (403)."""
    res = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "token_falso_incorrecto",
        "hub.challenge": "12345"
    })
    assert res.status_code == 403
    assert "token inválido" in res.json()["detail"]


def test_whatsapp_receive_incoming_phishing_message(client):
    """Verifica que un mensaje de phishing entrante sea recibido, procesado y responda 200 OK."""
    sender = "573001234567"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "10001",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "15551234", "phone_number_id": "999"},
                            "messages": [
                                {
                                    "from": sender,
                                    "id": "wamid.HBgL...",
                                    "timestamp": "1730000000",
                                    "type": "text",
                                    "text": {
                                        "body": "Bancolombia alerta: Su cuenta fue bloqueada. Ingrese a http://banc0lombia-seguro.xyz"
                                    }
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    res = client.post("/webhook", json=payload)
    assert res.status_code == 200
    assert res.json() == {"status": "EVENT_RECEIVED"}


def test_whatsapp_multiturn_conversation_flow(client):
    """
    Verifica que dos mensajes consecutivos del mismo número en WhatsApp
    mantengan el contexto en la memoria multi-turno (Hito S3).
    """
    sender = "573119876543"

    # Turno 1: Reporte de taxi
    res1 = client.post("/api/simulate-message", json={
        "phone": sender,
        "message": "Me acabo de subir al taxi placas TAZ888 hacia Unicentro",
        "metadata": {"plate": "TAZ888", "destination": "Unicentro"}
    })
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["turn_id"] == 1
    assert "TAZ888" in data1["whatsapp_reply_preview"]

    # Turno 2: Seguimiento de pánico
    res2 = client.post("/api/simulate-message", json={
        "phone": sender,
        "message": "¡Auxilio! El conductor se desvió por una trocha y no quiere parar"
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["turn_id"] == 2
    assert "TAZ888" in data2["whatsapp_reply_preview"]
    assert "EMERGENCIA" in data2["whatsapp_reply_preview"] or "ALERTA" in data2["whatsapp_reply_preview"]


def test_format_whatsapp_reply_badges():
    """Verifica que el formateador agregue radicados de policía y datos de transporte."""
    decision = {
        "response_to_user": "No consignes dinero.",
        "risk_level": "CRÍTICO",
        "mode": "threat_inspection",
        "action": "BLOCK_AND_REPORT"
    }
    police = {"report_id": "CAI-COL-20261029-99"}

    formatted = format_whatsapp_reply(decision, police_report=police)
    assert "No consignes dinero." in formatted
    assert "CAI-COL-20261029-99" in formatted
    assert "RADICADO PREVENTIVO" in formatted
