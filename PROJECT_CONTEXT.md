# PakAssist - Project Context for AI Coding Agents

## Purpose and Current Status

PakAssist is a backend-only, multi-turn LangGraph CLI for Pakistani passport
and driving-license assistance. Treat repository code as the source of truth.

Completed capabilities:

- structured Gemini Planner and conditional Knowledge/Action/Clarification
  routing;
- terminal Clarification behavior;
- section-aware multimodal RAG over a persistent trusted FAISS index and a
  separate ephemeral upload index;
- grounded Knowledge Agent generation with trusted source/confidence visibility;
- image and PDF upload retrieval;
- Action Agent and dataset-backed Service Center Lookup;
- in-process multi-turn CLI sessions with LangGraph `InMemorySaver`;
- missing-location clarification continuation;
- contextual service reuse for fee follow-ups;
- grounded Checklist Builder;
- high-confidence trusted Fee Lookup with safe missing/unverified handling;
- deterministic demo appointment slot checking and booking; and
- multi-turn office selection with session-local duplicate-booking prevention.

## Current Graph

```text
Multi-turn CLI (one thread_id)
  -> Planner / contextual continuation
  -> Conditional Router
       |-- Knowledge -> Knowledge Agent -> Multimodal RAG
       |      |-- normal grounded answer
       |      |-- trusted requirements -> Checklist Builder
       |      `-- trusted fee sections -> Fee Lookup
       |-- Action -> Action Agent
       |      |-- Service Center Lookup
       |      |-- Check Slots -> Appointment Simulator
       |      `-- Book Slot -> Appointment Simulator
       `-- Clarification
