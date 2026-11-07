"""
Evaluación de rendimiento y comparación de latencia de la caché de UrlSandbox.
Reto Agente 2026 · Equipo Codixia

Compara el rendimiento en frío frente a caliente (aciertos en caché),
simula un ciclo de carga con URLs del dataset y valida la idempotencia
y ahorro de red ante acortadores simulados.

Uso:
    python scripts/bench_sandbox_cache.py [--reps 200] [--iterations 1000]
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import src.tools.url_sandbox as url_sandbox
from src.tools.threat_inspector import inspect_threat

DATASET_PATH = ROOT / "data" / "scam_dataset_30.json"
DEFAULT_EXPAND_TIMEOUT = getattr(url_sandbox, "EXPAND_TIMEOUT", 3.0)


def _fake_head(url: str, timeout: float = DEFAULT_EXPAND_TIMEOUT) -> Tuple[int, Optional[str]]:
    """Doble de red local sin espera para evitar peticiones reales."""
    return (200, None)


def calculate_percentile(data: List[float], p: float) -> float:
    """Calcula el percentil p (0..100) utilizando interpolación lineal."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    if len(sorted_data) == 1:
        return sorted_data[0]
    rank = (len(sorted_data) - 1) * (p / 100.0)
    low = int(rank)
    high = min(low + 1, len(sorted_data) - 1)
    weight = rank - low
    return sorted_data[low] * (1.0 - weight) + sorted_data[high] * weight


