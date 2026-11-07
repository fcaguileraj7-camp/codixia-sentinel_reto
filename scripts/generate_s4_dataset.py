"""
Generador de Dataset de Carga Masiva (1.050 Casos de Ciberfraude e Ingeniería Social)
Hito S4: Reto Agente 2026 · Platica.mx × Campuslands
Equipo: Codixia · SentinelGuard AI

Genera una cola parametrizada de 1.050 tareas realistas de ciberseguridad ciudadana
en Colombia y Latinoamérica, cubriendo 8 vectores principales de ataque y líneas base legítimas.
"""

import json
import random
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

random.seed(20261107)  # Semilla determinista

BANCOS = ["Bancolombia", "Nequi", "Daviplata", "Davivienda", "Banco de Bogotá", "BBVA", "Scotiabank Colpatria", "Banco Agrario"]
URLS_PHISHING = [
    "http://banc0lombia-seguridad.cc/login",
    "http://nequi-desbloqueo-urgente.top/validar",
    "https://daviplata-alerta24.xyz/clave",
    "http://verificacion-davivienda.site/portal",
    "https://bancobogota-actualizacion.me/cuentas",
    "http://bbva-seguridad-colombia.cc/token",
    "http://portal-bancario-seguro.top/ingreso",
    "https://scotiabank-seguridad.xyz/auth",
    "http://desbloquea-tu-cuenta-hoy.site/tramite",
    "http://nequi-soporte-oficial.cc/confirmar"
]
NOMBRES = ["Carlos", "María", "Andrés", "Laura", "Alejandro", "Camila", "Felipe", "Daniela", "Sebastián", "Valentina", "Juan", "Sofía"]
CIUDADES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga", "Pereira", "Cartagena"]
GRUPOS_EXTORSION = ["Frente 33", "Clan del Golfo", "Comandante Camilo", "Frente Urbano", "Autodefensas", "Comandante Wilson"]

def generar_phishing_bancario(i: int) -> dict:
    banco = random.choice(BANCOS)
    url = random.choice(URLS_PHISHING)
    variantes = [
        f"{banco} Alerta: Su cuenta ha sido bloqueada por intento de acceso no autorizado. Para reactivar su servicio antes de 2 horas ingrese aquí: {url}",
        f"Aviso urgente {banco}: Se detectó una transferencia saliente por $850.000 no reconocida. Si no fue usted, cancele la operación de inmediato en: {url}",
        f"{banco} Notificaciones: Su clave dinámica vencerá hoy. Para no perder acceso a su aplicación móvil, actualice sus credenciales de seguridad en: {url}",
        f"Estimado cliente de {banco}, su tarjeta de débito fue temporalmente inhabilitada por prevención de fraude. Verifique su identidad en {url} para desbloquearla.",
        f"{banco} Seguridad: Hemos generado una nueva política de autenticación. Ingrese con su documento y clave en {url} para validar su dispositivo."
    ]
    return {
        "task_id": f"TASK-{i:04d}",
        "category": "phishing_bancario",
        "sender": f"+573{random.randint(10000000, 29999999)}",
        "text": random.choice(variantes),
        "expected_risk": "ALTO"
    }

def generar_extorsion_digital(i: int) -> dict:
    grupo = random.choice(GRUPOS_EXTORSION)
    ciudad = random.choice(CIUDADES)
    monto = random.choice(["500.000", "1.000.000", "2.000.000", "300.000"])
    variantes = [
        f"Le habla el {grupo}. Sabemos dónde vive usted y su familia en {ciudad}. Tiene 2 horas para consignar ${monto} a este Nequi 312{random.randint(1000000, 9999999)} o aténgase a las consecuencias militares.",
        f"Atención comerciante: Por orden de la comandancia de {grupo} en {ciudad}, debe colaborar con el impuesto de guerra de ${monto}. Si no contesta la llamada en 15 minutos procedemos contra su negocio.",
        f"Tenemos fotos íntimas suyas y de sus contactos de Facebook. Si no transfiere ${monto} a Daviplata 310{random.randint(1000000, 9999999)} antes de las 3:00 PM, se las enviaremos a toda su familia y compañeros de trabajo.",
        f"Soy el Teniente Rodríguez de la Policía de {ciudad}. Tenemos a su familiar retenido por porte ilegal. Con ${monto} lo dejamos ir sin abrirle prontuario penal, comuníquese urgente a este número."
    ]
    return {
        "task_id": f"TASK-{i:04d}",
        "category": "extorsion_digital",
        "sender": f"+573{random.randint(10000000, 29999999)}",
        "text": random.choice(variantes),
        "expected_risk": "CRÍTICO"
    }

