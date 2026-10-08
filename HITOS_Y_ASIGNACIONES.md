# 📅 HITOS Y ASIGNACIONES POR ROL — EQUIPO CODIXIA
## Reto Agente 2026 (Platica.mx × Campuslands)
### Proyecto: SentinelGuard AI · Escudo Digital Antifraude y Extorsión

> **Documento Oficial de Entregables, Responsabilidades y Calendario Semanal**  
> **Estructura del Reto:** El reto tiene una duración de semanas completas (octubre - noviembre/diciembre 2026). Cada hito (**S1, S2, S3, S4**) representa una **Semana Completa de Desarrollo**, permitiendo iterar, probar y madurar cada módulo con calma y calidad profesional.  
> Cada integrante del equipo tiene una asignación equitativa (20%) con entregables específicos por cada semana.  
> **Estado:** Aprobado por el equipo · Octubre 2026

---

## 🧭 1. Resumen Ejecutivo de los Hitos Oficiales (Track 1)

| Hito | Nombre del Hito | Alcance Temporal | Qué exige la Organización (Platica / Campuslands) | Responsable de Entrega en Portal |
| :---: | :--- | :---: | :--- | :--- |
| **S1** | **Semana 1 · Agente Corriendo** | **Semana 1 (Oct 7 - 13)** | Repositorio público en GitHub, README claro con problema fundamentado, cliente funcional contra Grok y ejecución de prueba documentada. | **Fabián Aguilera** (Subir link al portal) |
| **S2** | **Semana 2 · Herramientas Reales** | **Semana 2 (Oct 14 - 20)** | Mínimo 3 herramientas reales conectadas al agente, tolerancia a fallos, 10 ejecuciones grabadas y **video demo de 2 minutos**. | **Miguel & Juan José** (Video y UI) + Equipo |
| **S3** | **Semana 3 · Datos Reales** | **Semana 3 (Oct 21 - 27)** | Memoria multi-turno + Conjunto de evaluación con **30+ casos reales** de estafas en Colombia, reporte de costo y consumo de tokens. | **Juan José & Fabián** |
| **S4** | **Semana 4 · Semana de Carga** | **Semana 4 (Oct 28 - Nov 3)** | Procesar **1.000 unidades de trabajo desatendidas** en 12 horas, bitácora de latencias, tasa de éxito y fallos. | **Juan José & Santiago** |
| **Entrega Final** | **Refinamiento & Pitch** | **Noviembre (Cierre del Reto)** | Sesiones de feedback 1 a 1 con mentores de Platica, repositorio final congelado, video de impacto, diapositivas y postulación a premiación. | **Todo el Equipo Codixia** |

> 💡 **Nota clave confirmada por Iván (CEO Platica) en el Kick-off:**  
> Los hitos **S1, S2, S3 y S4 son semanales**. A medida que la organización aprueba cada hito semanal, se van liberando nuevos tramos de créditos en la plataforma `reto.pltk.mx`. Tras las primeras 2 semanas se habilitan espacios de feedback 1 a 1 para asesorar a los equipos hacia el cierre de noviembre.

---

## 👥 2. Matriz Cruzada: ¿Qué entrega cada uno en cada Semana?

