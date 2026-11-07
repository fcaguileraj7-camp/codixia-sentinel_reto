"""
Pruebas de Integración y UI para app_streamlit y Sistema Visual
Reto Agente 2026 - Platica.mx × Campuslands · Equipo Codixia
Rol 5: Juan José (Dataset Engineering, Stress Testing & UI)
"""

import os
import json
import pytest
from src.ui.theme import THEME_COLORS, RISK_COLORS, get_theme_css
from src.ui.styles import get_complete_css
from src.agent.sentinel import SentinelAgent
from src.tools.threat_inspector import inspect_threat
from src.tools.url_sandbox import analyze_url
from src.tools.police_reporter import generate_police_report

def test_theme_colors_exact_palette():
    """Verifica que la paleta oficial contenga los valores HEX obligatorios."""
    assert THEME_COLORS["cyber_forest"] == "#102820"
    assert THEME_COLORS["deep_forest"] == "#1B3830"
    assert THEME_COLORS["forest_green"] == "#426653"
    assert THEME_COLORS["digital_sage"] == "#83C6A3"
    assert THEME_COLORS["soft_sage"] == "#B6D1B8"
    assert THEME_COLORS["natural_ivory"] == "#F2F5EE"
    assert THEME_COLORS["warm_ivory"] == "#F5F5ED"
    assert THEME_COLORS["white"] == "#FFFFFF"
    assert THEME_COLORS["fog_green"] == "#E5EDE3"
    assert THEME_COLORS["slate_green"] == "#718477"
    assert THEME_COLORS["soft_border"] == "#D8E0D6"

def test_semantic_risk_colors():
    """Verifica los colores semánticos de riesgo y que sean independientes de marca."""
    assert RISK_COLORS["BAJO"]["bg"] == "#DCEBE0"
    assert RISK_COLORS["BAJO"]["text"] == "#315D45"
    assert RISK_COLORS["MEDIO"]["bg"] == "#F5E8C9"
    assert RISK_COLORS["MEDIO"]["text"] == "#795B22"
    assert RISK_COLORS["ALTO"]["bg"] == "#F4D9D8"
    assert RISK_COLORS["ALTO"]["text"] == "#8D3335"
    assert RISK_COLORS["CRÍTICO"]["bg"] == "#F4D9D8"
    assert RISK_COLORS["CRÍTICO"]["text"] == "#8D3335"

def test_complete_css_contains_26_effects_and_accessibility():
    """Verifica que el bloque CSS incluya los 26 efectos y la regla de accesibilidad."""
    css = get_complete_css()
    
    # Verificación de accesibilidad obligatoria
    assert "prefers-reduced-motion: reduce" in css
    
    # Categoría A: Scroll (1 a 5)
    assert "sg-parallax" in css          # 1. Parallax
    assert "sgScrollProgress" in css     # 2. Scroll-driven
    assert "sg-sticky-header" in css     # 3. Sticky
    assert "sg-floating-status-pill" in css # 3. Floating
    assert "scroll-snap-type" in css     # 4. Scroll Snap
    assert "sg-infinite" in css          # 5. Infinite scroll / progressive
    
    # Categoría B: Cursor / Hover / Click (6 a 11)
    assert "sg-card:hover" in css        # 6. Hover state 1
    assert "stButton > button" in css    # 6. Hover state 2
    assert "sg-hover-reveal-box" in css  # 7. Reveal effect 1
    assert "sg-term-reveal" in css       # 7. Reveal effect 2
    assert "sg-tooltip" in css           # 8. Tooltip
    assert "sg-popover" in css           # 8. Popover
    assert "sg-security-zone" in css     # 9. Custom cursor 1
    assert "sg-inspect-zone" in css      # 9. Custom cursor 2
    assert "sgRippleAnim" in css         # 10. Ripple effect
    assert "sg-tilt-card" in css         # 11. Tilt effect
    
    # Categoría C: Transiciones (12 a 16)
    assert "sgFadeIn" in css             # 12. Fade-in
    assert "sgSlideInRight" in css       # 13. Slide-in right
    assert "sgSlideInUp" in css          # 13. Slide-in up
    assert "tab-panel" in css            # 14. Page transitions
    assert "sg-lazy" in css              # 15. Lazy loading
    assert "sg-skeleton" in css          # 16. Skeleton screen
    
    # Categoría D: Fondo y Atmósfera (17 a 21)
    assert "sg-particle" in css          # 17. Particle effect
    assert "sgGradientFlow" in css       # 18. Gradient animation
    assert "backdrop-filter" in css      # 19. Glassmorphism
    assert "sgKenBurns" in css           # 20. Ken Burns
    assert "sgMarquee" in css            # 21. Marquee
    
    # Categoría E: Distorsión y Texturas (22 a 26)
    assert "sgLiquidMorph" in css        # 22. Liquid distortion
    assert "sgGlitchText" in css         # 23. Glitch effect
    assert "sgTyping" in css             # 24. Typing effect
    assert "-webkit-background-clip: text" in css # 25. Text masking
    assert "box-shadow: 6px 6px" in css  # 26. Neumorphism

def test_preserved_contracts():
    """Verifica que las llamadas a herramientas y agente funcionen idénticamente."""
    # 1. ThreatInspector
    sample_text = "Bancolombia Alerta: Su cuenta 456-*** fue bloqueada por movimientos sospechosos. Ingrese urgente a https://banc0lombia-seguridad.cc"
    threat = inspect_threat(sample_text)
    assert threat["status"] == "success"
    assert "detected_urls" in threat
    assert len(threat["detected_urls"]) >= 1

    # 2. UrlSandbox
    url_res = analyze_url("https://banc0lombia-seguridad.cc")
    assert url_res["status"] == "success"
    assert url_res["is_suspicious_tld"] is True

    # 3. PoliceReporter
    report = generate_police_report({
        "sender_phone": "+57 321 456 7890",
        "incident_type": "Suplantación Bancolombia / Phishing",
        "user_input": sample_text,
        "risk_level": "CRÍTICO",
        "findings": ["Enlace hacia dominio clonado"],
        "detected_urls": ["https://banc0lombia-seguridad.cc"]
    })
    assert report["status"] == "success"
    assert "CAI-COL-" in report["report_id"]
    assert "formatted_markdown" in report

    # 4. SentinelAgent
    agent = SentinelAgent()
    res = agent.process_message(sample_text, metadata={"sender": "+57 312 987 6543"})
    assert res["status"] == "success"
    assert "decision" in res
    assert "tool_results" in res


# =============================================================================
# PRUEBAS DEL SUBPROCESO 2: INGRESO DE MENSAJES, SELECTOR Y VALIDACIONES
# =============================================================================

