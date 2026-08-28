"""
PakAssist backend entry point.

Takes a single user input from the terminal, runs it through the
LangGraph workflow (currently: Planner only), and prints the resulting
state. Real routing and additional agents will be added in later stages.
"""
from dotenv import load_dotenv

from backend.agents.planner import PlannerError
from backend.graph.graph import build_graph
from backend.graph.state import PakAssistState

load_dotenv()


def main():
    graph = build_graph()
    user_input = input("PakAssist> ")
    initial_state: PakAssistState = {
        "user_input": user_input,
        "intent": "",
        "service_type": "",
        "next_step": "",
    }

    try:
        result = graph.invoke(initial_state)
    except PlannerError as exc:
        print(f"Planner failed: {exc}")
        return

    print(result)


if __name__ == "__main__":
    main()