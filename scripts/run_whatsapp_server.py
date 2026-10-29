"""
Script para levantar el Servidor Webhook de WhatsApp de SentinelGuard AI
Reto Agente 2026 - Platica.mx × Campuslands

Uso:
  python scripts/run_whatsapp_server.py [--port 8000] [--host 0.0.0.0]
"""

import sys
from pathlib import Path

# Asegurar que la raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import uvicorn
from src.utils.logger import logger
from src.config import WHATSAPP_VERIFY_TOKEN, is_whatsapp_configured

def main():
    parser = argparse.ArgumentParser(description="SentinelGuard AI · Servidor Webhook WhatsApp")
    parser.add_argument("--port", type=int, default=8000, help="Puerto de escucha (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host de escucha (default: 0.0.0.0)")
    args = parser.parse_args()

    logger.info("[bold cyan]══════════════════════════════════════════════════════[/bold cyan]")
    logger.info("[bold cyan]  🛡️  SENTINELGUARD AI — SERVIDOR WEBHOOK WHATSAPP  [/bold cyan]")
    logger.info("[bold cyan]══════════════════════════════════════════════════════[/bold cyan]")
    logger.info(f"[green]✓ Escuchando en:[/green] http://{args.host}:{args.port}")
    logger.info(f"[green]✓ Token de verificación Webhook:[/green] {WHATSAPP_VERIFY_TOKEN}")
    if is_whatsapp_configured():
        logger.info("[green]✓ Credenciales de Meta Cloud API: CONFIGURADAS (Envíos reales)[/green]")
    else:
        logger.info("[yellow]🛡️ Modo Simulado Local ACTIVO ($0.00 USD). Respuestas registradas en logs.[/yellow]")

    logger.info("\n[dim]Para exponer tu servidor a internet y conectarlo a Meta:[/dim]")
    logger.info(f"[bold white]  ngrok http {args.port}[/bold white]\n")

    uvicorn.run("src.interfaces.whatsapp:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    main()
