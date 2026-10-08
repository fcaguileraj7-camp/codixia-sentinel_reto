# 📅 HITOS Y ASIGNACIONES POR ROL — EQUIPO CODIXIA
## Reto Agente 2026 (Platica.mx × Campuslands)
### Proyecto: SentinelGuard AI · El Guardaespaldas Autónomo Ciudadano (Digital & Físico)

> **Documento Oficial de Entregables, Responsabilidades y Matriz por Fases**  
> **Estrategia Aprobada por el Equipo:** Desarrollo Secuencial por Bloques.  
> - **FASE 1 (Semanas 1 y 2):** 100% del equipo enfocado en el **Escudo Digital Antifraude** para lograr un MVP funcional, robusto y con video demo de 2 min.  
> - **FASE 2 (Semana 3):** Activación e integración del **Acompañamiento Físico (Rutas y Taxis nocturnos)** sobre la misma base modular.  
> - **FASE 3 (Semana 4):** Prueba de carga masiva unificada (1.000 requerimientos duales).  
> - **CIERRE (Noviembre):** Mentorías 1 a 1, pitch deck, video final y postulación a premiación.  
> **Fecha de Inicio Oficial:** 5 de Octubre de 2026  
> **Estado:** Ratificado por el equipo · Octubre 2026

---

## 🧭 1. Resumen Ejecutivo del Calendario Semanal (Track 1)

| Hito | Fase del Proyecto | Ventana Temporal | Qué exige la Organización (Platica / Campuslands) | Responsable de Entrega |
| :---: | :--- | :---: | :--- | :--- |
| **S1** | **Semana 1 · Agente Corriendo**<br>*(Base Escudo Digital)* | **Oct 5 - 11**<br>*(Semana actual)* | Repositorio estructurado, README fundamentado, cliente funcional contra Grok y prueba documentada. | **Fabián Aguilera**<br>*(¡Completado al 100%!)* |
| **S2** | **Semana 2 · Herramientas Reales**<br>*(MVP 100% Escudo Digital)* | **Oct 12 - 18** | Conexión de 3+ herramientas antifraude reales, tolerancia a fallos, 10 ejecuciones grabadas y **video demo de 2 minutos**. | **Nicolle, Santiago, Miguel** (Tools)<br>+ **Juan José** (UI Streamlit) |
| **S3** | **Semana 3 · Datos Reales**<br>*(Activación Acompañamiento Físico)* | **Oct 19 - 25** | Memoria multi-turno + Incorporación del módulo de taxis/rutas + Dataset de **30+ casos reales evaluados** y reporte de costos. | **Juan José & Fabián** (Dataset & Memory)<br>+ Equipo en Módulo Físico |
| **S4** | **Semana 4 · Semana de Carga**<br>*(Carga Masiva Dual)* | **Oct 26 - Nov 1** | Procesar **1.000 unidades desatendidas en 12 horas** (mixto: fraude digital + telemetría de taxis), bitácora y latencias. | **Juan José & Santiago** |
| **Final** | **Refinamiento & Demo Day**<br>*(Agente Integral Dual)* | **Noviembre**<br>*(Cierre del Reto)* | Sesiones de mentoría 1 a 1 con fundadores de Platica, video final de impacto, diapositivas y postulación a premiación. | **Todo el Equipo Codixia** |

---

## 👥 2. Matriz Maestra de Asignaciones por Fase y Semana

