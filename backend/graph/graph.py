"""LangGraph workflow for PakAssist."""
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig

from backend.agents.action import action_agent
from backend.agents.knowledge import is_upload_inspection_request, knowledge_agent
from backend.agents.planner import run_planner
from backend.graph.state import PakAssistState
from backend.services.fee_lookup import is_fee_request
from backend.services.checklist_builder import is_checklist_request
from backend.services.journey import (
    initialize_journey,
    is_journey_request,
    is_service_journey_goal,
    journey_orientation,
)
from backend.services.language import (
    detect_language,
    is_language_override_request,
    is_simple_language_request,
    message,
)


def _planner_context(state: PakAssistState) -> dict:
    """Expose only useful short-lived state to the Planner."""
    context = {}
    for field in (
        "service_type",
        "intent",
        "selected_office",
        "office_options",
        "appointment_date",
        "pending_clarification",
        "preferred_language",
    ):
        value = state.get(field)
        if value and value != "unknown":
            context[field] = value
    journeys = state.get("journeys") or {}
    if journeys:
        context["journey_services"] = list(journeys)
    return context


def _contextual_appointment_intent(state: PakAssistState) -> str | None:
    """Recognize generic appointment follow-ups if planning is inconclusive."""
    query = state["user_input"].casefold().strip(" .?!")
    if "book" in query and ("slot" in query or "appointment" in query):
        return "book_slot"
    if "appointment" in query or "available slot" in query or "show slots" in query:
        return "check_slots"
    ordinal_answers = {
        "first", "1st", "second", "2nd", "third", "3rd",
        "fourth", "4th", "fifth", "5th",
        "sixth", "6th", "seventh", "7th", "eighth", "8th",
        "ninth", "9th", "tenth", "10th",
    }
    if state.get("office_options") and (
        query.isdigit() or any(word in query.split() for word in ordinal_answers)
    ):
        return "check_slots"
    return None


def _planner_node(state: PakAssistState) -> dict:
    """Runs the Planner Agent and returns only the fields it owns."""
    preferred_language = detect_language(
        state.get("user_input", ""), state.get("preferred_language")
    )
    simple_language = is_simple_language_request(state.get("user_input", ""))
    language_override = is_language_override_request(state.get("user_input", ""))

    def planned(update: dict) -> dict:
        return {
            **update,
            "preferred_language": preferred_language,
            "simple_language": simple_language,
        }

    pending = state.get("pending_clarification")
    if pending in {"location", "office"}:
        user_input = state.get("user_input", "").strip()
        if pending == "location":
            original_request = (state.get("pending_request") or "").rstrip(" ?.!")
            user_input = f"{original_request} in {user_input}"
        return planned({
            "user_input": user_input,
            "intent": state["intent"],
            "service_type": state["service_type"],
            "next_step": "action",
            "pending_clarification": None,
            "pending_request": None,
        })

    result = run_planner(state["user_input"], context=_planner_context(state))
    previous_service = state.get("service_type")
    previous_intent = state.get("intent")
    if simple_language or language_override:
        if (
            not state.get("response")
            and not state.get("uploaded_files")
            and previous_service in {None, "", "unknown"}
            and result.service_type == "unknown"
        ):
            return planned({
                "intent": "missing_presentation_context",
                "service_type": "unknown",
                "next_step": "clarify",
            })
        service_type = result.service_type
        if service_type == "unknown" and previous_service not in {None, "", "unknown"}:
            service_type = previous_service
        document_presentation = (
            "document_presentation"
            if state.get("uploaded_files")
            or previous_intent in {
                "inspect_upload",
                "simple_document_explanation",
                "document_presentation",
            }
            else None
        )
        presentation_intent = document_presentation or (
            "simple_explanation" if simple_language else "language_rerender"
        )
        return planned({
            "intent": presentation_intent,
            "service_type": service_type,
            "next_step": "knowledge",
        })
    if (
        previous_intent
        in {"inspect_upload", "simple_document_explanation", "document_presentation"}
        and result.service_type == "unknown"
        and result.intent in {"unknown", "general_information", "inspect_upload"}
        and result.next_step in {"knowledge", "clarify"}
    ):
        return planned({
            "intent": "inspect_upload",
            "service_type": "unknown",
            "next_step": "knowledge",
        })
    if (
        state.get("uploaded_files")
        and result.next_step in {"knowledge", "clarify"}
        and result.intent in {"unknown", "inspect_upload", "general_inquiry"}
        and is_upload_inspection_request(state["user_input"])
    ):
        return planned({
            "intent": "inspect_upload",
            "service_type": result.service_type,
            "next_step": "knowledge",
        })
    if is_service_journey_goal(result.intent) and (
        result.next_step == "action"
        or result.intent in {"service_journey", "start_service_journey"}
    ):
        return planned({
            "intent": "service_journey",
            "service_type": result.service_type,
            "next_step": "knowledge",
        })
    if is_journey_request(result.intent, state["user_input"]):
        return planned({
            "intent": "journey_summary",
            "service_type": (
                previous_service
                if result.service_type == "unknown"
                and previous_service not in {None, "", "unknown"}
                else result.service_type
            ),
            "next_step": "action",
        })
    fallback_intent = _contextual_appointment_intent(state)
    appointment_intent = (
        result.intent
        if result.intent in {"check_slots", "book_slot"}
        else fallback_intent if result.intent == "unknown" else None
    )
    if appointment_intent:
        return planned({
            "intent": appointment_intent,
            "service_type": (
                previous_service
                if result.service_type == "unknown"
                and previous_service not in {None, "", "unknown"}
                else result.service_type
            ),
            "next_step": "action",
        })
    if (
        result.service_type == "unknown"
        and previous_service not in {None, "", "unknown"}
        and (
            is_fee_request(result.intent, state["user_input"])
            or is_checklist_request(result.intent, state["user_input"])
        )
    ):
        checklist_request = is_checklist_request(result.intent, state["user_input"])
        return planned({
            "intent": "requirements_checklist" if checklist_request else "fee_lookup",
            "service_type": previous_service,
            "next_step": "knowledge",
        })
    return planned({
        "intent": result.intent,
        "service_type": result.service_type,
        "next_step": result.next_step,
    })