| Miembro | Semana 1 (S1)<br>*Agente Corriendo* | Semana 2 (S2)<br>*3 Tools Reales + Video* | Semana 3 (S3)<br>*30 Casos + Memoria* | Semana 4 (S4)<br>*1.000 Reqs de Carga* | Cierre Final<br>*Pitch & Premiación* |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fabián Aguilera**<br>*(Lead Architect)* | • Scaffolding base<br>• Cliente Grok + Fallback<br>• `main.py` CLI<br>• Envío en portal | • Orquestador dinámico (tool calling en `sentinel.py`)<br>• Integración de las 4 tools | • Memoria multi-turno en `src/agent/memory.py`<br>• Context window management | • Optimización de concurrencia para 1.000 reqs<br>• Resiliencia y control de errores | • Congelamiento de versión en GitHub (Tag v1.0)<br>• Cierre técnico y revisión final |
| **Nicolle**<br>*(Social Eng. NLP)* | • Catálogo inicial de entidades financieras<br>• `tests/test_threat.py` | • Detección avanzada de urgencia y amenazas penales<br>• 10 casos de prueba en log | • Calibración de score de riesgo (0-100)<br>• Aporte de 10 casos de estafas al dataset S3 | • Pruebas de estrés NLP (evitar caídas por textos raros o emojis pesados) | • Redacción de métricas de precisión NLP para el pitch |
| **Santiago**<br>*(Network Sandbox)* | • Extracción y normalización de URLs<br>• `tests/test_sandbox.py` | • Desenrollado de acortadores (`bit.ly`, `t.co`) con `HEAD`<br>• Detección de typosquatting | • Verificación de certificados y TLDs maliciosos (`.xyz`, `.cc`)<br>• Blacklist local | • Optimización de velocidad (caché DNS/URL para no saturar las 1.000 reqs) | • Métricas de ciberseguridad y red para las diapositivas |
| **Miguel**<br>*(Vision & CAI Police)* | • Formato base de denuncia policial<br>• `tests/test_vision.py` | • Conexión Grok Vision para comprobantes falsos<br>• Generador legal CAI Virtual | • Exportación de radicado policial en Markdown/PDF con firma técnica | • Optimización de procesamiento de imágenes base64 | • Grabación y edición del video demo oficial (2 minutos) |
| **Juan José**<br>*(Data, UI & Load)* | • Validación de entorno local y ejecución de tests | • Interfaz Web en `app_streamlit.py` lista para el video demo de 2 min | • Curaduría y etiquetado del dataset de 30+ casos reales (`scam_dataset_30.json`) | • Ejecución del arnés de 1.000 peticiones (`scripts/load_test_1000.py`) y log | • Estructuración del guion del pitch y co-presentación del proyecto |

---

## 📋 3. Fichas de Trabajo Individuales (Roadmap por Integrante)

---

### 👤 1. FABIÁN AGUILERA — Lead Architect & Core Orchestrator
**Objetivo:** Garantizar que el motor del agente sea robusto, modular, tolerante a fallos y que las herramientas de los compañeros se integren limpiamente.

- **Semana 1 (Hito S1):**
  - [x] Crear repositorio público en GitHub y configurar ramas (`main`, `dev`).
  - [x] Scaffolding de arquitectura (`src/`, `tests/`, `data/`, `scripts/`).
  - [x] Implementar `src/client.py` con OpenAI SDK apuntando a `https://api.reto.pltk.mx/v1` con fallback local inteligente.
  - [x] Redactar `MASTER_PLAN_CODIXIA.md` y `README.md`.
  - [x] Registrar la entrega oficial de S1 en el portal `reto.pltk.mx`.
- **Semana 2 (Hito S2):**
  - [ ] Implementar el ciclo de Tool Calling dinámico en `src/agent/sentinel.py` (llamar condicionalmente a `threat_inspector`, `url_sandbox`, `vision_parser` y `police_reporter`).
  - [ ] Revisar y aprobar los Pull Requests de Nicolle, Santiago y Miguel hacia la rama `dev`.
- **Semana 3 (Hito S3):**
  - [ ] Crear el módulo `src/agent/memory.py` para almacenar historial de conversación y contexto previo entre mensajes del mismo usuario.
  - [ ] Medir y registrar el consumo de tokens promedio por turno de conversación.
- **Semana 4 (Hito S4):**
  - [ ] Optimizar la velocidad de respuesta del bucle del agente para que el script de carga de Juan José corra sin timeouts.
- **Cierre Final (Hito S5):**
  - [ ] Merge final de `dev` a `main`, etiquetar release `v1.0.0` y verificar que el repositorio cumpla con todas las rúbricas.

---

### 👤 2. NICOLLE — Social Engineering & NLP Specialist
**Objetivo:** Desarrollar el cerebro de detección psicológica y lingüística del agente contra el engaño humano.

- **Semana 1 (Hito S1):**
  - [x] Crear el módulo base `src/tools/threat_inspector.py`.
  - [x] Configurar lista de bancos de Colombia (*Bancolombia, Nequi, Daviplata, BBVA, Scotiabank*).
  - [x] Crear `tests/test_threat.py` y verificar que pase con `pytest`.
