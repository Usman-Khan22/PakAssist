"""
Lightweight tests for the Planner Agent.

Mocks the Gemini client so these run without network access or a live
API key — they check parsing/validation behavior for representative
inputs, not model quality.
"""
from unittest.mock import MagicMock, patch
import pytest

from backend.agents.planner import PlannerOutput, run_planner
from backend.graph.graph import build_graph
from langgraph.checkpoint.memory import InMemorySaver


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


@patch("backend.agents.planner._get_client")
def test_planner_receives_compact_context_for_follow_up(mock_get_client):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_response(
        "check_slots", "passport", "action"
    )
    mock_get_client.return_value = mock_client

    run_planner(
        "Show appointments for the first one.",
        context={
            "service_type": "passport",
            "office_options": ["Karachi-I (South)", "Karachi-II (Central)"],
        },
    )

    contents = mock_client.models.generate_content.call_args.kwargs["contents"]
    assert '"service_type": "passport"' in contents
    assert '"office_options"' in contents
    assert "Show appointments for the first one." in contents


@pytest.mark.parametrize(
    "query,raw_service",
    [
        ("book my passport appointment", "passport"),
        ("book an appointment for passport services in Karachi", "passport services"),
        ("passport ka appointment book karwa do", "passport_service"),
        (
            "book an appointment for driving licence services in Lahore",
            "driving licence services",
        ),
    ],
)
@patch("backend.agents.planner._get_client")
def test_supported_appointment_aliases_route_to_demo_booking(
    mock_get_client, query, raw_service
):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_response(
        "book_appointment", raw_service, "appointment"
    )
    mock_get_client.return_value = mock_client

    result = run_planner(query)

    assert result == PlannerOutput(
        intent="book_slot",
        service_type=(
            "driving_license" if "driving" in query else "passport"
        ),
        next_step="action",
    )


@patch("backend.agents.planner._get_client")
def test_explicit_service_overrides_previous_appointment_context(mock_get_client):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_response(
        "book_appointment", "passport", "appointment"
    )
    mock_get_client.return_value = mock_client

    result = run_planner(
        "Also book a driving license appointment in Lahore.",
        context={"service_type": "passport"},
    )

    assert result.service_type == "driving_license"
    assert result.intent == "book_slot"
    assert result.next_step == "action"


@patch("backend.agents.planner._get_client")
def test_appointment_follow_up_inherits_supported_service_context(mock_get_client):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_response(
        "book_appointment", "unknown", "appointment"
    )
    mock_get_client.return_value = mock_client

    result = run_planner(
        "Also book my appointment in Karachi.",
        context={"service_type": "passport", "intent": "service_journey"},
    )

    assert result == PlannerOutput(
        intent="book_slot", service_type="passport", next_step="action"
    )


@patch("backend.agents.planner._get_client")
def test_exact_passport_services_booking_routes_to_demo_action(mock_get_client):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_response(
        "book_appointment", "passport", "appointment"
    )
    mock_get_client.return_value = mock_client

    result = build_graph().invoke(
        {
            "user_input": (
                "Also book my appointment for the passport services in Karachi"
            )
        }
    )

    assert result["intent"] == "book_slot"
    assert result["service_type"] == "passport"
    assert result["next_step"] == "action"
    assert result["pending_clarification"] == "office"
    assert "demo appointment" in result["response"]
    assert "Karachi-I (South)" in result["response"]


@patch("backend.agents.planner._get_client")
def test_booking_follow_up_uses_same_session_passport_context(mock_get_client):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = [
        _mock_response("service_journey", "passport", "knowledge"),
        _mock_response("book_appointment", "unknown", "appointment"),
    ]
    mock_get_client.return_value = mock_client
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "passport-booking-context"}}

    first = graph.invoke({"user_input": "I need passport renewal."}, config=config)
    second = graph.invoke(
        {"user_input": "Also book my appointment in Karachi."}, config=config
    )

    assert first["service_type"] == "passport"
    assert second["intent"] == "book_slot"
    assert second["service_type"] == "passport"
    assert second["next_step"] == "action"
    assert "demo appointment" in second["response"]


def _graph_state(user_input: str) -> dict:
    return {
        "user_input": user_input,
        "intent": "",
        "service_type": "",
        "next_step": "",
        "response": "",
    }


@patch("backend.graph.graph.knowledge_agent")
@patch("backend.graph.graph.run_planner")
def test_graph_routes_to_knowledge(mock_run_planner, mock_knowledge_agent):
    mock_run_planner.return_value = PlannerOutput(
        intent="requirements_checklist",
        service_type="passport",
        next_step="knowledge",
    )
    mock_knowledge_agent.return_value = {"response": "Knowledge response."}

    result = build_graph().invoke(_graph_state("What documents do I need?"))

    assert result["response"] == "Knowledge response."
    mock_knowledge_agent.assert_called_once()


@patch("backend.graph.graph.run_planner")
def test_graph_routes_to_action(mock_run_planner):
    mock_run_planner.return_value = PlannerOutput(
        intent="service_center_lookup",
        service_type="driving_license",
        next_step="action",
    )

    result = build_graph().invoke(_graph_state("Find a driving license office in Attock"))

    assert "Attock Driving Licensing Branch" in result["response"]


@patch("backend.graph.graph.run_planner")
def test_graph_routes_unclear_request_to_clarification(mock_run_planner):
    mock_run_planner.return_value = PlannerOutput(
        intent="unknown",
        service_type="unknown",
        next_step="clarify",
    )

    result = build_graph().invoke(_graph_state("Something unclear"))

    assert result["response"] == "Please clarify which government service you need."


@pytest.mark.parametrize("greeting", ["Assalam Walekum", "salam", "salam hello", "Hello, salam!", " salam\nhello "])
@patch("backend.graph.graph.run_planner")
def test_roman_urdu_greeting(mock_run_planner, greeting):
    mock_run_planner.return_value = PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify")
    result = build_graph().invoke(_graph_state(greeting))
    assert "Wa Alaikum Assalam" in result["response"]
