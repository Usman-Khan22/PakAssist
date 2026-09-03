# PakAssist - Architecture

## Implementation Status

PakAssist is a backend-only, multi-turn CLI assistant built on LangGraph. Its
implemented capabilities are:

- Gemini-backed structured planning;
- conditional Knowledge, Action, and Clarification routing;
- grounded multimodal RAG over trusted knowledge and ephemeral uploads;
- grounded requirements checklists and verified fee lookup inside the
  Knowledge path;
- an Action Agent with dataset-backed service-center lookup and deterministic
  appointment simulation;
- service-specific Citizen Journey / Progress Tracking; and
- short-lived conversational state for location, office selection, contextual
  knowledge follow-ups, simulated bookings, and assistance progress.

There is no HTTP API, frontend, database, authentication, long-term memory,
live government appointment integration, map integration, or voice interface.

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
    |      |-- Broad service goal -> Journey orientation
    |      `-- Knowledge Agent
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
    |   Action Agent
    |      |-- Service Center Lookup -> static office JSON datasets
    |      |-- Check Slots -> Appointment Simulator -> demo seed JSON
    |      |-- Book Slot -> Appointment Simulator -> session-local bookings
    |      `-- Journey Summary -> per-service journey state
    |
    `-- Clarification

Successful grounded/deterministic assistance
    |
    v
Per-service Citizen Journey state in the same checkpoint
```

Each graph invocation still reaches `END`, but the CLI invokes the same
compiled graph repeatedly with one stable thread ID. The in-memory checkpointer
merges state between turns in that thread.

Checklist Builder and Fee Lookup are not Action Agent capabilities. They are
specialized grounded response modes selected by the Knowledge Agent after RAG
retrieval. The Action Agent is a separate dispatch layer supporting
`service_center_lookup`, `check_slots`, `book_slot`, and `journey_summary`.

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

The current session logic intentionally supports these narrow cases:

1. **Missing service-center location.** When Action lookup needs a location,
   it stores `pending_clarification="location"` and the original query. A reply
   such as `Karachi` is combined with the pending request, while its previous
   service and Action route are retained. The pending fields are then cleared.
2. **Service-ambiguous fee follow-up.** The Planner still evaluates a question
   such as `How much does it cost?`. If it identifies a fee request but returns
   an unknown service, the planner graph node may reuse a known, non-unknown
   `service_type` from the same checkpointed thread and route to Knowledge as
   `fee_lookup`.
   Requirements/checklist follow-ups use the same safe service inheritance.
3. **Appointment office selection.** Multiple center matches are retained in
   `office_options` with `pending_clarification="office"`. A later office name,
   numeric choice, or simple ordinal resolves the selection.
4. **Simulated booking flow.** The selected office, configured demo date, and
   booked slot keys survive across turns in the same thread. This enables slot
   checking, booking, and duplicate-booking prevention within the session.
5. **Journey continuation.** Broad goals establish an empty service journey,
   successful assistance updates it, and progress questions can reuse the
   active service when the new turn omits it.

Current-turn information has precedence over checkpointed context. An explicit
new service or location triggers a fresh lookup and replaces incompatible
`office_options`, `selected_office`, and appointment context. Retained options
are reused only for dependent turns such as `Show appointments for the first
one`.

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
| `pending_clarification` | Missing datum for supported continuation: `location` or `office` |
| `pending_request` | Original request retained while location or office selection is pending |
| `office_options` | Ordered office names offered for appointment selection |
| `selected_office` | Office selected for the simulated appointment workflow |
| `appointment_date` | Configured demo date for the selected office |
| `booked_slots` | Session-local simulator slot keys already booked in this thread |
| `journeys` | Per-service mapping from journey step to assistance status |

`SourceRef` contains `label`, `origin`, `service`, `section`, `source_url`, and
`confidence`. Knowledge and Action both use this existing source contract; no
second citation mechanism exists.

`JourneyProgress` is `TypedDict(total=False)` with `requirements`, `fees`,
`service_center`, and `appointment` string fields. The observed statuses are
`reviewed`, `located`, `selected`, `availability_checked`, and `demo_booked`,
as appropriate to each step.

## Planner and Conditional Routing

`backend/agents/planner.py` calls Gemini through `google-genai` and validates
native structured output with Pydantic `PlannerOutput`:

- `intent`: a short snake-case goal, including established values such as
  `service_center_lookup`, `check_slots`, `book_slot`,
  `requirements_checklist`, `fee_lookup`, `service_journey`, and
  `journey_summary`;
- `service_type`: normally `passport`, `driving_license`, or `unknown`; and
- `next_step`: `knowledge`, `action`, `appointment`, or `clarify`.

The prompt directs requirements/checklist and fee/cost questions to Knowledge;
service-center, simulated slot-check, and simulated booking requests to Action;
progress summaries to Action; broad apply/get/renew goals to the Knowledge
branch as `service_journey`; and ambiguous requests to Clarification.
English, Urdu, and Roman Urdu are accepted at prompt level, but there is no
complete localization subsystem.

`backend/graph/graph.py` routes as follows:

- unknown intent or service -> Clarification;
- known `next_step="knowledge"` -> Knowledge Agent;
- known `next_step="action"` -> Action Agent; and
- all other values -> Clarification.

