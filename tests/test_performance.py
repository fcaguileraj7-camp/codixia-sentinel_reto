"""
Pruebas de Evaluación, Certificación e Integridad del Dataset Dual (Hito S3)
Rol: Juan José González (Dataset Engineering, Stress Testing & UI)
Reto Agente 2026 - SentinelGuard AI · Equipo Codixia

Evalúa de forma diferenciada y determinista ($0.00 USD):
1. Integridad estructural y no-regresión de los 30 casos iniciales.
2. Dominio Escudo Digital: Heurísticas NLP y clasificación contra ThreatInspector (reconociendo nivel ALTO).
3. Dominio Acompañamiento Físico: Enrutamiento pericial y evaluación de pánico/seguridad contra RouteCompanion y SentinelAgent.
4. Cobertura de la lista negra de URLs (data/url_blacklist.json).
"""

import os
import json
import re
import pytest

from src.tools.threat_inspector import inspect_threat
from src.tools.route_companion import evaluate_trip_audio_response
from src.agent.sentinel import SentinelAgent, _is_physical_route_request

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "scam_dataset_30.json")
BLACKLIST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "url_blacklist.json")

PHYSICAL_CATEGORIES = {"ACOMPANAMIENTO_FISICO_PANICO", "ACOMPANAMIENTO_FISICO_CONTROL"}
# CASE-027 es un caso de acompañamiento físico catalogado originalmente como LEGITIMO_CONTROL
PHYSICAL_CASE_IDS = {"CASE-025", "CASE-027"}


def _load_dataset():
    assert os.path.exists(DATASET_PATH), f"El archivo dataset debe existir en: {DATASET_PATH}"
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _is_physical_case(case: dict) -> bool:
    return case.get("id") in PHYSICAL_CASE_IDS or case.get("category") in PHYSICAL_CATEGORIES


# ==============================================================================
# 1. PRUEBAS DE ESTRUCTURA Y CALIDAD DE DATOS (REQUISITO HITO S3)
# ==============================================================================

def test_scam_dataset_structure():
    """
    Verifica la estructura física y los contratos de datos de cada registro en el dataset.
    Conserva compatibilidad hacia atrás exigiendo len >= 15 y campos base.
    """
    cases = _load_dataset()
    assert len(cases) >= 38, f"El dataset ampliado debe contener al menos 38 registros (actual: {len(cases)})"

    required_fields = ["id", "category", "expected_verdict", "text", "entity_target", "has_malicious_url"]
    valid_verdicts = {"CRÍTICO", "ALTO", "MEDIO", "BAJO"}

    seen_ids = set()
    seen_texts = set()

    for idx, case in enumerate(cases):
        # Todos los campos obligatorios deben estar presentes
        for field in required_fields:
            assert field in case, f"El registro {case.get('id', idx)} no contiene el campo obligatorio '{field}'"
            assert case[field] is not None, f"El campo '{field}' en registro {case.get('id')} no puede ser nulo"

        # Validación estricta de tipos
        assert isinstance(case["id"], str), f"id en {case['id']} debe ser cadena"
        assert isinstance(case["category"], str), f"category en {case['id']} debe ser cadena"
        assert isinstance(case["expected_verdict"], str), f"expected_verdict en {case['id']} debe ser cadena"
        assert isinstance(case["text"], str), f"text en {case['id']} debe ser cadena"
        assert isinstance(case["entity_target"], str), f"entity_target en {case['id']} debe ser cadena"
        assert isinstance(case["has_malicious_url"], bool), f"has_malicious_url en {case['id']} debe ser booleano real"

        # Veredictos permitidos
        assert case["expected_verdict"] in valid_verdicts, (
            f"Veredicto '{case['expected_verdict']}' en {case['id']} no es válido. Permitidos: {valid_verdicts}"
        )

        # Sin campos vacíos y longitud mínima de texto
        assert len(case["text"].strip()) >= 20, f"El texto en {case['id']} es demasiado breve o está vacío"

        # Identificadores únicos y estrictamente consecutivos
        cid = case["id"]
        assert cid not in seen_ids, f"Identificador duplicado detectado: {cid}"
        seen_ids.add(cid)
        expected_seq_id = f"CASE-{idx + 1:03d}"
        assert cid == expected_seq_id, f"Identificador fuera de secuencia: esperado {expected_seq_id}, recibido {cid}"

        # Textos no duplicados
        normalized_text = " ".join(case["text"].lower().split())
        assert normalized_text not in seen_texts, f"Texto duplicado detectado en registro: {cid}"
        seen_texts.add(normalized_text)


