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
| **S3** | **Semana 3 · Datos Reales**<br>*(Activación Acompañamiento Físico)* | **Oct 19 - 25** | Memoria multi-turno + Incorporación del módulo de taxis/rutas + Dataset de **30+ casos reales evaluados** y reporte de costos. | **Juan José & Fabián** (Dataset & Memory)<br>+ **Miguel** (Módulo Rutas/Taxis) |
| **S4** | **Semana 4 · Semana de Carga**<br>*(Carga Masiva Dual)* | **Oct 26 - Nov 1** | Procesar **1.000 unidades desatendidas en 12 horas** (mixto: fraude digital + telemetría de taxis), bitácora y latencias. | **Juan José & Santiago** |
| **Final** | **Refinamiento & Demo Day**<br>*(Agente Integral Dual)* | **Noviembre**<br>*(Cierre del Reto)* | Sesiones de mentoría 1 a 1 con fundadores de Platica, video final de impacto, diapositivas y postulación a premiación. | **Todo el Equipo Codixia** |

> 💰 **GESTIÓN DE CRÉDITOS Y TOKENS ($80.00 USD ASIGNADOS):**  
> - **Bolsa Compartida:** Los $80 USD asignados en el portal son compartidos entre los 5 integrantes.
> - **Desarrollo en Local ($0.00):** Se debe programar y probar en local usando `pytest` y el mock fallback de `src/client.py`.
> - **Tope de Seguridad:** Todas las llamadas a Grok tienen `max_tokens=500` para evitar respuestas largas innecesarias.
> - **Prohibidos bucles masivos:** Nunca correr scripts desatendidos con la API real sin previa medición de costo.

---

## 👥 2. Matriz Maestra de Asignaciones por Fase y Semana

| Integrante | Rol Oficial en el Equipo | Archivos Principales | FASE 1: Semanas 1 y 2 (Oct 5 - 18)<br>🛡️ **Escudo Digital (Antifraude)** | FASE 2: Semana 3 (Oct 19 - 25)<br>🚖 **Acompañamiento Físico (Taxis)** | FASE 3: Semana 4 (Oct 26 - Nov 1)<br>⚡ **Carga Masiva (1.000 Reqs Duales)** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fabián Aguilera** | **Rol 1: Lead Architect & Core Orchestrator** | `src/agent/sentinel.py`<br>`src/client.py`<br>`main.py` | Orquestador dinámico de Tools Antifraude y cliente Grok. | Memoria multi-turno en `src/agent/memory.py` y gestión de tokens. | Optimización de concurrencia y latencia del bucle central. |
| **Miguel** | **Rol 2: Network & Threat Sandbox Specialist** | `src/tools/url_sandbox.py`<br>`tests/test_sandbox.py` | Desenrollado de acortadores (`bit.ly`, `t.co`) y detector de *typosquatting* bancario. | Telemetría de red y optimización de latencia de conexiones. | Implementación de caché en memoria (`lru_cache`) para acelerar consultas. |
| **Santiago** | **Rol 3: Seguridad Física, Rutas & Acompañamiento** | `src/tools/route_companion.py`<br>`src/tools/emergency_escalator.py`<br>`tests/test_route.py` | Apoyo en integración de herramientas y pruebas de escalada en Fase 1. | **Lidera el módulo de Taxis**: registro de placas, temporizador de check-in y alerta SOS física. | Pruebas de estrés y robustez de monitoreo desatendido en viajes continuos. |
| **Nicolle** | **Rol 4: Social Eng. NLP, Visión & CAI Virtual** | `src/tools/threat_inspector.py`<br>`src/tools/vision_parser.py`<br>`src/tools/police_reporter.py`<br>`tests/test_threat.py`<br>`tests/test_vision.py` | Detección de urgencia, extorsión carcelaria, análisis de comprobantes falsos con Grok Vision y expediente para CAI Virtual. | Detección acústica/NLP de estrés y palabras de auxilio del pasajero en taxi. | Pruebas de robustez contra entradas malformadas y textos con emojis masivos. |
| **Juan José** | **Rol 5: Dataset Engineering, Stress & UI** | `data/scam_dataset_30.json`<br>`app_streamlit.py`<br>`scripts/load_test_1000.py`<br>`tests/test_performance.py` | Interfaz interactiva en Streamlit para el demo de 2 min y dataset preliminar. | Pestaña de monitoreo de viajes en Streamlit + Dataset dual de 30 casos reales. | Ejecución del arnés de **1.000 consultas desatendidas** en 12h y reporte de costos. |

