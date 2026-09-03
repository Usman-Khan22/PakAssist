# PakAssist FastAPI Integration and RAG Fix Proposal

**For:** Usman and the PakAssist backend team  
**Status:** Integration progress and proposed changes only  
**Important:** This document does not apply any changes to the RAG, agents, graph, or state code.

## 1. Purpose

This document records:

- what has been completed in `backend/api`;
- how to install and run the API;
- how to test it through FastAPI Swagger UI;
- the current uploaded-image routing failure;
- findings from the latest `app.py`, `runtime.py`, Retriever, vector-store, multimodal, checklist, fee, journey, and architecture files; and
- the smallest proposed fix that preserves the current PakAssist architecture.

The main design conclusion is:

> FastAPI should continue mapping its `session_id` to LangGraph's configurable `thread_id`. A `session_id` field should not be added to `PakAssistState`. Upload-vector isolation should instead use the existing LangGraph thread identity.

## 2. Current FastAPI Integration Progress

The latest API implementation provides these endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Confirm that the API process is running |
| `POST` | `/sessions` | Generate an in-process session identifier |
| `POST` | `/chat` | Send a normal text turn to PakAssist |
| `POST` | `/sessions/{session_id}/upload` | Upload an image/PDF and ask a question about it |

The current request flow is:

```text
Frontend or Swagger UI
        |
        | session_id
        v
FastAPI backend/api/app.py
        |
        v
backend/api/runtime.py
        |
        | configurable.thread_id = session_id
        v
One compiled LangGraph + one InMemorySaver
        |
        v
Planner -> Knowledge / Action / Clarification
```

`runtime.py` builds the graph and `InMemorySaver` once when the server process starts. Each request invokes the same graph, while `thread_id` separates checkpointed conversations:

```python
config = {
    "configurable": {
        "thread_id": session_id
    }
}
```

The per-turn input currently contains the user message, optional upload paths, and a fresh source list:

```python
turn_state = {
    "user_input": message,
    "uploaded_files": uploaded_files,
    "sources": [],
}
```

This is the correct separation of responsibilities. The API owns the HTTP-facing `session_id`; LangGraph uses the same value as its runtime `thread_id`; `PakAssistState` remains focused on conversation and business state.

### Current limitations of API sessions

- `sessions` is an in-memory Python set.
- LangGraph checkpoints use `InMemorySaver`.
- Sessions and conversation state disappear when Uvicorn restarts.
- Multiple Uvicorn worker processes would not share the same `sessions` set or checkpointer.
- There is currently no database, authentication, or durable session storage.

For the present prototype, run one Uvicorn worker and treat sessions as process-local.

## 3. Setup and Run Instructions

Run all commands from the repository root—the directory containing `requirements.txt` and the `backend` folder.

### 3.1 Create and activate a virtual environment (recommended)

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If the environment already exists, only run the activation command.

### 3.2 Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The upload endpoint uses multipart form data. `python-multipart` must therefore be present in `requirements.txt`. The existing project also requires its LangGraph, FastAPI/Uvicorn, Gemini, FAISS, sentence-transformers, Pillow, PyMuPDF, and environment-loading dependencies.

### 3.3 Configure environment variables

Make sure the project environment contains the values already required by the Planner and multimodal pipeline, especially:

```dotenv
GEMINI_API_KEY=your_key_here
```

Existing optional settings such as `GEMINI_MODEL`, `KB_INDEX_DIR`, `RAG_TOP_K`, and `RAG_MIN_SCORE` should retain the values expected by the current project. Do not commit secrets.

The official FAISS index must also already exist at the configured index directory. If it is missing or stale, rebuild it using the project's existing index-building procedure before testing RAG.

### 3.4 Start Uvicorn

```powershell
python -m uvicorn backend.api.app:app --reload --port 8001
```

Use `--reload` for local development only. Keep one worker because all current sessions and checkpoints are in memory.

Open:

```text
Swagger UI: http://127.0.0.1:8001/docs
Health URL: http://127.0.0.1:8001/health
```

Stop the server with `Ctrl+C`.

## 4. Swagger UI Test Workflow

### Step 1: Check API health

1. Open `GET /health`.
2. Select **Try it out**.
3. Select **Execute**.

