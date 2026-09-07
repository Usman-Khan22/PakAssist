"""Multilingual presentation, simple-language, and selective verification tests."""

from unittest.mock import patch

import numpy as np
import pytest
from langgraph.checkpoint.memory import InMemorySaver

from backend.agents.action import action_agent
from backend.agents.knowledge import knowledge_agent
from backend.agents.planner import PlannerOutput
from backend.graph.graph import build_graph
from backend.rag.loader import RagDocument
from backend.rag.retriever import RetrievedChunk
from backend.rag.retriever import Retriever
from backend.rag.vector_store import FaissVectorStore
from backend.services.appointment_simulator import AppointmentResult
from backend.services.journey import update_journey
from backend.services.language import detect_language, is_simple_language_request
from backend.services.verification import (
    verify_document_answer,
    verify_fee_sources,
    verify_requirement_sources,
)


def _chunk(
    text: str,
    *,
    origin: str = "knowledge_base",
    service: str = "passport",
    section: str = "General",
    confidence: str = "high",
) -> RetrievedChunk:
    return RetrievedChunk(
        text=text,
        metadata={
            "service": service,
            "section": section,
            "confidence": confidence,
        },
        score=0.9,
        origin=origin,
    )


def _fake_grounded_knowledge(state, *, thread_id=None):
    intent = state["intent"]
    step = "requirements" if intent == "requirements_checklist" else "fees"
    response = "Grounded checklist" if step == "requirements" else "Grounded fee"
    return {
        "response": response,
        "sources": [
            {
                "label": "Trusted source",
                "origin": "knowledge_base",
                "service": state["service_type"],
                "section": step,
                "source_url": "https://example.gov.pk",
                "confidence": "high",
            }
        ],
        "journeys": update_journey(state, step, "reviewed"),
    }


def _invoke_turns(graph, config, turns):
    return [graph.invoke({"user_input": turn}, config=config) for turn in turns]


@pytest.mark.parametrize(
    ("text", "previous", "expected"),
    [
        ("I want to apply for a passport.", None, "english"),
        ("Mujhe passport banwana hai.", None, "roman_urdu"),
        ("مجھے پاسپورٹ بنوانا ہے۔", None, "urdu"),
        ("Karachi", "roman_urdu", "roman_urdu"),
        ("Explain this in English.", "urdu", "english"),
    ],
)
def test_language_detection_and_short_turn_persistence(text, previous, expected):
    assert detect_language(text, previous) == expected


@pytest.mark.parametrize(
    ("query", "language", "expected_text"),
    [
        ("I want to apply for a passport.", "english", "I can guide you"),
        ("Mujhe passport banwana hai.", "roman_urdu", "Main passport process"),
        ("مجھے پاسپورٹ بنوانا ہے۔", "urdu", "میں passport کے عمل"),
    ],
)
@patch("backend.graph.graph.run_planner")
def test_passport_journey_uses_detected_language(
    mock_planner, query, language, expected_text
):
    mock_planner.return_value = PlannerOutput(
        intent="service_journey", service_type="passport", next_step="knowledge"
    )

    result = build_graph().invoke({"user_input": query})

    assert result["service_type"] == "passport"
    assert result["preferred_language"] == language
    assert expected_text in result["response"]


@patch("backend.agents.knowledge._call_gemini")
@patch("backend.agents.knowledge._get_retriever")
def test_urdu_checklist_uses_trusted_context_and_urdu_instruction(
    get_retriever, generate
):
    requirement = _chunk(
        "Required Documents\n- Original CNIC",
        section="Required Documents",
    )
    get_retriever.return_value.retrieve.return_value = [requirement]
    generate.return_value = "مطلوبہ کاغذات:\n☐ اصل شناختی کارڈ"

    result = knowledge_agent(
        {
            "user_input": "پاسپورٹ کے لیے کون سے کاغذات چاہیے؟",
            "intent": "requirements_checklist",
            "service_type": "passport",
            "preferred_language": "urdu",
        }
    )

    assert "☐" in result["response"]
    assert result["sources"][0]["origin"] == "knowledge_base"
    assert "Respond in Urdu script" in generate.call_args.kwargs["system_prompt"]


@patch("backend.agents.knowledge._call_gemini")
@patch("backend.agents.knowledge._get_retriever")
def test_roman_urdu_fee_uses_trusted_context_and_language_instruction(
    get_retriever, generate
):
    fee = _chunk("Fees\nOfficial fee table", section="Fees")
    get_retriever.return_value.retrieve.return_value = [fee]
    generate.return_value = "Official fee categories yeh hain."

    result = knowledge_agent(
        {
            "user_input": "Passport ki fee kitni hai?",
            "intent": "fee_lookup",
            "service_type": "passport",
            "preferred_language": "roman_urdu",
        }
    )

    assert result["sources"][0]["origin"] == "knowledge_base"
    assert "natural Roman Urdu" in generate.call_args.kwargs["system_prompt"]


