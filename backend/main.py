"""
PakAssist backend entry point.

At this stage, this file only verifies that the LangGraph foundation is
wired correctly. It takes a single user input from the terminal, runs it
through the (currently empty) graph, and prints the resulting state.
Real agents and routing logic will be added in later stages.
"""

from dotenv import load_dotenv

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

    result = graph.invoke(initial_state)
    print(result)


if __name__ == "__main__":
    main()