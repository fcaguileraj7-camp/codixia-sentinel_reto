"""Unit tests for local trip tracking and SOS preparation."""

import datetime as dt
import json

import pytest

from src.agent.sentinel import SentinelAgent
from src.client import GrokClient
from src.tools import emergency_escalator, route_companion

FIXED_NOW = dt.datetime(2026, 1, 1, 10, 0, 0)


@pytest.fixture(autouse=True)
def isolate_module_state(monkeypatch):
    """Keep process-local trip and alert state isolated between tests."""
    monkeypatch.setattr(route_companion, "_TRIPS", {})
    monkeypatch.setattr(route_companion, "_now", lambda: FIXED_NOW)
    monkeypatch.setattr(emergency_escalator, "_now", lambda: FIXED_NOW)


def test_register_trip_success_and_unique_opaque_ids():
    first = route_companion.register_trip(
        plate="WDY-452",
        destination="Centro Comercial Andino",
        origin="Oficina",
        checkin_interval_minutes=10,
    )
    second = route_companion.register_trip(plate="WDY452", destination="Centro")

    assert first["status"] == "active"
    assert first["vehicle_plate"] == "WDY452"
    assert first["origin"] == "Oficina"
    assert first["next_checkin_scheduled"] == "2026-01-01T10:10:00"
    assert first["monitoring_active"] is True
    assert first["trip_id"].startswith("TRIP-")
    assert "WDY452" not in first["trip_id"]
    assert first["trip_id"] != second["trip_id"]


def test_sentinel_agent_can_use_route_tool_without_contract_changes():
    client = GrokClient(
        simulated_response=json.dumps(
            {
                "mode": "route_companion",
                "risk_level": "BAJO",
                "action": "CONTINUE_MONITORING",
            }
        )
    )
    agent = SentinelAgent(client=client)

    result = agent.process_message(
        "Voy en taxi hacia el centro",
        metadata={"plate": "ABC123", "destination": "Centro"},
    )

    assert result["status"] == "success"
    assert result["tool_results"]["route"]["status"] == "active"
    assert result["tool_results"]["route"]["vehicle_plate"] == "ABC123"
    assert result["tool_results"]["route"]["trip_id"].startswith("TRIP-")


@pytest.mark.parametrize("plate", ["-", "", "123456", "ABCDEF"])
def test_register_trip_rejects_invalid_plate(plate):
    with pytest.raises(ValueError):
        route_companion.register_trip(plate=plate, destination="Bogotá")


def test_register_trip_rejects_non_string_plate():
    with pytest.raises(TypeError):
        route_companion.register_trip(plate=123, destination="Bogotá")


@pytest.mark.parametrize("destination", ["", "  ", None])
def test_register_trip_requires_destination(destination):
    with pytest.raises(ValueError):
        route_companion.register_trip(plate="ABC123", destination=destination)


def test_register_trip_rejects_empty_origin():
    with pytest.raises(ValueError):
        route_companion.register_trip(plate="ABC123", destination="Bogotá", origin=" ")


@pytest.mark.parametrize("interval", [0, -1, 1441])
def test_register_trip_rejects_out_of_range_interval(interval):
    with pytest.raises(ValueError):
        route_companion.register_trip(
            plate="ABC123",
            destination="Bogotá",
            checkin_interval_minutes=interval,
        )


@pytest.mark.parametrize("interval", [True, 1.5, "10"])
def test_register_trip_rejects_non_integer_interval(interval):
    with pytest.raises(TypeError):
        route_companion.register_trip(
            plate="ABC123",
            destination="Bogotá",
            checkin_interval_minutes=interval,
        )


def test_register_trip_accepts_maximum_interval():
    trip = route_companion.register_trip(
        plate="ABC123",
        destination="Bogotá",
        checkin_interval_minutes=1440,
    )
    assert trip["checkin_interval_minutes"] == 1440
    assert trip["next_checkin_scheduled"] == "2026-01-02T10:00:00"


def test_checkin_due_boundary_creates_one_non_emergency_alert():
    trip = route_companion.register_trip(
        plate="TRL-981",
        destination="Suba",
        checkin_interval_minutes=10,
    )
    trip_id = trip["trip_id"]

    assert route_companion.detect_overdue_checkins(
        now=dt.datetime(2026, 1, 1, 10, 9, 59)
    ) == []
    assert route_companion.detect_overdue_checkins(
        now=dt.datetime(2026, 1, 1, 10, 10, 0)
    ) == [trip_id]
    assert route_companion.detect_overdue_checkins(
        now=dt.datetime(2026, 1, 1, 10, 11, 0)
    ) == [trip_id]

    status = route_companion.get_trip_status(trip_id)
    assert status["status"] == "checkin_pending"
    assert len(status["alerts"]) == 1
    alert = status["alerts"][0]
    assert alert["type"] == "MISSED_CHECKIN"
    assert alert["severity"] == "UNCONFIRMED"
    assert alert["notification_status"] == "not_sent"
    assert alert["emergency_confirmed"] is False


