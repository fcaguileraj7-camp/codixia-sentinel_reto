from types import SimpleNamespace

import src.client as client_module
from src.client import GrokClient


def _client_with_response(monkeypatch, response=None, error=None):
    class Completions:
        def create(self, **kwargs):
            if error is not None:
                raise error
            return response

    completions = Completions()
    monkeypatch.setattr(client_module, "is_configured", lambda: True)
    monkeypatch.setattr(
        client_module,
        "OpenAI",
        lambda **kwargs: SimpleNamespace(
            chat=SimpleNamespace(completions=completions)
        ),
    )
    return GrokClient(use_real_api=True)


def _response(usage):
    return SimpleNamespace(
        id="chatcmpl-audit-test",
        model="grok-4.7",
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"risk_level":"BAJO"}'))],
        usage=usage,
    )


def test_live_usage_records_provider_metadata_and_consistency(monkeypatch):
    client = _client_with_response(
        monkeypatch,
        response=_response(
            SimpleNamespace(prompt_tokens=11, completion_tokens=4, total_tokens=15)
        ),
    )

    client.chat_completion([{"role": "user", "content": "mensaje de prueba"}])

    assert client.last_usage["mode"] == "live_api"
    assert client.last_usage["execution_status"] == "provider_success"
    assert client.last_usage["usage_available"] is True
    assert client.last_usage["requested_model"] == "grok-4.7"
    assert client.last_usage["provider_model"] == "grok-4.7"
    assert client.last_usage["provider_response_id"] == "chatcmpl-audit-test"
    assert client.last_usage["usage_consistent"] is True


def test_live_response_without_usage_is_not_recorded_as_zero_cost(monkeypatch):
    client = _client_with_response(monkeypatch, response=_response(None))

    client.chat_completion([{"role": "user", "content": "mensaje de prueba"}])

    assert client.last_simulated is False
    assert client.last_usage["mode"] == "live_api"
    assert client.last_usage["execution_status"] == "provider_usage_missing_or_invalid"
    assert client.last_usage["usage_available"] is False
    assert client.last_usage["prompt_tokens"] is None
    assert client.last_usage["completion_tokens"] is None
    assert client.last_usage["total_tokens"] is None
    assert client.last_usage["estimated_cost_usd"] is None


def test_inconsistent_provider_total_is_preserved_and_flagged(monkeypatch):
    client = _client_with_response(
        monkeypatch,
        response=_response(
            SimpleNamespace(prompt_tokens=11, completion_tokens=4, total_tokens=22)
        ),
    )

    client.chat_completion([{"role": "user", "content": "mensaje de prueba"}])

    assert client.last_usage["provider_total_tokens"] == 22
    assert client.last_usage["total_tokens"] == 22
    assert client.last_usage["usage_consistent"] is False


def test_provider_failure_fallback_is_marked_unverifiable(monkeypatch):
    client = _client_with_response(
        monkeypatch,
        error=OSError("provider unavailable"),
    )

    client.chat_completion([{"role": "user", "content": "mensaje cotidiano"}])

    assert client.last_simulated is True
    assert client.last_source == "simulated"
    assert client.last_usage["mode"] == "simulated_after_provider_error"
    assert client.last_usage["execution_status"] == "simulated_fallback_after_provider_error"
    assert client.last_usage["usage_available"] is False
    assert client.last_usage["total_tokens"] is None
    assert client.last_usage["estimated_cost_usd"] is None