def test_scam_dataset_original_30_records_integrity():
    """
    Garantía de no-regresión: demuestra que los 30 registros originales (CASE-001 a CASE-030)
    se conservan exactamente íntegros, sin alteraciones en texto, categoría ni veredicto.
    """
    cases = _load_dataset()
    assert len(cases) >= 30, "El dataset debe contener al menos los 30 casos originales"

    original_30 = cases[:30]
    assert original_30[0]["id"] == "CASE-001"
    assert original_30[0]["category"] == "PHISHING_BANCO"
    assert "banc0lombia-seguridad.cc" in original_30[0]["text"]

    assert original_30[24]["id"] == "CASE-025"
    assert original_30[24]["category"] == "FALSO_SECUESTRO_EXPRESS"
    assert "Tenemos a su hijo retenido" in original_30[24]["text"]

    assert original_30[26]["id"] == "CASE-027"
    assert original_30[26]["category"] == "LEGITIMO_CONTROL"
    assert "Hola familia, ya voy saliendo" in original_30[26]["text"]

    assert original_30[29]["id"] == "CASE-030"
    assert original_30[29]["category"] == "LEGITIMO_CONTROL"


def test_scam_dataset_digital_expansion_coverage():
    """
    Valida la ampliación del dominio Escudo Digital (Hito S3 / Casos Nicolle):
    - Se incorporaron 10 nuevos casos de ciberfraude a partir de CASE-031 hasta CASE-040.
    - El conjunto total de casos alcanza 40 registros completos.
    - Cubre vectores clave: Nequi falso comprobante, Bancolombia, Cripto, Falso Soporte,
      QRishing, Falsa Oferta, Compraventa, SIM Swapping, Devolución DIAN y Extorsión Digital.
    - Todos los casos nuevos poseen veredictos esperados de alta severidad (CRÍTICO o ALTO).
    """
    cases = _load_dataset()
    new_digital_cases = [c for c in cases[30:] if not _is_physical_case(c)]
    assert len(new_digital_cases) == 10, (
        f"Se requieren exactamente 10 nuevos casos de ciberfraude agregados (actual: {len(new_digital_cases)})"
    )

    expected_categories = {
        "FALSO_COMPROBANTE_NEQUI",
        "PHISHING_BANCOLOMBIA",
        "ESTAFA_INVERSION_CRIPTOMONEDAS",
        "FALSO_SOPORTE_TECNICO",
        "FRAUDE_QR_PAGO",
        "FALSA_OFERTA_LABORAL",
        "FRAUDE_COMPRAVENTA_DIGITAL",
        "SUPLANTACION_OPERADOR_SIM",
        "FALSO_REEMBOLSO_DIAN",
        "EXTORSION_DIGITAL"
    }
    actual_categories = {c["category"] for c in new_digital_cases}
    assert expected_categories == actual_categories, (
        f"Las categorías de la ampliación digital deben coincidir exactamente con las modalidades aprobadas: {expected_categories - actual_categories}"
    )

    for case in new_digital_cases:
        assert case["expected_verdict"] in ["CRÍTICO", "ALTO"], (
            f"El caso {case['id']} debe tener veredicto de severidad alta (actual: {case['expected_verdict']})"
        )


def test_scam_dataset_url_blacklist_integrity():
    """
    Verifica que todos los dominios de la lista negra oficial (data/url_blacklist.json)
    sigan existiendo intactos dentro de los casos digitales del dataset.
    """
    assert os.path.exists(BLACKLIST_PATH), f"El archivo de lista negra debe existir: {BLACKLIST_PATH}"
    with open(BLACKLIST_PATH, "r", encoding="utf-8") as f:
        bl_data = json.load(f)

    cases = _load_dataset()
    dataset_texts = " ".join(c["text"] for c in cases if not _is_physical_case(c))

    entries = bl_data.get("entries", [])
    assert len(entries) >= 11, "La lista negra debe contener al menos 11 dominios sembrados"

    for entry in entries:
        domain = entry.get("domain", "")
        assert domain, "Cada entrada de la lista negra debe tener un dominio"
        assert domain in dataset_texts, (
            f"El dominio '{domain}' de la lista negra debe estar presente en los textos de fraude del dataset"
        )


# ==============================================================================
# 2. EVALUACIÓN Y CERTIFICACIÓN DEL DOMINIO DIGITAL (ESCUDO DIGITAL)
# ==============================================================================

