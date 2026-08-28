"""
LangGraph setup for PakAssist.

The graph currently has a single node: the Planner Agent, which
interprets the user's raw input and populates intent/service_type/
next_step. No conditional routing exists yet — that's a later milestone.
"""
from langgraph.graph import StateGraph, START, END

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


def build_graph():
    """Build and compile the PakAssist graph."""
    graph_builder = StateGraph(PakAssistState)
    graph_builder.add_node("planner", _planner_node)
    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", END)
    return graph_builder.compile()