| Integrante | Rol en el Equipo | FASE 1: Semanas 1 y 2 (Oct 5 - 18)<br>🛡️ **100% Escudo Digital (Antifraude)** | FASE 2: Semana 3 (Oct 19 - 25)<br>🚖 **Activación Acompañamiento Físico (Taxis)** | FASE 3: Semana 4 (Oct 26 - Nov 1)<br>⚡ **Carga Masiva (1.000 Reqs Duales)** | CIERRE: Noviembre<br>🏆 **Pitch & Premiación** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fabián Aguilera** | *Lead Architect & Orchestrator* | **S1:** Cliente Grok + Base repo.<br>**S2:** Orquestador dinámico de Tools Antifraude (`threat`, `url`, `vision`, `police`). | **S3:** Bucle de temporizador desatendido (*timer loop*) para check-ins de taxi + Memoria multi-turno (`memory.py`). | **S4:** Optimización de concurrencia y latencia para absorber las 1.000 peticiones mixtas. | **Final:** Release `v1.0.0` unificado, auditoría técnica de rúbricas del jurado. |
| **Nicolle** | *Social Eng. & NLP Specialist* | **S1:** Detección de bancos.<br>**S2:** Detección de urgencia, extorsión carcelaria y falso familiar en WhatsApp. | **S3:** Detector de estrés y palabras de pánico del pasajero en taxi (*"ayuda"*, *"no me deja bajar"*, coacción). | **S4:** Pruebas de estrés NLP con textos malformados y audios/mensajes simulados. | **Final:** Redacción de métricas de precisión de detección de amenazas. |
| **Santiago** | *Network & Telemetry Specialist* | **S1:** Extracción de URLs.<br>**S2:** Desenrollado de acortadores (`bit.ly`, `t.co`) y detección de *typosquatting* bancario. | **S3:** Telemetría de ruta: detección de paradas sospechosas prolongadas o desvíos de trayecto. | **S4:** Caché en memoria (`lru_cache`) para responder telemetría en <1 ms. | **Final:** Diagramas técnicos de seguridad de red y geolocalización. |
| **Miguel** | *Vision & Emergency Dispatch* | **S1:** Formato base CAI.<br>**S2:** Comprobantes falsos con Grok Vision + **Edición del Video Demo 2 min (Antifraude)**. | **S3:** Escalada de emergencia física: despacho de alerta SOS con placa, GPS y audio disuasivo en altavoz. | **S4:** Pruebas de robustez en generación de reportes y alertas continuas. | **Final:** Video final de impacto mostrando ambos casos de uso integrados. |
| **Juan José** | *Dataset, UI & Stress Testing* | **S1:** Verificación local.<br>**S2:** Interfaz web en **`app_streamlit.py`** (Pestaña Antifraude) para el video demo de 2 min. | **S3:** Pestaña de Acompañamiento en Streamlit + Dataset dual (20 estafas + 10 trayectos de taxi). | **S4:** Ejecución del arnés de **1.000 peticiones en 12h** (`load_test_1000.py`) con bitácora. | **Final:** Estructuración del guion del pitch y co-presentación en vivo. |

---

## 🔄 3. Transferencia de Roles: Módulo 1 (Digital) vs. Módulo 2 (Físico)

Las habilidades técnicas desarrolladas en las Semanas 1 y 2 se reutilizan directamente en la Semana 3:

| Miembro | En el Módulo 1 (Escudo Digital · Semanas 1 y 2) | En el Módulo 2 (Acompañamiento Físico · Semana 3) |
| :--- | :--- | :--- |
| **Fabián** | Orquesta el análisis de capturas, enlaces y chats fraudulentos. | Orquesta el temporizador autónomo de check-in preventivo en viajes. |
| **Nicolle** | Analiza si el mensaje es estafa, extorsión o suplantación financiera. | Analiza si el pasajero está asustado o siendo coaccionado en cabina. |
| **Santiago** | Inspecciona URLs, dominios maliciosos y acortadores. | Inspecciona la coherencia de la ruta y desvíos GPS sospechosos. |
| **Miguel** | Genera denuncias formales para el CAI Virtual de la Policía. | Dispara la alerta SOS con placa a contactos y audio disuasorio en altavoz. |
| **Juan José** | Construye la UI de análisis de texto/enlaces y casos de estafa. | Construye el simulador de ruta en Streamlit y casos de trayecto seguro/peligro. |

---

## 📋 4. Fichas de Misión por Integrante (Checklist de Tareas)

---

