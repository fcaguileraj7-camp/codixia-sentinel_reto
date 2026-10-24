import re
from typing import Dict, Any
from urllib.parse import urlsplit

OFFICIAL_DOMAINS = [
    "bancolombia.com",
    "nequi.com.co",
    "daviplata.com",
    "davivienda.com",
    "bbva.com.co",
    "scotiabankcolpatria.com",
    "gob.co",
    "policia.gov.co"
]

SUSPICIOUS_KEYWORDS = [
    "bloqueada", "suspensión", "urgente", "inmediato", "haga clic",
    "transfiera", "premios", "sorteo", "felicidades", "código de seguridad",
    "actualice sus datos", "cai virtual", "embargo", "captura"
]

# ---------------------------------------------------------------------------
# Vectores de ataque ampliados (Hito S2)
#
# Cada vector aporta un peso al riesgo. Los pesos están calibrados para que un
# vector fuerte (extorsión, sextorsión, orden judicial falsa) sea suficiente
# para marcar ALTO/CRÍTICO sin producir falsos positivos en charlas cotidianas.
# ---------------------------------------------------------------------------
THREAT_VECTORS: Dict[str, Dict[str, Any]] = {
    "urgencia_artificial": {
        "peso": 15,
        "patrones": [
            r"urgente", r"urgencia", r"inmediatamente?", r"de inmediato",
            r"lo antes posible",
            r"en menos de \d+\s*(hora|minuto|días?)", r"antes de \d+\s*(hora|minuto)",
            r"plazo (máximo|maximo)", r"vence (hoy|pronto)", r"último aviso",
            r"(?:tiene|dispone de|quedan?)\s+\d+\s*horas?\s+(?:para|antes de|o su cuenta)",
            r"hoy mismo"
        ],
        "descripcion": "Presión temporal artificial para impedir que la víctima verifique",
    },
    "amenaza_bloqueo": {
        "peso": 15,
        "patrones": [
            # Se admite cualquier mención de cuenta/usuaria bloqueada o suspendida,
            # incluso con texto interpuesto ("su cuenta está bloqueada").
            r"\bbloquead[ao]\b", r"bloqueo (preventivo|de su cuenta|temporal)",
            r"suspendid[ao]",
            r"suspensi[oó]n (?:de|para) (?:su )?(?:cuenta|perfil)",
            r"desactivada", r"inactivar", r"cierre de (su )?cuenta",
            r"recuperar su cuenta", r"desbloque"
        ],
        "descripcion": "Amenaza de bloqueo o suspensión para forzar una acción inmediata",
    },
    "falsa_autoridad_bancaria": {
        "peso": 15,
        "patrones": [
            r"(bancolombia|nequi|daviplata|davivienda|bbva|scotiabank).{0,80}"
            r"(bloquead[ao]|suspendid[ao]|actividad inusual|movimientos? sospechosos|"
            r"actualice sus datos|valide su cuenta)",
            r"entidad (bancaria|financiera)", r"su banco",
            r"movimientos? (inusuales|sospechosos)", r"actividad inusual"
        ],
        "descripcion": "Suplantación de entidad financiera o bancaria",
    },
    "falsa_autoridad_estatal": {
        "peso": 20,
        "patrones": [
            r"orden de captura", r"mandamiento de (pago|embargo|captura)",
            r"notificaci[oó]n judicial", r"embargo", r"\bdian\b", r"\bsimit\b",
            r"fotomultas?", r"proceso (judicial|penal|legal)", r"fiscal[ií]a",
            r"comparendo", r"c[ai]i virtual"
        ],
        "descripcion": "Suplantación de autoridad judicial o estatal (falsa orden, embargo o multa)",
    },
    "extorsion_carcelaria": {
        "peso": 45,
        "patrones": [
            r"frente urbano", r"aten[g]ase a las consecuencias",
            r"tenemos ubicado", r"sabemos d[oó]nde", r"consecuencias graves",
            r"si no (nos )?(colabora|paga|consigna|transfiere)",
            r"le hacemos (da[ñn]o|algo)", r"secuestr", r"plata o plomo",
            r"extorsi[oó]n", r"frente armado", r"zona (?:está )?rodeada",
            r"interceptadas? sus comunicaciones", r"no sale de la zona",
            r"captura de su camioneta"
        ],
        "descripcion": "Patrón de extorsión carcelaria o de organización criminal",
    },
    "sextorsion": {
        "peso": 45,
        "patrones": [
            r"grabaciones? ([íi]ntimas|[íi]ntimo)", r"v[íi]deos? ([íi]ntimas?|[íi]ntimo)",
            r"c[áa]mara web", r"fotos? ([íi]ntimas?|[íi]ntimo)",
            r"enviar[eé] (el video|las fotos)", r"difundir", r"todos sus contactos",
            r"bitcoin", r"billetera", r"criptomoneda"
        ],
        "descripcion": "Patrón de sextorsión con amenaza de difusión de material íntimo",
    },
    "solicitud_dinero": {
        "peso": 15,
        "patrones": [
            r"transfier[ae]", r"consign", r"dep[oó]sit[aeo]", r"pague (en|ya|de inmediato)",
            r"env[ií][ae] (el dinero|plata|\$)", r"colabor\w* con",
            r"n[uú]mero de (cuenta|nequi|daviplata)", r"recarg", r"abone",
            r"(pague|consigne|transfiera|env[ií]e).{0,30}\d+\s?(mil|millones)"
        ],
        "descripcion": "Exigencia directa de dinero, consignación o recarga",
    },
    "solicitud_credenciales": {
        "peso": 30,
        "patrones": [
            # Se exige un verbo de solicitud: un simple "su codigo de verificacion es..."
            # en una notificacion legitima del propio banco NO debe disparar la alarma.
            r"(env[íi]e|ind[íi]quenos|comparta|confirme|ingrese|proporcione|digite|suministre)"
            r"(?:\s+(?:de inmediato|inmediatamente|ahora|por favor))?"
            r"\s+(su\s+)?(el\s+)?c[oó]digo",
            r"clave (din[áa]mica|de seguridad)", r"token", r"\botp\b",
            r"actualice sus datos", r"valide su (identidad|cuenta)",
            r"confirme sus (datos|credenciales)", r"n[uú]mero de (tarjeta|c[eé]dula)",
            r"ingrese su (clave|contrase[ñn]a|usuario)"
        ],
        "descripcion": "Solicitud de credenciales, claves dinámicas o datos sensibles",
    },
    "suplantacion_familiar": {
        "peso": 45,
        "patrones": [
            r"cambi[eé] de n[uú]mero", r"me robaron", r"n[uú]mero nuevo",
            r"maletas (retenidas|decomisadas)", r"aduan", r"es una emergencia",
            r"m[eé]ndame (plata|dinero) r[áa]pido",
            r"soy (yo|tu (hijo|hija|nieto|nieta|primo|prima))"
        ],
        "descripcion": "Suplantación de identidad de un familiar con historia de emergencia",
    },
    "falsa_oferta": {
        "peso": 20,
        "patrones": [
            r"felicidades", r"ha sido (seleccionado|elegido|ganador)",
            r"sorteo", r"premio", r"gan[oó] (un|una|\\$)", r"trabajar desde casa",
            r"ganancias? (r[áa]pidas|diarias|desde)", r"vacantes", r"contratando personal",
            r"sin experiencia", r"oportunidad [uú]nica", r"pr[eé]stamos?",
            r"cr[eé]dito preaprobado", r"sin codeudor", r"cr[eé]dito (?:sin|con)"
        ],
        "descripcion": "Falsa oferta de premio, sorteo, préstamo o empleo (cebo de avaricia)",
    },
    "acortador_enmascarado": {
        "peso": 15,
        "patrones": [
            r"https?://bit\.ly", r"https?://tinyurl\.com", r"https?://t\.co",
            r"https?://is\.gd", r"https?://cutt\.ly", r"https?://rb\.gy"
        ],
        "descripcion": "Uso de acortador de URLs para ocultar el destino real",
    },
    "dominio_enganoso": {
        "peso": 25,
        "patrones": [
            r"https?://[^\s]*\.(xyz|top|cc|ru|tk|ml|ga|cf|gq|live|site|online)([/\s]|$)",
            r"https?://[^\s]*(banc0lombia|bancol[o0]mbia|nequ1|nequii|dav1plata)[^\s]*"
        ],
        "descripcion": "Dominio de alto riesgo o con errores tipográficos deliberados",
    },
    "fraude_comprobante_marketplace": {
        "peso": 40,
        "patrones": [
            r"(?:transferencia|transfer[ií]).{0,100}"
            r"(?:pantallazo|comprobante).{0,160}"
            r"(?:m[aá]nd\w+|env[ií]\w+|uber).{0,120}"
            r"(?:interbancari\w*|24 horas)"
        ],
        "descripcion": (
            "Presión para entregar un producto basada en un comprobante "
            "y una demora de liquidación no verificada"
        ),
    },
}