from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from src.ui.components import (
    validate_input_text,
    load_demo_samples,
    NEUTRAL_SAMPLE_OPTION,
    get_analysis_metadata,
    render_source_badge,
    render_analysis_unavailable,
)

APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app_streamlit.py"))

def test_validate_input_text_empty_and_whitespace():
    """Caso E y F: Validación estricta de entradas vacías y espacios en blanco."""
    # Vacío absoluto y None
    is_valid, msg = validate_input_text(None)
    assert is_valid is False
    assert "Introduce un mensaje o selecciona un ejemplo" in msg

    is_valid, msg = validate_input_text("")
    assert is_valid is False
    assert "Introduce un mensaje o selecciona un ejemplo" in msg

    # Espacios en blanco simples
    is_valid, msg = validate_input_text("   ")
    assert is_valid is False
    assert "Introduce un mensaje o selecciona un ejemplo" in msg

    # Saltos de línea y tabuladores
    is_valid, msg = validate_input_text("\n\n\t  \r\n")
    assert is_valid is False
    assert "Introduce un mensaje o selecciona un ejemplo" in msg

def test_validate_input_text_valid_content():
    """Caso A: Validación exitosa de textos reales, enlaces y multilínea."""
    # Mensaje normal
    is_valid, msg = validate_input_text("Hola papá, ya llegué")
    assert is_valid is True
    assert msg == ""

    # Enlace sospechoso
    is_valid, msg = validate_input_text("https://banc0lombia-seguridad.cc")
    assert is_valid is True
    assert msg == ""

    # Multilínea con saltos y espacios perimetrales
    is_valid, msg = validate_input_text("  \nAlerta Bancaria:\nSu clave fue bloqueada.\n  ")
    assert is_valid is True
    assert msg == ""

def test_load_demo_samples_coverage_and_metadata():
    """Caso B: Cobertura representativa del catálogo de ejemplos con metadatos requeridos."""
    samples = load_demo_samples()
    assert len(samples) >= 6

    # Verificar que existen las 5 categorías esenciales del Hito S2
    categories = [s["category"] for s in samples]
    assert "PHISHING_BANCO" in categories or "PHISHING_NEQUI" in categories
    assert "EXTORSION_CARCELARIA" in categories or "EXTORSION_SEXTORSION" in categories
    assert "SUPLANTACION_FAMILIAR" in categories or "FALSA_OFERTA_LABORAL" in categories
    assert "LEGITIMO_CONTROL" in categories

    # Verificar estructura completa de cada muestra
    for s in samples:
        assert "id" in s
        assert "display_title" in s
        assert "text" in s
        assert len(s["text"]) > 10
        assert "phone" in s
        assert "icon" in s
        assert "expected_verdict" in s

def test_apptest_caso_a_user_typed_input():
    """Caso A: Entrada escrita por el usuario, visible, editable y validada para análisis."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert len(at.exception) == 0

    custom_text = "Alerta: Transacción rechazada en https://nequii-pagos.top"
    at.text_area(key="user_input_text").input(custom_text).run()
    assert at.text_area(key="user_input_text").value == custom_text

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "decision": {"risk_level": "ALTO", "action": "ANALYZE_ONLY", "response_to_user": "Sospechoso"},
            "tool_results": {"threat": {"findings": ["Phishing"]}, "url": {}}
        }
        at.button(key="btn_analyze_main").click().run()
        mock_agent.assert_called_once()
        assert len(at.warning) == 0


def test_apptest_caso_e_and_f_empty_and_whitespace_validation():
    """Casos E y F: Entrada vacía y con espacios rechazada sin llamar al agente ni consumir tokens."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    # Estado inicial (vacío)
    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        at.button(key="btn_analyze_main").click().run()
        assert len(at.warning) >= 1
        assert "Introduce un mensaje o selecciona un ejemplo" in at.warning[0].value
        mock_agent.assert_not_called()

    # Entrada compuesta solo por espacios y saltos de línea
    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        at.text_area(key="user_input_text").input("   \n\t   \n  ").run()
        at.button(key="btn_analyze_main").click().run()
        assert len(at.warning) >= 1
        assert "Introduce un mensaje o selecciona un ejemplo" in at.warning[0].value
        mock_agent.assert_not_called()


# =============================================================================
# PRUEBAS DEL HITO 2: SIMULACIÓN, GROK REAL Y MANEJO DE FALLOS (NICOLLE REVIEW)
# =============================================================================

def test_metadata_extractor_simulated_and_real():
    """Valida la extracción precisa de metadatos de origen (simulado vs real)."""
    # 1. Metadatos directos de simulación
    is_sim, src = get_analysis_metadata({"simulated": True})
    assert is_sim is True
    assert src == "simulated"

    is_sim, src = get_analysis_metadata({"analysis_source": "simulated"})
    assert is_sim is True
    assert src == "simulated"

    is_sim, src = get_analysis_metadata({"analysis_source": "local_mock"})
    assert is_sim is True
    assert src == "local_mock"

    # 2. Metadatos directos de modelo real
    is_sim, src = get_analysis_metadata({"simulated": False})
    assert is_sim is False
    assert src == "grok_4.7"

    is_sim, src = get_analysis_metadata({"analysis_source": "grok_4.7"})
    assert is_sim is False
    assert src == "grok_4.7"

    is_sim, src = get_analysis_metadata({"analysis_source": "grok"})
    assert is_sim is False

    # 3. Metadatos dentro del diccionario de decisión
    is_sim, src = get_analysis_metadata({"decision": {"simulated": True}})
    assert is_sim is True

    is_sim, src = get_analysis_metadata({"decision": {"simulated": False}})
    assert is_sim is False

    # 4. Fallback por patrones conocidos de texto
    is_sim, src = get_analysis_metadata({"decision": {"reasoning": "Conversación cotidiana sin patrones"}})
    assert is_sim is True