### 👤 1. FABIÁN AGUILERA — Lead Architect & Core Orchestrator
- **Semana 1 (Hito S1 · Oct 5 - 11):**
  - [x] Repositorio configurado con arquitectura limpia y ramas (`main`, `dev`).
  - [x] Cliente `src/client.py` con OpenAI SDK apuntando a `api.reto.pltk.mx/v1` y fallback local resiliente.
  - [x] Documentación maestra: `MASTER_PLAN_CODIXIA.md` y `README.md`.
  - [x] Subir link del repositorio al portal oficial `reto.pltk.mx`.
- **Semana 2 (Hito S2 · Oct 12 - 18):**
  - [ ] Implementar el ciclo dinámico de Tool Calling en `src/agent/sentinel.py` para activar las tools del Escudo Digital.
  - [ ] Revisar y aprobar los Pull Requests de Nicolle, Santiago y Miguel hacia `dev`.
- **Semana 3 (Hito S3 · Oct 19 - 25):**
  - [ ] Activar el bucle de temporizador en segundo plano para check-ins de taxi (`src/tools/route_companion.py`).
  - [ ] Crear el módulo de memoria conversacional multi-turno `src/agent/memory.py`.
- **Semana 4 (Hito S4 · Oct 26 - Nov 1):**
  - [ ] Optimizar la concurrencia del bucle del agente para que procese las 1.000 peticiones mixtas en <1.5s por turno.
- **Cierre Final (Noviembre):**
  - [ ] Congelar la versión final en GitHub (`tag v1.0.0`), auditar rúbricas de evaluación del jurado.

---

### 👤 2. NICOLLE — Social Engineering & NLP Specialist
- **Semana 1 (Hito S1 · Oct 5 - 11):**
  - [x] Módulo base `src/tools/threat_inspector.py` con catálogo de bancos colombianos.
  - [x] Pruebas unitarias en `tests/test_threat.py` pasando con `pytest`.
- **Semana 2 (Hito S2 · Oct 12 - 18):**
  - [ ] Ampliar reglas NLP de ingeniería social:
    - Urgencia artificial (*"bloqueo inmediato en 1 hora"*).
    - Falsa orden judicial (*"embargo de cuentas DIAN"*, *"orden de captura fiscalía"*).
    - Extorsión carcelaria (*"frente urbano"*, *"le tenemos ubicada la casa"*).
  - [ ] Generar un log con 10 ejecuciones reales documentadas.
- **Semana 3 (Hito S3 · Oct 19 - 25):**
  - [ ] Desarrollar detector de estrés/pánico para respuestas de audio/texto del pasajero en taxi.
  - [ ] Calibrar score de riesgo (0-100) y aportar casos de estafas al dataset de Juan José.
- **Semana 4 (Hito S4 · Oct 26 - Nov 1):**
  - [ ] Pruebas de robustez contra textos con emojis masivos, caracteres nulos o entradas malformadas.
- **Cierre Final (Noviembre):**
  - [ ] Redactar las métricas de precisión y efectividad NLP para las diapositivas del pitch.

---

### 👤 3. SANTIAGO — Network & Threat Sandbox Specialist
- **Semana 1 (Hito S1 · Oct 5 - 11):**
  - [x] Módulo base `src/tools/url_sandbox.py` con detección de TLDs riesgosos (`.xyz`, `.top`, `.cc`).
  - [x] Pruebas unitarias en `tests/test_sandbox.py` pasando con `pytest`.
- **Semana 2 (Hito S2 · Oct 12 - 18):**
  - [ ] Desenrollado seguro de enlaces acortados (`bit.ly`, `tinyurl.com`, `t.co`) con peticiones HTTP `HEAD` seguras.
  - [ ] Detección de typosquatting contra entidades financieras (`banc0lombia`, `nequii-pagos`).
- **Semana 3 (Hito S3 · Oct 19 - 25):**
  - [ ] Módulo de telemetría de ruta: lógica para detectar paradas sospechosas prolongadas o desvíos del trayecto.
  - [ ] Blacklist local de URLs fraudulentas reportadas por la Policía Cibernética.
- **Semana 4 (Hito S4 · Oct 26 - Nov 1):**
  - [ ] Implementar caché en memoria (`@lru_cache`) para responder consultas repetidas en <1 ms en la prueba de carga.
