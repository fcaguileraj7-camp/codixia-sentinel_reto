import json
from openai import OpenAI
from src.config import RETO_API_KEY, RETO_BASE_URL, GROK_MODEL, is_configured
from src.utils.logger import logger

class GrokClient:
    """Cliente para la API de Grok con monitoreo de tokens, cálculo de costos y fallback local."""

    def __init__(self):
        self.configured = is_configured()
        if self.configured:
            self.client = OpenAI(
                base_url=RETO_BASE_URL,
                api_key=RETO_API_KEY,
            )
            logger.info(f"[green]✓ Cliente de Grok conectado a:[/green] {RETO_BASE_URL}")
        else:
            self.client = None
            logger.warning("[yellow]⚠ RETO_API_KEY no configurada en .env. Operando en MODO SIMULACIÓN LOCAL.[/yellow]")

    def chat_completion(
        self,
        messages: list[dict],
        model: str = GROK_MODEL,
        temperature: float = 0.2,
        max_tokens: int = 500
    ) -> str:
        """
        Ejecuta solicitud a Grok controlando el consumo de tokens.
        - max_tokens: 500 por defecto para evitar respuestas verbosas y proteger el saldo.
        - Calcula y registra el consumo de tokens y el costo en USD (Hito S3).
        """
        if self.configured and self.client:
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
                    # Costos base aproximados xAI (~$2/M input, ~$10/M output)
                    estimated_cost = (p_tokens * 0.000002) + (c_tokens * 0.000010)
                    logger.info(
                        f"[dim cyan]📊 Consumo de Tokens: {t_tokens} (Prompt: {p_tokens}, Completions: {c_tokens}) | "
                        f"Costo estimado: ${estimated_cost:.5f} USD[/dim cyan]"
                    )
                
                return response.choices[0].message.content or ""
            except Exception as e:
                logger.warning(f"[yellow]⚠ Falla o créditos pendientes en API de Grok ({e}). Activando fallback local resiliente.[/yellow]")

        # Fallback de simulación determinista para pruebas locales (Gasto $0.00 USD)
        last_message = messages[-1].get("content", "")
        if "taxi" in last_message.lower() or "trayecto" in last_message.lower():
            return json.dumps({
                "mode": "route_companion",
                "risk_level": "BAJO",
                "reasoning": "El usuario inicia trayecto en taxi. Se activan temporizadores de check-in preventivo a 10 minutos.",
                "action": "SCHEDULE_CHECKIN",
                "response_to_user": "Acompañamiento iniciado para el vehículo. Tu ruta y placa quedan registradas. Te escribiré en 10 minutos para confirmar que todo va bien."
            }, ensure_ascii=False)
        elif any(w in last_message.lower() for w in ["bloqueada", "bancolombia", "nequi", "urgente", "alerta", "pague", "frente urbano"]):
            return json.dumps({
                "mode": "threat_inspection",
                "risk_level": "CRÍTICO",
                "reasoning": "Mensaje típico de ingeniería social que simula bloqueo de cuenta o extorsión con urgencia artificial y/o enlace malicioso.",
                "action": "BLOCK_AND_REPORT",
                "response_to_user": "🚨 ALERTA ROJA: Este mensaje es un intento evidente de Fraude/Extorsión. No abras enlaces ni consignes dinero. Hemos generado un radicado preventivo para el CAI Virtual."
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "mode": "threat_inspection",
                "risk_level": "BAJO",
                "reasoning": "Conversación cotidiana sin patrones identificables de fraude financiero o manipulación.",
                "action": "INFORMATIVE_ONLY",
                "response_to_user": "No se detectaron indicios de amenaza o estafa en este mensaje. Si recibes solicitudes de dinero o códigos inesperados, reenvíamelos."
            }, ensure_ascii=False)
