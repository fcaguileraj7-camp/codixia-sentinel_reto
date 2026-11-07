import sys
import os

# Asegurar que la raíz del proyecto esté en sys.path para pruebas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import src.tools.url_sandbox as url_sandbox


@pytest.fixture(autouse=True)
def _clear_sandbox_cache():
    """Limpia la caché de análisis antes y después de cada test para aislar el estado."""
    url_sandbox.clear_analysis_cache()
    yield
    url_sandbox.clear_analysis_cache()


@pytest.fixture(autouse=True)
def _block_real_network(monkeypatch):
    """Los tests nunca hacen peticiones HEAD reales: el desenrollado de acortadores falla de forma controlada."""
    def _no_network(*args, **kwargs):
        raise OSError("red bloqueada en tests")
    monkeypatch.setattr("src.tools.url_sandbox._head_request", _no_network)
