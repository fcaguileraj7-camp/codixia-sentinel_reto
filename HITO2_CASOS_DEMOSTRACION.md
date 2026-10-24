# 🛡️ Hito S2 — Casos de demostración locales (Escudo Digital)

**Rol 4 · Nicolle Camila Piñeros** — Social Eng. NLP, Visión & CAI Virtual
Reto Agente 2026 · Equipo Codixia

> **Costo de esta ejecución: $0.00 USD.**
> Ningún caso realizó llamadas a Grok, xAI, Platica ni a ningún servicio externo.
> El análisis semántico de imágenes se ejercita con un adaptador SIMULADO.
> La imagen de prueba es un PNG 1x1 generado en memoria (dato sintético).

## Reproducir

```bash
# Los 10 casos con salida legible (para grabar el video demo)
python scripts/run_hito2_demo.py

# Los mismos casos como pruebas automatizadas
python -m pytest tests/test_threat.py tests/test_vision.py -v
```

`scripts/run_hito2_demo.py` neutraliza `RETO_API_KEY` **antes** de importar `src`.
Como `src/config.py` usa `load_dotenv()` sin `override`, una variable ya definida
en el entorno gana sobre `.env`: el script es seguro incluso con una llave real.

---

## Tabla de resultados

| # | Identificador | Entrada de prueba | Herramientas | Esperado | Observado | Estado |
|---|---|---|---|---|---|---|
| 01 | Mensaje legítimo | "Hola mamá, ¿cómo estás? Ya llegué a la universidad, te llamo al almuerzo." | ThreatInspector | BAJO | `threat_level=BAJO`, `risk_score=0`, `is_ambiguous=True`, `vectors=[]` | ✅ |
| 02 | Phishing bancario | "Bancolombia: su cuenta ha sido bloqueada. Ingrese de inmediato a https://banc0lombia-seguridad.cc/login" | ThreatInspector + UrlSandbox | ALTO/CRÍTICO + vector bancario | `threat_level=CRÍTICO`, `risk_score=100`, vectores `urgencia_artificial`, `amenaza_bloqueo`, `falsa_autoridad_bancaria`, `dominio_enganoso`; UrlSandbox `verdict=MALICIOSO typosquatting=True` | ✅ |
| 03 | Urgencia artificial | "URGENTE: tiene 2 horas para actualizar sus datos o su cuenta será cerrada." | ThreatInspector | Vector `urgencia_artificial` | Vector detectado; `triggers=['urgente','2 horas']` | ✅ |
| 04 | Posible extorsión | "Hablamos del Frente Urbano. Tenemos ubicado su negocio. Si no nos colabora con 2 millones, aténgase a las consecuencias." | ThreatInspector | Vector `extorsion_carcelaria` | `threat_level=ALTO`; vectores `extorsion_carcelaria`, `solicitud_dinero` | ✅ |
| 05 | URL sospechosa | `https://bancolombia-seguro-login.xyz/recuperar` | UrlSandbox | MALICIOSO + typosquatting | `verdict=MALICIOSO`, `risk_score=100`, `typosquatting=True`, `impersonated_brand=bancolombia` | ✅ |
| 06 | Análisis visual | PNG 1x1 sintético en `tmp_path` | VisionParser + adaptador SIMULADO | Escenarios controlados | `falsificado→True`, `autentico→False`, `inconcluso→None`. Validación local real `magic_bytes=True`. `analysis_source=simulado_local` | ✅ |
| 07 | Mensaje ambiguo | "Hola, ¿me escribes luego cuando puedas?" | ThreatInspector | Ambiguo, BAJO | `is_ambiguous=True`, `threat_level=BAJO`, `vectors=[]` | ✅ |
| 08 | Entrada malformada | `None`, `12345`, `[]`, `{}` | ThreatInspector | Error, nunca "seguro" | Los cuatro: `status=error`, `error=entrada_invalida`, `level=NO_ANALIZADO`, `risk_score=0` | ✅ |
| 08b | Cadena vacía | `""` | ThreatInspector | Ambiguo, no "segura" | `status=success`, `is_ambiguous=True`, `vectors=[]` | ✅ |
| 09 | Fallo simulado | PNG válido + `SimulatedVisionAnalyzer(raise_exception=True)` | VisionParser | Fallo sin veredicto seguro | `status=error`, `error=fallo_analisis_semantico`, `is_fraudulent=None`, `analysis_source=no_disponible` | ✅ |
| 10 | Informe estructurado | Phishing + emisor `+57 300 111 2233` | ThreatInspector + PoliceReporter | Expediente CAI válido | `report_id=CAI-COL-20261014-DF9C1F94`, markdown con radicado y medidas, `faltantes=[]` | ✅ |
| 10b | Evidencia insuficiente | `{"sender_phone": "+57 300 111 2233"}` | PoliceReporter | No generar expediente | `status=error`, `error=evidencia_insuficiente`, `faltantes=['user_input','incident_type','risk_level']` | ✅ |