Expected HTTP `200` response:

```json
{
  "status": "ok"
}
```

This only confirms that FastAPI is running; it does not fully test Gemini, FAISS, or LangGraph.

### Step 2: Create a session

1. Open `POST /sessions`.
2. Select **Try it out** and **Execute**.
3. Copy the returned `session_id`.

Example:

```json
{
  "session_id": "f38c645b9d8b4ed893c4aabbccddeeff"
}
```

The ID is generated by the backend using `uuid4().hex`. The frontend may later provide and retain this value itself, but it must use the same value for every turn in one conversation. In the current API, only IDs registered by `POST /sessions` are accepted.

### Step 3: Test normal chat

1. Open `POST /chat`.
2. Select **Try it out**.
3. Paste the session ID and a message.

```json
{
  "session_id": "f38c645b9d8b4ed893c4aabbccddeeff",
  "message": "What documents do I need for a passport?"
}
```

4. Select **Execute**.

The response should include the same `session_id`, the assistant `response`, and any `sources` used.

### Step 4: Test an upload

1. Open `POST /sessions/{session_id}/upload`.
2. Select **Try it out**.
3. Put the copied ID in the `session_id` path field.
4. Choose a supported `.pdf`, `.png`, `.jpg`, `.jpeg`, or `.webp` file.
5. Enter the multipart `message` field.
6. Select **Execute**.

Recommended diagnostic message:

```text
For my passport service, tell me what information is visible in this uploaded image.
```

Use a dummy or redacted test document, not a real citizen's CNIC or other sensitive document.

The current upload transport performs this sequence:

```text
UploadFile
  -> validate filename extension
  -> copy to a temporary file
  -> invoke_graph(..., uploaded_files=[temp_path])
  -> graph finishes
  -> delete temporary file in finally
```

The temp file therefore still exists while multimodal extraction runs and is removed afterward.

## 5. Concrete Test Cases

Record the HTTP status, response, and `sources` for every case.

### A. API validation

| Test | Request | Expected result |
|---|---|---|
| Health | `GET /health` | `200`, `{"status":"ok"}` |
| Unknown session | `/chat` with an unregistered ID | `404`, `Session not found` |
| Empty chat | Whitespace-only `message` | `400`, `Message cannot be empty` |
| Unsupported upload | Upload `.txt` or `.exe` | `400`, `Unsupported file type` |
| Empty upload question | Whitespace-only form `message` | `400` with the upload-question validation message |

### B. Knowledge, Action, and multi-turn behavior

Use one newly created session unless a case says otherwise.

1. **Passport checklist**

   ```text
   What documents do I need for a passport?
   ```

   Expected: Knowledge route, trusted checklist formatting, and official knowledge-base sources.

2. **Passport fee**

   ```text
   What is the passport fee?
   ```

   Expected: Knowledge route and only trusted high-confidence fee context.

3. **Service-center lookup**

   ```text
   Find a passport office in Karachi.
   ```

   Expected: Action route and matching dataset-backed office results.

4. **Location continuation**

   First turn:

   ```text
   Find a passport office.
   ```

   Second turn, with the same session ID:

   ```text
   Karachi
   ```

   Expected: the second request resumes the first request using the same LangGraph checkpoint.

5. **Thread isolation**

   - Session A: `Find a passport office.`
   - Session B: `Karachi`

   Expected: Session B must not resume Session A's pending request.

6. **Appointment simulation**

   Test service-center selection, slot checking, and demo booking using the current supported phrasing/data. Expected results must be explicitly described as simulated rather than real government bookings.

### C. Upload diagnostics

1. Restart the development server to begin with a clean process-global Retriever.
2. Create a fresh session.
3. Upload a dummy image containing a distinctive, harmless phrase or value.
4. Ask:

   ```text
   For my passport service, tell me what information is visible in this uploaded image.
   ```

5. Inspect `sources` for an entry with:

   ```json
   {
     "origin": "user_upload"
   }
   ```

6. Create a second session and confirm that it cannot retrieve the first session's distinctive value. This isolation test is expected to expose the current process-global upload-store bug.

