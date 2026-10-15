"""
SentinelGuard AI - Hojas de Estilo CSS Avanzadas y Efectos Visuales
Identidad: Cyber Forest × Sage Sanctuary
Reto Agente 2026 - Platica.mx × Campuslands · Equipo Codixia
"""

from .theme import get_theme_css

def get_complete_css() -> str:
    """
    Genera el bloque completo de CSS para Streamlit con la paleta oficial,
    los 26 tipos de efectos interactivos (2 manifestaciones por tipo),
    soporte responsive y accesibilidad con prefers-reduced-motion.
    """
    theme_vars = get_theme_css()
    
    return f"""
    <style>
    {theme_vars}
    
    /* =========================================================================
       1. TIPOGRAFÍA Y CONFIGURACIÓN GLOBAL STREAMLIT
       ========================================================================= */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background-color: var(--sg-warm-ivory) !important;
        color: var(--sg-cyber-forest);
        color-scheme: light;
    }}
    
    /* Contenedor principal ajustado con espaciado balanceado */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        max-width: 1300px !important;
    }}
    
    /* Ocultar barra superior y menú por defecto de Streamlit para look premium */
    #MainMenu, header, footer {{
        visibility: hidden;
    }}
    header[data-testid="stHeader"] {{
        background: transparent !important;
        height: 0px !important;
    }}
    
    /* =========================================================================
       2. CURSORES PERSONALIZADOS (EFECTO 9: CUSTOM CURSOR - 2 MANIFESTACIONES)
       ========================================================================= */
    /* Manifestación 1: Zona de Escaneo Táctico de Amenazas */
    .sg-security-zone {{
        cursor: crosshair;
        cursor: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23426653' stroke-width='2'><circle cx='12' cy='12' r='8'/><line x1='12' y1='2' x2='12' y2='6'/><line x1='12' y1='18' x2='12' y2='22'/><line x1='2' y1='12' x2='6' y2='12'/><line x1='18' y1='12' x2='22' y2='12'/></svg>") 12 12, crosshair;
    }}
    /* Manifestación 2: Zona de Inspección de Enlaces y Dominios */
    .sg-inspect-zone {{
        cursor: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%231B3830' stroke-width='2'><circle cx='11' cy='11' r='7'/><line x1='21' y1='21' x2='16.65' y2='16.65'/></svg>") 10 10, pointer;
    }}

    /* =========================================================================
       3. EFECTOS DE DESPLAZAMIENTO (SCROLL: 1 A 5)
       ========================================================================= */
    /* EFECTO 2: SCROLL-DRIVEN ANIMATION - Manifestación 1: Barra de progreso fija */
    .sg-scroll-progress-bar {{
        position: fixed;
        top: 0;
        left: 0;
        height: 4px;
        width: 100%;
        background: linear-gradient(90deg, var(--sg-digital-sage), var(--sg-forest-green));
        z-index: 10000;
        transform-origin: 0% 50%;
        animation: sgScrollProgress 1s linear forwards;
    }}
    
    @keyframes sgScrollProgress {{
        from {{ transform: scaleX(0.08); }}
        to {{ transform: scaleX(1); }}
    }}
    
    /* EFECTO 3: STICKY / FLOATING - Manifestación 1: Barra de Navegación Pegajosa */
    .sg-sticky-header {{
        position: sticky;
        top: 0;
        z-index: 999;
        margin-bottom: 1.5rem;
        border-radius: 12px;
        background: rgba(16, 40, 32, 0.92);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(131, 198, 163, 0.25);
        box-shadow: 0 8px 32px rgba(16, 40, 32, 0.18);
        padding: 0.85rem 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.3s ease;
    }}
    
    /* EFECTO 3: STICKY / FLOATING - Manifestación 2: Indicador / Botón Flotante de SOS */
    .sg-floating-status-pill {{
        position: fixed;
        bottom: 24px;
        right: 28px;
        z-index: 9999;
        background: var(--sg-cyber-forest);
        color: var(--sg-natural-ivory);
        border: 1px solid var(--sg-digital-sage);
        border-radius: 50px;
        padding: 0.65rem 1.25rem;
        font-size: 0.85rem;
        font-weight: 600;
        box-shadow: 0 8px 24px rgba(16, 40, 32, 0.25);
        display: flex;
        align-items: center;
        gap: 8px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        text-decoration: none;
    }}
    .sg-floating-status-pill:hover {{
        transform: translateY(-3px);
        box-shadow: 0 12px 28px rgba(16, 40, 32, 0.35);
        color: var(--sg-digital-sage);
    }}
    
    /* EFECTO 1: PARALLAX SCROLLING - Manifestación 1: Hero con capas desacopladas */
    .sg-hero-container {{
        position: relative;
        overflow: hidden;
        border-radius: 14px;
        background: linear-gradient(135deg, var(--sg-cyber-forest) 0%, var(--sg-deep-forest) 60%, #152f26 100%);
        padding: 2.2rem 2.4rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(131, 198, 163, 0.2);
        box-shadow: 0 14px 40px rgba(16, 40, 32, 0.16);
    }}
    .sg-parallax-layer-bg {{
        position: absolute;
        top: -20px;
        right: -20px;
        width: 320px;
        height: 320px;
        background: radial-gradient(circle, rgba(131, 198, 163, 0.12) 0%, rgba(16, 40, 32, 0) 70%);
        pointer-events: none;
        transform: translateZ(0);
        transition: transform 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
    }}
    
    /* EFECTO 1: PARALLAX SCROLLING - Manifestación 2: Insignia de profundidad en tarjeta */
    .sg-parallax-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transform: translateZ(20px);
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    }}

    /* EFECTO 4: SCROLL SNAP Y CARRUSEL DE TELEMETRÍA - Manifestación 1: Carrusel continuo e interactivo */
    .sg-carousel-wrapper {{
        background: var(--sg-fog-green);
        border: 1.5px solid var(--sg-soft-border);
        border-radius: 16px;
        padding: 18px 20px 20px 20px;
        margin: 2rem 0 1.5rem 0;
        box-shadow: 0 4px 18px rgba(16, 40, 32, 0.05);
        position: relative;
        overflow: hidden;
    }}
    .sg-carousel-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        flex-wrap: wrap;
        gap: 12px;
    }}
    .sg-carousel-badge {{
        background: var(--sg-cyber-forest);
        color: var(--sg-digital-sage);
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 5px 12px;
        border-radius: 9999px;
        border: 1px solid rgba(131, 198, 163, 0.3);
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 2px 6px rgba(16, 40, 32, 0.2);
    }}
    .sg-carousel-title {{
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--sg-cyber-forest);
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }}
    .sg-carousel-hint {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.82rem;
        color: var(--sg-forest-green);
        font-weight: 600;
        background: rgba(255, 255, 255, 0.85);
        padding: 4px 12px;
        border-radius: 20px;
        border: 1px solid var(--sg-soft-border);
    }}
    .sg-carousel-beacon {{
        width: 8px;
        height: 8px;
        background: #2E7D32;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 rgba(46, 125, 50, 0.4);
        animation: sgBeaconPulse 2s infinite;
    }}
    .sg-carousel-viewport {{
        overflow: hidden;
        position: relative;
        width: 100%;
        padding: 6px 0;
        mask-image: linear-gradient(to right, transparent 0%, black 3%, black 97%, transparent 100%);
        -webkit-mask-image: linear-gradient(to right, transparent 0%, black 3%, black 97%, transparent 100%);
    }}
    .sg-carousel-track {{
        display: flex;
        gap: 20px;
        width: max-content;
        animation: sgCarouselScroll 32s linear infinite;
        scroll-snap-type: x mandatory;
    }}
    .sg-carousel-wrapper:hover .sg-carousel-track {{
        animation-play-state: paused;
    }}
    .sg-snap-carousel {{
        display: flex;
        gap: 20px;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        padding: 6px 0;
        scrollbar-width: thin;
        scrollbar-color: var(--sg-forest-green) var(--sg-fog-green);
    }}
    .sg-snap-carousel::-webkit-scrollbar {{
        height: 6px;
    }}
    .sg-snap-carousel::-webkit-scrollbar-thumb {{
        background: var(--sg-soft-sage);
        border-radius: 6px;
    }}
    .sg-snap-item, .sg-carousel-card {{
        flex: 0 0 290px;
        width: 290px;
        scroll-snap-align: start;
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease, border-color 0.25s ease;
        margin-bottom: 0 !important;
    }}
    .sg-snap-item:hover, .sg-carousel-card:hover {{
        transform: translateY(-5px) scale(1.02);
        box-shadow: 8px 12px 24px rgba(16, 40, 32, 0.12), -4px -4px 14px #ffffff !important;
        border-color: var(--sg-digital-sage) !important;
    }}
    @keyframes sgCarouselScroll {{
        0% {{
            transform: translateX(0);
        }}
        100% {{
            transform: translateX(-1240px);
        }}
    }}
    .sg-carousel-indicators {{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 14px;
        margin-top: 14px;
        flex-wrap: wrap;
    }}
    .sg-carousel-indicator-pill {{
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid var(--sg-soft-border);
        border-radius: 20px;
        padding: 4px 10px;
        font-size: 0.75rem;
        font-weight: 700;
        color: var(--sg-title-dark);
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 1px 4px rgba(16, 40, 32, 0.04);
    }}
    .sg-carousel-dot {{
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--sg-forest-green);
    }}
    
    /* EFECTO 4: SCROLL SNAP - Manifestación 2: Fila de selección rápida de ejemplos */
    .sg-snap-examples {{
        display: flex;
        gap: 10px;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        padding-bottom: 8px;
    }}
    .sg-snap-example-chip {{
        flex: 0 0 auto;
        scroll-snap-align: start;
    }}

    /* EFECTO 5: INFINITE SCROLL / CARGA PROGRESIVA - 2 Manifestaciones */
    .sg-infinite-cases-container {{
        max-height: 440px;
        overflow-y: auto;
        padding-right: 8px;
        scrollbar-width: thin;
        scrollbar-color: var(--sg-forest-green) var(--sg-fog-green);
    }}
    .sg-infinite-audit-log {{
        max-height: 260px;
        overflow-y: auto;
        border: 1px solid var(--sg-soft-border);
        border-radius: 10px;
        padding: 12px;
        background: #FAFCF9;
    }}

    /* =========================================================================
       4. EFECTOS DE INTERACCIÓN (HOVER, CLICK, TILT, REVEAL, RIPPLE)
       ========================================================================= */
    /* EFECTO 6: HOVER STATE - Manifestación 1: Elevación de tarjetas */
    .sg-card {{
        background: var(--sg-white);
        border: 1px solid var(--sg-soft-border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 2px 8px rgba(16, 40, 32, 0.04);
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), 
                    box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                    border-color 0.25s ease;
    }}
    .sg-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 10px 24px rgba(16, 40, 32, 0.08);
        border-color: #B6D1B8;
    }}
    
    /* EFECTO 6: HOVER STATE - Manifestación 2: Botones principales Streamlit */
    div.stButton > button:first-child,
    .sg-btn-primary {{
        background-color: var(--sg-forest-green) !important;
        color: var(--sg-white) !important;
        border-radius: 10px !important;
        border: 1px solid #365545 !important;
        font-weight: 600 !important;
        padding: 0.65rem 1.6rem !important;
        transition: all 0.22s cubic-bezier(0.2, 0, 0, 1) !important;
        box-shadow: 0 4px 12px rgba(66, 102, 83, 0.2) !important;
    }}
    div.stButton > button:first-child:hover,
    .sg-btn-primary:hover {{
        background-color: var(--sg-deep-forest) !important;
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 6px 18px rgba(27, 56, 48, 0.3) !important;
        border-color: var(--sg-digital-sage) !important;
    }}
    div.stButton > button:first-child:active {{
        transform: translateY(0px) scale(0.99) !important;
    }}
    
    /* EFECTO 7: REVEAL EFFECT - Manifestación 1: Revelación en Hover de detalles técnicos */
    .sg-hover-reveal-box {{
        position: relative;
        overflow: hidden;
        border-radius: 10px;
        background: var(--sg-white);
        border: 1px solid var(--sg-soft-border);
        padding: 1.2rem;
        transition: all 0.3s ease;
    }}
    .sg-hover-reveal-box .sg-reveal-hidden {{
        max-height: 0;
        opacity: 0;
        overflow: hidden;
        transition: max-height 0.35s ease, opacity 0.35s ease;
    }}
    .sg-hover-reveal-box:hover .sg-reveal-hidden {{
        max-height: 180px;
        opacity: 1;
        margin-top: 10px;
    }}
    
    /* EFECTO 7: REVEAL EFFECT - Manifestación 2: Término Glosario Contextual */
    .sg-term-reveal {{
        display: inline-block;
        border-bottom: 1px dashed var(--sg-forest-green);
        cursor: help;
        position: relative;
    }}
    .sg-term-reveal:hover::after {{
        content: attr(data-explanation);
        position: absolute;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        background: var(--sg-cyber-forest);
        color: var(--sg-natural-ivory);
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.78rem;
        white-space: nowrap;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    }}
    
    /* EFECTO 8: TOOLTIP / POPOVER - Manifestación 1: Tooltip con flecha en Badges */
    .sg-tooltip {{
        position: relative;
        display: inline-flex;
        cursor: pointer;
    }}
    .sg-tooltip::before {{
        content: attr(data-tooltip);
        position: absolute;
        bottom: 130%;
        left: 50%;
        transform: translateX(-50%) translateY(4px);
        background: var(--sg-cyber-forest);
        color: var(--sg-natural-ivory);
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        line-height: 1.25;
        white-space: nowrap;
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
        transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
        z-index: 2000;
        box-shadow: 0 6px 16px rgba(16, 40, 32, 0.3);
        border: 1px solid rgba(131, 198, 163, 0.3);
    }}
    .sg-tooltip:hover::before {{
        opacity: 1;
        visibility: visible;
        transform: translateX(-50%) translateY(0);
    }}
    
    /* EFECTO 8: TOOLTIP / POPOVER - Manifestación 2: Popover Box */
    .sg-popover-trigger {{
        position: relative;
        display: inline-block;
    }}
    .sg-popover-box {{
        display: none;
        position: absolute;
        top: 100%;
        right: 0;
        width: 260px;
        background: var(--sg-white);
        border: 1px solid var(--sg-soft-border);
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.12);
        z-index: 1500;
        font-size: 0.82rem;
    }}
    .sg-popover-trigger:hover .sg-popover-box {{
        display: block;
        animation: sgFadeIn 0.2s ease forwards;
    }}

    /* EFECTO 10: RIPPLE EFFECT - Manifestación 1: Botones con onda expansiva */
    .sg-ripple-btn {{
        position: relative;
        overflow: hidden;
    }}
    .sg-ripple-btn::after {{
        content: "";
        position: absolute;
        top: 50%;
        left: 50%;
        width: 10px;
        height: 10px;
        background: rgba(255, 255, 255, 0.5);
        opacity: 0;
        border-radius: 100%;
        transform: scale(1, 1) translate(-50%);
        transform-origin: 50% 50%;
    }}
    .sg-ripple-btn:focus:not(:active)::after {{
        animation: sgRippleAnim 0.6s ease-out;
    }}
    @keyframes sgRippleAnim {{
        0% {{ transform: scale(0, 0); opacity: 0.5; }}
        20% {{ transform: scale(25, 25); opacity: 0.3; }}
        100% {{ opacity: 0; transform: scale(40, 40); }}
    }}
    
    /* EFECTO 10: RIPPLE EFFECT - Manifestación 2: Chips de ejemplos con onda al toque */
    .sg-case-chip {{
        position: relative;
        overflow: hidden;
        background: var(--sg-fog-green);
        border: 1px solid var(--sg-soft-border);
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 0.82rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    .sg-case-chip:hover {{
        background: #D5E4D2;
        border-color: var(--sg-forest-green);
    }}
    .sg-case-chip:active::after {{
        content: "";
        position: absolute;
        inset: 0;
        background: rgba(66, 102, 83, 0.25);
        border-radius: inherit;
        animation: sgFadeOutSubtle 0.4s ease;
    }}

    /* EFECTO 11: TILT EFFECT - Manifestación 1: Tilt 3D moderado en Tarjeta Grok */
    .sg-tilt-card {{
        transform-style: preserve-3d;
        perspective: 1000px;
        transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
    }}
    .sg-tilt-card:hover {{
        transform: rotateX(4deg) rotateY(-4deg) translateY(-4px);
    }}
    
    /* EFECTO 11: TILT EFFECT - Manifestación 2: Tilt sutil en Tarjetas de Métricas */
    .sg-metric-tilt {{
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }}
    .sg-metric-tilt:hover {{
        transform: rotateZ(1deg) translateY(-3px);
        box-shadow: 0 8px 20px rgba(16, 40, 32, 0.08);
    }}

    /* =========================================================================
       5. TRANSICIONES Y CAMBIO DE VISTA (12 A 16)
       ========================================================================= */
    /* EFECTO 12: FADE-IN / FADE-OUT - Manifestación 1: Aparición suave */
    @keyframes sgFadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}
    .sg-fade-in {{
        animation: sgFadeIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}
    /* EFECTO 12: FADE-IN / FADE-OUT - Manifestación 2: Desvanecimiento sutil */
    @keyframes sgFadeOutSubtle {{
        from {{ opacity: 1; }}
        to {{ opacity: 0; }}
    }}

    /* EFECTO 13: SLIDE-IN / SLIDE-OUT - Manifestación 1: Deslizamiento Horizontal */
    @keyframes sgSlideInRight {{
        from {{ opacity: 0; transform: translateX(20px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}
    .sg-slide-in-right {{
        animation: sgSlideInRight 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}
    
    /* EFECTO 13: SLIDE-IN / SLIDE-OUT - Manifestación 2: Deslizamiento Vertical Ascendente */
    @keyframes sgSlideInUp {{
        from {{ opacity: 0; transform: translateY(18px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .sg-slide-in-up {{
        animation: sgSlideInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}

    /* EFECTO 14: PAGE / TAB TRANSITIONS - Manifestación 1: Transición entre pestañas Streamlit */
    div[data-baseweb="tab-panel"] {{
        animation: sgTabFade 0.35s cubic-bezier(0.2, 0.8, 0.2, 1);
    }}
    @keyframes sgTabFade {{
        from {{ opacity: 0.3; transform: translateY(6px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    /* EFECTO 14: PAGE / TAB TRANSITIONS - Manifestación 2: Estilo de pestaña activa */
    div[data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: transparent !important;
        border-bottom: 2px solid var(--sg-soft-border) !important;
        padding-bottom: 4px;
        margin-bottom: 1.5rem;
    }}
    div[data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0 !important;
        padding: 0.65rem 1.25rem !important;
        font-weight: 600 !important;
        color: var(--sg-slate-green) !important;
        background: transparent !important;
        transition: all 0.2s ease !important;
    }}
    div[data-baseweb="tab"][aria-selected="true"] {{
        color: var(--sg-cyber-forest) !important;
        border-bottom: 3px solid var(--sg-forest-green) !important;
        background: rgba(66, 102, 83, 0.08) !important;
    }}

    /* EFECTO 15: LAZY LOADING EFFECT - Manifestación 1: Contenedor con revelación diferida */
    .sg-lazy-container {{
        opacity: 0;
        animation: sgLazyReveal 0.5s 0.15s ease-out forwards;
    }}
    @keyframes sgLazyReveal {{
        to {{ opacity: 1; }}
    }}
    /* EFECTO 15: LAZY LOADING EFFECT - Manifestación 2: Carga diferida en expanders */
    .streamlit-expanderContent {{
        animation: sgFadeIn 0.3s ease;
    }}

    /* EFECTO 16: SKELETON SCREEN - Manifestación 1: Skeleton Box Shimmer */
    .sg-skeleton-box {{
        width: 100%;
        height: 80px;
        border-radius: 10px;
        background: linear-gradient(90deg, #EBEFE8 25%, #F7FAF5 50%, #EBEFE8 75%);
        background-size: 200% 100%;
        animation: sgShimmer 1.5s infinite;
        margin-bottom: 12px;
    }}
    @keyframes sgShimmer {{
        0% {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}
    /* EFECTO 16: SKELETON SCREEN - Manifestación 2: Skeleton Line Shimmer */
    .sg-skeleton-line {{
        height: 16px;
        border-radius: 4px;
        background: linear-gradient(90deg, #EBEFE8 25%, #F7FAF5 50%, #EBEFE8 75%);
        background-size: 200% 100%;
        animation: sgShimmer 1.5s infinite;
        margin-bottom: 8px;
    }}

    /* =========================================================================
       6. EFECTOS VISUALES DE FONDO Y ATMÓSFERA (17 A 21)
       ========================================================================= */
    /* EFECTO 17: PARTICLE EFFECT - Manifestación 1: Malla SVG de partículas conectadas */
    .sg-particle-grid {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0.12;
        background-image: radial-gradient(var(--sg-digital-sage) 1px, transparent 1px);
        background-size: 24px 24px;
        pointer-events: none;
    }}
    /* EFECTO 17: PARTICLE EFFECT - Manifestación 2: Puntos de baliza pulsante */
    .sg-particle-beacon {{
        width: 10px;
        height: 10px;
        background: var(--sg-digital-sage);
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 rgba(131, 198, 163, 0.4);
        animation: sgBeaconPulse 2s infinite;
    }}
    @keyframes sgBeaconPulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(131, 198, 163, 0.7); }}
        70% {{ box-shadow: 0 0 0 8px rgba(131, 198, 163, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(131, 198, 163, 0); }}
    }}

    /* EFECTO 18: GRADIENT ANIMATION - Manifestación 1: Flujo continuo en cabecera */
    .sg-gradient-animated {{
        background: linear-gradient(125deg, #102820, #1B3830, #254438, #102820);
        background-size: 300% 300%;
        animation: sgGradientFlow 12s ease infinite;
    }}
    @keyframes sgGradientFlow {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    /* EFECTO 18: GRADIENT ANIMATION - Manifestación 2: Borde animado perimetral */
    .sg-animated-gradient-border {{
        position: relative;
        border-radius: 12px;
        border: 2px solid transparent;
        background: linear-gradient(white, white) padding-box,
                    linear-gradient(90deg, var(--sg-digital-sage), var(--sg-forest-green), var(--sg-digital-sage)) border-box;
        background-size: 200% 100%;
        animation: sgBorderGradient 6s linear infinite;
    }}
    @keyframes sgBorderGradient {{
        0% {{ background-position: 0% 0%; }}
        100% {{ background-position: 200% 0%; }}
    }}

    /* EFECTO 19: GLASSMORPHISM - Manifestación 1: Vidrio Oscuro Cyber Forest */
    .sg-glass-dark {{
        background: rgba(16, 40, 32, 0.88);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(131, 198, 163, 0.2);
    }}
    /* EFECTO 19: GLASSMORPHISM - Manifestación 2: Vidrio Claro Sage Sanctuary */
    .sg-glass-light {{
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(216, 224, 214, 0.8);
    }}

    /* EFECTO 20: KEN BURNS EFFECT - Manifestación 1: Zoom y paneo en gráfico de Hero */
    .sg-kenburns-shield {{
        animation: sgKenBurns 18s ease-in-out infinite alternate;
        transform-origin: center center;
    }}
    @keyframes sgKenBurns {{
        0% {{ transform: scale(1) translate(0, 0); }}
        50% {{ transform: scale(1.08) translate(-4px, 3px); }}
        100% {{ transform: scale(1.03) translate(3px, -2px); }}
    }}
    /* EFECTO 20: KEN BURNS EFFECT - Manifestación 2: Paneo sutil en insignia policial */
    .sg-kenburns-badge {{
        animation: sgKenBurnsSubtle 12s ease-in-out infinite alternate;
    }}
    @keyframes sgKenBurnsSubtle {{
        0% {{ transform: scale(1); }}
        100% {{ transform: scale(1.05); }}
    }}

    /* EFECTO 21: MARQUEE - Manifestación 1: Cinta de telemetría de amenazas superior */
    .sg-marquee-container {{
        overflow: hidden;
        white-space: nowrap;
        background: var(--sg-cyber-forest);
        color: var(--sg-natural-ivory);
        padding: 0.45rem 0;
        font-size: 0.76rem;
        font-weight: 500;
        border-radius: 6px;
        margin-bottom: 1.25rem;
        border: 1px solid rgba(131, 198, 163, 0.2);
    }}
    .sg-marquee-track {{
        display: inline-block;
        padding-left: 100%;
        animation: sgMarquee 28s linear infinite;
    }}
    @keyframes sgMarquee {{
        0% {{ transform: translate(0, 0); }}
        100% {{ transform: translate(-100%, 0); }}
    }}
    /* EFECTO 21: MARQUEE - Manifestación 2: Cinta de consejos ciudadanos en footer */
    .sg-marquee-footer-track {{
        display: inline-block;
        padding-left: 100%;
        animation: sgMarquee 100s linear infinite;
    }}

    /* =========================================================================
       7. EFECTOS DE DISTORSIÓN Y TEXTURAS AVANZADAS (22 A 26)
       ========================================================================= */
    /* EFECTO 22: LIQUID DISTORTION - Manifestación 1: Morfología líquida orgánica */
    .sg-liquid-morph {{
        border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
        animation: sgLiquidMorph 8s ease-in-out infinite;
        transition: all 1s ease-in-out;
    }}
    @keyframes sgLiquidMorph {{
        0% {{ border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }}
        50% {{ border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; }}
        100% {{ border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }}
    }}
    /* EFECTO 22: LIQUID DISTORTION - Manifestación 2: Pulso líquido en botón */
    .sg-liquid-pulse {{
        animation: sgLiquidPulseAnim 3s infinite;
    }}
    @keyframes sgLiquidPulseAnim {{
        0% {{ box-shadow: 0 0 0 0 rgba(66, 102, 83, 0.4); }}
        70% {{ box-shadow: 0 0 0 12px rgba(66, 102, 83, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(66, 102, 83, 0); }}
    }}

    /* EFECTO 23: GLITCH EFFECT - Manifestación 1: Micro-glitch en Alerta Crítica */
    .sg-glitch-text {{
        position: relative;
        display: inline-block;
        animation: sgGlitchText 4s infinite;
    }}
    @keyframes sgGlitchText {{
        0%, 92%, 100% {{ transform: none; opacity: 1; }}
        93% {{ transform: skewX(-2deg); opacity: 0.9; }}
        94% {{ transform: skewX(2deg); }}
        95% {{ transform: translate(-1px, 1px); }}
        96% {{ transform: translate(1px, -1px); }}
    }}
    /* EFECTO 23: GLITCH EFFECT - Manifestación 2: Glitch en etiqueta de radicado CAI */
    .sg-glitch-badge {{
        position: relative;
        display: inline-block;
        animation: sgGlitchSubtle 6s infinite;
    }}
    @keyframes sgGlitchSubtle {{
        0%, 94%, 100% {{ opacity: 1; }}
        95% {{ opacity: 0.8; transform: translateX(1px); }}
        96% {{ opacity: 1; transform: translateX(0); }}
    }}

    /* EFECTO 24: TYPING EFFECT - Manifestación 1: Tipeo animado en Lema de Cabecera */
    .sg-typing-container {{
        display: inline-block;
        overflow: hidden;
        white-space: nowrap;
        border-right: 2px solid var(--sg-digital-sage);
        animation: sgTyping 3.5s steps(42, end), sgBlink 0.75s step-end infinite;
    }}
    @keyframes sgTyping {{
        from {{ width: 0; }}
        to {{ width: 100%; }}
    }}
    @keyframes sgBlink {{
        from, to {{ border-color: transparent; }}
        50% {{ border-color: var(--sg-digital-sage); }}
    }}
    /* EFECTO 24: TYPING EFFECT - Manifestación 2: Subtítulo con tipeo de consola */
    .sg-typing-sub {{
        display: inline-block;
        overflow: hidden;
        white-space: nowrap;
        border-right: 2px solid var(--sg-soft-sage);
        animation: sgTyping 2.8s steps(35, end), sgBlink 0.75s step-end infinite;
    }}

    /* EFECTO 25: TEXT MASKING - Manifestación 1: Título de Marca con Máscara Degradada */
    .sg-text-masked-title {{
        background: linear-gradient(135deg, var(--sg-digital-sage) 0%, var(--sg-natural-ivory) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
        font-weight: 800;
        letter-spacing: -0.02em;
    }}
    /* EFECTO 25: TEXT MASKING - Manifestación 2: Métricas numéricas con máscara sage */
    .sg-text-masked-metric {{
        background: linear-gradient(135deg, var(--sg-title-dark) 0%, var(--sg-forest-green) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.2rem;
        line-height: 1;
    }}

    /* EFECTO 26: NEUMORPHISM - Manifestación 1: Relieve neumórfico suave */
    .sg-neumorphic-card {{
        background: var(--sg-warm-ivory);
        border-radius: 14px;
        box-shadow: 6px 6px 14px #e3e8de, -6px -6px 14px #ffffff;
        border: 1px solid rgba(216, 224, 214, 0.4);
        padding: 1.5rem;
        margin-bottom: 1.25rem;
    }}
    /* EFECTO 26: NEUMORPHISM - Manifestación 2: Bajo relieve neumórfico hundido */
    .sg-neumorphic-inset {{
        background: var(--sg-warm-ivory);
        border-radius: 10px;
        box-shadow: inset 2px 2px 5px #dce2d7, inset -2px -2px 5px #ffffff;
        padding: 0.75rem 1rem;
    }}

    /* =========================================================================
       8. COMPONENTES SEMÁNTICOS DE RIESGO (INDEPENDIENTES DE MARCA)
       ========================================================================= */
    .sg-risk-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.95rem;
        letter-spacing: 0.02em;
        margin-bottom: 1rem;
    }}
    .sg-risk-low {{
        background-color: var(--sg-risk-low-bg);
        color: var(--sg-risk-low-text);
        border: 1px solid #B9DCBE;
    }}
    .sg-risk-medium {{
        background-color: var(--sg-risk-med-bg);
        color: var(--sg-risk-med-text);
        border: 1px solid #EAD198;
    }}
    .sg-risk-high, .sg-risk-critical {{
        background-color: var(--sg-risk-high-bg);
        color: var(--sg-risk-high-text);
        border: 1px solid #E8B2B1;
    }}

    /* Tarjeta de Veredicto */
    .sg-verdict-box {{
        background: var(--sg-white);
        border-left: 5px solid var(--sg-forest-green);
        border-radius: 0 10px 10px 0;
        padding: 1.25rem 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 14px rgba(16, 40, 32, 0.05);
    }}
    .sg-verdict-title {{
        color: var(--sg-title-dark);
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .sg-verdict-text {{
        color: #2F3E35;
        font-size: 0.95rem;
        line-height: 1.6;
        margin: 0;
    }}

    /* =========================================================================
       9. ESTILIZACIÓN DE ENTRADAS, TEXTAREA Y DATAFRAME DE STREAMLIT
       ========================================================================= */
    .stTextArea textarea, .stTextInput input {{
        background-color: var(--sg-white) !important;
        border: 1px solid var(--sg-soft-border) !important;
        border-radius: 8px !important;
        color: var(--sg-cyber-forest) !important;
        font-size: 0.92rem !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}
    .stTextArea textarea:focus, .stTextInput input:focus {{
        border-color: var(--sg-forest-green) !important;
        box-shadow: 0 0 0 3px rgba(66, 102, 83, 0.15) !important;
    }}
    
    /* Contenedor Dataframe */
    div[data-testid="stDataFrame"] {{
        border-radius: 10px;
        border: 1px solid var(--sg-soft-border);
        overflow: hidden;
        background: var(--sg-white);
    }}

    /* =========================================================================
       10. ACCESIBILIDAD: PREFERS-REDUCED-MOTION
       ========================================================================= */
    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }}
        .sg-scroll-progress-bar,
        .sg-marquee-track,
        .sg-marquee-footer-track,
        .sg-glitch-text,
        .sg-liquid-morph,
        .sg-kenburns-shield,
        .sg-tilt-card:hover,
        .sg-typing-container,
        .sg-carousel-track {{
            animation: none !important;
            transform: none !important;
            width: auto !important;
            border-right: none !important;
        }}
    }}
    
    /* =========================================================================
       11. RESPONSIVE DESIGN (MÓVIL Y TABLET)
       ========================================================================= */
    @media (max-width: 768px) {{
        .sg-sticky-header {{
            flex-direction: column;
            gap: 10px;
            align-items: flex-start;
            padding: 0.75rem 1rem;
        }}
        .sg-hero-container {{
            padding: 1.5rem 1.25rem;
        }}
        .sg-text-masked-title {{
            font-size: 1.7rem !important;
        }}
        .sg-floating-status-pill {{
            bottom: 12px;
            right: 12px;
            padding: 0.5rem 1rem;
            font-size: 0.78rem;
        }}
    }}
    </style>
    """
