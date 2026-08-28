"""
Lightweight tests for the Planner Agent.

Mocks the Gemini client so these run without network access or a live
API key — they check parsing/validation behavior for representative
inputs, not model quality.
"""
from unittest.mock import MagicMock, patch

from backend.agents.planner import PlannerOutput, run_planner


def _mock_response(intent: str, service_type: str, next_step: str) -> MagicMock:
    mock_response = MagicMock()
    mock_response.text = (
        f'{{"intent": "{intent}", "service_type": "{service_type}", '
        f'"next_step": "{next_step}"}}'
    )
    return mock_response


@patch("backend.agents.planner._get_client")
def test_english_driving_license(mock_get_client):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_response(
        "apply_for_service", "driving_license", "action"
    )
    mock_get_client.return_value = mock_client

    result = run_planner("I want to apply for a driving license.")

    assert isinstance(result, PlannerOutput)
    assert result.service_type == "driving_license"
    assert result.next_step == "action"


@patch("backend.agents.planner._get_client")
def test_english_passport(mock_get_client):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_response(
        "renew_service", "passport", "action"
    )
    mock_get_client.return_value = mock_client

    result = run_planner("I need to renew my passport.")

    assert result.service_type == "passport"
    assert result.intent == "renew_service"


@patch("backend.agents.planner._get_client")
def test_roman_urdu_driving_license(mock_get_client):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_response(
        "apply_for_service", "driving_license", "action"
    )
    mock_get_client.return_value = mock_client

    result = run_planner("Mujhe driving license banwana hai.")

    assert result.service_type == "driving_license"


@patch("backend.agents.planner._get_client")
def test_ambiguous_request(mock_get_client):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_response(
        "unknown", "unknown", "clarify"
    )
    mock_get_client.return_value = mock_client

    result = run_planner("hello")

    assert result.next_step == "clarify"