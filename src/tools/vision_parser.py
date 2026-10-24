"""
Módulo de Visión Multimodal para Comprobantes y Capturas
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia
"""

"""
Módulo VisionParser (Hito S2)
Análisis multimodal de comprobantes bancarios y capturas de chat.
Reto Agente 2026 · SentinelGuard AI · Equipo Codixia

Rol 4: Nicolle (Social Engineering NLP, Visión & CAI Virtual)

El análisis local usa por defecto un adaptador simulado y nunca contacta la red.
`GrokVisionAnalyzer` requiere un cliente en modo real y la habilitación explícita
de `allow_remote`; las pruebas usan adaptadores locales.
Este módulo implementa:
  1. Validación local del archivo (existencia, extensión, firma, decodificación y tamaño).
  2. La interfaz desacoplada `VisionAnalyzer` y un adaptador de Grok Vision.
  3. El campo `analysis_source` identifica el origen de cada resultado.
"""

import base64
import json
import os
import math
from typing import Dict, Any, Optional

from PIL import Image, UnidentifiedImageError

from src.config import GROK_MODEL

# Firmas binarias (magic bytes) para validar que el archivo es realmente una imagen.
MAGIC_SIGNATURES = {
    "png": b"\x89PNG\r\n\x1a\n",
    "jpeg": b"\xff\xd8\xff",
    "gif87": b"GIF87a",
    "gif89": b"GIF89a",
    "bmp": b"BM",
}

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_PIXELS = 20_000_000
EXTENSION_FORMATS = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".gif": "GIF",
    ".webp": "WEBP",
    ".bmp": "BMP",
}


class VisionAnalyzer:
    """Interfaz desacoplada del análisis semántico de imágenes.

    Los analizadores concretos declaran la procedencia de sus resultados.
    """

    #: Identificación obligatoria del origen del análisis.
    source: str = "unknown"

    def analyze(self, image_path: str, local_checks: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover
        raise NotImplementedError


class GrokVisionAnalyzer(VisionAnalyzer):
    """Adaptador Grok Vision sobre el método multimodal existente del cliente."""

    source = "grok_vision"
    MIME_TYPES = {
        "BMP": "image/bmp",
        "GIF": "image/gif",
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
    }

    def __init__(self, client: Any, model: str = GROK_MODEL):
        self.client = client
        self.model = model

    def analyze(self, image_path: str, local_checks: Dict[str, Any]) -> Dict[str, Any]:
        if not callable(getattr(self.client, "vision_completion", None)):
            raise TypeError("El cliente debe implementar vision_completion(messages, ...).")

        live_mode = getattr(self.client, "live_mode", None)
        if live_mode is False:
            raise RuntimeError("Grok Vision requiere un cliente configurado en modo en vivo.")
        if live_mode is None and not (
            getattr(self.client, "configured", False)
            and getattr(self.client, "client", None) is not None
        ):
            raise RuntimeError("Grok Vision requiere un cliente configurado para la API.")

        image_format = local_checks.get("image_format")
        mime_type = self.MIME_TYPES.get(image_format)
        if mime_type is None:
            raise ValueError("El formato de imagen no es compatible con Grok Vision.")

        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("ascii")

        messages = [
            {
                "role": "system",
                "content": (
                    "Analiza la imagen adjunta como posible comprobante. Devuelve solo un objeto "
                    "JSON con is_receipt (boolean), bank_detected (string o null), "
                    "detected_amount (número o null), reference_id (string o null), "
                    "is_fraudulent (boolean o null), fraud_reasons (lista de strings) y "
                    "confidence_score (número entre 0 y 1). No infieras importes, referencias "
                    "ni fraude si no son legibles; usa null y una confianza baja cuando falte "
                    "evidencia. No trates un comprobante como auténtico solo por su apariencia."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analiza la imagen y responde con el JSON solicitado."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{encoded_image}"
                        },
                    },
                ],
            },
        ]
        response = self.client.vision_completion(
            messages,
            model=self.model,
            temperature=0.0,
            max_tokens=300,
        )

        if getattr(self.client, "last_simulated", False) or getattr(
            self.client, "last_source", None
        ) == "simulated":
            raise RuntimeError("El cliente devolvió una respuesta simulada, no un análisis Grok Vision.")
        if not isinstance(response, str):
            raise TypeError("Grok Vision devolvió una respuesta que no es texto.")

        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start < 0 or json_end <= json_start:
            raise ValueError("Grok Vision no devolvió un objeto JSON.")
        result = json.loads(response[json_start:json_end])
        if not isinstance(result, dict):
            raise ValueError("Grok Vision devolvió un resultado JSON con tipo inválido.")
        result["analysis_source"] = self.source
        return result