def test_apptest_simulated_result_identifies_as_simulated():
    """Criterio de aceptación 1: Al probar un resultado simulado, la interfaz lo identifica como tal."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje de prueba para simulación").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "simulated": True,
            "analysis_source": "simulated",
            "decision": {
                "risk_level": "MEDIO",
                "action": "ANALYZE_ONLY",
                "response_to_user": "Respuesta simulada",
                "reasoning": "Motivo de prueba"
            },
            "tool_results": {}
        }
        at.button(key="btn_analyze_main").click().run()

    # Verificar que el badge visible de 'Resultado simulado' está presente
    markdown_texts = [m.value for m in at.markdown]
    has_simulated_badge = any("Resultado simulado" in txt for txt in markdown_texts)
    assert has_simulated_badge, "La interfaz debe mostrar el indicador 'Resultado simulado'"

    # Verificar que NO afirme que se usó Grok 4.7
    has_grok_heading = any("Veredicto del Agente (Grok 4.7)" in txt for txt in markdown_texts)
    assert not has_grok_heading, "No debe afirmar que se utilizó Grok 4.7 si el resultado es simulado"

    # Debe indicar 'Modo Simulado' en el veredicto
    has_sim_verdict = any("Modo Simulado" in txt or "Simulado" in txt for txt in markdown_texts)
    assert has_sim_verdict, f"Debe indicar 'Modo Simulado': {markdown_texts}"


def test_apptest_real_result_does_not_label_as_simulated():
    """Criterio de aceptación 2: Al recibir un resultado real, no lo etiqueta como simulado."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje de prueba con Grok real").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "simulated": False,
            "analysis_source": "grok_4.7",
            "decision": {
                "risk_level": "ALTO",
                "action": "BLOCK_AND_REPORT",
                "response_to_user": "Respuesta de Grok real",
                "reasoning": "Inferencia xAI activa"
            },
            "tool_results": {}
        }
        at.button(key="btn_analyze_main").click().run()

    markdown_texts = [m.value for m in at.markdown]

    # Verificar que NO se etiquete como simulado
    has_simulated_badge = any("Resultado simulado" in txt for txt in markdown_texts)
    assert not has_simulated_badge, "Un resultado real no debe ser etiquetado como simulado"

    # Verificar que muestre el indicador de Grok 4.7
    has_grok_source = any("Grok 4.7" in txt for txt in markdown_texts)
    assert has_grok_source, "Debe mantener el indicador normal de Grok 4.7 para respuestas reales"


def test_apptest_failed_analysis_shows_not_completed_and_not_safe():
    """Criterio de aceptación 3: Ante un fallo, muestra que el análisis no se completó sin presentarlo como seguro."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje que genera fallo en el proveedor").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.side_effect = Exception("Conexión perdida con el servicio de inferencia")
        at.button(key="btn_analyze_main").click().run()

    # Verificar que se informe el estado no completado
    error_values = [e.value for e in at.error]
    assert any("Análisis no completado" in err for err in error_values), "Debe mostrar que el análisis no se completó"

    markdown_texts = [m.value for m in at.markdown]
    has_failed_card = any("Análisis no disponible — Inspección no completada" in txt for txt in markdown_texts)
    assert has_failed_card, "Debe mostrar la tarjeta de estado de análisis no disponible"

    has_safety_notice = any("garantiza que el mensaje sea seguro" in txt for txt in markdown_texts)
    assert has_safety_notice, "Debe advertir al usuario que la ausencia de análisis no es garantía de seguridad"

    # Verificar que NO lo presente como mensaje seguro
    success_values = [s.value for s in at.success]
    assert not any("MENSAJE APARENTEMENTE LEGÍTIMO" in s for s in success_values), "Un análisis fallido NO debe presentarse como seguro"


def test_apptest_error_status_in_result_handled():
    """Valida el manejo cuando el agente devuelve status != 'success'."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje con respuesta errónea").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "error",
            "error": "Saldo insuficiente en API xAI"
        }
        at.button(key="btn_analyze_main").click().run()

    error_values = [e.value for e in at.error]
    assert any("Saldo insuficiente en API xAI" in err or "Análisis no completado" in err for err in error_values)


# =============================================================================
# PRUEBAS DEL SUBPROCESO 3: PUNTOS 3, 4 Y 5 (REPORTE POLICIAL, ERRORES Y FLUJO)
# =============================================================================

def test_apptest_police_report_displayed_when_valid():
    """Punto 3: Muestra radicado técnico y estado 'preparado (no radicado ante autoridad)' cuando existe reporte válido."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje crítico con enlace malicioso https://banc0lombia-seguridad.cc").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "decision": {
                "risk_level": "CRÍTICO",
                "action": "BLOCK_AND_REPORT",
                "response_to_user": "Dictamen: Intento crítico de estafa detectado.",
                "reasoning": "Dominio clonado y urgencia artificial"
            },
            "tool_results": {
                "threat": {"findings": ["Dominio clonado"], "detected_urls": ["https://banc0lombia-seguridad.cc"]},
                "url": {"status": "success", "domain": "banc0lombia-seguridad.cc", "is_suspicious_tld": True}
            },
            "escalation": {
                "alert_id": "SOS-991122",
                "incident_type": "DIGITAL_FRAUD",
                "severity": "CRITICAL"
            },
            "police_report": {
                "status": "success",
                "report_id": "CAI-COL-777888",
                "timestamp": "2026-10-15 20:30:00",
                "formatted_markdown": "# EXPEDIENTE DE DENUNCIA DIGITAL\n**Radicado Técnico:** CAI-COL-777888"
            }
        }
        at.button(key="btn_analyze_main").click().run()

    # Verificar que el radicado técnico real es visible
    info_texts = [i.value for i in at.info]
    markdown_texts = [m.value for m in at.markdown]
    all_texts = info_texts + markdown_texts

    assert any("CAI-COL-777888" in txt for txt in all_texts), "Debe mostrar el radicado técnico 'CAI-COL-777888'"
    
    # Verificar que indica claramente que está preparado y no presentado ante una autoridad judicial
    assert any("preparado y listo para radicación" in txt or "No ha sido presentado ante una autoridad judicial" in txt for txt in info_texts), \
        "Debe indicar explícitamente que el reporte está preparado pero no presentado formalmente"


def test_apptest_police_report_confirmed_status():
    """Punto 3: Si el sistema confirma radicación oficial ante autoridades, muestra estado confirmado."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje con radicación confirmada").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "decision": {
                "risk_level": "CRÍTICO",
                "action": "BLOCK_AND_REPORT",
                "response_to_user": "Dictamen crítico",
                "reasoning": "Extorsión comprobada"
            },
            "tool_results": {},
            "escalation": {"alert_id": "SOS-5544"},
            "police_report": {
                "status": "success",
                "report_id": "CAI-COL-CONFIRMED-123",
                "official_filing_confirmed": True,
                "timestamp": "2026-10-15 20:35:00",
                "formatted_markdown": "# EXPEDIENTE CONFIRMADO"
            }
        }
        at.button(key="btn_analyze_main").click().run()

    success_texts = [s.value for s in at.success]
    assert any("Radicación Oficial Confirmada ante Autoridades" in txt and "CAI-COL-CONFIRMED-123" in txt for txt in success_texts), \
        "Debe mostrar el estado confirmado cuando existe evidencia de radicación oficial"