def generar_suplantacion_familiar(i: int) -> dict:
    familiar = random.choice(["tío", "tía", "primo", "sobrino", "abuela"])
    nombre = random.choice(NOMBRES)
    monto = random.choice(["250.000", "400.000", "600.000", "180.000"])
    variantes = [
        f"Hola {familiar}, soy {nombre}. Cambié de número de celular porque me robaron el anterior. Guarda este número. Te quería pedir un favor urgente, ¿tienes Nequi?",
        f"{familiar.capitalize()}, estoy en el aeropuerto El Dorado y la aerolínea me tiene retenidas unas maletas con mercancía. Necesito pagar un impuesto de ${monto} urgente o me decomisan todo. ¿Me ayudas?",
        f"Hola {familiar}, tuve un choque suave con un taxi saliendo del trabajo. El señor me pide ${monto} para no llamar a tránsito ni inmovilizarme la moto. Préstame por favor que mañana te devuelvo.",
        f"Buenas tardes {familiar}, te escribe {nombre}. Tengo mi cuenta bloqueada y necesito pagar la matrícula de la universidad hoy antes de las 4 PM. ¿Me puedes transferir ${monto} a la cuenta de mi amigo?"
    ]
    return {
        "task_id": f"TASK-{i:04d}",
        "category": "suplantacion_familiar",
        "sender": f"+573{random.randint(10000000, 29999999)}",
        "text": random.choice(variantes),
        "expected_risk": "ALTO"
    }

def generar_suplantacion_estatal(i: int) -> dict:
    variantes = [
        f"DIAN Notificaciones: Se ha emitido orden de embargo preventivo sobre sus cuentas por mora en declaración de renta. Descargue su liquidación oficial urgente aquí: http://dian-tramites-co.top/embargo",
        f"SIMIT Tránsito: Registra comparendo por exceso de velocidad con 50% de descuento por pronto pago ($260.000). Evite cobro coactivo pagando en: http://simit-multas-colombia.site/pago",
        f"FISCALÍA GENERAL: Se le cita con carácter urgente y obligatorio a comparecer por investigación penal en curso. Consulte la citación judicial firmada en: http://fiscalia-notificaciones.cc/citacion",
        f"ADRES / Prosperidad Social: Usted ha sido seleccionado para recibir el bono extraordinario de $500.000 de Ingreso Solidario. Inscriba su cuenta para el giro en: http://subsidios-colombia.xyz/registro"
    ]
    return {
        "task_id": f"TASK-{i:04d}",
        "category": "suplantacion_estatal",
        "sender": f"890{random.randint(100, 999)}",
        "text": random.choice(variantes),
        "expected_risk": "ALTO"
    }

def generar_falso_empleo(i: int) -> dict:
    empresa = random.choice(["Amazon", "Mercado Libre", "TikTok", "Shein", "YouTube"])
    ganancia = random.choice(["150.000 a 450.000", "200.000 a 800.000", "100.000 a 300.000"])
    variantes = [
        f"Hola! Representamos a {empresa} Colombia. Buscamos personal para trabajar desde casa 1 hora al día dando 'Me gusta' a videos y calificando productos. Ganancias de ${ganancia} diarios. Escríbenos a Telegram: https://t.me/reclutamiento_empleo_{random.randint(100,999)}",
        f"Oportunidad laboral inmediata: {empresa} solicita evaluadores de servicio remoto. Pago diario garantizado por Nequi o Daviplata. Sin experiencia previa. Inicia hoy enviando WhatsApp al +57312{random.randint(1000000,9999999)}.",
        f"Felicidades! Su perfil fue seleccionado para el programa de comisiones de {empresa}. Gane comisiones del 20% por cada tarea completada. Cupos limitados. Regístrese ya en: http://empleos-remotos-colombia.top"
    ]
    return {
        "task_id": f"TASK-{i:04d}",
        "category": "falso_empleo",
        "sender": f"+573{random.randint(10000000, 29999999)}",
        "text": random.choice(variantes),
        "expected_risk": "ALTO"
    }

