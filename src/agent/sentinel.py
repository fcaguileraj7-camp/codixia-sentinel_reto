import json
from typing import Dict, Any
from src.client import GrokClient
from src.agent.prompts import SENTINEL_SYSTEM_PROMPT
from src.tools.threat_inspector import inspect_threat
from src.tools.url_sandbox import analyze_url
from src.tools.police_reporter import generate_police_report
from src.tools.route_companion import register_trip, evaluate_trip_audio_response
from src.tools.emergency_escalator import escalate_emergency
from src.utils.logger import logger

class SentinelAgent:
    """Orquestador del agente autónomo SentinelGuard AI."""

    def __init__(self):
        self.client = GrokClient()

    def process_message(self, user_input: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ciclo autónomo completo:
        Percibir -> Ejecutar Tools -> Razonar con Grok -> Decidir -> Actuar
        """
        metadata = metadata or {}
        logger.info(f"[cyan]→ Recibiendo entrada de usuario:[/cyan] {user_input[:80]}...")

        tool_results = {}

        # 1. Ejecución resiliente de herramientas según el contexto (Tolerancia a fallos S2)
        if any(term in user_input.lower() for term in ["taxi", "placa", "voy en", "trayecto"]):
            # Modo acompañamiento físico: RouteCompanion
            plate = metadata.get("plate", "ABC123")
            dest = metadata.get("destination", "Destino particular")
            try:
                tool_results["route"] = register_trip(plate=plate, destination=dest)
                logger.info(f"[blue]⚡ Tool ejecutada: register_trip -> {tool_results['route'].get('trip_id')}[/blue]")
            except Exception as e:
                logger.warning(f"[yellow]⚠ Falla en tool register_trip ({e}). Continuando con fallback.[/yellow]")
                tool_results["route"] = {"status": "error", "error": str(e), "monitoring_active": False}
        else:
            # Modo escudo digital: ThreatInspector
            try:
                threat_data = inspect_threat(user_input)
                tool_results["threat"] = threat_data
                logger.info(f"[blue]⚡ Tool ejecutada: inspect_threat -> Nivel {threat_data.get('threat_level')}[/blue]")
            except Exception as e:
                logger.warning(f"[yellow]⚠ Falla en tool inspect_threat ({e}). Continuando con fallback.[/yellow]")
                threat_data = {"status": "error", "threat_level": "MEDIO", "detected_urls": [], "error": str(e)}
                tool_results["threat"] = threat_data

            # Inspección profunda de URLs si fueron detectadas: UrlSandbox
            urls = threat_data.get("detected_urls", [])
            if urls:
                sandbox_results = []
                for u in urls:
                    try:
                        sandbox_results.append(analyze_url(u))
                    except Exception as e:
                        logger.warning(f"[yellow]⚠ Falla en sandbox para URL {u}: {e}[/yellow]")
                        sandbox_results.append({"status": "error", "original_url": u, "verdict": "SOSPECHOSO", "error": str(e)})
                tool_results["url_sandbox"] = sandbox_results
                logger.info(f"[blue]⚡ Tool ejecutada: url_sandbox -> {len(sandbox_results)} enlaces analizados[/blue]")

        # 2. Construcción del contexto para el razonamiento de Grok
        context_prompt = (
            f"Entrada del usuario:\n\"{user_input}\"\n\n"
            f"Metadatos y resultados de herramientas:\n{json.dumps(tool_results, ensure_ascii=False, indent=2)}\n\n"
            f"Analiza la situación y decide el plan de acción en formato JSON."
        )

        messages = [
            {"role": "system", "content": SENTINEL_SYSTEM_PROMPT},
            {"role": "user", "content": context_prompt}
        ]

        # 3. Razonamiento en Grok
        logger.info("[magenta]🧠 Consultando núcleo de razonamiento Grok 4.7...[/magenta]")
        raw_response = self.client.chat_completion(messages)

        # 4. Parseo y Validación de la decisión
        try:
            json_start = raw_response.find("{")
            json_end = raw_response.rfind("}") + 1
            if json_start != -1 and json_end != -1:
                decision = json.loads(raw_response[json_start:json_end])
            else:
                decision = json.loads(raw_response)
        except Exception as e:
            logger.warning(f"[yellow]Advertencia al parsear JSON de Grok: {e}. Usando fallback.[/yellow]")
            decision = {
                "mode": "threat_inspection",
                "risk_level": "MEDIO",
                "reasoning": raw_response,
                "action": "ANALYZE_ONLY",
                "response_to_user": raw_response
            }

        # 5. Ejecución autónoma de escalada si el riesgo es CRÍTICO o ALTO
        escalation_result = None
        police_report = None
        if decision.get("risk_level") in ["ALTO", "CRÍTICO"] or decision.get("action") == "TRIGGER_ALARM":
            logger.warning(f"[red]🚨 Activando protocolo de escalada: Riesgo {decision.get('risk_level')}[/red]")
            incident_type = "PHYSICAL_RISK" if decision.get("mode") == "route_companion" else "DIGITAL_FRAUD"
            
            # Escalada SOS general
            try:
                escalation_result = escalate_emergency(
                    incident_type=incident_type,
                    evidence_payload={"input": user_input, "decision": decision, "tools": tool_results}
                )
            except Exception as e:
                logger.warning(f"[yellow]⚠ Falla en escalate_emergency ({e})[/yellow]")
                escalation_result = {"status": "error", "error": str(e)}

            # Generación de expediente para CAI Virtual
            if incident_type == "DIGITAL_FRAUD":
                try:
                    police_report = generate_police_report({
                        "sender_phone": metadata.get("sender", "Desconocido"),
                        "incident_type": "Tentativa de Estafa / Phishing",
                        "user_input": user_input,
                        "risk_level": decision.get("risk_level", "ALTO"),
                        "findings": tool_results.get("threat", {}).get("findings", []),
                        "detected_urls": tool_results.get("threat", {}).get("detected_urls", [])
                    })
                    logger.info(f"[green]📜 Expediente generado para CAI Virtual: {police_report.get('report_id')}[/green]")
                except Exception as e:
                    logger.warning(f"[yellow]⚠ Falla en generate_police_report ({e})[/yellow]")
                    police_report = {"status": "error", "error": str(e)}

        return {
            "status": "success",
            "decision": decision,
            "tool_results": tool_results,
            "escalation": escalation_result,
            "police_report": police_report,
            "telemetry": getattr(self.client, "last_usage", {})
        }
