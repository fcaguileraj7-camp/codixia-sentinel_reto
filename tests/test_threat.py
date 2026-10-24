"""
Pruebas Unitarias para ThreatInspector
Rol: Nicolle (Social Engineering & NLP Specialist) · Hito S2

Todas las pruebas son locales, deterministas y de costo $0.00.
No se realizan llamadas de red ni se consumen créditos de API.
"""

import re

import pytest

from src.tools.threat_inspector import (
    inspect_threat,
    THREAT_VECTORS,
    SUSPICIOUS_KEYWORDS,
)

def test_inspect_legitimate_message():
    message = "Hola mamá, ¿cómo estás? Ya voy saliendo del trabajo."
    result = inspect_threat(message)
    assert result["status"] == "success"
    assert result["threat_level"] == "BAJO"
    assert result["risk_score"] < 30

def test_inspect_bancolombia_phishing():
    message = "Bancolombia informa: Su cuenta ha sido bloqueada. Urgente ingrese a http://banc0lombia-alerta.cc para evitar suspensión."
    result = inspect_threat(message)
    assert result["status"] == "success"
    assert result["threat_level"] in ["MEDIO", "CRÍTICO"]
    assert len(result["suspicious_urls"]) > 0
    assert result["risk_score"] >= 40


# ---------------------------------------------------------------------------
# Casos legítimos adicionales (control de falsos positivos)
# ---------------------------------------------------------------------------

def test_legitimate_bank_notification_is_not_flagged():
    """Una notificación real del banco no debe confundirse con phishing."""
    message = (
        "Bancolombia le informa que su pago por $45.000 en Supermercado Éxito "
        "fue exitoso. Si no reconoce esta transacción comuníquese a la línea de "
        "atención oficial 018000912345."
    )
    result = inspect_threat(message)
    assert result["threat_level"] == "BAJO"
    assert result["risk_score"] < 20


def test_legitimate_whatsapp_code_is_not_flagged():
    """El propio WhatsApp avisa que el código es secreto: no es una estafa."""
    message = "Tu código de verificación de WhatsApp es 849-204. No compartas este código con nadie."
    result = inspect_threat(message)
    assert result["threat_level"] == "BAJO"


def test_legitimate_work_meeting_is_not_flagged():
    message = "Hola Juan, recuerda que mañana tenemos la reunión de planeación del sprint a las 9:00 AM."
    result = inspect_threat(message)
    assert result["threat_level"] == "BAJO"
    assert result["is_ambiguous"] is True


# ---------------------------------------------------------------------------
# Phishing: contrato 6.1 del MASTER_PLAN
# ---------------------------------------------------------------------------

def test_phishing_reports_vectors_and_contract_fields():
    """Verifica los campos exigidos por el contrato 6.1 del MASTER_PLAN."""
    message = (
        "Bancolombia: su cuenta ha sido bloqueada. Ingrese de inmediato a "
        "https://banc0lombia-seguridad.cc/login para desbloquearla."
    )
    result = inspect_threat(message)

    # Campos del contrato 6.1
    assert "detected_vectors" in result
    assert "matched_keywords" in result
    assert isinstance(result["detected_vectors"], list)
    assert len(result["detected_vectors"]) > 0

    # Vectores esperados en un phishing bancario clásico
    assert "amenaza_bloqueo" in result["detected_vectors"]
    assert "falsa_autoridad_bancaria" in result["detected_vectors"]
    assert "dominio_enganoso" in result["detected_vectors"]

    # Compatibilidad hacia atrás con el contrato del Hito S1
    assert "matched_triggers" in result
    assert len(result["matched_triggers"]) > 0


def test_official_domain_url_is_not_suspicious():
    message = "Ingrese a https://www.bancolombia.com/personas para ver su extracto."
    result = inspect_threat(message)
    assert result["suspicious_urls"] == []
    assert any("dominio oficial" in f for f in result["findings"])


def test_brand_in_url_path_does_not_make_host_official():
    result = inspect_threat("Consulte https://evil.example/bancolombia.com")
    assert result["suspicious_urls"] == ["https://evil.example/bancolombia.com"]
    assert not any("dominio oficial" in finding for finding in result["findings"])


