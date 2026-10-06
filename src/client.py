import json
from openai import OpenAI
from src.config import RETO_API_KEY, RETO_BASE_URL, GROK_MODEL, is_configured
from src.utils.logger import logger

class GrokClient:
    """Cliente para la API de Grok a través del gateway de Platica.mx / Reto Agente."""

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

    def chat_completion(self, messages: list[dict], model: str = GROK_MODEL, temperature: float = 0.2) -> str:
        """Ejecuta una solicitud de chat completions contra Grok o usa fallback en modo demo."""
        if self.configured and self.client:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                logger.error(f"[red]Error al conectar con la API de Grok: {e}[/red]")
                raise e

        # Fallback de simulación determinista para pruebas previas a la entrega de la llave
        last_message = messages[-1].get("content", "")
        if "taxi" in last_message.lower() or "trayecto" in last_message.lower():
            return json.dumps({
                "mode": "route_companion",
                "risk_level": "BAJO",
                "reasoning": "El usuario inicia trayecto en taxi. Se activan temporizadores de check-in preventivo a 10 minutos.",
                "action": "SCHEDULE_CHECKIN",
                "response_to_user": "Acompañamiento iniciado para el vehículo. Tu ruta y placa quedan registradas. Te escribiré en 10 minutos para confirmar que todo va bien."
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "mode": "threat_inspection",
                "risk_level": "ALTO",
                "reasoning": "Mensaje típico de ingeniería social que simula bloqueo de cuenta bancaria con urgencia artificial y enlace no oficial.",
                "action": "BLOCK_AND_REPORT",
                "response_to_user": "⚠️ ALERTA ROJA: Este mensaje es un intento de Phishing/Estafa. El enlace NO pertenece a la entidad financiera oficial. No abras el enlace ni entregues tus claves."
            }, ensure_ascii=False)
