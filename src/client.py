import json
from openai import OpenAI
from src.config import RETO_API_KEY, RETO_BASE_URL, GROK_MODEL, is_configured, is_live_mode_enabled
from src.utils.logger import logger

class GrokClient:
    """
    Cliente para la API de Grok con monitoreo de tokens, cálculo de costos y fallback local.
    
    Blindaje de Presupuesto (Requisito Hito 2):
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
                "estimated_cost_usd": 0.0,
                "mode": "simulated_injection"
            }
            return self.simulated_response

        # Modo Real (solo si fue activado explícitamente)
        if self.live_mode and self.client:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                
                # Monitoreo de Tokens y Cálculo de Costo (Hito S3)
                if hasattr(response, "usage") and response.usage:
                    p_tokens = response.usage.prompt_tokens or 0
                    c_tokens = response.usage.completion_tokens or 0
                    t_tokens = response.usage.total_tokens or (p_tokens + c_tokens)
                    estimated_cost = (p_tokens * 0.000002) + (c_tokens * 0.000010)
                    self.last_usage = {
                        "prompt_tokens": p_tokens,
                        "completion_tokens": c_tokens,
                        "total_tokens": t_tokens,
                        "estimated_cost_usd": round(estimated_cost, 6),
                        "mode": "live_api"
                    }
                    logger.info(
                        f"[dim cyan]📊 Consumo de Tokens: {t_tokens} (Prompt: {p_tokens}, Completions: {c_tokens}) | "
                        f"Costo estimado: ${estimated_cost:.5f} USD[/dim cyan]"
                    )
                else:
                    self.last_usage = {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "estimated_cost_usd": 0.0,
                        "mode": "live_api"
                    }
                
                self.last_source = "grok_4.7"
                self.last_simulated = False
                return response.choices[0].message.content or ""
            except Exception as e:
                logger.warning(f"[yellow]⚠ Falla en API de Grok ({e}). Activando fallback local resiliente.[/yellow]")

        # Fallback de simulación determinista para pruebas locales (Gasto $0.00 USD)
        self.last_source = "simulated"
        self.last_simulated = True
        self.last_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "mode": "simulated_local"
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
        if "taxi" in audit_lower or "trayecto" in audit_lower:
            return json.dumps({
                "mode": "route_companion",
                "risk_level": "BAJO",
                "reasoning": "El usuario inicia trayecto en taxi. Se activan temporizadores de check-in preventivo a 10 minutos.",
                "action": "SCHEDULE_CHECKIN",
                "response_to_user": "Acompañamiento iniciado para el vehículo. Tu ruta y placa quedan registradas. Te escribiré en 10 minutos para confirmar que todo va bien."
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