- **Cierre Final (Noviembre):**
  - [ ] Elaborar los diagramas de arquitectura de red y geolocalización para la presentación.

---

### 👤 4. MIGUEL — Multimodal Vision & Emergency Dispatch
- **Semana 1 (Hito S1 · Oct 5 - 11):**
  - [x] Módulos base `src/tools/police_reporter.py` y `src/tools/vision_parser.py`.
  - [x] Pruebas unitarias en `tests/test_vision.py` pasando con `pytest`.
- **Semana 2 (Hito S2 · Oct 12 - 18):**
  - [ ] Conectar `vision_parser.py` con Grok Vision (`grok-4.7`) para detectar comprobantes de pago falsificados.
  - [ ] **Liderar la grabación y edición del Video Demo de 2 minutos del Escudo Digital** (requisito formal de S2).
- **Semana 3 (Hito S3 · Oct 19 - 25):**
  - [ ] Implementar el protocolo de escalada SOS para viajes en taxi (`emergency_escalator.py`): compilación de placa, coordenadas y libreto de audio disuasorio en altavoz.
  - [ ] Formatear expediente legal con radicado y hash probatorio para radicar en CAI Virtual.
- **Semana 4 (Hito S4 · Oct 26 - Nov 1):**
  - [ ] Optimizar manejo de imágenes pesadas en Base64 para prevenir fugas de memoria en estrés.
- **Cierre Final (Noviembre):**
  - [ ] Pulir el video final de impacto para los jurados mostrando la protección integral (digital + física).

---

### 👤 5. JUAN JOSÉ — Dataset Engineering, Stress Testing & UI
- **Semana 1 (Hito S1 · Oct 5 - 11):**
  - [x] Clonar repo, configurar entorno virtual y ejecutar los 12 tests con `pytest`.
  - [x] Revisar la estructura base de datos en `data/scam_dataset_30.json`.
- **Semana 2 (Hito S2 · Oct 12 - 18):**
  - [ ] Personalizar y pulir la interfaz web en **`app_streamlit.py`** con el modo Escudo Digital (caja de texto, selector de ejemplos, alertas visuales y radicado policial) para facilitar la grabación del video demo de 2 min.
- **Semana 3 (Hito S3 · Oct 19 - 25):**
  - [ ] Añadir la pestaña de simulación de Acompañamiento en Taxi a la interfaz de Streamlit.
  - [ ] Completar y certificar los **30 casos reales** en `data/scam_dataset_30.json` (20 de fraude + 10 trayectos de taxi).
  - [ ] Medir el consumo de tokens y estimar el costo promedio en dólares por tarea analizada.
- **Semana 4 (Hito S4 · Oct 26 - Nov 1):**
  - [ ] Ejecutar el arnés de prueba de carga de 1.000 peticiones desatendidas (`scripts/load_test_1000.py`).
  - [ ] Generar el reporte `load_test_summary.json` documentando: latencia promedio, tasa de éxito (>99%) y peticiones/seg.
- **Cierre Final (Noviembre):**
  - [ ] Estructurar el guion del pitch final y co-presentar el proyecto en el Demo Day.

---

## 🚦 5. Convenciones de Ramas en Git

Para que cada uno trabaje en su propio espacio sin colisiones:

```bash
# 1. Crear tu rama según tu rol:
git checkout -b feature/<tu-nombre>-<tu-modulo>
# Ejemplos:
# git checkout -b feature/nicolle-nlp
# git checkout -b feature/santiago-url
# git checkout -b feature/miguel-vision
# git checkout -b feature/juanjo-ui

# 2. Hacer cambios y verificar que los tests pasen:
pytest tests/ -v

# 3. Guardar cambios con Conventional Commits:
git add .
git commit -m "feat(<modulo>): descripcion clara de lo que agregaste"

# 4. Subir tu rama a GitHub:
git push -u origin feature/<tu-nombre>-<tu-modulo>

# 5. Abrir Pull Request hacia 'dev' en GitHub
```

---

*Documento aprobado y ratificado por el **Equipo Codixia** · Reto Agente 2026*
