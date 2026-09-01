"""
PakAssist backend entry point.

Takes user input (and optional file paths) from the terminal, runs it through
the LangGraph workflow, and prints the resulting state and response.
"""
import sys
from dotenv import load_dotenv

from backend.agents.planner import PlannerError
from backend.graph.graph import build_graph
from backend.graph.state import PakAssistState

load_dotenv()


def main():
    graph = build_graph()
    user_input = input("PakAssist> ")
    uploaded_files = [arg for arg in sys.argv[1:] if arg] if len(sys.argv) > 1 else None

    initial_state: PakAssistState = {
        "user_input": user_input,
        "intent": "",
        "service_type": "",
        "next_step": "",
        "response": "",
        "uploaded_files": uploaded_files,
        "sources": [],
    }

    try:
        result = graph.invoke(initial_state)
    except PlannerError as exc:
        print(f"Planner failed: {exc}")
        return

    print("\n--- Result ---")
    print(f"Response:\n{result.get('response', '')}")
    sources = result.get("sources")
    if sources:
        print("\nSources:")
        for s in sources:
            print(f" - {s.get('label')} (origin: {s.get('origin')}, confidence: {s.get('confidence')})")


if __name__ == "__main__":
    main()