def test_checkin_resolves_pending_alert_and_reschedules_from_confirmation():
    trip = route_companion.register_trip(
        plate="TRL-981",
        destination="Suba",
        checkin_interval_minutes=10,
    )
    trip_id = trip["trip_id"]
    route_companion.detect_overdue_checkins(now=dt.datetime(2026, 1, 1, 10, 10))

    result = route_companion.confirm_checkin(
        trip_id,
        timestamp=dt.datetime(2026, 1, 1, 10, 12),
    )
    status = route_companion.get_trip_status(trip_id)

    assert result["status"] == "success"
    assert result["current_status"] == "active"
    assert result["next_checkin_scheduled"] == "2026-01-01T10:22:00"
    assert result["checkin_count"] == 1
    assert status["alerts"][0]["status"] == "resolved"
    assert status["alerts"][0]["resolved_at"] == "2026-01-01T10:12:00"


def test_finalize_stops_future_alerts_and_rejects_later_checkins():
    trip = route_companion.register_trip(
        plate="ABC123",
        destination="Centro",
        checkin_interval_minutes=1,
    )
    trip_id = trip["trip_id"]
    route_companion.detect_overdue_checkins(now=dt.datetime(2026, 1, 1, 10, 1))

    result = route_companion.finalize_trip(trip_id, reason="Llegada confirmada")
    assert result["status"] == "completed"
    assert route_companion.detect_overdue_checkins(
        now=dt.datetime(2026, 1, 1, 11, 0)
    ) == []
    assert route_companion.get_trip_status(trip_id)["status"] == "completed"
    assert route_companion.get_trip_status(trip_id)["alerts"][0]["status"] == "resolved"
    assert route_companion.confirm_checkin(trip_id)["error"] == "trip_already_finished"
    assert route_companion.finalize_trip(trip_id)["error"] == "trip_already_finished"


def test_unknown_trip_errors_are_structured():
    assert route_companion.get_trip_status("TRIP-MISSING")["error"] == "trip_not_found"
    assert route_companion.confirm_checkin("TRIP-MISSING")["error"] == "trip_not_found"
    assert route_companion.finalize_trip("TRIP-MISSING")["error"] == "trip_not_found"
    assert route_companion.get_trip_coordinates("TRIP-MISSING")["error"] == "trip_not_found"


def test_manual_sos_creates_auditable_record_without_claiming_delivery():
    trip = route_companion.register_trip(
        plate="ABC123",
        destination="Centro",
        origin="No usar como coordenada",
    )
    coordinates = route_companion.record_trip_coordinates(
        trip["trip_id"],
        latitude=4.711,
        longitude=-74.0721,
        source="user_provided",
        timestamp=FIXED_NOW,
    )

    result = route_companion.activate_trip_sos(
        trip_id=trip["trip_id"],
        incident_type="PHYSICAL_RISK",
        severity="HIGH",
        evidence_payload={"observation": "Conductor tomó otra ruta"},
        contacts=["Ana", "Luis"],
    )
    status = route_companion.get_trip_status(trip["trip_id"])

    assert coordinates["coordinates"]["source"] == "user_provided"
    assert result["status"] == "escalated"
    assert result["alert_status"] == "PREPARED"
    assert result["notification_status"] == "not_sent"
    assert result["contacts_notified"] == []
    assert result["contacts_requested_count"] == 2
    assert "Ana" not in repr(result)
    assert "Luis" not in repr(result)
    assert result["severity"] == "HIGH"
    assert result["alert_id"].startswith("ALERT-")
    assert result["incident_report"]["report_id"].startswith("SOS-")
    assert result["incident_report"]["evidence"]["coordinates"] == coordinates["coordinates"]
    assert result["trip_status"] == "emergency_pending"
    assert status["status"] == "emergency_pending"
    assert status["monitoring_active"] is False
    assert status["alerts"][-1]["type"] == "SOS"
    assert status["alerts"][-1]["notification_status"] == "not_sent"
    assert route_companion.confirm_checkin(trip["trip_id"])["error"] == "trip_emergency_pending"
    assert route_companion.activate_trip_sos(
        trip["trip_id"], "PHYSICAL_RISK"
    )["error"] == "trip_emergency_already_pending"


def test_sos_rejects_unknown_completed_and_invalid_incidents():
    assert route_companion.activate_trip_sos(
        "TRIP-MISSING", "PHYSICAL_RISK"
    )["error"] == "trip_not_found"
    trip = route_companion.register_trip(plate="ABC123", destination="Centro")
    route_companion.finalize_trip(trip["trip_id"])
    assert route_companion.activate_trip_sos(
        trip["trip_id"], "PHYSICAL_RISK"
    )["error"] == "trip_already_finished"

    with pytest.raises(ValueError):
        emergency_escalator.escalate_emergency("INVALID_TYPE")
    with pytest.raises(ValueError):
        emergency_escalator.escalate_emergency("THREAT", severity="URGENT")
    with pytest.raises(ValueError):
        emergency_escalator.escalate_emergency(
            "THREAT",
            evidence_payload={"not_json_serializable": object()},
        )


