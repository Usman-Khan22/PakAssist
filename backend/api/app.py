import io
import os
import shutil
import tempfile
import wave
from uuid import uuid4

from google import genai
from google.genai import errors, types
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


def _tts_wav(response):
    """Preserve native WAV; wrap Gemini's legacy mono PCM when necessary."""
    candidates = response.candidates or []
    parts = candidates[0].content.parts if candidates and candidates[0].content else []
    for part in parts or []:
        blob = part.inline_data
        if blob is None or not blob.data:
            continue
        data = blob.data
        mime, *parameters = (blob.mime_type or "").lower().split(";")
        if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
            with wave.open(io.BytesIO(data), "rb") as audio:
                if audio.getnframes() == 0:
                    raise ValueError("Empty WAV")
            return data
        if mime.strip() not in {"audio/l16", "audio/pcm"}:
            raise ValueError("Unsupported audio format")
        params = dict(p.strip().split("=", 1) for p in parameters if "=" in p)
        rate = int(params.get("rate", "24000"))
        if rate <= 0 or int(params.get("channels", "1")) != 1 or len(data) % 2:
            raise ValueError("Invalid PCM format")
        output = io.BytesIO()
        with wave.open(output, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(rate)
            audio.writeframes(data)
        return output.getvalue()
    raise ValueError("Provider returned no audio")


def _generate_speech(text, api_key):
    # Client lifetime and all synchronous network work stay in the worker thread.
    with genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=60000,
            retry_options=types.HttpRetryOptions(
                attempts=2, initial_delay=1, http_status_codes=[429, 503],
            ),
        ),
    ) as client:
        response = client.models.generate_content(
            model=os.getenv("TTS_MODEL", "gemini-3.8-flash-lite-tts"),
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=os.getenv("TTS_VOICE", "Iapetus"),
                        ),
                    ),
                ),
            ),
        )
        return _tts_wav(response)


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

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Text-to-speech is not configured",
        )

    try:
        audio = await run_in_threadpool(_generate_speech, text, api_key)
    except errors.APIError as exc:
        raise HTTPException(
            status_code=503 if exc.code in {429, 503} else 502,
            detail="Text-to-speech provider is unavailable" if exc.code in {429, 503}
            else "Text-to-speech generation failed",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Text-to-speech generation failed",
        ) from exc

    return Response(
        content=audio,
        media_type="audio/wav",
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
