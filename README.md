# PakAssist

FastAPI + LangGraph + Gemini + RAG backend with the completed React/TypeScript/Vite frontend in frontend/.

## Run locally (PowerShell, from repository root)

Backend:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8001
```

Configure GEMINI_API_KEY and OPENROUTER_API_KEY only in the root .env. Existing model overrides remain supported. The existing RAG index is used; rebuild if necessary with the script in scripts/build_index.py.

Frontend (second terminal):

```powershell
npm.cmd ci --prefix frontend
npm.cmd run dev --prefix frontend
```

Open http://localhost:5173. Copy frontend/.env.example to frontend/.env.local only if overriding VITE_API_BASE_URL. Never put provider keys in Vite variables.

## Integration

- GET /health: backend availability.
- POST /sessions: lazy session creation, shared by typed chat, microphone and uploads; session ID persists in sessionStorage.
- POST /chat: session_id + message; response is displayed unchanged, with source cards.
- POST /sessions/{session_id}/upload: multipart file + message. PDF/JPG/JPEG/PNG/WEBP. No invented upload size limit.
- POST /voice/tts: text to audio/mpeg. Voice recognition uses en-PK, noncontinuous recognition and interim transcripts. The migrated makeVoiceFriendly helper shortens speech without an LLM call.

Conversation history survives route navigation in memory. Reload preserves the backend session ID but resets the visible history. Clear chat starts a fresh session on the next message. Backend memory is process-local; after a backend restart, clear an expired chat explicitly.

Service catalog and informational pages remain static. Journey, office and demo appointment requests use chat because the API exposes no separate structured dashboard endpoint. The dashboard links to a journey-progress question in the shared conversation.

## Verification

```powershell
npm.cmd run build --prefix frontend
node --test frontend/integration.test.cjs
.\venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

The Node integration tests require Node 24 (stripTypeScriptTypes). They check session reuse, exact answer preservation, multipart fields, network errors, recognition settings, duplicate final-event prevention and isolated TTS failures.

See INTEGRATION_REPORT.md for results and manual checks still needed.