def test_legitimate_bank_brand_mention_is_not_an_impersonation_vector():
    result = inspect_threat("Bancolombia es el banco que uso para recibir mi nómina.")
    assert "falsa_autoridad_bancaria" not in result["detected_vectors"]
    assert result["threat_level"] == "BAJO"


# ---------------------------------------------------------------------------
# Urgencia artificial
# ---------------------------------------------------------------------------

def test_inspect_urgency_triggers():
    message = "Urgente, inmediato haga clic para evitar embargo y orden de captura."
    result = inspect_threat(message)
    assert result["status"] == "success"
    assert len(result["matched_triggers"]) > 0
    assert "urgencia_artificial" in result["detected_vectors"]


def test_urgency_with_deadline_escalates_risk():
    """La presión por plazo (menos de 1 hora) debe elevar el riesgo."""
    message = "Tiene 2 horas para confirmar o su cuenta será cerrada definitivamente."
    result = inspect_threat(message)
    assert "urgencia_artificial" in result["detected_vectors"]
    assert result["risk_score"] >= 15


def test_neutral_transfer_delay_is_not_flagged_as_artificial_urgency():
    result = inspect_threat(
        "La transferencia puede tardar 2 horas en reflejarse; no tienes que hacer nada."
    )
    assert "urgencia_artificial" not in result["detected_vectors"]


def test_inspect_urgency_triggers():
    message = "Urgente, inmediato haga clic para evitar embargo y orden de captura."
    result = inspect_threat(message)
    assert result["status"] == "success"
    assert len(result["matched_triggers"]) > 0

# ---------------------------------------------------------------------------
# Posible extorsión (carcelaria, sextorsión, falsa autoridad estatal)
# ---------------------------------------------------------------------------

def test_jail_extortion_pattern():
    message = (
        "Hablamos del Frente Urbano. Tenemos ubicado a usted y a su negocio en "
        "Bucaramanga. Si no nos colabora con 2 millones antes del mediodía por "
        "Nequi al 3124567890, aténgase a las consecuencias."
    )
    result = inspect_threat(message)
    assert "extorsion_carcelaria" in result["detected_vectors"]
    assert result["threat_level"] == "CRÍTICO"


def test_sextortion_pattern():
    message = (
        "Tengo grabaciones íntimas de su cámara web. Si no me transfiere 0.05 "
        "Bitcoin a esta billetera en 24 horas, enviaré el video a todos sus "
        "contactos de Facebook y trabajo."
    )
    result = inspect_threat(message)
    assert "sextorsion" in result["detected_vectors"]
    assert result["threat_level"] == "CRÍTICO"


def test_fake_judicial_order_pattern():
    message = (
        "DIAN NOTIFICACIÓN JUDICIAL: Tiene un mandamiento de pago pendiente y "
        "orden de embargo sobre sus cuentas. Descargue el expediente en "
        "https://dian-notificaciones.xyz/expediente"
    )
    result = inspect_threat(message)
    assert "falsa_autoridad_estatal" in result["detected_vectors"]
    assert result["threat_level"] in ["ALTO", "CRÍTICO"]


def test_family_impersonation_pattern():
    message = (
        "Hola tío, cambié de número porque me robaron en el aeropuerto. Tengo "
        "las maletas retenidas en la aduana y necesito que me consigne 450 mil "
        "a este Daviplata."
    )
    result = inspect_threat(message)
    assert "suplantacion_familiar" in result["detected_vectors"]
    assert result["threat_level"] == "CRÍTICO"


def test_marketplace_fake_receipt_requires_converging_indicators():
    message = (
        "Ya le hice la transferencia y le mandé el pantallazo del comprobante. "
        "Mándelos ya en Uber; en la app aparece en 24 horas por ser interbancario."
    )
    result = inspect_threat(message)
    assert "fraude_comprobante_marketplace" in result["detected_vectors"]
    assert result["threat_level"] == "ALTO"


def test_marketplace_receipt_without_delivery_pressure_is_not_escalated():
    message = (
        "Ya envié el comprobante de la transferencia. La plataforma indica "
        "que puede tardar 24 horas; no envíes el producto hasta confirmar."
    )
    result = inspect_threat(message)
    assert "fraude_comprobante_marketplace" not in result["detected_vectors"]


