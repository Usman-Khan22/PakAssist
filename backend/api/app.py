import os
import shutil
import tempfile

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Form
)
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp"
}
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.agents.planner import PlannerError
from backend.api.runtime import invoke_graph
from backend.api.schemas import (
    ChatRequest,
    ChatResponse,
    SessionResponse
)


app = FastAPI(
    title="PakAssist API",
    description="HTTP API for the PakAssist LangGraph backend",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


sessions = set()


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post(
    "/sessions",
    response_model=SessionResponse
)
def create_session():

    session_id = uuid4().hex

    sessions.add(session_id)

    return {
        "session_id": session_id
    }


@app.post(
    "/chat",
    response_model=ChatResponse
)
def chat(request: ChatRequest):

    if request.session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    try:
        result = invoke_graph(
            message=request.message,
            session_id=request.session_id
        )

    except PlannerError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Planner failed: {exc}"
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="PakAssist failed to process the request"
        )

    return {
        "session_id": request.session_id,
        "response": result.get("response", ""),
        "sources": result.get("sources") or []
    }

@app.post(
    "/sessions/{session_id}/upload",
    response_model=ChatResponse
)
async def upload_file(
    session_id: str,
    file: UploadFile = File(...),
    message: str = Form(...)
):

    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    if not message.strip():
        raise HTTPException(
            status_code=400,
            detail="Please provide a question about the uploaded file"
        )


    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is missing"
        )

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type"
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp_file:

            shutil.copyfileobj(
                file.file,
                temp_file
            )

            temp_path = temp_file.name

        result = invoke_graph(
            message=message,
            session_id=session_id,
            uploaded_files=[temp_path]
        )

        return {
            "session_id": session_id,
            "response": result.get("response", ""),
            "sources": result.get("sources") or []
        }

    except PlannerError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Planner failed: {exc}"
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="PakAssist failed to process the uploaded file"
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)