**Resultado: 10/10 casos aprobados** (12 comprobaciones incluyendo 08b y 10b).

---

## Aclaración obligatoria: integración real vs. simulación

**Verificado de forma real y local:**
- Benchmark local actual de `data/scam_dataset_30.json`: exactitud de severidad de 29/30 (96,7%). La única diferencia es CASE-025, un escenario de pánico físico que se excluye intencionalmente del alcance de fraude digital. En detección binaria digital, excluyendo CASE-025: 19/19 amenazas detectadas, 10/10 controles benignos descartados, 0 falsos positivos y 0 falsos negativos.
- Inspección de URLs (UrlSandbox, módulo de Miguel): typosquatting y TLD sospechosos.
- **Validación de archivo de imagen** (VisionParser): existencia, extensión permitida, **firmas binarias (magic bytes)** y tamaño. Comprobación auténtica ejecutada en local.
- Generación del expediente (PoliceReporter): radicado con UUID, validación de campos, marcado de datos ausentes.

**Simulado y declarado como tal:**
- El **análisis semántico de imágenes** (si un comprobante está falsificado) proviene de `SimulatedVisionAnalyzer`, no de Grok Vision. Viaja etiquetado en `analysis_source=simulado_local`.
- El **razonamiento del agente** sigue usando el fallback local de `GrokClient`.

⚠️ **No se afirma en ninguna parte que Grok Vision haya detectado una falsificación real.**

---

## Guion del video demo (2 minutos) — solo guion, NO grabado

| Tiempo | Escena | Qué mostrar en pantalla |
|---|---|---|
| 0:00–0:15 | Apertura | Título "SentinelGuard AI · Escudo Digital · Hito S2" y la leyenda **"Modo local · $0.00"** |
| 0:15–0:35 | Phishing real | `python scripts/run_hito2_demo.py` → Caso 02: `CRÍTICO`, los 4 vectores y `UrlSandbox → MALICIOSO` |
| 0:35–0:55 | Extorsión y urgencia | Casos 03 y 04: vectores `urgencia_artificial` y `extorsion_carcelaria` |
| 0:55–1:15 | Expediente policial | Caso 10: `CAI-COL-…` con radicado y medidas preventivas |
| 1:15–1:35 | Tolerancia a fallos | Casos 08 y 09: `NO_ANALIZADO` / `is_fraudulent=None` — el fallo no produce un falso "seguro" |
| 1:35–1:50 | Pruebas | `python -m pytest tests/test_threat.py tests/test_vision.py -v` con 59 pruebas en verde |
| 1:50–2:00 | Cierre | "Conexión real con Grok pendiente para la verificación final" + Equipo Codixia |

**Frases clave para la locución:**
- "Todo lo que ves corre en local y cuesta cero dólares."
- "Ninguna prueba toca la API de Grok."
- "Un análisis que falla nunca se convierte en un falso mensaje seguro."

---

## Pendientes para la integración externa con Grok

1. **`GrokVisionAnalyzer`**: implementar la interfaz `VisionAnalyzer` ya definida en `src/tools/vision_parser.py`. La validación local de *magic bytes* y tamaño se reutiliza sin cambios.
2. **Razonamiento del agente**: ejecutar el ciclo con transporte real autorizado.
3. **Calibración del score**: validar los pesos de `THREAT_VECTORS` contra los 30+ casos reales (Hito S3).
