import logging
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.logging import RichHandler
from rich.console import Console

console = Console()

def setup_logger(name: str = "sentinel_guard") -> logging.Logger:
    """Configura un logger estructurado con soporte visual enriquecido."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True
        )
        formatter = logging.Formatter("%(message)s")
        rich_handler.setFormatter(formatter)
        logger.addHandler(rich_handler)
    return logger

logger = setup_logger()
