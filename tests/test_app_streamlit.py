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