```

Checklist and fee handling are Knowledge/RAG transformations, not Action Agent
capabilities. Action supports `service_center_lookup`, `check_slots`, and
`book_slot`.

## Important Files

- `main.py`: multi-turn CLI loop, `InMemorySaver`, UUID thread ID, optional
  first-turn uploads, source display, and `exit`/`quit` handling.
- `backend/graph/graph.py`: contextual continuation, nodes, and routing.
- `backend/graph/state.py`: `PakAssistState` and `SourceRef`.
- `backend/agents/planner.py`: validated `intent`, `service_type`, and
  `next_step` classification.
- `backend/agents/knowledge.py`: retrieval orchestration, response-mode
  selection, grounded generation, fallbacks, and sources.
- `backend/services/checklist_builder.py`: checklist detection, trusted
  required-section selection, and fact-free formatting rules.
- `backend/services/fee_lookup.py`: fee detection, confidence-gated fee-section
  selection, and fact-free formatting rules.
- `backend/rag/`: one shared Markdown/multimodal RAG implementation.
- `scripts/build_index.py`: rebuilds `data/faiss_index/`.
- `backend/agents/action.py`: Action dispatch and response/source formatting.
- `backend/services/service_centers.py`: JSON-backed location matching.
- `backend/services/appointment_simulator.py`: deterministic schedule lookup,
  time normalization, booking validation, and demo references.
- `data/appointment_slots.json`: immutable demo seed, not live government
  availability or trusted KB content.
- `knowledge_base/`: trusted Markdown and service-center JSON datasets.
- `tests/`: Planner, RAG, Action, session, checklist, fee, and appointment
  coverage.

There is no `backend/main.py`; the entry point is root `main.py`.

## Current State Contract

`PakAssistState` is `TypedDict(total=False)` with only:

- `user_input: str`
- `intent: str`
- `service_type: str`
- `next_step: str`
- `response: str`
- `uploaded_files: Optional[List[str]]`
- `sources: Optional[List[SourceRef]]`
- `pending_clarification: Optional[str]`
- `pending_request: Optional[str]`
- `office_options: Optional[List[str]]`
- `selected_office: Optional[str]`
- `appointment_date: Optional[str]`
- `booked_slots: Optional[List[str]]`

`SourceRef` contains `label`, `origin`, `service`, `section`, `source_url`, and
`confidence`.

## Session Behavior

One CLI process creates one in-memory checkpointer and stable UUID thread ID,
then invokes the graph repeatedly until `exit`, `quit`, or EOF. State does not
persist across restarts and different thread IDs do not share checkpoints.

Supported contextual continuation is intentionally narrow:

- a service-center request missing location records `pending_clarification`
  and `pending_request`; the next location answer resumes that Action request;
- a fee follow-up whose Planner output lacks a service can inherit a known
  `service_type` from the same thread and route to Knowledge.
- an appointment can reuse service context, perform location clarification,
  retain ordered office choices, accept a name/index/ordinal selection, check
  demo slots, and reject a slot already booked in the same thread.

There is no general message-history reasoning or generic clarification-resume
system.

## Grounding and Integration Rules

- Reuse the single RAG implementation under `backend/rag/`; do not duplicate
  retrieval or change the embedding/vector-store architecture casually.
- Official Markdown uses section-aware loading, normalized
  `sentence-transformers/all-MiniLM-L6-v2` embeddings, and FAISS
  `IndexFlatIP`. The official index is persistent; uploads remain separate and
  in memory.
- Checklist requests stay on the Knowledge route. Only trusted
  `Required Documents` chunks for the current service may supply checklist
  facts. `checklist_builder.py` must remain fact-free.
- Fee requests stay on the Knowledge route. Numeric generation requires a
  matching trusted fee section with high confidence and no unverified marker.
  `fee_lookup.py` must remain amount-free.
- Passport has high-confidence official fee tables but retains a re-confirmation
  warning. Driving-license numeric fees are medium-confidence/unverified, so
  current lookup returns reliable-fee-not-found instead of quoting them.
- Build `sources` from the chunks actually used. Keep the existing `SourceRef`
  contract; do not add a parallel citation mechanism.
- Normal Knowledge, Checklist Builder, Fee Lookup, Planner structured output,
  and multimodal extraction use direct Gemini calls with no tools and
  `automatic_function_calling.disable=True`. Preserve the AFC fix.
- Grounded generation must never fill missing requirements, fees, or process
  facts from model knowledge.

## Action and Dataset Rules

- Keep Action dispatch separate from service/data logic.
- Action supports `service_center_lookup`, `check_slots`, and `book_slot`;
  checklist and fee modes do not belong in Action.
- Use the existing passport and driving-license JSON datasets without scraping
  or an external location API.
- Never invent missing office fields or substitute another city.
- Driving-license center coverage is intentionally incomplete.
- There is no GPS, coordinate, distance, or map-based nearest-office feature.
- Keep appointment rules in `backend/services/appointment_simulator.py`, not
  in Action dispatch.
- Appointment seed data is deterministic demo data, not trusted knowledge or
  live availability. Never imply that a real government booking occurred.
- Bookings belong in checkpointed `booked_slots`; do not mutate the seed JSON
  or introduce global cross-session booking state.

## Completed Milestones

1. Repository/backend and LangGraph state foundation.
2. Structured Planner Agent.
3. Conditional routing and Clarification path.
4. Multimodal RAG with persistent trusted and ephemeral upload indexes.
5. Knowledge Agent integration and trusted source visibility.
6. Action Agent and Service Center Lookup.
7. Multi-Turn Conversational Session Flow.
8. Grounded Checklist Builder and Fee Lookup.
9. Appointment Simulator and multi-turn appointment workflow.

The current completed milestone is **Milestone 9: Appointment Simulator**.

## Current Limitations

- Appointment availability and booking are simulated from a small local seed;
  there is no live government integration or real reservation.
- Demo bookings are process/thread-local and disappear with the session.
- Sessions and checkpoints are process-local only.
- Context reuse covers pending location, office selection, appointment flow,
  and service-ambiguous fee follow-ups, not arbitrary conversation.
- Generic Clarification responses do not all support structured continuation.
- Driving-license fee data is not reliable enough for numeric answers.
- Driving-license service-center data is incomplete.
- No GPS/maps, progress tracking, API, frontend, production upload UI,
  database, authentication, voice, or broad localization layer exists.

## Next Planned Milestone

**Journey/Progress Tracking and Orchestration Refinement**

RAG latency profiling and optimization is also a technical improvement area,
not a completed capability.

## Development Rules

- Keep tasks focused on a small set of related features.
- Preserve Planner -> conditional routing and existing session behavior.
- Keep comments short and purposeful.
- Add state only for a concrete requirement.
- Never hardcode or commit credentials.
- Do not add unrelated APIs, databases, providers, or frameworks.
- Add focused tests and run the full suite.

## Git and Branching Rules

- Do not commit directly to `main`.
- Work on focused feature branches and commits.
- Use conventional prefixes such as `feat:`, `fix:`, `docs:`, and `chore:`.
