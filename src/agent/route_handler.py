"""
Módulo de Gestión y Orquestación de Acompañamiento Físico en Rutas (RouteCompanionHandler)
Hito S3: Reto Agente 2026 - SentinelGuard AI · Equipo Codixia

Desacoplado del pipeline de ciberseguridad de SentinelAgent para garantizar
la estricta separación de responsabilidades entre Escudo Digital y Seguridad Física.
"""

import json
import re
from typing import Dict, Any, Optional

from src.client import GrokClient
from src.agent.prompts import SENTINEL_SYSTEM_PROMPT
from src.agent.memory import ConversationMemory
from src.tools.threat_inspector import inspect_threat
from src.tools.emergency_escalator import escalate_emergency
from src.tools.route_companion import (
    register_trip,
    evaluate_trip_audio_response,
    confirm_checkin,
    finalize_trip,
)
from src.utils.logger import logger


def _is_physical_route_request(
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
    has_active_trip: bool = False
) -> bool:
    """
    Determina con alta precisión pericial si el mensaje corresponde a una solicitud
    de acompañamiento físico en ruta (taxi/transporte) o a una auditoría de ciberseguridad.
    Evita falsos positivos con mensajes de trámites/estafas que mencionan 'placas' o 'vehículos'.
    """
    metadata = metadata or {}
    audio_transcript = str(metadata.get("audio_transcript") or metadata.get("transcript") or "")
    t = f"{text} {audio_transcript}".lower()

    # Capa 1: Filtro de exclusión de fraude digital y trámites
    fraud_indicators = [
        "simit", "fotomulta", "comparendo", "multa", "infracción", "infraccion",
        "pague en línea", "pague en linea", "descuento hoy", "embargo", "bancolombia",
        "nequi", "daviplata", "dian", "claro", "sorteo", "premio", "ganador", "banco"
    ]
    if any(ind in t for ind in fraud_indicators):
        return False

    # Si hay un viaje activo en memoria, el seguimiento en curso se canaliza en modo ruta
    if has_active_trip:
        return True

    # Si vienen metadatos explícitos de viaje
    if metadata.get("plate") and metadata.get("destination"):
        return True

    # Capa 2: Términos explícitos de abordaje, transporte o auxilio en ruta
    transport_terms = [
        "taxi", "uber", "didi", "indriver", "cabify", "trayecto",
        "voy en", "me subí", "me subi", "abordé", "aborde", "inicio viaje", "inicio trayecto",
        "trocha oscura", "se desvió", "se desvio", "conductor no responde", "pánico", "panico",
        "auxilio", "ayuda", "desvío", "desvio"
    ]
    if any(term in t for term in transport_terms):
        return True

    # Capa 3: Patrón estricto de matrícula vehicular colombiana (AAA-123 / AAA123)
    has_plate = bool(re.search(r"\b[a-z]{3}[-\s]?\d{3}\b", t))
    has_trip_context = any(w in t for w in ["hacia", "destino", "camino", "conductor", "ruta", "llegando", "desplaz"])

    return has_plate and has_trip_context


# Frases con las que el pasajero da por terminado el viaje. Solo cierran el viaje si el
# mensaje no es de pánico y, cuando hay palabra segura, la respuesta la confirma.
_TRIP_CLOSING_RE = re.compile(
    r"\b(ya llegu[eé]|llegu[eé] bien|llegamos|finaliz(?:ar|o|amos) (?:el )?viaje|"
    r"termin(?:ar|o|é|e|amos) (?:el )?viaje|fin del viaje|me baj[eé]|cancel(?:ar|o) (?:el )?viaje)\b"
)


def _is_trip_closing(text: str) -> bool:
    """Indica si el texto del pasajero comunica que el viaje terminó."""
    return bool(_TRIP_CLOSING_RE.search(str(text).lower()))


