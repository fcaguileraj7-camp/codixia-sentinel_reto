"""
Script de Prueba de Conexión Mínima a Grok 4.7
Hito S2: Verificación de Conectividad con Presupuesto Controlado (<50 tokens, ~$0.0001 USD)
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
"""

import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from src.client import GrokClient
from src.config import RETO_BASE_URL, GROK_MODEL, is_configured

console = Console()

def test_minimal_live_connection():
    console.print(Panel.fit(
        "[bold cyan]🔍 PRUEBA DE CONEXIÓN MÍNIMA A GROK 4.7[/bold cyan]\n"
        "[dim]Presupuesto ultralimitado: max_tokens=25 | Costo estimado < $0.0001 USD[/dim]\n\n"
        f"• Gateway: [yellow]{RETO_BASE_URL}[/yellow]\n"
        f"• Modelo: [magenta]{GROK_MODEL}[/magenta]\n"
        f"• Llave configurada: {'[green]Sí (Válida)[/green]' if is_configured() else '[red]No[/red]'}",
        border_style="cyan"
    ))

    if not is_configured():
        console.print("[bold red]❌ RETO_API_KEY no está configurada o es inválida en .env.[/bold red]")
        return False

    console.print("[yellow]⚡ Conectando a la API real de Grok con use_real_api=True...[/yellow]")
    client = GrokClient(use_real_api=True)

    start_time = time.time()
    try:
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Responde únicamente con la palabra: CONECTADO"}],
            max_tokens=25,
            temperature=0.1
        )
        elapsed = round(time.time() - start_time, 2)
        usage = getattr(client, "last_usage", {})
        
        console.print(Panel(
            f"• [bold green]✓ Conexión Exitosa con Grok 4.7[/bold green]\n"
            f"• Respuesta recibida: [bold white]\"{response.strip()}\"[/bold white]\n"
            f"• Latencia: [magenta]{elapsed}s[/magenta]\n"
            f"• Tokens de Prompt: [cyan]{usage.get('prompt_tokens', 0)}[/cyan]\n"
            f"• Tokens de Respuesta: [cyan]{usage.get('completion_tokens', 0)}[/cyan]\n"
            f"• Tokens Totales: [cyan]{usage.get('total_tokens', 0)}[/cyan]\n"
            f"• Costo Incurrido: [bold green]${usage.get('estimated_cost_usd', 0.0):.6f} USD[/bold green]",
            title="🎯 Resultado de Verificación",
            border_style="green"
        ))
        return True
    except Exception as e:
        console.print(f"[bold red]❌ Error al contactar la API de Grok: {e}[/bold red]")
        return False

if __name__ == "__main__":
    test_minimal_live_connection()
