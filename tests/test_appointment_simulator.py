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
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
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
    refreshed = graph.invoke(
        {"user_input": "Show appointments again."}, config=config
    )

    assert centers["office_options"][0] == "Karachi-I (South)"
    assert slots["selected_office"] == "Karachi-I (South)"
    assert "Available demo slots" in slots["response"]
    assert "Simulated booking confirmed" in booked["response"]
    assert refreshed["service_type"] == "passport"
    assert refreshed["selected_office"] == "Karachi-I (South)"
    assert "10:00" not in refreshed["response"]


@patch("backend.graph.graph.run_planner")
def test_contextual_slots_preserve_service_and_office_options(mock_planner):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="service_center_lookup",
            service_type="passport",
            next_step="action",
        ),
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "contextual-slots"}}

    centers = graph.invoke(
        {"user_input": "Find a passport office in Karachi."}, config=config
    )
    slots = graph.invoke(
        {"user_input": "Show appointments for the first one."}, config=config
    )

    assert len(centers["office_options"]) > 1
    assert slots["service_type"] == "passport"
    assert slots["selected_office"] == centers["office_options"][0]
    assert "Available demo slots" in slots["response"]


@patch("backend.graph.graph.run_planner")
def test_bare_office_choice_uses_retained_options(mock_planner):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="service_center_lookup",
            service_type="passport",
            next_step="action",
        ),
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "bare-office-choice"}}

    centers = graph.invoke(
        {"user_input": "Find a passport office in Karachi."}, config=config
    )
    slots = graph.invoke({"user_input": "first"}, config=config)

    assert slots["service_type"] == "passport"
    assert slots["selected_office"] == centers["office_options"][0]
    assert "Available demo slots" in slots["response"]


@patch("backend.graph.graph.run_planner")
def test_contextual_slots_without_choice_preserve_service(mock_planner):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="service_center_lookup",
            service_type="passport",
            next_step="action",
        ),
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "slots-need-office"}}

    graph.invoke(
        {"user_input": "Find a passport office in Karachi."}, config=config
    )
    selection = graph.invoke({"user_input": "Show appointments."}, config=config)

    assert selection["service_type"] == "passport"
    assert selection["pending_clarification"] == "office"
    assert "Several matching offices" in selection["response"]


@patch("backend.graph.graph.run_planner")
def test_explicit_service_switch_replaces_previous_context(mock_planner):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="service_center_lookup",
            service_type="passport",
            next_step="action",
        ),
        PlannerOutput(
            intent="service_center_lookup",
            service_type="driving_license",
            next_step="action",
        ),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "service-switch"}}

    graph.invoke({"user_input": "Find a passport office in Karachi."}, config=config)
    switched = graph.invoke(
        {"user_input": "Now find a driving license center in Attock."}, config=config
    )

    assert switched["service_type"] == "driving_license"
    assert switched["office_options"] == ["Attock Driving Licensing Branch"]


@patch("backend.graph.graph.run_planner")
def test_appointment_context_is_isolated_between_threads(mock_planner):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="service_center_lookup",
            service_type="passport",
            next_step="action",
        ),
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
    ]
    graph = build_graph(checkpointer=InMemorySaver())

    graph.invoke(
        {"user_input": "Find a passport office in Karachi."},
        config={"configurable": {"thread_id": "populated"}},
    )
    isolated = graph.invoke(
        {"user_input": "Show appointments for the first one."},
        config={"configurable": {"thread_id": "isolated"}},
    )

    assert isolated["response"] == "Please clarify which government service you need."
    assert not isolated.get("office_options")


@patch("backend.graph.graph.run_planner")
def test_explicit_location_replaces_options_after_clarification(mock_planner):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="service_center_lookup",
            service_type="passport",
            next_step="action",
        ),
        PlannerOutput(intent="check_slots", service_type="passport", next_step="action"),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "location-override"}}

    missing = graph.invoke({"user_input": "Find a passport office."}, config=config)
    lahore = graph.invoke({"user_input": "Lahore"}, config=config)
    karachi = graph.invoke(
        {"user_input": "Show me passport appointments in Karachi."}, config=config
    )

    assert missing["pending_clarification"] == "location"
    assert all("Lahore" in office for office in lahore["office_options"])
    assert karachi["pending_clarification"] == "office"
    assert karachi["selected_office"] is None
    assert karachi["appointment_date"] is None
    assert all("Karachi" in office for office in karachi["office_options"])
    assert "Lahore" not in karachi["response"]


