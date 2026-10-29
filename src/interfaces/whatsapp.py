"""
Servidor Webhook para WhatsApp Cloud API (Meta Sandbox y Producción)
SentinelGuard AI · El Guardaespaldas Autónomo Ciudadano
Reto Agente 2026 - Platica.mx × Campuslands

Este módulo permite:
1. Recibir mensajes entrantes de WhatsApp vía Webhook de Meta.
2. Mantener memoria conversacional multi-turno por cada número de teléfono (session_id).
3. Procesar las solicitudes con SentinelAgent (Detección de estafas, URLs, comprobantes y taxis).
4. Responder al usuario en WhatsApp de forma automática e inmediata con dictámenes estructurados.
5. Modo simulado local: permite probar sin credenciales de Meta registrando los envíos en consola/logs.
"""

import json
import urllib.request
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel

from src.agent.sentinel import SentinelAgent
from src.config import (
    WHATSAPP_VERIFY_TOKEN,
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_API_VERSION,
    is_whatsapp_configured,
)
from src.utils.logger import logger

app = FastAPI(
    title="SentinelGuard AI · WhatsApp Webhook",
    description="Integración de SentinelGuard AI con WhatsApp Cloud API / Meta Sandbox",
    version="1.0.0"
)

# Instancia global del agente con memoria multi-turno habilitada
agent = SentinelAgent()


class SimulateMessageRequest(BaseModel):
    phone: str
    message: str
    metadata: Optional[Dict[str, Any]] = None


def format_whatsapp_reply(
    decision: Dict[str, Any],
    police_report: Optional[Dict[str, Any]] = None,
    active_trip: Optional[Dict[str, Any]] = None
) -> str:
    """
    Construye el texto de respuesta formateado con emojis y estructura óptima para WhatsApp.
    """
    response_to_user = decision.get("response_to_user", "").strip()
    action = decision.get("action", "ANALYZE_ONLY")

    parts = [response_to_user]

    # Si se generó radicado formal para el CAI Virtual
    if police_report and isinstance(police_report, dict) and police_report.get("report_id"):
        report_id = police_report["report_id"]
        parts.append(
            f"\n\n📋 *RADICADO PREVENTIVO CAI VIRTUAL:*\n"
            f"🆔 `{report_id}`\n"
            f"🛡️ *Acción:* Caso catalogado para reporte policial. Mantén bloqueado el número remitente."
        )

    # Si el usuario tiene un viaje de transporte activo
    if active_trip and isinstance(active_trip, dict):
        plate = active_trip.get("vehicle_plate", "N/A")
        dest = active_trip.get("destination", "Destino registrado")
        if action == "TRIGGER_ALARM":
            parts.append(
                f"\n\n🚨 *ALERTA DE SEGURIDAD FÍSICA:*\n"
                f"🚖 Vehículo: *{plate}* | Destino: *{dest}*\n"
                f"📡 Se ha emitido notificación de emergencia con la matrícula del vehículo."
            )
        elif action == "SCHEDULE_CHECKIN":
            parts.append(
                f"\n\n🚖 *Acompañamiento Activo:* Vehículo *{plate}* hacia *{dest}*. Te recordaremos chequear en 10 min."
            )

    return "".join(parts)


def send_whatsapp_message(to_phone: str, text: str) -> Dict[str, Any]:
    """
    Envía un mensaje de texto saliente a un número de WhatsApp vía Meta Cloud API.
    Si no hay credenciales configuradas, opera en modo simulado local ($0.00 USD).
    """
    to_clean = "".join(filter(str.isdigit, to_phone))

    if not is_whatsapp_configured():
        logger.info(
            f"[dim cyan]📱 [SIMULACIÓN WHATSAPP] Para: {to_clean} | "
            f"Mensaje: {text[:100]}...[/dim cyan]"
        )
        return {
            "status": "simulated",
            "recipient": to_clean,
            "message_sent": text,
            "notes": "Modo local: configura WHATSAPP_ACCESS_TOKEN y WHATSAPP_PHONE_NUMBER_ID en .env para envíos reales."
        }

    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_clean,
        "type": "text",
        "text": {"body": text},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_body = resp.read().decode("utf-8")
            response_data = json.loads(resp_body) if resp_body else {}
            logger.info(f"[green]✓ Mensaje WhatsApp enviado exitosamente a {to_clean}[/green]")
            return {"status": "sent", "response": response_data}
    except Exception as exc:
        logger.error(f"[red]❌ Excepción de red al enviar WhatsApp ({exc})[/red]")
        return {"status": "network_error", "error": str(exc)}