def test_apptest_police_report_not_invented_on_low_risk():
    """Punto 3: En riesgo bajo sin reporte, no inventa radicados ni muestra expedientes falsos."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Hola mamá, ya llegué a la casa").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "decision": {
                "risk_level": "BAJO",
                "action": "INFORMATIVE_ONLY",
                "response_to_user": "Mensaje seguro y legítimo",
                "reasoning": "Sin patrones de fraude"
            },
            "tool_results": {"threat": {"threat_level": "BAJO", "findings": []}},
            "escalation": None,
            "police_report": None
        }
        at.button(key="btn_analyze_main").click().run()

    info_texts = [i.value for i in at.info]
    markdown_texts = [m.value for m in at.markdown]
    all_texts = info_texts + markdown_texts

    # No debe inventar ningún radicado CAI-COL
    assert not any("CAI-COL" in txt for txt in all_texts), "No debe inventar ningún radicado policial en riesgo bajo"
    
    # Debe mantener la alerta positiva
    success_texts = [s.value for s in at.success]
    assert any("MENSAJE APARENTEMENTE LEGÍTIMO" in s for s in success_texts)


def test_apptest_police_report_failure_informs_without_inventing():
    """Puntos 3 y 4: Si el módulo de reportes falla, informa la condición sin inventar radicado y preserva el análisis de amenazas."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje de estafa donde falla la generación del reporte").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "decision": {
                "risk_level": "ALTO",
                "action": "BLOCK_AND_REPORT",
                "response_to_user": "Alerta: Intento de suplantación bancaria.",
                "reasoning": "Suplantación de entidad bancaria"
            },
            "tool_results": {
                "threat": {"findings": ["Presión psicológica por bloqueo"]},
                "url": {}
            },
            "escalation": {"alert_id": "SOS-FAIL-01"},
            "police_report": {
                "status": "error",
                "error_message": "Servicio de compilación de expedientes no disponible"
            }
        }
        at.button(key="btn_analyze_main").click().run()

    # Verificar que informa el fallo del reporte
    info_texts = [i.value for i in at.info]
    assert any("Reporte policial no disponible" in txt and "Servicio de compilación" in txt for txt in info_texts), \
        "Debe informar que el reporte policial no está disponible con el detalle técnico"

    # Verificar que NO inventa un radicado
    assert not any("CAI-COL" in txt for txt in info_texts)

    # Verificar que PRESERVA los resultados válidos del análisis de fraude (Puntos 1 y 2)
    error_texts = [e.value for e in at.error]
    assert any("NIVEL DE AMENAZA: ALTO" in err for err in error_texts), "Debe conservar la alerta de amenaza ALTA"
    
    markdown_texts = [m.value for m in at.markdown]
    assert any("Intento de suplantación bancaria" in m for m in markdown_texts), "Debe conservar el veredicto del agente"


def test_apptest_partial_analysis_distinguished_and_preserves_valid_results():
    """Punto 4: Distingue un análisis parcial de uno completo y preserva los resultados válidos."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje con fallo en una herramienta secundaria").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "partial",
            "partial_reason": "La herramienta UrlSandbox no pudo contactar el servidor DNS.",
            "decision": {
                "risk_level": "MEDIO",
                "action": "ANALYZE_ONLY",
                "response_to_user": "Precaución: El mensaje contiene enlaces no verificables.",
                "reasoning": "Heurística detectó palabras sospechosas pero sandbox falló"
            },
            "tool_results": {
                "threat": {"findings": ["Palabras de urgencia"]},
                "url": {"status": "error", "error": "Fallo de conexión DNS"}
            }
        }
        at.button(key="btn_analyze_main").click().run()

    # 1. Debe advertir explícitamente que es un ANÁLISIS PARCIAL
    warning_texts = [w.value for w in at.warning]
    assert any("Análisis Parcial" in w for w in warning_texts), "Debe presentar la advertencia de Análisis Parcial"
    
    # 2. Debe conservar el nivel de riesgo MEDIO
    assert any("NIVEL DE AMENAZA: MEDIO" in w for w in warning_texts)

    # 3. Debe conservar el veredicto del agente
    markdown_texts = [m.value for m in at.markdown]
    assert any("El mensaje contiene enlaces no verificables" in m for m in markdown_texts)

    # 4. No debe reportarse como análisis fallido total ni como aparentemente legítimo
    error_texts = [e.value for e in at.error]
    assert not any("Análisis no completado" in err for err in error_texts), "Un análisis parcial no debe marcarse como fallo total"


def test_apptest_sanitizes_sensitive_error_traces():
    """Punto 4: Sanitiza trazas internas y credenciales para no exponerlas al usuario."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje que detona excepción con secreto").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.side_effect = Exception("Traceback (most recent call last): File 'server.py', line 12: api_key=sk-proj-SUPER_SECRET_12345")
        at.button(key="btn_analyze_main").click().run()

    error_texts = [e.value for e in at.error]
    markdown_texts = [m.value for m in at.markdown]
    all_rendered = " ".join(error_texts + markdown_texts)

    # La clave secreta y la traza interna NO deben aparecer en la interfaz
    assert "sk-proj-SUPER_SECRET_12345" not in all_rendered, "No debe exponer credenciales en la UI"
    assert "Traceback (most recent call last)" not in all_rendered, "No debe exponer trazas de stack en la UI"

    # Debe mostrar mensaje de error seguro y no presentar el mensaje como legítimo
    assert any("Análisis no completado" in err for err in error_texts)
    success_texts = [s.value for s in at.success]
    assert not any("MENSAJE APARENTEMENTE LEGÍTIMO" in s for s in success_texts)


