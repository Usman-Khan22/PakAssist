"""Upload session isolation, blending, trust, and routing regressions."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from langgraph.checkpoint.memory import InMemorySaver

from backend.agents.knowledge import UPLOAD_REQUIRED_MESSAGE, knowledge_agent
from backend.agents.planner import PlannerOutput
from backend.graph.graph import build_graph
from backend.rag.loader import RagDocument
from backend.rag.retriever import RetrievedChunk, Retriever
from backend.rag.vector_store import FaissVectorStore


class _SearchStore:
    def __init__(self, results):
        self.results = results

    def search(self, _query_vector, k=5):
        return self.results[:k]


def _vectors(texts):
    return np.ones((len(texts), 2), dtype=np.float32)


def _upload_document(text: str) -> RagDocument:
    return RagDocument(
        text=text,
        source_file="upload.png",
        service="user_upload",
        section="image",
        document_type="user_image",
    )


@patch("backend.rag.retriever.embed_texts", side_effect=_vectors)
def test_same_thread_upload_is_retrievable_with_source(_embed):
    retriever = Retriever(FaissVectorStore())
    with (
        patch("backend.agents.knowledge._get_retriever", return_value=retriever),
        patch(
            "backend.agents.knowledge._extract_uploaded_files",
            return_value=[_upload_document("PAKASSIST-THREAD-A-48291")],
        ),
        patch("backend.agents.knowledge._call_gemini", return_value="48291"),
    ):
        knowledge_agent(
            {
                "user_input": "Read this uploaded image for my passport.",
                "service_type": "passport",
                "intent": "inspect_upload",
                "uploaded_files": ["dummy.png"],
            },
            thread_id="thread-a",
        )
        result = knowledge_agent(
            {
                "user_input": "What was the distinctive value in my uploaded file?",
                "service_type": "passport",
                "intent": "inspect_upload",
            },
            thread_id="thread-a",
        )

    assert result["response"] == "48291"
    assert any(source["origin"] == "user_upload" for source in result["sources"])


@patch("backend.rag.retriever.embed_texts", side_effect=_vectors)
def test_cross_thread_upload_isolation(_embed):
    retriever = Retriever(FaissVectorStore())
    retriever.add_user_content(
        [_upload_document("PAKASSIST-THREAD-A-48291")], thread_id="thread-a"
    )

    assert retriever.retrieve("48291", thread_id="thread-b") == []


@patch("backend.rag.retriever.embed_texts", side_effect=_vectors)
def test_two_threads_have_independent_upload_stores(_embed):
    retriever = Retriever(FaissVectorStore())
    retriever.add_user_content([_upload_document("PHRASE-A")], thread_id="a")
    retriever.add_user_content([_upload_document("PHRASE-B")], thread_id="b")

    a_results = retriever.retrieve("phrase", thread_id="a")
    b_results = retriever.retrieve("phrase", thread_id="b")

    assert [result.text for result in a_results] == ["PHRASE-A"]
    assert [result.text for result in b_results] == ["PHRASE-B"]


@patch("backend.rag.retriever.embed_texts", side_effect=_vectors)
def test_official_store_is_shared_across_threads(_embed):
    official = _SearchStore(
        [(0.9, "Official passport requirements", {"service": "passport"})]
    )
    retriever = Retriever(official)

    a_results = retriever.retrieve("requirements", thread_id="a")
    b_results = retriever.retrieve("requirements", thread_id="b")

    assert a_results[0].text == b_results[0].text
    assert a_results[0].origin == b_results[0].origin == "knowledge_base"


@patch("backend.rag.retriever.embed_texts", side_effect=_vectors)
def test_upload_aware_blending_reserves_qualifying_upload(_embed):
    retriever = Retriever(
        _SearchStore(
            [
                (0.99, "Official one", {}),
                (0.98, "Official two", {}),
                (0.97, "Official three", {}),
            ]
        )
    )
    retriever.upload_stores["a"] = _SearchStore(
        [(0.50, "Relevant upload", {"document_type": "user_image"})]
    )

    results = retriever.retrieve(
        "uploaded image", top_k=2, thread_id="a", prefer_user_files=True
    )

    assert len(results) == 2
    assert any(result.origin == "user_upload" for result in results)


@patch("backend.rag.retriever.embed_texts", side_effect=_vectors)
def test_upload_blending_respects_score_threshold(_embed):
    retriever = Retriever(_SearchStore([(0.9, "Official", {})]))
    retriever.upload_stores["a"] = _SearchStore(
        [(0.1, "Low upload", {"document_type": "user_image"})]
    )

    results = retriever.retrieve(
        "uploaded image",
        top_k=2,
        min_score=0.2,
        thread_id="a",
        prefer_user_files=True,
    )

    assert all(result.origin != "user_upload" for result in results)


def _chunk(text, origin, section, confidence="high"):
    return RetrievedChunk(
        text=text,
        metadata={
            "service": "passport",
            "section": section,
            "confidence": confidence,
        },
        score=0.9,
        origin=origin,
    )


@pytest.mark.parametrize(
    ("query", "intent", "official", "uploaded"),
    [
        (
            "What documents do I need for a passport?",
            "requirements_checklist",
            _chunk("Required Documents: CNIC", "knowledge_base", "Required Documents"),
            _chunk("Passport requires a library card", "user_upload", "image"),
        ),
        (
            "What is the passport fee?",
            "fee_lookup",
            _chunk("Fees: official table", "knowledge_base", "Fees"),
            _chunk("Invented passport fee", "user_upload", "image"),
        ),
    ],
)
def test_checklist_and_fee_generation_remain_trusted_only(
    query, intent, official, uploaded
):
    retriever = MagicMock()
    retriever.retrieve.return_value = [uploaded, official]
    with (
        patch("backend.agents.knowledge._get_retriever", return_value=retriever),
        patch("backend.agents.knowledge._call_gemini", return_value="Grounded") as call,
    ):
        result = knowledge_agent(
            {"user_input": query, "service_type": "passport", "intent": intent},
            thread_id="a",
        )

    assert all(source["origin"] == "knowledge_base" for source in result["sources"])
    assert uploaded.text not in call.call_args.args[1]
    assert retriever.retrieve.call_args.kwargs["include_user_files"] is False


@pytest.mark.parametrize(
    "query",
    [
        "For my passport service, tell me what information is visible in this uploaded image.",
        "Tell me what is visible in this uploaded passport image.",
        "Explain this uploaded image for my passport.",
    ],
)
@patch("backend.graph.graph.knowledge_agent", return_value={"response": "Upload read"})
@patch("backend.graph.graph.run_planner")
def test_upload_inspection_routes_to_knowledge(
    mock_planner, mock_knowledge, query
):
    mock_planner.return_value = PlannerOutput(
        intent="unknown", service_type="passport", next_step="clarify"
    )
    result = build_graph().invoke(
        {"user_input": query, "uploaded_files": ["dummy.png"]},
        config={"configurable": {"thread_id": "upload-routing"}},
    )

    assert result["intent"] == "inspect_upload"
    assert result["next_step"] == "knowledge"
    assert result["response"] == "Upload read"
    mock_knowledge.assert_called_once()
    assert mock_knowledge.call_args.kwargs["thread_id"] == "upload-routing"


@pytest.mark.parametrize(
    "query",
    [
        "What information is visible in this uploaded image?",
        "Explain this uploaded document.",
        "What does this government notice say?",
        "What information can you extract from this image?",
    ],
)
@patch("backend.rag.retriever.embed_texts", side_effect=_vectors)
def test_generic_upload_inspection_uses_upload_without_service(_embed, query):
    retriever = Retriever(FaissVectorStore())
    visible_text = "PUBLIC NOTICE TEST-NOTICE-48291 Office closed on Friday"
    with (
        patch(
            "backend.graph.graph.run_planner",
            return_value=PlannerOutput(
                intent="unknown", service_type="unknown", next_step="clarify"
            ),
        ),
        patch("backend.agents.knowledge._get_retriever", return_value=retriever),
        patch(
            "backend.agents.knowledge._extract_uploaded_files",
            return_value=[_upload_document(visible_text)],
        ),
        patch("backend.agents.knowledge._call_gemini", return_value=visible_text),
    ):
        result = build_graph().invoke(
            {"user_input": query, "uploaded_files": ["dummy.png"]},
            config={"configurable": {"thread_id": f"generic-{query}"}},
        )

    assert result["intent"] == "inspect_upload"
    assert result["service_type"] == "unknown"
    assert result["next_step"] == "knowledge"
    assert "TEST-NOTICE-48291" in result["response"]
    assert any(source["origin"] == "user_upload" for source in result["sources"])


@patch("backend.graph.graph.run_planner")
@patch("backend.agents.knowledge._get_retriever")
def test_generic_upload_request_without_upload_asks_for_document(
    get_retriever, mock_planner
):
    mock_planner.return_value = PlannerOutput(
        intent="inspect_upload", service_type="unknown", next_step="knowledge"
    )
    get_retriever.return_value.retrieve.return_value = []

    result = build_graph().invoke(
        {"user_input": "What information is visible in this uploaded image?"},
        config={"configurable": {"thread_id": "no-upload"}},
    )

    assert result["response"] == UPLOAD_REQUIRED_MESSAGE
    assert result["sources"] == []


@patch("backend.rag.retriever.embed_texts", side_effect=_vectors)
def test_generic_upload_context_is_available_on_same_thread_follow_up(_embed):
    retriever = Retriever(FaissVectorStore())
    planner_results = [
        PlannerOutput(intent="unknown", service_type="unknown", next_step="clarify"),
        PlannerOutput(
            intent="inspect_upload", service_type="unknown", next_step="knowledge"
        ),
    ]
    with (
        patch("backend.graph.graph.run_planner", side_effect=planner_results),
        patch("backend.agents.knowledge._get_retriever", return_value=retriever),
        patch(
            "backend.agents.knowledge._extract_uploaded_files",
            return_value=[
                _upload_document("PUBLIC NOTICE from the Transport Department")
            ],
        ),
        patch(
            "backend.agents.knowledge._call_gemini",
            side_effect=["It is a public notice.", "The Transport Department."],
        ),
    ):
        graph = build_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "generic-follow-up"}}
        graph.invoke(
            {
                "user_input": "What does this notice say?",
                "uploaded_files": ["dummy.png"],
            },
            config=config,
        )
        follow_up = graph.invoke(
            {
                "user_input": "Which department is it from?",
                "uploaded_files": None,
            },
            config=config,
        )

    assert follow_up["response"] == "The Transport Department."
    assert any(source["origin"] == "user_upload" for source in follow_up["sources"])


@pytest.mark.parametrize(
    ("query", "planner_output"),
    [
        (
            "What documents do I need?",
            PlannerOutput(
                intent="requirements_checklist",
                service_type="unknown",
                next_step="knowledge",
            ),
        ),
        (
            "What is the fee?",
            PlannerOutput(
                intent="fee_lookup", service_type="unknown", next_step="knowledge"
            ),
        ),
        (
            "Find the nearest office.",
            PlannerOutput(
                intent="service_center_lookup",
                service_type="unknown",
                next_step="action",
            ),
        ),
    ],
)
@patch("backend.graph.graph.run_planner")
def test_service_specific_requests_without_service_still_clarify(
    mock_planner, query, planner_output
):
    mock_planner.return_value = planner_output

    result = build_graph().invoke(
        {"user_input": query},
        config={"configurable": {"thread_id": "service-required"}},
    )

    assert result["response"] == "Please clarify which government service you need."


@patch("backend.agents.knowledge._get_retriever")
@pytest.mark.parametrize("uploaded_files", [["dummy.png"], None])
def test_upload_processing_or_retrieval_without_thread_id_fails_safely(
    get_retriever, uploaded_files
):
    result = knowledge_agent(
        {
            "user_input": "Read this uploaded image for my passport.",
            "service_type": "passport",
            "intent": "inspect_upload",
            "uploaded_files": uploaded_files,
        }
    )

    assert "no valid session context" in result["response"]
    assert result["sources"] == []
    get_retriever.assert_not_called()
