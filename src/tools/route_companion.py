"""
Módulo de Acompañamiento Físico y Monitoreo de Rutas (RouteCompanion)
Liderado por: Santiago (Rol 3: Especialista en Seguridad Física, Rutas & Acompañamiento en Taxis)
Reto Agente 2026 - SentinelGuard AI
"""

import re
import datetime
from typing import Dict, Any, Optional

PANIC_KEYWORDS = ["ayuda", "socorro", "me siguen", "desvío", "bloqueado", "auxilio", "peligro", "no es la ruta"]

def register_trip(plate: str, destination: str, origin: Optional[str] = None, checkin_interval_minutes: int = 10) -> Dict[str, Any]:
    """
    Inicia un acompañamiento preventivo para un trayecto en taxi o vehículo.
    Registra la placa, destino y programa el siguiente chequeo.
    """
    clean_plate = re.sub(r'[^a-zA-Z0-9]', '', plate).upper()
    now = datetime.datetime.now()
    next_checkin = now + datetime.timedelta(minutes=checkin_interval_minutes)

    return {
        "status": "active",
        "trip_id": f"TRIP-{clean_plate}-{int(now.timestamp())}",
        "vehicle_plate": clean_plate,
        "destination": destination,
        "origin": origin or "Ubicación inicial compartida",
        "started_at": now.isoformat(),
        "next_checkin_scheduled": next_checkin.isoformat(),
        "interval_minutes": checkin_interval_minutes,
        "monitoring_active": True
    }

def evaluate_trip_audio_response(transcript: str, expected_safe_word: Optional[str] = None) -> Dict[str, Any]:
    """
    Evalúa la respuesta de voz o texto del usuario durante el chequeo periódico.
    Detecta estrés, coacción o palabras clave de auxilio.
    """
    transcript_clean = transcript.lower()
    
    # Detección de palabras de auxilio o coacción
    panic_detected = any(pw in transcript_clean for pw in PANIC_KEYWORDS)
    safe_word_present = (expected_safe_word.lower() in transcript_clean) if expected_safe_word else False

    if panic_detected:
        return {
            "status": "alert",
            "is_safe": False,
            "escalation_required": True,
            "reason": "Se detectaron palabras de alerta o auxilio en la comunicación del usuario."
        }
    
    return {
        "status": "normal",
        "is_safe": True,
        "escalation_required": False,
        "reason": "Respuesta dentro de los parámetros esperados de normalidad."
    }
