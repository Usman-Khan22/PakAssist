"""
STAND-IN Planner.

This is NOT the real PakAssist Planner — it's a minimal mock so
backend/graph/graph.py and the tests in this milestone can demonstrate the
Knowledge Agent wired into a Planner -> route -> agent flow without needing
the actual Planner implementation. Replace this with the real planner.py
when merging.
"""

from backend.graph.state import PakAssistState

_ACTION_KEYWORDS = {"book", "appointment", "schedule", "apply now"}


def planner(state: PakAssistState) -> PakAssistState:
    query = state.get("user_query", "").lower()

    if any(k in query for k in _ACTION_KEYWORDS):
        state["route"] = "action"
    elif query.strip() == "":
        state["route"] = "clarification"
    else:
        state["route"] = "knowledge"

    state["intent"] = "informational" if state["route"] == "knowledge" else state["route"]
    return state
