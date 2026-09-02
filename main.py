"""PakAssist multi-turn CLI entry point."""
import sys
from uuid import uuid4

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

from backend.agents.planner import PlannerError
from backend.graph.graph import build_graph
from backend.graph.state import PakAssistState

load_dotenv()


def run_cli(uploaded_files=None, input_fn=input, output_fn=print):
    """Run one short-lived conversation backed by an in-memory checkpoint."""
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": uuid4().hex}}
    first_turn = True

    while True:
        try:
            user_input = input_fn("PakAssist> ")
        except EOFError:
            output_fn("\nGoodbye.")
            break

        if user_input.strip().casefold() in {"exit", "quit"}:
            output_fn("Goodbye.")
            break
        if not user_input.strip():
            continue

        turn_state: PakAssistState = {
            "user_input": user_input,
            "uploaded_files": uploaded_files if first_turn else None,
            "sources": [],
        }

        try:
            result = graph.invoke(turn_state, config=config)
        except PlannerError as exc:
            output_fn(f"Planner failed: {exc}")
            first_turn = False
            continue

        output_fn("\nPakAssist:")
        output_fn(result.get("response", ""))
        sources = result.get("sources")
        if sources:
            output_fn("\nSources:")
            for source in sources:
                output_fn(
                    f" - {source.get('label')} "
                    f"(origin: {source.get('origin')}, "
                    f"confidence: {source.get('confidence')})"
                )
        first_turn = False


def main():
    uploaded_files = [arg for arg in sys.argv[1:] if arg] or None
    run_cli(uploaded_files=uploaded_files)


if __name__ == "__main__":
    main()
