"""Exact follow-up regressions using the persisted KB and real retrieval.

Only planning and answer generation are mocked; these tests must exercise the
indexed metadata, similarity threshold, trusted filters, and session context.
"""

from unittest.mock import patch

from langgraph.checkpoint.memory import InMemorySaver

from backend.agents.planner import PlannerOutput
from backend.graph.graph import build_graph
from backend.services.language import message


def _assert_sources(result, service, section_term, confidence):
    assert result["sources"]
    for source in result["sources"]:
        assert source["origin"] == "knowledge_base"
        assert source["service"] == service
        assert section_term in source["section"].casefold()
        assert source["confidence"] == confidence
        assert source["source_url"].startswith("https://")


@patch("backend.agents.knowledge._call_gemini")
@patch("backend.graph.graph.run_planner")
def test_driving_license_renewal_followups_use_real_trusted_kb(planner, generate):
    planner.side_effect = [
        PlannerOutput(
            intent="renew_service",
            service_type="driving_license",
            next_step="action",
        ),
        PlannerOutput(
            intent="requirements_checklist",
            service_type="unknown",
            next_step="knowledge",
        ),
        PlannerOutput(
            intent="fee_lookup", service_type="unknown", next_step="knowledge"
        ),
    ]
    generate.return_value = (
        "Original CNIC aur photocopy chahiye. "
        "Province-specific documents ki list confirm karein."
    )
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "real-kb-driving-renewal"}}

    journey = graph.invoke(
        {"user_input": "I need to renew my driving licence."}, config=config
    )
    assert journey["service_type"] == "driving_license"
    assert journey["intent"] == "service_journey"
    assert journey["journeys"]["driving_license"] == {}
    generate.assert_not_called()

    checklist = graph.invoke(
        {"user_input": "documents kya chahiye?"}, config=config
    )
    assert checklist["service_type"] == "driving_license"
    assert checklist["response"] == generate.return_value
    _assert_sources(checklist, "driving_license", "required document", "medium")
    generate.assert_called_once()
    context = generate.call_args.args[1]
    assert "Original CNIC + photocopy" in context
    assert "confirm province-specific list" in context
    assert "confidence=medium" in context
    assert checklist["journeys"]["driving_license"]["requirements"] == "reviewed"

    fee = graph.invoke({"user_input": "fee kitni hai?"}, config=config)
    assert fee["service_type"] == "driving_license"
    assert fee["response"] == message("fee_not_found", "roman_urdu")
    _assert_sources(fee, "driving_license", "fee", "medium")
    # The actual KB contains only unverified driving licence fee ranges. Finding
    # the right service must not make those ranges trusted or invoke generation.
    generate.assert_called_once()
    assert "fees" not in fee["journeys"]["driving_license"]


@patch("backend.agents.knowledge._call_gemini")
@patch("backend.graph.graph.run_planner")
def test_passport_documents_and_fee_use_real_trusted_kb(planner, generate):
    planner.side_effect = [
        PlannerOutput(
            intent="requirements_checklist",
            service_type="passport",
            next_step="knowledge",
        ),
        PlannerOutput(
            intent="fee_lookup", service_type="passport", next_step="knowledge"
        ),
    ]
    answers = [
        "Bring your original valid CNIC or NICOP and one photocopy.",
        "Passport fee type, pages, validity aur urgency par depend karti hai.",
    ]
    generate.side_effect = answers
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "real-kb-passport"}}

    checklist = graph.invoke(
        {"user_input": "What documents do I need for a passport?"}, config=config
    )
    assert checklist["response"] == answers[0]
    _assert_sources(checklist, "passport", "required document", "high")
    assert "Original valid CNIC or NICOP" in generate.call_args.args[1]

    fee = graph.invoke({"user_input": "passport fee kitni hai?"}, config=config)
    assert fee["service_type"] == "passport"
    assert fee["response"] == answers[1]
    _assert_sources(fee, "passport", "fee", "high")
    assert generate.call_count == 2
    fee_context = generate.call_args.args[1]
    assert "confidence=high" in fee_context
    assert "Rs." in fee_context
    assert "driving_license" not in fee_context
    assert fee["journeys"]["passport"] == {
        "requirements": "reviewed",
        "fees": "reviewed",
    }