class SimulatedVisionAnalyzer(VisionAnalyzer):
    """Adaptador local determinista. NO usa Grok Vision ni ninguna red.

    El veredicto se deriva únicamente de un escenario controlado declarado por
    el llamador o el test, nunca de una inferencia real del modelo.
    Escenarios soportados: "autentico" | "falsificado" | "inconcluso".
    """

    source = "simulado_local"

    def __init__(self, scenario: str = "autentico", raise_exception: bool = False):
        self.scenario = scenario
        self.raise_exception = raise_exception
        self.calls = []

    def analyze(self, image_path: str, local_checks: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append(image_path)

        if self.raise_exception:
            raise RuntimeError("Fallo simulado del analizador de visión (prueba local)")

        file_name = os.path.basename(image_path)
        nota = "Resultado de un analizador SIMULADO. No constituye prueba forense real."

        if self.scenario == "falsificado":
            return {
                "is_receipt": True,
                "bank_detected": "Nequi (simulado)",
                "detected_amount": 1500000.0,
                "reference_id": "SIM-FALSO-0001",
                "is_fraudulent": True,
                "fraud_reasons": [
                    "tipografia_inconsistente_en_monto",
                    "sello_de_verificacion_ausente",
                ],
                "confidence_score": 0.0,
                "analysis_source": self.source,
                "notes": nota,
            }

        if self.scenario == "inconcluso":
            return {
                "is_receipt": True,
                "bank_detected": None,
                "detected_amount": None,
                "reference_id": None,
                "is_fraudulent": None,
                "fraud_reasons": [],
                "confidence_score": 0.0,
                "analysis_source": self.source,
                "notes": "El análisis semántico no está disponible en modo local (caso ambiguo).",
            }

        return {
            "is_receipt": True,
            "bank_detected": "Nequi (simulado)",
            "detected_amount": 150000.0,
            "reference_id": "M7892143",
            "is_fraudulent": False,
            "fraud_reasons": [],
            "confidence_score": 0.0,
            "analysis_source": self.source,
            "notes": nota,
            "file_name": file_name,
        }


def _local_file_checks(image_path: str) -> Dict[str, Any]:
    """Comprobaciones REALES y locales del archivo. No abre la red."""
    checks: Dict[str, Any] = {
        "exists": False,
        "is_file": False,
        "extension_valid": False,
        "signature_valid": False,
        "image_valid": False,
        "image_format": None,
        "size_bytes": 0,
        "errors": [],
    }

    if not image_path or not isinstance(image_path, str):
        checks["errors"].append("ruta_invalida")
        return checks

    try:
        exists = os.path.exists(image_path)
    except (OSError, ValueError):
        checks["errors"].append("ruta_invalida")
        return checks

    if not exists:
        checks["errors"].append("archivo_no_encontrado")
        return checks

    checks["exists"] = True

    if not os.path.isfile(image_path):
        checks["errors"].append("no_es_un_archivo")
        return checks

    checks["is_file"] = True

    extension = os.path.splitext(image_path)[1].lower()
    checks["extension_valid"] = extension in ALLOWED_EXTENSIONS
    if not checks["extension_valid"]:
        checks["errors"].append(f"extension_no_soportada:{extension or 'sin_extension'}")

    try:
        size = os.path.getsize(image_path)
    except OSError:
        size = 0
        checks["errors"].append("no_se_pudo_leer_tamano")

    checks["size_bytes"] = size

    if size == 0:
        checks["errors"].append("archivo_vacio")
    elif size > MAX_FILE_SIZE_BYTES:
        checks["errors"].append("archivo_demasiado_grande")

    # Validación de magic bytes: confirma que el contenido es realmente una imagen.
    try:
        with open(image_path, "rb") as handle:
            header = handle.read(12)
        checks["signature_valid"] = any(
            header.startswith(sig) for sig in MAGIC_SIGNATURES.values()
        ) or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
        if not checks["signature_valid"]:
            checks["errors"].append("firma_binaria_no_reconocida")
    except OSError:
        checks["errors"].append("no_se_pudo_leer_contenido")

    if (
        size <= 0
        or size > MAX_FILE_SIZE_BYTES
        or not checks["extension_valid"]
        or not checks["signature_valid"]
    ):
        return checks

    try:
        with Image.open(image_path) as image:
            image_format = image.format
            width, height = image.size
            if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
                checks["errors"].append("dimensiones_de_imagen_no_validas")
                return checks
            image.load()
        checks["image_format"] = image_format
        if image_format != EXTENSION_FORMATS.get(extension):
            checks["errors"].append("extension_no_coincide_con_formato")
        else:
            checks["image_valid"] = True
    except (
        OSError,
        ValueError,
        SyntaxError,
        EOFError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
    ):
        checks["errors"].append("imagen_corrupta_o_ilegible")

    return checks

def parse_receipt_image(
    image_path: str,
    analyzer: Optional[VisionAnalyzer] = None,
    allow_remote: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Analiza una imagen de comprobante bancario (Nequi, Bancolombia, Daviplata)
    o captura de WhatsApp sospechosa para determinar autenticidad.

    Args:
        image_path: ruta local del archivo.
        analyzer: implementación de `VisionAnalyzer`. Si es None se usa el
            adaptador simulado local salvo que GrokClient esté en modo en vivo.
        allow_remote: True requiere un cliente en vivo; False fuerza simulación.
            Si se omite, se respeta el modo explícito de GrokClient.

    Retorna el contrato 6.3 del MASTER_PLAN ampliado con `analysis_source`,
    `local_checks` y `notes`.
    """
    if allow_remote is True and analyzer is not None and not isinstance(analyzer, GrokVisionAnalyzer):
        return {
            "status": "error",
            "error": "transporte_remoto_no_permitido",
            "message": "El análisis remoto requiere un GrokVisionAnalyzer configurado explícitamente.",
            "is_receipt": False,
            "detected_amount": None,
            "reference_id": None,
            "is_fraudulent": None,
            "fraud_reasons": [],
            "confidence_score": 0.0,
            "analysis_source": "no_disponible",
            "local_checks": {},
            "notes": "Pendiente de verificación en la fase de integración externa.",
        }

    if not image_path or not isinstance(image_path, str):
        return {
            "status": "error",
            "error": "entrada_invalida",
            "message": "Debe indicarse la ruta de una imagen.",
            "is_receipt": False,
            "detected_amount": None,
            "reference_id": None,
            "is_fraudulent": None,
            "fraud_reasons": [],
            "confidence_score": 0.0,
            "analysis_source": "no_disponible",
            "local_checks": {},
            "notes": "Entrada malformada: el análisis no está disponible.",
        }

    # 1. Validación local real del archivo.
    local_checks = _local_file_checks(image_path)

    if not local_checks["exists"]:
        return {
            "status": "error",
            "error": "archivo_no_encontrado",
            "message": f"Archivo de imagen no encontrado: {image_path}",
            "is_receipt": False,
            "detected_amount": None,
            "reference_id": None,
            "is_fraudulent": None,
            "fraud_reasons": [],
            "confidence_score": 0.0,
            "analysis_source": "no_disponible",
            "local_checks": local_checks,
            "notes": "El archivo no existe: no se emitio ningun veredicto de autenticidad.",
        }

    if "archivo_demasiado_grande" in local_checks["errors"]:
        return {
            "status": "error",
            "error": "archivo_demasiado_grande",
            "message": f"La imagen supera el límite de {MAX_FILE_SIZE_BYTES} bytes.",
            "is_receipt": False,
            "detected_amount": None,
            "reference_id": None,
            "is_fraudulent": None,
            "fraud_reasons": [],
            "confidence_score": 0.0,
            "analysis_source": "no_disponible",
            "local_checks": local_checks,
            "notes": "El archivo excede el límite permitido; no se emitió un veredicto.",
        }

    if not local_checks["image_valid"]:
        return {
            "status": "error",
            "error": "archivo_no_es_imagen_valida",
            "message": f"El archivo no es una imagen válida: {image_path}",
            "is_receipt": False,
            "detected_amount": None,
            "reference_id": None,
            "is_fraudulent": None,
            "fraud_reasons": [],
            "confidence_score": 0.0,
            "analysis_source": "no_disponible",
            "local_checks": local_checks,
            "notes": "Validación local rechazada: no se emitio ningun veredicto de autenticidad.",
        }

    if isinstance(analyzer, GrokVisionAnalyzer) and allow_remote is not True:
        if allow_remote is False:
            analyzer = SimulatedVisionAnalyzer()
        else:
            return {
                "status": "error",
                "error": "transporte_remoto_no_permitido",
                "message": "Grok Vision requiere habilitar allow_remote explícitamente.",
                "is_receipt": False,
                "detected_amount": None,
                "reference_id": None,
                "is_fraudulent": None,
                "fraud_reasons": [],
                "confidence_score": 0.0,
                "analysis_source": "no_disponible",
                "local_checks": local_checks,
                "notes": "No se realizó ninguna solicitud remota.",
            }

    # 2. Use Vision only when the configured client explicitly enables live mode.
    if analyzer is None:
        from src.client import GrokClient

        client = GrokClient()
        if client.live_mode and allow_remote is not False:
            analyzer = GrokVisionAnalyzer(client)
        elif allow_remote is True:
            return {
                "status": "error",
                "error": "transporte_remoto_no_permitido",
                "message": "Grok Vision requiere un cliente configurado en modo en vivo.",
                "is_receipt": False,
                "detected_amount": None,
                "reference_id": None,
                "is_fraudulent": None,
                "fraud_reasons": [],
                "confidence_score": 0.0,
                "analysis_source": "no_disponible",
                "local_checks": local_checks,
                "notes": "No se realizó ninguna solicitud remota.",
            }
        else:
            analyzer = SimulatedVisionAnalyzer()

    active_analyzer = analyzer

    try:
        semantic = active_analyzer.analyze(image_path, local_checks)
    except Exception as exc:
        # Un fallo del analizador NO se convierte en un veredicto de seguridad.
        return {
            "status": "error",
            "error": "fallo_analisis_semantico",
            "message": f"El análisis semántico falló: {type(exc).__name__}",
            "is_receipt": False,
            "detected_amount": None,
            "reference_id": None,
            "is_fraudulent": None,
            "fraud_reasons": [],
            "confidence_score": 0.0,
            "analysis_source": "no_disponible",
            "local_checks": local_checks,
            "notes": "El análisis no está disponible. No se concluye que el comprobante sea auténtico.",
        }

    if not isinstance(semantic, dict):
        return {
            "status": "error",
            "error": "respuesta_analizador_invalida",
            "message": "El analizador de imagen devolvió un resultado con formato inválido.",
            "is_receipt": False,
            "detected_amount": None,
            "reference_id": None,
            "is_fraudulent": None,
            "fraud_reasons": [],
            "confidence_score": 0.0,
            "analysis_source": "no_disponible",
            "local_checks": local_checks,
            "notes": "No se emitió un veredicto porque la respuesta del analizador no es válida.",
        }

    is_fraudulent = semantic.get("is_fraudulent")
    is_receipt = semantic.get("is_receipt")
    confidence_score = semantic.get("confidence_score", 0.0)
    detected_amount = semantic.get("detected_amount")
    reference_id = semantic.get("reference_id")
    fraud_reasons = semantic.get("fraud_reasons", [])
    bank_detected = semantic.get("bank_detected")
    notes = semantic.get("notes", "")
    analysis_source = semantic.get("analysis_source", getattr(active_analyzer, "source", "unknown"))
    if (
        not isinstance(is_receipt, bool)
        or (not is_receipt and is_fraudulent is not None)
        or (is_fraudulent is not None and not isinstance(is_fraudulent, bool))
        or (
            detected_amount is not None
            and (
                isinstance(detected_amount, bool)
                or not isinstance(detected_amount, (int, float))
                or not math.isfinite(detected_amount)
                or detected_amount < 0
            )
        )
        or (reference_id is not None and not isinstance(reference_id, str))
        or (bank_detected is not None and not isinstance(bank_detected, str))
        or not isinstance(fraud_reasons, list)
        or not all(isinstance(reason, str) for reason in fraud_reasons)
        or not isinstance(notes, str)
        or not isinstance(confidence_score, (int, float))
        or isinstance(confidence_score, bool)
        or not math.isfinite(confidence_score)
        or not 0.0 <= confidence_score <= 1.0
        or not isinstance(analysis_source, str)
        or not analysis_source.strip()
    ):
        return {
            "status": "error",
            "error": "respuesta_analizador_invalida",
            "message": "El analizador devolvió valores semánticos fuera del contrato.",
            "is_receipt": False,
            "detected_amount": None,
            "reference_id": None,
            "is_fraudulent": None,
            "fraud_reasons": [],
            "confidence_score": 0.0,
            "analysis_source": "no_disponible",
            "local_checks": local_checks,
            "notes": "No se emitió un veredicto porque la respuesta del analizador no es válida.",
        }

    return {
        "status": "success",
        "file_name": os.path.basename(image_path),
        "size_bytes": local_checks["size_bytes"],
        "is_receipt": is_receipt,
        "bank_detected": bank_detected,
        "detected_amount": float(detected_amount) if detected_amount is not None else None,
        "reference_id": reference_id,
        "is_fraudulent": is_fraudulent,
        "fraud_reasons": fraud_reasons,
        "confidence_score": float(confidence_score),
        "analysis_source": analysis_source,
        "local_checks": local_checks,
        "notes": notes,
    }