def test_credential_request_with_urgency_and_account_suspension_is_critical():
    message = (
        "WhatsApp Soporte: Para evitar la suspensión de su cuenta, comparta "
        "de inmediato el código de seguridad de 6 dígitos que recibió por SMS."
    )
    result = inspect_threat(message)
    assert "solicitud_credenciales" in result["detected_vectors"]
    assert "amenaza_bloqueo" in result["detected_vectors"]
    assert result["threat_level"] == "CRÍTICO"


def test_armed_false_service_extortion_is_critical():
    message = (
        "La zona está rodeada por el frente armado y tenemos interceptadas sus "
        "comunicaciones. Si no transfiera 3 millones urgente, no sale de la zona."
    )
    result = inspect_threat(message)
    assert "extorsion_carcelaria" in result["detected_vectors"]
    assert result["threat_level"] == "CRÍTICO"


# ---------------------------------------------------------------------------
# Caso ambiguo
# ---------------------------------------------------------------------------

def test_ambiguous_message_is_flagged_as_ambiguous():
    result = inspect_threat("Hola, ¿me puedes escribir luego?")
    assert result["status"] == "success"
    assert result["is_ambiguous"] is True
    assert result["threat_level"] == "BAJO"


def test_empty_input_does_not_yield_confident_verdict():
    """Una entrada vacía NO debe tratarse como 'analizada y segura'."""
    result = inspect_threat("")
    assert result["status"] == "success"
    assert result["threat_level"] == "BAJO"
    assert result["is_ambiguous"] is True
    assert result["detected_vectors"] == []


# ---------------------------------------------------------------------------
# Entradas malformadas
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_input", [None, 123, [], {}, 4.5, object()])
def test_non_string_input_returns_error(bad_input):
    """Entradas no textuales: error explícito, jamás un veredicto de seguridad."""
    result = inspect_threat(bad_input)
    assert result["status"] == "error"
    assert result["error"] == "entrada_invalida"
    assert result["threat_level"] == "NO_ANALIZADO"
    assert result["risk_score"] == 0


def test_massive_emoji_input_does_not_crash():
    """Robustez contra textos con emojis masivos (requisito S4 de Nicolle)."""
    message = "🎉" * 5000 + " urgencia en su cuenta " + "🔥" * 3000
    result = inspect_threat(message)
    assert result["status"] == "success"
    assert "urgencia_artificial" in result["detected_vectors"]


def test_control_characters_do_not_crash():
    """Robustez contra caracteres nulos y de control."""
    message = "Hola\x00\x00 su cuenta está bloqueada \x07\x1b[31m urgente"
    result = inspect_threat(message)
    assert result["status"] == "success"
    assert "amenaza_bloqueo" in result["detected_vectors"]


# ---------------------------------------------------------------------------
# Determinismo e integridad del catálogo
# ---------------------------------------------------------------------------

def test_analysis_is_deterministic():
    message = "Bancolombia: cuenta bloqueada, ingrese urgente a http://banc0lombia.cc"
    first = inspect_threat(message)
    second = inspect_threat(message)
    assert first == second


def test_all_threat_vector_patterns_are_valid_regex():
    """Todo patrón declarado debe compilar: evita fallos silenciosos."""
    for name, spec in THREAT_VECTORS.items():
        assert isinstance(spec["peso"], int), f"{name} debe declarar un peso entero"
        assert spec["patrones"], f"{name} debe declarar patrones"
        for pattern in spec["patrones"]:
            re.compile(pattern)


def test_legacy_keywords_are_preserved():
    """El catálogo heredado del S1 debe conservarse para compatibilidad."""
    assert "bloqueada" in SUSPICIOUS_KEYWORDS
    assert "urgente" in SUSPICIOUS_KEYWORDS


# ---------------------------------------------------------------------------
# Cumplimiento del contrato 6.1 del MASTER_PLAN
# ---------------------------------------------------------------------------