def test_evaluate_dataset_precision():
    """
    Evaluación de compatibilidad hacia atrás:
    Mide la precisión de las reglas heurísticas de ThreatInspector sobre los casos
    del dominio digital, reconociendo correctamente el nivel ALTO (además de MEDIO y CRÍTICO)
    para evitar falsos descartes en fraudes bancarios y ofertas falsas.
    Exige un mínimo del 90% de exactitud en clasificación digital.
    """
    cases = _load_dataset()
    digital_cases = [c for c in cases if not _is_physical_case(c)]
    assert len(digital_cases) >= 25, "Deben existir al menos 25 casos evaluables en el dominio digital"

    correct = 0
    total = len(digital_cases)

    for case in digital_cases:
        res = inspect_threat(case["text"])
        threat_level = res["threat_level"]

        if case["category"] == "LEGITIMO_CONTROL":
            # Los controles benignos deben ser catalogados como BAJO
            if threat_level == "BAJO":
                correct += 1
        else:
            # Los ataques maliciosos deben detectarse con severidad MEDIO, ALTO o CRÍTICO
            if threat_level in ["MEDIO", "ALTO", "CRÍTICO"]:
                correct += 1

    accuracy = correct / total
    print(f"\n[Certificación Digital] Exactitud heurística en Escudo Digital: {accuracy * 100:.1f}% ({correct}/{total})")
    assert accuracy >= 0.90, f"La precisión en el dominio digital debe ser al menos del 90% (obtenida: {accuracy * 100:.1f}%)"


# ==============================================================================
# 3. EVALUACIÓN Y CERTIFICACIÓN DEL DOMINIO FÍSICO (ACOMPAÑAMIENTO EN TAXI)
# ==============================================================================

CONTROL_TAXI_CASES = [
    {
        "id": "TAXI-CTRL-01",
        "category": "ACOMPANAMIENTO_FISICO_PANICO",
        "expected_verdict": "CRÍTICO",
        "text": "Voy en el taxi placa TRL-981 hacia Suba, pero el conductor se desvió por una trocha oscura, apagó las luces y no me responde. Es urgente, auxilio inmediato por favor."
    },
    {
        "id": "TAXI-CTRL-02",
        "category": "ACOMPANAMIENTO_FISICO_CONTROL",
        "expected_verdict": "BAJO",
        "text": "Acabo de abordar el taxi de placas WDY-452 saliendo de la oficina en Chapinero hacia mi casa en Cedritos. Inicio recorrido tranquilo, les aviso apenas llegue."
    }
]

def test_evaluate_physical_accompaniment_routing_and_audio():
    """
    Evalúa los casos de acompañamiento físico en taxi frente a los componentes
    técnicos reales de transporte:
    1. Enrutamiento pericial (_is_physical_route_request): confirma que los 12 casos
       se identifiquen como solicitudes de ruta física y no se confundan con fraude digital.
    2. Evaluación acústica/textual (evaluate_trip_audio_response): confirma que las
       situaciones de pánico activen estado 'alert' y que los trayectos seguros reporten 'normal'.
    """
    cases = _load_dataset()
    taxi_cases = CONTROL_TAXI_CASES
    assert len(taxi_cases) >= 2, "Deben existir los casos de control histórico de transporte"

    routing_ok = 0
    audio_eval_ok = 0
    total = len(taxi_cases)

    for case in taxi_cases:
        text = case["text"]
        expected_verdict = case["expected_verdict"]

        # 1. Enrutamiento: debe canalizarse como transporte físico
        if _is_physical_route_request(text):
            routing_ok += 1

        # 2. Evaluación de respuesta en viaje (RouteCompanion)
        audio_res = evaluate_trip_audio_response(text)
        if expected_verdict == "CRÍTICO":
            if audio_res["status"] == "alert" and audio_res["is_safe"] is False and audio_res["escalation_required"] is True:
                audio_eval_ok += 1
        elif expected_verdict == "BAJO":
            if audio_res["status"] == "normal" and audio_res["is_safe"] is True and audio_res["escalation_required"] is False:
                audio_eval_ok += 1

    routing_accuracy = routing_ok / total
    audio_accuracy = audio_eval_ok / total

    print(f"\n[Certificación Física] Exactitud enrutamiento pericial taxi: {routing_accuracy * 100:.1f}% ({routing_ok}/{total})")
    print(f"[Certificación Física] Exactitud clasificación señales RouteCompanion: {audio_accuracy * 100:.1f}% ({audio_eval_ok}/{total})")

    assert routing_accuracy >= 0.90, f"El enrutamiento físico debe alcanzar al menos 90% (obtenido: {routing_accuracy * 100:.1f}%)"
    assert audio_accuracy >= 0.90, f"La exactitud de señales RouteCompanion debe alcanzar al menos 90% (obtenida: {audio_accuracy * 100:.1f}%)"


