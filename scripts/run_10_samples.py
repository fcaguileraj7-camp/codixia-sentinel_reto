"""
Arnés de Validación y Ejecución Documentada de 10 Casos de Prueba
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

# 10 escenarios diseñados para poner a prueba las herramientas.
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
    is_live = is_configured() and os.getenv("GROK_MODE", "mock").lower() in ["live", "real", "production"]
    run_id = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    console.print(Panel.fit(
        "[bold cyan]🛡️ ARNÉS DE EJECUCIÓN DOCUMENTADA — HITO S2[/bold cyan]\n"
        "[italic]10 casos de prueba con herramientas, tolerancia a fallos y telemetría[/italic]\n\n"
        f"• Gateway: [yellow]{RETO_BASE_URL}[/yellow]\n"
        f"• Modelo: [magenta]{GROK_MODEL}[/magenta]\n"
        f"• Modo solicitado: {'[bold green]EN VIVO (la llamada aún debe verificarse por caso)[/bold green]' if is_live else '[bold yellow]SIMULACIÓN LOCAL ($0.00 USD)[/bold yellow]'}",
        border_style="green"
    ))

    os.makedirs("logs", exist_ok=True)
    agent = SentinelAgent(use_real_api=is_live)

    results = []
    total_tokens = 0
    total_cost_usd = 0.0
    verified_usage_cases = 0
    unverifiable_usage_case_ids = []
    successful_agent_cases = 0

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
            if res.get("status") == "success":
                successful_agent_cases += 1
            
            decision = res.get("decision", {})
            risk_level = decision.get("risk_level", "DESCONOCIDO")
            action = decision.get("action", "NINGUNA")
            tools_used = list(res.get("tool_results", {}).keys())
            if res.get("police_report"):
                tools_used.append("police_reporter")
            if res.get("escalation"):
                tools_used.append("emergency_escalator")

            telemetry = res.get("telemetry", {})
            usage_is_verifiable = (
                telemetry.get("mode") == "live_api"
                and telemetry.get("execution_status") == "provider_success"
                and telemetry.get("usage_available") is True
                and telemetry.get("usage_consistent") is not False
                and isinstance(telemetry.get("total_tokens"), int)
                and isinstance(telemetry.get("estimated_cost_usd"), (int, float))
            )
            if usage_is_verifiable:
                tokens = telemetry["total_tokens"]
                cost_usd = telemetry["estimated_cost_usd"]
                total_tokens += tokens
                total_cost_usd += cost_usd
                verified_usage_cases += 1
            else:
                tokens = None
                cost_usd = None
                unverifiable_usage_case_ids.append(case["id"])

            # Color según riesgo
            risk_color = "red" if risk_level in ["CRÍTICO", "ALTO"] else ("yellow" if risk_level == "MEDIO" else "green")

            table.add_row(
                case["id"],
                case["title"][:25],
                f"[{risk_color}]{risk_level}[/{risk_color}]",
                action,
                ", ".join(tools_used),
                str(tokens) if tokens is not None else "N/D",
                f"${cost_usd:.5f}" if cost_usd is not None else "N/D",
                f"{duration}s"
            )

            record = {
                "id": case["id"],
                "title": case["title"],
                "timestamp": datetime.now().isoformat(),
                "status": res.get("status", "unknown"),
                "execution_mode_requested": "live" if is_live else "simulated",
                "simulated": res.get("simulated"),
                "analysis_source": res.get("analysis_source", "unknown"),
                "provider_execution_status": telemetry.get("execution_status", "unknown"),
                "usage_verifiable": usage_is_verifiable,
                "requested_model": GROK_MODEL,
                "provider_model": telemetry.get("provider_model"),
                "provider_response_id": telemetry.get("provider_response_id"),
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
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "execution_mode_requested": "live" if is_live else "simulated",
                "usage_verifiable": False,
                "requested_model": GROK_MODEL,
                "error": str(e)
            })
            unverifiable_usage_case_ids.append(case["id"])

    console.print("\n")
    console.print(table)

    # Estadísticas Consolidadas
    average_verified_cost = (
        total_cost_usd / verified_usage_cases if verified_usage_cases else None
    )
    agent_success_rate = (
        successful_agent_cases / len(results) * 100 if results else 0.0
    )
    verified_cost_display = (
        f"${total_cost_usd:.5f} USD" if verified_usage_cases else "N/D"
    )
    verified_tokens_display = (
        f"{total_tokens:,}" if verified_usage_cases else "N/D"
    )
    console.print(Panel(
        f"• Casos Procesados: [bold white]{len(results)}/10[/bold white]\n"
        f"• Casos con respuesta y uso del proveedor: [bold cyan]{verified_usage_cases}[/bold cyan]\n"
        f"• Casos sin uso verificable: [bold yellow]{len(unverifiable_usage_case_ids)}[/bold yellow]\n"
        f"• Tokens reportados en casos verificables: [bold cyan]{verified_tokens_display}[/bold cyan]\n"
        f"• Costo estimado en casos verificables: [bold green]{verified_cost_display}[/bold green]\n"
        f"• Promedio estimado por caso verificable: [bold green]{f'${average_verified_cost:.5f} USD' if average_verified_cost is not None else 'N/D'}[/bold green]\n"
        f"• Éxito del procesamiento del agente: [bold green]{agent_success_rate:.1f}%[/bold green]",
        title="📈 Estadísticas Consolidadas de la Ejecución",
        border_style="green"
    ))

    # Keep historical execution files intact; every new run gets a unique filename.
    json_path = os.path.join("logs", f"s2_10_executions_{run_id}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "run_id": run_id,
            "execution_mode_requested": "live" if is_live else "simulated",
            "requested_model": GROK_MODEL,
            "gateway": RETO_BASE_URL,
            "total_cases": len(results),
            "successful_agent_cases": successful_agent_cases,
            "verified_usage_cases": verified_usage_cases,
            "unverifiable_usage_case_ids": unverifiable_usage_case_ids,
            "total_tokens_with_verifiable_usage": total_tokens if verified_usage_cases else None,
            "total_estimated_cost_usd_with_verifiable_usage": (
                round(total_cost_usd, 6) if verified_usage_cases else None
            ),
            "average_estimated_cost_usd_per_case_with_verifiable_usage": (
                round(average_verified_cost, 6) if average_verified_cost is not None else None
            ),
            "executions": results
        }, f, ensure_ascii=False, indent=2)
    console.print(f"[green]✓ Bitácora JSON guardada en:[/green] {json_path}")

    # Guardar informe ejecutivo en Markdown
    md_path = os.path.join("logs", f"s2_10_executions_{run_id}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 📋 Bitácora de 10 Ejecuciones Documentadas — Hito S2\n")
        f.write("### SentinelGuard AI · Reto Agente 2026 (Platica.mx × Campuslands)\n")
        f.write(f"* **ID de ejecución:** `{run_id}`\n")
        f.write(f"* **Modo solicitado:** `{'live' if is_live else 'simulated'}`\n")
        f.write(f"* **Fecha de Ejecución:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"* **Modelo solicitado:** `{GROK_MODEL}` vía `{RETO_BASE_URL}`\n")
        f.write(
            "* **Tarifas:** tasas codificadas en el cliente; requieren verificación "
            "contra la tarifa del proveedor para la fecha.\n"
        )
        f.write(f"* **Equipo:** Equipo Codixia\n")
        f.write(f"* **Casos con uso verificable del proveedor:** {verified_usage_cases}/{len(results)}\n")
        f.write(
            f"* **Tokens de esos casos:** {verified_tokens_display} | "
            f"**Costo estimado:** {verified_cost_display}"
        )
        f.write(
            f" | **Promedio por caso verificable:** ${average_verified_cost:.5f} USD\n\n"
            if average_verified_cost is not None
            else " | **Promedio por caso verificable:** N/D\n\n"
        )
        f.write("---\n\n")
        f.write("## 📊 Tabla Resumen de Ejecuciones\n\n")
        f.write("| ID | Escenario de Prueba | Riesgo | Acción Decidida | Tools Activadas | Radicado CAI | Costo (USD) | Latencia |\n")
        f.write("| :--- | :--- | :---: | :--- | :--- | :---: | :---: | :---: |\n")
        for r in results:
            tools_str = ", ".join(f"`{t}`" for t in r.get("tools_invoked", []))
            cai_str = f"`{r.get('police_report_id')}`" if r.get('police_report_id') else "N/A"
            cost = r.get("telemetry", {}).get("estimated_cost_usd")
            cost_str = (
                f"${cost:.5f}"
                if r.get("usage_verifiable") and isinstance(cost, (int, float))
                else "N/D"
            )
            f.write(f"| **{r['id']}** | {r['title']} | **{r['risk_level']}** | `{r['action']}` | {tools_str} | {cai_str} | {cost_str} | {r.get('duration_seconds', 0)}s |\n")
        f.write("\n---\n\n")
        f.write("## 📝 Detalle Caso a Caso\n\n")
        for r in results:
            f.write(f"### {r['id']} · {r['title']}\n")
            f.write(
                f"- **Estado:** `{r.get('status', 'unknown')}` | "
                f"**Modo solicitado:** `{r.get('execution_mode_requested', 'unknown')}` | "
                f"**Origen:** `{r.get('analysis_source', 'unknown')}` | "
                f"**Estado del proveedor:** `{r.get('provider_execution_status', 'unknown')}`\n"
            )
            f.write(
                f"- **Modelo solicitado/proveedor:** `{r.get('requested_model', 'unknown')}` / "
                f"`{r.get('provider_model') or 'N/D'}` | "
                f"**Respuesta proveedor:** `{r.get('provider_response_id') or 'N/D'}`\n"
            )
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
