"""
Arnés de Prueba de Carga Desatendida (1.000 Ejecuciones)
Hito S4 - Reto Agente 2026
Liderado por: Juan José (Rol: Dataset Engineering, Stress Testing & UI)
"""

import time
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.sentinel import SentinelAgent

def run_load_test(target_iterations: int = 100, delay_sec: float = 0.05):
    """
    Ejecuta un ciclo desatendido de consultas al agente,
    registrando tiempos de respuesta, tasa de éxito y bitácora completa.
    """
    print(f"🚀 Iniciando Arnés de Carga: {target_iterations} ejecuciones...")
    agent = SentinelAgent()
    
    # Cargar dataset de pruebas
    dataset_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "scam_dataset_30.json")
    if os.path.exists(dataset_file):
        with open(dataset_file, "r", encoding="utf-8") as f:
            cases = json.load(f)
    else:
        cases = [{"text": "Bancolombia alerta: cuenta bloqueada, entre a https://banc0.cc"}]

    results = []
    start_all = time.time()
    success_count = 0

    for i in range(target_iterations):
        sample = cases[i % len(cases)]
        t0 = time.time()
        try:
            res = agent.process_message(sample["text"])
            lat = time.time() - t0
            success_count += 1
            results.append({
                "iteration": i + 1,
                "latency_sec": round(lat, 3),
                "status": "SUCCESS",
                "risk_level": res.get("decision", {}).get("risk_level", "UNKNOWN")
            })
        except Exception as e:
            lat = time.time() - t0
            results.append({
                "iteration": i + 1,
                "latency_sec": round(lat, 3),
                "status": "ERROR",
                "error": str(e)
            })

        if (i + 1) % 10 == 0 or (i + 1) == target_iterations:
            print(f"  → Procesadas: {i + 1}/{target_iterations} | Éxitos: {success_count} | Última latencia: {round(lat, 3)}s")
        time.sleep(delay_sec)

    total_time = time.time() - start_all
    avg_lat = sum(r["latency_sec"] for r in results) / len(results)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_requests": target_iterations,
        "success_rate": f"{(success_count / target_iterations) * 100:.2f}%",
        "total_time_sec": round(total_time, 2),
        "average_latency_sec": round(avg_lat, 3),
        "throughput_req_per_sec": round(target_iterations / total_time, 2)
    }

    print("\n📊 RESUMEN DE PRUEBA DE CARGA (HITO S4):")
    print(json.dumps(summary, indent=2))

    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "load_test_summary.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results[:50]}, f, indent=2)
    print(f"📁 Bitácora guardada en: {log_path}")

if __name__ == "__main__":
    # Para prueba rápida por defecto corre 20; en producción S4 se usa 1000
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    run_load_test(iterations)