---

## 🔄 3. Transferencia de Roles: Módulo 1 (Digital) vs. Módulo 2 (Físico)

Las habilidades técnicas desarrolladas en las Semanas 1 y 2 se reutilizan directamente en la Semana 3:

| Miembro | En el Módulo 1 (Escudo Digital · Semanas 1 y 2) | En el Módulo 2 (Acompañamiento Físico · Semana 3) |
| :--- | :--- | :--- |
| **Fabián (Rol 1)** | Orquesta el análisis de capturas, enlaces y chats fraudulentos. | Orquesta el temporizador autónomo de check-in preventivo en viajes. |
| **Miguel (Rol 2)** | Inspecciona URLs, dominios maliciosos y acortadores engañosos. | Optimiza la conectividad y latencia de telemetría de red. |
| **Santiago (Rol 3)** | Apoya la integración de alertas y escalada de incidentes. | Lidera el módulo de taxi: registro de placa, destino y protocolo SOS. |
| **Nicolle (Rol 4)** | Analiza manipulación psicológica, comprobantes falsos y CAI Virtual. | Analiza si el pasajero está asustado o siendo coaccionado en cabina. |
| **Juan José (Rol 5)** | Construye la UI de análisis de texto/enlaces y casos de estafa. | Construye el simulador de viaje en Streamlit y casos de trayectos seguros/peligro. |

---

## 📋 4. Fichas de Misión por Integrante (Checklist de Tareas)

---

### 👤 1. FABIÁN AGUILERA — Rol 1: Lead Architect & Core Orchestrator
- **Semana 1 (Hito S1 · Oct 5 - 11):**
  - [x] Repositorio configurado con arquitectura limpia y ramas (`main`, `dev`).
  - [x] Cliente `src/client.py` con OpenAI SDK apuntando a `api.reto.pltk.mx/v1` y fallback local resiliente.
  - [x] Documentación maestra: `MASTER_PLAN_CODIXIA.md` y `README.md`.
  - [x] Subir link del repositorio al portal oficial `reto.pltk.mx`.
- **Semana 2 (Hito S2 · Oct 12 - 18):**
  - [ ] Implementar el ciclo dinámico de Tool Calling en `src/agent/sentinel.py` para activar las tools del Escudo Digital.
  - [ ] Revisar y aprobar los Pull Requests de Miguel, Nicolle y Santiago hacia `dev`.
- **Semana 3 (Hito S3 · Oct 19 - 25):**
  - [ ] Crear el módulo de memoria conversacional multi-turno `src/agent/memory.py`.
  - [ ] Integrar el temporizador del módulo de taxi desarrollado por Santiago.
- **Semana 4 (Hito S4 · Oct 26 - Nov 1):**
  - [ ] Optimizar la concurrencia del bucle del agente para que procese las 1.000 peticiones mixtas en <1.5s por turno.
- **Cierre Final (Noviembre):**
  - [ ] Congelar la versión final en GitHub (`tag v1.0.0`), auditar rúbricas de evaluación del jurado.

---

### 👤 2. MIGUEL — Rol 2: Network & Threat Sandbox Specialist
- **Semana 1 (Hito S1 · Oct 5 - 11):**
  - [x] Módulo base `src/tools/url_sandbox.py` con detección de TLDs riesgosos (`.xyz`, `.top`, `.cc`).
  - [x] Pruebas unitarias en `tests/test_sandbox.py` pasando con `pytest`.
- **Semana 2 (Hito S2 · Oct 12 - 18):**
  - [ ] Desenrollado seguro de enlaces acortados (`bit.ly`, `tinyurl.com`, `t.co`) con peticiones HTTP `HEAD` seguras.
  - [ ] Detección de typosquatting contra entidades financieras (`banc0lombia`, `nequii-pagos`).