def test_apptest_retry_analysis_after_error():
    """Punto 4 y 5: Permite al usuario volver a ejecutar un análisis exitosamente tras un error."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    # 1. Primer intento que falla
    at.text_area(key="user_input_text").input("Primer intento fallido").run()
    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent_fail:
        mock_agent_fail.side_effect = Exception("Fallo transitorio de conexión")
        at.button(key="btn_analyze_main").click().run()

    assert any("Análisis no completado" in e.value for e in at.error)

    # 2. Segundo intento exitoso
    at.text_area(key="user_input_text").input("Segundo intento corregido").run()
    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent_success:
        mock_agent_success.return_value = {
            "status": "success",
            "decision": {
                "risk_level": "BAJO",
                "action": "INFORMATIVE_ONLY",
                "response_to_user": "Análisis reintentado con éxito.",
                "reasoning": "Todo en orden"
            },
            "tool_results": {"threat": {"findings": []}}
        }
        at.button(key="btn_analyze_main").click().run()

    # Verificar que el error ya no está activo y se muestra el nuevo veredicto
    assert not any("Análisis no completado" in e.value for e in at.error)
    markdown_texts = [m.value for m in at.markdown]
    assert any("Análisis reintentado con éxito" in m for m in markdown_texts)


# =============================================================================
# PRUEBAS DE ESTRUCTURA SIN MÓDULO DE TAXI (ROL 5 - INTERFAZ OFICIAL)
# =============================================================================

def test_apptest_two_tabs_rendered_without_taxi():
    """Verifica que la app renderice exclusivamente 2 pestañas oficiales sin componentes de taxi."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert len(at.exception) == 0

    # Pestaña 1: Escudo Digital presente e intacto
    assert at.text_area(key="user_input_text") is not None
    assert at.button(key="btn_analyze_main") is not None

    # Componentes del servicio de taxi no deben existir en el árbol de renderizado
    text_input_keys = [getattr(w, "key", None) for w in at.text_input]
    button_keys = [getattr(w, "key", None) for w in at.button]
    assert "taxi_plate_input" not in text_input_keys
    assert "taxi_destination_input" not in text_input_keys
    assert "taxi_btn_register" not in button_keys
    assert "taxi_btn_sos" not in button_keys
    assert "taxi_active_trip" not in at.session_state


def test_apptest_cai_virtual_tab_accessible_and_functional():
    """Verifica que la pestaña de Denuncias para CAI Virtual sea plenamente accesible y funcional."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert len(at.exception) == 0

    # Generar expediente de ejemplo
    gen_buttons = [b for b in at.button if "Generar Expediente" in b.label]
    assert len(gen_buttons) > 0
    gen_buttons[0].click().run()
    assert len(at.exception) == 0
    assert any("Expediente de ejemplo preparado" in i.value for i in at.info)


def test_apptest_metric_cards_contain_no_taxi_accompaniment():
    """Verifica que las tarjetas métricas de la UI no incluyan acompañamiento en viajes."""
    from src.ui.components import render_metric_cards
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert len(at.exception) == 0

    all_rendered = " ".join([m.value for m in at.markdown])
    assert "Acompañamiento en Viajes" not in all_rendered
    assert "Ruta 24/7" not in all_rendered
    assert "Auditoría de Enlaces" in all_rendered


# =============================================================================
# PRUEBAS DE TELEMETRÍA GROK 4.7, CONSUMO DE TOKENS Y COSTOS (ROL 5)
# =============================================================================

def test_apptest_telemetry_panel_simulated_mode():
    """
    Verifica que en modo simulado/fallback local:
    - Se indique claramente el estado SIMULADO ($0.00 USD).
    - Se reporten 0 tokens y $0.000000 USD de consumo de API.
    - Se actualicen las métricas de sesión como contingencia local.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje de prueba para fallback").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "session_id": "sess_sim_01",
            "turn_id": 1,
            "decision": {
                "risk_level": "CRÍTICO",
                "action": "ESCALATE_AND_REPORT",
                "response_to_user": "Alerta crítica de prueba en fallback.",
                "reasoning": "Ingeniería social bancaria local",
                "analysis_source": "simulated",
                "simulated": True
            },
            "tool_results": {"threat": {"findings": ["Enlace malicioso"]}},
            "telemetry": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
                "mode": "simulated_local"
            },
            "simulated": True,
            "analysis_source": "simulated"
        }
        at.button(key="btn_analyze_main").click().run()

    assert len(at.exception) == 0

    # Verificación del estado visual SIMULADO
    info_texts = [i.value for i in at.info]
    assert any("SIMULADO / FALLBACK LOCAL" in t for t in info_texts)
    assert any("$0.000000 USD" in t for t in info_texts)

    # Verificación de las tarjetas métricas de tokens
    metrics_map = {m.label: m.value for m in at.metric}
    assert metrics_map.get("Tokens Entrada") == "0"
    assert metrics_map.get("Tokens Salida") == "0"
    assert metrics_map.get("Tokens Totales") == "0"
    assert metrics_map.get("Costo Consulta") == "$0.000000 USD"

    # Verificación del estado de sesión acumulado
    s_tel = at.session_state["session_telemetry"]
    assert s_tel["interaction_count"] == 1
    assert s_tel["simulated_count"] == 1
    assert s_tel["live_count"] == 0
    assert s_tel["total_tokens"] == 0
    assert s_tel["total_cost_usd"] == 0.0


