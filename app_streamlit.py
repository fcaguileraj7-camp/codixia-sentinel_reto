"""
SentinelGuard AI - Interfaz Web de Demostración (Streamlit)
Reto Agente 2026 - Platica.mx × Campuslands · Equipo Codixia
Rol 5: Juan José (Dataset Engineering, Stress Testing & UI)
Subproceso 2: Ingreso de mensajes y selector de ejemplos
Identidad: Cyber Forest × Sage Sanctuary (Inspirado en Snyk & SecurityScorecard)
"""

import streamlit as st
import json
import os
import sys

# Agregar la raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent.sentinel import SentinelAgent
from src.tools.threat_inspector import inspect_threat
from src.tools.url_sandbox import analyze_url
from src.tools.police_reporter import generate_police_report

# Importaciones del Subsistema UI (Identidad Cyber Forest × Sage Sanctuary)
from src.ui.styles import get_complete_css
from src.ui.components import (
    render_header,
    render_marquee_ticker,
    render_metric_cards,
    render_risk_badge,
    render_verdict_card,
    render_threat_findings,
    render_cai_protocol_card,
    render_footer,
    render_html,
    validate_input_text,
    render_tool_results_human,
    render_escalation_human,
)

# Configuración de página de Streamlit
st.set_page_config(
    page_title="SentinelGuard AI - Reto Agente 2026",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inyección de estilos avanzados y los 26 tipos de efectos interactivos
st.markdown(get_complete_css(), unsafe_allow_html=True)

# 2. Hero Banner principal con Parallax, Particles, Gradient, Liquid Morph y Text Masking
render_header()

# 3. Ticker continuo de telemetría de amenazas (Efecto 21 Marquee)
render_marquee_ticker()

# Inicialización de estado de sesión para persistencia, auditoría y reactividad de widgets
if "analysis_history" not in st.session_state:
    st.session_state["analysis_history"] = []
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None
if "user_input_text" not in st.session_state:
    st.session_state["user_input_text"] = ""
if "sender_phone_text" not in st.session_state:
    st.session_state["sender_phone_text"] = ""
if "selected_sample" not in st.session_state:
    st.session_state["selected_sample"] = st.session_state["user_input_text"]
if "selected_phone" not in st.session_state:
    st.session_state["selected_phone"] = st.session_state["sender_phone_text"]

# Instancia del orquestador del agente
agent = SentinelAgent()

# Pestañas principales de navegación
tab1, tab2 = st.tabs([
    "💬 Analizador de Mensajes & Enlaces",
    "📜 Expediente Policial"
])

# =============================================================================
# TAB 1: ANALIZADOR DE MENSAJES & ENLACES
# =============================================================================
with tab1:
    st.write("### 💬 Ingreso de Mensaje o Enlace Sospechoso:")
    st.caption("Pega cualquier SMS, mensaje de WhatsApp, correo o enlace que desees auditar:")

    # Área de Texto para el Mensaje (Multilínea, editable, persistente)
    user_input = st.text_area(
        "Mensaje recibido para inspección:",
        key="user_input_text",
        height=130,
        placeholder="Pega aquí el texto sospechoso completo (SMS, WhatsApp, correo o enlace)...",
        help="Introduce o edita libremente el texto antes de iniciar la inspección."
    )

    col1, col2 = st.columns(2)
    with col1:
        sender_phone = st.text_input(
            "Número o remitente del emisor (opcional):",
            key="sender_phone_text",
            placeholder="Ej: +57 312 987 6543 o remitente SMS",
            help="Número telefónico o identificador del remitente sospechoso."
        )
    with col2:
        render_html(
            """
            <div style="background: var(--sg-fog-green); padding: 10px 14px; border-radius: 8px; margin-top: 26px; border: 1px solid var(--sg-soft-border); font-size: 0.8rem; color: var(--sg-title-dark);">
                🛡️ <strong>Garantía de Privacidad:</strong> Inspección local sin almacenamiento persistente de credenciales. Respaldo directo ante el CAI Virtual.
            </div>
            """
        )

    # 4. Botón Principal de Análisis (con Efecto 10: Ripple y Efecto 6: Hover State)
    analyze_btn = st.button("🔍 Analizar con SentinelGuard AI", type="primary", use_container_width=True, key="btn_analyze_main")

    # 5. Validación de Entrada y Ejecución Segura
    if analyze_btn:
        is_valid, validation_err = validate_input_text(user_input)
        if not is_valid:
            st.warning(f"⚠️ {validation_err}")
        else:
            # Sincronización de estado para retrocompatibilidad
            st.session_state["selected_sample"] = user_input
            st.session_state["selected_phone"] = sender_phone

            # Efecto 16: Skeleton Screen mientras se procesa la solicitud
            skeleton_placeholder = st.empty()
            skeleton_placeholder.markdown(
                """
                <div style="margin: 1.5rem 0;">
                    <div class="sg-skeleton-box"></div>
                    <div class="sg-skeleton-line" style="width: 80%;"></div>
                    <div class="sg-skeleton-line" style="width: 60%;"></div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            with st.spinner("SentinelGuard ejecutando ciclo autónomo con Grok 4.7..."):
                result = agent.process_message(user_input, metadata={"sender": sender_phone})
                st.session_state["last_result"] = result
                
                # Registrar en historial acumulativo para auditoría de sesión (Efecto 5 Infinite Scroll 2)
                st.session_state["analysis_history"].append({
                    "timestamp": (result.get("police_report") or {}).get("timestamp", "Reciente"),
                    "risk": (result.get("decision") or {}).get("risk_level", "DESCONOCIDO"),
                    "input_snippet": user_input[:60] + "..." if len(user_input) > 60 else user_input
                })
                
            skeleton_placeholder.empty()

    # Presentación de resultados si existe análisis activo
    active_result = st.session_state.get("last_result")
    if active_result:
        result = active_result
        decision = result.get("decision", {})
        risk_level = decision.get("risk_level", "MEDIO")
        tool_results = result.get("tool_results", {})
        threat_data = tool_results.get("threat", {})
        
        st.divider()

        # Badge de Nivel de Riesgo (Semántica oficial + preservación de alertas nativas)
        render_risk_badge(risk_level)
        
        if risk_level in ["CRÍTICO", "ALTO"]:
            st.error(f"🚨 NIVEL DE AMENAZA: {risk_level} — INTENTO DE ESTAFA DETECTADO")
        elif risk_level == "MEDIO":
            st.warning(f"⚠️ NIVEL DE AMENAZA: {risk_level} — PRECAUCIÓN REQUERIDA")
        else:
            st.success(f"✅ NIVEL DE AMENAZA: {risk_level} — MENSAJE APARENTEMENTE LEGÍTIMO")

        # Veredicto del Agente (Visualización moderna con Efecto 13 Slide-in y preservación de st.info)
        render_verdict_card(decision)
        
        st.write("#### 🤖 Veredicto del Agente:")
        st.info(decision.get("response_to_user", decision.get("reasoning", "Sin respuesta")))

        # Resumen contextual de hallazgos (Efecto 7 Reveal)
        render_threat_findings(
            findings=threat_data.get("findings", []),
            detected_urls=threat_data.get("detected_urls", []),
            tool_results=tool_results
        )

        # Detalle técnico legible (Reemplazo de st.json por tarjetas legibles)
        with st.expander("🛠️ Ver Detalle Técnico del Análisis"):
            render_tool_results_human(result.get("tool_results", {}))

        # Protocolo de denuncia CAI Virtual
        if result.get("escalation"):
            render_cai_protocol_card(result["escalation"], result.get("police_report"))
            with st.expander("📋 Ver Expediente Completo del Incidente"):
                render_escalation_human(result["escalation"])

# =============================================================================
# TAB 2: EXPEDIENTE POLICIAL (CAI VIRTUAL)
# =============================================================================
with tab2:
    st.write("### 📜 Generador de Denuncias para CAI Virtual de Policía:")
    st.write("Compila formalmente la evidencia técnica lista para radicación judicial ante la Policía Nacional de Colombia.")
    
    # Si existe un análisis previo en la sesión con expediente generado, ofrecer su visualización directa
    active_report = st.session_state.get("last_result", {}).get("police_report") if st.session_state.get("last_result") else None
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        gen_sample = st.button("📄 Generar Expediente de Ejemplo", use_container_width=True)
    with col_btn2:
        gen_current = st.button("🚨 Radicar Análisis Actual", disabled=(active_report is None), use_container_width=True)

    if gen_sample:
        sample_evidence = {
            "sender_phone": "+57 321 456 7890",
            "incident_type": "Suplantación Bancolombia / Phishing",
            "user_input": "Bancolombia Alerta: Su cuenta 456-*** fue bloqueada por movimientos sospechosos. Ingrese urgente a https://banc0lombia-seguridad.cc para validar su identidad.",
            "risk_level": "CRÍTICO",
            "findings": ["Enlace hacia dominio clonado", "Urgencia y amenaza de bloqueo injustificada"],
            "detected_urls": ["https://banc0lombia-seguridad.cc"]
        }
        report = generate_police_report(sample_evidence)
        st.markdown(report["formatted_markdown"])
    elif gen_current and active_report:
        st.markdown(active_report["formatted_markdown"])
    elif active_report and not gen_sample:
        st.info("ℹ️ Tienes un expediente generado del último análisis. Haz clic en **'Radicar Análisis Actual'** para visualizarlo.")

# 4. Tarjetas métricas de capacidades del sistema (Efecto 11 Tilt + Efecto 26 Neumorphism)
render_metric_cards()

# 5. Pie de página y Botón Flotante SOS (Efecto 21 Marquee 2 + Efecto 3 Floating Pill 2)
render_footer()
