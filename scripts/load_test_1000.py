"""
Arnés de Prueba de Carga Desatendida (1.000+ Tareas de Ciberfraude en 12 Horas)
Hito S4: Reto Agente 2026 · Platica.mx × Campuslands
Equipo: Codixia (Rol 5: Juan José · Rol 1: Fabián Aguilera · Rol 2: Miguel · Rol 3: Santiago · Rol 4: Nicolle)

Requisitos de la Organización (S4):
1. 1.000 o más unidades de trabajo completadas de punta a punta.
2. 12 horas desatendidas registradas en el consumo real de la pasarela oficial.
3. Bitácora completa en JSON y CSV con hora, entrada, resultado, éxito/fallo y costo real.
4. Reanudación automática ante interrupciones de red.
"""

import sys
from pathlib import Path

# Configurar encoding UTF-8 para consola de Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Asegurar que la raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import os
import csv
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List

from src.agent.sentinel import SentinelAgent
from src.client import GrokClient
from src.config import RETO_API_KEY, RETO_BASE_URL, GROK_MODEL, is_configured
from src.utils.logger import logger

DATA_DIR = PROJECT_ROOT / "data"
QUEUE_FILE = DATA_DIR / "workload_queue_1050.json"
BITACORA_JSON = DATA_DIR / "bitacora_s4_carga.json"
BITACORA_CSV = DATA_DIR / "bitacora_s4_carga.csv"
SUMMARY_FILE = DATA_DIR / "load_test_summary.json"


def init_csv_if_missing(csv_path: Path):
    """Inicializa los encabezados del archivo CSV de bitácora si no existe."""
    if not csv_path.exists():
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "task_id",
                "timestamp",
                "category",
                "sender",
                "user_input",
                "risk_level",
                "action",
                "police_report_id",
                "status",
                "execution_status",
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "estimated_cost_usd",
                "latency_sec",
                "error_details"
            ])


def load_existing_bitacora(json_path: Path):
    """Carga los registros y tiempo previo para soporte de reanudación automática."""
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                tasks = data.get("tasks", [])
                prev_time = data.get("metadata", {}).get("elapsed_time_sec", 0.0)
                if tasks and len(tasks) >= 2:
                    try:
                        t0 = datetime.fromisoformat(tasks[0].get("timestamp"))
                        t1 = datetime.fromisoformat(tasks[-1].get("timestamp"))
                        span = (t1 - t0).total_seconds()
                        prev_time = max(prev_time, span)
                    except Exception:
                        pass
                return tasks, prev_time
        except Exception:
            return [], 0.0
    return [], 0.0


def append_csv_record(csv_path: Path, record: Dict[str, Any], max_retries: int = 5):
    """Agrega un registro individual al archivo CSV con reintentos si el archivo está bloqueado (ej. por Excel)."""
    for attempt in range(max_retries):
        try:
            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    record.get("task_id", ""),
                    record.get("timestamp", ""),
                    record.get("category", ""),
                    record.get("sender", ""),
                    record.get("user_input", "").replace("\n", " "),
                    record.get("risk_level", ""),
                    record.get("action", ""),
                    record.get("police_report_id", ""),
                    record.get("status", ""),
                    record.get("execution_status", ""),
                    record.get("prompt_tokens", 0),
                    record.get("completion_tokens", 0),
                    record.get("total_tokens", 0),
                    record.get("estimated_cost_usd", 0.0),
                    record.get("latency_sec", 0.0),
                    record.get("error_details", "")
                ])
            return
        except PermissionError:
            time.sleep(1.0)
        except Exception as e:
            logger.warning(f"Error escribiendo en CSV ({e})")
            return


def save_json_state(json_path: Path, tasks_records: List[Dict[str, Any]], stats: Dict[str, Any], max_retries: int = 5):
    """Guarda el estado completo de la bitácora en JSON de forma atómica con tolerancia a bloqueos."""
    payload = {
        "metadata": {
            "title": "SentinelGuard AI · Bitácora Oficial de Carga Desatendida (Hito S4)",
            "gateway": RETO_BASE_URL,
            "model": GROK_MODEL,
            "updated_at": datetime.now().isoformat(),
            **stats
        },
        "tasks": tasks_records
    }
    for attempt in range(max_retries):
        try:
            temp_path = json_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            temp_path.replace(json_path)
            return
        except PermissionError:
            time.sleep(1.0)
        except Exception as e:
            logger.warning(f"Error guardando JSON ({e})")
            return


