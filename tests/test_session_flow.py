"""Multi-turn session and clarification-continuation tests."""

from unittest.mock import MagicMock, patch

from langgraph.checkpoint.memory import InMemorySaver

from backend.agents.planner import PlannerOutput
from backend.graph.graph import build_graph
from backend.main import run_cli


def _session_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


@patch("backend.graph.graph.run_planner")
def test_passport_location_clarification_continues(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="service_center_lookup",
        service_type="passport",
        next_step="action",
    )
    graph = build_graph(checkpointer=InMemorySaver())
    config = _session_config("passport-session")

    first = graph.invoke(
        {"user_input": "Find the nearest passport office."}, config=config
    )
    second = graph.invoke({"user_input": "Karachi"}, config=config)

    assert "Which city or region" in first["response"]
    assert first["pending_clarification"] == "location"
    assert "Karachi-I (South)" in second["response"]
    assert second["service_type"] == "passport"
    assert second["pending_clarification"] is None
    mock_planner.assert_called_once()


@patch("backend.graph.graph.run_planner")
def test_driving_license_location_clarification_continues(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="service_center_lookup",
        service_type="driving_license",
        next_step="action",
    )
    graph = build_graph(checkpointer=InMemorySaver())
    config = _session_config("license-session")

    first = graph.invoke(
        {"user_input": "Find a driving license center."}, config=config
    )
    second = graph.invoke({"user_input": "Attock"}, config=config)

    assert "Which city or region" in first["response"]
    assert "Attock Driving Licensing Branch" in second["response"]
    assert second["service_type"] == "driving_license"


@patch("backend.graph.graph.run_planner")
def test_direct_action_still_works(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="service_center_lookup",
        service_type="passport",
        next_step="action",
    )

    result = build_graph().invoke(
        {"user_input": "Find a passport office in Karachi."}
    )

    assert "Karachi-I (South)" in result["response"]


@patch("backend.graph.graph.knowledge_agent", return_value={"response": "RAG response"})
@patch("backend.graph.graph.run_planner")
def test_knowledge_route_still_works(mock_planner, mock_knowledge):
    mock_planner.return_value = PlannerOutput(
        intent="requirements",
        service_type="passport",
        next_step="knowledge",
    )

    result = build_graph().invoke(
        {"user_input": "What documents are required for a passport?"}
    )

    assert result["response"] == "RAG response"
    mock_knowledge.assert_called_once()


@patch("backend.graph.graph.run_planner")
def test_ambiguous_request_still_uses_clarification(mock_planner):
    mock_planner.return_value = PlannerOutput(
        intent="unknown",
        service_type="unknown",
        next_step="clarify",
    )

    result = build_graph().invoke({"user_input": "Help me"})

    assert result["response"] == "Please clarify which government service you need."


@patch("main.build_graph")
def test_exit_and_quit_end_cli_without_invoking_graph(mock_build_graph):
    graph = MagicMock()
    mock_build_graph.return_value = graph

    exit_output = []
    run_cli(input_fn=lambda _: "exit", output_fn=exit_output.append)
    quit_output = []
    run_cli(input_fn=lambda _: "quit", output_fn=quit_output.append)

    graph.invoke.assert_not_called()
    assert exit_output == ["Goodbye."]
    assert quit_output == ["Goodbye."]


@patch("main.build_graph")
def test_cli_reuses_one_thread_id_for_all_turns(mock_build_graph):
    graph = MagicMock()
    graph.invoke.side_effect = [
        {"response": "First response", "sources": []},
        {"response": "Second response", "sources": []},
    ]
    mock_build_graph.return_value = graph
    inputs = iter(["First question", "Second question", "exit"])

    run_cli(input_fn=lambda _: next(inputs), output_fn=lambda _: None)

    first_config = graph.invoke.call_args_list[0].kwargs["config"]
    second_config = graph.invoke.call_args_list[1].kwargs["config"]
    assert first_config["configurable"]["thread_id"]
    assert first_config == second_config


@patch("backend.graph.graph.run_planner")
def test_checkpoint_state_does_not_leak_between_threads(mock_planner):
    mock_planner.side_effect = [
        PlannerOutput(
            intent="service_center_lookup",
            service_type="passport",
            next_step="action",
        ),
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
    ]
    graph = build_graph(checkpointer=InMemorySaver())

    pending = graph.invoke(
        {"user_input": "Find the nearest passport office."},
        config=_session_config("first-session"),
    )
    separate = graph.invoke(
        {"user_input": "Karachi"}, config=_session_config("second-session")
    )

    assert pending["pending_clarification"] == "location"
    assert separate["response"] == "Please clarify which government service you need."
    assert "Karachi-I (South)" not in separate["response"]
