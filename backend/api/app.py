import logging
import os
import tempfile
from uuid import uuid4

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from backend.agents.planner import PlannerError
from backend.api.runtime import invoke_graph
from backend.api.schemas import (
    ChatRequest,
    ChatResponse,
    SessionResponse,
)


logger = logging.getLogger(__name__)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

MAX_UPLOAD_SIZE_MB = int(
    os.getenv("MAX_UPLOAD_SIZE_MB", "10")
)

MAX_UPLOAD_SIZE_BYTES = (
    MAX_UPLOAD_SIZE_MB * 1024 * 1024
)

UPLOAD_CHUNK_SIZE = 1024 * 1024


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


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


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
def chat(request: ChatRequest):

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

    try:
        result = invoke_graph(
            message=request.message,
            session_id=request.session_id,
        )

    except PlannerError:
        logger.exception(
            "Planner failed during chat request. session_id=%s",
            request.session_id,
        )

        raise HTTPException(
            status_code=502,
            detail="Planner service failed",
        )

    except Exception:
        logger.exception(
            "Unexpected error while processing chat. session_id=%s",
            request.session_id,
        )

        raise HTTPException(
            status_code=500,
            detail="PakAssist failed to process the request",
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

    temp_path = None

    try:
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

        total_size = 0

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:

            temp_path = temp_file.name

            while True:

                chunk = await file.read(
                    UPLOAD_CHUNK_SIZE
                )

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"File exceeds the "
                            f"{MAX_UPLOAD_SIZE_MB} MB limit"
                        ),
                    )

                temp_file.write(chunk)

        result = await run_in_threadpool(
            invoke_graph,
            message,
            session_id,
            [temp_path],
        )

        return {
            "session_id": session_id,
            "response": result.get(
                "response",
                "",
            ),
            "sources": result.get(
                "sources"
            ) or [],
        }

    except HTTPException:
        raise

    except PlannerError:
        logger.exception(
            "Planner failed while processing upload. "
            "session_id=%s filename=%s",
            session_id,
            file.filename,
        )

        raise HTTPException(
            status_code=502,
            detail="Planner service failed",
        )

    except Exception:
        logger.exception(
            "Unexpected upload processing error. "
            "session_id=%s filename=%s",
            session_id,
            file.filename,
        )

        raise HTTPException(
            status_code=500,
            detail="PakAssist failed to process the uploaded file",
        )

    finally:

        try:
            await file.close()

        except Exception:
            logger.warning(
                "Failed to close uploaded file. "
                "session_id=%s",
                session_id,
                exc_info=True,
            )

        if temp_path and os.path.exists(temp_path):

            try:
                os.remove(temp_path)

            except OSError:
                logger.warning(
                    "Failed to delete temporary upload file: %s",
                    temp_path,
                    exc_info=True,
                )