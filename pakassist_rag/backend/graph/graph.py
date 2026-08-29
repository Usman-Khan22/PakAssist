"""
ILLUSTRATIVE graph wiring.

This shows how backend/agents/knowledge.py plugs into the existing
Planner -> conditional routing -> {Knowledge, Action, Clarification}
LangGraph structure. It uses the stand-in planner.py from this milestone,
not the real one. When merging into the actual repo, wire
`knowledge_agent` into the real graph.py's existing "knowledge" node
instead of using this file.
"""

from langgraph.graph import END, StateGraph

from backend.agents.knowledge import knowledge_agent
from backend.agents.planner import planner
from backend.graph.state import PakAssistState


def _route(state: PakAssistState) -> str:
    return state.get("route", "knowledge")


def build_graph():
    graph = StateGraph(PakAssistState)

    graph.add_node("planner", planner)
    graph.add_node("knowledge", knowledge_agent)
    # "action" and "clarification" nodes are out of scope for this milestone.

    graph.set_entry_point("planner")
    graph.add_conditional_edges(
        "planner",
        _route,
        {
            "knowledge": "knowledge",
            "action": END,  # not implemented yet
            "clarification": END,  # not implemented yet
        },
    )
    graph.add_edge("knowledge", END)

    return graph.compile()