def _knowledge_node(state: PakAssistState, config: RunnableConfig) -> dict:
    """Executes the Multimodal RAG Knowledge Agent."""
    if state.get("intent") == "service_journey":
        return {
            "response": journey_orientation(state),
            "sources": [],
            "journeys": initialize_journey(state),
        }
    thread_id = config.get("configurable", {}).get("thread_id")
    return knowledge_agent(state, thread_id=thread_id)


def _action_node(state: PakAssistState) -> dict:
    """Execute a supported action through the Action Agent."""
    return action_agent(state)


def _clarification_node(state: PakAssistState) -> dict:
    """Ask for clarification when the request cannot be routed safely."""
    language = state.get("preferred_language", "english")
    if state.get("intent") == "missing_presentation_context":
        return {"response": message("presentation_context_required", language)}
    return {"response": message("clarify_service", language)}


def _route_after_planner(state: PakAssistState) -> str:
    """Select a downstream node from the Planner's validated decision."""
    if state["intent"] in {
        "inspect_upload",
        "simple_explanation",
        "simple_document_explanation",
        "document_presentation",
        "language_rerender",
    } and state["next_step"] == "knowledge":
        return "knowledge"
    if state["intent"] == "unknown" or state["service_type"] == "unknown":
        return "clarification"
    if state["next_step"] == "knowledge":
        return "knowledge"
    if state["next_step"] == "action":
        return "action"
    return "clarification"


def build_graph(checkpointer=None):
    """Build and compile the PakAssist graph."""
    graph_builder = StateGraph(PakAssistState)
    graph_builder.add_node("planner", _planner_node)
    graph_builder.add_node("knowledge", _knowledge_node)
    graph_builder.add_node("action", _action_node)
    graph_builder.add_node("clarification", _clarification_node)
    graph_builder.add_edge(START, "planner")
    graph_builder.add_conditional_edges(
        "planner",
        _route_after_planner,
        {
            "knowledge": "knowledge",
            "action": "action",
            "clarification": "clarification",
        },
    )
    graph_builder.add_edge("knowledge", END)
    graph_builder.add_edge("action", END)
    graph_builder.add_edge("clarification", END)
    return graph_builder.compile(checkpointer=checkpointer)