- **Semana 3 (Hito S3 · Oct 19 - 25):**
  - [ ] Blacklist local de URLs fraudulentas reportadas por la Policía Cibernética.
  - [ ] Telemetría de red y optimización de latencias para el módulo de taxi.
- **Semana 4 (Hito S4 · Oct 26 - Nov 1):**
  - [ ] Implementar caché en memoria (`@lru_cache`) para responder consultas repetidas en <1 ms en la prueba de carga.
- **Cierre Final (Noviembre):**
  - [ ] Elaborar los diagramas de arquitectura de red y ciberseguridad para la presentación.

---

### 👤 3. SANTIAGO — Rol 3: Seguridad Física, Rutas & Acompañamiento
- **Semana 1 (Hito S1 · Oct 5 - 11):**
  - [x] Módulos base `src/tools/route_companion.py` y `src/tools/emergency_escalator.py`.
  - [x] Pruebas unitarias en `tests/test_route.py` pasando con `pytest`.
- **Semana 2 (Hito S2 · Oct 12 - 18):**
  - [ ] Apoyo en la integración de alertas de emergencia y validación de flujos de escalada del Escudo Digital.
  - [ ] Preparación y diseño de la arquitectura de temporizadores para el módulo de taxis de Semana 3.
- **Semana 3 (Hito S3 · Oct 19 - 25):**
  - [ ] **Liderar el Módulo de Taxis**: registro de vehículo (placa, destino), intervalo de check-ins y evaluación acústica.
  - [ ] Protocolo de escalada SOS física: compilación de placa, últimas coordenadas y libreto de audio disuasorio en altavoz.
- **Semana 4 (Hito S4 · Oct 26 - Nov 1):**
  - [ ] Pruebas de robustez y resiliencia en monitoreo de viajes prolongados sin pérdida de estado.
- **Cierre Final (Noviembre):**
  - [ ] Demostración del módulo de acompañamiento físico y presentación técnica ante los jueces.

---

### 👤 4. NICOLLE — Rol 4: Social Eng. NLP, Visión & CAI Virtual
- **Semana 1 (Hito S1 · Oct 5 - 11):**
  - [x] Módulos base `src/tools/threat_inspector.py`, `src/tools/vision_parser.py` y `src/tools/police_reporter.py`.
  - [x] Pruebas unitarias en `tests/test_threat.py` y `tests/test_vision.py` pasando con `pytest`.
- **Semana 2 (Hito S2 · Oct 12 - 18):**
  - [ ] Ampliar reglas NLP de ingeniería social (urgencia artificial, falsa orden judicial, extorsión carcelaria).
  - [ ] Conectar `vision_parser.py` con Grok Vision (`grok-4.7`) para detectar comprobantes de pago falsificados.
  - [ ] **Liderar la grabación y edición del Video Demo de 2 minutos del Escudo Digital** (requisito formal de S2).
- **Semana 3 (Hito S3 · Oct 19 - 25):**
  - [ ] Desarrollar detector de estrés/pánico para respuestas de audio/texto del pasajero en taxi.
  - [ ] Calibrar score de riesgo (0-100) y aportar casos de estafas al dataset de Juan José.
- **Semana 4 (Hito S4 · Oct 26 - Nov 1):**
  - [ ] Pruebas de robustez contra textos con emojis masivos, caracteres nulos o entradas malformadas.
- **Cierre Final (Noviembre):**
  - [ ] Redactar las métricas de precisión y efectividad NLP/Visión para las diapositivas del pitch.

---

### 👤 5. JUAN JOSÉ — Rol 5: Dataset Engineering, Stress Testing & UI
- **Semana 1 (Hito S1 · Oct 5 - 11):**
  - [x] Clonar repo, configurar entorno virtual y ejecutar los 15 tests con `pytest`.
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
# git checkout -b feature/miguel-url
# git checkout -b feature/santiago-route
# git checkout -b feature/nicolle-nlp-vision
# git checkout -b feature/juanjo-ui-data

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
