# PakAssist - Project Context for AI Coding Agents

## Purpose

PakAssist is a backend-only assistant that helps Pakistani citizens navigate
government services. Current service coverage is passport and driving license.
Treat the repository implementation as the source of truth and develop
incrementally.

## Current Implementation

Completed capabilities:

- repository and backend foundation;
- shared LangGraph graph/state foundation;
- Gemini Planner Agent with Pydantic-validated structured output;
- conditional Knowledge, Action, and Clarification routing;
- terminal Clarification response for unknown or unsupported routes;
- trusted passport and driving-license Markdown knowledge base;
- section-aware multimodal RAG;
- Knowledge Agent integration and grounded Gemini generation;
- trusted source and confidence visibility;
- image and PDF user-upload extraction and retrieval;
- persistent official FAISS knowledge-base index;
- separate ephemeral, in-memory user-upload index;
- Action Agent dispatch foundation; and
- dataset-backed passport and driving-license service-center lookup.

Current graph:

```text
Planner
  |
  v
Conditional Router
  |-- Knowledge -> Knowledge Agent -> Multimodal RAG
  |-- Action -> Action Agent -> Service Center Lookup
  `-- Clarification
```

All downstream branches currently end after one graph invocation.

## Important Files

- `main.py`: single-query CLI entry point; accepts optional upload paths from
  command-line arguments and prints the response and sources.
- `backend/agents/planner.py`: Gemini structured classification into `intent`,
  `service_type`, and `next_step`.
- `backend/graph/graph.py`: LangGraph nodes and conditional routing.
- `backend/graph/state.py`: `PakAssistState` and `SourceRef` definitions.
- `backend/agents/knowledge.py`: retrieval orchestration, grounded generation,
  no-context fallback, and source construction.
- `backend/rag/`: Markdown loading/chunking, normalized MiniLM embeddings,
  FAISS stores, retrieval, and image/PDF extraction.
- `scripts/build_index.py`: rebuilds the persistent official FAISS index.
- `backend/agents/action.py`: Action selection, dispatch, response formatting,
  and service-center source construction.
- `backend/services/service_centers.py`: deterministic dataset loading,
  location extraction, and service-center filtering.
- `knowledge_base/`: trusted Markdown content and service-center JSON datasets.
- `tests/`: offline Planner/graph tests plus RAG and Action integration coverage.
- `ARCHITECTURE.md`: detailed architecture and limitations.

There is no `backend/main.py`; the current entry point is root `main.py`.

## Current State Contract

`PakAssistState` is a `TypedDict(total=False)` with these fields only:

- `user_input: str`
- `intent: str`
- `service_type: str`
- `next_step: str`
- `response: str`
- `uploaded_files: Optional[List[str]]`
- `sources: Optional[List[SourceRef]]`

`SourceRef` contains `label`, `origin`, `service`, `section`, `source_url`, and
`confidence`. The Planner writes the three classification fields. Knowledge
and Action write the response and sources.

## Routing and Agent Behavior

The Planner returns structured `intent`, `service_type`, and `next_step` data.
Unknown intent/service values route to Clarification. Known `knowledge` and
`action` decisions route to their real agents. Any other route, including the
currently unimplemented `appointment` decision, falls back to Clarification.
Service-center requests can use `intent="service_center_lookup"` and route to
Action.

The Knowledge Agent searches the persistent trusted index plus an optional
in-memory upload index, returns a safe fallback when no relevant chunks exist,
and otherwise asks Gemini to answer strictly from retrieved context. Source
origin, service, section, URL, and confidence metadata are preserved where
available.

The Action Agent currently supports only `service_center_lookup`. Lookup logic
is separate under `backend/services/`, reads the existing JSON files, performs
textual location/office matching, asks for city/region when missing, and
returns no result for locations absent from the data. Other actions receive a
safe unsupported-action response.

## RAG and AFC Constraints

- Preserve the single RAG implementation under `backend/rag/`; do not create a
  duplicate retrieval pipeline.
- The official knowledge-base index is persistent under `data/faiss_index/`
  and is rebuilt with `scripts/build_index.py`.
- User-upload content is indexed separately in memory and is never persisted
  into the official index. The current single-run CLI bounds it to the process.
- Section-aware Markdown loading, source/confidence metadata, normalized
  `sentence-transformers/all-MiniLM-L6-v2` embeddings, and FAISS `IndexFlatIP`
  are established architecture.
- Planner structured output, Knowledge generation, and multimodal Gemini
  extraction use direct `models.generate_content` calls with no tools and
  `automatic_function_calling.disable=True`.
- The AFC fix must remain intact. Do not introduce tools or AFC into existing
  RAG generation unless that architecture is explicitly redesigned.
- Grounded generation must not fill missing requirements, fees, or process
  details from general model knowledge.

## Action and Data Constraints

- Keep Action selection/formatting separate from service and dataset logic.
- Use the repository's passport and driving-license service-center datasets;
  do not scrape the web or add an external location API for lookup.
- Return only fields actually present in a record. Never hallucinate an
  address, phone, portal, confidence value, or nearby substitute.
- The driving-license dataset has only six records and is intentionally
  incomplete. Missing cities are a dataset limitation, not a lookup failure.
- There is no GPS, coordinate, distance, or map-based nearest-office feature.

## Current CLI Limitation

`main.py` reads one main user input and invokes the graph once per execution.
A Clarification response ends that invocation, so the user's follow-up must
currently start a new process. There is no conversational loop, accumulated
message history, or checkpointer integration.

## Completed Milestones

1. Repository/backend and LangGraph state foundation.
2. Structured Planner Agent.
3. Conditional routing and Clarification path.
4. Multimodal RAG foundation with persistent trusted index and ephemeral
   upload index.
5. Knowledge Agent integration and trusted source visibility.
6. Action Agent foundation and Service Center Lookup.

The current completed milestone is **Action Agent + Service Center Lookup**.

## Next Planned Milestone

**Multi-turn Conversational CLI / Session Flow**

The goal is to allow clarification and follow-up answers to continue within
the same conversation instead of requiring a new process execution.

Planned Action milestones after that:

1. Checklist Builder
2. Fee Lookup
3. Appointment Simulator

None of those later actions is implemented yet.

## Development Rules

- Keep each coding task focused on a small number of related features.
- Preserve the Planner -> conditional LangGraph routing design.
- Reuse existing agents and RAG modules instead of duplicating them.
- Add state fields only for a real current requirement.
- Keep comments short and purposeful.
- Do not add an API, frontend, database, authentication, or unrelated feature
  without an explicit milestone.
- Never hardcode or commit credentials; use environment configuration.
- Add focused tests and run the relevant/full suite before completion.

## Git and Branching Rules

- Do not commit directly to `main`.
- Work on feature branches.
- Keep commits focused on one logical change.
- Use conventional commit prefixes such as `feat:`, `fix:`, `docs:`, and
  `chore:`.
