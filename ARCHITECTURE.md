# PakAssist - Architecture

## Implementation Status

PakAssist is currently a backend-only, single-turn CLI application built on
LangGraph. The implemented system includes structured planning, conditional
routing, a grounded multimodal Knowledge path, an Action Agent with
dataset-backed service-center lookup, and a clarification path.

There is no HTTP API, frontend, database, authentication, conversational
checkpointer, appointment workflow, or voice interface.

## Current Request Flow

```text
User Input
    |
    v
Planner
    |
    v
Conditional Router
    |-- Knowledge
    |      |
    |      v
    |   Knowledge Agent
    |      |
    |      v
    |   Multimodal RAG
    |      |-- Trusted persistent knowledge-base index
    |      `-- Ephemeral in-memory user-upload index
    |
    |-- Action
    |      |
    |      v
    |   Action Agent
    |      |
    |      v
    |   Service Center Lookup
    |
    `-- Clarification
```

Every selected downstream node is terminal for the current invocation and
connects to `END`.

## CLI Entry Point

The entry point is the repository-root `main.py`; there is no
`backend/main.py`.

For each execution, the CLI:

1. loads `.env` values;
2. builds the compiled LangGraph graph;
3. reads one user query from `PakAssist>`;
4. treats command-line arguments as optional uploaded file paths;
5. invokes the graph once; and
6. prints the response and, when present, source labels, origins, and
   confidence values.

`PlannerError` is reported as a CLI failure message. The CLI is not a
multi-turn conversation loop and does not retain a checkpointer-backed
conversation between inputs.

## Shared State

`backend/graph/state.py` defines `PakAssistState` as a `TypedDict` with
`total=False`. Its current fields are:

| Field | Purpose |
|---|---|
| `user_input` | Raw user query passed to the Planner and downstream agent |
| `intent` | Planner-produced high-level goal |
| `service_type` | Planner-produced government service, such as `passport` or `driving_license` |
| `next_step` | Planner-produced downstream decision |
| `response` | User-facing response written by the selected downstream node |
| `uploaded_files` | Optional list of image/PDF paths for the Knowledge path |
| `sources` | Optional source references for retrieved knowledge or service-center results |

`SourceRef` contains:

| Field | Purpose |
|---|---|
| `label` | User-facing source label |
| `origin` | `knowledge_base` or `user_upload` |
| `service` | Associated service, when known |
| `section` | Knowledge-base section, upload page, or service-center section |
| `source_url` | Source URL when supplied by the underlying content |
| `confidence` | Source confidence when available |

The Planner node owns `intent`, `service_type`, and `next_step`. Knowledge and
Action nodes write `response` and `sources`.

## Planner Agent

`backend/agents/planner.py` calls Gemini through the direct `google-genai`
client and validates the result with the Pydantic `PlannerOutput` model.
Planner output contains:

- `intent`: a short snake-case goal such as `apply_for_service`,
  `renew_service`, or `service_center_lookup`; `unknown` is used when unclear;
- `service_type`: the identified service, currently commonly `passport` or
  `driving_license`, or `unknown`; and
- `next_step`: one of `knowledge`, `action`, `appointment`, or `clarify`.

The prompt supports classification of English, Urdu, and Roman Urdu input and
prefers clarification rather than guessing. This is prompt-level language
handling, not a complete localization subsystem. Service-center and office
lookup requests are explicitly classified for the Action route.

Gemini structured output uses:

- `response_mime_type="application/json"`;
- `response_schema=PlannerOutput`;
- no tools; and
- `automatic_function_calling.disable=True`.

The response is parsed with `json.loads` and validated with Pydantic before it
enters graph state. API errors, empty responses, malformed JSON, and validation
failures become `PlannerError`. `GEMINI_API_KEY` and optional `GEMINI_MODEL`
come from the environment; the default model is `gemini-2.5-flash`.

## Conditional Routing

`backend/graph/graph.py` compiles the current graph:

```text
START -> Planner -> Conditional Router -> Knowledge / Action / Clarification -> END
```

Routing uses the validated Planner fields:

- an unknown `intent` or `service_type` always routes to Clarification;
- a known request with `next_step="knowledge"` routes to Knowledge;
- a known request with `next_step="action"` routes to Action; and
- every other value, including the currently unimplemented `appointment`
  path, routes to Clarification.

The Clarification node returns: `Please clarify which government service you
need.` It currently ends the invocation; the user must start another CLI
execution to answer it.

## Knowledge Agent

`backend/agents/knowledge.py` is the real Knowledge graph node. It:

1. obtains the persisted official knowledge-base retriever;
2. extracts and indexes supported uploaded files when supplied;
3. retrieves relevant chunks from the trusted and upload indexes;
4. returns a safe no-context response without calling Gemini when no chunks
   meet the retrieval threshold;
5. builds a context block containing origin, service, section, and confidence
   metadata;
6. asks Gemini to generate an answer using only that context; and
7. writes the grounded `response` and deduplicated `sources` to state.

The generation prompt prohibits filling gaps with general model knowledge and
requires low- or medium-confidence context to be identified as such. Knowledge
generation uses no tools and explicitly disables automatic function calling.

## Multimodal RAG

The single RAG implementation lives under `backend/rag/`:

