import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

RETO_API_KEY = os.getenv("RETO_API_KEY", "")
RETO_BASE_URL = os.getenv("RETO_BASE_URL", "https://api.reto.pltk.mx/v1")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4.7")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
# Modo de ejecución: "mock" (por defecto, $0 USD) o "live" (llamadas a la API real)
GROK_MODE = os.getenv("GROK_MODE", "mock").lower()

def is_configured() -> bool:
    """Verifica si la llave del reto ha sido configurada correctamente en .env."""
    return bool(RETO_API_KEY and RETO_API_KEY.startswith("pk_") and RETO_API_KEY != "pk_tu_llave_aqui")

def is_live_mode_enabled() -> bool:
    """
    Blindaje estructural del presupuesto (Requisito Hito 2):
    Retorna True SOLAMENTE si el modo live fue solicitado explícitamente y la llave es válida.
    Por defecto, las pruebas y ejecuciones locales operan en modo simulado para proteger el saldo.
    """
    if "PYTEST_CURRENT_TEST" in os.environ and os.getenv("GROK_FORCE_LIVE_TEST") != "1":
        return False
    return is_configured() and GROK_MODE in ["live", "real", "production"]
