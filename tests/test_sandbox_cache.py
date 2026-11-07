"""
Pruebas unitarias de la caché LRU en memoria para UrlSandbox.
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
"""

import concurrent.futures
from typing import Dict, Any

import pytest

import src.tools.url_sandbox as sandbox


def _make_counting_head(routes: Dict[str, Any]):
    """Crea un doble de _head_request que registra y cuenta las llamadas de red."""
    calls = []

    def _head(url: str, timeout: int = 3, **kwargs):
        calls.append(url)
        return routes.get(url, (200, None))

    return _head, calls


def test_second_call_cache_hit_and_telemetry(monkeypatch):
    """La segunda llamada idéntica acierta en caché sin invocar la red y reporta telemetry adecuada."""
    routes = {
        "http://bit.ly/test-hit": (301, "https://example.org/final"),
        "https://bit.ly/test-hit": (301, "https://example.org/final"),
        "https://example.org/final": (200, None),
    }
    head_mock, calls = _make_counting_head(routes)
    monkeypatch.setattr(sandbox, "_head_request", head_mock)

    url = "https://bit.ly/test-hit"
    res1 = sandbox.analyze_url(url, expand=True, blacklist=frozenset())
    assert res1["status"] == "success"
    assert res1["telemetry"]["cache_hit"] is False
    assert res1["telemetry"]["expansion_ms"] is not None
    first_calls_count = len(calls)
    assert first_calls_count > 0

    res2 = sandbox.analyze_url(url, expand=True, blacklist=frozenset())
    assert res2["status"] == "success"
    assert res2["telemetry"]["cache_hit"] is True
    assert res2["telemetry"]["expansion_ms"] is None
    # No se realizaron nuevas llamadas de red en el acierto
    assert len(calls) == first_calls_count

    # Mismo resultado salvo la telemetría
    clean_res1 = {k: v for k, v in res1.items() if k != "telemetry"}
    clean_res2 = {k: v for k, v in res2.items() if k != "telemetry"}
    assert clean_res1 == clean_res2


def test_mutations_do_not_affect_future_responses(monkeypatch):
    """Mutar findings, redirect_chain o telemetry en el resultado devuelto no contamina la caché."""
    routes = {
        "https://bit.ly/test-mutate": (301, "https://example.org/dest"),
        "https://example.org/dest": (200, None),
    }
    head_mock, _ = _make_counting_head(routes)
    monkeypatch.setattr(sandbox, "_head_request", head_mock)

    url = "https://bit.ly/test-mutate"
    res1 = sandbox.analyze_url(url, expand=True, blacklist=frozenset())
    orig_findings = list(res1["findings"])
    orig_chain = list(res1["redirect_chain"])

    # Mutaciones agresivas sobre el primer resultado
    res1["findings"].append("hallazgo_falso_inyectado")
    res1["redirect_chain"].append("https://sitio-falso.org")
    res1["telemetry"]["cache_hit"] = "mutado"
    res1["telemetry"]["extra_campo"] = 12345

    res2 = sandbox.analyze_url(url, expand=True, blacklist=frozenset())
    assert res2["telemetry"]["cache_hit"] is True
    assert "hallazgo_falso_inyectado" not in res2["findings"]
    assert res2["findings"] == orig_findings
    assert res2["redirect_chain"] == orig_chain
    assert "extra_campo" not in res2["telemetry"]

    # Mutar el segundo resultado tampoco afecta a una tercera llamada
    res2["findings"].append("segundo_hallazgo_falso")
    res2["redirect_chain"].append("https://otro-falso.org")
    res3 = sandbox.analyze_url(url, expand=True, blacklist=frozenset())
    assert res3["telemetry"]["cache_hit"] is True
    assert "segundo_hallazgo_falso" not in res3["findings"]
    assert res3["findings"] == orig_findings
    assert res3["redirect_chain"] == orig_chain


