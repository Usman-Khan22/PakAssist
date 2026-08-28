"""
Minimal LangGraph setup for PakAssist.

At this stage there are no real agents yet, so the graph has a single
placeholder node that simply passes the state through unchanged. This
exists to confirm that the LangGraph wiring (state -> node -> compiled
graph) works end to end. Real agent nodes (planner, intent detection,
etc.) will be added to this graph in later stages.
"""

from langgraph.graph import StateGraph, START, END

from backend.graph.state import PakAssistState


def _passthrough_node(state: PakAssistState) -> PakAssistState:
    """Temporary node that does nothing but return the state as-is."""
    return state


def build_graph():
    """Build and compile the PakAssist graph."""
    graph_builder = StateGraph(PakAssistState)

    graph_builder.add_node("passthrough", _passthrough_node)
    graph_builder.add_edge(START, "passthrough")
    graph_builder.add_edge("passthrough", END)

    return graph_builder.compile()