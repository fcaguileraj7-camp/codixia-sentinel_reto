#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/benchmark_token_costs.py
SentinelGuard AI - Reto Agente 2026 (Platica.mx x Campuslands)
Módulo: Subproceso 3 del Rol 5 - Dataset Engineering, Stress Testing & UI
Responsable: Juan José González (Rol 5)

Benchmark offline determinista para medición de tokens y proyección de costos por tarea.
Procesa los 40 registros de data/scam_dataset_30.json en modo 100% local ($0.00 USD)
y genera dos reportes oficiales:
  1. data/token_cost_report_30.json (CASE-001 a CASE-030)
  2. data/token_cost_report_40.json (CASE-001 a CASE-040)
"""

import os
import sys
import json
import math
import socket
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import List, Dict, Any

# ==============================================================================
# 1. BARRERA OFFLINE PREVENTIVA (Antes de cualquier importación de configuración)
# ==============================================================================
ORIGINAL_GROK_MODE = os.environ.get("GROK_MODE")
os.environ["GROK_MODE"] = "mock"

# Asegurar que el directorio raíz del proyecto esté en sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Importar configuración y neutralizar modo en memoria
import src.config
src.config.GROK_MODE = "mock"

from src.client import GrokClient, GROK_MODEL
from src.agent.sentinel import SentinelAgent


class InstrumentedGrokClient(GrokClient):
    """
    Cliente LLM instrumentado para telemetría offline de tokens y costos (Rol 5).
    Reutiliza el fallback determinista existente en GrokClient.chat_completion()
    sin duplicar código ni emitir llamadas a la red ($0.00 USD).
    """

    def __init__(self):
        super().__init__(use_real_api=False)
        # Blindaje de seguridad estricto: forzar modo offline inmutable
        self.live_mode = False
        self.client = None
        self.configured = False
        self.last_source = "simulated"
        self.last_simulated = True
        self.last_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "mode": "simulated_benchmark"
        }

    def chat_completion(
        self,
        messages: list[dict],
        model: str = GROK_MODEL,
        temperature: float = 0.2,
        max_tokens: int = 500
    ) -> str:
        # 1. Asegurar estado offline incondicional
        self.live_mode = False
        self.client = None

        # 2. Reutilizar el fallback determinista existente en src/client.py
        raw_response = super().chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # 3. Estimación heurística de tokens: ceil(caracteres / 4.0)
        # Para la entrada: considerar el contenido de todos los mensajes enviados
        input_chars = sum(len(m.get("content", "")) for m in messages)
        prompt_tokens = math.ceil(input_chars / 4.0)

        # Para la salida: considerar el texto completo devuelto por el fallback
        completion_chars = len(raw_response)
        completion_tokens = math.ceil(completion_chars / 4.0)
        total_tokens = prompt_tokens + completion_tokens

        # 4. Proyección de costos con Decimal (Tarifas CONFIGURED_UNVERIFIED de src/client.py)
        # Prompt: USD 2.00 por 1M tokens ($0.000002 / token)
        # Completion: USD 10.00 por 1M tokens ($0.000010 / token)
        cost_dec = (Decimal(prompt_tokens) * Decimal("0.000002")) + (Decimal(completion_tokens) * Decimal("0.000010"))
        estimated_cost_usd = float(cost_dec.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))

        # 5. Registrar telemetría de la inferencia simulada
        self.last_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost_usd,
            "mode": "simulated_benchmark_heuristic"
        }

        return raw_response


def compute_summary_metrics(evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula las métricas agregadas a partir de los resultados individuales procesados."""
    total_cases = len(evaluations)
    successful = sum(1 for c in evaluations if c.get("status") == "success")
    failed = sum(1 for c in evaluations if c.get("status") != "success")

    total_prompt_tokens = sum(c.get("prompt_tokens", 0) for c in evaluations)
    total_completion_tokens = sum(c.get("completion_tokens", 0) for c in evaluations)
    total_tokens = sum(c.get("total_tokens", 0) for c in evaluations)

    total_cost_dec = sum((Decimal(str(c.get("estimated_cost_usd", 0.0))) for c in evaluations), Decimal("0.0"))
    total_estimated_cost_usd = float(total_cost_dec.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))

    if total_cases > 0:
        avg_tokens = round(total_tokens / total_cases, 2)
        avg_cost_dec = total_cost_dec / Decimal(total_cases)
        avg_cost = float(avg_cost_dec.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))
    else:
        avg_tokens = 0.0
        avg_cost = 0.0

    return {
        "total_cases_evaluated": total_cases,
        "successful_evaluations": successful,
        "failed_evaluations": failed,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
        "total_estimated_cost_usd": total_estimated_cost_usd,
        "average_tokens_per_case": avg_tokens,
        "average_cost_usd_per_case": avg_cost
    }


