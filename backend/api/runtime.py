from typing import List, Optional

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

from backend.graph.graph import build_graph
from backend.graph.state import PakAssistState


load_dotenv()


checkpointer = InMemorySaver()

graph = build_graph(
    checkpointer=checkpointer
)


def invoke_graph(
    message: str,
    session_id: str,
    uploaded_files: Optional[List[str]] = None,
    is_first_turn: bool = False,
):
    config = {
        "configurable": {
            "thread_id": session_id
        }
    }

    turn_state: PakAssistState = {
        "user_input": message,
        "uploaded_files": uploaded_files,
        "sources": [],
        "is_first_turn": is_first_turn,
    }

    return graph.invoke(
        turn_state,
        config=config,
    )