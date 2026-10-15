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
    has_sim_verdict = any("Veredicto del Agente (Modo Simulado)" in txt for txt in markdown_texts)
    assert has_sim_verdict, "Debe indicar 'Veredicto del Agente (Modo Simulado)'"


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


