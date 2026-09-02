# PakAssist - Architecture

## Implementation Status

PakAssist is a backend-only, multi-turn CLI assistant built on LangGraph. Its
implemented capabilities are:

- Gemini-backed structured planning;
- conditional Knowledge, Action, and Clarification routing;
- grounded multimodal RAG over trusted knowledge and ephemeral uploads;
- grounded requirements checklists and verified fee lookup inside the
  Knowledge path;
- an Action Agent with dataset-backed service-center lookup; and
- short-lived conversational state for location clarification and contextual
  fee follow-ups.

There is no HTTP API, frontend, database, authentication, long-term memory,
appointment workflow, map integration, or voice interface.

## Current Architecture

```text
Multi-turn CLI session
    |
    | one UUID thread_id + InMemorySaver
    v
Planner / contextual continuation
    |
    v
Conditional Router
    |
    |-- Knowledge
    |      |
    |      v
    |   Knowledge Agent
    |      |
    |      v
    |   Multimodal RAG
    |      |-- Persistent trusted Markdown index
    |      `-- Ephemeral in-memory user-upload index
    |      |
    |      |-- Normal grounded answer
    |      |-- Required-document chunks -> Checklist Builder
    |      `-- Trusted fee chunks -> Fee Lookup formatter
    |
    |-- Action
    |      |
    |      v
    |   Action Agent -> Service Center Lookup -> JSON datasets
    |
    `-- Clarification
```

Each graph invocation still reaches `END`, but the CLI invokes the same
compiled graph repeatedly with one stable thread ID. The in-memory checkpointer
merges state between turns in that thread.

Checklist Builder and Fee Lookup are not Action Agent capabilities. They are
specialized grounded response modes selected by the Knowledge Agent after RAG
retrieval. The Action Agent remains a separate dispatch layer whose only
implemented action is `service_center_lookup`.

## Multi-Turn CLI and Session Lifecycle

The entry point is repository-root `main.py`; there is no `backend/main.py`.
`run_cli()`:

1. compiles the graph with LangGraph `InMemorySaver`;
2. creates one random UUID thread ID for the conversation;
3. repeatedly reads input from `PakAssist>`;
4. invokes the graph with the same thread ID on each turn;
5. prints the response and available source labels, origins, and confidence;
6. ignores blank input; and
7. exits cleanly on `exit`, `quit`, or EOF.

Command-line file paths are supplied as `uploaded_files` on the first turn.
Later turns explicitly set that input field to `None`. Session checkpoints are
process-local and disappear when the CLI exits; they are not long-term memory.
A different thread ID does not inherit a previous thread's pending state.

### Supported contextual continuation

The current session logic intentionally supports two narrow cases:

1. **Missing service-center location.** When Action lookup needs a location,
   it stores `pending_clarification="location"` and the original query. A reply
   such as `Karachi` is combined with the pending request, while its previous
   service and Action route are retained. The pending fields are then cleared.
2. **Service-ambiguous fee follow-up.** The Planner still evaluates a question
   such as `How much does it cost?`. If it identifies a fee request but returns
   an unknown service, the planner graph node may reuse a known, non-unknown
   `service_type` from the same checkpointed thread and route to Knowledge as
   `fee_lookup`.

This is not general conversational intent resolution. Generic clarification
answers and arbitrary follow-ups are not reconstructed from full message
history.

## Shared State

`backend/graph/state.py` defines `PakAssistState` as
`TypedDict(total=False)` with exactly these fields:

| Field | Purpose |
|---|---|
| `user_input` | Current user text, or the reconstructed pending location request |
| `intent` | Planner-produced high-level goal |
| `service_type` | Planner-produced or safely inherited service context |
| `next_step` | Planner-produced downstream decision |
| `response` | User-facing downstream response |
| `uploaded_files` | Optional list of image/PDF paths for Knowledge retrieval |
| `sources` | Optional trusted knowledge, upload, or service-center references |
| `pending_clarification` | Missing datum for supported continuation; currently `location` |
| `pending_request` | Original request retained while location is pending |

`SourceRef` contains `label`, `origin`, `service`, `section`, `source_url`, and
`confidence`. Knowledge and Action both use this existing source contract; no
second citation mechanism exists.

## Planner and Conditional Routing

`backend/agents/planner.py` calls Gemini through `google-genai` and validates
native structured output with Pydantic `PlannerOutput`:

- `intent`: a short snake-case goal, including established values such as
  `service_center_lookup`, `requirements_checklist`, and `fee_lookup`;
- `service_type`: normally `passport`, `driving_license`, or `unknown`; and
- `next_step`: `knowledge`, `action`, `appointment`, or `clarify`.

The prompt directs requirements/checklist and fee/cost questions to Knowledge,
service-center requests to Action, and ambiguous requests to Clarification.
English, Urdu, and Roman Urdu are accepted at prompt level, but there is no
complete localization subsystem.

`backend/graph/graph.py` routes as follows:

- unknown intent or service -> Clarification;
- known `next_step="knowledge"` -> Knowledge Agent;
- known `next_step="action"` -> Action Agent; and
- all other values, including `appointment`, -> Clarification because no
  appointment node exists yet.

The Planner node also implements the two contextual continuation rules above.
It does not replace the Planner with a separate memory agent.

### Gemini structured-output constraint

Planner output uses `response_mime_type="application/json"`,
`response_schema=PlannerOutput`, no tools, and
`automatic_function_calling.disable=True`. The response is parsed with
`json.loads` and validated before reaching graph state. Failures become
`PlannerError`.

## Knowledge Agent and Multimodal RAG

`backend/agents/knowledge.py` orchestrates all knowledge-grounded behavior:

1. obtain the cached retriever for the persistent official index;
2. extract and index supported user uploads when provided;
3. select a normal, checklist, or fee retrieval query;
4. retrieve candidate chunks;
5. apply specialized trusted-section selection for checklist or fee mode;
6. return a safe fallback without generation when suitable context is absent;
7. generate only from the selected context; and
8. write `response` plus deduplicated `sources`.

Normal grounded generation explicitly forbids inventing missing requirements,
fees, or process steps. Low- and medium-confidence information must be
identified as uncertain. Knowledge generation uses no tools and keeps Gemini
automatic function calling disabled.

### RAG implementation

The single RAG implementation remains under `backend/rag/`:

- `loader.py` loads trusted Markdown by `##` section and propagates file-level
  source URL and confidence metadata;
