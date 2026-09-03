"""Citizen assistance journey tracking tests."""

from unittest.mock import patch

from langgraph.checkpoint.memory import InMemorySaver

from backend.agents.action import action_agent
from backend.agents.knowledge import knowledge_agent
from backend.agents.planner import PlannerOutput
from backend.graph.graph import build_graph
from backend.rag.retriever import RetrievedChunk
from backend.services.fee_lookup import FEE_NOT_FOUND_MESSAGE
from backend.services.journey import journey_summary, update_journey


def _chunk(text: str, section: str, confidence: str = "high") -> RetrievedChunk:
    return RetrievedChunk(
        text=text,
        metadata={
            "service": "passport",
            "section": section,
            "confidence": confidence,
            "source_url": "https://official.example/passport",
            "document_type": "knowledge_base",
        },
        score=0.9,
        origin="knowledge_base",
    )


@patch("backend.agents.knowledge._call_gemini", return_value="Checklist delivered")
@patch("backend.agents.knowledge._get_retriever")
def test_successful_requirements_marks_reviewed(get_retriever, _generate):
    get_retriever.return_value.retrieve.return_value = [
        _chunk("Required Documents\n- Original CNIC", "3. Required Documents")
    ]

    result = knowledge_agent(
        {
            "user_input": "What documents do I need for a passport?",
            "intent": "requirements_checklist",
            "service_type": "passport",
        }
    )

    assert result["journeys"]["passport"]["requirements"] == "reviewed"


@patch("backend.agents.knowledge._call_gemini", return_value="Verified fees")
@patch("backend.agents.knowledge._get_retriever")
def test_successful_fee_marks_reviewed(get_retriever, _generate):
    get_retriever.return_value.retrieve.return_value = [
        _chunk("Fees\nVerified fee table", "7. Fees")
    ]

    result = knowledge_agent(
        {
            "user_input": "How much does a passport cost?",
            "intent": "fee_lookup",
            "service_type": "passport",
        }
    )

    assert result["journeys"]["passport"]["fees"] == "reviewed"


def test_successful_center_lookup_marks_assistance():
    result = action_agent(
        {
            "user_input": "Find passport offices in Karachi.",
            "intent": "service_center_lookup",
            "service_type": "passport",
        }
    )

    assert result["journeys"]["passport"]["service_center"] == "located"


def test_availability_and_demo_booking_have_distinct_progress():
    checked = action_agent(
        {
            "user_input": "Show appointments.",
            "intent": "check_slots",
            "service_type": "passport",
            "selected_office": "Karachi-I (South)",
        }
    )
    booked = action_agent(
        {
            "user_input": "Book the 10:00 slot.",
            "intent": "book_slot",
            "service_type": "passport",
            "selected_office": "Karachi-I (South)",
            "journeys": checked["journeys"],
        }
    )

    assert checked["journeys"]["passport"]["appointment"] == "availability_checked"
    assert "demo_booked" not in checked["journeys"]["passport"].values()
    assert booked["journeys"]["passport"]["appointment"] == "demo_booked"


@patch("backend.agents.knowledge._call_gemini")
@patch("backend.agents.knowledge._get_retriever")
def test_failed_operations_do_not_advance_progress(get_retriever, generate):
    get_retriever.return_value.retrieve.return_value = [
        _chunk("Fees - unverified ranges", "5. Fees", confidence="medium")
    ]
    fee = knowledge_agent(
        {
            "user_input": "How much does a passport cost?",
            "intent": "fee_lookup",
            "service_type": "passport",
        }
    )
    booking = action_agent(
        {
            "user_input": "Book the 16:45 slot.",
            "intent": "book_slot",
            "service_type": "passport",
            "selected_office": "Karachi-I (South)",
        }
    )

    assert fee["response"] == FEE_NOT_FOUND_MESSAGE
    assert not fee.get("journeys")
    assert not booking.get("journeys")
    generate.assert_not_called()


def test_journey_summary_reports_assistance_not_real_completion():
    state = {
        "service_type": "passport",
        "journeys": {
            "passport": {
                "requirements": "reviewed",
                "fees": "reviewed",
                "service_center": "selected",
                "appointment": "demo_booked",
            }
        },
    }

    response = journey_summary(state)

    assert "Requirements reviewed" in response
    assert "Fee information reviewed" in response
    assert "Service center selected" in response
    assert "Demo appointment booked" in response
    assert "not verified government completion" in response


def test_whats_left_identifies_incomplete_steps():
    response = action_agent(
        {
            "user_input": "What's left?",
            "intent": "journey_summary",
            "service_type": "passport",
            "journeys": {"passport": {"requirements": "reviewed"}},
        }
    )["response"]

    assert "Requirements reviewed" in response
    assert "Fee information not reviewed yet" in response
    assert "Service center not located yet" in response
    assert "Demo appointment not booked yet" in response


def test_service_journeys_remain_separate():
    state = {"service_type": "passport"}
    passport = update_journey(state, "requirements", "reviewed")
    switched = {"service_type": "driving_license", "journeys": passport}
    journeys = update_journey(switched, "service_center", "located")

    assert journeys["passport"] == {"requirements": "reviewed"}
    assert journeys["driving_license"] == {"service_center": "located"}