def _normalize(content: str) -> str:
    """Minúsculas y espacios colapsados. Tolera emojis masivos y caracteres nulos."""
    if not isinstance(content, str):
        return ""
    # Elimina caracteres de control y nulos que rompen las expresiones regulares.
    cleaned = "".join(ch for ch in content if ch.isprintable() or ch in " \n\t")
    return re.sub(r"\s+", " ", cleaned).lower()


def _is_official_url(url: str) -> bool:
    """Solo considera oficial un host autorizado o uno de sus subdominios."""
    candidate = url if "://" in url else f"http://{url}"
    try:
        hostname = (urlsplit(candidate).hostname or "").lower().rstrip(".")
    except ValueError:
        return False
    return any(
        hostname == domain or hostname.endswith(f".{domain}")
        for domain in OFFICIAL_DOMAINS
    )


def _extract_trigger_words(normalized_text: str, patterns: list) -> list:
    """Devuelve los fragmentos literales que dispararon cada patrón (trazabilidad)."""
    encontradas = []
    for patron in patterns:
        try:
            match = re.search(patron, normalized_text)
        except re.error:
            continue
        if match:
            token = match.group(0).strip()
            if token:
                encontradas.append(token)
    return encontradas


def _looks_like_transport_panic(text: str) -> bool:
    """Detecta contexto de riesgo físico real sin intención de fraude digital."""
    if not isinstance(text, str):
        return False
    lower = text.lower()
    transport_markers = [
        "taxi", "placa", "conductor", "trocha oscura", "desvió", "desvio",
        "auxilio", "miedo", "no me responde", "apagó las luces", "apago las luces",
        "no me deja", "nos vamos por otra ruta"
    ]
    digital_markers = [
        "banco", "bancolombia", "nequi", "daviplata", "simit", "dian",
        "claro", "sorteo", "premio", "ganador", "código", "codigo",
        "cuenta", "saldo", "transferencia", "consigne", "deposite",
        "embargo", "tarjeta", "credencial"
    ]
    has_transport = any(marker in lower for marker in transport_markers)
    has_digital_context = any(marker in lower for marker in digital_markers)
    return has_transport and not has_digital_context


