"""Grounded checklist and fee lookup tests."""

from unittest.mock import patch

from langgraph.checkpoint.memory import InMemorySaver

from backend.agents.knowledge import _GENERATION_SYSTEM_PROMPT, knowledge_agent
from backend.agents.planner import PlannerOutput
from backend.graph.graph import build_graph
from backend.rag.retriever import RetrievedChunk
from backend.services.checklist_builder import CHECKLIST_SYSTEM_PROMPT
from backend.services.fee_lookup import FEE_NOT_FOUND_MESSAGE, FEE_SYSTEM_PROMPT


def _chunk(
    text: str,
    service: str,
    section: str,
    confidence: str,
) -> RetrievedChunk:
    return RetrievedChunk(
        text=text,
        metadata={
            "service": service,
            "section": section,
            "confidence": confidence,
            "source_url": f"https://official.example/{service}",
            "document_type": "knowledge_base",
        },
        score=0.9,
        origin="knowledge_base",
    )


def _run_knowledge(query, service, intent, chunks, answer):
    with (
        patch("backend.agents.knowledge._get_retriever") as get_retriever,
        patch("backend.agents.knowledge._call_gemini", return_value=answer) as generate,
    ):
        get_retriever.return_value.retrieve.return_value = chunks
        result = knowledge_agent(
            {"user_input": query, "service_type": service, "intent": intent}
        )
    return result, get_retriever.return_value, generate


def test_passport_requirements_use_grounded_checklist():
    requirement = _chunk(
        "Required Documents\n- Original valid identity document.",
        "passport",
        "3. Required Documents",
        "high",
    )
    result, retriever, generate = _run_knowledge(
        "What documents do I need for a passport?",
        "passport",
        "requirements_checklist",
        [requirement],
        "Required documents:\n☐ Original valid identity document.",
    )

    assert result["response"].startswith("Required documents:")
    assert "☐" in result["response"]
    assert result["sources"][0]["section"] == "3. Required Documents"
    assert "required documents" in retriever.retrieve.call_args.args[0]
    assert generate.call_args.kwargs["system_prompt"] == CHECKLIST_SYSTEM_PROMPT


def test_explicit_passport_checklist_is_grounded():
    requirement = _chunk(
        "Required Documents\n- Fee payment receipt.",
        "passport",
        "3. Required Documents",
        "high",
    )
    result, _, generate = _run_knowledge(
        "Give me a checklist for applying for a passport.",
        "passport",
        "requirements_checklist",
        [requirement],
        "Required documents:\n☐ Fee payment receipt.",
    )

    assert "☐ Fee payment receipt" in result["response"]
    assert "Fee payment receipt" in generate.call_args.args[1]


def test_driving_license_requirements_preserve_uncertainty():
    requirement = _chunk(
        "Required Documents (typical, confirm province-specific list)\n- Original CNIC.",
        "driving_license",
        "4. Required Documents (typical, confirm province-specific list)",
        "medium",
    )
    result, _, _ = _run_knowledge(
        "What should I take for my driving license?",
        "driving_license",
        "requirements_checklist",
        [requirement],
        "Required documents:\n☐ Original CNIC.\nConfirm the list for your province.",
    )

    assert "☐ Original CNIC" in result["response"]
    assert "Confirm" in result["response"]
    assert result["sources"][0]["confidence"] == "medium"


def test_passport_fee_uses_high_confidence_fee_context():
    fee = _chunk(
        "Fees\nMRP and e-Passport tables with distinct categories.",
        "passport",
        "7. Fees",
        "high",
    )
    result, retriever, generate = _run_knowledge(
        "How much does a passport cost?",
        "passport",
        "fee_lookup",
        [fee],
        "Passport fees vary by type, pages, validity, and urgency.",
    )

    assert "vary by type" in result["response"]
    assert result["sources"][0]["section"] == "7. Fees"
    assert "fee schedule" in retriever.retrieve.call_args.args[0]
    assert generate.call_args.kwargs["system_prompt"] == FEE_SYSTEM_PROMPT


def test_unverified_driving_license_fee_returns_not_found():
    fee = _chunk(
        "Fees — Handle With Care\nIndicative unverified ranges only.",
        "driving_license",
        "5. Fees — Handle With Care",
        "medium",
    )

    with (
        patch("backend.agents.knowledge._get_retriever") as get_retriever,
        patch("backend.agents.knowledge._call_gemini") as generate,
    ):
        get_retriever.return_value.retrieve.return_value = [fee]
        result = knowledge_agent(
            {
                "user_input": "How much is a driving license?",
                "service_type": "driving_license",
                "intent": "fee_lookup",
            }
        )

    assert result["response"] == FEE_NOT_FOUND_MESSAGE
    assert result["sources"][0]["section"] == "5. Fees — Handle With Care"
    generate.assert_not_called()


def test_normal_knowledge_query_keeps_normal_generation():
    validity = _chunk(
        "Validity\nPassport validity depends on the selected term.",
        "passport",
        "6. Validity",
        "high",
    )
    result, _, generate = _run_knowledge(
        "How long is a passport valid?",
        "passport",
        "general_information",
        [validity],
        "The available validity terms are described in the source.",
    )

    assert result["response"].startswith("The available validity")
    assert generate.call_args.kwargs["system_prompt"] == _GENERATION_SYSTEM_PROMPT


@patch("backend.graph.graph.run_planner")
def test_existing_service_center_action_still_works(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="service_center_lookup",
        service_type="passport",
        next_step="action",
    )

    result = build_graph().invoke(
        {"user_input": "Find a passport office in Karachi."}
    )

    assert "Karachi-I (South)" in result["response"]


@patch("backend.agents.knowledge._call_gemini")
@patch("backend.agents.knowledge._get_retriever")
@patch("backend.graph.graph.run_planner")
def test_contextual_fee_follow_up_reuses_service(
    mock_planner, get_retriever, generate
):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="requirements_checklist",
            service_type="passport",
            next_step="knowledge",
        ),
        PlannerOutput(intent="fee_lookup", service_type="unknown", next_step="knowledge"),
    ]
    requirement = _chunk(
        "Required Documents\n- Identity document.",
        "passport",
        "3. Required Documents",
        "high",
    )
    fee = _chunk("Fees\nVerified fee table.", "passport", "7. Fees", "high")
    get_retriever.return_value.retrieve.side_effect = [[requirement], [fee]]
    generate.side_effect = [
        "Required documents:\n☐ Identity document.",
        "Passport fee categories from the verified table.",
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "fee-follow-up"}}

    first = graph.invoke(
        {"user_input": "What documents do I need for a passport?"}, config=config
    )
    second = graph.invoke({"user_input": "How much does it cost?"}, config=config)

    assert "☐" in first["response"]
    assert second["service_type"] == "passport"
    assert second["response"].startswith("Passport fee categories")


@patch("backend.graph.graph.run_planner")
def test_location_clarification_continuation_remains_functional(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="service_center_lookup",
        service_type="passport",
        next_step="action",
    )
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "location-continuation"}}

    first = graph.invoke(
        {"user_input": "Find the nearest passport office."}, config=config
    )
    second = graph.invoke({"user_input": "Karachi"}, config=config)

    assert "Which city or region" in first["response"]
    assert "Karachi-I (South)" in second["response"]

