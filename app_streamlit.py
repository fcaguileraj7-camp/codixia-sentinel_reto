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
from src.utils.logger import logger

def sanitize_error_message(raw_error: any) -> str:
    """
    Sanitiza mensajes de error técnicos para evitar exponer credenciales,
    rutas del sistema operativo o trazas internas al usuario final.
    """
    if not raw_error:
        return "No fue posible completar la evaluación del mensaje."
    err_str = str(raw_error).strip()
    if not err_str:
        return "No fue posible completar la evaluación del mensaje."
    
    sensitive_markers = ["traceback", "file \"", "line ", "api_key", "sk-", "token", "password", "secret", "bearer"]
    lower_err = err_str.lower()
    if any(m in lower_err for m in sensitive_markers):
        return "Error interno en el servicio de análisis. El incidente técnico fue registrado para auditoría."
    
    if len(err_str) > 180:
        return err_str[:180] + "..."
    return err_str

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
    render_source_badge,
    render_analysis_unavailable,
    get_analysis_metadata,
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
    "Analizador de Mensajes & Enlaces",
    "Denuncias para CAI Virtual"
])

# =============================================================================
# TAB 1: ANALIZADOR DE MENSAJES & ENLACES
# =============================================================================
with tab1:
    st.write("## Ingrese el Mensaje o Enlace Sospechoso:")

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
            
            try:
                with st.spinner("SentinelGuard ejecutando ciclo autónomo de inspección..."):
                    result = agent.process_message(user_input, metadata={"sender": sender_phone})
                    if not isinstance(result, dict):
                        st.session_state["last_result"] = {
                            "status": "error",
                            "error_message": "Respuesta no válida del motor de análisis.",
                            "simulated": False
                        }
                    elif result.get("status") == "error" and not (isinstance(result.get("decision"), dict) and result.get("decision", {}).get("risk_level")):
                        err_text = result.get("error_message") or result.get("error") or "No se pudo completar el análisis del mensaje."
                        st.session_state["last_result"] = {
                            "status": "error",
                            "error_message": sanitize_error_message(err_text),
                            "simulated": result.get("simulated", False)
                        }
                    else:
                        st.session_state["last_result"] = result
                        # Registrar en historial acumulativo para auditoría de sesión (Efecto 5 Infinite Scroll 2)
                        st.session_state["analysis_history"].append({
                            "timestamp": (result.get("police_report") or {}).get("timestamp", "Reciente"),
                            "risk": (result.get("decision") or {}).get("risk_level", "DESCONOCIDO"),
                            "input_snippet": user_input[:60] + "..." if len(user_input) > 60 else user_input
                        })
            except Exception as e:
                logger.error(f"Excepción durante la ejecución del análisis: {e}", exc_info=True)
                clean_err = sanitize_error_message(str(e))
                st.session_state["last_result"] = {
                    "status": "error",
                    "error_message": clean_err,
                    "simulated": False
                }
                
            skeleton_placeholder.empty()

    # Presentación de resultados si existe análisis activo
    active_result = st.session_state.get("last_result")
    if active_result:
        decision = active_result.get("decision") if isinstance(active_result, dict) else None
        has_valid_decision = isinstance(decision, dict) and bool(decision.get("risk_level"))
        is_error_status = active_result.get("status") == "error"

        # 1. Validación de estado: Si falló completamente o no se determinó el nivel de riesgo
        if is_error_status or not has_valid_decision:
            err_msg = active_result.get("error_message") or active_result.get("error") or "Fallo en la comunicación con el motor de análisis."
            st.divider()
            render_analysis_unavailable(err_msg)
            st.error(f"❌ Análisis no completado: {err_msg}")
        else:
            result = active_result
            risk_level = decision.get("risk_level", "MEDIO")
            tool_results = result.get("tool_results", {})
            threat_data = tool_results.get("threat", {})
            
            # Normalización segura de url_sandbox para visualización detallada
            if "url" not in tool_results and "url_sandbox" in tool_results:
                sb = tool_results["url_sandbox"]
                if isinstance(sb, list) and len(sb) > 0 and isinstance(sb[0], dict):
                    tool_results["url"] = sb[0]
                elif isinstance(sb, dict):
                    tool_results["url"] = sb

            # Detección de análisis parcial vs completo (Punto 4)
            partial_reasons = []
            if result.get("status") == "partial":
                p_reason = result.get("partial_reason") or result.get("error_message")
                if p_reason:
                    partial_reasons.append(str(p_reason))
                else:
                    partial_reasons.append("Una o más herramientas secundarias retornaron respuestas parciales.")

            if isinstance(threat_data, dict) and threat_data.get("status") == "error":
                t_err = threat_data.get("error", "Error en ThreatInspector")
                partial_reasons.append(f"ThreatInspector reportó un error: {t_err}")

            url_data = tool_results.get("url_sandbox") or tool_results.get("url")
            if isinstance(url_data, list):
                for u in url_data:
                    if isinstance(u, dict) and u.get("status") == "error":
                        u_err = u.get("error", "Error al analizar enlace")
                        partial_reasons.append(f"UrlSandbox reportó un error: {u_err}")
                        break
            elif isinstance(url_data, dict) and url_data.get("status") == "error":
                u_err = url_data.get("error", "Error al analizar enlace")
                partial_reasons.append(f"UrlSandbox reportó un error: {u_err}")

            police_report = result.get("police_report")
            if isinstance(police_report, dict) and police_report.get("status") == "error":
                p_err = police_report.get("error_message") or police_report.get("error") or "Fallo al generar expediente policial"
                partial_reasons.append(f"Reporte policial: {p_err}")

            is_partial = len(partial_reasons) > 0

            # Determinación de metadatos de origen (simulado vs real)
            is_simulated, source_label = get_analysis_metadata(result, agent)
            
            st.divider()

            # Notificación explícita de análisis parcial (Punto 4)
            if is_partial:
                st.warning(
                    "⚠️ **Análisis Parcial:** La evaluación de riesgo se completó con datos parciales. "
                    "Una o más herramientas secundarias no estuvieron disponibles o retornaron errores. "
                    "Los resultados válidos obtenidos se presentan a continuación."
                )
                for pr in partial_reasons:
                    st.caption(f"• {pr}")

            # Indicador visible de origen (Resultado simulado vs Grok real)
            render_source_badge(is_simulated=is_simulated, source=source_label)

            # Badge de Nivel de Riesgo (Semántica oficial + preservación de alertas nativas)
            render_risk_badge(risk_level)
            
            if risk_level in ["CRÍTICO", "ALTO"]:
                st.error(f"🚨 NIVEL DE AMENAZA: {risk_level} — INTENTO DE ESTAFA DETECTADO")
            elif risk_level == "MEDIO":
                st.warning(f"⚠️ NIVEL DE AMENAZA: {risk_level} — PRECAUCIÓN REQUERIDA")
            else:
                st.success(f"✅ NIVEL DE AMENAZA: {risk_level} — MENSAJE APARENTEMENTE LEGÍTIMO")

            # Veredicto del Agente (Visualización moderna sin afirmar falsamente Grok si es simulado)
            render_verdict_card(decision, is_simulated=is_simulated, analysis_source=source_label)

            # Resumen contextual de hallazgos (Efecto 7 Reveal)
            render_threat_findings(
                findings=threat_data.get("findings", []) if isinstance(threat_data, dict) else [],
                detected_urls=threat_data.get("detected_urls", []) if isinstance(threat_data, dict) else [],
                tool_results=tool_results
            )

            # Detalle técnico legible (Reemplazo de st.json por tarjetas legibles)
            with st.expander("🛠️ Ver Detalle Técnico del Análisis"):
                render_tool_results_human(tool_results)

            # Protocolo de denuncia CAI Virtual
            if result.get("escalation"):
                render_cai_protocol_card(result["escalation"], result.get("police_report"))
                with st.expander("📋 Ver Expediente Completo del Incidente"):
                    render_escalation_human(result["escalation"])

            # Punto 3: Mostrar el reporte o radicado policial cuando corresponda
            if police_report and isinstance(police_report, dict):
                if police_report.get("status") == "success" and police_report.get("report_id"):
                    report_id = str(police_report["report_id"]).strip()
                    is_official = bool(
                        police_report.get("official_filing_confirmed")
                        or police_report.get("submission_status") == "CONFIRMED"
                    )
                    
                    if is_official:
                        st.success(f"✅ **Radicación Oficial Confirmada ante Autoridades** — Radicado: `{report_id}`")
                    else:
                        st.info(
                            f"📋 **Radicado Técnico:** `{report_id}`\n\n"
                            "⚠️ **Estado:** Expediente técnico preparado y listo para radicación. "
                            "**No ha sido presentado ante una autoridad judicial.** "
                            "Para formalizar la denuncia, radique con este código en [caivirtual.policia.gov.co](https://caivirtual.policia.gov.co/)."
                        )
                    
                    with st.expander("📄 Ver Denuncia Formal para CAI Virtual (Policía Nacional)"):
                        st.markdown(police_report.get("formatted_markdown", ""))
                elif police_report.get("status") == "error":
                    p_err = police_report.get("error_message") or police_report.get("error") or "Fallo en el módulo de generación de reportes"
                    st.info(f"ℹ️ **Reporte policial no disponible:** No se pudo compilar el expediente para CAI Virtual ({p_err}). Los resultados del análisis de amenazas se conservan.")
            elif result.get("escalation") and not police_report:
                st.info("ℹ️ **Reporte policial no disponible:** No se generó expediente para el CAI Virtual en este ciclo. La evaluación de amenazas previa se conserva.")

# =============================================================================
# TAB 2: EXPEDIENTE POLICIAL (CAI VIRTUAL)
# =============================================================================
with tab2:
    st.write("## Generador de Denuncias para CAI Virtual de Policía:")
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
        st.info("ℹ️ **Estado:** Expediente de ejemplo preparado. Pendiente de radicación formal por el ciudadano en caivirtual.policia.gov.co.")
        st.markdown(report["formatted_markdown"])
    elif gen_current and active_report:
        st.info("ℹ️ **Estado:** Expediente técnico preparado. Pendiente de radicación formal por el ciudadano en caivirtual.policia.gov.co.")
        st.markdown(active_report["formatted_markdown"])
    elif active_report and not gen_sample:
        st.info("ℹ️ Tienes un expediente generado del último análisis. Haz clic en **'Radicar Análisis Actual'** para visualizarlo.")

# 4. Tarjetas métricas de capacidades del sistema (Efecto 11 Tilt + Efecto 26 Neumorphism)
render_metric_cards()

# 5. Pie de página y Botón Flotante SOS (Efecto 21 Marquee 2 + Efecto 3 Floating Pill 2)
render_footer()
