"""
Verifies the Knowledge Agent's no-hallucination fallback: when retrieval
finds nothing relevant, it must return the safe message directly and must
NOT call Gemini at all (so this test needs no API key and no network).
"""

from unittest.mock import patch

from backend.agents.knowledge import NO_CONTEXT_MESSAGE, knowledge_agent


@patch("backend.agents.knowledge._get_retriever")
@patch("backend.agents.knowledge._call_gemini")
def test_no_relevant_chunks_skips_gemini_and_returns_safe_message(mock_call_gemini, mock_get_retriever):
    mock_get_retriever.return_value.retrieve.return_value = []

    state = {"user_input": "What is the best recipe for biryani?"}
    result = knowledge_agent(state)

    assert result["response"] == NO_CONTEXT_MESSAGE
    assert result["sources"] == []
    mock_call_gemini.assert_not_called()


@patch("backend.agents.knowledge._get_retriever")
def test_empty_query_skips_retrieval_entirely(mock_get_retriever):
    state = {"user_input": "   "}
    result = knowledge_agent(state)

    assert result["response"] == NO_CONTEXT_MESSAGE
    mock_get_retriever.assert_not_called()
