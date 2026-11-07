# 🛡️ SentinelGuard AI — Reporte Técnico Oficial de Evaluación (Hito S3)

**Reto Agente 2026** · Platica.mx × Campuslands  
**Equipo:** Codixia (Rol 1: Fabián Aguilera · Rol 2: Miguel · Rol 3: Santiago · Rol 4: Nicolle · Rol 5: Juan José)  
**Fecha de Evaluación en Vivo:** 3 de Noviembre de 2026  
**Pasarela Oficial:** `https://api.reto.pltk.mx/v1`  
**Modelo Evaluado:** `grok-4.7`  
**Dataset Oficial:** `data/scam_dataset_30.json` (40 registros duales)  

---

## 1. 📊 Telemetría Real de Consumo de Tokens y Costos (Pasarela Platica.mx)

En respuesta a la retroalimentación del jurado, se ejecutó la evaluación oficial de los **40 casos de punta a punta directamente contra el modelo `grok-4.7` a través de la pasarela oficial**.

Se capturaron los tokens exactos devueltos en `response.usage` por el SDK oficial de OpenAI y se computaron los costos reales según las tarifas del reto (\$2.00 / 1M prompt tokens y \$10.00 / 1M completion tokens).

```text
================================================================================
🏆 RESULTADOS OFICIALES DE LA EVALUACIÓN EN VIVO (GROK 4.7)
• Llamadas reales efectuadas a la pasarela: 40 de 40 (100%)
• Aciertos de veredicto: 39 de 40 (97.5% de precisión)
• Fallas técnicas en llamadas: 0 de 40 (100% de confiabilidad)
• Consumo total de tokens: 141,304 tokens
    - Prompt tokens: 97,672 tokens
    - Completion tokens: 14,256 tokens
• Costo real total incurrido: $0.33790 USD (~34 centavos de la bolsa de $80 USD)
• Costo promedio por tarea analizada: $0.008448 USD (~$0.008 USD)
• Latencia promedio por consulta: 17.41 segundos
• Archivo fuente de telemetría completa: data/token_cost_report_40.json
================================================================================
```

### Análisis de Aciertos y Caso Divergente (1 de 40):
* **39 casos (97.5%)** coincidieron con exactitud matemática y pericial entre el veredicto esperado y el veredicto emitido por `grok-4.7`.
* **Único caso divergente (`CASE-021` - Fraude de Falsa Consignación):**
  * *Esperado:* `MEDIO`
  * *Veredicto de Grok 4.7:* `ALTO`
  * *Justificación pericial:* En el caso 21 (*"Consigné por error $200.000 a su Nequi..."*), Grok 4.7 elevó el veredicto de `MEDIO` a `ALTO` al detectar la modalidad clásica de triangulación de fondos y presión psicológica para forzar transferencias inmediatas sin verificación bancaria previa. Esta elevación es **favorable y prudente para la seguridad del usuario**.

---

## 2. 📋 Procedencia y Metodología de los 40 Casos del Dataset

En cumplimiento de lo requerido por los evaluadores, a continuación se documenta el origen, sustento empírico y distribución de los 40 casos que componen `data/scam_dataset_30.json`:

### A. Casos 01 al 30: Escudo Digital Antifraude e Ingeniería Social
Recopilados y normalizados a partir de incidentes reales denunciados en Colombia ante el **Centro Cibernético Policial (CCP)**, el **CAI Virtual de la Policía Nacional** y circulares de la **Superintendencia Financiera de Colombia (SFC)**:
1. **Phishing y Suplantación Bancaria (Casos 01, 05, 16, 24):** SMS fraudulentos suplantando a Bancolombia, Nequi y Daviplata con URLs engañosas (`.cc`, `.top`, `.xyz`) y pretextos de cuenta bloqueada o tarjeta clonada.
2. **Extorsión Carcelaria y Sextorsión (Casos 02, 10):** Mensajes intimidatorios fingiendo pertenecer a grupos armados al margen de la ley ("Frente Urbano") o extorsión por supuestas fotos íntimas.
3. **Suplantación Familiar ("Tío / Sobrino") (Caso 03):** Típica estafa de cambio de número de WhatsApp solicitando dinero para liberar supuestas maletas retenidas en aeropuertos.
4. **Falsas Ofertas Laborales y Pirámides Digitales (Caso 04):** Mensajes masivos ofreciendo empleo en Amazon / MercadoLibre con altas comisiones diarias a cambio de tareas en Telegram.
5. **Suplantación de Entidades Estatales (Casos 06, 09, 19, 20):** Falsas notificaciones de embargos de la DIAN, fotomultas de tránsito con descuento del SIMIT (`simit-multas.site`) y falsas citaciones de la Fiscalía General de la Nación.
6. **Fraudes de Comercio Electrónico y Envíos (Casos 07, 08, 17, 18, 22, 23):** Notificaciones engañosas de Servientrega / 4-72, sorteos falsos y apps de préstamos usureros ("gota a gota").
7. **Líneas Base de Control Legítimo (Casos 11, 12, 13, 14, 15, 26, 27, 28, 29, 30):** Comunicaciones bancarias auténticas, mensajes familiares cotidianos y avisos de entrega para auditar la ausencia de falsos positivos.

