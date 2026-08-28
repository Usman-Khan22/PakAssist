"""
Lightweight tests for the Planner Agent.

Mocks the Gemini client so these run without network access or a live
API key — they check parsing/validation behavior for representative
inputs, not model quality.
"""
from unittest.mock import MagicMock, patch

from backend.agents.planner import PlannerOutput, run_planner
from backend.graph.graph import build_graph


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


def _graph_state(user_input: str) -> dict:
    return {
        "user_input": user_input,
        "intent": "",
        "service_type": "",
        "next_step": "",
        "response": "",
    }


@patch("backend.graph.graph.run_planner")
def test_graph_routes_to_knowledge(mock_run_planner):
    mock_run_planner.return_value = PlannerOutput(
        intent="apply_for_service",
        service_type="passport",
        next_step="knowledge",
    )

    result = build_graph().invoke(_graph_state("What documents do I need?"))

    assert result["response"] == "Request routed to knowledge."


@patch("backend.graph.graph.run_planner")
def test_graph_routes_to_action(mock_run_planner):
    mock_run_planner.return_value = PlannerOutput(
        intent="apply_for_service",
        service_type="driving_license",
        next_step="action",
    )

    result = build_graph().invoke(_graph_state("Apply for a license"))

    assert result["response"] == "Request routed to action."


@patch("backend.graph.graph.run_planner")
def test_graph_routes_unclear_request_to_clarification(mock_run_planner):
    mock_run_planner.return_value = PlannerOutput(
        intent="unknown",
        service_type="unknown",
        next_step="clarify",
    )

    result = build_graph().invoke(_graph_state("Hello"))

    assert result["response"] == "Please clarify which government service you need."