@patch("backend.graph.graph.run_planner")
def test_journey_state_is_isolated_between_threads(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="journey_summary", service_type="passport", next_step="action"
    )
    graph = build_graph(checkpointer=InMemorySaver())

    populated = graph.invoke(
        {
            "user_input": "Show my progress.",
            "journeys": {"passport": {"requirements": "reviewed"}},
        },
        config={"configurable": {"thread_id": "journey-one"}},
    )
    fresh = graph.invoke(
        {"user_input": "Show my progress."},
        config={"configurable": {"thread_id": "journey-two"}},
    )

    assert "✓ Requirements reviewed" in populated["response"]
    assert "○ Requirements not reviewed yet" in fresh["response"]


@patch("backend.graph.graph.run_planner")
def test_contextual_progress_summary_reuses_active_service(mock_planner):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="service_center_lookup", service_type="passport", next_step="action"
        ),
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "journey-summary"}}

    graph.invoke({"user_input": "Find passport offices in Karachi."}, config=config)
    summary = graph.invoke(
        {"user_input": "What have we done so far?"}, config=config
    )

    assert summary["intent"] == "journey_summary"
    assert summary["service_type"] == "passport"
    assert "Service centers located" in summary["response"]


@patch("backend.graph.graph.run_planner")
def test_broad_passport_goal_starts_empty_supported_journey(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="apply_for_service", service_type="passport", next_step="action"
    )

    result = build_graph().invoke(
        {"user_input": "I want to apply for a passport."}
    )

    assert "required documents" in result["response"]
    assert "unsupported" not in result["response"].casefold()
    assert result["intent"] == "service_journey"
    assert result["service_type"] == "passport"
    assert result["journeys"]["passport"] == {}


@patch("backend.graph.graph.run_planner")
def test_broad_driving_license_goal_gets_supported_orientation(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="apply_for_service", service_type="driving_license", next_step="action"
    )

    result = build_graph().invoke(
        {"user_input": "I need to get a driving license."}
    )

    assert "driving license process" in result["response"]
    assert result["journeys"]["driving_license"] == {}


@patch("backend.agents.knowledge._call_gemini", return_value="Checklist delivered")
@patch("backend.agents.knowledge._get_retriever")
@patch("backend.graph.graph.run_planner")
def test_broad_goal_then_contextual_checklist(
    mock_planner, get_retriever, _generate
):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="apply_for_service", service_type="passport", next_step="action"
        ),
        PlannerOutput(
            intent="requirements_checklist",
            service_type="unknown",
            next_step="knowledge",
        ),
    ]
    get_retriever.return_value.retrieve.return_value = [
        _chunk("Required Documents\n- Original CNIC", "3. Required Documents")
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "broad-checklist"}}

    graph.invoke({"user_input": "I want to apply for a passport."}, config=config)
    checklist = graph.invoke(
        {"user_input": "What documents do I need?"}, config=config
    )

    assert checklist["service_type"] == "passport"
    assert checklist["response"] == "Checklist delivered"
    assert checklist["journeys"]["passport"]["requirements"] == "reviewed"


@patch("backend.agents.knowledge._call_gemini", return_value="Verified fees")
@patch("backend.agents.knowledge._get_retriever")
@patch("backend.graph.graph.run_planner")
def test_broad_goal_then_contextual_fee(mock_planner, get_retriever, _generate):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="apply_for_service", service_type="passport", next_step="action"
        ),
        PlannerOutput(intent="fee_lookup", service_type="unknown", next_step="knowledge"),
    ]
    get_retriever.return_value.retrieve.return_value = [
        _chunk("Fees\nVerified fee table", "7. Fees")
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "broad-fee"}}

    graph.invoke({"user_input": "Help me with my passport application."}, config=config)
    fee = graph.invoke({"user_input": "How much does it cost?"}, config=config)

    assert fee["service_type"] == "passport"
    assert fee["response"] == "Verified fees"
    assert fee["journeys"]["passport"]["fees"] == "reviewed"


@patch("backend.graph.graph.run_planner")
def test_concrete_actions_keep_action_routing(mock_planner):
    cases = (
        (
            PlannerOutput(
                intent="service_center_lookup",
                service_type="passport",
                next_step="action",
            ),
            {"user_input": "Find a passport office in Karachi."},
            "Karachi-I (South)",
        ),
        (
            PlannerOutput(intent="check_slots", service_type="passport", next_step="action"),
            {
                "user_input": "Show available appointments.",
                "selected_office": "Karachi-I (South)",
            },
            "Available demo slots",
        ),
        (
            PlannerOutput(intent="book_slot", service_type="passport", next_step="action"),
            {
                "user_input": "Book the 10:00 slot.",
                "selected_office": "Karachi-I (South)",
            },
            "Simulated booking confirmed",
        ),
    )

    for planner_output, state, expected in cases:
        mock_planner.return_value = planner_output
        result = build_graph().invoke(state)
        assert result["next_step"] == "action"
        assert expected in result["response"]


@patch("backend.graph.graph.run_planner")
def test_broad_goal_for_unknown_service_clarifies(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="apply_for_service", service_type="unknown", next_step="action"
    )

    result = build_graph().invoke(
        {"user_input": "Help me apply for an unsupported service."}
    )

    assert result["response"] == "Please clarify which government service you need."
    assert not result.get("journeys")
