# Propuestas de casos para Juan José — Nicolle (Hito 3)

Estas propuestas son sintéticas y están listas para revisión/incorporación por Juan José.
No se modificó `data/scam_dataset_30.json`.

## CASE-031
- category: ACOMPANAMIENTO_FISICO_PANICO
- expected_verdict: CRÍTICO
- text: "Voy en taxi placa XYZ-987 hacia el norte, el conductor se desvió por una trocha oscura, apagó las luces y no me responde. Auxilio, tengo miedo."
- entity_target: Pasajero
- has_malicious_url: false

## CASE-032
- category: ACOMPANAMIENTO_FISICO_COACCION
- expected_verdict: CRÍTICO
- text: "El conductor me amenaza, no me deja salir del vehículo y me está obligando a entregar mi celular."
- entity_target: Pasajero
- has_malicious_url: false

## CASE-033
- category: ACOMPANAMIENTO_FISICO_ESTRES
- expected_verdict: BAJO
- text: "Estoy nerviosa porque voy tarde a casa, pero el viaje va normal."
- entity_target: Pasajero
- has_malicious_url: false

## CASE-034
- category: PHISHING_BANCO
- expected_verdict: CRÍTICO
- text: "Bancolombia: su cuenta fue suspendida por actividad inusual. Ingrese a https://banc0lombia-alerta.cc para recuperarla."
- entity_target: Bancolombia
- has_malicious_url: true

## CASE-035
- category: EXTORSION_CARCELARIA
- expected_verdict: CRÍTICO
- text: "Hablamos del Frente Urbano. Tenemos ubicado su negocio. Si no consigna 2 millones, atengase a las consecuencias."
- entity_target: Comercio Local
- has_malicious_url: false

## CASE-036
- category: SUPLANTACION_FAMILIAR
- expected_verdict: CRÍTICO
- text: "Cambié de número porque me robaron. Tengo las maletas retenidas en aduana, consígneme 450 mil."
- entity_target: Familiar
- has_malicious_url: false

## CASE-037
- category: FALSA_OFERTA_LABORAL
- expected_verdict: ALTO
- text: "Amazon Colombia contrata para trabajar desde casa. Deposite 50.000 en https://trabajo-amazon-latam.top para activar."
- entity_target: Amazon
- has_malicious_url: true

## CASE-038
- category: PHISHING_NEQUI
- expected_verdict: CRÍTICO
- text: "Nequi Alerta: disponible suspendido. Actualice datos en https://nequii-seguridad.online."
- entity_target: Nequi
- has_malicious_url: true

## CASE-039
- category: LEGITIMO_CONTROL
- expected_verdict: BAJO
- text: "Bancolombia le informa que su pago fue exitoso. Si no reconoce la transacción comuníquese a la línea oficial."
- entity_target: Bancolombia
- has_malicious_url: false

## CASE-040
- category: ACOMPANAMIENTO_FISICO_AMBIGUO
- expected_verdict: BAJO
- text: "No sé qué hacer, estoy muy nerviosa."
- entity_target: Pasajero
- has_malicious_url: false