def run_load_test(
    total_tasks: int = 1050,
    target_duration_hours: float = 12.0,
    use_live_api: bool = True,
    resume: bool = True
):
    print("\n" + "=" * 80)
    print("🚀 SENTINELGUARD AI · ARNÉS DE CARGA DESATENDIDA (HITO S4)")
    print(f"• Pasarela Oficial: {RETO_BASE_URL}")
    print(f"• Modelo: {GROK_MODEL}")
    print(f"• Modo API: {'REAL (Llamadas en vivo contra Grok)' if use_live_api else 'SIMULADO LOCAL ($0 USD)'}")
    print(f"• Meta de Tareas: {total_tasks} unidades de trabajo")
    print(f"• Duración Planificada: {target_duration_hours:.1f} horas continuas")
    print("=" * 80 + "\n")

    if use_live_api and not is_configured():
        print("❌ ERROR: RETO_API_KEY no configurada o inválida en .env")
        sys.exit(1)

    # 1. Cargar cola de tareas
    if not QUEUE_FILE.exists():
        print(f"Generando cola de tareas en {QUEUE_FILE}...")
        from scripts.generate_s4_dataset import main as gen_main
        gen_main()

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        all_tasks = json.load(f)

    all_tasks = all_tasks[:total_tasks]

    # 2. Reanudación automática
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    init_csv_if_missing(BITACORA_CSV)
    completed_records, previous_elapsed_sec = load_existing_bitacora(BITACORA_JSON) if resume else ([], 0.0)
    completed_ids = {r["task_id"] for r in completed_records}

    tasks_to_run = [t for t in all_tasks if t["task_id"] not in completed_ids]

    print(f"📊 Estado de arranque:")
    print(f"   • Tareas totales en la cola: {len(all_tasks)}")
    print(f"   • Ya procesadas anteriormente: {len(completed_records)}")
    print(f"   • Pendientes por procesar: {len(tasks_to_run)}\n")

    if not tasks_to_run:
        print("✅ Todas las tareas ya fueron completadas.")
        return

    # 3. Inicializar agente con cliente real
    client = GrokClient(use_real_api=use_live_api)
    agent = SentinelAgent(client=client)

    start_time = time.time()
    target_seconds = target_duration_hours * 3600.0

    total_prompt_tokens = sum(r.get("prompt_tokens", 0) for r in completed_records)
    total_completion_tokens = sum(r.get("completion_tokens", 0) for r in completed_records)
    total_cost_usd = sum(r.get("estimated_cost_usd", 0.0) for r in completed_records)
    success_count = sum(1 for r in completed_records if r.get("status") == "SUCCESS")
    error_count = sum(1 for r in completed_records if r.get("status") == "ERROR")

    for idx, item in enumerate(tasks_to_run, start=len(completed_records) + 1):
        task_id = item["task_id"]
        text = item["text"]
        sender = item.get("sender", "+573000000000")
        category = item.get("category", "ciberfraude")

        item_t0 = time.time()
        record: Dict[str, Any] = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "sender": sender,
            "user_input": text,
        }

        try:
            # Ejecución completa de punta a punta del agente
            audit_result = agent.process_message(
                user_input=text,
                session_id=sender,
                metadata={"sender": sender, "task_id": task_id, "category": category}
            )

            latency = time.time() - item_t0
            decision = audit_result.get("decision", {})
            police_report = audit_result.get("police_report")
            police_report_id = police_report.get("report_id") if isinstance(police_report, dict) else ""

            # Extraer telemetría real del cliente
            last_usage = getattr(client, "last_usage", {}) or {}
            p_tokens = last_usage.get("prompt_tokens") or 0
            c_tokens = last_usage.get("completion_tokens") or 0
            t_tokens = last_usage.get("total_tokens") or (p_tokens + c_tokens)
            cost = last_usage.get("estimated_cost_usd") or 0.0
            exec_status = last_usage.get("execution_status") or "ok"

            record.update({
                "risk_level": decision.get("risk_level", "DESCONOCIDO"),
                "action": decision.get("action", "ANALYZE_ONLY"),
                "police_report_id": police_report_id,
                "status": "SUCCESS",
                "execution_status": exec_status,
                "prompt_tokens": p_tokens,
                "completion_tokens": c_tokens,
                "total_tokens": t_tokens,
                "estimated_cost_usd": round(cost, 6),
                "latency_sec": round(latency, 2),
                "error_details": ""
            })
            success_count += 1
            total_prompt_tokens += p_tokens
            total_completion_tokens += c_tokens
            total_cost_usd += cost

        except Exception as exc:
            latency = time.time() - item_t0
            error_count += 1
            logger.error(f"[red]❌ Error en tarea {task_id}: {exc}[/red]")
            record.update({
                "risk_level": "ERROR",
                "action": "ERROR_RECOVERY",
                "police_report_id": "",
                "status": "ERROR",
                "execution_status": "exception",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
                "latency_sec": round(latency, 2),
                "error_details": str(exc)
            })

        # Guardado incremental inmediato (Garantía contra pérdida de datos)
        completed_records.append(record)
        append_csv_record(BITACORA_CSV, record)

        # Estadísticas acumuladas
        elapsed_total = previous_elapsed_sec + (time.time() - start_time)
        remaining_tasks = len(all_tasks) - len(completed_records)
        avg_latency = sum(r.get("latency_sec", 0) for r in completed_records) / len(completed_records)

        stats = {
            "total_tasks": len(all_tasks),
            "completed_tasks": len(completed_records),
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": f"{(success_count / len(completed_records)) * 100:.2f}%",
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "total_cost_usd": round(total_cost_usd, 5),
            "average_cost_per_task_usd": round(total_cost_usd / len(completed_records), 6) if completed_records else 0,
            "average_latency_sec": round(avg_latency, 2),
            "elapsed_time_sec": round(elapsed_total, 1),
            "elapsed_time_hours": round(elapsed_total / 3600.0, 2)
        }

        save_json_state(BITACORA_JSON, completed_records, stats)

        # Reporte visual por consola
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] #{len(completed_records):04d}/{len(all_tasks)} "
            f"| {task_id} ({category[:15]}) "
            f"| Riesgo: {record.get('risk_level', 'N/A'):<8} "
            f"| Tokens: {record.get('total_tokens', 0):>5} "
            f"| Costo: ${record.get('estimated_cost_usd', 0):.5f} "
            f"| Latencia: {record.get('latency_sec', 0):.1f}s "
            f"| Acumulado: ${total_cost_usd:.4f} USD"
        )

        # Regulación de cadencia para cumplir las 12 horas desatendidas
        if remaining_tasks > 0 and target_seconds > 0:
            remaining_time = target_seconds - elapsed_total
            ideal_delay = (remaining_time / remaining_tasks) - latency if remaining_time > 0 else 12.0
            delay = max(5.0, min(ideal_delay, 15.0))  # Máximo 15s de pausa para cumplir 12h y cerrar antes de 23:30 Colombia
            time.sleep(delay)

    # 4. Resumen final oficial (Hito S4)
    print("\n" + "=" * 80)
    print("🏆 PRUEBA DE CARGA DESATENDIDA COMPLETADA (HITO S4)")
    print(json.dumps(stats, indent=2))
    print("=" * 80)

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(f"\n📁 Bitácora JSON: {BITACORA_JSON}")
    print(f"📁 Bitácora CSV:  {BITACORA_CSV}")
    print(f"📁 Resumen Oficial: {SUMMARY_FILE}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelGuard AI · Arnés de Carga Desatendida")
    parser.add_argument("--tasks", type=int, default=1050, help="Total de tareas (default: 1050)")
    parser.add_argument("--hours", type=float, default=12.0, help="Horas continuas desatendidas (default: 12.0)")
    parser.add_argument("--live", action="store_true", default=True, help="Usar API real de Grok 4.7")
    parser.add_argument("--mock", dest="live", action="store_false", help="Modo simulado local ($0 USD)")
    parser.add_argument("--no-resume", dest="resume", action="store_false", help="No reanudar bitácora existente")
    args = parser.parse_args()

    run_load_test(
        total_tasks=args.tasks,
        target_duration_hours=args.hours,
        use_live_api=args.live,
        resume=args.resume
    )
