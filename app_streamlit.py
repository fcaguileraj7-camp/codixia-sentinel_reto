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
    render_navigation_status,
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
    load_demo_samples,
    NEUTRAL_SAMPLE_OPTION,
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

# 1. Barra de navegación contextual superior (Efecto 3 Sticky + Efecto 19 Glassmorphism)
render_navigation_status()

# 2. Hero Banner principal con Parallax, Particles, Gradient, Liquid Morph y Text Masking
render_header()

# 3. Ticker continuo de telemetría de amenazas (Efecto 21 Marquee)
render_marquee_ticker()

# 4. Tarjetas métricas de capacidades del sistema (Efecto 11 Tilt + Efecto 26 Neumorphism)
render_metric_cards()

# Carga modular de ejemplos del catálogo (Dataset S3)
demo_samples = load_demo_samples()
sample_options = [NEUTRAL_SAMPLE_OPTION] + [s["display_title"] for s in demo_samples]

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
if "example_dropdown_selector" not in st.session_state:
    st.session_state["example_dropdown_selector"] = NEUTRAL_SAMPLE_OPTION

# Callbacks para actualizar el área de texto sin ejecución automática de análisis
def on_example_dropdown_change():
    """Carga el texto del ejemplo seleccionado desde el desplegable sin disparar el análisis."""
    chosen = st.session_state.get("example_dropdown_selector")
    if chosen and chosen != NEUTRAL_SAMPLE_OPTION:
        for s in demo_samples:
            if s["display_title"] == chosen:
                st.session_state["user_input_text"] = s["text"]
                st.session_state["sender_phone_text"] = s.get("phone", "+57 300 000 0000")
                st.session_state["selected_sample"] = s["text"]
                st.session_state["selected_phone"] = s.get("phone", "+57 300 000 0000")
                break

def load_quick_sample(case_id: str):
    """Callback de botón rápido para cargar vectores comunes antes de instanciar widgets."""
    for s in demo_samples:
        if s["id"] == case_id:
            st.session_state["user_input_text"] = s["text"]
            st.session_state["sender_phone_text"] = s.get("phone", "+57 300 000 0000")
            st.session_state["selected_sample"] = s["text"]
            st.session_state["selected_phone"] = s.get("phone", "+57 300 000 0000")
            st.session_state["example_dropdown_selector"] = s["display_title"]
            break

# Instancia del orquestador del agente
agent = SentinelAgent()

# Pestañas principales de navegación
tab1, tab2, tab3 = st.tabs([
    "💬 Analizador de Mensajes & Enlaces",
    "📊 Casos de Prueba (Dataset S3)",
    "📜 Expediente Policial"
])