Do not use wording such as `requirements`, `what documents do I need`, `checklist`, `fee`, `cost`, or `price` for the basic upload diagnostic. Those words intentionally activate specialized trusted-only modes.

## 6. Current Failing Upload Query

Observed request:

```text
For my passport service, tell me what information is visible in this uploaded image.
```

Observed response:

```text
Please clarify which government service you need
```

This result indicates a Planner/routing problem before it proves a multimodal extraction or retrieval failure. The request explicitly mentions `passport`, but the graph still reaches Clarification. We should inspect the Planner output (`intent`, `service_type`, and `next_step`) for this exact request and verify how the graph normalizes/routes it.

The failure should be separated into stages:

```text
1. HTTP upload accepted?                 Yes, based on current app.py flow
2. Temp path passed to graph?            Yes, based on app.py/runtime.py
3. Planner selects Knowledge/passport?   Currently failing or being normalized incorrectly
4. Image text extracted?                 Not proven by the clarification response
5. Upload chunks indexed/retrieved?      Not proven by the clarification response
6. user_upload source reaches answer?    Not proven; also affected by ranking
```

A narrow diagnostic should temporarily log or capture the Planner result and selected route for this test without exposing uploaded content or secrets. Do not respond to the symptom by weakening trusted checklist/fee filters.

## 7. Findings from the Latest Code

### 7.1 Correct: `session_id` already maps to LangGraph `thread_id`

`backend/api/runtime.py` performs the required mapping through the runnable config. This is the correct mechanism for LangGraph checkpoint identity.

Therefore:

- do not add `session_id` to `PakAssistState`;
- do not duplicate transport identifiers inside business state; and
- keep using one stable ID across the related `/chat` and `/upload` calls.

### 7.2 Bug: the upload `user_store` is process-global, not per session

The latest Retriever contains one mutable field:

```python
self.user_store = None
```

Its comment and docstring call this store “per-session” and also “request-scoped,” but the actual lifecycle is neither. The Knowledge Agent caches a Retriever by official index directory, so many FastAPI sessions reuse the same Retriever object and therefore the same mutable `user_store`.

Current effective lifecycle:

```text
One Uvicorn process
    -> one cached Retriever for KB_INDEX_DIR
        -> one shared user_store
            -> uploads from Session A, B, C, ...
```

This could leak retrieved upload content across sessions. It was less visible in the original one-process/one-conversation CLI model, but a multi-session HTTP server makes the mismatch important.

The official persisted knowledge-base store may remain process-shared and read-only. Only mutable user-upload stores require thread-level isolation.

### 7.3 Weakness: upload chunks can lose the global top-k competition

The Retriever currently:

1. gets up to `top_k` results from the official store;
2. gets up to `top_k` results from the upload store;
3. combines and sorts all results; and
4. truncates the combined list back to `top_k`.

Consequently, all final positions can be occupied by official KB chunks even when the current request includes an upload. The image may be successfully extracted and indexed but still never reach grounded generation.

For ordinary upload questions, the retrieval policy should reserve or deliberately blend upload candidates rather than relying only on a single global cutoff. This must not override checklist and fee trust rules.

### 7.4 Intentional and correct: checklist filtering is trusted-only

`select_requirement_chunks()` keeps only chunks that:

- originate from `knowledge_base`;
- match the selected service; and
- come from a required-document section.

An uploaded file must not become an authoritative source for official government requirements. Therefore, a prompt such as “check this CNIC for my passport application requirements” can intentionally produce only official KB sources. That behavior does not demonstrate that extraction failed, and the trusted filter should remain.

### 7.5 Intentional and correct: fee filtering is trusted-only

`select_fee_chunks()` also keeps matching official knowledge-base fee sections and permits numeric generation only from reliable/high-confidence material. User-uploaded claims must not become official fees. Preserve this behavior.

### 7.6 Structurally sound: multimodal extraction and vector store

The current multimodal implementation:

- loads image pixels before closing the file;
- uses Gemini with automatic function calling disabled;
- extracts normal PDF text through PyMuPDF;
- rasterizes likely scanned pages and sends those page images to Gemini; and
- removes temporary page images afterward.

The FAISS wrapper uses normalized-vector inner-product search and maintains text/metadata beside the index. Neither file is the first place to change for the present bug.

