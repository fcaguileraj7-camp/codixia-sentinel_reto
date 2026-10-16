"""Pruebas unitarias para RouteCompanion y emergencias locales."""

import datetime as dt

import pytest

from src.tools.emergency_escalator import escalate_emergency
from src.tools.route_companion import (
    confirm_checkin,
    detect_overdue_checkins,
    finalize_trip,
    get_trip_status,
    register_trip,
    evaluate_trip_audio_response,
)


def test_register_trip_success():
    res = register_trip(plate="WDY-452", destination="Centro Comercial Andino")
    assert res["status"] == "active"
    assert res["vehicle_plate"] == "WDY452"
    assert "TRIP-WDY452-" in res["trip_id"]
    assert res["origin"] is None
    assert res["monitoring_active"] is True


def test_register_trip_invalid_plate_raises():
    with pytest.raises(ValueError):
        register_trip(plate="-", destination="Bogotá")


def test_register_trip_invalid_interval_raises():
    with pytest.raises(ValueError):
        register_trip(plate="ABC123", destination="Bogotá", checkin_interval_minutes=0)


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


def test_trip_state_and_overdue_checks():
    trip = register_trip(plate="TRL-981", destination="Suba", checkin_interval_minutes=10)
    trip_id = trip["trip_id"]

    assert get_trip_status(trip_id)["status"] == "active"
    confirm_checkin(trip_id, timestamp=dt.datetime(2026, 1, 1, 10, 0, 0))

    overdue = detect_overdue_checkins(now=dt.datetime(2026, 1, 1, 10, 15, 0))
    assert trip_id in overdue

    result = finalize_trip(trip_id)
    assert result["status"] == "completed"
    assert get_trip_status(trip_id)["status"] == "completed"


def test_misleading_trip_not_found_and_already_finished():
    missing = get_trip_status("TRIP-NO-EXISTS")
    assert missing["status"] == "error"

    trip = register_trip(plate="ABC123", destination="Centro")
    finalize_trip(trip["trip_id"])
    assert finalize_trip(trip["trip_id"])["status"] == "error"


def test_emergency_escalator_contract():
    result = escalate_emergency(
        incident_type="PHYSICAL_RISK",
        evidence_payload={"vehicle_plate": "ABC123", "destination": "Centro", "decision": {"risk_level": "CRITICO"}},
        contacts=["Ana", "Luis"],
    )

    assert result["status"] == "escalated"
    assert result["severity"] == "CRITICAL"
    assert result["incident_type"] == "PHYSICAL_RISK"
    assert "alert_id" in result
    assert result["contacts_notified"] == ["Ana", "Luis"]
    assert "deterrent_audio_script" in result
    assert bool(result["deterrent_audio_script"])


def test_emergency_escalator_invalid_type_raises():
    with pytest.raises(ValueError):
        escalate_emergency("INVALID_TYPE", {"decision": {"risk_level": "BAJO"}})
