# 🛡️ SentinelGuard AI — Reporte Técnico Oficial de Entrega (Hito S3)

**Reto Agente 2026** · Platica.mx × Campuslands  
**Equipo:** Codixia  
**Fecha:** Noviembre 1, 2026  
**Rama de Entrega:** `dev`  
**Commit:** Consolidado unificado  

---

## 1. 👥 Integrantes del Equipo y Asignación de Roles (20% por Miembro)

| Integrante | Rol Oficial | Módulos y Archivos Líderados en Hito S3 |
| :--- | :--- | :--- |
| **Fabián Aguilera** | **Rol 1: Lead Architect & Core Orchestrator** | `src/agent/sentinel.py`, `src/agent/memory.py`, `src/client.py`, tests de memoria y taxi audio. |
| **Miguel** | **Rol 2: Network & Threat Sandbox Specialist** | `src/tools/url_sandbox.py`, `data/url_blacklist.json`, capa anti-SSRF y single-resolution DNS. |
| **Santiago** | **Rol 3: Seguridad Física, Rutas & Acompañamiento** | `src/tools/route_companion.py`, `src/tools/emergency_escalator.py`, tests de ruta y auditoría SOS. |
| **Nicolle** | **Rol 4: Social Eng. NLP, Visión & CAI Virtual** | `src/tools/threat_inspector.py`, marcadores de coacción física en taxi, tests en `tests/test_threat.py`. |
| **Juan José** | **Rol 5: Dataset Engineering, Stress & UI** | `data/scam_dataset_30.json` (40 casos), `app_streamlit.py`, `scripts/benchmark_token_costs.py`, reportes de tokens. |

---

## 2. 🎯 Objetivos y Alcance Alcanzado en el Hito S3

El Hito S3 consolida la arquitectura híbrida de **SentinelGuard AI**, unificando el **Escudo Digital Antifraude** con el **Copiloto de Acompañamiento Físico en Rutas / Taxis**:

### A. Memoria Conversacional Multi-Turno (`src/agent/memory.py`)
- Implementación de `ConversationMemory` con aislamiento estricto por `session_id`.
- Mecanismo de **Sliding Window** que compacta el historial previo en resúmenes contextuales para evitar desbordamiento de contexto y minimizar el consumo de tokens.
- Persistencia de estado para incidentes de fraude en curso y monitoreo continuo de viajes de transporte activos.

### B. Acompañamiento Físico en Taxi y Evaluación Acústica/Texto
- Integración resiliente de `evaluate_trip_audio_response` para evaluar respuestas del pasajero tanto por texto directo como mediante transcripciones de audio (`metadata['audio_transcript']`).
- Verificación de palabra clave de seguridad (`expected_safe_word`) con estado `checkin_pending` para confirmación preventiva sin disparar falsas alarmas SOS.
- Protocolo determinista de escalada ante pánico o desvío crítico: genera expediente `PHYSICAL_RISK`, activa script disuasorio por altavoz y notifica a contactos predefinidos con identificador único de auditoría.
- Generación de identificadores opacos de viaje (`TRIP-{uuid}`) para proteger la privacidad de la matrícula vehicular.

### C. Inspección de Amenazas y Sandbox de Red Anti-Evasión
- Enriquecimiento de `threat_inspector.py` con marcadores periciales de coacción y retención física en cabina (`"me amenaza"`, `"me obliga"`, `"me retiene"`, `"no me deja salir"`).
- Lista negra local en `data/url_blacklist.json` con procedencia (`origin`), consulta ultra-rápida y telemetría de latencia (`telemetry.latency_ms` y `expansion_ms`).
- Optimización de red: resolución DNS única por salto (`single DNS lookup`) y blindaje estricto anti-SSRF (bloqueo de direcciones loopback, privadas y metadatos de nube).

### D. Dataset Dual y Benchmarking de Tokens
- Dataset ampliado a **40 casos reales colombianos** (`data/scam_dataset_30.json`): 30 casos de fraude digital/ingeniería social + 10 casos de acompañamiento físico y pánico en taxi.
- Script automatizado de benchmarking (`scripts/benchmark_token_costs.py`).
- Generación de reportes formales de consumo de tokens:
  - `data/token_cost_report_30.json` (30 casos base).
  - `data/token_cost_report_40.json` (40 casos duales completos).
- Panel interactivo en Streamlit (`app_streamlit.py`) con visualización gráfica del mapa de ruta, alertas SOS, telemetría y métricas de consumo de tokens en tiempo real.

---

## 3. 📊 Resultados de Pruebas y Certificación de Calidad

Toda la base de código cuenta con pruebas automatizadas continuas bajo `pytest`:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
collected 481 items

tests\test_agent.py ..........                                           [  2%]
tests\test_app_streamlit.py ...........................                  [  7%]
tests\test_memory.py ......                                              [  8%]
tests\test_multiturn.py ...                                              [  9%]
tests\test_network_dns_ports.py ......                                   [ 10%]
tests\test_network_gaps.py ....                                          [ 11%]
tests\test_network_hops.py .............                                 [ 14%]
tests\test_network_http.py ...........                                   [ 16%]
tests\test_network_ip.py ............................................... [ 26%]
tests\test_network_review_fixes.py ............                          [ 31%]
tests\test_performance.py ........                                       [ 33%]
tests\test_route.py ................................                     [ 39%]
tests\test_sandbox.py .................................................. [ 50%]
tests\test_taxi_audio_evaluation.py .......                              [ 80%]
tests\test_threat.py ..............................................      [ 90%]
tests\test_vision.py ...............................................     [100%]

============================ 481 passed in 10.56s =============================
```

- **Tasa de éxito:** 100% (481/481 pruebas exitosas).
- **Tiempo total de ejecución:** 10.56 segundos.
- **Gasto en pruebas locales:** **$0.00 USD** (blindaje de simulación determinista verificado en `src/client.py`).

---

## 4. 💰 Monitoreo de Tokens y Presupuesto

- **Modo Local de Pruebas:** Opera con tokens simulados y costo cero ($0.00 USD) para proteger la bolsa compartida de la API.
- **Modo en Vivo (Live Gateway `api.reto.pltk.mx/v1`):**
  - Prompt tokens promedio: ~180 tokens/turno.
  - Completion tokens promedio: ~95 tokens/turno.
  - Costo estimado por interacción: **~$0.000085 USD**.
  - El presupuesto disponible de $80.00 USD garantiza una capacidad teórica de más de **900.000 consultas** asistidas.

---

## 5. 🛠️ Resiliencia y Manejo de Fallas

1. **Tolerancia a Caídas de Red y API:** Si la API externa no responde o falla, el agente conmuta de forma transparente al motor heurístico determinista sin arrojar falsos veredictos (`NO_ANALIZADO` preventivo si ocurre excepción crítica).
2. **Prevención de Falsas Alarmas:** La ausencia de palabra clave de seguridad genera un estado preventivo de confirmación (`checkin_pending`, score 50) antes de escalar a alarma crítica física.
3. **Aislamiento Total entre Modos:** El clasificador de enrutamiento pericial previene falsos positivos separando consultas de ciberseguridad (SIMIT, bancos, premios) del acompañamiento vehicular.