- **Semana 2 (Hito S2):**
  - [ ] Ampliar las reglas de ingeniería social:
    - Falsa urgencia (*"última oportunidad"*, *"en menos de 1 hora"*).
    - Falsa autoridad judicial (*"orden de captura"*, *"mandamiento de pago DIAN"*, *"embargo de bienes"*).
    - Extorsión carcelaria (*"frente urbano"*, *"le tenemos ubicada la casa"*).
  - [ ] Generar un log con 10 ejecuciones documentadas de mensajes detectados.
- **Semana 3 (Hito S3):**
  - [ ] Calibrar el algoritmo de puntaje (`risk_score` de 0 a 100) para minimizar falsos positivos en mensajes cotidianos.
  - [ ] Aportar y validar al menos 10 casos de estafas de texto en `data/scam_dataset_30.json`.
- **Semana 4 (Hito S4):**
  - [ ] Realizar pruebas de robustez: asegurarse de que el analizador no falle si el mensaje contiene emojis masivos, caracteres nulos o textos de más de 5.000 palabras.
- **Cierre Final (Hito S5):**
  - [ ] Redactar el resumen de efectividad del analizador NLP para las diapositivas finales.

---

### 👤 3. SANTIAGO — Network & Threat Sandbox Specialist
**Objetivo:** Proteger al usuario de la trampa digital en la web (enlaces maliciosos, dominios clonados y acortadores engañosos).

- **Semana 1 (Hito S1):**
  - [x] Crear el módulo base `src/tools/url_sandbox.py`.
  - [x] Detección de dominios con TLDs de alto riesgo (`.xyz`, `.cc`, `.top`, `.ru`).
  - [x] Crear `tests/test_sandbox.py` y verificar que pase con `pytest`.
- **Semana 2 (Hito S2):**
  - [ ] Implementar la función de desenrollado de acortadores (`bit.ly`, `tinyurl.com`, `t.co`, `cutt.ly`):
    - Realizar petición HTTP `HEAD` con `requests` y timeout estricto (2 segundos) para obtener la URL de destino final sin descargar archivos maliciosos.
  - [ ] Implementar detector de *typosquatting* (ejemplo: detectar si `banc0lombia` o `nequii-pagos` imita la marca legal).
- **Semana 3 (Hito S3):**
  - [ ] Crear lista de bloqueo local (*Blacklist*) de dominios reportados en Colombia por la Policía Cibernética.
  - [ ] Integrar el análisis de URL dentro del contrato de datos de salida para el agente central.
- **Semana 4 (Hito S4):**
  - [ ] Implementar caché en memoria (`@lru_cache`) para URLs analizadas: si el arnés de 1.000 peticiones repite una URL, se responde en <1 milisegundo sin hacer peticiones externas.
- **Cierre Final (Hito S5):**
  - [ ] Elaborar el diagrama técnico de inspección de red para la presentación.

---

### 👤 4. MIGUEL — Multimodal Vision & Security Reporting
**Objetivo:** Detectar comprobantes de pago falsos mediante visión computacional y compilar los expedientes legales oficiales.

- **Semana 1 (Hito S1):**
  - [x] Crear el módulo base `src/tools/police_reporter.py` y `src/tools/vision_parser.py`.
  - [x] Crear `tests/test_vision.py` con pruebas unitarias pasando.
- **Semana 2 (Hito S2):**
  - [ ] Conectar `src/tools/vision_parser.py` con Grok Vision (`grok-4.7`) enviando imágenes en Base64 para evaluar comprobantes de Nequi/Bancolombia falsificados (tipografía desalineada, fecha adulterada, saldo incongruente).
  - [ ] Grabar y editar el **Video Demo de 2 minutos** (exigido para S2), mostrando al agente detectando una estafa en vivo y generando la denuncia.
- **Semana 3 (Hito S3):**
  - [ ] Enriquecer el formato de `police_reporter.py` para que genere expedientes listos para radicar en el portal CAI Virtual de la Policía (`caivirtual.policia.gov.co`), incluyendo hash SHA-256 de la evidencia.
- **Semana 4 (Hito S4):**
  - [ ] Probar tolerancia de carga en el generador de reportes con 100 incidentes secuenciales sin fugas de memoria.
- **Cierre Final (Hito S5):**
  - [ ] Pulir el video final de impacto para el jurado con la narrativa del proyecto.