@patch("backend.graph.graph.run_planner")
def test_roman_urdu_service_center_action_is_localized(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="service_center_lookup",
        service_type="passport",
        next_step="action",
    )

    result = build_graph().invoke(
        {"user_input": "Karachi mein passport office kahan hai?"}
    )

    assert result["preferred_language"] == "roman_urdu"
    assert "Karachi ke liye" in result["response"]
    assert "Karachi-I (South)" in result["response"]


@patch("backend.graph.graph.knowledge_agent", return_value={"response": "Continued"})
@patch("backend.graph.graph.run_planner")
def test_short_follow_up_keeps_roman_urdu_and_passport_context(
    mock_planner, _knowledge
):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="service_journey", service_type="passport", next_step="knowledge"
        ),
        PlannerOutput(
            intent="general_information",
            service_type="passport",
            next_step="knowledge",
        ),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "roman-language-session"}}

    graph.invoke({"user_input": "Mujhe passport banwana hai."}, config=config)
    follow_up = graph.invoke({"user_input": "Karachi"}, config=config)

    assert follow_up["service_type"] == "passport"
    assert follow_up["preferred_language"] == "roman_urdu"


@patch("backend.graph.graph.knowledge_agent", return_value={"response": "English response"})
@patch("backend.graph.graph.run_planner")
def test_explicit_english_override_replaces_urdu_language(
    mock_planner, mock_knowledge
):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="service_journey", service_type="passport", next_step="knowledge"
        ),
        PlannerOutput(
            intent="general_information",
            service_type="unknown",
            next_step="knowledge",
        ),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "language-override"}}

    graph.invoke({"user_input": "مجھے پاسپورٹ بنوانا ہے۔"}, config=config)
    result = graph.invoke({"user_input": "Explain this in English."}, config=config)

    knowledge_state = mock_knowledge.call_args.args[0]
    assert result["preferred_language"] == "english"
    assert knowledge_state["intent"] == "language_rerender"
    assert knowledge_state["simple_language"] is False


def test_simple_language_detection_covers_all_supported_styles():
    assert is_simple_language_request("Make this easier to understand.")
    assert is_simple_language_request("Is notice ko asaan alfaaz mein samjhao.")
    assert is_simple_language_request("اس نوٹس کو آسان الفاظ میں سمجھائیں۔")


@patch("backend.graph.graph.run_planner")
def test_referential_simple_request_without_context_asks_for_content(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="unknown", service_type="unknown", next_step="clarify"
    )

    result = build_graph().invoke(
        {"user_input": "Explain this in simple language."}
    )

    assert "provide the information or document" in result["response"]


@patch("backend.graph.graph.knowledge_agent", return_value={"response": "Grounded"})
@patch("backend.graph.graph.run_planner")
def test_document_follow_up_stays_on_knowledge_without_service(
    mock_planner, mock_knowledge
):
    mock_planner.side_effect = [
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
        PlannerOutput(
            intent="general_information",
            service_type="unknown",
            next_step="knowledge",
        ),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "document-follow-up-routing"}}

    graph.invoke(
        {
            "user_input": "What does this notice say?",
            "uploaded_files": ["dummy.png"],
        },
        config=config,
    )
    follow_up = graph.invoke(
        {"user_input": "Is there a deadline?", "uploaded_files": None},
        config=config,
    )

    assert follow_up["intent"] == "inspect_upload"
    assert follow_up["next_step"] == "knowledge"
    assert mock_knowledge.call_count == 2


@patch("backend.agents.knowledge._call_gemini")
@patch("backend.agents.knowledge._get_retriever")
def test_simple_document_response_uses_upload_and_simple_prompt(
    get_retriever, generate
):
    upload = _chunk(
        "Applications must be submitted before 30 September.",
        origin="user_upload",
        service="user_upload",
        section="image",
        confidence="",
    )
    get_retriever.return_value.retrieve.return_value = [upload]
    generate.return_value = "Submit the application before 30 September."

    result = knowledge_agent(
        {
            "user_input": "Explain it in simple words.",
            "intent": "simple_document_explanation",
            "service_type": "unknown",
            "preferred_language": "english",
            "simple_language": True,
        },
        thread_id="simple-document",
    )

    prompt = generate.call_args.kwargs["system_prompt"]
    assert "short, clear sentences" in prompt
    assert result["sources"][0]["origin"] == "user_upload"


