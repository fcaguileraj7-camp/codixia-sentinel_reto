"""
SentinelGuard AI - Sistema de Diseño y Tokens Visuales
Identidad: Cyber Forest × Sage Sanctuary
Reto Agente 2026 - Platica.mx × Campuslands · Equipo Codixia
"""

from typing import Dict, Any

# 1. Paleta Oficial de Marca (Valores HEX Exactos)
THEME_COLORS: Dict[str, str] = {
    # Marca Principal
    "cyber_forest": "#102820",   # Navegación, encabezados y áreas principales
    "deep_forest": "#1B3830",    # Superficies oscuras secundarias y paneles
    "forest_green": "#426653",   # Botones principales y énfasis sobre fondos claros
    "digital_sage": "#83C6A3",   # Acciones e indicadores activos sobre fondos oscuros
    "soft_sage": "#B6D1B8",      # Iconos y detalles suaves
    "natural_ivory": "#F2F5EE",  # Texto claro sobre fondos oscuros
    "warm_ivory": "#F5F5ED",     # Fondo general de la aplicación
    
    # Colores de Apoyo
    "white": "#FFFFFF",          # Tarjetas, formularios y superficies de contenido
    "fog_green": "#E5EDE3",      # Bloques informativos y fondos suaves
    "slate_green": "#718477",    # Texto secundario verificado
    "soft_border": "#D8E0D6",    # Bordes, separadores y límites
    "title_dark": "#294638",     # Títulos sobre superficies claras
}

# 2. Colores Semánticos de Riesgo (Independientes de Marca)
RISK_COLORS: Dict[str, Dict[str, str]] = {
    "BAJO": {
        "bg": "#DCEBE0",
        "text": "#315D45",
        "border": "#B9DCBE",
        "label": "BAJO / SIN SEÑALES RELEVANTES",
        "icon": "🛡️",
        "description": "No se detectaron señales relevantes de riesgo dentro del alcance analizado."
    },
    "MEDIO": {
        "bg": "#F5E8C9",
        "text": "#795B22",
        "border": "#EAD198",
        "label": "PRECAUCIÓN / MEDIO",
        "icon": "⚠️",
        "description": "Existen indicios sospechosos que requieren atención y verificación prudente."
    },
    "ALTO": {
        "bg": "#F4D9D8",
        "text": "#8D3335",
        "border": "#E8B2B1",
        "label": "ALTO / CRÍTICO",
        "icon": "🚨",
        "description": "Se detectaron patrones inequívocos de estafa, suplantación o ingeniería social."
    },
    "CRÍTICO": {
        "bg": "#F4D9D8",
        "text": "#8D3335",
        "border": "#E8B2B1",
        "label": "CRÍTICO — AMENAZA CONFIRMADA",
        "icon": "🚨",
        "description": "Intento de fraude inminente con enlaces maliciosos o coacción psicológica."
    }
}

def get_theme_css() -> str:
    """Retorna las variables CSS raíz con la paleta oficial."""
    return f"""
    :root {{
        --sg-cyber-forest: {THEME_COLORS["cyber_forest"]};
        --sg-deep-forest: {THEME_COLORS["deep_forest"]};
        --sg-forest-green: {THEME_COLORS["forest_green"]};
        --sg-digital-sage: {THEME_COLORS["digital_sage"]};
        --sg-soft-sage: {THEME_COLORS["soft_sage"]};
        --sg-natural-ivory: {THEME_COLORS["natural_ivory"]};
        --sg-warm-ivory: {THEME_COLORS["warm_ivory"]};
        --sg-white: {THEME_COLORS["white"]};
        --sg-fog-green: {THEME_COLORS["fog_green"]};
        --sg-slate-green: {THEME_COLORS["slate_green"]};
        --sg-soft-border: {THEME_COLORS["soft_border"]};
        --sg-title-dark: {THEME_COLORS["title_dark"]};
        
        --sg-risk-low-bg: {RISK_COLORS["BAJO"]["bg"]};
        --sg-risk-low-text: {RISK_COLORS["BAJO"]["text"]};
        --sg-risk-med-bg: {RISK_COLORS["MEDIO"]["bg"]};
        --sg-risk-med-text: {RISK_COLORS["MEDIO"]["text"]};
        --sg-risk-high-bg: {RISK_COLORS["ALTO"]["bg"]};
        --sg-risk-high-text: {RISK_COLORS["ALTO"]["text"]};
    }}
    """
