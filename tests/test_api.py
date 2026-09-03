import os

import pytest
from fastapi.testclient import TestClient

import backend.api.app as api_module


client = TestClient(
    api_module.app
)


@pytest.fixture(autouse=True)
def reset_sessions():

    api_module.sessions.clear()

    yield

    api_module.sessions.clear()


def create_session():

    response = client.post(
        "/sessions"
    )

    assert response.status_code == 200

    return response.json()["session_id"]


def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok"
    }


def test_create_session():

    response = client.post(
        "/sessions"
    )

    assert response.status_code == 200

    data = response.json()

    assert "session_id" in data

    assert data["session_id"] in api_module.sessions


def test_chat_invalid_session():

    response = client.post(
        "/chat",
        json={
            "session_id": "invalid-session",
            "message": "Passport requirements",
        },
    )

    assert response.status_code == 404


def test_chat_empty_message():

    session_id = create_session()

    response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "   ",
        },
    )

    assert response.status_code == 400


def test_chat_success(
    monkeypatch,
):

    session_id = create_session()

    def fake_invoke_graph(
        message,
        session_id,
        uploaded_files=None,
    ):
        return {
            "response": "Test response",
            "sources": [],
        }

    monkeypatch.setattr(
        api_module,
        "invoke_graph",
        fake_invoke_graph,
    )

    response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "Passport requirements",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["session_id"] == session_id

    assert data["response"] == "Test response"

    assert data["sources"] == []


def test_upload_invalid_session():

    response = client.post(
        "/sessions/invalid-session/upload",
        data={
            "message": "Analyze this image"
        },
        files={
            "file": (
                "test.jpg",
                b"fake-image",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 404


def test_upload_unsupported_file_type():

    session_id = create_session()

    response = client.post(
        f"/sessions/{session_id}/upload",
        data={
            "message": "Analyze this document"
        },
        files={
            "file": (
                "notes.txt",
                b"hello",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Unsupported file type"
    )


def test_upload_empty_message():

    session_id = create_session()

    response = client.post(
        f"/sessions/{session_id}/upload",
        data={
            "message": "   "
        },
        files={
            "file": (
                "test.jpg",
                b"fake-image",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 400


def test_upload_too_large(
    monkeypatch,
):

    session_id = create_session()

    monkeypatch.setattr(
        api_module,
        "MAX_UPLOAD_SIZE_BYTES",
        10,
    )

    large_file = b"a" * 20

    response = client.post(
        f"/sessions/{session_id}/upload",
        data={
            "message": "Analyze this image"
        },
        files={
            "file": (
                "large.jpg",
                large_file,
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 413


def test_upload_success(
    monkeypatch,
):

    session_id = create_session()

    received = {}

    def fake_invoke_graph(
        message,
        session_id,
        uploaded_files=None,
    ):

        received["message"] = message
        received["session_id"] = session_id
        received["uploaded_files"] = uploaded_files

        assert uploaded_files
        assert len(uploaded_files) == 1
        assert os.path.exists(
            uploaded_files[0]
        )

        return {
            "response": "Uploaded file processed",
            "sources": [
                {
                    "label": "Uploaded file",
                    "origin": "user_upload",
                    "service": None,
                    "section": "image",
                    "source_url": None,
                    "confidence": None,
                }
            ],
        }

    monkeypatch.setattr(
        api_module,
        "invoke_graph",
        fake_invoke_graph,
    )

    response = client.post(
        f"/sessions/{session_id}/upload",
        data={
            "message": (
                "Analyze this uploaded image"
            )
        },
        files={
            "file": (
                "test.jpg",
                b"fake-image-content",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["response"]
        == "Uploaded file processed"
    )

    assert (
        received["session_id"]
        == session_id
    )

    temp_path = received[
        "uploaded_files"
    ][0]

    assert not os.path.exists(
        temp_path
    )


def test_chat_internal_error_is_safe(
    monkeypatch,
):

    session_id = create_session()

    def broken_graph(*args, **kwargs):
        raise RuntimeError(
            "SECRET INTERNAL ERROR"
        )

    monkeypatch.setattr(
        api_module,
        "invoke_graph",
        broken_graph,
    )

    response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "Passport help",
        },
    )

    assert response.status_code == 500

    data = response.json()

    assert (
        data["detail"]
        == "PakAssist failed to process the request"
    )

    assert (
        "SECRET INTERNAL ERROR"
        not in response.text
    )