---

### 👤 5. JUAN JOSÉ — Dataset Engineering, Stress Testing & UI
**Objetivo:** Desarrollar la interfaz visual interactiva, probar científicamente el agente con datos reales y certificar la escalabilidad en carga.

- **Semana 1 (Hito S1):**
  - [x] Clonar el repositorio y correr `python main.py --demo` y `pytest tests/ -v` en su entorno local para certificar paridad de desarrollo.
  - [x] Probar `data/scam_dataset_30.json` preliminar.
- **Semana 2 (Hito S2):**
  - [ ] Desarrollar y estilizar la interfaz web interactiva en `app_streamlit.py`:
    - Caja de texto para pegar mensajes de WhatsApp.
    - Selector de casos predefinidos de prueba.
    - Visualización visual de nivel de riesgo (Rojo = Crítico, Amarillo = Medio, Verde = Seguro).
    - Pestaña para visualizar la denuncia generada para la Policía.
  - [ ] Dejar la interfaz lista para que Miguel grabe el video demo de 2 minutos.
- **Semana 3 (Hito S3):**
  - [ ] Completar y certificar los **30 casos reales** en `data/scam_dataset_30.json`:
    - 10 casos de Phishing bancario (Nequi, Bancolombia, Daviplata).
    - 10 casos de Extorsión carcelaria y WhatsApp (amenazas, falso familiar).
    - 5 casos de Falsas ofertas laborales o compras Marketplace.
    - 5 casos legítimos de control (para medir falsos positivos).
  - [ ] Medir la precisión (% de acierto) y redactar el reporte de consumo de tokens y costos estimados por mensaje.
- **Semana 4 (Hito S4):**
  - [ ] Ejecutar el arnés de prueba de carga de 1.000 peticiones (`scripts/load_test_1000.py`).
  - [ ] Generar el reporte `load_test_summary.json` documentando: latencia promedio, peticiones por segundo y porcentaje de éxito (objetivo >99%).
- **Cierre Final (Hito S5):**
  - [ ] Diseñar las diapositivas de la presentación final y apoyar en la sustentación ante los jueces.

---

## 🚦 4. Flujo de Trabajo Git: Cómo subir cambios sin pisarse

Cada desarrollador trabaja en su propia rama y crea Pull Requests hacia `dev`:

```bash
# 1. Crear tu rama personal según tu rol:
git checkout -b feature/<tu-nombre>-<tu-modulo>
# Ejemplos:
# git checkout -b feature/nicolle-nlp
# git checkout -b feature/santiago-url
# git checkout -b feature/miguel-vision
# git checkout -b feature/juanjo-ui

# 2. Hacer cambios y probar que los tests sigan pasando:
pytest tests/ -v

# 3. Guardar cambios con commit semántico:
git add .
git commit -m "feat(<modulo>): descripcion clara de lo que agregaste"

# 4. Subir tu rama a GitHub:
git push -u origin feature/<tu-nombre>-<tu-modulo>

# 5. Crear Pull Request en GitHub hacia la rama 'dev'
```

---

## 🏆 5. Criterios de Evaluación del Reto (Rúbrica de Jurados)

Para ganar el reto, los jurados evalúan 5 aspectos:

1. **Autonomía del Agente (30%):** ¿El agente decide por sí mismo cuándo llamar herramientas y cuándo escalar alertas, sin requerir intervención humana constante?
2. **Utilidad Real y Relevancia (25%):** ¿Resuelve un problema urgente y cotidiano para ciudadanos en Colombia/Latinoamérica? *(SentinelGuard protege contra la pérdida de dinero y el engaño criminal)*.
3. **Resiliencia y Manejo de Errores (15%):** ¿Qué pasa si una API falla, la URL está caída o el mensaje tiene formato extraño? *(Implementado con fallback y validación de tipos)*.
4. **Pruebas y Evaluación Científica (15%):** ¿El equipo demostró que funciona con un dataset real (S3) y soportó carga masiva (S4)?
5. **Claridad del Pitch y Video (15%):** Video conciso de 2 minutos y demostración funcional.

---

*Documento aprobado y ratificado por el **Equipo Codixia** · Reto Agente 2026*
