"""
Evaluación honesta de UrlSandbox sobre las URLs del dataset (Hito S3)
Reto Agente 2026 · Equipo Codixia

Separa la detección por heurística (TLD, typosquatting) de la detección por lista negra.
Solo lectura y SIN red: usa analyze_url(url, expand=False), que nunca abre conexiones.
No escribe archivos ni modifica el dataset.

Uso:
    python scripts/eval_sandbox_urls.py
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# _get_blacklist es privada: se importa solo para avisar si la lista por defecto está vacía
# (script interno del repo; no es API pública del sandbox).
from src.tools.url_sandbox import analyze_url, _get_blacklist

DATASET_PATH = ROOT / "data" / "scam_dataset_30.json"
URL_RE = re.compile(r"""https?://[^\s"'<>]+""")
FLAGGED_VERDICTS = ("MALICIOSO", "SOSPECHOSO")


def evaluate(dataset_path) -> dict:
    """Analiza las URLs únicas de los casos maliciosos solo con heurística y con lista negra."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
    urls = []
    for case in cases:
        if not case.get("has_malicious_url"):
            continue
        for url in URL_RE.findall(case.get("text") or ""):
            url = url.rstrip(".,;:!?)")
            if url not in urls:
                urls.append(url)
    rows = []
    for url in urls:
        rows.append({
            "url": url,
            "heuristic": analyze_url(url, expand=False, blacklist=frozenset())["verdict"],
            "with_list": analyze_url(url, expand=False)["verdict"],
        })
    heuristic_counts = Counter(r["heuristic"] for r in rows)
    blacklist_counts = Counter(r["with_list"] for r in rows)
    heuristic = sum(heuristic_counts[v] for v in FLAGGED_VERDICTS)
    with_list = sum(blacklist_counts[v] for v in FLAGGED_VERDICTS)
    return {
        "total": len(rows),
        "heuristic_flagged": heuristic,
        "blacklist_flagged": with_list,
        "list_only": with_list - heuristic,
        "heuristic_counts": dict(heuristic_counts),
        "blacklist_counts": dict(blacklist_counts),
        "blacklist_size": len(_get_blacklist()),
        "rows": rows,
    }


def _breakdown(counts: dict) -> str:
    return ", ".join(f"{counts.get(v, 0)} {v}" for v in FLAGGED_VERDICTS)


def main():
    result = evaluate(DATASET_PATH)
    rows, total = result["rows"], result["total"]
    width = max([len("URL")] + [len(r["url"]) for r in rows])
    line = "+-" + "-" * width + "-+-----------------+-----------------+"
    print(line)
    print(f"| {'URL':<{width}} | {'Solo heurística':<15} | {'Con lista negra':<15} |")
    print(line)
    for r in rows:
        print(f"| {r['url']:<{width}} | {r['heuristic']:<15} | {r['with_list']:<15} |")
    print(line)
    print(f"Solo heurística: {result['heuristic_flagged']}/{total} marcadas "
          f"({_breakdown(result['heuristic_counts'])})")
    print(f"Con lista negra: {result['blacklist_flagged']}/{total} marcadas "
          f"({_breakdown(result['blacklist_counts'])})")
    print(f"Detecciones que dependen solo de la lista: {result['list_only']}")
    if result["blacklist_size"] == 0:
        print("AVISO: la lista negra por defecto esta vacia o no se pudo cargar: "
              "la columna 'Con lista negra' equivale a la heuristica.")
    print("La lista incluye los dominios de este mismo dataset: la cifra con lista no mide la heurística.")
    print("Esta evaluación no mide falsos positivos: solo analiza casos con URL maliciosa.")


if __name__ == "__main__":
    main()
