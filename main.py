import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from src.agent.sentinel import SentinelAgent
from src.config import is_configured, GROK_MODEL, RETO_BASE_URL

console = Console()

def run_scenario_digital_fraud(agent: SentinelAgent):
    console.print("\n[bold yellow]═══ ESCENARIO 1: DETECCIÓN DE FRAUDE DIGITAL (PHISHING / NEQUI) ═══[/bold yellow]")
    scam_message = (
        "BANCOLOMBIA ALERTA: Su cuenta ha sido bloqueada preventivamente por movimientos inusuales. "
        "Para reactivar de inmediato ingrese a http://bancolombia-reactivacion-segura.xyz/login "
        "y confirme sus credenciales en menos de 1 hora para evitar suspensión definitiva."
    )
    console.print(Panel(scam_message, title="📱 Mensaje recibido por el usuario en WhatsApp", border_style="cyan"))
    
    result = agent.process_message(scam_message)
    decision = result["decision"]
    
    table = Table(title="🛡️ Veredicto Autónomo de SentinelGuard", border_style="green")
    table.add_column("Propiedad", style="cyan", no_wrap=True)
    table.add_column("Detalle", style="white")
    table.add_row("Modo", decision.get("mode", ""))
    table.add_row("Nivel de Riesgo", f"[bold red]{decision.get('risk_level', '')}[/bold red]")
    table.add_row("Acción Decidida", decision.get("action", ""))
    table.add_row("Razonamiento Grok", decision.get("reasoning", ""))
    table.add_row("Respuesta al Usuario", f"[green]{decision.get('response_to_user', '')}[/green]")
    if result.get("escalation"):
        table.add_row("Protocolo Escalada", f"[red]{result['escalation']['alert_message']}[/red]")
    console.print(table)

def run_scenario_route_companion(agent: SentinelAgent):
    console.print("\n[bold yellow]═══ ESCENARIO 2: ACOMPAÑAMIENTO FÍSICO EN TAXI / NOCHE ═══[/bold yellow]")
    trip_message = "Voy saliendo de la oficina en un taxi placa WDY-452 hacia mi casa en el norte."
    console.print(Panel(trip_message, title="🎙️ Audio / Mensaje de inicio de viaje", border_style="cyan"))
    
    result = agent.process_message(trip_message, metadata={"plate": "WDY452", "destination": "Calle 142 con 19"})
    decision = result["decision"]
    
    table = Table(title="🛡️ Estado de Acompañamiento Activo", border_style="blue")
    table.add_column("Propiedad", style="cyan", no_wrap=True)
    table.add_column("Detalle", style="white")
    table.add_row("Modo", decision.get("mode", ""))
    table.add_row("Nivel de Riesgo", f"[bold green]{decision.get('risk_level', '')}[/bold green]")
    table.add_row("Acción Decidida", decision.get("action", ""))
    table.add_row("Próximo Check-in", result["tool_results"]["route"]["next_checkin_scheduled"])
    table.add_row("Respuesta al Usuario", f"[green]{decision.get('response_to_user', '')}[/green]")
    console.print(table)

def main():
    console.print(Panel.fit(
        "[bold cyan]🛡️ SENTINELGUARD AI — EQUIPO CODIXIA[/bold cyan]\n"
        "[italic]Reto Agente 2026 · Platica.mx × Campuslands[/italic]\n\n"
        f"• Gateway: [yellow]{RETO_BASE_URL}[/yellow]\n"
        f"• Modelo: [magenta]{GROK_MODEL}[/magenta]\n"
        f"• Estado de LLave: {'[bold green]CONECTADA (pk_...)[/bold green]' if is_configured() else '[bold yellow]MODO DEMO LOCAL (Configura .env con tu pk_...)[/bold yellow]'}",
        border_style="green"
    ))

    agent = SentinelAgent()

    # Ejecución de demostración end-to-end de ambos escenarios
    run_scenario_digital_fraud(agent)
    run_scenario_route_companion(agent)

    console.print("\n[bold green]✓ Demostración completada con éxito. SentinelGuard listo para operar end-to-end.[/bold green]\n")

if __name__ == "__main__":
    main()
