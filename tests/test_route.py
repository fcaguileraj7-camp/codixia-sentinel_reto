"""
Pruebas Unitarias para RouteCompanion
Rol 3: Miguel (Especialista en Seguridad Física, Rutas & Acompañamiento en Taxis)
"""

from src.tools.route_companion import register_trip, evaluate_trip_audio_response

def test_register_trip_success():
    res = register_trip(plate="WDY-452", destination="Centro Comercial Andino")
    assert res["status"] == "active"
    assert res["vehicle_plate"] == "WDY452"
    assert "TRIP-WDY452-" in res["trip_id"]
    assert res["monitoring_active"] is True

def test_evaluate_trip_normal():
    res = evaluate_trip_audio_response("Todo va bien, voy llegando a mi casa")
    assert res["status"] == "normal"
    assert res["is_safe"] is True
    assert res["escalation_required"] is False

def test_evaluate_trip_panic():
    res = evaluate_trip_audio_response("Ayuda por favor, el conductor tomó un desvío extraño y no me deja bajar")
    assert res["status"] == "alert"
    assert res["is_safe"] is False
    assert res["escalation_required"] is True