- `loader.py` loads every knowledge-base Markdown file by `##` section. It
  applies file-level source URL and confidence metadata from the `Metadata`
  section to each retrievable section.
- `chunker.py` keeps short sections intact and splits only long sections on
  paragraph boundaries, with overlap and a hard-split fallback.
- `embeddings.py` lazily loads
  `sentence-transformers/all-MiniLM-L6-v2`, generates 384-dimensional vectors,
  and L2-normalizes them so inner product represents cosine similarity.
- `vector_store.py` wraps FAISS `IndexFlatIP`, stores text and metadata beside
  vectors, and saves/loads `index.faiss` plus `store.pkl`.
- `retriever.py` searches the persisted official index and, when present, an
  in-memory upload index. Results retain an origin of `knowledge_base` or
  `user_upload`, are filtered by a configurable minimum score, merged, ranked,
  and limited to the configured top-k.
- `multimodal.py` extracts text from images with Gemini and from PDFs
  page-by-page with PyMuPDF. PDF pages with little extractable text are
  rasterized and sent through the same Gemini image extraction path.

Supported image extensions are PNG, JPG/JPEG, and WebP. PDF and image
extraction do not persist user content. The upload FAISS store exists only in
memory; with the current one-query CLI, its lifetime is the current process.
The official knowledge-base store is separate and persists under
`data/faiss_index/`.

`scripts/build_index.py` rebuilds the official index by loading the Markdown
knowledge base, section-aware chunking it, embedding the chunks, and saving the
FAISS index and parallel metadata store. The service-center JSON datasets are
not part of this semantic index; the Action path reads them directly.

## Trusted Knowledge and Source Visibility

The trusted textual knowledge base currently covers passport and driving
license guidance in `knowledge_base/passport.md` and
`knowledge_base/driving_license.md`. Their source and confidence metadata flow
through chunks, retrieved context, and `SourceRef` entries.

User uploads remain distinguishable from official knowledge through their
`user_upload` origin and upload-specific document type. Official content and
uploads may both contribute retrieved chunks, but they are indexed separately
and user uploads are never written into the persistent official index.

## Action Agent

`backend/agents/action.py` is the real Action graph node. It determines the
requested action from Planner intent and lookup language in the user query,
then dispatches to the supported action implementation.

The only implemented action is `service_center_lookup`. Requests routed to
Action that do not select this action receive a safe response explaining that
the action is not supported yet and that service-center lookup is currently
available. This dispatch layer is intentionally separate from the dataset and
matching logic so additional actions can be added later without placing data
processing in the graph node.

## Service Center Lookup

`backend/services/service_centers.py` contains the deterministic lookup logic.
It reads the existing JSON datasets directly:

- `knowledge_base/passport_service_centers.json`: 180 passport offices with
  region, office name, address, phone when published, service, and source;
- `knowledge_base/driving_license_service_centers.json`: 6 intentionally
  incomplete records with province, office name, address, phone, hours,
  documents, services, portal, confidence, and source where available.

Lookup is textual rather than geographic. It extracts an explicit location
from phrases such as `in`, `near`, `at`, or `around`, or recognizes available
region/province and office names. Matching then checks the dataset's region or
province, office name, and address. Up to five matching records are returned.

The Action Agent formats only fields present in a matched record, including
address, phone, service information, hours, portal, confidence, and source as
available. It can also convert matched records into existing `SourceRef`
entries. It does not invent missing values.

- If no location is supplied, the response asks for a city or region.
- If a supplied location has no matching record, the response states that the
  current dataset has no result.
- If the service type has no configured dataset, the response states that
  lookup is unavailable for that service.

There is no web scraping, external location service, GPS, coordinate data,
distance calculation, or map integration. In particular, the driving-license
dataset is deliberately partial: a missing city such as Lahore is a data
coverage limitation, not evidence that the lookup failed or permission to
substitute a different city.

## Testing

The test suite uses mocked Gemini calls where appropriate and covers:

- structured Planner parsing for English and Roman Urdu examples;
- ambiguous Planner output and Clarification routing;
- Knowledge, Action, and Clarification graph routes;
- grounded passport and driving-license retrieval;
- safe no-context behavior without an unnecessary Gemini generation call;
- image extraction and retrieval from an in-memory upload index;
- text PDF extraction and retrieval;
- passport and driving-license service-center results;
- missing and unsupported locations;
- refusal to substitute another city for missing driving-license data; and
- unsupported Action requests.

## Current Limitations and Planned Work

The following are not implemented:

- multi-turn conversational CLI/session flow;
- persistent conversation state or LangGraph checkpointer integration;
- checklist builder action;
- fee lookup action;
- appointment slot checking;
- appointment booking simulator;
- journey/progress tracking refinement;
- GPS or map-based nearest-office calculation;
- broader service-center coverage, especially driving-license branches;
- HTTP API, frontend, and production file-upload UI;
- database, authentication, or multi-user storage;
- voice integration;
- broader Urdu and regional-language polish; and
- additional citizen services beyond the current passport and driving-license
  scope.

The next planned milestone is **Multi-turn Conversational CLI / Session Flow**,
so clarification and follow-up answers can continue within one process. Later
Action milestones are Checklist Builder, Fee Lookup, and Appointment Simulator.