def generar_falsas_encomiendas(i: int) -> dict:
    empresa = random.choice(["Servientrega", "4-72", "Coordinadora", "DHL"])
    guia = f"CO{random.randint(10000000, 99999999)}"
    valor = random.choice(["7.800", "9.500", "12.000", "8.200"])
    variantes = [
        f"{empresa} Alerta: Su paquete con guía {guia} no pudo ser entregado debido a error en la nomenclatura de su dirección. Para reprogramar la entrega y pagar flete de ${valor}, ingrese a: http://envios-nacionales.site/rastreo",
        f"Aviso de entrega {empresa}: Paquete retenido en centro logístico internacional. Pendiente pago arancelario de ${valor}. Ingrese su tarjeta en: http://aduanas-entregas.cc/guia-{guia}",
        f"Estimado usuario, {empresa} intentó entregar su encomienda hoy a las 11:30 AM pero no encontró quién recibiera. Actualice su entrega en http://rastreo-paqueteria.top/{guia}"
    ]
    return {
        "task_id": f"TASK-{i:04d}",
        "category": "falsas_encomiendas",
        "sender": f"87{random.randint(100, 999)}",
        "text": random.choice(variantes),
        "expected_risk": "ALTO"
    }

def generar_falsa_consignacion(i: int) -> dict:
    monto = random.choice(["150.000", "280.000", "350.000", "420.000"])
    variantes = [
        f"Buenas tardes vecino, qué pena molestarlo. Es que por error digité mal un número y le consigné ${monto} a su Nequi. Es la plata de la comida de mis hijos, ¿me los podría devolver por favor?",
        f"Hola, disculpa la molestia. Mi mamá te transfirió ${monto} a Daviplata equivocándose en el último dígito. Te adjunto el soporte de pago. Por favor devuélvelo al 314{random.randint(1000000, 9999999)}, te lo suplico.",
        f"Aviso Bancolombia: Le informamos que se acreditó en su cuenta una consignación por $500.000. Remitente solicita reversión inmediata comunicándose al 311{random.randint(1000000, 9999999)}."
    ]
    return {
        "task_id": f"TASK-{i:04d}",
        "category": "falsa_consignacion",
        "sender": f"+573{random.randint(10000000, 29999999)}",
        "text": random.choice(variantes),
        "expected_risk": "MEDIO"
    }

def generar_control_legitimo(i: int) -> dict:
    nombre = random.choice(NOMBRES)
    variantes = [
        f"Bancolombia informa: Compra por $45.200 en Éxito Calle 80 con su tarjeta débito terminada en 4321. Si no reconoce esta transacción comuníquese a la línea de atención al cliente.",
        f"Nequi: Tu código de seguridad para iniciar sesión es {random.randint(100000, 999999)}. Recuerda que Nequi NUNCA te pedirá este código por llamada o mensaje. No lo compartas con nadie.",
        f"Hola {nombre}, ya salí de la oficina y voy camino a la casa. ¿Quieres que compre algo de comer en el camino?",
        f"Daviplata te informa que recibiste un giro de $150.000 de {nombre}. Tu nuevo saldo disponible es $320.000. Consulta en tu app oficial.",
        f"Hola mamá, ya llegamos bien a la finca con los niños. El clima está delicioso. Te llamamos más tarde para saludarte.",
        f"Servientrega informa: Su envío con guía {random.randint(10000000, 99999999)} fue entregado exitosamente a satisfacción en la portería del edificio. Gracias por usar nuestros servicios.",
        f"Confirmación de cita médica: Su cita de medicina general con la Dra. Gómez está programada para mañana a las 9:00 AM en la sede norte. Llegar 15 minutos antes."
    ]
    return {
        "task_id": f"TASK-{i:04d}",
        "category": "control_legitimo",
        "sender": f"+573{random.randint(10000000, 29999999)}",
        "text": random.choice(variantes),
        "expected_risk": "BAJO"
    }

def main():
    generators = [
        (generar_phishing_bancario, 300),
        (generar_extorsion_digital, 160),
        (generar_suplantacion_familiar, 160),
        (generar_suplantacion_estatal, 150),
        (generar_falso_empleo, 110),
        (generar_falsas_encomiendas, 80),
        (generar_falsa_consignacion, 40),
        (generar_control_legitimo, 50),
    ]

    tasks = []
    task_num = 1
    for gen_func, count in generators:
        for _ in range(count):
            tasks.append(gen_func(task_num))
            task_num += 1

    # Desordenar aleatoriamente para simular tráfico de red del mundo real
    random.shuffle(tasks)

    # Reindexar orden cronológico
    for idx, t in enumerate(tasks, start=1):
        t["task_id"] = f"TASK-{idx:04d}"

    out_file = Path(__file__).resolve().parent.parent / "data" / "workload_queue_1050.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

    print(f"✅ Dataset de carga generado exitosamente con {len(tasks)} tareas.")
    print(f"📁 Guardado en: {out_file}")

if __name__ == "__main__":
    main()