def _looks_like_legitimate_confirmation(text: str) -> bool:
    """Evita interpretar como fraudulento un aviso de confirmación legítimo."""
    lower = text.lower()
    if "confirmada" not in lower and "confirmado" not in lower and "fue" not in lower:
        return False
    if any(term in lower for term in ["recarga", "saldo", "pago", "compra", "transferencia"]):
        return not any(request in lower for request in ["transfiera", "consigne", "envie", "pague", "deposite", "entregue", "devuelva"])
    return False


def _looks_like_direct_money_request(text: str) -> bool:
    lower = text.lower()
    return bool(re.search(r"(?:transfier[ae]|consign|dep[oó]sit[ae]|pague|env[ií][ae]|devuelva|devuelv|entregue|abone)", lower))


def _looks_like_fake_offer(text: str) -> bool:
    lower = text.lower()
    offer_terms = [
        "premio", "sorteo", "ganador", "ganaste",
        "trabajar desde casa", "contratando personal", "crédito preaprobado",
        "credito preaprobado", "préstamos", "prestamos", "sin codeudor",
        "ganancias diarias", "vacantes", "oportunidad única"
    ]
    if not any(term in lower for term in offer_terms):
        return False
    if any(term in lower for term in ["llame", "llámame", "comunícate", "comunicate", "reclame", "reclamar", "contacte", "contactar", "dr.", "doctor", "ingrese", "ingresa", "actualice", "deposite", "deposita"]):
        return True
    if re.search(r"(?:premio|sorteo|ganador).{0,120}(?:millon|millones|toyota|prado|claro|éxito|exito)", lower):
        return True
    return True