@app.get("/")
def health_check():
    """Estado y configuración del servicio de WhatsApp Webhook."""
    return {
        "service": "SentinelGuard AI · WhatsApp Webhook",
        "status": "online",
        "configured_for_live_api": is_whatsapp_configured(),
        "verify_token_configured": bool(WHATSAPP_VERIFY_TOKEN),
        "endpoint_webhook": "/webhook",
        "memory_active": True,
    }


@app.get("/webhook")
def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """
    Protocolo de verificación de Webhook de Meta (Handshake inicial).
    Meta envía un GET con hub.mode, hub.verify_token y hub.challenge.
    """
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        logger.info("[green]✓ Verificación de Webhook de WhatsApp completada con éxito por Meta.[/green]")
        return PlainTextResponse(content=hub_challenge or "", status_code=status.HTTP_200_OK)

    logger.warning("[yellow]⚠ Intento de verificación de Webhook con token inválido o parámetros ausentes.[/yellow]")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verificación fallida: token inválido")


@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    Receptor principal de eventos y mensajes entrantes de WhatsApp de Meta.
    Procesa el mensaje con SentinelGuard AI y responde automáticamente.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JSON malformado")

    # Validar si el evento proviene de un mensaje de WhatsApp
    entries = body.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])

            for msg in messages:
                sender_phone = msg.get("from")
                msg_type = msg.get("type")

                user_text = ""
                image_metadata = {}

                if msg_type == "text":
                    user_text = msg.get("text", {}).get("body", "")
                elif msg_type == "image":
                    caption = msg.get("image", {}).get("caption", "")
                    user_text = caption or "Analiza este comprobante adjunto"
                    image_metadata["whatsapp_media_id"] = msg.get("image", {}).get("id")
                elif msg_type == "location":
                    loc = msg.get("location", {})
                    user_text = f"Ubicación en ruta: Lat {loc.get('latitude')}, Long {loc.get('longitude')}"
                else:
                    user_text = f"Mensaje recibido de tipo: {msg_type}"

                if not sender_phone or not user_text.strip():
                    continue

                logger.info(f"[cyan]📱 Mensaje recibido de WhatsApp ({sender_phone}):[/cyan] {user_text[:80]}")

                # Invocar al agente utilizando el número de teléfono como session_id (Memoria Multi-Turno)
                agent_result = agent.process_message(
                    user_input=user_text,
                    session_id=str(sender_phone),
                    metadata={"sender": str(sender_phone), "channel": "whatsapp", **image_metadata}
                )

                decision = agent_result.get("decision", {})
                police_report = agent_result.get("police_report")
                active_trip = agent_result.get("active_trip")

                # Formatear y enviar respuesta de vuelta a WhatsApp
                reply_text = format_whatsapp_reply(decision, police_report=police_report, active_trip=active_trip)
                send_whatsapp_message(to_phone=sender_phone, text=reply_text)

    # Meta requiere responder 200 OK inmediatamente para confirmar recepción del evento
    return JSONResponse(content={"status": "EVENT_RECEIVED"}, status_code=status.HTTP_200_OK)


@app.post("/api/simulate-message")
def simulate_whatsapp_message(req: SimulateMessageRequest):
    """
    Endpoint para probar el bot de WhatsApp en local o desde frontend sin requerir Meta ni ngrok.
    """
    agent_result = agent.process_message(
        user_input=req.message,
        session_id=req.phone,
        metadata={"sender": req.phone, "channel": "whatsapp_simulation", **(req.metadata or {})}
    )
    decision = agent_result.get("decision", {})
    police_report = agent_result.get("police_report")
    active_trip = agent_result.get("active_trip")

    reply_text = format_whatsapp_reply(decision, police_report=police_report, active_trip=active_trip)

    return {
        "status": "success",
        "phone": req.phone,
        "input_message": req.message,
        "agent_result": agent_result,
        "whatsapp_reply_preview": reply_text,
        "turn_id": agent_result.get("turn_id"),
    }