def test_requirement_and_fee_verification_reject_upload_claims():
    fake_requirement = _chunk(
        "Passport requires TEST-CARD-999",
        origin="user_upload",
        service="passport",
        section="Required Documents",
    )
    fake_fee = _chunk(
        "Passport fee is Rs. 50",
        origin="user_upload",
        service="passport",
        section="Fees",
    )

    assert not verify_requirement_sources([fake_requirement], "passport")
    assert not verify_fee_sources([fake_fee], "passport")


def test_document_verification_checks_critical_literals():
    upload = _chunk(
        "Deadline: 30 September",
        origin="user_upload",
        service="user_upload",
        section="image",
    )

    assert verify_document_answer("The deadline is 30 September.", [upload])
    assert not verify_document_answer("The deadline is 1 October.", [upload])
    assert not verify_document_answer(
        "Submit it online before 30 September.", [upload]
    )


@patch("backend.agents.knowledge._call_gemini", return_value="The deadline is 1 October.")
@patch("backend.agents.knowledge._get_retriever")
def test_unverified_document_literal_is_not_presented(get_retriever, _generate):
    get_retriever.return_value.retrieve.return_value = [
        _chunk(
            "Deadline: 30 September",
            origin="user_upload",
            service="user_upload",
            section="image",
        )
    ]

    result = knowledge_agent(
        {
            "user_input": "What is the deadline in this uploaded notice?",
            "intent": "inspect_upload",
            "service_type": "unknown",
            "preferred_language": "english",
        },
        thread_id="document-verification",
    )

    assert "won't present it as confirmed" in result["response"]
    assert result["sources"][0]["origin"] == "user_upload"


@patch("backend.agents.action.book_slot")
@patch("backend.agents.action.check_slots")
def test_forged_booking_success_is_not_confirmed_or_recorded(check, book):
    check.return_value = AppointmentResult(
        status="available",
        office_name="Karachi-I (South)",
        date="2026-09-15",
        slots=("11:00",),
    )
    book.return_value = AppointmentResult(
        status="booked",
        office_name="Karachi-I (South)",
        date="2026-09-15",
        requested_time="10:00",
        booking_reference="DEMO-FORGED",
        booked_slot_key="passport|Karachi-I (South)|2026-09-15|10:00",
    )

    result = action_agent(
        {
            "user_input": "Book the 10:00 slot.",
            "intent": "book_slot",
            "service_type": "passport",
            "selected_office": "Karachi-I (South)",
            "booked_slots": [],
            "journeys": {"passport": {}},
        }
    )

    assert "no booking is being confirmed" in result["response"]
    assert result["booked_slots"] == []
    assert not result.get("journeys", {}).get("passport", {}).get("appointment")


def test_successful_booking_is_verified_and_explicitly_simulated():
    result = action_agent(
        {
            "user_input": "Book the 10:00 slot.",
            "intent": "book_slot",
            "service_type": "passport",
            "selected_office": "Karachi-I (South)",
            "booked_slots": [],
        }
    )

    assert "Simulated booking confirmed (demo only)" in result["response"]
    assert result["journeys"]["passport"]["appointment"] == "demo_booked"


