import os
import shutil
import tempfile
from uuid import uuid4

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from backend.agents.planner import PlannerError
from backend.api.runtime import invoke_graph
from backend.api.schemas import (
    ChatRequest,
    ChatResponse,
    SessionResponse,
)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


app = FastAPI(
    title="PakAssist API",
    description="HTTP API for the PakAssist LangGraph backend",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


sessions = set()
sessions_with_messages = set()


class TTSRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/voice/tts")
async def voice_tts(request: TTSRequest):
    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty",
        )

    if len(text) > 5000:
        raise HTTPException(
            status_code=400,
            detail="Text cannot exceed 5000 characters",
        )

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Text-to-speech is not configured",
        )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            openrouter_response = await client.post(
                "https://openrouter.ai/api/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "fish-audio/s2.1-pro-free:free",
                    "input": text,
                    "response_format": "mp3",
                },
            )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Text-to-speech provider is unavailable",
        ) from exc

    if not openrouter_response.is_success:
        print(
            "OpenRouter TTS error:",
            openrouter_response.status_code,
            openrouter_response.text,
        )

        raise HTTPException(
            status_code=502,
            detail="Text-to-speech generation failed",
        )

    return Response(
        content=openrouter_response.content,
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-store"
        },
    )


@app.post(
    "/sessions",
    response_model=SessionResponse,
)
def create_session():
    session_id = uuid4().hex

    sessions.add(session_id)

    return {
        "session_id": session_id
    }


@app.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(request: ChatRequest):
    if request.session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty",
        )

    is_first_turn = (
        request.session_id not in sessions_with_messages
    )

    try:
        result = await run_in_threadpool(
            invoke_graph,
            request.message,
            request.session_id,
            None,
            is_first_turn,
        )

    except PlannerError as exc:
        print("Planner error:", exc)
        raise HTTPException(
            status_code=502,
            detail=f"Planner failed: {exc}",
        ) from exc

    except Exception as exc:
        print("PakAssist chat error:", exc)

        raise HTTPException(
            status_code=500,
            detail="PakAssist failed to process the request",
        ) from exc

    sessions_with_messages.add(
        request.session_id
    )

    return {
        "session_id": request.session_id,
        "response": result.get("response", ""),
        "sources": result.get("sources") or [],
    }


@app.post(
    "/sessions/{session_id}/upload",
    response_model=ChatResponse,
)
async def upload_file(
    session_id: str,
    file: UploadFile = File(...),
    message: str = Form(...),
):
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    if not message.strip():
        raise HTTPException(
            status_code=400,
            detail="Please provide a question about the uploaded file",
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is missing",
        )

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type",
        )

    is_first_turn = (
        session_id not in sessions_with_messages
    )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:

            shutil.copyfileobj(
                file.file,
                temp_file,
            )

            temp_path = temp_file.name

        result = await run_in_threadpool(
            invoke_graph,
            message,
            session_id,
            [temp_path],
            is_first_turn,
        )

        sessions_with_messages.add(
            session_id
        )

        return {
            "session_id": session_id,
            "response": result.get("response", ""),
            "sources": result.get("sources") or [],
        }

    except PlannerError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Planner failed: {exc}",
        ) from exc

    except Exception as exc:
        print("PakAssist upload error:", exc)

        raise HTTPException(
            status_code=500,
            detail="PakAssist failed to process the uploaded file",
        ) from exc

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)