"""Deterministic Appointment Simulator and Action integration tests."""

from unittest.mock import patch

from langgraph.checkpoint.memory import InMemorySaver

from backend.agents.action import action_agent
from backend.agents.planner import PlannerOutput
from backend.graph.graph import build_graph
from backend.services.appointment_simulator import book_slot, check_slots


def test_check_slots_with_known_office():
    result = action_agent(
        {
            "user_input": "Show available appointments for this office.",
            "intent": "check_slots",
            "service_type": "passport",
            "selected_office": "Karachi-I (South)",
        }
    )

    assert "Simulated prototype availability" in result["response"]
    assert "10:00" in result["response"]
    assert "not live government availability" in result["response"]
    assert result["appointment_date"] == "2026-09-15"


def test_check_slots_without_office_or_location_asks_for_location():
    result = action_agent(
        {
            "user_input": "Show available passport appointments.",
            "intent": "check_slots",
            "service_type": "passport",
        }
    )

    assert "Which city or region" in result["response"]
    assert result["pending_clarification"] == "location"


def test_check_slots_with_multiple_offices_asks_for_selection():
    result = action_agent(
        {
            "user_input": "Show passport appointments in Karachi.",
            "intent": "check_slots",
            "service_type": "passport",
        }
    )

    assert "Several matching offices" in result["response"]
    assert "1. Karachi-I (South)" in result["response"]
    assert result["pending_clarification"] == "office"
    assert len(result["office_options"]) > 1


def test_book_valid_slot_returns_simulated_confirmation():
    result = action_agent(
        {
            "user_input": "Book the 10:00 slot.",
            "intent": "book_slot",
            "service_type": "passport",
            "selected_office": "Karachi-I (South)",
            "booked_slots": [],
        }
    )

    assert "Simulated booking confirmed" in result["response"]
    assert "No real government appointment was created" in result["response"]
    assert result["booked_slots"]


def test_book_nonexistent_slot_fails_clearly():
    result = action_agent(
        {
            "user_input": "Book the 16:45 slot.",
            "intent": "book_slot",
            "service_type": "passport",
            "selected_office": "Karachi-I (South)",
            "booked_slots": [],
        }
    )

    assert "does not exist" in result["response"]
    assert result["booked_slots"] == []


def test_double_booking_is_prevented():
    first = book_slot(
        "passport", "Karachi-I (South)", "Book 10 AM", booked_slots=[]
    )
    second = book_slot(
        "passport",
        "Karachi-I (South)",
        "Book 10 AM",
        booked_slots=[first.booked_slot_key],
    )

    assert first.status == "booked"
    assert second.status == "unavailable"
    availability = check_slots(
        "passport", "Karachi-I (South)", [first.booked_slot_key]
    )
    assert "10:00" not in availability.slots


@patch("backend.graph.graph.run_planner")
def test_multi_turn_center_slots_and_booking_flow(mock_planner):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="service_center_lookup",
            service_type="passport",
            next_step="action",
        ),
        PlannerOutput(
            intent="check_slots", service_type="unknown", next_step="appointment"
        ),
        PlannerOutput(
            intent="book_slot", service_type="unknown", next_step="appointment"
        ),
        PlannerOutput(
            intent="book_slot", service_type="unknown", next_step="appointment"
        ),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "appointment-flow"}}

    centers = graph.invoke(
        {"user_input": "Find a passport office in Karachi."}, config=config
    )
    slots = graph.invoke(
        {"user_input": "Show appointments for the first one."}, config=config
    )
    booked = graph.invoke({"user_input": "Book the 10:00 slot."}, config=config)
    duplicate = graph.invoke(
        {"user_input": "Book the 10:00 slot again."}, config=config
    )

    assert centers["office_options"][0] == "Karachi-I (South)"
    assert slots["selected_office"] == "Karachi-I (South)"
    assert "Available demo slots" in slots["response"]
    assert "Simulated booking confirmed" in booked["response"]
    assert "already unavailable or booked" in duplicate["response"]


@patch("backend.graph.graph.run_planner")
def test_existing_service_center_lookup_remains_functional(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="service_center_lookup",
        service_type="passport",
        next_step="action",
    )

    result = build_graph().invoke(
        {"user_input": "Find a passport office in Karachi."}
    )

    assert "Karachi-I (South)" in result["response"]


@patch("backend.graph.graph.knowledge_agent", return_value={"response": "RAG response"})
@patch("backend.graph.graph.run_planner")
def test_existing_knowledge_route_remains_functional(mock_planner, mock_knowledge):
    mock_planner.return_value = PlannerOutput(
        intent="general_information",
        service_type="passport",
        next_step="knowledge",
    )

    result = build_graph().invoke(
        {"user_input": "How long is a passport valid?"}
    )

    assert result["response"] == "RAG response"
    mock_knowledge.assert_called_once()


@patch("backend.graph.graph.knowledge_agent", return_value={"response": "Checklist"})
@patch("backend.graph.graph.run_planner")
def test_existing_checklist_route_remains_on_knowledge(mock_planner, mock_knowledge):
    mock_planner.return_value = PlannerOutput(
        intent="requirements_checklist",
        service_type="passport",
        next_step="knowledge",
    )

    result = build_graph().invoke(
        {"user_input": "What documents do I need for a passport?"}
    )

    assert result["response"] == "Checklist"
    mock_knowledge.assert_called_once()


@patch("backend.graph.graph.run_planner")
def test_existing_location_clarification_continuation_remains_functional(
    mock_planner,
):
    mock_planner.return_value = PlannerOutput(
        intent="service_center_lookup",
        service_type="passport",
        next_step="action",
    )
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "existing-location-flow"}}

    first = graph.invoke(
        {"user_input": "Find the nearest passport office."}, config=config
    )
    second = graph.invoke({"user_input": "Karachi"}, config=config)

    assert "Which city or region" in first["response"]
    assert "Karachi-I (South)" in second["response"]