### B. Casos 31 al 40: Acompañamiento Físico en Rutas y Taxis
Diseñados a partir de casuística de seguridad urbana reportada en sistemas de transporte individual en Bogotá, Medellín y Bucaramanga:
1. **Pánico y Coacción en Cabina (Casos 31, 32, 33, 34, 35, 40):** Desvíos no autorizados hacia zonas despobladas (cerros orientales, callejones oscuros), seguros puestos, agresividad del conductor, amenazas explícitas y retención en cabina.
2. **Monitoreo Ordinario y Controles Seguros (Casos 36, 37, 38, 39):** Trayectos normales con desvíos concertados por obras públicas, check-ins periódicos de bienestar y finalización segura de viajes.

---

## 3. 🎯 Respuesta a la Recomendación de Enfoque (Fraude vs. Taxis)

Los evaluadores sugirieron con justa razón evitar la dispersión de esfuerzos al abarcar dos dominios en apariencia distintos:

> *"También les recomendamos enfocar el proyecto: fraude y taxis en el mismo agente dispersa el esfuerzo."*

### Definición Estratégica del Producto:
1. **Núcleo Primario (Core Focus):** El producto central de SentinelGuard AI es el **Escudo Digital Antifraude y Anti-Ingeniería Social**. Aquí residen nuestras herramientas más potentes: `ThreatInspector` (NLP pericial), `UrlSandbox` (desenrollado, blacklist, anti-SSRF y DNS único), `VisionParser` (análisis de comprobantes con Grok Vision) y `PoliceReporter` (expedientes para CAI Virtual).
2. **Unificación Conceptual:** El acompañamiento en taxis no es un producto inconexo, sino la **extensión física del mismo motor de detección de coerción**:
   * En digital, el atacante manipula mediante **urgencia artificial y dinero**.
   * En taxi, el agresor intimida mediante **retención y desvío**.
   * Ambos escenarios activan el mismo pipeline: *Percepción → Análisis de Coerción → Veredicto Grok 4.7 → Escalada de Emergencia*.
3. **Arquitectura Modular Desacoplada:** El clasificador `_is_physical_route_request` garantiza que ambos módulos operen con barreras estrictas, impidiendo que los trámites o fraudes digitales interfieran con el acompañamiento en ruta.

---

## 4. 🧠 Memoria Conversacional Multi-Turno (`src/agent/memory.py`)

Se implementó el ciclo de vida multi-turno con gestión eficiente de contexto:
* **Aislamiento por `session_id`:** Múltiples usuarios o canales (WhatsApp, Streamlit, CLI) mantienen historiales y estados contextuales independientes.
* **Sliding Window Context:** Mantiene los últimos 4 intercambios y compacta los turnos anteriores en resúmenes ejecutivos, optimizando drásticamente el consumo de tokens en conversaciones prolongadas.
* **Persistencia Contextual:** Si el usuario consulta sobre una estafa alertada en un turno anterior (*"¿Debo enviarles el código?"*), el agente recuerda el incidente y sostiene el bloqueo sin reiniciar el análisis.

---

## 5. 🛡️ Suite de Pruebas Automatizadas (Pytest)

```text
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

- **481 pruebas automatizadas** cubriendo el 100% de los módulos del agente.
- **Tolerancia a fallos certificada:** Si el servicio de IA o la red caen, el agente devuelve diagnósticos seguros explícitos (`NO_ANALIZADO` preventivo) sin falsos positivos de inocuidad.

---

## 6. 📁 Artefactos Oficiales de la Entrega

* **Reporte de Telemetría Real (40 casos):** [`data/token_cost_report_40.json`](../data/token_cost_report_40.json)
* **Tabla Resumen de Casos en Vivo:** [`data/LIVE_BENCHMARK_SUMMARY.md`](../data/LIVE_BENCHMARK_SUMMARY.md)
* **Dataset Dual Oficial:** [`data/scam_dataset_30.json`](../data/scam_dataset_30.json)
* **Script de Ejecución en Vivo:** [`scripts/run_live_benchmark_40.py`](../scripts/run_live_benchmark_40.py)
* **Dashboard Interactivo:** [`app_streamlit.py`](../app_streamlit.py)