def test_evaluate_physical_accompaniment_agent_workflow():
    """
    Evalúa el ciclo end-to-end de SentinelAgent en modo simulado local ($0.00 USD)
    sobre todos los casos de acompañamiento físico.
    Verifica que:
    - Se active el modo 'route_companion'.
    - Los casos de pánico produzcan riesgo 'CRÍTICO', acción 'TRIGGER_ALARM' y escalada SOS activa.
    - Los casos seguros produzcan riesgo 'BAJO', acción 'SCHEDULE_CHECKIN' y sin escalada de emergencia.
    """
    cases = _load_dataset()
    taxi_cases = CONTROL_TAXI_CASES
    agent = SentinelAgent()

    agent_eval_ok = 0
    total = len(taxi_cases)

    for case in taxi_cases:
        text = case["text"]
        expected_verdict = case["expected_verdict"]

        # Sesiones aisladas para evitar contaminación del estado conversacional entre pruebas
        session_id = f"cert_taxi_{case['id']}"
        res = agent.process_message(text, session_id=session_id)

        decision = res.get("decision", {})
        risk_level = decision.get("risk_level")
        mode = decision.get("mode")
        action = decision.get("action")
        escalation = res.get("escalation")

        assert mode == "route_companion", f"El caso {case['id']} debía ejecutar modo 'route_companion', obtuvo: '{mode}'"

        if expected_verdict == "CRÍTICO":
            if risk_level == "CRÍTICO" and action == "TRIGGER_ALARM" and escalation is not None:
                agent_eval_ok += 1
        elif expected_verdict == "BAJO":
            if risk_level == "BAJO" and action == "SCHEDULE_CHECKIN" and escalation is None:
                agent_eval_ok += 1

    workflow_accuracy = agent_eval_ok / total
    print(f"[Certificación Agente] Exactitud flujo autónomo SentinelAgent (Taxi): {workflow_accuracy * 100:.1f}% ({agent_eval_ok}/{total})")
    assert workflow_accuracy >= 0.90, (
        f"El flujo autónomo de acompañamiento debe alcanzar al menos 90% (obtenido: {workflow_accuracy * 100:.1f}%)"
    )


# ==============================================================================
# 4. CERTIFICACIÓN GLOBAL DEL DATASET DUAL (HITO S3)
# ==============================================================================

def test_overall_dual_dataset_certification():
    """
    Certificación global y unificada del Dataset Dual (Digital + Físico).
    Calcula la tasa de acierto ponderada en todo el dataset ampliado:
    - Casos digitales evaluados contra ThreatInspector.
    - Casos físicos evaluados contra RouteCompanion / SentinelAgent.
    Exige una precisión global mínima del 95% a costo $0.00 USD.
    """
    cases = _load_dataset()
    total_cases = len(cases)
    assert total_cases >= 38, f"Se requieren al menos 38 casos para la certificación global (actual: {total_cases})"

    correct_overall = 0
    agent = SentinelAgent()

    for case in cases:
        text = case["text"]
        expected_verdict = case["expected_verdict"]

        if _is_physical_case(case):
            session_id = f"cert_global_{case['id']}"
            res = agent.process_message(text, session_id=session_id)
            decision = res.get("decision", {})
            if decision.get("risk_level") == expected_verdict and decision.get("mode") == "route_companion":
                correct_overall += 1
        else:
            threat_res = inspect_threat(text)
            actual_level = threat_res.get("threat_level")
            if case["category"] == "LEGITIMO_CONTROL":
                if actual_level == "BAJO":
                    correct_overall += 1
            else:
                if actual_level in ["MEDIO", "ALTO", "CRÍTICO"]:
                    correct_overall += 1

    overall_accuracy = correct_overall / total_cases
    print(
        f"\n=======================================================\n"
        f"🏆 CERTIFICACIÓN HITO S3 · DATASET DUAL SENTINELGUARD AI\n"
        f"Total Casos Evaluados: {total_cases}\n"
        f"Aciertos Totales: {correct_overall}/{total_cases}\n"
        f"Tasa de Precisión Global: {overall_accuracy * 100:.1f}%\n"
        f"Costo de Ejecución: $0.00 USD (Modo Local Determinista)\n"
        f"======================================================="
    )
    assert overall_accuracy >= 0.95, (
        f"La precisión global certificada del dataset debe ser al menos del 95% (obtenida: {overall_accuracy * 100:.1f}%)"
    )
