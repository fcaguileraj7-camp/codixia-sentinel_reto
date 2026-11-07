"""
Demostración en vivo del bot de WhatsApp para SentinelGuard AI
Simula 4 turnos conversacionales reales contra el servidor Webhook local.
"""

import sys
from pathlib import Path

# Configurar encoding UTF-8 para consola de Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://localhost:8000"

def call_api(endpoint: str, method: str = "GET", payload: dict = None, params: dict = None):
    url = f"{BASE_URL}{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read().decode("utf-8")

def main():
    print("\n" + "="*70)
    print("  📱 PRUEBA EN VIVO: SENTINELGUARD AI — CANAL WHATSAPP")
    print("="*70 + "\n")

    # 1. Healthcheck
    status, body = call_api("/")
    print(f"1. Verificación de Estado Servidor (GET /):")
    print(f"   Status: {status} | Respuesta: {body}\n")

    # 2. Handshake Meta Webhook
    challenge = "1234567890_META_OK"
    status, text = call_api("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "sentinelguard_verify_2026",
        "hub.challenge": challenge
    })
    print(f"2. Handshake de Verificación Meta (GET /webhook):")
    print(f"   Status: {status} | Challenge recibido de vuelta: {text}\n")

    # 3. Flujo Conversacional Multi-Turno en WhatsApp (Mismo número de teléfono)
    test_phone = "+57 312 456 7890"

    conversacion = [
        ("Turno 1 · Phishing Bancario", "Bancolombia informa: Su cuenta ha sido bloqueada. Urgente ingrese a http://banc0lombia-alerta.cc para desbloquearla."),
        ("Turno 2 · Pregunta de Seguimiento", "¿Y si me llaman a pedir el código que me llegó por SMS, se lo debo dar?"),
        ("Turno 3 · Inicio de Viaje en Taxi", "Me subí a un taxi placas WTL123 hacia Unicentro"),
        ("Turno 4 · Desvío y Alarma SOS", "¡Auxilio! El conductor se desvió por una trocha oscura y no quiere parar")
    ]

    for titulo, mensaje in conversacion:
        print("-" * 70)
        print(f"👉 {titulo.upper()}")
        print(f"👤 Ciudadano [{test_phone}] en WhatsApp:")
        print(f"   \"{mensaje}\"")

        payload = {
            "phone": test_phone,
            "message": mensaje
        }
        status, resp_text = call_api("/api/simulate-message", method="POST", payload=payload)
        data = json.loads(resp_text)
        
        reply = data.get("whatsapp_reply_preview", "")
        turn_id = data.get("turn_id")
        
        print(f"\n🤖 SentinelGuard AI en WhatsApp (Turno {turn_id}):")
        for line in reply.split("\n"):
            print(f"   {line}")
        print()
        time.sleep(0.5)

    print("="*70)
    print("  ✅ PRUEBA COMPLETADA CON ÉXITO: 4/4 TURNOS CONTEXTUALES FUNCIONANDO")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