def inspect_threat(content: str) -> Dict[str, Any]:
    """
    Analiza un mensaje de texto, enlace o transcripción para detectar patrones
    de estafa, phishing o extorsión.

    Retorna el contrato del Hito S1 (compatible con el orquestador y con
    tests/test_performance.py) ampliado con los campos `detected_vectors` y
    `matched_keywords` exigidos por el contrato 6.1 del MASTER_PLAN.
    """
    # --- Validación de entrada: nunca convertir una entrada inválida en "seguro" ---
    if content is None or not isinstance(content, str):
        return {
            "status": "error",
            "error": "entrada_invalida",
            "message": "El contenido a analizar debe ser una cadena de texto.",
            "threat_level": "NO_ANALIZADO",
            "risk_score": 0,
            "detected_urls": [],
            "suspicious_urls": [],
            "matched_triggers": [],
            "matched_keywords": [],
            "detected_vectors": [],
            "is_ambiguous": True,
            "findings": [],
            "recommendation": "No fue posible analizar el contenido recibido."
        }

    findings = []
    matched_triggers = []
    detected_vectors = []
    risk_score = 0

    text = _normalize(content)
    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)
    route_panic_context = _looks_like_transport_panic(content)

    # 1. Análisis de URLs
    suspicious_urls = []
    for url in urls:
        is_official = _is_official_url(url)
        if not is_official:
            suspicious_urls.append(url)
            risk_score += 5
            findings.append(f"Enlace no oficial sospechoso detectado: {url}")
        else:
            findings.append(f"Enlace hacia dominio oficial: {url}")

    # 2. Análisis de Disparadores Psicológicos (Ingeniería Social) — vectores ampliados
    for vector_name, spec in THREAT_VECTORS.items():
        hits = _extract_trigger_words(text, spec["patrones"])
        if not hits:
            continue

        if vector_name == "urgencia_artificial" and route_panic_context:
            continue
        if vector_name == "solicitud_dinero" and _looks_like_legitimate_confirmation(content):
            continue
        if vector_name == "solicitud_credenciales" and not re.search(
            r"(?:env[ií]e|ind[ií]quenos|comparta|confirme|ingrese|proporcione|digite|suministre|verifique|compartir)",
            text,
        ):
            continue
        if vector_name == "falsa_oferta" and not _looks_like_fake_offer(content):
            continue

        weight = spec["peso"]
        if vector_name == "falsa_oferta" and _looks_like_fake_offer(content):
            weight = 30
        elif vector_name == "solicitud_credenciales":
            weight = 20
        elif vector_name == "dominio_enganoso":
            weight = 10
        elif vector_name == "solicitud_dinero":
            if _looks_like_direct_money_request(content):
                weight = 15
            else:
                weight = 0

        if weight <= 0:
            continue

        risk_score += weight
        detected_vectors.append(vector_name)
        for palabra in hits:
            if palabra not in matched_triggers:
                matched_triggers.append(palabra)
        findings.append(f"[{vector_name}] {spec['descripcion']}")

    # Compatibilidad hacia atrás: las palabras clave heredadas del S1.
    matched_keywords = [kw for kw in SUSPICIOUS_KEYWORDS if kw in text]
    if matched_keywords:
        findings.append(
            f"Disparadores de urgencia o alarma detectados: {', '.join(matched_keywords)}"
        )

    if "falsa_oferta" in detected_vectors and _looks_like_fake_offer(content):
        risk_score = max(risk_score, 40)
    if "urgencia_artificial" in detected_vectors and suspicious_urls:
        risk_score = max(risk_score, 40)

    if "amenaza_bloqueo" in detected_vectors and "solicitud_credenciales" in detected_vectors:
        risk_score = max(risk_score, 60)
    if "falsa_autoridad_estatal" in detected_vectors and "dominio_enganoso" in detected_vectors:
        risk_score = max(risk_score, 60)
    if "falsa_autoridad_estatal" in detected_vectors and "solicitud_dinero" in detected_vectors:
        risk_score = max(risk_score, 60)
    if any(vector in detected_vectors for vector in ["extorsion_carcelaria", "sextorsion", "suplantacion_familiar"]):
        risk_score = max(risk_score, 60)
    if not any(vector in detected_vectors for vector in ["extorsion_carcelaria", "sextorsion", "suplantacion_familiar", "amenaza_bloqueo", "falsa_autoridad_estatal"]):
        risk_score = min(risk_score, 55)

    if route_panic_context and not suspicious_urls and not detected_vectors:
        risk_score = 0

    # 3. Caso ambiguo: sin vectores, sin palabras clave y sin enlaces.
    is_ambiguous = not detected_vectors and not matched_keywords and not urls

    # 4. Clasificación de Nivel de Riesgo.
    #    Se incorpora el nivel ALTO exigido por el contrato 6.1 del MASTER_PLAN.
    if risk_score >= 60:
        threat_level = "CRÍTICO"
        recommendation = "No interactúe, no abra enlaces ni entregue códigos. Denuncie ante el CAI Virtual."
    elif risk_score >= 40:
        threat_level = "ALTO"
        recommendation = "Alta probabilidad de estafa o extorsión. No responda, bloquee el contacto y radique la denuncia."
    elif risk_score >= 20:
        threat_level = "MEDIO"
        recommendation = "Precaución: verifique directamente en la aplicación oficial del banco."
    elif risk_score > 0:
        threat_level = "BAJO"
        recommendation = "Se detectaron señales menores. Mantenga cautela ante solicitudes inesperadas."
    else:
        threat_level = "BAJO"
        recommendation = "No se identificaron patrones inmediatos de fraude conocido."

    return {
        "status": "success",
        "threat_level": threat_level,
        "risk_score": min(100, risk_score),
        "detected_urls": urls,
        "suspicious_urls": suspicious_urls,
        "matched_triggers": matched_triggers,
        "matched_keywords": matched_keywords,
        "detected_vectors": detected_vectors,
        "is_ambiguous": is_ambiguous,
        "findings": findings,
        "recommendation": recommendation
    }