For exact `check_slots` and `book_slot` intents, the Planner graph node
normalizes routing to Action and may inherit a known service from the current
session. `next_step="appointment"` remains a reserved Planner value; there is
no separate appointment graph node because the simulator is an Action
capability.

Broad `apply_for_service`/`renew_service` outputs that were classified as
Action are normalized to `service_journey` and Knowledge. The Knowledge graph
node returns a short supported-capabilities orientation and initializes the
service journey without calling RAG or advancing progress. This does not submit
an application. Progress requests are normalized to `journey_summary` and use
the Action Agent's deterministic summary dispatch.

The Planner node also implements the contextual continuation rules above.
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

Only a nonempty generated checklist backed by selected trusted requirement
chunks records `requirements="reviewed"` for the current service journey.
Retrieval/selection failures do not advance it.

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

Only a nonempty answer generated from reliable fee chunks records
`fees="reviewed"`. Missing or unverified fee information does not advance the
journey.

The current passport KB contains high-confidence official fee tables with MRP,
Fast Track, e-Passport, validity/page/urgency distinctions, surcharges, and a
warning to re-confirm current values. The driving-license KB explicitly marks
its numeric fee ranges medium-confidence and unverified. Consequently, current
driving-license fee requests return a reliable-fee-not-found response rather
than quoting those ranges. When matching but unreliable fee context exists,
its source may still be shown to explain the limitation; Gemini generation is
skipped.

## Action Agent, Service Center Lookup, and Appointment Simulator

`backend/agents/action.py` selects and dispatches `service_center_lookup`,
`check_slots`, `book_slot`, and `journey_summary`. Unsupported Action requests
receive a safe unsupported-action response. Checklist and fee requests do not
use this agent.

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

A successful center lookup records `service_center="located"`, or `"selected"`
when only one office is returned. Failed and unsupported lookups do not advance
progress.

### Deterministic appointment simulation

`backend/services/appointment_simulator.py` owns appointment schedule and
booking rules, separate from Action dispatch. It reads immutable demo schedules
from `data/appointment_slots.json`, matches exact service/office pairs,
normalizes common requested times to `HH:MM`, filters session-booked slots, and
creates deterministic `DEMO-...` references for successful simulations.

The workflow reuses Service Center Lookup for location and office discovery.
One match is selected automatically; multiple matches prompt for an office;
missing location uses the existing continuation. Unsupported offices, missing
times, absent slots, and duplicate bookings produce safe deterministic results.

This is explicitly a prototype: it does not call a government system, scrape
live availability, create a real reservation, or mutate the seed JSON.
Appointment responses label results as simulated, direct users to official
systems for real appointments, and return an empty `sources` list because demo
slot data is not trusted government evidence.

Office selection accepts an explicit active office name, numeric selection,
or simple ordinal from first/`1st` through tenth/`10th`. References are checked
against the current `office_options`; an out-of-range selection returns a
bounded clarification and never falls back to an older selection. An explicit
new location is resolved before retained context, replacing stale options and
clearing `selected_office`/`appointment_date` when multiple new matches exist.

Successful slot checking records `appointment="availability_checked"`, which
is distinct from a booking. Only a simulator result with status `booked`
records `appointment="demo_booked"`.

## Citizen Journey / Progress Tracking

`backend/services/journey.py` provides the lightweight journey model and its
operations. `journeys` is keyed by service, so passport and driving-license
assistance does not contaminate the other service. Updates copy the mapping and
change one supported step; the LangGraph checkpointer then retains that mapping
for later turns in the same thread.

Broad service goals initialize an empty mapping for the active service and
return an orientation toward documents, fees, centers, and demo appointments.
They do not mark a step complete. `Show my progress`, `What have we done`, and
`What's left`-style requests are recognized by intent or a small phrase set and
formatted by `journey_summary()` through the Action route. Missing steps are
shown as not reviewed/located/booked; availability checking is shown as an
intermediate demo status.

This is assistance progress only. It never proves that documents were
submitted, fees were paid, an office was visited, an application was filed, or
a real government appointment was booked.

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
- ordinary Knowledge responses remaining unformatted;
- contextual fee follow-up using the checkpointed service;
- appointment office selection, slot discovery, booking, invalid slots, and
  duplicate-booking prevention;
- regression coverage for existing routes after appointment integration;
- per-service journey initialization and updates;
- progress summaries, incomplete steps, and session isolation;
- broad service-goal orientation and contextual checklist/fee continuation;
- current-turn location/service precedence and stale-office invalidation; and
- valid, out-of-range, and replacement office references.

## Current Limitations and Planned Work

The following are not implemented:

- live appointment availability or real government booking integration;
- appointment schedules beyond the small deterministic demo seed;
- persistent simulated bookings across process restarts or between users;
- persistent sessions across process restarts or database-backed memory;
- broad conversational history and general follow-up intent resolution;
- generic continuation for every Clarification response;
- reliable driving-license fee amounts;
- complete driving-license service-center coverage;
- GPS/map-based nearest-office calculation;
- HTTP API, frontend, or production upload UI;
- database, authentication, or multi-user storage;
- voice integration;
- broader Urdu/regional-language polish; and
- additional services beyond passport and driving license.

Journey/progress tracking is implemented through Milestone 10. No later
agent/backend milestone is established here. RAG latency profiling and
optimization remains a technical improvement area.