def build_report(
    report_name: str,
    dataset_source: str,
    scope_description: str,
    evaluations: List[Dict[str, Any]],
    generated_at: str
) -> Dict[str, Any]:
    """Construye la estructura formal del reporte JSON cumpliendo la especificación."""
    return {
        "report_metadata": {
            "report_name": report_name,
            "generated_at": generated_at,
            "dataset_source": dataset_source,
            "scope_description": scope_description,
            "execution_mode": "offline_deterministic_benchmark",
            "real_api_calls_made": 0,
            "real_api_cost_usd": 0.0,
            "estimation_method": "heuristic_lexical_character_ratio_4.0",
            "pricing_policy": {
                "prompt_rate_per_1m_tokens_usd": 2.0,
                "completion_rate_per_1m_tokens_usd": 10.0
            },
            "tariff_status": "CONFIGURED_UNVERIFIED"
        },
        "summary_metrics": compute_summary_metrics(evaluations),
        "case_evaluations": evaluations
    }


def run_benchmark():
    """Ejecuta el ciclo integral de benchmarking offline sobre el dataset dual."""
    # Bloqueo estricto de red a nivel de socket
    orig_socket_connect = socket.socket.connect
    def _blocked_connect(self, *args, **kwargs):
        raise RuntimeError("Violación de seguridad offline: intento de conexión de red detectado durante el benchmark.")

    socket.socket.connect = _blocked_connect

    try:
        print("=" * 70)
        print("🛡️  SENTINELGUARD AI — BENCHMARK OFFLINE DE TOKENS Y COSTOS (ROL 5)")
        print("=" * 70)

        # 1. Inicialización del cliente y verificación pre-flight
        spy_client = InstrumentedGrokClient()
        if spy_client.live_mode is not False or spy_client.client is not None:
            raise RuntimeError("Fallo crítico de seguridad: InstrumentedGrokClient no está en modo offline estricto.")

        agent = SentinelAgent(client=spy_client)
        print("✓ Cliente instrumentado verificado en modo offline ($0.00 USD).")
        print("✓ Barrera de socket y variables de entorno activas. Cero llamadas HTTP.")

        # 2. Carga del dataset dual
        dataset_path = BASE_DIR / "data" / "scam_dataset_30.json"
        if not dataset_path.exists():
            raise FileNotFoundError(f"No se encontró el dataset en: {dataset_path}")

        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        total_records = len(dataset)
        print(f"✓ Dataset cargado exitosamente: {total_records} registros encontrados.")
        if total_records < 40:
            print(f"⚠ Advertencia: Se esperaban 40 registros y se encontraron {total_records}.")

        # 3. Ejecución en una sola pasada determinista
        evaluations: List[Dict[str, Any]] = []
        print("\nIniciando procesamiento determinista de casos...")

        for idx, case in enumerate(dataset, start=1):
            case_id = case.get("id", f"UNKNOWN-{idx}")
            case_text = case.get("text", "")
            category = case.get("category", "DESCONOCIDO")
            expected_verdict = case.get("expected_verdict", "DESCONOCIDO")

            # Aislamiento determinista de sesión por caso
            session_id = f"bench_s3_{case_id}"

            try:
                res = agent.process_message(case_text, session_id=session_id)
                decision = res.get("decision", {})
                status_raw = res.get("status", "error")

                # Si el análisis no estuvo disponible, marcar error
                if not decision.get("analysis_available", True):
                    status = "error"
                    error_message = decision.get("reasoning", "Análisis no disponible en inferencia.")
                elif status_raw != "success":
                    status = "error"
                    error_message = res.get("error", "Error reportado en respuesta del agente.")
                else:
                    status = "success"
                    error_message = None

                actual_verdict = decision.get("risk_level", "DESCONOCIDO")
                actual_action = decision.get("action", "DESCONOCIDO")

                usage = spy_client.last_usage
                p_tokens = usage.get("prompt_tokens", 0)
                c_tokens = usage.get("completion_tokens", 0)
                t_tokens = usage.get("total_tokens", 0)
                cost_usd = usage.get("estimated_cost_usd", 0.0)

            except Exception as e:
                status = "error"
                error_message = str(e)
                actual_verdict = "ERROR"
                actual_action = "ERROR"
                p_tokens = 0
                c_tokens = 0
                t_tokens = 0
                cost_usd = 0.0

            case_eval = {
                "case_id": case_id,
                "category": category,
                "expected_verdict": expected_verdict,
                "actual_verdict": actual_verdict,
                "actual_action": actual_action,
                "status": status,
                "error_message": error_message,
                "prompt_tokens": p_tokens,
                "completion_tokens": c_tokens,
                "total_tokens": t_tokens,
                "estimated_cost_usd": cost_usd
            }
            evaluations.append(case_eval)

            # Log resumido cada 10 casos
            if idx % 10 == 0 or idx == total_records:
                print(f"  -> Procesados {idx}/{total_records} casos (Último: {case_id} | Tokens: {t_tokens} | Costo: ${cost_usd:.6f} USD)")

        # 4. Segmentación y generación de los dos reportes oficiales
        generated_at = datetime.now(timezone.utc).isoformat()
        reports_dir = BASE_DIR / "data"

        # Reporte de 30 casos originales (CASE-001 a CASE-030)
        evals_30 = evaluations[:30]
        report_30 = build_report(
            report_name="token_cost_report_30.json",
            dataset_source="data/scam_dataset_30.json",
            scope_description="30 registros originales del dataset histórico (CASE-001 a CASE-030: 29 casos de auditoría digital y 1 control legítimo de transporte)",
            evaluations=evals_30,
            generated_at=generated_at
        )
        report_30_path = reports_dir / "token_cost_report_30.json"
        with open(report_30_path, "w", encoding="utf-8") as f:
            json.dump(report_30, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Reporte generado: {report_30_path}")

        # Reporte de 40 casos duales completos (CASE-001 a CASE-040)
        evals_40 = evaluations[:40]
        report_40 = build_report(
            report_name="token_cost_report_40.json",
            dataset_source="data/scam_dataset_30.json",
            scope_description="40 registros del dataset dual completo (CASE-001 a CASE-040: 30 registros originales más 10 escenarios de acompañamiento físico y emergencias en taxi)",
            evaluations=evals_40,
            generated_at=generated_at
        )
        report_40_path = reports_dir / "token_cost_report_40.json"
        with open(report_40_path, "w", encoding="utf-8") as f:
            json.dump(report_40, f, ensure_ascii=False, indent=2)
        print(f"✓ Reporte generado: {report_40_path}")

        # 5. Resumen de resultados en consola
        s30 = report_30["summary_metrics"]
        s40 = report_40["summary_metrics"]

        print("\n" + "=" * 70)
        print("📊 RESUMEN EJECUTIVO DE RESULTADOS")
        print("=" * 70)
        print(f"Reporte 30 Casos:")
        print(f"  • Casos evaluados: {s30['total_cases_evaluated']} (Exitosos: {s30['successful_evaluations']}, Fallidos: {s30['failed_evaluations']})")
        print(f"  • Tokens totales: {s30['total_tokens']:,} (Prompt: {s30['total_prompt_tokens']:,}, Completion: {s30['total_completion_tokens']:,})")
        print(f"  • Promedio de tokens por tarea: {s30['average_tokens_per_case']:.2f}")
        print(f"  • Costo total proyectado: ${s30['total_estimated_cost_usd']:.6f} USD")
        print(f"  • Costo promedio proyectado por tarea: ${s30['average_cost_usd_per_case']:.6f} USD")

        print(f"\nReporte 40 Casos (Dataset Dual Completo):")
        print(f"  • Casos evaluados: {s40['total_cases_evaluated']} (Exitosos: {s40['successful_evaluations']}, Fallidos: {s40['failed_evaluations']})")
        print(f"  • Tokens totales: {s40['total_tokens']:,} (Prompt: {s40['total_prompt_tokens']:,}, Completion: {s40['total_completion_tokens']:,})")
        print(f"  • Promedio de tokens por tarea: {s40['average_tokens_per_case']:.2f}")
        print(f"  • Costo total proyectado: ${s40['total_estimated_cost_usd']:.6f} USD")
        print(f"  • Costo promedio proyectado por tarea: ${s40['average_cost_usd_per_case']:.6f} USD")

        print("\n🔒 CONFIRMACIÓN DE SEGURIDAD OFFLINE:")
        print("  • Llamadas reales a la API de Grok: 0")
        print("  • Costo real incurrido en Platica: $0.00 USD")
        print("=" * 70)

        return report_30, report_40

    finally:
        # Restaurar socket y variables de entorno originales
        socket.socket.connect = orig_socket_connect
        if ORIGINAL_GROK_MODE is not None:
            os.environ["GROK_MODE"] = ORIGINAL_GROK_MODE
        else:
            os.environ.pop("GROK_MODE", None)


if __name__ == "__main__":
    run_benchmark()
