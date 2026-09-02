"""LangGraph workflow for PakAssist."""
from langgraph.graph import StateGraph, START, END

from backend.agents.action import action_agent
from backend.agents.knowledge import knowledge_agent
from backend.agents.planner import run_planner
from backend.graph.state import PakAssistState
from backend.services.fee_lookup import is_fee_request


def _planner_node(state: PakAssistState) -> dict:
    """Runs the Planner Agent and returns only the fields it owns."""
    if state.get("pending_clarification") == "location":
        original_request = (state.get("pending_request") or "").rstrip(" ?.!")
        location = state.get("user_input", "").strip()
        return {
            "user_input": f"{original_request} in {location}",
            "intent": state["intent"],
            "service_type": state["service_type"],
            "next_step": "action",
            "pending_clarification": None,
            "pending_request": None,
        }

    result = run_planner(state["user_input"])
    previous_service = state.get("service_type")
    if (
        result.service_type == "unknown"
        and previous_service not in {None, "", "unknown"}
        and is_fee_request(result.intent, state["user_input"])
    ):
        return {
            "intent": "fee_lookup",
            "service_type": previous_service,
            "next_step": "knowledge",
        }
    return {
        "intent": result.intent,
        "service_type": result.service_type,
        "next_step": result.next_step,
    }


def _knowledge_node(state: PakAssistState) -> dict:
    """Executes the Multimodal RAG Knowledge Agent."""
    return knowledge_agent(state)


def _action_node(state: PakAssistState) -> dict:
    """Execute a supported action through the Action Agent."""
    return action_agent(state)


def _clarification_node(state: PakAssistState) -> dict:
    """Ask for clarification when the request cannot be routed safely."""
    return {"response": "Please clarify which government service you need."}


def _route_after_planner(state: PakAssistState) -> str:
    """Select a downstream node from the Planner's validated decision."""
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
