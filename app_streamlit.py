"""
SentinelGuard AI - Interfaz Web de Demostración (Streamlit)
Liderado por: Juan José (Rol: Dataset Engineering, Stress Testing & UI)
Reto Agente 2026 - Platica.mx × Campuslands
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

st.set_page_config(
    page_title="SentinelGuard AI - Reto Agente 2026",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ SentinelGuard AI")
st.subheader("El Escudo Digital Ciudadano contra Estafas y Extorsiones (Reto Agente 2026)")
st.caption("Desarrollado por el Equipo Codixia: Nicolle · Santiago · Miguel · Fabián · Juan José")

tab1, tab2, tab3 = st.tabs(["💬 Analizador de Mensajes & Enlaces", "📊 Casos de Prueba (Dataset S3)", "📜 Expediente Policial"])

agent = SentinelAgent()

with tab1:
    st.write("### Pega un mensaje sospechoso recibido por WhatsApp o SMS:")
    sample_text = "Bancolombia Alerta: Su cuenta 456-*** fue bloqueada por movimientos sospechosos. Ingrese urgente a https://banc0lombia-seguridad.cc para validar su identidad."
    user_input = st.text_area("Mensaje recibido:", value=sample_text, height=120)

    col1, col2 = st.columns(2)
    with col1:
        sender_phone = st.text_input("Número del emisor (opcional):", value="+57 312 987 6543")

    if st.button("🔍 Analizar con SentinelGuard AI", type="primary"):
        with st.spinner("SentinelGuard ejecutando ciclo autónomo con Grok 4.7..."):
            result = agent.process_message(user_input, metadata={"sender": sender_phone})
            
            decision = result.get("decision", {})
            risk_level = decision.get("risk_level", "MEDIO")
            
            st.divider()
            
            # Badge de Nivel de Riesgo
            if risk_level in ["CRÍTICO", "ALTO"]:
                st.error(f"🚨 NIVEL DE AMENAZA: {risk_level} — INTENTO DE ESTAFA DETECTADO")
            elif risk_level == "MEDIO":
                st.warning(f"⚠️ NIVEL DE AMENAZA: {risk_level} — PRECAUCIÓN REQUERIDA")
            else:
                st.success(f"✅ NIVEL DE AMENAZA: {risk_level} — MENSAJE APARENTEMENTE LEGÍTIMO")
                
            st.write("#### 🤖 Veredicto del Agente:")
            st.info(decision.get("response_to_user", decision.get("reasoning", "Sin respuesta")))
            
            # Pestañas de detalle técnico
            with st.expander("🛠️ Ver Resultados Técnicos de Herramientas (Tools)"):
                st.json(result.get("tool_results", {}))
                
            if result.get("escalation"):
                st.write("#### 🚨 Protocolo de Denuncia CAI Virtual:")
                st.json(result["escalation"])

with tab2:
    st.write("### Dataset de Evaluación Real (30 Casos Documentados):")
    dataset_path = "data/scam_dataset_30.json"
    if os.path.exists(dataset_path):
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
        st.write(f"Total de casos cargados: **{len(dataset)}**")
        st.dataframe(dataset)
    else:
        st.warning("Dataset en construcción para el Hito S3.")

with tab3:
    st.write("### Generador de Denuncias para CAI Virtual de Policía:")
    st.write("Compila formalmente la evidencia técnica lista para radicación judicial.")
    if st.button("Generar Expediente de Ejemplo"):
        sample_evidence = {
            "sender_phone": "+57 321 456 7890",
            "incident_type": "Suplantación Bancolombia / Phishing",
            "user_input": sample_text,
            "risk_level": "CRÍTICO",
            "findings": ["Enlace hacia dominio clonado", "Urgencia y amenaza de bloqueo injustificada"],
            "detected_urls": ["https://banc0lombia-seguridad.cc"]
        }
        report = generate_police_report(sample_evidence)
        st.markdown(report["formatted_markdown"])