### 7.7 Later API hardening needed in `app.py`

The current API works as a prototype but should later be cleaned up:

- remove duplicate `FastAPI` and `HTTPException` imports;
- group constants/imports consistently;
- enforce a maximum upload size before an unbounded file is written;
- close the `UploadFile` in `finally` (for example, `await file.close()`);
- retain guaranteed deletion of the temporary path;
- validate content safely rather than trusting extension alone where practical;
- log server-side exceptions with a request/session correlation value while returning generic messages to clients;
- never include raw exception text, file contents, secrets, or local temp paths in a `500` response; and
- consider concurrency protection for mutable in-memory session/upload structures.

The current special handling for `PlannerError` is useful, but `detail=f"Planner failed: {exc}"` should be reviewed before production because exception text may disclose internal/provider information. Return a safe public message and log the detailed cause server-side.

## 8. Proposed Minimal Fix

The target design is:

```text
Shared for the process
  official persisted knowledge-base FAISS store (read-only)

Scoped by LangGraph configurable.thread_id
  thread A -> upload FAISS store A
  thread B -> upload FAISS store B
  thread C -> upload FAISS store C
```

### 8.1 Pass runtime config to the Knowledge node

Allow the Knowledge graph node to receive LangGraph `RunnableConfig`, read:

```python
thread_id = config["configurable"]["thread_id"]
```

and pass that value into the Knowledge/Retriever upload operations. The exact node signature should follow the LangGraph version already pinned by the project.

This preserves the existing API-to-LangGraph contract and avoids adding infrastructure identity to `PakAssistState`.

### 8.2 Separate shared KB retrieval from thread-scoped upload storage

Use one shared official store plus a mapping of upload stores keyed by the existing thread ID. Conceptually:

```python
upload_stores: dict[str, FaissVectorStore]
```

The Retriever APIs would accept a scope/thread key when adding or retrieving user content. Any mapping must be protected appropriately for concurrent requests.

The prototype also needs an explicit lifecycle policy. At minimum, clear the upload store when a session is deleted/expired or when the server restarts. If session deletion is not yet implemented, document the process-local lifetime and add bounded eviction/TTL before production to avoid unbounded memory growth.

### 8.3 Preserve upload candidates for normal upload questions

When a request includes or references user uploads, retrieve official and upload candidates separately and apply an explicit blend—for example, reserve at least one qualifying upload result while filling remaining slots by score. The exact quota should be covered by tests and must still honor `RAG_MIN_SCORE`.

Do not use this blending rule for trusted checklist or fee facts. Those modes should continue selecting only approved official chunks.

### 8.4 Diagnose Planner routing independently

Before changing prompts broadly:

1. reproduce the exact failing image query;
2. capture the Planner's validated `intent`, `service_type`, and `next_step`;
3. confirm the graph router decision;
4. add a regression test requiring `passport` + uploaded-image inspection wording to reach Knowledge; and
5. make the smallest prompt/normalization change supported by that evidence.

This routing correction is separate from upload-store isolation and top-k blending. All three can exist independently.

## 9. Proposed Files to Change

### First implementation phase: RAG isolation and upload retrieval

| File | Proposed reason |
|---|---|
| `backend/rag/retriever.py` | Replace the single mutable `user_store` lifecycle with thread-scoped upload storage; add explicit upload-aware result blending |
| `backend/agents/knowledge.py` | Obtain/use the current runtime thread scope and pass it to Retriever upload/retrieval operations |
| `backend/graph/graph.py` | Only if needed to pass `RunnableConfig` into the Knowledge node cleanly |
| Relevant tests under `tests/` | Add cross-session isolation, upload inclusion, trusted-filter, and routing regressions |

Depending on the current graph-node signatures, `graph.py` may require only a small wiring change or none at all.

### Separate later phase: API cleanup and hardening

| File | Proposed reason |
|---|---|
| `backend/api/app.py` | Import cleanup, upload-size enforcement, `UploadFile` closure, safer logging/error responses, and possibly lifecycle endpoints |
| `requirements.txt` | Only if an explicitly chosen validation/logging dependency is genuinely needed; do not add packages unnecessarily |
| API tests | Cover size limits, cleanup, invalid files, safe errors, and normal upload success |

