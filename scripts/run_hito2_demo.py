"""
Demostración local de los 10 casos del Hito S2 (Escudo Digital)
Rol 4: Nicolle Camila Piñeros (Social Engineering NLP, Visión & CAI Virtual)
Reto Agente 2026 · Equipo Codixia

COSTO $0.00 — Este script NUNCA abre una conexión de red.

Blindaje inherente: antes de importar cualquier módulo de `src`, se neutraliza
la llave del reto. Como `src/config.py` usa `load_dotenv()` sin `override`, una
variable ya definida en el entorno gana sobre el contenido de `.env`. Así
`is_configured()` devuelve False aunque `.env` contenga una llave real y el
cliente de IA usa obligatoriamente su fallback local.

Uso:
    python scripts/run_hito2_demo.py
"""

import os
import sys
import json
import tempfile

# ---------------------------------------------------------------------------
# Blindaje de costo: se aplica ANTES de importar `src`.
# ---------------------------------------------------------------------------
os.environ["RETO_API_KEY"] = ""
os.environ["SENTINEL_LOCAL_OFFLINE"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.threat_inspector import inspect_threat
from src.tools.url_sandbox import analyze_url
from src.tools.vision_parser import parse_receipt_image, SimulatedVisionAnalyzer
from src.tools.police_reporter import generate_police_report

# PNG mínimo válido (1x1). Dato sintético: no se descarga nada de Internet.
PNG_1x1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

RESULTADOS = []


def caso(numero, titulo, esperado, observado):
    estado = "APROBADO" if esperado(observado) else "REVISAR"
    RESULTADOS.append((numero, titulo, estado))
    print(f"\n{'=' * 76}")
    print(f"CASO {numero:02d} · {titulo}   [{estado}]")
    print("=" * 76)
    return observado


def main():
    print("=" * 76)
    print(" SENTINELGUARD AI · HITO S2 · 10 CASOS LOCALES (Escudo Digital)")
    print(" Modo: LOCAL   ·   Costo: $0.00   ·   Llamadas externas: NINGUNA")
    print("=" * 76)

    with tempfile.TemporaryDirectory() as tmp:
        imagen = os.path.join(tmp, "comprobante_demo.png")
        with open(imagen, "wb") as fh:
            fh.write(PNG_1x1)

        # --- CASO 01 · Mensaje legítimo -------------------------------------
        r = caso(
            1, "Mensaje legítimo",
            lambda o: o["threat_level"] == "BAJO",
            inspect_threat("Hola mamá, ¿cómo estás? Ya llegué a la universidad, te llamo al almuerzo."),
        )
        print(f"  threat_level={r['threat_level']}  risk_score={r['risk_score']}  ambiguo={r['is_ambiguous']}")
        print(f"  vectors={r['detected_vectors']}")

        # --- CASO 02 · Phishing ---------------------------------------------
        r = caso(
            2, "Intento de phishing",
            lambda o: o["threat_level"] in ("ALTO", "CRÍTICO") and o["suspicious_urls"],
            inspect_threat(
                "Bancolombia: su cuenta ha sido bloqueada. Ingrese de inmediato a "
                "https://banc0lombia-seguridad.cc/login para desbloquearla."
            ),
        )
        print(f"  threat_level={r['threat_level']}  risk_score={r['risk_score']}")
        print(f"  vectors={r['detected_vectors']}")
        print(f"  urls_sospechosas={r['suspicious_urls']}")
        url = analyze_url("https://bancolombia-seguridad.cc/login")
        print(f"  UrlSandbox -> verdict={url['verdict']} typosquatting={url['is_typosquatting']}")

        # --- CASO 03 · Urgencia artificial ----------------------------------
        r = caso(
            3, "Urgencia artificial",
            lambda o: "urgencia_artificial" in o["detected_vectors"],
            inspect_threat("URGENTE: tiene 2 horas para actualizar sus datos o su cuenta será cerrada."),
        )
        print(f"  vectors={r['detected_vectors']}")
        print(f"  triggers={r['matched_triggers']}")

        # --- CASO 04 · Posible extorsión ------------------------------------
        r = caso(
            4, "Posible extorsión",
            lambda o: "extorsion_carcelaria" in o["detected_vectors"],
            inspect_threat(
                "Hablamos del Frente Urbano. Tenemos ubicado su negocio. Si no nos "
                "colabora con 2 millones, aténgase a las consecuencias."
            ),
        )
        print(f"  threat_level={r['threat_level']}  vectors={r['detected_vectors']}")

        # --- CASO 05 · URL sospechosa ---------------------------------------
        r = caso(
            5, "URL sospechosa",
            lambda o: o["verdict"] == "MALICIOSO" and o["is_typosquatting"],
            analyze_url("https://bancolombia-seguro-login.xyz/recuperar"),
        )
        print(f"  verdict={r['verdict']}  risk_score={r['risk_score']}")
        print(f"  typosquatting={r['is_typosquatting']}  marca={r['impersonated_brand']}")
        print(f"  findings={r['findings']}")


        # --- CASO 06 · Análisis visual (adaptador SIMULADO) -----------------
        print("\n  [VisionParser] validación local real + adaptador simulado")
        r_falso = parse_receipt_image(imagen, analyzer=SimulatedVisionAnalyzer(scenario="falsificado"))
        r_autentico = parse_receipt_image(imagen)
        r_amb = parse_receipt_image(imagen, analyzer=SimulatedVisionAnalyzer(scenario="inconcluso"))
        caso(
            6, "Análisis visual (adaptador SIMULADO)",
            lambda o: o is True,
            (
                r_falso["is_fraudulent"] is True
                and r_autentico["is_fraudulent"] is False
                and r_amb["is_fraudulent"] is None
            ),
        )
        print(f"  validación local real -> magic_bytes={r_autentico['local_checks']['signature_valid']} "
              f"existe={r_autentico['local_checks']['exists']}")
        print(f"  escenario 'falsificado' -> is_fraudulent={r_falso['is_fraudulent']} "
              f"reasons={r_falso['fraud_reasons']}")
        print(f"  escenario 'autentico'   -> is_fraudulent={r_autentico['is_fraudulent']}")
        print(f"  escenario 'inconcluso'  -> is_fraudulent={r_amb['is_fraudulent']} (ambiguo)")
        print(f"  analysis_source={r_autentico['analysis_source']}  <- SIMULADO, no Grok Vision")

        # --- CASO 07 · Mensaje ambiguo --------------------------------------
        r = caso(
            7, "Mensaje ambiguo",
            lambda o: o["is_ambiguous"] is True and o["threat_level"] == "BAJO",
            inspect_threat("Hola, ¿me escribes luego cuando puedas?"),
        )
        print(f"  ambiguo={r['is_ambiguous']}  threat_level={r['threat_level']}  vectors={r['detected_vectors']}")

        # --- CASO 08 · Entrada malformada -----------------------------------
        malformados = {}
        for etiqueta, valor in [("None", None), ("int", 12345), ("lista", []), ("dict", {})]:
            malformados[etiqueta] = inspect_threat(valor)
        caso(
            8, "Entrada malformada",
            lambda o: all(
                v["status"] == "error"
                and v["threat_level"] == "NO_ANALIZADO"
                and v["risk_score"] == 0
                for v in o.values()
            ),
            malformados,
        )
        for etiqueta, v in malformados.items():
            print(f"  entrada={etiqueta:6s} -> status={v['status']} error={v['error']} level={v['threat_level']}")
        print("  -> Nunca se convierte una entrada inválida en un veredicto de seguridad.")

        vacio = inspect_threat("")
        print(f"  cadena vacía -> status={vacio['status']} ambiguo={vacio['is_ambiguous']} (no es 'segura')")

        # --- CASO 09 · Fallo simulado del análisis --------------------------
        analizador_roto = SimulatedVisionAnalyzer(raise_exception=True)
        r = caso(
            9, "Fallo simulado del análisis",
            lambda o: o["status"] == "error" and o["is_fraudulent"] is None,
            parse_receipt_image(imagen, analyzer=analizador_roto),
        )
        print(f"  status={r['status']}  error={r['error']}")
        print(f"  is_fraudulent={r['is_fraudulent']}  analysis_source={r['analysis_source']}")
        print(f"  -> {r['notes']}")

        # --- CASO 10 · Informe estructurado ---------------------------------
        amenaza = inspect_threat(
            "Bancolombia: cuenta bloqueada, ingrese urgente a http://banc0lombia-alerta.cc"
        )
        evidencia = {
            "sender_phone": "+57 300 111 2233",
            "incident_type": "Suplantación Bancolombia / Phishing",
            "user_input": "Bancolombia: cuenta bloqueada, ingrese urgente a http://banc0lombia-alerta.cc",
            "risk_level": "CRÍTICO",
            "findings": amenaza["findings"],
            "detected_urls": amenaza["detected_urls"],
        }
        r = caso(
            10, "Generación de informe estructurado",
            lambda o: o["status"] == "success" and "CAI-COL-" in (o["report_id"] or ""),
            generate_police_report(evidencia),
        )
        print(f"  report_id={r['report_id']}")
        print(f"  categoria={r['incident_category']}")
        print(f"  faltantes={r['missing_fields']}")
        print("  --- extracto del expediente ---")
        for linea in r["formatted_markdown"].splitlines()[:9]:
            print("  " + linea)

        incompleto = generate_police_report({"sender_phone": "+57 300 111 2233"})
        print(f"\n  evidencia incompleta -> status={incompleto['status']} "
              f"error={incompleto['error']} faltantes={incompleto['missing_fields']}")
        print("  -> No se genera expediente con evidencia insuficiente.")

    # --- Resumen ----------------------------------------------------------
    print("\n" + "=" * 76)
    print(" RESUMEN DE LOS 10 CASOS LOCALES")
    print("=" * 76)
    for numero, titulo, estado in RESULTADOS:
        marca = "OK  " if estado == "APROBADO" else "TODO"
        print(f"  [{marca}] Caso {numero:02d} · {titulo}")
    aprobados = sum(1 for _, _, e in RESULTADOS if e == "APROBADO")
    print("-" * 76)
    print(f"  {aprobados}/{len(RESULTADOS)} casos aprobados · costo $0.00 · sin llamadas externas")
    print("=" * 76)
    return 0 if aprobados == len(RESULTADOS) else 1


if __name__ == "__main__":
    sys.exit(main())
