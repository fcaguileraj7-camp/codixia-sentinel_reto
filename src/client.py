import time
import json
from openai import OpenAI
from src.config import RETO_API_KEY, RETO_BASE_URL, GROK_MODEL, is_configured, is_live_mode_enabled
from src.utils.logger import logger

INPUT_TOKEN_RATE_USD = 0.000002
OUTPUT_TOKEN_RATE_USD = 0.000010


class GrokClient:
    """
    Cliente para la API de Grok con monitoreo de tokens, cálculo de costos y fallback local.
    
    Blindaje de Presupuesto (Requisito Hito 2 y Hito 3):
    Por defecto opera en modo de simulación local ($0.00 USD), impidiendo cualquier
    solicitud HTTP externa involuntaria aunque exista una llave válida en .env.
    Para activar llamadas reales a la API de Grok, se debe solicitar explícitamente con:
    - use_real_api=True en la instanciación, o
    - GROK_MODE='live' en variables de entorno (fuera de pytest).
    """

    def __init__(self, use_real_api: bool = False, simulated_response: str = None):
        self.simulated_response = simulated_response
        self.configured = is_configured()
        # Determinar si se debe activar el cliente HTTP real
        self.live_mode = False
        if use_real_api:
            if self.configured:
                self.live_mode = True
            else:
                logger.warning("[yellow]⚠ Se solicitó use_real_api=True pero RETO_API_KEY no está configurada. Fallback a modo simulado.[/yellow]")
        elif is_live_mode_enabled():
            self.live_mode = True

        self.last_source = "grok_4.7" if self.live_mode else "simulated"
        self.last_simulated = not self.live_mode

        if self.live_mode:
            self.client = OpenAI(
                base_url=RETO_BASE_URL,
                api_key=RETO_API_KEY,
            )
            logger.info(f"[green]✓ Cliente de Grok en MODO REAL conectado a:[/green] {RETO_BASE_URL}")
        else:
            self.client = None
            logger.info("[cyan]🛡️ Modo de Simulación Local ACTIVO ($0.00 USD). Llamadas externas deshabilitadas.[/cyan]")

    def chat_completion(
        self,
        messages: list[dict],
        model: str = GROK_MODEL,
        temperature: float = 0.2,
        max_tokens: int = 500
    ) -> str:
        """
        Ejecuta solicitud a Grok controlando el consumo de tokens.
        - En modo simulado (por defecto): no realiza llamadas HTTP y devuelve respuestas locales deterministas.
        - En modo real: ejecuta la llamada con control de max_tokens y telemetría de costos.
        """
        # Si se inyectó una respuesta simulada para pruebas
        if self.simulated_response is not None:
            self.last_source = "simulated"
            self.last_simulated = True
            self.last_usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "provider_total_tokens": None,
                "total_tokens_source": None,
                "usage_consistent": None,
                "estimated_cost_usd": 0.0,
                "mode": "simulated_injection",
                "usage_available": False,
                "execution_status": "simulated",
                "requested_model": model,
                "provider_model": None,
                "provider_response_id": None,
            }
            return self.simulated_response

        provider_error_type = None
        # Modo Real (solo si fue activado explícitamente)
        if self.live_mode and self.client:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                
                    usage = getattr(response, "usage", None)
                    prompt_tokens = getattr(usage, "prompt_tokens", None)
                    completion_tokens = getattr(usage, "completion_tokens", None)
                    provider_total_tokens = getattr(usage, "total_tokens", None)
                    has_token_counts = all(
                        isinstance(value, int) and not isinstance(value, bool) and value >= 0
                        for value in (prompt_tokens, completion_tokens)
                    )
                    has_provider_total = (
                        isinstance(provider_total_tokens, int)
                        and not isinstance(provider_total_tokens, bool)
                        and provider_total_tokens >= 0
                    )
    
                    if has_token_counts:
                        total_tokens = (
                            provider_total_tokens
                            if has_provider_total
                            else prompt_tokens + completion_tokens
                        )
                        estimated_cost = (
                            prompt_tokens * INPUT_TOKEN_RATE_USD
                            + completion_tokens * OUTPUT_TOKEN_RATE_USD
                        )
                        usage_consistent = (
                            provider_total_tokens == prompt_tokens + completion_tokens
                            if has_provider_total
                            else None
                        )
                        logger.info(
                            f"[dim cyan]📊 Consumo de Tokens: {total_tokens} (Prompt: {prompt_tokens}, Completions: {completion_tokens}) | "
                            f"Costo estimado: ${estimated_cost:.5f} USD[/dim cyan]"
                        )
                    else:
                        total_tokens = None
                        estimated_cost = None
                        usage_consistent = None
    
                    usage_available = usage is not None and has_token_counts
                    self.last_usage = {
                        "prompt_tokens": prompt_tokens if has_token_counts else None,
                        "completion_tokens": completion_tokens if has_token_counts else None,
                        "total_tokens": total_tokens,
                        "provider_total_tokens": provider_total_tokens if has_provider_total else None,
                        "total_tokens_source": (
                            "provider" if has_provider_total
                            else "sum_of_prompt_and_completion" if has_token_counts
                            else None
                        ),
                        "usage_consistent": usage_consistent,
                        "usage_available": usage_available,
                        "estimated_cost_usd": round(estimated_cost, 6) if estimated_cost is not None else None,
                        "pricing_basis": (
                            "hard-coded rates; verify against provider tariff for execution date"
                            if usage_available
                            else None
                        ),
                        "input_token_rate_usd": INPUT_TOKEN_RATE_USD if usage_available else None,
                        "output_token_rate_usd": OUTPUT_TOKEN_RATE_USD if usage_available else None,
                        "mode": "live_api",
                        "execution_status": (
                            "provider_success" if usage_available else "provider_usage_missing_or_invalid"
                        ),
                        "requested_model": model,
                        "provider_model": getattr(response, "model", None),
                        "provider_response_id": getattr(response, "id", None),
                    }
                    
                    self.last_source = "grok_4.7"
                    self.last_simulated = False
                    return response.choices[0].message.content or ""
                except Exception as e:
                    provider_error_type = type(e).__name__
                    err_str = str(e)
                    if any(code in err_str for code in ["503", "capacity_unavailable", "429", "rate_limit"]) and attempt < max_retries - 1:
                        sleep_s = (attempt + 1) * 3
                        logger.warning(f"[yellow]⚠ Capacidad temporalmente ocupada en pasarela ({e}). Reintentando en {sleep_s}s (intento {attempt+1}/{max_retries})...[/yellow]")
                        time.sleep(sleep_s)
                        continue
                    logger.warning(f"[yellow]⚠ Falla en API de Grok ({e}). Activando fallback local resiliente.[/yellow]")
                    break

        # Fallback de simulación determinista para pruebas locales (Gasto $0.00 USD)
        self.last_source = "simulated"
        self.last_simulated = True
        provider_failed = provider_error_type is not None
        self.last_usage = {
            "prompt_tokens": None if provider_failed else 0,
            "completion_tokens": None if provider_failed else 0,
            "total_tokens": None if provider_failed else 0,
            "provider_total_tokens": None,
            "total_tokens_source": None,
            "usage_consistent": None,
            "estimated_cost_usd": None if provider_failed else 0.0,
            "mode": "simulated_after_provider_error" if provider_failed else "simulated_local",
            "usage_available": False,
            "execution_status": "simulated_fallback_after_provider_error" if provider_failed else "simulated",
            "fallback_reason": "provider_error" if provider_failed else None,
            "provider_error_type": provider_error_type,
            "requested_model": model,
            "provider_model": None,
            "provider_response_id": None,
        }
        last_message = messages[-1].get("content", "")
        # Si el prompt está estructurado con delimitadores de auditoría, inspeccionar solo el texto sospechoso
        audit_text = last_message
        if "--- TEXTO SOSPECHOSO A AUDITAR ---" in last_message and "--- FIN DEL TEXTO SOSPECHOSO ---" in last_message:
            try:
                start = last_message.find("--- TEXTO SOSPECHOSO A AUDITAR ---") + len("--- TEXTO SOSPECHOSO A AUDITAR ---")
                end = last_message.find("--- FIN DEL TEXTO SOSPECHOSO ---")
                audit_text = last_message[start:end]
            except Exception:
                audit_text = last_message

        audit_lower = audit_text.lower()
        last_message_lower = last_message.lower()

        # Detección de pánico o desvío crítico en taxi (Escenario Físico Multi-Turno)
        is_route_context = "SOLICITUD DE ACOMPAÑAMIENTO FÍSICO EN RUTA:" in last_message
        has_route_panic = (
            any(w in audit_lower for w in [
                "desvio", "desvió", "panico", "pánico", "trocha", "miedo",
                "no para", "no frena", "auxilio", "peligro", "ayuda", "socorro",
                "secuestr", "arma", "emergencia"
            ])
            or '"status": "alert"' in last_message
            or '"escalation_required": true' in last_message.lower()
            or '"event": "panic_reported"' in last_message.lower()
        )
        if has_route_panic and (is_route_context or any(w in audit_lower for w in ["desvio", "desvió", "panico", "pánico", "trocha", "miedo", "no para", "no frena", "auxilio", "peligro"])):
            return json.dumps({
                "mode": "route_companion",
                "risk_level": "CRÍTICO",
                "risk_score": 100,
                "threat_level": "CRÍTICO",
                "reasoning": "El usuario reporta situación de peligro, coacción o desvío anómalo en su ruta de transporte. Se activa alarma SOS y protocolo de escalada inmediata.",
                "action": "TRIGGER_ALARM",
                "response_to_user": "🚨 ALERTA DE EMERGENCIA ACTIVADA: Hemos detectado una situación de riesgo crítico en tu trayecto. Notificando de inmediato a tus contactos de emergencia y cuerpos de seguridad con la matrícula del vehículo."
            }, ensure_ascii=False)
        elif is_route_context and ('"status": "checkin_pending"' in last_message or '"event": "checkin_pending"' in last_message.lower()):
            return json.dumps({
                "mode": "route_companion",
                "risk_level": "MEDIO",
                "risk_score": 50,
                "threat_level": "MEDIO",
                "reasoning": "Respuesta de check-in recibida pero no coincide con la palabra de seguridad esperada. Se requiere verificación preventiva.",
                "action": "REQUEST_CONFIRMATION",
                "response_to_user": "⚠️ Alerta preventiva: Tu respuesta no confirmó la palabra clave de seguridad esperada. Por favor confírmanos si te encuentras seguro en el trayecto."
            }, ensure_ascii=False)
        elif is_route_context or "taxi" in audit_lower or "trayecto" in audit_lower:
            return json.dumps({
                "mode": "route_companion",
                "risk_level": "BAJO",
                "risk_score": 0,
                "threat_level": "BAJO",
                "reasoning": "El usuario inicia o continúa trayecto en taxi. Se activan temporizadores de check-in preventivo a 10 minutos.",
                "action": "SCHEDULE_CHECKIN",
                "response_to_user": "Acompañamiento iniciado para el vehículo. Tu ruta y placa quedan registradas. Te escribiré en 10 minutos para confirmar que todo va bien."
            }, ensure_ascii=False)
        # Seguimiento multi-turno a fraude previo
        elif ("alerta previa en curso" in last_message_lower or "riesgo crítico" in last_message_lower) and any(w in audit_lower for w in ["debo", "hago", "respondo", "llaman", "consigno", "codigo", "código", "clave", "consignar", "responder", "número", "numero"]):
            return json.dumps({
                "mode": "threat_inspection",
                "risk_level": "CRÍTICO",
                "reasoning": "Seguimiento a incidente de ingeniería social previamente alertado. El usuario consulta si debe interactuar, responder o entregar credenciales al atacante.",
                "action": "BLOCK_AND_REPORT",
                "response_to_user": "🚨 Recordatorio de seguridad sobre el fraude reportado: Bajo ninguna circunstancia respondas ni compartas datos, códigos o consignaciones. Mantén el bloqueo al remitente."
            }, ensure_ascii=False)
        elif any(w in audit_lower for w in ["bloqueada", "bancolombia", "nequi", "urgente", "alerta", "pague", "frente urbano", "herido", "accidente", "hospital", "secuestr", "simit", "fotomulta", "comparendo", "multa", "infraccion", "infracción"]):
            return json.dumps({
                "mode": "threat_inspection",
                "risk_level": "CRÍTICO",
                "reasoning": "Mensaje típico de ingeniería social que simula bloqueo de cuenta, comparendo de tránsito, extorsión o falsa emergencia médica/familiar con urgencia artificial.",
                "action": "BLOCK_AND_REPORT",
                "response_to_user": "🚨 ALERTA ROJA: El mensaje que recibiste es un intento de fraude / manipulación de ingeniería social. No respondas, no abras enlaces ni consignes dinero. Hemos generado un radicado preventivo para el CAI Virtual."
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "mode": "threat_inspection",
                "risk_level": "BAJO",
                "reasoning": "Conversación cotidiana sin patrones identificables de fraude financiero o manipulación.",
                "action": "INFORMATIVE_ONLY",
                "response_to_user": "Dictamen: No se detectaron indicios de amenaza o estafa en el mensaje recibido. Recuerda no compartir claves ni códigos si te los solicitan más adelante."
            }, ensure_ascii=False)

    def vision_completion(
        self,
        messages: list[dict],
        model: str = GROK_MODEL,
        temperature: float = 0.2,
        max_tokens: int = 500,
    ) -> str:
        """
        Ejecuta solicitud multimodal a Grok Vision controlando el consumo de tokens.
        A diferencia de chat_completion, vision_completion requiere explícitamente modo en vivo;
        en modo simulado o mock se rehúsa a ejecutarse para evitar falsos positivos de red.
        Si la API del proveedor falla, propaga la excepción directamente sin fallback silencioso.
        """
        if not getattr(self, "live_mode", False) or not getattr(self, "client", None):
            raise RuntimeError("El cliente GrokClient requiere modo en vivo explícito para vision_completion.")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Monitoreo de Tokens y Cálculo de Costo
            if hasattr(response, "usage") and response.usage:
                p_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
                c_tokens = getattr(response.usage, "completion_tokens", 0) or 0
                t_tokens = getattr(response.usage, "total_tokens", 0) or (p_tokens + c_tokens)
                estimated_cost = (p_tokens * 0.000002) + (c_tokens * 0.000010)
                self.last_usage = {
                    "prompt_tokens": p_tokens,
                    "completion_tokens": c_tokens,
                    "total_tokens": t_tokens,
                    "estimated_cost_usd": round(estimated_cost, 6),
                    "mode": "live_api"
                }
            else:
                self.last_usage = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost_usd": 0.0,
                    "mode": "live_api"
                }

            self.last_source = "grok_vision"
            self.last_simulated = False
            return response.choices[0].message.content or ""
        except Exception:
            self.last_source = "unavailable"
            self.last_simulated = False
            raise
