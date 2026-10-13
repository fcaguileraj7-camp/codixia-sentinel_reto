"""
SentinelGuard AI - Componentes Visuales y Estructura de Interfaz
Identidad: Cyber Forest × Sage Sanctuary (Inspirado en Snyk & SecurityScorecard)
Reto Agente 2026 - Platica.mx × Campuslands · Equipo Codixia
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from .theme import THEME_COLORS, RISK_COLORS

def render_html(html_str: str) -> None:
    """
    Renderiza HTML en Streamlit eliminando líneas en blanco intermedias.
    Esto previene que el parser de CommonMark (MarkdownIt) de Streamlit interprete
    las líneas indentadas después de un salto de línea como bloques de código (<pre><code>).
    """
    cleaned = "\n".join(line for line in html_str.strip().splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)

def render_navigation_status():
    """
    Renderiza la barra superior pegajosa con efecto Glassmorphism y estado en vivo.
    (Efecto 3: Sticky Element + Efecto 19: Glassmorphism + Efecto 17: Particle Beacon + Efecto 24: Typing)
    """
    html = """
    <div class="sg-scroll-progress-bar"></div>
    <div class="sg-sticky-header">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div class="sg-parallax-badge" style="font-size: 1.3rem;">🛡️</div>
            <div>
                <span style="font-weight: 800; color: var(--sg-natural-ivory); font-size: 1.05rem; letter-spacing: -0.01em;">
                    SentinelGuard <span style="color: var(--sg-digital-sage);">AI</span>
                </span>
                <span style="display: block; font-size: 0.72rem; color: var(--sg-soft-sage);">
                    Reto Agente 2026 · Platica.mx × Campuslands · Equipo Codixia
                </span>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="display: flex; align-items: center; gap: 8px; background: rgba(0,0,0,0.25); padding: 5px 12px; border-radius: 20px; border: 1px solid rgba(131, 198, 163, 0.2);">
                <span class="sg-particle-beacon"></span>
                <span style="font-size: 0.76rem; color: var(--sg-digital-sage); font-weight: 600;">
                    NÚCLEO GROK 4.7 ACTIVO
                </span>
            </div>
            <div class="sg-tooltip" data-tooltip="Modo Local Resiliente (Costo $0.00 USD)">
                <span style="background: rgba(131, 198, 163, 0.15); color: var(--sg-soft-sage); font-size: 0.72rem; padding: 4px 10px; border-radius: 6px; font-weight: 600; border: 1px solid rgba(131, 198, 163, 0.3);">
                    ⚡ T-Max: 500
                </span>
            </div>
        </div>
    </div>
    """
    render_html(html)

def render_header():
    """
    Renderiza el Hero Banner principal de SentinelGuard AI.
    (Efecto 1: Parallax Hero, Efecto 17: Particle Grid, Efecto 18: Gradient Animation,
     Efecto 20: Ken Burns, Efecto 22: Liquid Morph, Efecto 24: Typing Headline, Efecto 25: Text Masked Title)
    """
    html = """
    <div class="sg-hero-container sg-gradient-animated">
        <div class="sg-particle-grid"></div>
        <div class="sg-parallax-layer-bg"></div>
        <div style="position: relative; z-index: 2; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
            <div style="max-width: 780px;">
                <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(131, 198, 163, 0.15); border: 1px solid rgba(131, 198, 163, 0.3); border-radius: 20px; padding: 4px 14px; margin-bottom: 12px;">
                    <span style="font-size: 0.8rem;">🇨🇴</span>
                    <span style="color: var(--sg-digital-sage); font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                        Defensa Digital Ciudadana contra Ciberdelitos
                    </span>
                </div>
                <h1 class="sg-text-masked-title" style="margin: 0 0 10px 0; font-size: 2.35rem; line-height: 1.15;">
                    SENTINELGUARD AI
                </h1>
                <div style="margin-bottom: 14px; height: 26px;">
                    <p class="sg-typing-container" style="color: var(--sg-natural-ivory); font-size: 1.05rem; font-weight: 500; margin: 0;">
                        El Escudo Digital Ciudadano contra Estafas y Extorsiones
                    </p>
                </div>
                <p style="color: #C8DCD0; font-size: 0.88rem; line-height: 1.5; margin: 0; max-width: 660px;">
                    Inspección autónoma multi-herramienta con Grok 4.7. Neutraliza phishing bancario, manipulación de ingeniería social y extorsión por WhatsApp con radicación formal ante el <strong>CAI Virtual de la Policía Nacional</strong>.
                </p>
            </div>
            <div style="text-align: center; position: relative;">
                <div class="sg-tilt-card" style="display: inline-block;">
                    <div class="sg-liquid-morph sg-kenburns-shield" style="width: 120px; height: 120px; background: linear-gradient(135deg, var(--sg-digital-sage), var(--sg-forest-green)); display: flex; align-items: center; justify-content: center; box-shadow: 0 10px 30px rgba(0,0,0,0.35);">
                        <span style="font-size: 3.2rem; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));">🛡️</span>
                    </div>
                </div>
                <div style="margin-top: 8px;">
                    <span style="background: rgba(16, 40, 32, 0.7); color: var(--sg-digital-sage); font-size: 0.7rem; padding: 3px 10px; border-radius: 12px; font-weight: 600; border: 1px solid rgba(131, 198, 163, 0.25);">
                        CODIXIA AGENTS
                    </span>
                </div>
            </div>
        </div>
    </div>
    """
    render_html(html)

def render_marquee_ticker():
    """
    Renderiza la cinta continua de telemetría de amenazas del sistema.
    (Efecto 21: Marquee - Manifestación 1)
    """
    html = """
    <div class="sg-marquee-container">
        <div class="sg-marquee-track">
            <span>🛡️ ESTADO DE DEFENSA: VIGILANCIA ACTIVA</span> &nbsp;&nbsp;•&nbsp;&nbsp;
            <span>🔍 MOTOR DE AMENAZAS: GROK 4.7 (xAI)</span> &nbsp;&nbsp;•&nbsp;&nbsp;
            <span>📊 CASOS CERTIFICADOS: 30 CASOS REALES EVALUADOS</span> &nbsp;&nbsp;•&nbsp;&nbsp;
            <span>🚨 PROTOCOLO CAI VIRTUAL: caivirtual.policia.gov.co INTEGRADO</span> &nbsp;&nbsp;•&nbsp;&nbsp;
            <span>⏱️ TIEMPO DE RESPUESTA: &lt; 2.5 SEGUNDOS</span> &nbsp;&nbsp;•&nbsp;&nbsp;
            <span>🛑 TYPOSQUATTING: FILTROS PARA BANCOLOMBIA, NEQUI, DAVIPLATA</span> &nbsp;&nbsp;•&nbsp;&nbsp;
            <span>💰 MODO LOCAL RESILIENTE: CONSUMO CONTROLADO $0.00 USD</span>
        </div>
    </div>
    """
    render_html(html)

def render_metric_cards():
    """
    Renderiza tarjetas métricas de seguridad al estilo SecurityScorecard / Snyk.
    (Efecto 11: Tilt Effect 2, Efecto 25: Text Masked Metric 2, Efecto 26: Neumorphism 1, Efecto 4: Scroll Snap 1)
    """
    html = """
    <div class="sg-snap-carousel">
        <div class="sg-snap-item sg-neumorphic-card sg-metric-tilt">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: var(--sg-slate-green); letter-spacing: 0.05em;">Defensa Multicapa</span>
                <span style="font-size: 1.1rem;">⚡</span>
            </div>
            <div class="sg-text-masked-metric">3 Tools</div>
            <div style="font-size: 0.8rem; color: #52685B; margin-top: 4px;">ThreatInspector + UrlSandbox + PoliceReporter sincronizados.</div>
        </div>
        <div class="sg-snap-item sg-neumorphic-card sg-metric-tilt">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: var(--sg-slate-green); letter-spacing: 0.05em;">Dataset S3</span>
                <span style="font-size: 1.1rem;">📊</span>
            </div>
            <div class="sg-text-masked-metric">30 Casos</div>
            <div style="font-size: 0.8rem; color: #52685B; margin-top: 4px;">Phishing, extorsión carcelaria, suplantación y ofertas trampa.</div>
        </div>
        <div class="sg-snap-item sg-neumorphic-card sg-metric-tilt">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: var(--sg-slate-green); letter-spacing: 0.05em;">Respaldo Policial</span>
                <span style="font-size: 1.1rem;">📜</span>
            </div>
            <div class="sg-text-masked-metric">100% CAI</div>
            <div style="font-size: 0.8rem; color: #52685B; margin-top: 4px;">Expedientes técnicos formateados para radicación judicial.</div>
        </div>
        <div class="sg-snap-item sg-neumorphic-card sg-metric-tilt">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: var(--sg-slate-green); letter-spacing: 0.05em;">Eficiencia Tokens</span>
                <span style="font-size: 1.1rem;">🎯</span>
            </div>
            <div class="sg-text-masked-metric">&le; 500</div>
            <div style="font-size: 0.8rem; color: #52685B; margin-top: 4px;">Tope estricto de tokens y fallback local a $0.00 USD.</div>
        </div>
    </div>
    """
    render_html(html)

def render_risk_badge(risk_level: str) -> None:
    """
    Renderiza la insignia de nivel de riesgo con colores semánticos exactos.
    (Colores semánticos: Bajo #DCEBE0/#315D45, Medio #F5E8C9/#795B22, Alto #F4D9D8/#8D3335)
    (Efecto 8: Tooltip 1 + Efecto 23: Glitch Text 1 en riesgo crítico)
    """
    risk_data = RISK_COLORS.get(risk_level.upper(), RISK_COLORS["MEDIO"])
    css_class = "sg-risk-medium"
    if risk_level.upper() in ["CRÍTICO", "CRITICO", "ALTO"]:
        css_class = "sg-risk-critical"
    elif risk_level.upper() == "BAJO":
        css_class = "sg-risk-low"

    glitch_class = "sg-glitch-text" if risk_level.upper() in ["CRÍTICO", "CRITICO", "ALTO"] else ""

    html = f"""
    <div class="sg-tooltip" data-tooltip="{risk_data['description']}">
        <div class="sg-risk-badge {css_class}">
            <span>{risk_data['icon']}</span>
            <span class="{glitch_class}">NIVEL DE AMENAZA: {risk_data['label']}</span>
        </div>
    </div>
    """
    render_html(html)

def render_verdict_card(decision: Dict[str, Any]) -> None:
    """
    Renderiza la tarjeta del veredicto del agente Grok 4.7.
    (Efecto 12: Fade In + Efecto 13: Slide In Right + Efecto 18: Animated Gradient Border)
    """
    response_text = decision.get("response_to_user", decision.get("reasoning", "Sin respuesta"))
    risk_level = decision.get("risk_level", "MEDIO")
    action = decision.get("action", "ANALYZE_ONLY")
    border_class = "sg-animated-gradient-border" if risk_level in ["CRÍTICO", "CRITICO", "ALTO"] else ""
    
    html = f"""
    <div class="sg-fade-in sg-slide-in-right {border_class}" style="margin: 1.25rem 0;">
        <div class="sg-verdict-box" style="background: var(--sg-white); border-radius: 12px; padding: 1.5rem; border: 1px solid var(--sg-soft-border); border-left: 6px solid var(--sg-forest-green);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div class="sg-verdict-title">
                    <span>🤖</span>
                    <span>Veredicto Autónomo del Agente SentinelGuard</span>
                </div>
                <span style="background: var(--sg-fog-green); color: var(--sg-title-dark); font-size: 0.74rem; padding: 3px 10px; border-radius: 12px; font-weight: 600;">
                    Acción: {action}
                </span>
            </div>
            <div class="sg-verdict-text" style="font-size: 0.95rem; color: #23382D; line-height: 1.65; white-space: pre-line;">{response_text}</div>
        </div>
    </div>
    """
    render_html(html)

def render_threat_findings(findings: List[str], detected_urls: List[str], tool_results: Dict[str, Any]) -> None:
    """
    Renderiza los hallazgos técnicos de ThreatInspector y UrlSandbox en un único contenedor sin romper el árbol DOM.
    (Efecto 7: Reveal Effect 1 + Efecto 9: Inspect Cursor + Efecto 15: Lazy Tools)
    """
    findings_items = "".join([f"<li style='margin-bottom: 4px;'>⚠️ <strong>Vector:</strong> {f}</li>" for f in findings]) if findings else "<li>No se detectaron vectores críticos explícitos.</li>"
    urls_items = "".join([f"<li style='margin-bottom: 4px;'>🌐 <strong>Enlace inspeccionado:</strong> <code>{u}</code></li>" for u in detected_urls]) if detected_urls else ""
    
    html = f"""
    <div class="sg-hover-reveal-box sg-inspect-zone" style="margin-top: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-weight: 700; color: var(--sg-title-dark); font-size: 0.92rem;">
                🔎 Resumen Rápido de Vectores Detectados (Pasa el cursor para ver detalles)
            </span>
            <span style="font-size: 0.78rem; color: var(--sg-forest-green); font-weight: 600;">
                Hover Reveal ▾
            </span>
        </div>
        <ul style="margin: 0 0 10px 18px; padding: 0; font-size: 0.88rem; color: #23382D;">
            {findings_items}
            {urls_items}
        </ul>
        <div class="sg-reveal-hidden">
            <div style="background: var(--sg-fog-green); padding: 10px 14px; border-radius: 8px; font-size: 0.8rem; color: var(--sg-title-dark);">
                🛡️ <strong>Inspección UrlSandbox:</strong> Verificación de entropía, TLDs de alto riesgo (.xyz, .top, .cc) y comprobación de typosquatting bancario contra Bancolombia, Nequi y Daviplata.
            </div>
        </div>
    </div>
    """
    render_html(html)

def render_cai_protocol_card(escalation: Dict[str, Any], police_report: Optional[Dict[str, Any]] = None) -> None:
    """
    Renderiza el protocolo de denuncia formal para CAI Virtual de Policía.
    (Efecto 13: Slide In Up + Efecto 20: Ken Burns Badge + Efecto 22: Liquid Pulse + Efecto 23: Glitch Badge)
    """
    alert_id = escalation.get("alert_id", "ALERTA-SOS-CAI")
    incident_type = escalation.get("incident_type", "DIGITAL_FRAUD")
    severity = escalation.get("severity", "CRITICAL")
    contacts = escalation.get("contacts_notified", [])
    contacts_str = ', '.join(contacts) if contacts else 'Línea de Emergencia y Red Familiar'
    script = escalation.get('deterrent_audio_script', 'Bloqueo inmediato y aviso a las autoridades.')
    
    html = f"""
    <div class="sg-slide-in-up" style="background: #FDF9F8; border: 1.5px solid #E8B2B1; border-radius: 12px; padding: 1.5rem; margin-top: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div class="sg-kenburns-badge" style="background: #8D3335; color: white; border-radius: 8px; padding: 6px 10px; font-size: 1.1rem;">
                    🚨
                </div>
                <div>
                    <span style="font-weight: 700; color: #8D3335; font-size: 1.05rem;">
                        Protocolo de Activación CAI Virtual (Policía Nacional)
                    </span>
                    <div style="font-size: 0.78rem; color: #795B22;">
                        caivirtual.policia.gov.co · Línea 123
                    </div>
                </div>
            </div>
            <span class="sg-glitch-badge" style="background: #F4D9D8; color: #8D3335; padding: 4px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; font-family: monospace;">
                {alert_id}
            </span>
        </div>
        <p style="font-size: 0.88rem; color: #3A2021; margin-bottom: 12px; line-height: 1.5;">
            Se detectó una amenaza clasificada como <strong>{severity}</strong> ({incident_type}). El agente preparó automáticamente el paquete de evidencia probatoria con cadenas de custodia digitales para radicación inmediata.
        </p>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; font-size: 0.82rem; margin-bottom: 12px;">
            <div style="background: white; border: 1px solid #E8B2B1; border-radius: 8px; padding: 10px;">
                <strong>📞 Contactos notificados:</strong><br/>
                {contacts_str}
            </div>
            <div style="background: white; border: 1px solid #E8B2B1; border-radius: 8px; padding: 10px;">
                <strong>🛑 Medida disuasiva:</strong><br/>
                {script}
            </div>
        </div>
    </div>
    """
    render_html(html)

def render_example_selector(examples: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Renderiza un selector visual con scroll snap y hover para cargar ejemplos rápidos.
    (Efecto 4: Scroll Snap 2 + Efecto 6: Hover 1 + Efecto 10: Ripple 2 + Efecto 26: Neumorphism 2)
    """
    st.write("##### ⚡ Selector Rápido de Ejemplos de Ataques Reales:")
    st.caption("Haz clic en un caso para cargarlo automáticamente en el analizador:")
    
    cols = st.columns(len(examples))
    selected = None
    for i, ex in enumerate(examples):
        with cols[i]:
            if st.button(f"{ex.get('icon', '📩')} {ex['title']}", key=f"btn_example_{i}", use_container_width=True):
                selected = ex
    return selected

def render_footer():
    """
    Renderiza el pie de página con marquee de consejos ciudadanos y botón flotante SOS.
    (Efecto 21: Marquee 2 + Efecto 3: Floating Status Pill 2)
    """
    html = """
    <div style="margin-top: 3rem; border-top: 1px solid var(--sg-soft-border); padding-top: 1.5rem;">
        <div class="sg-marquee-container" style="background: var(--sg-deep-forest);">
            <div class="sg-marquee-footer-track">
                <span>💡 CONSEJO CIUDADANO: Bancolombia, Nequi y Daviplata NUNCA solicitan claves dinámicas por SMS</span> &nbsp;&nbsp;•&nbsp;&nbsp;
                <span>🔒 No abras enlaces con extensiones .cc, .top, .xyz o .online enviadas por WhatsApp</span> &nbsp;&nbsp;•&nbsp;&nbsp;
                <span>🚨 Si recibes amenazas carcelarias, NO consignes dinero; denuncia inmediatamente en caivirtual.policia.gov.co</span> &nbsp;&nbsp;•&nbsp;&nbsp;
                <span>🛡️ SentinelGuard AI · Desarrollado por el Equipo Codixia para el Reto Agente 2026</span>
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; font-size: 0.8rem; color: var(--sg-slate-green); margin-top: 10px;">
            <div>
                <strong>SentinelGuard AI</strong> · Reto Agente 2026 (Platica.mx × Campuslands)
            </div>
            <div>
                Equipo Codixia: Fabián Aguilera · Nicolle · Santiago · Miguel · Juan José
            </div>
        </div>
    </div>
    <a href="https://caivirtual.policia.gov.co/" target="_blank" class="sg-floating-status-pill">
        <span class="sg-particle-beacon" style="background: #E8B2B1;"></span>
        <span>🚨 CAI Virtual 123</span>
    </a>
    """
    render_html(html)