def test_expansion_error_is_not_cached(monkeypatch):
    """Un resultado con error de expansión de red no se guarda en caché y reintenta en la siguiente llamada."""
    calls = []

    def _failing_head(url: str, timeout: int = 3, **kwargs):
        calls.append(url)
        raise OSError("fallo simulado de conexión")

    monkeypatch.setattr(sandbox, "_head_request", _failing_head)

    url = "https://bit.ly/network-error"
    res1 = sandbox.analyze_url(url, expand=True, blacklist=frozenset())
    assert res1["expansion_error"] is not None
    assert res1["telemetry"]["cache_hit"] is False
    assert len(calls) == 1
    assert len(sandbox._ANALYSIS_CACHE) == 0

    res2 = sandbox.analyze_url(url, expand=True, blacklist=frozenset())
    assert res2["expansion_error"] is not None
    assert res2["telemetry"]["cache_hit"] is False
    assert len(calls) == 2
    assert len(sandbox._ANALYSIS_CACHE) == 0

    # Caso en que el doble devuelve una redirección con error (bucle cíclico sin lanzar)
    loop_calls = []

    def _loop_head(u: str, timeout: int = 3, **kwargs):
        loop_calls.append(u)
        return (301, "https://bit.ly/network-loop")

    monkeypatch.setattr(sandbox, "_head_request", _loop_head)
    loop_url = "https://bit.ly/network-loop"
    res_l1 = sandbox.analyze_url(loop_url, expand=True, blacklist=frozenset())
    assert res_l1["expansion_error"] == "Bucle de redirecciones"
    assert res_l1["telemetry"]["cache_hit"] is False
    assert len(loop_calls) == 1
    assert len(sandbox._ANALYSIS_CACHE) == 0

    res_l2 = sandbox.analyze_url(loop_url, expand=True, blacklist=frozenset())
    assert res_l2["expansion_error"] == "Bucle de redirecciones"
    assert res_l2["telemetry"]["cache_hit"] is False
    assert len(loop_calls) == 2
    assert len(sandbox._ANALYSIS_CACHE) == 0


def test_ttl_expiration_recalculates(monkeypatch):
    """Una entrada vence transcurrido el TTL y se recalcula volviendo a invocar la red."""
    fake_time = 1000.0
    monkeypatch.setattr(sandbox, "_now", lambda: fake_time)

    routes = {
        "https://bit.ly/ttl-test": (301, "https://example.org/final"),
        "https://example.org/final": (200, None),
    }
    head_mock, calls = _make_counting_head(routes)
    monkeypatch.setattr(sandbox, "_head_request", head_mock)

    url = "https://bit.ly/ttl-test"
    res1 = sandbox.analyze_url(url, expand=True, blacklist=frozenset())
    assert res1["telemetry"]["cache_hit"] is False
    first_count = len(calls)
    assert first_count > 0

    # Segunda llamada dentro del TTL: acierto de caché, conteo no aumenta
    res2 = sandbox.analyze_url(url, expand=True, blacklist=frozenset())
    assert res2["telemetry"]["cache_hit"] is True
    assert len(calls) == first_count

    # Avanzar el reloj simulado más allá del TTL
    fake_time += sandbox.ANALYSIS_CACHE_TTL + 1

    # Tercera llamada: vencida, se recalcula y vuelve a pedir HEAD
    res3 = sandbox.analyze_url(url, expand=True, blacklist=frozenset())
    assert res3["telemetry"]["cache_hit"] is False
    assert len(calls) == first_count * 2


def test_lru_cache_eviction_and_refresh():
    """_AnalysisCache expulsa la entrada menos reciente y una lectura get la refresca."""
    cache = sandbox._AnalysisCache(maxsize=2, ttl=60.0)
    cache.put("clave1", "valor1")
    cache.put("clave2", "valor2")
    assert len(cache) == 2

    # Leer clave1 la convierte en la más recientemente usada
    assert cache.get("clave1") == "valor1"

    # Insertar clave3 debe expulsar clave2 (la menos reciente)
    cache.put("clave3", "valor3")
    assert len(cache) == 2
    assert cache.get("clave2") is None
    assert cache.get("clave1") == "valor1"
    assert cache.get("clave3") == "valor3"