def test_apptest_telemetry_panel_live_mode_real_tokens():
    """
    Verifica que en modo LIVE real de Grok 4.7:
    - Se indique explícitamente el estado LIVE con conexión a Grok 4.7.
    - Se extraigan y muestren los tokens reales (prompt, completion, total).
    - Se calcule y muestre el costo proyectado en USD con 6 decimales.
    - Se acumulen correctamente en la sesión como interacción en vivo.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje para inferencia Grok en vivo").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "session_id": "sess_live_01",
            "turn_id": 101,
            "decision": {
                "risk_level": "ALTO",
                "action": "BLOCK_AND_REPORT",
                "response_to_user": "Amenaza interceptada por Grok 4.7.",
                "reasoning": "Detección semántica avanzada",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {"threat": {"findings": ["Urgencia temporal"]}},
            "telemetry": {
                "prompt_tokens": 420,
                "completion_tokens": 85,
                "total_tokens": 505,
                "estimated_cost_usd": 0.001690,
                "mode": "live_api"
            },
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    assert len(at.exception) == 0

    # Verificación del banner de éxito LIVE
    success_texts = [s.value for s in at.success]
    assert any("LIVE" in t and "grok-4.7" in t for t in success_texts)

    # Verificación de las métricas numéricas de tokens
    metrics_map = {m.label: m.value for m in at.metric}
    assert metrics_map.get("Tokens Entrada") == "420"
    assert metrics_map.get("Tokens Salida") == "85"
    assert metrics_map.get("Tokens Totales") == "505"
    assert metrics_map.get("Costo Consulta") == "$0.001690 USD"

    # Verificación del estado de sesión acumulado
    s_tel = at.session_state["session_telemetry"]
    assert s_tel["interaction_count"] == 1
    assert s_tel["live_count"] == 1
    assert s_tel["simulated_count"] == 0
    assert s_tel["prompt_tokens"] == 420
    assert s_tel["completion_tokens"] == 85
    assert s_tel["total_tokens"] == 505
    assert s_tel["total_cost_usd"] == pytest.approx(0.001690, rel=1e-4)


def test_apptest_telemetry_session_accumulation_and_idempotent_rerun():
    """
    Verifica que múltiples consultas acumulen correctamente los tokens y costos
    y que los reruns de Streamlit no dupliquen métricas (idempotencia estricta).
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    # --- Consulta 1 ---
    at.text_area(key="user_input_text").input("Primera consulta de prueba").run()
    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "session_id": "sess_accum",
            "turn_id": 1,
            "decision": {
                "risk_level": "MEDIO",
                "action": "ANALYZE_ONLY",
                "response_to_user": "Primer veredicto",
                "reasoning": "Normal",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": {
                "prompt_tokens": 300,
                "completion_tokens": 50,
                "total_tokens": 350,
                "estimated_cost_usd": 0.001100,
                "mode": "live_api"
            },
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    assert at.session_state["session_telemetry"]["interaction_count"] == 1
    assert at.session_state["session_telemetry"]["total_tokens"] == 350

    # --- Rerun sin nuevo clic (simula interacción con otro widget) ---
    at.run()
    # Debe mantener exactamente los mismos valores sin duplicar
    assert at.session_state["session_telemetry"]["interaction_count"] == 1
    assert at.session_state["session_telemetry"]["total_tokens"] == 350
    assert at.session_state["session_telemetry"]["total_cost_usd"] == pytest.approx(0.001100, rel=1e-4)

    # --- Consulta 2 ---
    at.text_area(key="user_input_text").input("Segunda consulta de prueba").run()
    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent2:
        mock_agent2.return_value = {
            "status": "success",
            "session_id": "sess_accum",
            "turn_id": 2,
            "decision": {
                "risk_level": "CRÍTICO",
                "action": "ESCALATE_AND_REPORT",
                "response_to_user": "Segundo veredicto",
                "reasoning": "Phishing",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": {
                "prompt_tokens": 200,
                "completion_tokens": 40,
                "total_tokens": 240,
                "estimated_cost_usd": 0.000800,
                "mode": "live_api"
            },
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    # Acumulación: 350 + 240 = 590 tokens; $0.001100 + $0.000800 = $0.001900 USD
    s_tel = at.session_state["session_telemetry"]
    assert s_tel["interaction_count"] == 2
    assert s_tel["prompt_tokens"] == 500
    assert s_tel["completion_tokens"] == 90
    assert s_tel["total_tokens"] == 590
    assert s_tel["total_cost_usd"] == pytest.approx(0.001900, rel=1e-4)

    # Segundo rerun de control: debe permanecer idéntico
    at.run()
    assert at.session_state["session_telemetry"]["interaction_count"] == 2
    assert at.session_state["session_telemetry"]["total_tokens"] == 590


def test_apptest_sidebar_telemetry_reset_button():
    """Verifica que el botón de reinicio en la barra lateral restablezca el acumulador a ceros."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    # Inyectar métricas previas en session_state
    at.session_state["session_telemetry"]["prompt_tokens"] = 1500
    at.session_state["session_telemetry"]["completion_tokens"] = 300
    at.session_state["session_telemetry"]["total_tokens"] = 1800
    at.session_state["session_telemetry"]["total_cost_usd"] = 0.006000
    at.session_state["session_telemetry"]["interaction_count"] = 5
    at.session_state["session_telemetry"]["recorded_turns"] = ["turn_1", "turn_2"]

    # Hacer clic en el botón de reinicio
    at.button(key="btn_reset_session_telemetry").click().run()
    assert len(at.exception) == 0

    s_tel = at.session_state["session_telemetry"]
    assert s_tel["prompt_tokens"] == 0
    assert s_tel["completion_tokens"] == 0
    assert s_tel["total_tokens"] == 0
    assert s_tel["total_cost_usd"] == 0.0
    assert s_tel["interaction_count"] == 0
    assert len(s_tel["recorded_turns"]) == 0


def test_apptest_multiple_consecutive_analyses_increment_count():
    """
    Verifica que cada nuevo mensaje enviado incremente consecutivamente
    el contador de consultas (1 -> 2 -> 3) y acumule la telemetría,
    resolviendo el problema reportado de consultas congeladas en 1.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    # Consulta 1
    at.text_area(key="user_input_text").input("Mensaje 1").run()
    at.button(key="btn_analyze_main").click().run()
    assert at.session_state["session_telemetry"]["interaction_count"] == 1

    # Consulta 2
    at.text_area(key="user_input_text").input("Mensaje 2").run()
    at.button(key="btn_analyze_main").click().run()
    assert at.session_state["session_telemetry"]["interaction_count"] == 2

    # Consulta 3
    at.text_area(key="user_input_text").input("Mensaje 3").run()
    at.button(key="btn_analyze_main").click().run()
    assert at.session_state["session_telemetry"]["interaction_count"] == 3


# =============================================================================
# PRUEBAS DE TELEMETRÍA Y OBSERVABILIDAD DETERMINISTA (FASE 3 - HITO S3)
# =============================================================================

def test_apptest_telemetry_synthetic_live_scenario_math_120_80_200():
    """
    Etapa 3.1 & 3.2: Valida la visualización matemática exacta de tokens y costo:
    - prompt_tokens = 120
    - completion_tokens = 80
    - total_tokens = 200
    - Costo esperado: (120 * 0.000002) + (80 * 0.000010) = 0.000240 + 0.000800 = $0.001040 USD
    - Tarifa identificada como CONFIGURED_UNVERIFIED.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Consulta de prueba con escenario matemático").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "session_id": "sess_math_01",
            "turn_id": 1,
            "decision": {
                "risk_level": "MEDIO",
                "action": "ANALYZE_ONLY",
                "response_to_user": "Validación matemática de telemetría.",
                "reasoning": "Inspección semántica sintética",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": {
                "prompt_tokens": 120,
                "completion_tokens": 80,
                "total_tokens": 200,
                "estimated_cost_usd": 0.001040,
                "mode": "live_api"
            },
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    assert len(at.exception) == 0

    metrics_map = {m.label: m.value for m in at.metric}
    assert metrics_map.get("Tokens Entrada") == "120"
    assert metrics_map.get("Tokens Salida") == "80"
    assert metrics_map.get("Tokens Totales") == "200"
    assert metrics_map.get("Costo Consulta") == "$0.001040 USD"

    caption_texts = [c.value for c in at.caption]
    assert any("CONFIGURED_UNVERIFIED" in t for t in caption_texts)


def test_apptest_telemetry_synthetic_multi_interaction_accumulation():
    """
    Etapa 3.3: Valida la acumulación de varias interacciones y su idempotencia:
    - Interacción 1: Entrada 120, Salida 80, Total 200 ($0.001040 USD)
    - Interacción 2: Entrada 200, Salida 100, Total 300 ($0.001400 USD)
    - Acumulado sesión: Entrada 320, Salida 180, Total 500, Costo $0.002440 USD, 2 interacciones.
    - Idempotencia: un rerun no duplica las métricas.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    # Interacción 1
    at.text_area(key="user_input_text").input("Interacción uno").run()
    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "session_id": "sess_multi",
            "turn_id": 1,
            "decision": {
                "risk_level": "BAJO",
                "action": "INFORMATIVE_ONLY",
                "response_to_user": "Turno 1",
                "reasoning": "Normal",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": {
                "prompt_tokens": 120,
                "completion_tokens": 80,
                "total_tokens": 200,
                "estimated_cost_usd": 0.001040,
                "mode": "live_api"
            },
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    assert at.session_state["session_telemetry"]["interaction_count"] == 1
    assert at.session_state["session_telemetry"]["prompt_tokens"] == 120
    assert at.session_state["session_telemetry"]["completion_tokens"] == 80
    assert at.session_state["session_telemetry"]["total_tokens"] == 200
    assert at.session_state["session_telemetry"]["total_cost_usd"] == pytest.approx(0.001040, rel=1e-5)

    # Rerun de verificación de idempotencia
    at.run()
    assert at.session_state["session_telemetry"]["interaction_count"] == 1
    assert at.session_state["session_telemetry"]["total_tokens"] == 200

    # Interacción 2
    at.text_area(key="user_input_text").input("Interacción dos").run()
    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent2:
        mock_agent2.return_value = {
            "status": "success",
            "session_id": "sess_multi",
            "turn_id": 2,
            "decision": {
                "risk_level": "ALTO",
                "action": "BLOCK_AND_REPORT",
                "response_to_user": "Turno 2",
                "reasoning": "Phishing",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": {
                "prompt_tokens": 200,
                "completion_tokens": 100,
                "total_tokens": 300,
                "estimated_cost_usd": 0.001400,
                "mode": "live_api"
            },
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    s_tel = at.session_state["session_telemetry"]
    assert s_tel["interaction_count"] == 2
    assert s_tel["prompt_tokens"] == 320
    assert s_tel["completion_tokens"] == 180
    assert s_tel["total_tokens"] == 500
    assert s_tel["total_cost_usd"] == pytest.approx(0.002440, rel=1e-5)


def test_apptest_telemetry_differential_neutral_note():
    """
    Prompt 63821: Valida que ante un diferencial de tokens (total > prompt + completion):
    - Se presente la métrica 'Diferencia de tokens' con el valor exacto (350 - (250 + 50) = 50).
    - La antigua nota de observabilidad haya desaparecido completamente.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Consulta con diferencial de tokens").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "session_id": "sess_diff_01",
            "turn_id": 1,
            "decision": {
                "risk_level": "CRÍTICO",
                "action": "BLOCK_AND_REPORT",
                "response_to_user": "Veredicto",
                "reasoning": "Ataque",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": {
                "prompt_tokens": 250,
                "completion_tokens": 50,
                "total_tokens": 350,
                "estimated_cost_usd": 0.001000,
                "mode": "live_api"
            },
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    # Verificación de la quinta métrica Diferencia de tokens
    metrics_map = {m.label: m.value for m in at.metric}
    assert metrics_map.get("Tokens Entrada") == "250"
    assert metrics_map.get("Tokens Salida") == "50"
    assert metrics_map.get("Tokens Totales") == "350"
    assert metrics_map.get("Diferencia de tokens") == "50"
    assert metrics_map.get("Costo Consulta") == "$0.001000 USD"

    # Verificación de que la antigua nota de observabilidad no aparece
    caption_texts = [c.value for c in at.caption]
    assert not any("refleja el total global reportado por la API" in t for t in caption_texts)
    assert not any("Nota de observabilidad" in t for t in caption_texts)


def test_apptest_telemetry_missing_usage_displayed_as_nd():
    """
    Etapa 4 Escenario C: Cuando no exista información de uso (telemetry=None o vacío):
    - No inventa tokens ni asume cero.
    - Muestra los valores como 'N/D'.
    - El costo se presenta como 'N/D'.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Consulta con telemetría no provista").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "session_id": "sess_no_usage",
            "turn_id": 1,
            "decision": {
                "risk_level": "MEDIO",
                "action": "INFORMATIVE_ONLY",
                "response_to_user": "Respuesta sin telemetría de proveedor.",
                "reasoning": "Veredicto sin usage",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": None,
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    metrics_map = {m.label: m.value for m in at.metric}
    assert metrics_map.get("Tokens Entrada") == "N/D"
    assert metrics_map.get("Tokens Salida") == "N/D"
    assert metrics_map.get("Tokens Totales") == "N/D"
    assert metrics_map.get("Costo Consulta") == "N/D"


def test_apptest_telemetry_incomplete_usage_fields():
    """
    Etapa 4 Escenario D: Cuando la telemetría tiene campos incompletos:
    - No completa con suposiciones los campos faltantes.
    - Los campos ausentes se presentan como 'N/D'.
    - El costo se muestra como 'N/D' si no se puede calcular de forma confiable.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Consulta con telemetría parcial").run()

    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "session_id": "sess_partial_usage",
            "turn_id": 1,
            "decision": {
                "risk_level": "BAJO",
                "action": "INFORMATIVE_ONLY",
                "response_to_user": "Respuesta parcial",
                "reasoning": "Sin salida",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": {
                "prompt_tokens": 120,
            },
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    metrics_map = {m.label: m.value for m in at.metric}
    assert metrics_map.get("Tokens Entrada") == "120"
    assert metrics_map.get("Tokens Salida") == "N/D"
    assert metrics_map.get("Tokens Totales") == "N/D"
    assert metrics_map.get("Costo Consulta") == "N/D"


def test_apptest_telemetry_no_stale_metrics_reuse():
    """
    Etapa 4 Escenario E: Interacción sin usage después de una interacción válida:
    - La interacción 2 no hereda los tokens ni costo de la interacción 1.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    # Interacción 1: válida con telemetría
    at.text_area(key="user_input_text").input("Interacción 1 con uso").run()
    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "session_id": "sess_stale",
            "turn_id": 1,
            "decision": {
                "risk_level": "MEDIO",
                "action": "INFORMATIVE_ONLY",
                "response_to_user": "Turno 1",
                "reasoning": "Normal",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": {
                "prompt_tokens": 500,
                "completion_tokens": 100,
                "total_tokens": 600,
                "estimated_cost_usd": 0.002000,
                "mode": "live_api"
            },
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    metrics_map = {m.label: m.value for m in at.metric}
    assert metrics_map.get("Tokens Totales") == "600"

    # Interacción 2: sin telemetría (None)
    at.text_area(key="user_input_text").input("Interacción 2 sin uso").run()
    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent2:
        mock_agent2.return_value = {
            "status": "success",
            "session_id": "sess_stale",
            "turn_id": 2,
            "decision": {
                "risk_level": "BAJO",
                "action": "INFORMATIVE_ONLY",
                "response_to_user": "Turno 2",
                "reasoning": "Normal",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": None,
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    metrics_map2 = {m.label: m.value for m in at.metric}
    assert metrics_map2.get("Tokens Totales") == "N/D"
    assert metrics_map2.get("Tokens Entrada") == "N/D"
    assert metrics_map2.get("Costo Consulta") == "N/D"


def test_apptest_telemetry_mock_and_live_alternation():
    """
    Etapa 4 Escenario F: Alternancia entre respuestas MOCK y LIVE sintéticas:
    - Cada interacción conserva su fuente y badge.
    - Se contabilizan correctamente live_count y simulated_count.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    # Turno 1: MOCK
    at.text_area(key="user_input_text").input("Turno 1 en mock").run()
    with patch("src.agent.sentinel.SentinelAgent.process_message") as m1:
        m1.return_value = {
            "status": "success",
            "session_id": "sess_alt",
            "turn_id": 1,
            "decision": {
                "risk_level": "BAJO",
                "action": "INFORMATIVE_ONLY",
                "response_to_user": "Mock 1",
                "reasoning": "conversación cotidiana sin patrones",
                "analysis_source": "simulated",
                "simulated": True
            },
            "tool_results": {},
            "telemetry": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
                "mode": "simulated_local"
            },
            "simulated": True,
            "analysis_source": "simulated"
        }
        at.button(key="btn_analyze_main").click().run()

    # Turno 2: LIVE sintético
    at.text_area(key="user_input_text").input("Turno 2 en live").run()
    with patch("src.agent.sentinel.SentinelAgent.process_message") as m2:
        m2.return_value = {
            "status": "success",
            "session_id": "sess_alt",
            "turn_id": 2,
            "decision": {
                "risk_level": "CRÍTICO",
                "action": "BLOCK_AND_REPORT",
                "response_to_user": "Live 2",
                "reasoning": "Ataque bancario",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": {
                "prompt_tokens": 120,
                "completion_tokens": 80,
                "total_tokens": 200,
                "estimated_cost_usd": 0.001040,
                "mode": "live_api"
            },
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    s_tel = at.session_state["session_telemetry"]
    assert s_tel["interaction_count"] == 2
    assert s_tel["simulated_count"] == 1
    assert s_tel["live_count"] == 1
    assert s_tel["total_tokens"] == 200


# =============================================================================
# PRUEBAS DEL PROMPT 63821: QUINTA MÉTRICA «DIFERENCIA DE TOKENS» Y ELIMINACIÓN DE NOTA
# =============================================================================

def test_telemetry_token_difference_calculation_standard_case():
    """
    Verifica que la quinta métrica 'Diferencia de tokens' se calcule dinámicamente:
    token_difference = total_tokens - (prompt_tokens + completion_tokens)
    Caso de prueba oficial (Prompt 63821):
      prompt_tokens = 2359
      completion_tokens = 269
      total_tokens = 2808
      expected_difference = 180
      cost = $0.007408 USD
    Y verifica que no exista la antigua nota de observabilidad.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje de prueba cálculo de diferencia").run()
    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "session_id": "sess_diff_standard",
            "turn_id": 1,
            "decision": {
                "risk_level": "CRÍTICO",
                "action": "BLOCK_AND_REPORT",
                "response_to_user": "Alerta de fraude",
                "reasoning": "Diferencial de tokens activo",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": {
                "prompt_tokens": 2359,
                "completion_tokens": 269,
                "total_tokens": 2808,
                "estimated_cost_usd": 0.007408,
                "mode": "live_api"
            },
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    assert len(at.exception) == 0

    metrics_map = {m.label: m.value for m in at.metric}
    assert metrics_map.get("Tokens Entrada") == "2,359"
    assert metrics_map.get("Tokens Salida") == "269"
    assert metrics_map.get("Tokens Totales") == "2,808"
    assert metrics_map.get("Diferencia de tokens") == "180"
    assert metrics_map.get("Costo Consulta") == "$0.007408 USD"

    # Verificar que la antigua nota de observabilidad no existe en la interfaz
    all_captions = [c.value for c in at.caption]
    assert not any("Nota de observabilidad" in c for c in all_captions)


def test_telemetry_token_difference_negative_value_preserves_sign():
    """
    Verifica que si la diferencia es negativa, se conserve el signo (ej. -50).
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje prueba diferencia negativa").run()
    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "session_id": "sess_diff_neg",
            "turn_id": 1,
            "decision": {
                "risk_level": "MEDIO",
                "action": "INFORMATIVE_ONLY",
                "response_to_user": "Prueba",
                "reasoning": "Negativo",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": {
                "prompt_tokens": 150,
                "completion_tokens": 100,
                "total_tokens": 200,
                "estimated_cost_usd": 0.001300,
                "mode": "live_api"
            },
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    metrics_map = {m.label: m.value for m in at.metric}
    assert metrics_map.get("Tokens Entrada") == "150"
    assert metrics_map.get("Tokens Salida") == "100"
    assert metrics_map.get("Tokens Totales") == "200"
    assert metrics_map.get("Diferencia de tokens") == "-50"


def test_telemetry_token_difference_missing_fields_shows_nd():
    """
    Verifica que si alguno de los campos de tokens requeridos falta,
    la métrica 'Diferencia de tokens' muestre 'N/D'.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()

    at.text_area(key="user_input_text").input("Mensaje prueba campos incompletos").run()
    with patch("src.agent.sentinel.SentinelAgent.process_message") as mock_agent:
        mock_agent.return_value = {
            "status": "success",
            "session_id": "sess_diff_nd",
            "turn_id": 1,
            "decision": {
                "risk_level": "BAJO",
                "action": "INFORMATIVE_ONLY",
                "response_to_user": "Prueba ND",
                "reasoning": "ND",
                "analysis_source": "grok_4.7",
                "simulated": False
            },
            "tool_results": {},
            "telemetry": {
                "prompt_tokens": 100,
                # completion_tokens y total_tokens faltantes
            },
            "simulated": False,
            "analysis_source": "grok_4.7"
        }
        at.button(key="btn_analyze_main").click().run()

    metrics_map = {m.label: m.value for m in at.metric}
    assert metrics_map.get("Tokens Entrada") == "100"
    assert metrics_map.get("Tokens Salida") == "N/D"
    assert metrics_map.get("Tokens Totales") == "N/D"
    assert metrics_map.get("Diferencia de tokens") == "N/D"