def _close_trip(active_trip: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cierra el viaje en route_companion y devuelve el estado de ruta con status "finished",
    que es el que ConversationMemory interpreta como viaje terminado y limpia de la sesión.
    Un fallo de la herramienta no impide cerrar el viaje del lado de la conversación.
    """
    closing = {
        **active_trip,
        "status": "finished",
        "event": "TRIP_FINISHED",
        "monitoring_active": False,
    }
    try:
        result = finalize_trip(active_trip.get("trip_id"), reason="arrival_confirmed")
        closing["finalize_status"] = result.get("status")
        if result.get("status") == "error":
            closing["finalize_error"] = result.get("error")
    except Exception as e:
        logger.warning(f"[yellow]⚠ Falla en tool finalize_trip ({e}). El viaje se cierra solo en la conversación.[/yellow]")
        closing["finalize_status"] = "error"
        closing["finalize_error"] = str(e)
    return closing


def _checkin_fields(active_trip: Dict[str, Any]) -> Dict[str, Any]:
    """Registra el check-in en route_companion y devuelve sus campos para el estado de ruta."""
    try:
        result = confirm_checkin(active_trip.get("trip_id"))
    except Exception as e:
        logger.warning(f"[yellow]⚠ Falla en tool confirm_checkin ({e}). Continuando con fallback.[/yellow]")
        return {}
    if result.get("status") != "success":
        return {}
    return {k: result[k] for k in ("last_checkin_at", "next_checkin_scheduled", "checkin_count") if k in result}


def _redact_for_prompt(tool_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Copia de tool_results sin la palabra segura del viaje. Grok no la necesita (la validación
    se hace en local en evaluate_trip_audio_response) y es un secreto del pasajero.
    """
    redacted = dict(tool_results)
    route = redacted.get("route")
    if isinstance(route, dict) and "safe_word" in route:
        redacted["route"] = {k: v for k, v in route.items() if k != "safe_word"}
    return redacted


class RouteCompanionHandler:
    """
    Orquestador especializado en el ciclo de vida de acompañamiento físico y emergencias en taxi.
    Gestiona registro de ruta, evaluación acústica/textual, chequeos preventivos y escalada SOS.
    """

    def __init__(
        self,
        client: Optional[GrokClient] = None,
        memory: Optional[ConversationMemory] = None
    ):
        self.client = client if client is not None else GrokClient()
        self.memory = memory if memory is not None else ConversationMemory()

    def process_route_message(
        self,
        user_input: str,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: str = "default",
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline exclusivo de acompañamiento físico en ruta:
        Evaluación de Audio/Texto -> Registro/Check-in -> Razonamiento Grok -> Escalada SOS (PHYSICAL_RISK).
        """
        metadata = metadata or {}
        mem = self.memory
        cli = self.client

        logger.info(f"[cyan]→ [RouteCompanion] Procesando solicitud física (Sesión: {session_id}):[/cyan] {user_input[:80]}...")

        tool_results: Dict[str, Any] = {}
        active_trip = mem.get_active_trip(session_id)

        plate = metadata.get("plate") or (active_trip.get("vehicle_plate") if active_trip else "ABC123")
        dest = metadata.get("destination") or (active_trip.get("destination") if active_trip else "Destino particular")

        # 1. Evaluación de transcripción de audio / mensaje del pasajero (Hito S3)
        transcript = metadata.get("audio_transcript") or metadata.get("transcript") or user_input
        expected_safe_word = (
            metadata.get("expected_safe_word")
            or metadata.get("safe_word")
            or (active_trip.get("safe_word") if active_trip else None)
        )

        if isinstance(transcript, str) and transcript.strip():
            try:
                audio_eval = evaluate_trip_audio_response(
                    transcript=transcript.strip(),
                    expected_safe_word=expected_safe_word
                )
                tool_results["audio_eval"] = audio_eval
                logger.info(f"[blue]⚡ Tool ejecutada: evaluate_trip_audio_response -> {audio_eval.get('status')}[/blue]")
            except Exception as e:
                logger.warning(f"[yellow]⚠ Falla en tool evaluate_trip_audio_response ({e}). Continuando con fallback.[/yellow]")
                audio_eval = {
                    "status": "error",
                    "is_safe": False,
                    "escalation_required": False,
                    "reason": str(e),
                    "error": str(e)
                }
                tool_results["audio_eval"] = audio_eval
        else:
            audio_eval = {
                "status": "normal",
                "is_safe": True,
                "escalation_required": False,
                "reason": "Sin transcripción provista; evaluación omitida."
            }
            tool_results["audio_eval"] = audio_eval

        # 2. Detección de coacción y señales de estrés en cabina
        threat_input = transcript if (isinstance(transcript, str) and transcript.strip()) else user_input
        try:
            threat_data = inspect_threat(threat_input)
            tool_results["threat"] = threat_data
            logger.info(f"[blue]⚡ Tool ejecutada: inspect_threat (taxi) -> Nivel {threat_data.get('threat_level')}, Score {threat_data.get('risk_score')}[/blue]")
        except Exception as e:
            logger.warning(f"[yellow]⚠ Falla en tool inspect_threat ({e}). Continuando con fallback.[/yellow]")
            threat_data = {
                "status": "error",
                "threat_level": "MEDIO",
                "risk_score": 50,
                "error": str(e)
            }
            tool_results["threat"] = threat_data

        is_panic = (
            audio_eval.get("escalation_required", False)
            or audio_eval.get("status") == "alert"
            or threat_data.get("threat_level") in ["ALTO", "CRÍTICO"]
            or any(w in user_input.lower() for w in [
                "desvió", "desvio", "trocha", "panico", "pánico", "auxilio",
                "miedo", "no para", "no frena", "apaga", "secuestr", "peligro",
                "ayuda", "socorro", "arma", "emergencia"
            ])
            or any(w in str(transcript).lower() for w in [
                "desvió", "desvio", "trocha", "panico", "pánico", "auxilio",
                "miedo", "no para", "no frena", "apaga", "secuestr", "peligro",
                "ayuda", "socorro", "arma", "emergencia"
            ])
        )

        # 3. Registro o actualización del estado del viaje
        if not active_trip:
            try:
                tool_results["route"] = register_trip(plate=plate, destination=dest)
                logger.info(f"[blue]⚡ Tool ejecutada: register_trip -> {tool_results['route'].get('trip_id')}[/blue]")
            except Exception as e:
                logger.warning(f"[yellow]⚠ Falla en tool register_trip ({e}). Continuando con fallback.[/yellow]")
                tool_results["route"] = {"status": "error", "error": str(e), "monitoring_active": False}

            if expected_safe_word and isinstance(tool_results.get("route"), dict):
                tool_results["route"]["safe_word"] = expected_safe_word

            if is_panic and tool_results.get("route", {}).get("status") == "active":
                tool_results["route"]["event"] = "PANIC_REPORTED"
                tool_results["route"]["panic_signal"] = True
        elif is_panic:
            tool_results["route"] = {
                **active_trip,
                "event": "PANIC_REPORTED",
                "panic_signal": True,
                "monitoring_active": True
            }
            logger.info(f"[red]⚡ Alerta de pánico detectada en viaje activo: {active_trip.get('trip_id')}[/red]")
        elif audio_eval.get("status") == "checkin_pending":
            tool_results["route"] = {
                **active_trip,
                "event": "CHECKIN_PENDING",
                "monitoring_active": True
            }
        elif _is_trip_closing(f"{user_input} {transcript}"):
            # solo llega aquí sin pánico y con la palabra segura confirmada (o sin palabra segura)
            tool_results["route"] = _close_trip(active_trip)
            logger.info(f"[green]⚡ Viaje finalizado por el pasajero: {active_trip.get('trip_id')}[/green]")
        else:
            # Viaje en curso, check-in ordinario
            tool_results["route"] = {
                **active_trip,
                **_checkin_fields(active_trip),
                "event": "CHECKIN_NORMAL",
                "monitoring_active": True
            }

        # 4. Contexto de razonamiento para Grok
        history_summary = mem.get_context_summary(session_id=session_id)
        context_prompt = (
            f"SOLICITUD DE ACOMPAÑAMIENTO FÍSICO EN RUTA:\n"
            f"Mensaje del usuario: \"{user_input}\"\n\n"
            f"Telemetría y herramientas:\n{json.dumps(_redact_for_prompt(tool_results), ensure_ascii=False, indent=2)}\n\n"
            f"Analiza la situación del trayecto y decide el plan de acción en formato JSON."
        )
        if history_summary:
            context_prompt += (
                f"\n\nHISTORIAL CONVERSACIONAL PREVIO (MEMORIA MULTI-TURNO):\n"
                f"{history_summary}\n"
                f"Considera este historial anterior para mantener la coherencia y responder adecuadamente al seguimiento."
            )

        messages = [
            {"role": "system", "content": SENTINEL_SYSTEM_PROMPT},
            {"role": "user", "content": context_prompt}
        ]

        logger.info("[magenta]🧠 Consultando núcleo de razonamiento Grok 4.7 (Ruta física)...[/magenta]")
        status = "success"
        try:
            raw_response = cli.chat_completion(messages, max_tokens=700)
            json_start = raw_response.find("{")
            json_end = raw_response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                decision = json.loads(raw_response[json_start:json_end])
            else:
                decision = json.loads(raw_response.strip())

            if not isinstance(decision, dict):
                raise ValueError("La respuesta del modelo no contiene un objeto JSON válido.")
            decision["analysis_available"] = True
        except Exception as e:
            logger.error(f"[red]❌ Error en la inferencia del modelo en ruta ({e}). Usando fallback.[/red]")
            status = "error"
            decision = {
                "mode": "route_companion",
                "analysis_available": False,
                "risk_level": "NO_ANALIZADO",
                "reasoning": f"Falla del servicio de inferencia en ruta: {str(e)}",
                "action": "MANUAL_REVIEW_REQUIRED",
                "response_to_user": (
                    "⚠\ufe0f No se pudo procesar la confirmación del trayecto debido a un fallo técnico. "
                    "Por seguridad, si te encuentras en peligro llama de inmediato al 123."
                )
            }

        # 5. Reconciliación de score y modo de acompañamiento
        if decision.get("analysis_available", True):
            decision["mode"] = "route_companion"
            if is_panic or (audio_eval and (audio_eval.get("escalation_required") or audio_eval.get("status") == "alert")):
                decision["risk_level"] = "CRÍTICO"
                decision["action"] = "TRIGGER_ALARM"
                decision["risk_score"] = 100
                decision["threat_level"] = "CRÍTICO"
            elif audio_eval and audio_eval.get("status") == "checkin_pending":
                t_score = tool_results.get("threat", {}).get("risk_score", 0)
                decision["risk_score"] = max(50, t_score)
                decision["threat_level"] = "ALTO" if decision["risk_score"] >= 60 else "MEDIO"
                if decision.get("risk_level") not in ["ALTO", "CRÍTICO"]:
                    decision["risk_level"] = decision["threat_level"]
                if decision.get("action") not in ["TRIGGER_ALARM", "REQUEST_CONFIRMATION"]:
                    decision["action"] = "REQUEST_CONFIRMATION"
            else:
                t_score = tool_results.get("threat", {}).get("risk_score", 0)
                t_level = tool_results.get("threat", {}).get("threat_level", decision.get("risk_level", "BAJO"))
                decision.setdefault("risk_score", t_score)
                decision.setdefault("threat_level", t_level)
                decision.setdefault("risk_level", decision.get("threat_level", "BAJO"))

        # 6. Escalada de emergencia física (PHYSICAL_RISK)
        escalation_result = None
        if decision.get("analysis_available", True) and (
            decision.get("risk_level") in ["ALTO", "CRÍTICO"] or decision.get("action") == "TRIGGER_ALARM"
        ):
            logger.warning(f"[red]🚨 Activando protocolo SOS físico: Riesgo {decision.get('risk_level')}[/red]")
            try:
                escalation_result = escalate_emergency(
                    incident_type="PHYSICAL_RISK",
                    evidence_payload={
                        "input": user_input,
                        "transcript": transcript,
                        "decision": decision,
                        "tools": tool_results
                    }
                )
            except Exception as e:
                logger.warning(f"[yellow]⚠ Falla en escalate_emergency ({e})[/yellow]")
                escalation_result = {"status": "error", "error": str(e)}

        # 7. Persistencia en memoria conversacional
        turn_record = mem.add_turn(
            session_id=session_id,
            user_input=user_input,
            agent_decision=decision,
            tool_results=tool_results,
            metadata=metadata,
            police_report=None,
        )

        return {
            "status": status,
            "session_id": session_id,
            "turn_id": turn_record.turn_id,
            "decision": decision,
            "tool_results": tool_results,
            "escalation": escalation_result,
            "police_report": None,
            "telemetry": getattr(cli, "last_usage", {}),
            "simulated": getattr(cli, "last_simulated", not getattr(cli, "live_mode", False)),
            "analysis_source": getattr(cli, "last_source", "simulated" if not getattr(cli, "live_mode", False) else "grok_4.7"),
            "active_trip": mem.get_active_trip(session_id),
        }