def test_sos_rejects_unregistered_coordinate_evidence():
    trip = route_companion.register_trip(plate="ABC123", destination="Centro")
    with pytest.raises(ValueError, match="Registre las coordenadas"):
        route_companion.activate_trip_sos(
            trip["trip_id"],
            "PHYSICAL_RISK",
            evidence_payload={
                "coordinates": {
                    "latitude": 4.7,
                    "longitude": -74.0,
                    "source": "unknown",
                }
            },
        )


def test_coordinate_storage_requires_valid_values_and_explicit_source():
    trip = route_companion.register_trip(plate="ABC123", destination="Centro")
    trip_id = trip["trip_id"]
    assert route_companion.get_trip_coordinates(trip_id)["coordinates"] is None

    with pytest.raises(ValueError):
        route_companion.record_trip_coordinates(trip_id, 91, 0, "gps")
    with pytest.raises(ValueError):
        route_companion.record_trip_coordinates(trip_id, 0, 181, "gps")
    with pytest.raises(ValueError):
        route_companion.record_trip_coordinates(trip_id, 0, 0, "")
    with pytest.raises(TypeError):
        route_companion.record_trip_coordinates(trip_id, True, 0, "gps")

    result = route_companion.record_trip_coordinates(
        trip_id, 4.7, -74.0, "simulated_test_provider"
    )
    assert result["status"] == "success"
    assert route_companion.get_trip_coordinates(trip_id)["coordinates"] == result["coordinates"]

    route_companion.finalize_trip(trip_id)
    assert route_companion.record_trip_coordinates(
        trip_id, 4.7, -74.0, "gps"
    )["error"] == "trip_already_finished"


def test_escalator_marks_record_prepared_and_never_uses_origin_as_location():
    result = emergency_escalator.escalate_emergency(
        incident_type="PHYSICAL_RISK",
        evidence_payload={"vehicle_plate": "ABC123", "origin": "Punto de partida"},
        contacts=["Ana"],
    )

    assert result["status"] == "escalated"
    assert result["alert_status"] == "PREPARED"
    assert result["notification_status"] == "not_sent"
    assert result["contacts_notified"] == []
    assert result["contacts_requested_count"] == 1
    assert result["severity"] == "CRITICAL"
    assert result["incident_type"] == "PHYSICAL_RISK"
    assert result["alert_id"] == result["incident_report"]["alert_id"]
    assert result["last_known_location"] is None
    assert result["coordinates"] is None
    assert "no se ha notificado" in result["deterrent_audio_script"]


def test_escalator_rejects_coordinates_without_provenance():
    with pytest.raises(ValueError, match="coordinates.source"):
        emergency_escalator.escalate_emergency(
            "PHYSICAL_RISK",
            {
                "coordinates": {
                    "latitude": 4.7,
                    "longitude": -74.0,
                }
            },
        )


def test_identical_sos_requests_receive_distinct_audit_ids():
    first = emergency_escalator.escalate_emergency(
        "THREAT", {"observation": "same evidence"}
    )
    second = emergency_escalator.escalate_emergency(
        "THREAT", {"observation": "same evidence"}
    )
    assert first["alert_id"] != second["alert_id"]
    assert first["incident_report"]["report_id"] != second["incident_report"]["report_id"]


def test_audio_panic_detection_does_not_dispatch_sos_automatically(monkeypatch):
    def fail_if_called(*args, **kwargs):
        pytest.fail("La detección de pánico no debe despachar SOS automáticamente.")

    monkeypatch.setattr(route_companion, "escalate_emergency", fail_if_called)
    result = route_companion.evaluate_trip_audio_response("Ayuda, tengo miedo")
    assert result["status"] == "alert"
    assert result["escalation_required"] is True


def test_audio_evaluation_validates_input():
    with pytest.raises(TypeError):
        route_companion.evaluate_trip_audio_response(123)
    with pytest.raises(TypeError):
        route_companion.evaluate_trip_audio_response("Estoy bien", expected_safe_word=123)
    with pytest.raises(ValueError):
        route_companion.evaluate_trip_audio_response("  ")


def test_checkin_and_coordinate_times_use_injectable_clock():
    trip = route_companion.register_trip(plate="ABC123", destination="Centro")
    checked_in = route_companion.confirm_checkin(trip["trip_id"])
    coordinates = route_companion.record_trip_coordinates(
        trip["trip_id"], 4.7, -74.0, "user_provided"
    )

    assert checked_in["last_checkin_at"] == FIXED_NOW.isoformat()
    assert checked_in["next_checkin_scheduled"] == "2026-01-01T10:10:00"
    assert coordinates["coordinates"]["recorded_at"] == FIXED_NOW.isoformat()
