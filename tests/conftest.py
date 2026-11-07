import sys
import os

# Asegurar que la raíz del proyecto esté en sys.path para pruebas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest


@pytest.fixture(autouse=True)
def _block_real_network(monkeypatch):
    """Los tests nunca hacen peticiones HEAD reales: el desenrollado de acortadores falla de forma controlada."""
    def _no_network(*args, **kwargs):
        raise OSError("red bloqueada en tests")
    monkeypatch.setattr("src.tools.url_sandbox._head_request", _no_network)