# =============================================================================
# TAB 1: ANALIZADOR DE MENSAJES & ENLACES
# =============================================================================
with tab1:
    render_html(
        """
        <div class="sg-security-zone" style="background: var(--sg-fog-green); border: 1px solid var(--sg-soft-border); border-radius: 10px; padding: 12px 16px; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 0.85rem; color: var(--sg-title-dark);">
                🎯 <strong>Zona de Escaneo Táctico:</strong> Pasa el cursor sobre esta área para activar la retícula de precisión balística y verificación de firmas (Efecto 9).
            </div>
            <span style="font-size: 0.75rem; background: rgba(66, 102, 83, 0.15); color: var(--sg-forest-green); padding: 3px 8px; border-radius: 6px; font-weight: 600;">Modo Vigilancia</span>
        </div>
        """
    )
    st.write("### 💬 Ingreso de Mensaje o Enlace Sospechoso:")
    st.caption("Pega cualquier SMS, mensaje de WhatsApp, correo o enlace que desees auditar, o selecciona un caso preparado del catálogo:")

    # 1. Selector Desplegable de Ejemplos Representativos (Opción neutral inicial)
    st.selectbox(
        "📂 Catálogo de Ejemplos Representativos:",
        options=sample_options,
        key="example_dropdown_selector",
        on_change=on_example_dropdown_change,
        help="Selecciona un caso preparado del dataset para cargarlo automáticamente en el área de análisis sin ejecutarlo."
    )

    # 2. Selector Rápido de Vectores Comunes (Efecto 10: Ripple y Efecto 6: Hover State)
    st.write("##### ⚡ Acceso Rápido por Vector de Ataque:")
    col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)
    with col_ex1:
        st.button("🏦 Phishing Bancolombia", key="btn_quick_banco", use_container_width=True, on_click=load_quick_sample, args=("CASE-001",))
    with col_ex2:
        st.button("📱 Suplantación Nequi", key="btn_quick_nequi", use_container_width=True, on_click=load_quick_sample, args=("CASE-005",))
    with col_ex3:
        st.button("🚨 Extorsión Carcelaria", key="btn_quick_extorsion", use_container_width=True, on_click=load_quick_sample, args=("CASE-002",))
    with col_ex4:
        st.button("✅ Mensaje Legítimo", key="btn_quick_legitimo", use_container_width=True, on_click=load_quick_sample, args=("CASE-011",))

    # 3. Área de Texto para el Mensaje (Multilínea, editable, persistente)
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
                    "timestamp": result.get("police_report", {}).get("timestamp", "Reciente"),
                    "risk": result.get("decision", {}).get("risk_level", "DESCONOCIDO"),
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

        # Pestañas de detalle técnico (Preservación estricta de st.json y expander)
        with st.expander("🛠️ Ver Resultados Técnicos de Herramientas (Tools)"):
            st.json(result.get("tool_results", {}))

        # Protocolo de denuncia CAI Virtual
        if result.get("escalation"):
            render_cai_protocol_card(result["escalation"], result.get("police_report"))
            st.write("#### 🚨 Protocolo de Denuncia CAI Virtual:")
            st.json(result["escalation"])

# =============================================================================
# TAB 2: CASOS DE PRUEBA (DATASET S3)
# =============================================================================
with tab2:
    st.write("### 📊 Dataset de Evaluación Real (30 Casos Documentados):")
    st.caption("Casos clasificados con veredictos esperados para el Hito S3 (Efecto 5: Infinite Scroll / Carga Progresiva).")
    
    dataset_path = "data/scam_dataset_30.json"
    if os.path.exists(dataset_path):
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
        
        col_d1, col_d2 = st.columns([1, 3])
        with col_d1:
            st.metric("Total de casos cargados", len(dataset), delta="Hito S3 Aprobado")
        with col_d2:
            st.write("Colección certificada con casos reales de **Phishing**, **Extorsión Carcelaria** y **Suplantación de Identidad**.")
        
        # Filtro interactivo de exploración
        categories = ["TODAS"] + sorted(list(set(d.get("category", "OTRO") for d in dataset)))
        selected_cat = st.selectbox("Filtrar casos por vector de ataque:", categories)
        
        filtered_dataset = dataset if selected_cat == "TODAS" else [d for d in dataset if d.get("category") == selected_cat]
        
        # Visualización de datos de evaluación
        st.dataframe(filtered_dataset, use_container_width=True)
    else:
        st.warning("Dataset en construcción para el Hito S3.")
    
    # Historial de auditoría acumulativo de la sesión (Efecto 5: Infinite Scroll 2)
    if st.session_state.get("analysis_history"):
        st.write("##### 🕒 Bitácora de Auditoría en Esta Sesión:")
        log_items = "".join([f"<li><strong>[{e['risk']}]</strong> {e['timestamp']} — <em>{e['input_snippet']}</em></li>" for e in reversed(st.session_state["analysis_history"])])
        render_html(f'<div class="sg-infinite-audit-log"><ul style="margin: 0; padding-left: 20px;">{log_items}</ul></div>')

# =============================================================================
# TAB 3: EXPEDIENTE POLICIAL (CAI VIRTUAL)
# =============================================================================
with tab3:
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

# 5. Pie de página y Botón Flotante SOS (Efecto 21 Marquee 2 + Efecto 3 Floating Pill 2)
render_footer()
