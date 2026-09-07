# PakAssist

PakAssist is an agentic AI civic-service assistant that helps Pakistani citizens navigate Passport and Driving Licence services through conversation. Government information is often scattered across portals and documents; PakAssist brings curated guidance, document inspection and office lookup into one English/Urdu interface, with Roman Urdu conversation and optional voice interaction.

This is a hackathon prototype for guidance, not a government portal. It does not submit applications or make real bookings.

## Key Features

- Passport and Driving Licence guidance: requirements, document checklists, fees and next steps grounded in curated information.
- Session-aware follow-ups, service journeys and progress summaries through chat.
- Dataset-backed office lookup, including multi-city queries and source references.
- Clearly labelled simulated appointment availability and booking flows.
- PDF, JPG/JPEG, PNG and WEBP inspection with session-isolated retrieval of extracted content.
- English, Urdu and Roman Urdu conversation; responsive React frontend with English/Urdu UI switching.
- Microphone input and response read-aloud, with typed chat available when voice is unsupported.

## How It Works

The frontend sends a message to FastAPI using a shared session ID. LangGraph runs a Gemini Planner that classifies `intent`, `service_type` and `next_step`, then routes the request to Knowledge/RAG, an Action handler or clarification. The response and available sources return to chat; voice requests can also play a shortened version.

### Architecture

```text
React + TypeScript + Vite
  | typed input / recognized speech / file + question
FastAPI
  | session_id -> LangGraph thread_id (in-memory checkpointer)
LangGraph
  +-- Gemini Planner (intent, service, route; retries + fallback)
  +-- Knowledge: Markdown -> MiniLM embeddings -> FAISS -> Gemini answer
  |             uploaded PDF/image -> extracted text -> session retrieval
  +-- Actions: JSON office datasets, journeys, simulated appointments
  +-- Clarification
  |
Response + sources -> Chat UI
  +-- Shortened text -> /voice/tts -> OpenRouter Fish Audio -> MP3
```

**Office lookup reads JSON directly; it does not use embeddings.** Markdown guidance uses the FAISS index. Rebuilding embeddings updates guidance; editing office JSON requires restarting the backend to refresh its cache.

### Session Memory

One lazily created `session_id` is reused for typed messages, voice transcripts, uploads and follow-ups. The backend maps it to a LangGraph `thread_id`, retaining service context and journey state. The frontend stores the ID in `sessionStorage`; visible history survives route navigation but resets on a full page reload.

Memory is process-local, not a persistent account. A backend restart clears sessions and extracted upload memory: select **Clear chat** before starting another conversation. Use one backend process for this demo.

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Frontend | React, TypeScript, Vite, React Router, Lucide React, CSS |
| API and orchestration | Python, FastAPI, Pydantic, LangGraph, python-dotenv |
| Generation | Google Gen AI SDK (`google-genai`), Gemini Planner and Knowledge models |
| Retrieval and documents | Sentence Transformers / `all-MiniLM-L6-v2`, FAISS, NumPy, PyMuPDF, Pillow |
| Voice | Browser SpeechRecognition; HTTPX and OpenRouter Fish Audio TTS |

## Project Structure

```text
PakAssist/
|-- backend/
|   |-- api/             # FastAPI routes, schemas, session runtime
|   |-- agents/          # Planner, Knowledge and Action agents
|   |-- graph/           # LangGraph workflow and state
|   |-- rag/             # Loading, chunking, embeddings, retrieval, extraction
|   `-- services/        # Offices, journeys, fees, checklists, demo appointments
|-- frontend/
|   |-- src/             # Pages, language support and shared API/voice services
|   |-- integration.test.cjs
|   `-- .env.example
|-- knowledge_base/      # Curated Markdown and office JSON datasets
|-- scripts/build_index.py
|-- data/                # Locally generated FAISS index (not committed)
|-- tests/               # Backend regression tests
|-- requirements.txt
`-- .env.example
```

## Prerequisites

- Python 3 with `venv` and pip. The repository does not pin a Python version; local integration was tested with Python 3.14.
- Node.js and npm. The locked Vite toolchain requires Node `^20.19.0 || >=22.12.0`; Node 24 was used locally and supports the frontend test harness.
- Git, internet access, a Gemini API key, and an OpenRouter API key for TTS. Model access and provider availability depend on your account.

## Installation

Run these commands in Windows PowerShell. If you already have the repository, start from its root instead of cloning again.

```powershell
git clone https://github.com/Usman-Khan22/PakAssist.git
cd PakAssist
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
npm.cmd ci --prefix frontend
```

These commands use the virtual environment's executable directly, so activation is optional. If preferred, activate it with `.\venv\Scripts\Activate.ps1`. On macOS/Linux, use `venv/bin/python` and `npm` instead of the Windows executable names.

## Environment Setup

For a fresh checkout, copy the examples, then edit the root `.env` with your own keys. Do not overwrite an existing configured `.env`.

```powershell
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env
```

| Variable | Purpose / source default |
| --- | --- |
| `GEMINI_API_KEY` | Required for Planner, generated answers and image extraction |
| `OPENROUTER_API_KEY` | Required for TTS; optional for typed-only use |
| `PLANNER_MODEL` | Primary Planner: `gemini-3.5-flash-lite` |
| `PLANNER_FALLBACK_MODEL` | Fallback Planner: `gemini-3.1-flash-lite` |
| `GEMINI_MODEL` | Knowledge generation and multimodal extraction: `gemini-2.5-flash` |
| `KB_DIR` | Markdown input directory: `knowledge_base` |
| `KB_INDEX_DIR` | Saved retrieval index: `data/faiss_index` |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` |
| `RAG_TOP_K` | Default retrieval count: `5`; some routes request more |
| `RAG_MIN_SCORE` | Retrieval threshold: `0.15` |
| `VITE_API_BASE_URL` | **Frontend env only:** `http://127.0.0.1:8001` (also the fallback) |