def test_distinct_cache_keys_separation(monkeypatch):
    """Parámetros expand y blacklist distintos generan entradas de caché independientes."""
    routes = {
        "https://bit.ly/sep": (301, "https://destino-seguro.com"),
        "https://destino-seguro.com": (200, None),
    }
    head_mock, _ = _make_counting_head(routes)
    monkeypatch.setattr(sandbox, "_head_request", head_mock)

    # Claves separadas según expand True vs False
    res_exp_t = sandbox.analyze_url("https://bit.ly/sep", expand=True, blacklist=frozenset())
    res_exp_f = sandbox.analyze_url("https://bit.ly/sep", expand=False, blacklist=frozenset())
    assert res_exp_t["telemetry"]["cache_hit"] is False
    assert res_exp_f["telemetry"]["cache_hit"] is False
    assert res_exp_t["expanded_url"] != res_exp_f["expanded_url"]

    # Ambas quedan cacheadas por separado
    assert sandbox.analyze_url("https://bit.ly/sep", expand=True, blacklist=frozenset())["telemetry"]["cache_hit"] is True
    assert sandbox.analyze_url("https://bit.ly/sep", expand=False, blacklist=frozenset())["telemetry"]["cache_hit"] is True

    # Claves separadas según blacklist: lista por defecto vs frozenset vacío vs personalizado
    # simit-multas-colombia.site está en la lista negra local por defecto
    target_domain = "simit-multas-colombia.site"
    res_default = sandbox.analyze_url(target_domain)
    assert res_default["verdict"] == "MALICIOSO"
    assert res_default["telemetry"]["cache_hit"] is False

    res_empty_bl = sandbox.analyze_url(target_domain, blacklist=frozenset())
    assert res_empty_bl["verdict"] == "SEGURO"
    assert res_empty_bl["telemetry"]["cache_hit"] is False

    res_custom_bl = sandbox.analyze_url(target_domain, blacklist=frozenset({"otro-dominio.com"}))
    assert res_custom_bl["verdict"] == "SEGURO"
    assert res_custom_bl["telemetry"]["cache_hit"] is False

    # Verificar que al reutilizarlas no se contaminan entre sí
    assert sandbox.analyze_url(target_domain)["verdict"] == "MALICIOSO"
    assert sandbox.analyze_url(target_domain)["telemetry"]["cache_hit"] is True

    assert sandbox.analyze_url(target_domain, blacklist=frozenset())["verdict"] == "SEGURO"
    assert sandbox.analyze_url(target_domain, blacklist=frozenset())["telemetry"]["cache_hit"] is True

    # set se convierte a frozenset y acierta en la entrada existente
    assert sandbox.analyze_url(target_domain, blacklist={"otro-dominio.com"})["telemetry"]["cache_hit"] is True


def test_non_string_and_oversized_inputs_not_cached():
    """Entradas que no son str o que superan MAX_URL_LEN devuelven error y nunca se guardan en caché."""
    bad_inputs = [None, 123, ["https://example.com"]]
    for bad in bad_inputs:
        res = sandbox.analyze_url(bad)
        assert res["status"] == "error"
        assert res["verdict"] == "NO_ANALIZADO"
        assert res["telemetry"]["cache_hit"] is False
        assert len(sandbox._ANALYSIS_CACHE) == 0

    # URL que supera MAX_URL_LEN
    long_url = "https://sitio-seguro.com/" + "x" * (sandbox.MAX_URL_LEN + 10)
    res_long1 = sandbox.analyze_url(long_url)
    assert res_long1["telemetry"]["cache_hit"] is False
    assert len(sandbox._ANALYSIS_CACHE) == 0

    res_long2 = sandbox.analyze_url(long_url)
    assert res_long2["telemetry"]["cache_hit"] is False
    assert len(sandbox._ANALYSIS_CACHE) == 0


def test_clear_analysis_cache_empties_state():
    """clear_analysis_cache vacía por completo las entradas de la caché global."""
    res1 = sandbox.analyze_url("https://example.com", blacklist=frozenset())
    assert res1["telemetry"]["cache_hit"] is False
    assert len(sandbox._ANALYSIS_CACHE) == 1

    sandbox.clear_analysis_cache()
    assert len(sandbox._ANALYSIS_CACHE) == 0

    res2 = sandbox.analyze_url("https://example.com", blacklist=frozenset())
    assert res2["telemetry"]["cache_hit"] is False
    assert len(sandbox._ANALYSIS_CACHE) == 1


def test_cache_concurrency_threadpool():
    """Llamadas concurrentes desde múltiples hilos sobre la misma URL no generan excepciones ni carreras."""
    url = "https://example.com/concurrent-test"
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(sandbox.analyze_url, url, blacklist=frozenset()) for _ in range(200)]
        results = [f.result() for f in futures]

    assert len(results) == 200
    baseline = {k: v for k, v in results[0].items() if k != "telemetry"}
    for r in results:
        assert {k: v for k, v in r.items() if k != "telemetry"} == baseline
        assert "cache_hit" in r["telemetry"]

    hits = sum(1 for r in results if r["telemetry"]["cache_hit"] is True)
    misses = sum(1 for r in results if r["telemetry"]["cache_hit"] is False)
    assert misses >= 1
    assert hits >= 1
    assert hits + misses == 200
