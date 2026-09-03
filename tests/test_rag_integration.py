"""
Integration tests for PakAssist LangGraph workflow with Multimodal RAG.

Tests all 6 core integration scenarios:
1. Driving license query -> Planner -> Knowledge route -> Knowledge Agent -> RAG retrieval -> Grounded response.
2. Passport query -> Planner -> Knowledge route -> Knowledge Agent -> RAG retrieval -> Grounded response.
3. Unknown / unrelated query -> Knowledge route -> No-context safe fallback.
4. User image upload -> Multimodal text extraction -> In-memory indexing -> Retrieval & Answer.
5. User PDF upload -> PyMuPDF/Gemini text extraction -> In-memory indexing -> Retrieval & Answer.
6. Existing non-knowledge routes (Action, Clarification) are preserved.
"""

from unittest.mock import MagicMock, patch
import pytest

from backend.agents.knowledge import NO_CONTEXT_MESSAGE
from backend.agents.planner import PlannerOutput
from backend.graph.graph import build_graph
from backend.graph.state import PakAssistState


@pytest.fixture(scope="module")
def app_graph():
    return build_graph()


@patch("backend.graph.graph.run_planner")
@patch("backend.agents.knowledge._call_gemini")
def test_1_driving_license_knowledge_flow(mock_gemini_call, mock_planner, app_graph):
    """Test 1: Driving license query flows to Knowledge agent and retrieves KB context."""
    mock_planner.return_value = PlannerOutput(
        intent="apply_for_service",
        service_type="driving_license",
        next_step="knowledge",
    )
    mock_gemini_call.return_value = "Learner permit, CNIC, and medical certificate are required."

    initial_state: PakAssistState = {
        "user_input": "What documents are required for a driving license?",
        "intent": "",
        "service_type": "",
        "next_step": "",
        "response": "",
        "sources": [],
    }

    result = app_graph.invoke(initial_state)

    assert result["intent"] == "apply_for_service"
    assert result["service_type"] == "driving_license"
    assert result["next_step"] == "knowledge"
    assert result["response"] == "Learner permit, CNIC, and medical certificate are required."
    assert len(result["sources"]) > 0
    assert any(s["service"] == "driving_license" for s in result["sources"])


@patch("backend.graph.graph.run_planner")
@patch("backend.agents.knowledge._call_gemini")
def test_2_passport_requirements_flow(mock_gemini_call, mock_planner, app_graph):
    """Test 2: Passport query flows to Knowledge agent and retrieves passport KB context."""
    mock_planner.return_value = PlannerOutput(
        intent="apply_for_service",
        service_type="passport",
        next_step="knowledge",
    )
    mock_gemini_call.return_value = "You need CNIC/NICOP and previous passport if renewing."

    initial_state: PakAssistState = {
        "user_input": "What are the requirements for a Pakistani passport?",
        "intent": "",
        "service_type": "",
        "next_step": "",
        "response": "",
        "sources": [],
    }

    result = app_graph.invoke(initial_state)

    assert result["service_type"] == "passport"
    assert result["next_step"] == "knowledge"
    assert result["response"] == "You need CNIC/NICOP and previous passport if renewing."
    assert len(result["sources"]) > 0
    assert any(s["service"] == "passport" for s in result["sources"])


@patch("backend.graph.graph.run_planner")
@patch("backend.agents.knowledge._call_gemini")
def test_3_unknown_request_fallback(mock_gemini_call, mock_planner, app_graph):
    """Test 3: Unrelated query returns safe no-context fallback and skips LLM generation."""
    mock_planner.return_value = PlannerOutput(
        intent="unknown",
        service_type="unknown",
        next_step="knowledge",
    )

    # Even if next_step is knowledge, if intent/service_type is unknown it routes to clarification
    initial_state: PakAssistState = {
        "user_input": "What is the best recipe for biryani?",
        "intent": "",
        "service_type": "",
        "next_step": "",
        "response": "",
        "sources": [],
    }

    result = app_graph.invoke(initial_state)
    assert result["response"] == "Please clarify which government service you need."
    mock_gemini_call.assert_not_called()


