"""
SentinelGuard AI - Módulo de UI y Experiencia de Usuario (Streamlit)
Reto Agente 2026 - Platica.mx × Campuslands · Equipo Codixia
Rol 5: Juan José (Dataset Engineering, Stress Testing & UI)
"""

from .theme import THEME_COLORS, RISK_COLORS, get_theme_css
from .components import (
    render_header,
    render_navigation_status,
    render_metric_cards,
    render_risk_badge,
    render_verdict_card,
    render_threat_findings,
    render_cai_protocol_card,
    render_marquee_ticker,
    render_footer,
    render_example_selector,
)

__all__ = [
    "THEME_COLORS",
    "RISK_COLORS",
    "get_theme_css",
    "render_header",
    "render_navigation_status",
    "render_metric_cards",
    "render_risk_badge",
    "render_verdict_card",
    "render_threat_findings",
    "render_cai_protocol_card",
    "render_marquee_ticker",
    "render_footer",
    "render_example_selector",
]
