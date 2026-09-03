"""Focused tests for the Action Agent service-center milestone."""

from unittest.mock import patch

from backend.agents.planner import PlannerOutput
from backend.graph.graph import build_graph


def _invoke(query: str, service_type: str, intent: str = "service_center_lookup"):
    planner_output = PlannerOutput(
        intent=intent,
        service_type=service_type,
        next_step="action",
    )
    with patch("backend.graph.graph.run_planner", return_value=planner_output):
        return build_graph().invoke({"user_input": query})


def test_passport_center_in_karachi():
    result = _invoke("Find a passport office in Karachi.", "passport")

    assert result["next_step"] == "action"
    assert "Karachi-I (South)" in result["response"]
    assert "Shahrah-e-Iraq" in result["response"]
    assert result["sources"]


def test_driving_license_center_in_represented_city():
    result = _invoke("Where can I get a driving license in Attock?", "driving_license")

    assert "Attock Driving Licensing Branch" in result["response"]
    assert "0579-316006" in result["response"]
    assert "High" in result["response"]


def test_driving_license_lahore_does_not_substitute_another_city():
    result = _invoke("Where can I get a driving license in Lahore?", "driving_license")

    assert "couldn't find" in result["response"]
    assert "Lahore" in result["response"]
    assert "Attock Driving Licensing Branch" not in result["response"]


def test_missing_location_requests_city_or_region():
    result = _invoke("Find the nearest passport office.", "passport")

    assert "Which city or region" in result["response"]
    assert result["sources"] == []


def test_unsupported_location_returns_no_result():
    result = _invoke("Find a passport office in Atlantis.", "passport")

    assert "couldn't find" in result["response"]
    assert "Atlantis" in result["response"]
    assert result["sources"] == []


@patch("backend.graph.graph.knowledge_agent", return_value={"response": "RAG response"})
def test_existing_knowledge_route_is_preserved(mock_knowledge):
    planner_output = PlannerOutput(
        intent="requirements",
        service_type="passport",
        next_step="knowledge",
    )
    with patch("backend.graph.graph.run_planner", return_value=planner_output):
        result = build_graph().invoke({"user_input": "What documents do I need?"})

    assert result["response"] == "RAG response"
    mock_knowledge.assert_called_once()


def test_existing_clarification_route_is_preserved():
    planner_output = PlannerOutput(
        intent="unknown",
        service_type="unknown",
        next_step="clarify",
    )
    with patch("backend.graph.graph.run_planner", return_value=planner_output):
        result = build_graph().invoke({"user_input": "Help me"})

    assert result["response"] == "Please clarify which government service you need."


def test_non_lookup_action_is_reported_as_unsupported():
    result = _invoke(
        "Submit my application now", "passport", intent="submit_application"
    )

    assert "not supported yet" in result["response"]
