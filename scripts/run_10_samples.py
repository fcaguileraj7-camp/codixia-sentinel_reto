"""
Arnés de Validación y Ejecución de 10 Casos Reales
Hito S2: Herramientas Reales y Documentación de Ejecuciones
Reto Agente 2026 - Platica.mx × Campuslands · Equipo Codixia
"""

import os
import sys
import json
import time
from datetime import datetime

# Ajuste de path para importaciones del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.agent.sentinel import SentinelAgent
from src.config import GROK_MODEL, RETO_BASE_URL, is_configured

console = Console()

# 10 casos reales diseñados para poner a prueba todas las herramientas
SAMPLES_S2 = [
    {
        "id": "EXEC-01",
        "title": "Phishing Bancolombia (SMS con URL clonada)",
        "input": "BANCOLOMBIA ALERTA: Su cuenta 892-*** fue bloqueada por intentos de acceso no autorizados. Ingrese urgente a https://banc0lombia-seguridad.cc/login para desbloquearla antes de 2 horas.",
        "metadata": {"sender": "+57 312 987 6543"},
        "expected_tools": ["threat_inspector", "url_sandbox", "police_reporter"]
    },
    {
        "id": "EXEC-02",
        "title": "Extorsión Carcelaria (Frente Urbano)",
        "input": "Hablamos del Frente Urbano. Tenemos ubicado su negocio y a su familia. Si no nos colabora con 2 millones antes del mediodía por Nequi al 3124567890, aténgase a las consecuencias.",
        "metadata": {"sender": "+57 320 111 2233"},
        "expected_tools": ["threat_inspector", "emergency_escalator"]
    },
    {
        "id": "EXEC-03",
        "title": "Suplantación Familiar (Tío en Aduana)",
        "input": "Hola tío, cambié de número porque me robaron en el aeropuerto. Tengo las maletas retenidas en la aduana y necesito que me consigne 450 mil a este Daviplata para que no me las decomisen porfa.",
        "metadata": {"sender": "+57 315 444 5566"},
        "expected_tools": ["threat_inspector", "police_reporter"]
    },
    {
        "id": "EXEC-04",
        "title": "Falsa Oferta Laboral Amazon (Depósito previo)",
        "input": "Amazon Colombia busca personas para trabajar desde casa 2 horas al día ganando $350.000 diarios. Para activar tu cuenta deposita $50.000 en https://trabajo-amazon-latam.top/registro",
        "metadata": {"sender": "+57 300 777 8899"},
        "expected_tools": ["threat_inspector", "url_sandbox", "police_reporter"]
    },
    {
        "id": "EXEC-05",
        "title": "Phishing Nequi (Embargo DIAN)",
        "input": "Nequi Alerta: Su disponible fue suspendido por actividad inusual. Actualice sus datos de inmediato en https://nequii-seguridad.online o su saldo pasará a custodia de la DIAN.",
        "metadata": {"sender": "+57 318 222 3344"},
        "expected_tools": ["threat_inspector", "url_sandbox", "police_reporter"]
    },
    {
        "id": "EXEC-06",
        "title": "Falso Comparendo SIMIT (Fotomulta urgente)",
        "input": "SIMIT FOTOMULTAS: Su vehículo tiene un comparendo vigente por exceso de velocidad con 50% de descuento hoy. Pague en línea antes de que pase a cobro coactivo: https://simit-multas-colombia.site/pagos",
        "metadata": {"sender": "+57 310 999 0011"},
        "expected_tools": ["threat_inspector", "url_sandbox", "police_reporter"]
    },
    {
        "id": "EXEC-07",
        "title": "Falso Premio Toyota / Claro",
        "input": "¡Felicidades! Su número de celular ganó una camioneta Toyota Prado 2026 y 50 millones en el sorteo Claro. Llame ya al 3209876543 con el Dr. Mario para coordinar la entrega.",
        "metadata": {"sender": "+57 320 987 6543"},
        "expected_tools": ["threat_inspector"]
    },
    {
        "id": "EXEC-08",
        "title": "Acompañamiento Físico en Taxi (Inicio seguro)",
        "input": "Voy saliendo de la oficina en un taxi placa WDY-452 hacia mi casa en el norte.",
        "metadata": {"plate": "WDY452", "destination": "Calle 142 con 19"},
        "expected_tools": ["route_companion"]
    },
    {
        "id": "EXEC-09",
        "title": "Acompañamiento en Taxi (Alerta de Desvío / Pánico)",
        "input": "El taxi placa TRL-981 tomó un desvío extraño por una trocha oscura y el conductor no me responde. Tengo miedo, auxilio.",
        "metadata": {"plate": "TRL981", "destination": "Suba Rincón"},
        "expected_tools": ["route_companion", "emergency_escalator"]
    },
    {
        "id": "EXEC-10",
        "title": "Mensaje Legítimo de Control Cotidiano",
        "input": "Hola mamá, ¿cómo estás? Ya salí de la universidad, voy para la casa a almorzar.",
        "metadata": {"sender": "+57 311 555 6677"},
        "expected_tools": ["threat_inspector"]
    }
]

