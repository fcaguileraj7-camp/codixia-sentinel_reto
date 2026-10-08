"""
Pruebas Unitarias para PoliceReporter y VisionParser
Rol: Miguel (Multimodal Vision & Security Reporting)
"""

from src.tools.police_reporter import generate_police_report
from src.tools.vision_parser import parse_receipt_image

def test_generate_police_report():
    evidence = {
        "sender_phone": "+57 300 111 2233",
        "incident_type": "Extorsión Carcelaria",
        "user_input": "Pague 2 millones o le hacemos atentado",
        "risk_level": "CRÍTICO",
        "findings": ["Amenaza explícita", "Exigencia de dinero"],
        "detected_urls": []
    }
    report = generate_police_report(evidence)
    assert report["status"] == "success"
    assert "CAI-COL-" in report["report_id"]
    assert "EXPEDIENTE DE DENUNCIA DIGITAL" in report["formatted_markdown"]
    assert "+57 300 111 2233" in report["formatted_markdown"]

def test_parse_receipt_image_nonexistent():
    res = parse_receipt_image("ruta/falsa/no_existe.jpg")
    assert res["status"] == "error"
    assert res["is_receipt"] is False