## 10. Files Intentionally Not Changed

Unless new test evidence points elsewhere, do not modify:

| File | Reason |
|---|---|
| `backend/graph/state.py` | No `session_id` field is needed; runtime config already carries thread identity |
| `backend/api/runtime.py` | Existing session-to-thread mapping and one-time graph/checkpointer construction are correct |
| `backend/agents/planner.py` | Do not change until the exact Planner output for the failing query is captured; then apply only a focused routing fix if required |
| `backend/agents/action.py` | Upload knowledge retrieval is not an Action concern |
| `backend/rag/vector_store.py` | FAISS wrapper is structurally suitable for the proposed scoped stores |
| `backend/rag/multimodal.py` | Image/PDF extraction path is structurally correct; first verify it with targeted tests |
| `backend/services/checklist_builder.py` | Trusted official-only requirements filter is intentional |
| `backend/services/fee_lookup.py` | Trusted high-confidence fee filtering is intentional |
| `backend/services/journey.py` | Journey tracking is unrelated to upload isolation/routing |

If the Planner regression proves that `planner.py` is the source of the clarification route, move it into the proposed-change list with a narrowly tested prompt or normalization adjustment. It should not be edited speculatively.

## 11. Proposed Implementation Order

1. **Baseline and reproduce**
   - Run the current API from a clean server process.
   - Execute health, session, chat, same-session continuation, and cross-session isolation tests.
   - Reproduce the exact upload-to-clarification query.

2. **Add regression tests before changing behavior**
   - Explicit passport image-inspection query routes to Knowledge.
   - Upload from thread A is unavailable to thread B.
   - A qualifying upload chunk survives normal upload retrieval.
   - Checklist and fee selectors still reject `user_upload` chunks as authoritative facts.

3. **Fix runtime-config propagation**
   - Make the existing `configurable.thread_id` available to the Knowledge/Retriever path without adding it to `PakAssistState`.

4. **Implement upload-store isolation**
   - Keep the official KB shared.
   - Key mutable upload stores by thread ID.
   - Add safe concurrent access and a documented cleanup policy.

5. **Fix normal upload ranking**
   - Blend/reserve qualifying upload candidates for ordinary upload questions.
   - Preserve score thresholds and source metadata.

6. **Apply the smallest routing fix supported by evidence**
   - Update Planner prompt/normalization only if the recorded Planner result proves it is necessary.

7. **Run focused and full test suites**
   - Confirm existing checklist, fees, action, appointment, journey, source, and continuation behavior has not regressed.

8. **Harden `app.py` separately**
   - Clean imports, limit upload size, close `UploadFile`, improve validation, and keep error details server-side.

## 12. Acceptance Criteria

The proposed work is complete when:

- the API starts with the documented Uvicorn command;
- Swagger can create a session and use it for `/chat` and `/sessions/{session_id}/upload`;
- the exact passport image-inspection query reaches Knowledge rather than Clarification;
- a dummy uploaded image produces relevant content and a `user_upload` source when it passes the score threshold;
- one session can never retrieve another session's uploaded chunks;
- same-session multi-turn checkpoint behavior still works;
- no `session_id` field has been added to `PakAssistState`;
- checklist answers still use only trusted official requirement chunks;
- fee answers still use only approved official high-confidence fee chunks;
- existing Action, appointment, and journey behavior remains intact; and
- API errors do not expose internal exception details or uploaded content.

## 13. Summary for Usman

The FastAPI integration is already correctly carrying a frontend/API `session_id` into LangGraph as `configurable.thread_id`; state changes are not required for session identity. Normal chat, uploads, and temporary-file cleanup are wired through the API. The observed upload question currently goes to Clarification, so Planner output and graph routing must be diagnosed independently from extraction/retrieval.

The main RAG architecture issue is that the cached Retriever owns one mutable upload `user_store`, making it process-global despite being documented as per-session/request-scoped. A second weakness is that upload chunks can be removed by the combined top-k cutoff. The minimal solution is to retain one shared official KB, scope upload stores by the existing LangGraph thread ID passed through runtime config, and explicitly preserve qualifying upload candidates for normal upload questions. Trusted checklist and fee filtering should remain unchanged.