`GEMINI_MODEL` is the actual Knowledge-model setting; `KNOWLEDGE_MODEL` is not used. TTS currently uses `fish-audio/s2.1-pro-free:free` in the backend source, with no environment override.

### Build the Knowledge Index

The generated index is Git-ignored, so build it before using RAG on a fresh checkout:

```powershell
.\venv\Scripts\python.exe scripts/build_index.py
```

This loads Markdown from `KB_DIR`, embeds its chunks and writes `index.faiss` and `store.pkl` under `KB_INDEX_DIR`. The first run may download the embedding model. Repeat after Markdown or embedding-model changes, then restart the backend. Office JSON changes do not need an embedding rebuild.

## Running PakAssist

Run both commands from the repository root in **separate terminals**, and keep both terminals running.

**Terminal 1 - backend:**

```powershell
.\venv\Scripts\python.exe -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8001
```

API: http://127.0.0.1:8001

Health: http://127.0.0.1:8001/health

Swagger: http://127.0.0.1:8001/docs

**Terminal 2 - frontend:**

```powershell
npm.cmd run dev --prefix frontend
```

Open **http://localhost:5173**. Vite uses a strict port, and backend CORS allows the localhost/127.0.0.1 frontend origins on port 5173.

If either port is already in use, check whether the application is already running. Do not launch a second copy. To restart, press `Ctrl+C` in the original terminal, then rerun its command. Clear chat after restarting the backend.

## Quick Test

Open chat and send these messages one at a time in the same conversation:

```text
Assalam Walekum
bhai mujhe driving licence renew karvana hai meri madad karo
documents kya chahiye?
aur fee kitni hai?
```

Follow-ups should retain Driving Licence context. If verified fee data is unavailable, the assistant should say so. Also try `find me passport offices near Islamabad Lahore and Karachi`, attach a supported file with a question, or test the microphone in a supported browser.

## API Overview

| Method / endpoint | Contract |
| --- | --- |
| `GET /health` | Returns backend status |
| `POST /sessions` | Creates a session; returns `session_id` |
| `POST /chat` | JSON `{ "session_id": "...", "message": "..." }`; returns session ID, response and sources |
| `POST /sessions/{session_id}/upload` | Multipart **`file` + `message`**, both required; returns the chat response contract |
| `POST /voice/tts` | JSON `{ "text": "..." }`; returns `audio/mpeg` |

Uploads accept `.pdf`, `.png`, `.jpg`, `.jpeg` and `.webp`. TTS accepts nonempty text up to 5,000 characters. Journey and appointment interactions use chat; there is no separate structured dashboard API.

## Voice Assistant

Browser `SpeechRecognition` / `webkitSpeechRecognition` uses `en-PK`, `continuous = false` and `interimResults = true`. This is intentional for English, Roman Urdu and mixed speech with terms such as CNIC and Passport; recognition quality still depends on the browser.

The final transcript uses the same chat flow and session as typed input. The full answer appears in chat, then `makeVoiceFriendly` shortens it without another LLM request. `/voice/tts` sends that text to OpenRouter Fish Audio and the browser plays the MP3. TTS failure reports a playback error without hiding a successful text answer.

Allow microphone access when prompted. Unsupported browsers retain typed chat; physical microphone and audible playback need testing on the demo machine.

## Language Support

The backend detects English, Urdu script and Roman Urdu, retaining the language preference for short follow-ups. Generation instructions request the corresponding style; mixed input is handled heuristically rather than by a perfect-translation layer. Official names and terms may remain English. The frontend preserves backend answers exactly, and the English/Urdu UI switch changes interface copy independently; some error messages remain English.

## Demo / Prototype Notes

- Appointment slots and bookings are simulations, not live government reservations. Journey progress records guidance steps, not official application status.
- Office results come from curated datasets, not GPS distance ranking or live availability. Some addresses, hours and fee information are incomplete; confirm details with the linked authority.
- Gemini and TTS require internet access. Planner retry/fallback handles some transient failures; provider outages or unavailable models can still produce an error.
- Sessions and extracted upload content live in server memory. Temporary uploaded files are deleted after processing, but session-extracted content can remain until the backend exits.
- This local demo has no account authentication, durable session storage or production security hardening.

## Security

Keep Gemini and OpenRouter keys in the backend `.env` only. Never put them in `VITE_*` variables, which are public frontend configuration. `.env` files are Git-ignored; only safe examples should be committed. Supply your own credentials locally and use non-sensitive sample documents for a public demo: document extraction/generation can send content to Gemini, and spoken response text is sent to OpenRouter.

## Testing

From the repository root:

```powershell
.\venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
node --test frontend/integration.test.cjs
npm.cmd run build --prefix frontend
```

Backend tests cover routing, session continuity, grounded assistance, upload isolation, multilingual behavior and simulated actions. Frontend tests cover API contracts, session reuse, recognition settings and TTS-failure separation; they are isolated tests, not browser end-to-end tests. The build runs TypeScript checks before producing Vite assets. Use Node 24 for the frontend test harness.

Historical integration results and manual browser checks are recorded in [INTEGRATION_REPORT.md](INTEGRATION_REPORT.md). Its test counts describe that earlier run; use the commands above for the current checkout.