def load_dataset_cases(dataset_path: Path) -> List[Dict[str, Any]]:
    """Carga los casos de prueba desde el archivo JSON del dataset."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset no encontrado en: {dataset_path}")
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("cases", [])
    if isinstance(data, list):
        return data
    return []


def extract_case_urls(cases: List[Dict[str, Any]]) -> Tuple[List[List[str]], List[str]]:
    """Extrae las URLs detectadas por caso y la lista de URLs únicas consolidadas."""
    case_urls_list: List[List[str]] = []
    unique_urls: List[str] = []
    for case in cases:
        text = case.get("text") or ""
        threat_data = inspect_threat(text)
        detected = threat_data.get("detected_urls") or []
        case_urls_list.append(detected)
        for u in detected:
            if u not in unique_urls:
                unique_urls.append(u)
    return case_urls_list, unique_urls


def verify_cache_contract() -> None:
    """Comprueba la disponibilidad de la caché y de telemetry['cache_hit']."""
    try:
        sample = url_sandbox.analyze_url("https://example.com", expand=False)
    except Exception as exc:
        sys.stderr.write(
            f"Error al ejecutar analyze_url para verificar la caché: {exc}\n"
        )
        sys.exit(1)

    telemetry = sample.get("telemetry") if isinstance(sample, dict) else None
    if not isinstance(telemetry, dict) or "cache_hit" not in telemetry:
        sys.stderr.write(
            "Error: analyze_url no incluye telemetry['cache_hit'] "
            "(la caché de UrlSandbox no está implementada en este entorno).\n"
        )
        sys.exit(1)

    if not hasattr(url_sandbox, "clear_analysis_cache"):
        sys.stderr.write(
            "Error: url_sandbox no expone la función pública clear_analysis_cache().\n"
        )
        sys.exit(1)


def run_dataset_benchmark(urls: List[str], reps: int) -> None:
    """Ejecuta el análisis de latencia en frío y caliente sobre las URLs del dataset."""
    clear_cache = getattr(url_sandbox, "clear_analysis_cache", lambda: None)
    cold_latencies: List[float] = []
    warm_latencies: List[float] = []
    worst_url: Optional[str] = None
    worst_url_median_cold: float = -1.0

    print(f"\n--- 1. URLs del Dataset ({len(urls)} URLs, {reps} repeticiones) ---")
    for url in urls:
        url_cold: List[float] = []
        for _ in range(reps):
            # Medición en frío: caché limpia antes de cada llamada
            clear_cache()
            t0 = time.perf_counter()
            url_sandbox.analyze_url(url)
            t_cold_ms = (time.perf_counter() - t0) * 1000.0
            cold_latencies.append(t_cold_ms)
            url_cold.append(t_cold_ms)

            # Medición en caliente: acierto en caché
            t0 = time.perf_counter()
            url_sandbox.analyze_url(url)
            t_warm_ms = (time.perf_counter() - t0) * 1000.0
            warm_latencies.append(t_warm_ms)

        med_cold = calculate_percentile(url_cold, 50.0)
        if med_cold > worst_url_median_cold:
            worst_url_median_cold = med_cold
            worst_url = url

    print(f"Mediciones globales ({len(cold_latencies)} frío, {len(warm_latencies)} caliente):")
    print(
        f"  Frío:     Mediana = {calculate_percentile(cold_latencies, 50.0):.4f} ms | "
        f"p95 = {calculate_percentile(cold_latencies, 95.0):.4f} ms | "
        f"p99 = {calculate_percentile(cold_latencies, 99.0):.4f} ms"
    )
    print(
        f"  Caliente: Mediana = {calculate_percentile(warm_latencies, 50.0):.4f} ms | "
        f"p95 = {calculate_percentile(warm_latencies, 95.0):.4f} ms | "
        f"p99 = {calculate_percentile(warm_latencies, 99.0):.4f} ms"
    )
    print(f"  Peor URL en frío: {worst_url} (mediana: {worst_url_median_cold:.4f} ms)")


def run_load_cycle_benchmark(
    cases: List[Dict[str, Any]], case_urls: List[List[str]], iterations: int
) -> None:
    """Simula un ciclo de carga con y sin caché sobre las URLs de los casos."""
    clear_cache = getattr(url_sandbox, "clear_analysis_cache", lambda: None)
    num_cases = len(cases)
    if num_cases == 0:
        print("\n--- 2. Ciclo de Carga Simulado: sin casos para evaluar ---")
        return

    print(f"\n--- 2. Ciclo de Carga Simulado ({iterations} iteraciones sobre {num_cases} casos) ---")

    # Ciclo con caché: limpia solo al inicio
    clear_cache()
    calls_cached = 0
    hits_cached = 0
    t_sandbox_cached = 0.0

    for i in range(iterations):
        urls = case_urls[i % num_cases]
        for u in urls:
            t0 = time.perf_counter()
            res = url_sandbox.analyze_url(u)
            t_sandbox_cached += (time.perf_counter() - t0)
            calls_cached += 1
            if res.get("telemetry", {}).get("cache_hit") is True:
                hits_cached += 1

    hit_rate_cached = (hits_cached / calls_cached * 100.0) if calls_cached > 0 else 0.0

    # Ciclo sin caché: limpia antes de cada llamada
    calls_uncached = 0
    hits_uncached = 0
    t_sandbox_uncached = 0.0

    for i in range(iterations):
        urls = case_urls[i % num_cases]
        for u in urls:
            clear_cache()
            t0 = time.perf_counter()
            res = url_sandbox.analyze_url(u)
            t_sandbox_uncached += (time.perf_counter() - t0)
            calls_uncached += 1
            if res.get("telemetry", {}).get("cache_hit") is True:
                hits_uncached += 1

    hit_rate_uncached = (hits_uncached / calls_uncached * 100.0) if calls_uncached > 0 else 0.0
    speedup = (t_sandbox_uncached / t_sandbox_cached) if t_sandbox_cached > 0 else 0.0

    print("Con caché activa:")
    print(f"  Llamadas totales: {calls_cached}")
    print(f"  Tasa de aciertos: {hit_rate_cached:.2f}% ({hits_cached}/{calls_cached})")
    print(
        f"  Tiempo total del sandbox: {t_sandbox_cached * 1000.0:.2f} ms ({t_sandbox_cached:.4f} s)"
    )

    print("Sin caché (frío continuo):")
    print(f"  Llamadas totales: {calls_uncached}")
    print(f"  Tasa de aciertos: {hit_rate_uncached:.2f}% ({hits_uncached}/{calls_uncached})")
    print(
        f"  Tiempo total del sandbox: {t_sandbox_uncached * 1000.0:.2f} ms ({t_sandbox_uncached:.4f} s)"
    )

    print(f"Aceleración de la caché: {speedup:.2f}x")


def run_simulated_shortener_benchmark() -> None:
    """Evalúa el comportamiento de la caché ante la resolución de un acortador simulado."""
    clear_cache = getattr(url_sandbox, "clear_analysis_cache", lambda: None)
    head_calls = 0

    def shortener_double(url: str, timeout: float = DEFAULT_EXPAND_TIMEOUT) -> Tuple[int, Optional[str]]:
        nonlocal head_calls
        head_calls += 1
        if url == "https://bit.ly/x":
            return (301, "https://example.com/destino")
        return (200, None)

    print("\n--- 3. Verificación de Acortador Simulado (https://bit.ly/x) ---")
    clear_cache()
    url_sandbox._head_request = shortener_double

    # Primera llamada: frío (debe expandir usando el doble)
    calls_before_first = head_calls
    t0 = time.perf_counter()
    res1 = url_sandbox.analyze_url("https://bit.ly/x", expand=True)
    t1_ms = (time.perf_counter() - t0) * 1000.0
    calls_first = head_calls - calls_before_first
    hit1 = res1.get("telemetry", {}).get("cache_hit")

    # Segunda llamada: caliente (debe responder desde la caché sin invocar el doble)
    calls_before_second = head_calls
    t0 = time.perf_counter()
    res2 = url_sandbox.analyze_url("https://bit.ly/x", expand=True)
    t2_ms = (time.perf_counter() - t0) * 1000.0
    calls_second = head_calls - calls_before_second
    hit2 = res2.get("telemetry", {}).get("cache_hit")

    # Restaurar doble por defecto sin red
    url_sandbox._head_request = _fake_head

    print("Primera llamada (frío):")
    print(f"  cache_hit: {hit1}")
    print(f"  Llamadas al doble _head_request: {calls_first}")
    print(f"  URL expandida: {res1.get('expanded_url')}")
    print(f"  Latencia: {t1_ms:.4f} ms")

    print("Segunda llamada (caliente):")
    print(f"  cache_hit: {hit2}")
    print(f"  Llamadas al doble _head_request: {calls_second} (acumuladas: {head_calls})")
    print(f"  URL expandida: {res2.get('expanded_url')}")
    print(f"  Latencia: {t2_ms:.4f} ms")

    if hit2 is True and calls_second == 0:
        print("Resultado: La segunda llamada fue un acierto de caché y no realizó peticiones de red.")
    else:
        print("Aviso: Comportamiento inesperado en la caché del acortador.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark del rendimiento de la caché de UrlSandbox."
    )
    parser.add_argument(
        "--reps",
        type=int,
        default=200,
        help="Número de repeticiones para las mediciones de latencia (defecto: 200).",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Número de iteraciones para el ciclo de carga simulada (defecto: 1000).",
    )
    args = parser.parse_args()

    # Reemplazar _head_request por un doble local antes de cualquier medición
    url_sandbox._head_request = _fake_head

    print("=" * 70)
    print("Punto de Referencia: Caché de UrlSandbox (Codixia Sentinel)")
    print("Aviso: La red está simulada (_head_request devuelve respuestas locales sin espera);")
    print("       por esta razón, los tiempos fríos NO incluyen red real.")
    print("=" * 70)

    # Validar presencia del contrato de caché
    verify_cache_contract()

    # Cargar casos y URLs
    cases = load_dataset_cases(DATASET_PATH)
    case_urls, unique_urls = extract_case_urls(cases)

    # 1. URLs del dataset
    run_dataset_benchmark(unique_urls, reps=args.reps)

    # 2. Ciclo de carga simulado
    run_load_cycle_benchmark(cases, case_urls, iterations=args.iterations)

    # 3. Acortador simulado
    run_simulated_shortener_benchmark()

    print("\nBenchmark completado con éxito.")


if __name__ == "__main__":
    main()