@patch("backend.graph.graph.run_planner")
@patch("backend.agents.knowledge._get_retriever")
@patch("backend.agents.knowledge._call_gemini")
def test_3b_unknown_request_routed_to_knowledge_returns_no_context(mock_gemini_call, mock_get_retriever, mock_planner, app_graph):
    """Test 3b: If an unanswerable query reaches the knowledge node, it returns NO_CONTEXT_MESSAGE."""
    mock_planner.return_value = PlannerOutput(
        intent="general_inquiry",
        service_type="general",
        next_step="knowledge",
    )
    mock_get_retriever.return_value.retrieve.return_value = []

    initial_state: PakAssistState = {
        "user_input": "What is the best recipe for chicken karahi?",
        "intent": "",
        "service_type": "",
        "next_step": "",
        "response": "",
        "sources": [],
    }

    result = app_graph.invoke(initial_state)
    assert result["response"] == NO_CONTEXT_MESSAGE
    assert result["sources"] == []
    mock_gemini_call.assert_not_called()


@patch("backend.graph.graph.run_planner")
@patch("backend.agents.knowledge.extract_text_from_image")
@patch("backend.agents.knowledge._call_gemini")
def test_4_image_handling_flow(mock_knowledge_gemini, mock_extract_image, mock_planner, app_graph, tmp_path):
    """Test 4: Image input is processed via multimodal extraction and retrieved."""
    mock_planner.return_value = PlannerOutput(
        intent="renew_service",
        service_type="driving_license",
        next_step="knowledge",
    )

    fake_img = tmp_path / "license_slip.jpg"
    fake_img.write_bytes(b"fake image data")

    mock_extract_image.return_value = "Learner permit token number 48291 expires next month."
    mock_knowledge_gemini.return_value = "Your token number is 48291 expiring next month."

    initial_state: PakAssistState = {
        "user_input": "What is the learner permit token number in my upload?",
        "intent": "",
        "service_type": "",
        "next_step": "",
        "response": "",
        "uploaded_files": [str(fake_img)],
        "sources": [],
    }

    result = app_graph.invoke(
        initial_state,
        config={"configurable": {"thread_id": "image-upload-session"}},
    )

    assert result["response"] == "Your token number is 48291 expiring next month."
    assert any(s["origin"] == "user_upload" for s in result["sources"])


@patch("backend.graph.graph.run_planner")
@patch("backend.agents.knowledge._call_gemini")
def test_5_pdf_handling_flow(mock_knowledge_gemini, mock_planner, app_graph, tmp_path):
    """Test 5: PDF input is processed via PyMuPDF and retrieved."""
    pytest.importorskip("fitz")
    import fitz

    mock_planner.return_value = PlannerOutput(
        intent="apply_for_service",
        service_type="passport",
        next_step="knowledge",
    )

    pdf_path = tmp_path / "instructions.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Urgent passport delivery is 3 working days.")
    doc.save(str(pdf_path))
    doc.close()

    mock_knowledge_gemini.return_value = "Urgent delivery takes 3 working days."

    initial_state: PakAssistState = {
        "user_input": "How many days for urgent delivery in this document?",
        "intent": "",
        "service_type": "",
        "next_step": "",
        "response": "",
        "uploaded_files": [str(pdf_path)],
        "sources": [],
    }

    result = app_graph.invoke(
        initial_state,
        config={"configurable": {"thread_id": "pdf-upload-session"}},
    )

    assert result["response"] == "Urgent delivery takes 3 working days."
    assert any(s["origin"] == "user_upload" for s in result["sources"])


@patch("backend.graph.graph.run_planner")
def test_6_action_and_clarification_routes_preserved(mock_planner, app_graph):
    """Test 6: Action and Clarification routes remain functional."""
    # Test action route
    mock_planner.return_value = PlannerOutput(
        intent="service_center_lookup",
        service_type="driving_license",
        next_step="action",
    )
    action_result = app_graph.invoke({
        "user_input": "Find a driving license office in Attock",
        "intent": "",
        "service_type": "",
        "next_step": "",
        "response": "",
    })
    assert action_result["next_step"] == "action"
    assert "Attock Driving Licensing Branch" in action_result["response"]

    # Test clarification route
    mock_planner.return_value = PlannerOutput(
        intent="unknown",
        service_type="unknown",
        next_step="clarify",
    )
    clarify_result = app_graph.invoke({
        "user_input": "hello help me",
        "intent": "",
        "service_type": "",
        "next_step": "",
        "response": "",
    })
    assert clarify_result["response"] == "Please clarify which government service you need."