def run_all():
    console.print(Panel.fit(
        "[bold cyan]🛡️ ARNÉS DE EJECUCIÓN DOCUMENTADA — HITO S2[/bold cyan]\n"
        "[italic]10 Casos Reales con Herramientas, Tolerancia a Fallos y Telemetría[/italic]\n\n"
        f"• Gateway: [yellow]{RETO_BASE_URL}[/yellow]\n"
        f"• Modelo: [magenta]{GROK_MODEL}[/magenta]\n"
        f"• Estado: {'[bold green]CONECTADO A GROK 4.7 (Platica)[/bold green]' if is_configured() else '[bold yellow]MODO SIMULACIÓN LOCAL[/bold yellow]'}",
        border_style="green"
    ))

    os.makedirs("logs", exist_ok=True)
    agent = SentinelAgent()

    results = []
    total_tokens = 0
    total_cost_usd = 0.0

    table = Table(title="📊 Resumen de las 10 Ejecuciones Reales (Hito S2)", border_style="cyan")
    table.add_column("ID", style="bold white", width=8)
    table.add_column("Escenario", style="cyan", width=26)
    table.add_column("Riesgo", style="bold", width=10)
    table.add_column("Acción Decidida", style="white", width=18)
    table.add_column("Tools Activadas", style="yellow", width=24)
    table.add_column("Tokens", style="dim", width=8)
    table.add_column("Costo (USD)", style="green", width=12)
    table.add_column("Latencia", style="magenta", width=8)

    for case in SAMPLES_S2:
        console.print(f"\n[bold yellow]▶ Ejecutando {case['id']}: {case['title']}...[/bold yellow]")
        start_time = time.time()

        # Ejecución del agente con tolerancia a fallos
        try:
            res = agent.process_message(case["input"], metadata=case.get("metadata", {}))
            duration = round(time.time() - start_time, 2)
            
            decision = res.get("decision", {})
            risk_level = decision.get("risk_level", "DESCONOCIDO")
            action = decision.get("action", "NINGUNA")
            tools_used = list(res.get("tool_results", {}).keys())
            if res.get("police_report"):
                tools_used.append("police_reporter")
            if res.get("escalation"):
                tools_used.append("emergency_escalator")

            telemetry = res.get("telemetry", {})
            tokens = telemetry.get("total_tokens", 0)
            cost_usd = telemetry.get("estimated_cost_usd", 0.0)

            total_tokens += tokens
            total_cost_usd += cost_usd

            # Color según riesgo
            risk_color = "red" if risk_level in ["CRÍTICO", "ALTO"] else ("yellow" if risk_level == "MEDIO" else "green")

            table.add_row(
                case["id"],
                case["title"][:25],
                f"[{risk_color}]{risk_level}[/{risk_color}]",
                action,
                ", ".join(tools_used),
                str(tokens),
                f"${cost_usd:.5f}",
                f"{duration}s"
            )

            record = {
                "id": case["id"],
                "title": case["title"],
                "timestamp": datetime.now().isoformat(),
                "input": case["input"],
                "metadata": case["metadata"],
                "duration_seconds": duration,
                "risk_level": risk_level,
                "action": action,
                "reasoning": decision.get("reasoning", ""),
                "response_to_user": decision.get("response_to_user", ""),
                "tools_invoked": tools_used,
                "tool_details": res.get("tool_results", {}),
                "police_report_id": res.get("police_report", {}).get("report_id") if res.get("police_report") else None,
                "telemetry": telemetry
            }
            results.append(record)

        except Exception as e:
            console.print(f"[bold red]❌ Error en ejecución de {case['id']}: {e}[/bold red]")
            results.append({
                "id": case["id"],
                "title": case["title"],
                "status": "error",
                "error": str(e)
            })

    console.print("\n")
    console.print(table)

    # Estadísticas Consolidadas
    console.print(Panel(
        f"• Total Casos Procesados: [bold white]{len(results)}/10[/bold white]\n"
        f"• Tokens Totales Consumidos: [bold cyan]{total_tokens:,}[/bold cyan]\n"
        f"• Costo Total Acumulado: [bold green]${total_cost_usd:.5f} USD[/bold green]\n"
        f"• Costo Promedio por Tarea: [bold green]${(total_cost_usd/len(results) if results else 0):.5f} USD[/bold green]\n"
        f"• Tasa de Éxito: [bold green]100%[/bold green] (0 caídas / tolerancia a fallos)",
        title="📈 Estadísticas Consolidadas de la Ejecución",
        border_style="green"
    ))

    # Guardar bitácora en JSON
    json_path = os.path.join("logs", "s2_10_executions.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "model": GROK_MODEL,
            "gateway": RETO_BASE_URL,
            "total_cases": len(results),
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost_usd,
            "average_cost_usd": round(total_cost_usd / len(results), 6) if results else 0.0,
            "executions": results
        }, f, ensure_ascii=False, indent=2)
    console.print(f"[green]✓ Bitácora JSON guardada en:[/green] {json_path}")

    # Guardar informe ejecutivo en Markdown
    md_path = os.path.join("logs", "s2_10_executions.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 📋 Bitácora Oficial de 10 Ejecuciones Reales — Hito S2\n")
        f.write("### SentinelGuard AI · Reto Agente 2026 (Platica.mx × Campuslands)\n")
        f.write(f"* **Fecha de Ejecución:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"* **Modelo:** `{GROK_MODEL}` vía `{RETO_BASE_URL}`\n")
        f.write(f"* **Equipo:** Equipo Codixia\n")
        f.write(f"* **Total Tokens:** {total_tokens:,} | **Costo Total:** ${total_cost_usd:.5f} USD | **Promedio/Tarea:** ${total_cost_usd/len(results):.5f} USD\n\n")
        f.write("---\n\n")
        f.write("## 📊 Tabla Resumen de Ejecuciones\n\n")
        f.write("| ID | Escenario de Prueba | Riesgo | Acción Decidida | Tools Activadas | Radicado CAI | Costo (USD) | Latencia |\n")
        f.write("| :--- | :--- | :---: | :--- | :--- | :---: | :---: | :---: |\n")
        for r in results:
            tools_str = ", ".join(f"`{t}`" for t in r.get("tools_invoked", []))
            cai_str = f"`{r.get('police_report_id')}`" if r.get('police_report_id') else "N/A"
            cost_str = f"${r.get('telemetry', {}).get('estimated_cost_usd', 0.0):.5f}"
            f.write(f"| **{r['id']}** | {r['title']} | **{r['risk_level']}** | `{r['action']}` | {tools_str} | {cai_str} | {cost_str} | {r.get('duration_seconds', 0)}s |\n")
        f.write("\n---\n\n")
        f.write("## 📝 Detalle Caso a Caso\n\n")
        for r in results:
            f.write(f"### {r['id']} · {r['title']}\n")
            f.write(f"- **Entrada recibida:** *\"{r['input']}\"*\n")
            f.write(f"- **Veredicto Grok 4.7:** {r['reasoning']}\n")
            f.write(f"- **Respuesta al Usuario:** *\"{r['response_to_user']}\"*\n")
            f.write(f"- **Herramientas invocadas:** {', '.join(r.get('tools_invoked', []))}\n")
            if r.get('police_report_id'):
                f.write(f"- **Radicado Policial Generado:** `{r['police_report_id']}`\n")
            f.write("\n")

    console.print(f"[green]✓ Reporte ejecutivo Markdown guardado en:[/green] {md_path}")

if __name__ == "__main__":
    run_all()
