"""Focused tests for the Action Agent service-center milestone."""

from unittest.mock import patch
import pytest

from backend.agents.planner import PlannerOutput
from backend.graph.graph import build_graph
from backend.services.service_centers import lookup_service_centers


@pytest.mark.parametrize("service", ["passport", "driving_license"])
@pytest.mark.parametrize("query", [
    "find me passport offices near me Karachi",
    "find offices near me Karachi mein",
    "find offices near me Islamabad Lahore and Karachi",
])
def test_near_me_with_explicit_city(service, query):
    result = lookup_service_centers(service, query)
    assert result.status == "found"
    assert any("karachi" in str(record).casefold() for record in result.centers)
    assert not result.missing_locations


@pytest.mark.parametrize("service", ["passport", "driving_license"])
@pytest.mark.parametrize("cities", ["Islamabad Lahore and karachi", "Islamabad, Lahore, Karachi", "Islamabad aur Lahore aur Karachi me"])
def test_multiple_cities_are_each_looked_up(service, cities):
    result = lookup_service_centers(service, f"find me offices near {cities}")
    assert result.status == "found"
    for city in ("Islamabad", "Lahore", "Karachi"):
        assert any(city.casefold() in str(record).casefold() for record in result.centers)
    assert not result.missing_locations


def test_multiple_cities_report_missing_city_without_hiding_results():
    result = _invoke("find passport offices near Karachi and Atlantis", "passport")
    assert "Karachi-I (South)" in result["response"]
    assert "couldn't find a passport service center for Atlantis" in result["response"]
    assert result["sources"]


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


@pytest.mark.parametrize("query", [
    "find me passports offices near karachi me",
    "find me passports offices near karachi mein",
    "find me passports offices near karachi main",
    "karachi me passport office kahan hai?",
    "Karachi mein passport office kahan hai?",
    "find me passport offices karachi mein",
])
def test_mixed_language_karachi_location(query):
    result = _invoke(query, "passport")
    assert "Karachi-I (South)" in result["response"]
    assert result["sources"]


def test_unknown_mixed_language_location_is_not_replaced():
    result = _invoke("find me passport offices near Atlantis me", "passport")
    assert "couldn't find" in result["response"]
    assert "Atlantis" in result["response"]
    assert not result["sources"]


def test_driving_license_center_in_represented_city():
    result = _invoke("Where can I get a driving license in Attock?", "driving_license")

    assert "Attock Driving Licensing Branch" in result["response"]
    assert "0579-316006" in result["response"]
    assert "High" in result["response"]


def test_driving_license_lahore_does_not_substitute_another_city():
    result = _invoke("Where can I get a driving license in Lahore?", "driving_license")

    assert "CTPL Licensing Center, Manawan" in result["response"]
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