- `chunker.py` preserves short sections and splits long sections with overlap;
- `embeddings.py` uses normalized
  `sentence-transformers/all-MiniLM-L6-v2` embeddings;
- `vector_store.py` uses FAISS `IndexFlatIP` and persists `index.faiss` plus
  the parallel text/metadata `store.pkl`;
- `retriever.py` merges ranked results from the persistent official index and
  optional in-memory upload index while retaining `knowledge_base` versus
  `user_upload` origins; and
- `multimodal.py` uses Gemini for PNG/JPG/JPEG/WebP extraction, PyMuPDF for
  textual PDFs, and Gemini image extraction for scanned/image-heavy PDF pages.

`scripts/build_index.py` rebuilds the official index from the Markdown files.
User uploads are never written into it. The service-center JSON files are not
part of semantic RAG and are read directly by the Action service.

All direct Gemini generation/extraction paths use no tools and explicitly
disable automatic function calling. The AFC fix must remain intact unless the
architecture is intentionally redesigned.

## Grounded Checklist Builder

`backend/services/checklist_builder.py` contains request detection, a
requirements-focused retrieval-query builder, trusted section selection, and
formatting instructions. It contains no passport or driving-license document
facts.

For a checklist request, the Knowledge Agent:

1. performs a requirements-focused RAG retrieval;
2. keeps only `knowledge_base` chunks for the current `service_type` whose
   section is a `Required Documents` section;
3. passes only those chunks to the checklist formatting prompt;
4. formats supported items as an actionable `☐` list; and
5. builds `sources` from those same selected chunks.

Adult/minor, conditional, renewal, and province-specific distinctions are
preserved when present in context. Uncertainty must remain visible. If no
trusted required-document section is retrieved, the builder returns a
checklist-specific information-not-found response instead of inventing items.
Questions such as validity, eligibility, or process explanations remain normal
Knowledge responses unless their intent/query matches the focused checklist
detector.

## Grounded Fee Lookup

`backend/services/fee_lookup.py` contains fee request detection, a fee-focused
retrieval-query builder, trusted fee-section selection, and grounded formatting
instructions. It contains no fee amounts.

For a fee request, the Knowledge Agent:

1. retrieves fee-focused RAG candidates;
2. keeps `knowledge_base` fee sections for the current service;
3. permits numeric generation only from chunks marked high confidence and not
   containing unverified information;
4. asks Gemini to preserve every retrieved category and distinction rather
   than selecting or collapsing one amount; and
5. builds `sources` from the selected fee chunks.

The current passport KB contains high-confidence official fee tables with MRP,
Fast Track, e-Passport, validity/page/urgency distinctions, surcharges, and a
warning to re-confirm current values. The driving-license KB explicitly marks
its numeric fee ranges medium-confidence and unverified. Consequently, current
driving-license fee requests return a reliable-fee-not-found response rather
than quoting those ranges. When matching but unreliable fee context exists,
its source may still be shown to explain the limitation; Gemini generation is
skipped.

## Action Agent and Service Center Lookup

`backend/agents/action.py` selects and dispatches actions. Its only implemented
action is `service_center_lookup`; unsupported Action requests receive a safe
unsupported-action response. Checklist and fee requests do not use this agent.

`backend/services/service_centers.py` separately reads:

- 180 passport office records; and
- 6 intentionally incomplete driving-license records.

Lookup performs deterministic textual matching over available region/province,
office-name, and address data. It can recognize explicit locations, asks for a
city or region when missing, returns no result for an unsupported location,
and formats only fields present in the matched records. Results may populate
the shared `sources` field.

There is no scraping, external location API, GPS, coordinate, distance, or map
calculation. Missing driving-license cities such as Lahore reflect incomplete
dataset coverage and must never be replaced with a different city's office.

## Testing

The test suite mocks external Gemini calls where appropriate and covers:

- Planner parsing and graph routing;
- Knowledge, Action, and Clarification preservation;
- official and uploaded multimodal RAG retrieval;
- safe no-context behavior;
- passport and driving-license service-center matches and failure cases;
- location clarification continuation and thread isolation;
- CLI `exit`/`quit` and stable thread IDs;
- grounded passport and driving-license checklists;
- high-confidence passport fee handling;
- refusal to generate from unverified driving-license fees;
- ordinary Knowledge responses remaining unformatted; and
- contextual fee follow-up using the checkpointed service.

## Current Limitations and Planned Work

The following are not implemented:

- appointment node, slot checking, or appointment booking simulator;
- persistent sessions across process restarts or database-backed memory;
- broad conversational history and general follow-up intent resolution;
- generic continuation for every Clarification response;
- reliable driving-license fee amounts;
- complete driving-license service-center coverage;
- GPS/map-based nearest-office calculation;
- journey/progress tracking;
- HTTP API, frontend, or production upload UI;
- database, authentication, or multi-user storage;
- voice integration;
- broader Urdu/regional-language polish; and
- additional services beyond passport and driving license.

The next planned milestone is **Appointment Simulator / Appointment
Workflow**, including an explicit appointment graph path and only the slot or
booking behavior approved for that milestone.
