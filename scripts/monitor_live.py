"""
Monitor en Vivo de la Bitácora de Carga Desatendida (Hito S4)
SentinelGuard AI · Equipo Codixia

Ejecuta un dashboard en vivo en la terminal mostrando:
- Progreso de 1.050 tareas
- Tiempo transcurrido (hacia las 12 horas)
- Consumo de tokens y costos en dólares reales
- Últimas tareas procesadas en tiempo real
"""

import sys
import os
import json
import time
from pathlib import Path

# Configurar encoding UTF-8 para consola de Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BITACORA_JSON = PROJECT_ROOT / "data" / "bitacora_s4_carga.json"
BITACORA_CSV = PROJECT_ROOT / "data" / "bitacora_s4_carga.csv"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def render_dashboard():
    if not BITACORA_JSON.exists():
        print("⏳ Esperando inicialización de la bitácora...")
        return

    try:
        with open(BITACORA_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return

    meta = data.get("metadata", {})
    tasks = data.get("tasks", [])

    total = meta.get("total_tasks", 1050)
    completed = meta.get("completed_tasks", len(tasks))
    success = meta.get("success_count", 0)
    pct = (completed / total) * 100 if total > 0 else 0
    tokens = meta.get("total_tokens", 0)
    cost = meta.get("total_cost_usd", 0.0)
    elapsed_h = meta.get("elapsed_time_hours", 0.0)
    
    # Calcular el tiempo desatendido real acumulado entre el primer y último registro
    if tasks and len(tasks) >= 2:
        try:
            from datetime import datetime
            t_first = datetime.fromisoformat(tasks[0].get("timestamp"))
            t_last = datetime.fromisoformat(tasks[-1].get("timestamp"))
            real_span_h = (t_last - t_first).total_seconds() / 3600.0
            elapsed_h = max(elapsed_h, real_span_h)
        except Exception:
            pass

    avg_lat = meta.get("average_latency_sec", 0.0)
    avg_cost = meta.get("average_cost_per_task_usd", 0.0)

    # Barra visual de progreso
    bar_width = 40
    filled = int(bar_width * (completed / total)) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_width - filled)

    clear_screen()
    print("=" * 85)
    print("  🛡️  SENTINELGUARD AI — MONITOR DE CARGA EN VIVO (HITO S4)")
    print("  Reto Agente 2026 · Platica.mx × Campuslands · Equipo Codixia")
    print("=" * 85)
    print(f"\n  📊 PROGRESO GENERAL: [{bar}] {pct:.1f}% ({completed}/{total} tareas)")
    print(f"  ⏱️  TIEMPO DESATENDIDO:  {elapsed_h:.2f}h de 12.00h requeridas")
    print(f"  ✅ TASA DE ÉXITO:       {meta.get('success_rate', '100%')} ({success} éxitos / {meta.get('error_count', 0)} fallos)")
    print(f"  🧠 CONSUMO TOKENS:      {tokens:,} tokens de Grok 4.7")
    print(f"  💰 COSTO REAL TOTAL:    ${cost:.4f} USD (promedio ${avg_cost:.5f}/tarea)")
    print(f"  ⚡ LATENCIA PROMEDIO:   {avg_lat:.2f}s por caso")
    print("\n" + "-" * 85)
    print("  📋 ÚLTIMAS 8 TAREAS AUDITADAS EN TIEMPO REAL:")
    print("-" * 85)
    print(f"  {'TASK ID':<11} | {'CATEGORÍA':<16} | {'RIESGO':<9} | {'EXPEDIENTE CAI':<23} | {'COSTO'}")
    print("  " + "-" * 81)

    recent = tasks[-8:] if len(tasks) >= 8 else tasks
    for t in reversed(recent):
        tid = t.get("task_id", "")
        cat = t.get("category", "")[:15]
        risk = t.get("risk_level", "N/A")[:8]
        cai = t.get("police_report_id") or "Sin radicado"
        c_task = t.get("estimated_cost_usd", 0.0)

        # Emoji visual según riesgo
        badge = "🔴" if risk in ["CRÍTICO", "CRITICO"] else "🟡" if risk == "ALTO" else "🟢"
        print(f"  {tid:<11} | {cat:<16} | {badge} {risk:<7} | {cai:<23} | ${c_task:.5f}")

    print("\n" + "=" * 85)
    print("  📡 Pasarela oficial: https://api.reto.pltk.mx/v1 (grok-4.7 en vivo)")
    print("  📁 Bitácora CSV: data/bitacora_s4_carga.csv  (Actualización en vivo cada 3s)")
    print("  (Presiona Ctrl+C en cualquier momento para salir del monitor)")
    print("=" * 85)


def main():
    while True:
        render_dashboard()
        time.sleep(3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Monitor cerrado. La corrida de carga continúa en segundo plano.")
