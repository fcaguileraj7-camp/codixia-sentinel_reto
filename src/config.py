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

def is_configured() -> bool:
    """Verifica si la llave del reto ha sido configurada correctamente."""
    return bool(RETO_API_KEY and RETO_API_KEY.startswith("pk_") and RETO_API_KEY != "pk_tu_llave_aqui")