def test_inspect_threat_fulfills_contract_6_1():
    """El resultado debe contener todos los campos del contrato 6.1."""
    expected_fields = [
        "status",
        "threat_level",
        "risk_score",
        "detected_vectors",
        "matched_keywords",
        "findings",
        "recommendation",
    ]
    result = inspect_threat("Bancolombia: cuenta bloqueada, ingrese urgente a http://banc0lombia.cc")

    for field in expected_fields:
        assert field in result, f"Falta el campo obligatorio del contrato 6.1: {field}"

    assert isinstance(result["detected_vectors"], list)
    assert isinstance(result["matched_keywords"], list)
    assert isinstance(result["findings"], list)
    assert isinstance(result["risk_score"], int)
    assert 0 <= result["risk_score"] <= 100


def test_contract_6_1_is_also_fulfilled_on_error():
    """El contrato debe respetarse incluso cuando la entrada es inválida."""
    expected_fields = [
        "status",
        "threat_level",
        "risk_score",
        "detected_vectors",
        "matched_keywords",
        "findings",
        "recommendation",
    ]
    result = inspect_threat(None)

    assert result["status"] == "error"
    for field in expected_fields:
        assert field in result, f"Falta el campo del contrato 6.1 en la rama de error: {field}"


def test_all_four_threat_levels_are_reachable():
    """El contrato 6.1 declara BAJO, MEDIO, ALTO y CRÍTICO: los cuatro deben existir."""
    niveles = set()

    # BAJO: mensaje cotidiano
    niveles.add(inspect_threat("Hola, nos vemos mañana en la oficina")["threat_level"])
    # MEDIO / ALTO / CRÍTICO: escalado por número de vectores concurrentes
    niveles.add(inspect_threat("Su cuenta fue suspendida por actividad inusual")["threat_level"])
    niveles.add(
        inspect_threat(
            "Mensaje urgente: revise este enlace https://example.test"
        )["threat_level"]
    )
    niveles.add(
        inspect_threat(
            "Hablamos del Frente Urbano. Tenemos ubicado su negocio. Si no nos "
            "colabora con 2 millones, aténgase a las consecuencias."
        )["threat_level"]
    )

    assert {"BAJO", "MEDIO", "ALTO", "CRÍTICO"} <= niveles, (
        f"Niveles alcanzados: {sorted(niveles)}. El contrato 6.1 exige los cuatro."
    )


@pytest.mark.parametrize(
    "message,expected_level",
    [
        (
            "Amazon Colombia está contratando personal para trabajar desde casa 2 horas al día ganando hasta $350.000 diarios. Para postularte y activar tu cuenta deposita $50.000 en https://trabajo-amazon-latam.top",
            "ALTO",
        ),
        (
            "¡Felicidades! Tu número fue seleccionado en el sorteo de Claro y Éxito para ganar una Toyota Prado 2026 y 50 millones. Comunícate al 3209876543 con el Dr. Carlos Mario para reclamar tu premio.",
            "ALTO",
        ),
        (
            "Servientrega: Su envío nacional #CO-928172 presenta dirección incompleta y está retenido. Ingrese de inmediato a https://servientrega-entregas-colombia.site/rastreo para que actualice sus datos y liquide el flete pendiente.",
            "ALTO",
        ),
        (
            "Prosperidad Social: Beneficiario prioritario del giro extraordinario de $500.000 de Renta Ciudadana. Ingrese urgente y actualice sus datos con su cédula en https://subsidios-prosperidadsocial.xyz para autorizar el desembolso.",
            "ALTO",
        ),
        (
            "Préstamos Ya Colombia: Su crédito preaprobado por $2.500.000 está listo sin codeudor ni historial crediticio. Ingrese urgente a https://prestamos-facil-colombia.site/desembolso para recibir el dinero de inmediato en su cuenta.",
            "ALTO",
        ),
    ],
)
def test_case_heuristics_match_expected_severity(message, expected_level):
    result = inspect_threat(message)
    assert result["threat_level"] == expected_level


def test_physical_panic_message_is_not_classified_as_digital_fraud():
    message = (
        "Voy en el taxi placa TRL-981 hacia Suba, pero el conductor se desvió por una trocha oscura, "
        "apagó las luces y no me responde. Es urgente, auxilio inmediato por favor."
    )
    result = inspect_threat(message)
    assert result["threat_level"] == "BAJO"
    assert "urgencia_artificial" not in result["detected_vectors"]
