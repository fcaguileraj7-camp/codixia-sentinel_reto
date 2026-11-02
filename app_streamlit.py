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
from src.tools.route_companion import (
    register_trip,
    get_trip_status,
    confirm_checkin,
    detect_overdue_checkins,
    finalize_trip,
    evaluate_trip_audio_response,
)
from src.tools.emergency_escalator import escalate_emergency
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

# Variables de estado de sesión para Acompañamiento en Taxi (Rol 5 - Hito S3)
if "taxi_active_trip" not in st.session_state:
    st.session_state["taxi_active_trip"] = None
if "taxi_sos_result" not in st.session_state:
    st.session_state["taxi_sos_result"] = None
if "taxi_eval_result" not in st.session_state:
    st.session_state["taxi_eval_result"] = None
if "taxi_last_completed_trip" not in st.session_state:
    st.session_state["taxi_last_completed_trip"] = None
if "taxi_sim_text_input" not in st.session_state:
    st.session_state["taxi_sim_text_input"] = ""
if "taxi_overdue_list" not in st.session_state:
    st.session_state["taxi_overdue_list"] = None

# Instancia del orquestador del agente
agent = SentinelAgent()

# Pestañas principales de navegación
tab1, tab2, tab3 = st.tabs([
    "Analizador de Mensajes & Enlaces",
    "🚕 Acompañamiento en Taxi",
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
# TAB 2: ACOMPAÑAMIENTO EN TAXI (RUTAS SEGURAS & MONITOREO PREVENTIVO)
# =============================================================================
with tab2:
    st.write("## 🚕 Acompañamiento Físico en Taxi & Monitoreo Preventivo")
    st.caption(
        "Monitoreo de seguridad ciudadana para desplazamientos y viajes en taxi: "
        "registro del vehículo, control de check-ins periódicos y activación de protocolos disuasorios ante situaciones de peligro."
    )

    active_trip = st.session_state.get("taxi_active_trip")
    last_completed = st.session_state.get("taxi_last_completed_trip")

    # A. REGISTRO DE VIAJE (Visible si no hay viaje activo en curso)
    if active_trip is None:
        if last_completed:
            st.info(
                f"ℹ️ **Último viaje finalizado:** Radicado `{last_completed.get('trip_id')}` "
                f"— Motivo: `{last_completed.get('completion_reason', 'completado')}` a las `{last_completed.get('completed_at', 'reciente')}`."
            )

        st.write("### 📝 Registro de Nuevo Viaje")
        col_reg1, col_reg2 = st.columns(2)
        with col_reg1:
            taxi_plate = st.text_input(
                "Placa del vehículo:",
                key="taxi_plate_input",
                placeholder="Ej: WDY-452 o TRL981",
                help="Matrícula del vehículo. Debe contener letras y números (3 a 12 caracteres)."
            )
            taxi_origin = st.text_input(
                "Lugar de origen (opcional):",
                key="taxi_origin_input",
                placeholder="Ej: Zona Rosa / Calle 85",
                help="Punto o barrio de partida del trayecto."
            )
        with col_reg2:
            taxi_destination = st.text_input(
                "Destino previsto:",
                key="taxi_destination_input",
                placeholder="Ej: Centro Comercial Andino / Calle 100",
                help="Punto de llegada o destino final del viaje."
            )
            taxi_interval = st.number_input(
                "Intervalo de check-in (minutos):",
                min_value=1,
                max_value=120,
                value=10,
                step=1,
                key="taxi_interval_input",
                help="Frecuencia con la que se solicitará confirmación de normalidad al pasajero."
            )

        btn_register = st.button("🚖 Iniciar acompañamiento", type="primary", use_container_width=True, key="taxi_btn_register")
        if btn_register:
            plate_clean = taxi_plate.strip() if taxi_plate else ""
            dest_clean = taxi_destination.strip() if taxi_destination else ""
            orig_clean = taxi_origin.strip() if taxi_origin else None

            if not plate_clean:
                st.warning("⚠️ La placa del vehículo es obligatoria.")
            elif not dest_clean:
                st.warning("⚠️ El destino del viaje es obligatorio.")
            else:
                try:
                    trip_payload = register_trip(
                        plate=plate_clean,
                        destination=dest_clean,
                        origin=orig_clean,
                        checkin_interval_minutes=int(taxi_interval)
                    )
                    st.session_state["taxi_active_trip"] = trip_payload
                    st.session_state["taxi_sos_result"] = None
                    st.session_state["taxi_eval_result"] = None
                    st.session_state["taxi_last_completed_trip"] = None
                    if hasattr(agent, "memory") and agent.memory:
                        agent.memory.set_active_trip("default", trip_payload)
                    st.success(f"✅ Acompañamiento iniciado exitosamente. Radicado del viaje: `{trip_payload['trip_id']}`")
                    st.rerun()
                except (ValueError, TypeError) as val_err:
                    st.error(f"⚠️ Error de validación: {val_err}")
                except Exception as exc:
                    logger.error(f"Falla inesperada al registrar viaje: {exc}", exc_info=True)
                    st.error(f"❌ Error al iniciar acompañamiento: {sanitize_error_message(str(exc))}")

    # B. PANEL DE SEGUIMIENTO (Visible cuando existe un viaje activo)
    else:
        trip_id = active_trip.get("trip_id", "")
        status_raw = str(active_trip.get("status", "active")).upper()
        plate_val = active_trip.get("vehicle_plate", "")
        dest_val = active_trip.get("destination", "")
        orig_val = active_trip.get("origin") or "No especificado"
        started_val = active_trip.get("started_at", "")
        interval_val = active_trip.get("checkin_interval_minutes", 10)
        checkin_count = active_trip.get("checkin_count", 0)
        next_checkin = active_trip.get("next_checkin_scheduled") or "No programado"

        st.markdown(
            f"""
            <div style="background: var(--sg-fog-green); border: 1px solid var(--sg-soft-border); border-radius: 10px; padding: 18px 22px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                    <span style="font-size: 1.15rem; font-weight: 700; color: var(--sg-title-dark);">🚕 Panel de Monitoreo de Viaje Activo</span>
                    <span style="background: var(--sg-digital-sage); color: var(--sg-cyber-forest); font-weight: 700; font-size: 0.8rem; padding: 4px 14px; border-radius: 20px;">
                        ESTADO: {status_raw}
                    </span>
                </div>
                <div style="font-size: 0.86rem; color: #314C3E; line-height: 1.7;">
                    <strong>Identificador del Viaje:</strong> <code>{trip_id}</code><br>
                    <strong>Vehículo (Placa):</strong> <code>{plate_val}</code> &nbsp;|&nbsp; 
                    <strong>Origen:</strong> {orig_val} &nbsp;|&nbsp; 
                    <strong>Destino:</strong> {dest_val}<br>
                    <strong>Hora de inicio:</strong> {started_val} &nbsp;|&nbsp; 
                    <strong>Intervalo programado:</strong> Cada {interval_val} minutos<br>
                    <strong>Check-ins completados:</strong> <code>{checkin_count}</code> &nbsp;|&nbsp; 
                    <strong>Próximo check-in:</strong> <code>{next_checkin}</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_act1, col_act2, col_act3, col_act4 = st.columns(4)
        with col_act1:
            btn_refresh = st.button("🔄 Actualizar estado", use_container_width=True, key="taxi_btn_refresh")
        with col_act2:
            btn_checkin = st.button("✅ Confirmar que estoy bien", use_container_width=True, key="taxi_btn_checkin")
        with col_act3:
            btn_finalize = st.button("🏁 Finalizar viaje", use_container_width=True, key="taxi_btn_finalize")
        with col_act4:
            btn_overdue = st.button("⏱️ Revisar check-ins pendientes", use_container_width=True, key="taxi_btn_overdue")

        if btn_refresh:
            status_res = get_trip_status(trip_id)
            if status_res.get("status") == "error":
                st.error(f"❌ Viaje no encontrado en el motor de monitoreo: {status_res.get('error')}")
            else:
                st.session_state["taxi_active_trip"] = status_res
                st.success("🔄 Estado del viaje actualizado en tiempo real.")

        if btn_checkin:
            checkin_res = confirm_checkin(trip_id)
            if checkin_res.get("status") == "success":
                active_trip["checkin_count"] = checkin_res.get("checkin_count", checkin_count + 1)
                active_trip["last_checkin_at"] = checkin_res.get("last_checkin_at")
                active_trip["next_checkin_scheduled"] = checkin_res.get("next_checkin_scheduled")
                st.session_state["taxi_active_trip"] = active_trip
                st.success(
                    f"✅ Check-in #{checkin_res.get('checkin_count')} confirmado exitosamente. "
                    f"Próxima verificación: `{checkin_res.get('next_checkin_scheduled')}`"
                )
            else:
                st.error(f"❌ No fue posible registrar el check-in: {checkin_res.get('error')}")

        if btn_finalize:
            final_res = finalize_trip(trip_id, reason="completado_por_usuario")
            if final_res.get("status") == "completed":
                st.session_state["taxi_last_completed_trip"] = final_res
                st.session_state["taxi_active_trip"] = None
                st.session_state["taxi_eval_result"] = None
                if hasattr(agent, "memory") and agent.memory:
                    agent.memory.clear_active_trip("default")
                st.success(f"🏁 Viaje `{trip_id}` finalizado correctamente. Acompañamiento cerrado sin incidentes.")
                st.rerun()
            else:
                st.error(f"❌ No se pudo finalizar el viaje: {final_res.get('error')}")

        if btn_overdue:
            try:
                overdue_ids = detect_overdue_checkins()
                st.session_state["taxi_overdue_list"] = overdue_ids
                if overdue_ids:
                    st.warning(f"⚠️ Se detectaron {len(overdue_ids)} viaje(s) con check-in vencido: {', '.join(overdue_ids)}")
                else:
                    st.info("ℹ️ No hay check-ins vencidos en este momento. Todos los viajes activos están al día.")
            except Exception as e:
                st.error(f"❌ Error al consultar check-ins vencidos: {e}")

    # C. SIMULADOR DE ESCENARIOS (Análisis de respuestas / transcripciones)
    st.write("---")
    st.write("### 🎭 Simulación de situaciones durante el viaje")
    st.caption(
        "Evalúa respuestas textuales o transcripciones de audio del pasajero contra el detector de señales de auxilio, "
        "palabras de pánico (`PANIC_KEYWORDS`) y desviaciones de ruta del módulo `RouteCompanion`."
    )

    col_sim_btn1, col_sim_btn2 = st.columns(2)
    with col_sim_btn1:
        btn_sim_safe = st.button("🟢 Simular situación segura", use_container_width=True, key="taxi_btn_sim_safe")
    with col_sim_btn2:
        btn_sim_danger = st.button("🔴 Simular situación de peligro", use_container_width=True, key="taxi_btn_sim_danger")

    if btn_sim_safe:
        st.session_state["taxi_sim_text_input"] = "Todo va bien, el conductor va por la ruta principal hacia mi destino."
        try:
            eval_res = evaluate_trip_audio_response(st.session_state["taxi_sim_text_input"])
            st.session_state["taxi_eval_result"] = eval_res
        except Exception as e:
            st.error(f"❌ Error al evaluar respuesta: {e}")

    if btn_sim_danger:
        st.session_state["taxi_sim_text_input"] = "Ayuda por favor, el conductor tomó un desvío extraño y no me deja bajar del taxi."
        try:
            eval_res = evaluate_trip_audio_response(st.session_state["taxi_sim_text_input"])
            st.session_state["taxi_eval_result"] = eval_res
        except Exception as e:
            st.error(f"❌ Error al evaluar respuesta: {e}")

    sim_text = st.text_area(
        "Respuesta o transcripción del pasajero para inspección:",
        key="taxi_sim_text_input",
        height=85,
        placeholder="Escriba o pegue la transcripción del mensaje de voz o texto del pasajero...",
        help="Inspección semántica de estrés y auxilio. (Nota: analiza texto/transcripciones; no procesa señales de micrófono en vivo)."
    )

    btn_eval_manual = st.button("🔍 Analizar respuesta", type="primary", use_container_width=True, key="taxi_btn_analyze_response")
    if btn_eval_manual:
        clean_eval_input = sim_text.strip() if sim_text else ""
        if not clean_eval_input:
            st.warning("⚠️ Debe introducir un mensaje o presionar una de las opciones de simulación.")
        else:
            try:
                eval_res = evaluate_trip_audio_response(clean_eval_input)
                st.session_state["taxi_eval_result"] = eval_res
            except (ValueError, TypeError) as e:
                st.error(f"⚠️ Error de validación: {e}")
            except Exception as e:
                st.error(f"❌ Fallo técnico al evaluar respuesta: {sanitize_error_message(str(e))}")

    # Visualización del veredicto del simulador
    eval_result = st.session_state.get("taxi_eval_result")
    if eval_result:
        status_eval = eval_result.get("status")
        is_safe = eval_result.get("is_safe")
        escalation_req = eval_result.get("escalation_required")
        reason_txt = eval_result.get("reason", "")

        if status_eval == "normal":
            st.success(f"✅ **Estado: NORMAL (Seguro)** — {reason_txt}")
        elif status_eval == "checkin_pending":
            st.warning(f"⚠️ **Estado: CONFIRMACIÓN PENDIENTE** — {reason_txt}")
        elif status_eval == "alert":
            st.error(f"🚨 **Estado: ALERTA DE RIESGO FÍSICO** — {reason_txt}")
            if escalation_req:
                st.warning("⚠️ **Escalamiento Requerido:** Se identificaron indicadores de peligro inminente. Se recomienda accionar el Protocolo SOS a continuación.")

    # D. PROTOCOLO DE EMERGENCIA SOS
    st.write("---")
    st.write("### 🚨 Protocolo de emergencia SOS")
    st.caption(
        "Preparación local de alertas disuasorias y expediente preventivo para protección del pasajero ante situaciones críticas."
    )

    btn_sos = st.button("🆘 ACTIVAR PROTOCOLO SOS", type="primary", use_container_width=True, key="taxi_btn_sos")
    if btn_sos:
        if active_trip is None:
            st.warning("⚠️ Se requiere un viaje activo registrado para activar el protocolo de emergencia SOS.")
        else:
            evidence = {
                "vehicle_plate": active_trip.get("vehicle_plate"),
                "destination": active_trip.get("destination"),
                "trip_id": active_trip.get("trip_id"),
            }
            if active_trip.get("origin"):
                evidence["origin"] = active_trip.get("origin")
                evidence["last_known_location"] = active_trip.get("origin")
            if eval_result and eval_result.get("status") == "alert":
                evidence["evaluation_reason"] = eval_result.get("reason")

            contacts_notified = ["Contacto de Confianza", "Línea 123 (Simulada)"]
            try:
                sos_res = escalate_emergency(
                    incident_type="PHYSICAL_RISK",
                    evidence_payload=evidence,
                    contacts=contacts_notified
                )
                st.session_state["taxi_sos_result"] = sos_res
            except (ValueError, TypeError) as val_err:
                st.error(f"⚠️ Error al preparar escalada de emergencia: {val_err}")
            except Exception as exc:
                logger.error(f"Falla en escalate_emergency: {exc}", exc_info=True)
                st.error(f"❌ Error interno en protocolo SOS: {sanitize_error_message(str(exc))}")

    # Visualización del resultado del Protocolo SOS
    sos_data = st.session_state.get("taxi_sos_result")
    if sos_data:
        sos_status = sos_data.get("status", "escalated")
        alert_id = sos_data.get("alert_id", "DESCONOCIDO")
        severity = sos_data.get("severity", "CRITICAL")
        contacts_list = sos_data.get("contacts_notified", [])
        deterrent_script = sos_data.get("deterrent_audio_script", "")
        alert_msg = sos_data.get("alert_message", "")
        incident_rep = sos_data.get("incident_report", {})

        plate_show = sos_data.get("vehicle_plate") or (active_trip.get("vehicle_plate") if active_trip else "No registrada")
        dest_show = sos_data.get("destination") or (active_trip.get("destination") if active_trip else "No informado")
        loc_show = sos_data.get("last_known_location") or (active_trip.get("origin") if active_trip else None)

        st.markdown(
            f"""
            <div style="background: rgba(244, 217, 216, 0.45); border: 2px solid #8D3335; border-radius: 10px; padding: 18px 22px; margin-top: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                    <span style="font-size: 1.15rem; font-weight: 800; color: #8D3335;">🚨 EXPEDIENTE DE EMERGENCIA LOCAL PREPARADO</span>
                    <span style="background: #8D3335; color: white; font-weight: 700; font-size: 0.8rem; padding: 4px 14px; border-radius: 12px;">
                        SEVERIDAD: {severity}
                    </span>
                </div>
                <p style="font-size: 0.84rem; color: #5B1C1D; margin-bottom: 8px;">
                    🛡️ <strong>Garantía de Transparencia:</strong> Escalada preventiva preparada en entorno local. No se generan comunicaciones telefónicas reales a autoridades sin autorización expresa.
                </p>
                <div style="font-size: 0.85rem; line-height: 1.7; color: #351213;">
                    <strong>Estado de la Alerta:</strong> <code>{sos_status}</code> ({'Alerta preventiva registrada' if sos_status == 'escalated' else 'Alerta idéntica previa consolidada / Duplicada'})<br>
                    <strong>Identificador de Alerta:</strong> <code>{alert_id}</code><br>
                    <strong>Vehículo (Placa):</strong> <code>{plate_show}</code> &nbsp;|&nbsp; 
                    <strong>Destino:</strong> {dest_show}<br>
                    <strong>Última ubicación conocida:</strong> {loc_show or 'No disponible (no se simulan coordenadas ficticias)'}<br>
                    <strong>Contactos asignados para despacho:</strong> {', '.join(contacts_list) if contacts_list else 'Ninguno'}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if alert_msg:
            st.error(f"📢 **Despacho Preventivo:** {alert_msg}")

        if deterrent_script:
            st.markdown(
                f"""
                <div style="background: var(--sg-warm-ivory); border-left: 4px solid var(--sg-forest-green); padding: 14px 18px; border-radius: 4px; margin: 14px 0;">
                    <span style="font-size: 0.8rem; font-weight: 700; color: var(--sg-forest-green); text-transform: uppercase;">
                        🔊 Guión de Audio Disuasorio para Altavoz:
                    </span>
                    <p style="font-size: 0.95rem; font-style: italic; color: var(--sg-title-dark); margin: 6px 0 0 0;">
                        "{deterrent_script}"
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        if incident_rep and isinstance(incident_rep, dict):
            with st.expander("📋 Ver Expediente Técnico del Incidente (JSON)"):
                st.json(incident_rep)

# =============================================================================
# TAB 3: EXPEDIENTE POLICIAL (CAI VIRTUAL)
# =============================================================================
with tab3:
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