@patch("backend.graph.graph.knowledge_agent", side_effect=_fake_grounded_knowledge)
@patch("backend.graph.graph.run_planner")
def test_english_passport_journey_end_to_end(mock_planner, _knowledge):
    mock_planner.side_effect = [
        PlannerOutput(intent="service_journey", service_type="passport", next_step="knowledge"),
        PlannerOutput(intent="requirements_checklist", service_type="passport", next_step="knowledge"),
        PlannerOutput(intent="fee_lookup", service_type="unknown", next_step="knowledge"),
        PlannerOutput(intent="service_center_lookup", service_type="passport", next_step="action"),
        PlannerOutput(intent="check_slots", service_type="unknown", next_step="action"),
        PlannerOutput(intent="book_slot", service_type="unknown", next_step="action"),
        PlannerOutput(intent="journey_summary", service_type="unknown", next_step="action"),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    results = _invoke_turns(
        graph,
        {"configurable": {"thread_id": "english-e2e"}},
        [
            "I want to apply for a passport.",
            "What documents do I need?",
            "How much does it cost?",
            "Find a passport office in Karachi.",
            "Show appointments for the first one.",
            "Book the 10:00 slot.",
            "Show my progress.",
        ],
    )

    assert "Grounded checklist" in results[1]["response"]
    assert "Grounded fee" in results[2]["response"]
    assert "Karachi-I (South)" in results[3]["response"]
    assert "Available demo slots" in results[4]["response"]
    assert "Simulated booking confirmed" in results[5]["response"]
    assert "Demo appointment booked" in results[6]["response"]


@patch("backend.graph.graph.knowledge_agent", side_effect=_fake_grounded_knowledge)
@patch("backend.graph.graph.run_planner")
def test_roman_urdu_passport_journey_end_to_end(mock_planner, _knowledge):
    mock_planner.side_effect = [
        PlannerOutput(intent="service_journey", service_type="passport", next_step="knowledge"),
        PlannerOutput(intent="requirements_checklist", service_type="passport", next_step="knowledge"),
        PlannerOutput(intent="fee_lookup", service_type="unknown", next_step="knowledge"),
        PlannerOutput(intent="service_center_lookup", service_type="passport", next_step="action"),
        PlannerOutput(intent="check_slots", service_type="unknown", next_step="action"),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    results = _invoke_turns(
        graph,
        {"configurable": {"thread_id": "roman-urdu-e2e"}},
        [
            "Mujhe passport banwana hai.",
            "Passport ke liye kya documents chahiye?",
            "Fee kitni hai?",
            "Karachi mein nearest passport office batao.",
            "Pehle wale ke appointments dikhao.",
        ],
    )

    assert all(result["preferred_language"] == "roman_urdu" for result in results)
    assert "Karachi ke liye" in results[3]["response"]
    assert "Available demo slots" in results[4]["response"]


@patch("backend.graph.graph.knowledge_agent", side_effect=_fake_grounded_knowledge)
@patch("backend.graph.graph.run_planner")
def test_urdu_passport_journey_end_to_end(mock_planner, _knowledge):
    mock_planner.side_effect = [
        PlannerOutput(intent="service_journey", service_type="passport", next_step="knowledge"),
        PlannerOutput(intent="requirements_checklist", service_type="passport", next_step="knowledge"),
        PlannerOutput(intent="fee_lookup", service_type="unknown", next_step="knowledge"),
        PlannerOutput(intent="service_center_lookup", service_type="passport", next_step="action"),
    ]
    graph = build_graph(checkpointer=InMemorySaver())
    results = _invoke_turns(
        graph,
        {"configurable": {"thread_id": "urdu-e2e"}},
        [
            "مجھے پاسپورٹ بنوانا ہے۔",
            "پاسپورٹ کے لیے کون سے کاغذات درکار ہیں؟",
            "فیس کتنی ہے؟",
            "کراچی میں پاسپورٹ آفس کہاں ہے؟",
        ],
    )

    assert all(result["preferred_language"] == "urdu" for result in results)
    assert "Karachi کے لیے" in results[3]["response"]
    assert "Karachi-I (South)" in results[3]["response"]


def test_uploaded_notice_multi_turn_simple_language_flow():
    retriever = Retriever(FaissVectorStore())
    notice = RagDocument(
        text="PUBLIC NOTICE: Applications must be submitted before 30 September.",
        source_file="notice.png",
        service="user_upload",
        section="image",
        document_type="user_image",
    )
    planner_results = [
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
        PlannerOutput(intent="general_information", service_type="unknown", next_step="knowledge"),
        PlannerOutput(intent="general_information", service_type="unknown", next_step="knowledge"),
    ]
    answers = [
        "Applications must be submitted before 30 September.",
        "Submit the application before 30 September.",
        "The deadline is 30 September.",
        "Submit the application before 30 September.",
    ]
    with (
        patch("backend.graph.graph.run_planner", side_effect=planner_results),
        patch("backend.agents.knowledge._get_retriever", return_value=retriever),
        patch("backend.agents.knowledge._extract_uploaded_files", return_value=[notice]),
        patch("backend.agents.knowledge._call_gemini", side_effect=answers),
        patch(
            "backend.rag.retriever.embed_texts",
            side_effect=lambda texts: np.ones((len(texts), 2), dtype=np.float32),
        ),
    ):
        graph = build_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "notice-e2e"}}
        first = graph.invoke(
            {
                "user_input": "What does this notice say?",
                "uploaded_files": ["notice.png"],
            },
            config=config,
        )
        simple = graph.invoke(
            {"user_input": "Explain it in simple language.", "uploaded_files": None},
            config=config,
        )
        deadline = graph.invoke(
            {"user_input": "Is there a deadline?", "uploaded_files": None},
            config=config,
        )
        action = graph.invoke(
            {"user_input": "What do I need to do?", "uploaded_files": None},
            config=config,
        )

    for result in (first, simple, deadline, action):
        assert result["sources"][0]["origin"] == "user_upload"
    assert "30 September" in deadline["response"]
    assert "Submit" in action["response"]
