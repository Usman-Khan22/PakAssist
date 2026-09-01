"""LangGraph workflow for PakAssist."""
from langgraph.graph import StateGraph, START, END

from backend.agents.action import action_agent
from backend.agents.knowledge import knowledge_agent
from backend.agents.planner import run_planner
from backend.graph.state import PakAssistState


def _planner_node(state: PakAssistState) -> dict:
    """Runs the Planner Agent and returns only the fields it owns."""
    result = run_planner(state["user_input"])
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


def build_graph():
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
    return graph_builder.compile()