@patch("backend.graph.graph.run_planner")
def test_direct_location_replacement_replaces_office_options(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="service_center_lookup", service_type="passport", next_step="action"
    )
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "direct-location-replacement"}}

    graph.invoke({"user_input": "Find passport offices in Lahore."}, config=config)
    karachi = graph.invoke(
        {"user_input": "Find passport offices in Karachi."}, config=config
    )

    assert all("Karachi" in office for office in karachi["office_options"])
    assert not any("Lahore" in office for office in karachi["office_options"])


def test_valid_fifth_office_reference_is_resolved():
    options = [f"Office {number}" for number in range(1, 6)]
    result = action_agent(
        {
            "user_input": "Show appointments for the fifth one.",
            "intent": "check_slots",
            "service_type": "passport",
            "office_options": options,
        }
    )

    assert result["selected_office"] == "Office 5"
    assert "Office 5" in result["response"]


def test_invalid_ordinal_does_not_fall_back_to_selected_office():
    options = [f"Office {number}" for number in range(1, 6)]
    result = action_agent(
        {
            "user_input": "and for the sixth one?",
            "intent": "check_slots",
            "service_type": "passport",
            "office_options": options,
            "selected_office": "Office 5",
        }
    )

    assert result["response"] == (
        "There are only 5 matching offices. Please choose an office from 1 to 5."
    )
    assert "selected_office" not in result


def test_invalid_numeric_reference_is_rejected():
    options = [f"Office {number}" for number in range(1, 6)]
    result = action_agent(
        {
            "user_input": "Show appointments for 6.",
            "intent": "check_slots",
            "service_type": "passport",
            "office_options": options,
            "selected_office": "Office 5",
        }
    )

    assert "only 5 matching offices" in result["response"]
    assert "selected_office" not in result


def test_explicit_office_reference_replaces_previous_selection():
    options = [
        "Karachi-I (South)",
        "Karachi-II (Central)",
        "Karachi-III (West)",
    ]
    result = action_agent(
        {
            "user_input": "Show appointments for the second one.",
            "intent": "check_slots",
            "service_type": "passport",
            "office_options": options,
            "selected_office": options[0],
        }
    )

    assert result["selected_office"] == options[1]
    assert options[1] in result["response"]


@patch("backend.graph.graph.run_planner")
def test_invalid_ordinal_after_valid_selection_is_rejected(mock_planner):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="service_center_lookup", service_type="passport", next_step="action"
        ),
        PlannerOutput(intent="check_slots", service_type="unknown", next_step="action"),
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "invalid-after-valid"}}

    graph.invoke({"user_input": "Find passport offices in Karachi."}, config=config)
    fifth = graph.invoke(
        {"user_input": "Show appointments for the fifth one."}, config=config
    )
    invalid = graph.invoke({"user_input": "and for the sixth one?"}, config=config)

    assert fifth["selected_office"] == "Karachi-V (Awami Markaz)"
    assert "only 5 matching offices" in invalid["response"]
    assert "No demo appointment schedule" not in invalid["response"]


@patch("backend.graph.graph.run_planner")
def test_explicit_location_invalidates_previous_selection(mock_planner):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="service_center_lookup", service_type="passport", next_step="action"
        ),
        PlannerOutput(intent="check_slots", service_type="unknown", next_step="action"),
        PlannerOutput(intent="check_slots", service_type="passport", next_step="action"),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "selection-invalidation"}}

    graph.invoke({"user_input": "Find passport offices in Lahore."}, config=config)
    graph.invoke({"user_input": "Show appointments for the first one."}, config=config)
    karachi = graph.invoke(
        {"user_input": "Show passport appointments in Karachi."}, config=config
    )

    assert karachi["selected_office"] is None
    assert all("Karachi" in office for office in karachi["office_options"])


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
