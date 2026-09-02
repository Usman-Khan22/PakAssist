# PakAssist Code Walkthrough

This guide is for a developer who understands basic Python and wants a mental
model of PakAssist without reading every helper function. It follows the code
that exists today through Milestone 9, including multi-turn sessions, grounded
assistance, and deterministic appointment simulation.

## 1. Big Picture

PakAssist is a command-line assistant for Pakistani passport and driving-license
questions. It can:

- answer questions from a trusted Markdown knowledge base;
- turn trusted document requirements into checklists;
- return verified fee information when the knowledge base supports it;
- read relevant text from uploaded images and PDFs;
- find passport and driving-license service centers from local JSON datasets;
- check and book deterministic demo appointment slots after office selection;
- ask for a missing location and continue when the user replies; and
- reuse a known service for a narrow fee follow-up such as “How much does it
  cost?”

The main flow is:

```text
User
  |
  v
CLI session (one in-memory thread)
  |
  v
LangGraph Planner
  |
  v
Conditional Router
  |-- Knowledge -> Knowledge Agent -> RAG
  |                                  |-- normal grounded answer
  |                                  |-- grounded checklist
  |                                  `-- grounded fee answer
  |
  |-- Action -> Action Agent
  |              |-- Service Center Lookup
  |              |-- Check Slots -> Appointment Simulator
  |              `-- Book Slot -> Appointment Simulator
  |
  `-- Clarification
```

The components have different jobs:

- The **Planner** decides what the user is trying to do and which branch should
  run.
- The **Knowledge Agent** coordinates retrieval and grounded answer generation.
- **RAG** is the lower-level machinery that finds relevant text.
- The **Checklist Builder** structures retrieved requirements; it does not own
  requirement facts.
- **Fee Lookup** selects trustworthy retrieved fee sections; it contains no fee
  amounts itself.
- The **Action Agent** dispatches service-center lookup, simulated slot checks,
  and simulated bookings.
- **Service Center Lookup** reads and filters local JSON records.
- The **Appointment Simulator** reads immutable demo schedules and validates
  session-local bookings; it is not a live appointment system.
- **Clarification** is the safe fallback when routing is uncertain.
- **Session state** lets a small amount of context survive between turns in the
  same process.

## 2. Program Entry - `main.py`

The executable entry point is the repository-root `main.py`. There is no
`backend/main.py` in the current repository.

`main()` collects optional file paths from command-line arguments and calls
`run_cli()`. The important setup inside `run_cli()` is conceptually:

```python
graph = build_graph(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": uuid4().hex}}
```

`InMemorySaver` is LangGraph's temporary checkpoint store. The generated
`thread_id` identifies this CLI conversation. Every graph invocation in the
loop uses the same configuration, so LangGraph can merge the latest turn with
that thread's previous state.

The loop then:

1. reads one line from `PakAssist>`;
2. ignores an empty line;
3. stops on `exit`, `quit`, or end-of-file;
4. creates a small turn update containing `user_input`, a fresh empty source
   list, and first-turn upload paths when provided;
5. invokes the graph with the stable thread configuration; and
6. prints the response and any source label/origin/confidence information.

Planner failures are printed without crashing the whole loop. Uploaded file
paths are supplied on the first turn only. Once their content has been added to
the in-memory retriever, it remains available in that process; it is never
written into the official persistent index.

## 3. Shared State - `backend/graph/state.py`

`PakAssistState` is the shared record passed through LangGraph. Each node reads
the fields it needs and returns updates for the fields it owns.

The current fields are:

- `user_input`: the current user text. During location continuation, the graph
  replaces it with a reconstructed request such as “Find the nearest passport
  office in Karachi”.
- `intent`: the Planner's high-level interpretation, such as
  `requirements_checklist`, `fee_lookup`, or `service_center_lookup`.
- `service_type`: the government service, normally `passport`,
  `driving_license`, or `unknown`.
- `next_step`: the Planner's requested downstream branch: `knowledge`,
  `action`, `appointment`, or `clarify`.
- `response`: the user-facing answer written by the selected downstream node.
- `uploaded_files`: optional image/PDF paths for Knowledge retrieval.
- `sources`: source references supporting the answer.
- `pending_clarification`: the missing datum for a resumable request;
  currently `location` or `office`.
- `pending_request`: the original request kept while location or office choice
  is missing.
- `office_options`: ordered office names offered to the user.
- `selected_office`: the office chosen for appointment simulation.
- `appointment_date`: the demo date configured for that office.
- `booked_slots`: slot keys booked in this checkpointed session.

`SourceRef` is the common source shape used by Knowledge and Action responses.
It stores a display label, origin, service, section, source URL, and confidence
when those values exist. Keeping one source contract means the CLI does not
need to know how each agent found its evidence.

## 4. LangGraph Workflow - `backend/graph/graph.py`

`build_graph()` creates four nodes:

- `planner`: classifies a normal turn or resumes a supported contextual turn;
- `knowledge`: calls `knowledge_agent()`;
- `action`: calls `action_agent()`; and
- `clarification`: asks the user to clarify which government service is needed.

The graph starts at `START`, always visits the Planner node, and then uses
`_route_after_planner()`:

```text
START
  -> planner
      -> knowledge -> END
      -> action -> END
      -> clarification -> END
```

An invocation reaches `END` after one downstream node. Multi-turn behavior
comes from the CLI invoking the graph again with the same checkpointer and
thread ID, not from a cycle inside the graph.

Routing rules are intentionally conservative:

- unknown intent or service -> Clarification;
- known `next_step="knowledge"` -> Knowledge;
- known `next_step="action"` -> Action; and
- everything else -> Clarification.

Before calling the Planner, the planner node resolves pending location or
office answers. After calling it, the node can safely reuse service context for
fee and exact appointment intents. Exact `check_slots` and `book_slot` intents
are normalized to Action. These are small compatibility rules, not a separate
conversation-memory agent.

## 5. Planner - `backend/agents/planner.py`

`run_planner(user_input)` sends the current text to Gemini and requires a
Pydantic-validated `PlannerOutput` with three values:

- `intent`: what the user wants;
- `service_type`: which service it concerns; and
- `next_step`: which graph branch should run.

Conceptual examples:

```text
"Find a passport office in Karachi"
  intent       -> service_center_lookup
  service_type -> passport
  next_step    -> action

"What documents do I need for a passport?"
  intent       -> requirements_checklist
  service_type -> passport
  next_step    -> knowledge

"How much does a passport cost?"
  intent       -> fee_lookup
  service_type -> passport
  next_step    -> knowledge
```

The contract also permits `appointment`, but the implemented simulator does
not require a separate graph node: exact `check_slots` and `book_slot` intents
route through Action. Unsupported routing values still fall back to
Clarification.

Gemini returns native structured JSON. The code parses it with `json.loads`
and validates it before state is updated. Tools are not configured, and
automatic function calling (AFC) is explicitly disabled. That detail is an
important compatibility constraint throughout this project.

For a contextual fee follow-up, the Planner still runs. If the new turn is a
fee request but the Planner cannot identify a service, the graph may reuse a
known service from the same checkpointed thread and route to Knowledge.

## 6. Knowledge Path

The Knowledge path begins in `backend/agents/knowledge.py`:

```text
Knowledge state
  -> obtain Retriever
  -> optionally extract/index uploads
  -> detect normal/checklist/fee response mode
  -> retrieve relevant chunks
  -> select trusted chunks for the chosen mode
  -> build a source-labelled context block
  -> call Gemini with grounded instructions
  -> write response and SourceRef entries
```

The Knowledge Agent is an orchestrator. It decides which retrieval query to
use, which chunks are allowed to support the response, which system prompt to
use, and which sources to expose.

The RAG modules below it do not decide whether a citizen asked for a checklist
or fee. They load, embed, store, and retrieve text.

If retrieval returns nothing, the Knowledge Agent returns its safe no-context
message and skips Gemini generation. Specialized checklist and fee modes also
have their own safe fallbacks when retrieved chunks do not meet their grounding
rules.

## 7. RAG Internals - `backend/rag/`

### Building the trusted index

```text
knowledge_base/*.md
  -> loader.py
  -> section documents
  -> chunker.py
  -> text chunks + metadata
  -> embeddings.py
  -> normalized vectors
  -> vector_store.py
  -> data/faiss_index/index.faiss + store.pkl
```

`scripts/build_index.py` runs this pipeline. It reads `KB_DIR` and
`KB_INDEX_DIR` from the environment when set, otherwise using
`knowledge_base/` and `data/faiss_index/`.

The major files are:

- `loader.py`: splits Markdown on `##` headings. Every retrievable section
  retains service, section, source URL, confidence, and document-type metadata.
- `chunker.py`: keeps short sections together and splits long ones with a small
  overlap so related text is not abruptly separated.
- `embeddings.py`: lazily loads
  `sentence-transformers/all-MiniLM-L6-v2` and converts text to 384-dimensional
  vectors.
- `vector_store.py`: wraps FAISS `IndexFlatIP` and keeps the original texts and
  metadata alongside the vector index.
- `retriever.py`: searches the official index and optional upload index,
  filters by score, combines and ranks results, and labels each result's origin.
- `multimodal.py`: converts images and PDFs into text before they enter the
  upload index.

Embeddings are L2-normalized. For normalized vectors, inner product is the same
ranking measure as cosine similarity, so FAISS `IndexFlatIP` provides a simple
exact similarity search suitable for this project.

### Query-time retrieval

```text
user query
  -> normalized query embedding
  -> FAISS search
  -> score threshold + top-k ranking
  -> RetrievedChunk objects
  -> Knowledge Agent
```

The official index is persisted on disk. User-upload content is embedded into
a separate `FaissVectorStore` held only in memory and is marked
`origin="user_upload"`. It is never added to the official index.

For images (PNG, JPG/JPEG, or WebP), Gemini extracts visible factual text. For
PDFs, PyMuPDF extracts normal text page by page. Pages with too little text are
rasterized and sent through the image-extraction path. The multimodal Gemini
call also uses no tools and has AFC explicitly disabled.

## 8. Checklist and Fee Assistance

Checklist and fee assistance both stay inside the Knowledge path.

### Checklist requests

`backend/services/checklist_builder.py` contains:

- phrases for recognizing document/checklist requests;
- a requirements-focused retrieval-query builder;
- selection logic that accepts only trusted `knowledge_base` chunks for the
  current service and a `Required Documents` section; and
- instructions for formatting retrieved facts as `☐` items.

It deliberately contains no passport or driving-license requirement list.

```text
"Give me a passport checklist"
  -> Knowledge Agent
  -> RAG retrieves passport requirements
  -> trusted Required Documents chunks selected
  -> Checklist Builder prompt structures those facts
  -> checklist response + sources from those chunks
```

Conditional items and uncertainty must remain visible. This matters for the
driving-license KB, whose requirements are described as typical and dependent
on province.

A normal question such as “How long is a passport valid?” does not use the
Checklist Builder. It uses ordinary grounded Knowledge generation.

### Fee requests

`backend/services/fee_lookup.py` contains fee detection, a fee-focused
retrieval query, confidence-based selection, and formatting instructions. It
contains no amounts.

The selector first finds trusted fee-section chunks for the current service.
Numeric generation is allowed only when a chunk is high confidence and does
not contain an `unverified` marker. The formatter must preserve distinctions
such as validity, urgency, document type, page count, surcharge, and effective
date found in the retrieved context.

The passport KB contains high-confidence official fee tables, so a passport fee
answer can be generated. The driving-license KB explicitly says its numeric
ranges are unverified and medium confidence, so the current code returns a
reliable-fee-not-found response instead of quoting them.

Both modes build `sources` from the chunks actually selected. They do not
create a second citation mechanism.

## 9. Action Path

The Action path is separate from factual Knowledge transformations:

```text
Planner
  -> Action node
  -> action_agent(state)
  -> select supported action
  -> call service/helper
  -> response + sources
```

`backend/agents/action.py` interprets the Planner intent and request language.
It dispatches `service_center_lookup`, `check_slots`, and `book_slot`. Any other
Action request receives a safe unsupported-action message.

The distinction is useful:

- the **agent** decides which action should run and formats its result;
- the **service** implements deterministic dataset loading and matching.

Checklist and fee requests are not Action Agent features because their factual
content must come through RAG.

## 10. Service Center Lookup

`backend/services/service_centers.py` reads one of two local files:

- `knowledge_base/passport_service_centers.json`; or
- `knowledge_base/driving_license_service_centers.json`.

The service type chooses the dataset. The lookup extracts an explicit location
from phrases such as `in`, `near`, `at`, or `around`, or recognizes known
region/province and office names. It normalizes text and compares the location
against region/province, office name, and address fields. It returns at most
five matches.

The possible outcomes are:

- `found`: format available office name, address, phone, service, hours,
  portal, confidence, and source fields;
- `missing_location`: ask the user for a city or region;
- `no_results`: say the current dataset has no result for that location; or
- `unsupported_service`: explain that no dataset is configured.

There is no distance calculation, GPS, map, web scraping, or external location
API. The code never invents an address or substitutes another city.

The passport dataset is broad. The driving-license dataset has only six
records and is intentionally incomplete. For example, a Lahore lookup cannot
safely return an Attock office.

### Appointment Simulator

`backend/services/appointment_simulator.py` is the deterministic service behind
slot checking and demo booking. The Action Agent first resolves an office by
reusing Service Center Lookup. A single match can be selected automatically;
multiple matches are stored in `office_options` and prompt the user to choose
by office name, number, or a simple ordinal.

The service reads `data/appointment_slots.json`, which is a small immutable demo
schedule rather than trusted knowledge or live government availability. It
matches exact service/office entries, normalizes common requested times to
`HH:MM`, and removes slot keys already present in the session's `booked_slots`.
A successful booking appends its key to state and returns a deterministic
`DEMO-...` reference. It never edits the seed file or creates a real booking.

Responses explicitly say that availability and confirmation are simulated and
that a real appointment must be made through the official government system.
Because demo schedules are not trusted evidence, appointment responses use an
empty `sources` list.

## 11. Multi-Turn Conversation

The practical location flow is:

```text
User: Find the nearest passport office.
  -> Planner chooses passport service-center Action
  -> lookup reports missing location
  -> Action stores pending_clarification="location"
     and pending_request=<original text>

Assistant: Which city or region should I search in?

User: Karachi
  -> same thread checkpoint is loaded
  -> Planner node sees the pending location
  -> it reconstructs the original request with "in Karachi"
  -> previous passport service and Action route are retained
  -> lookup returns Karachi offices
  -> pending fields are cleared
```

The other supported contextual case is a fee follow-up:

```text
User: What documents do I need for a passport?
Assistant: [grounded checklist]
User: How much does it cost?
  -> Planner identifies a fee request but may return service=unknown
  -> graph reuses passport from this thread
  -> Knowledge fee path runs
```

Appointment continuation adds location and office resolution:

```text
User: Check passport appointment slots in Karachi.
  -> Service Center Lookup finds several offices
  -> Action stores office_options and asks the user to select
User: first
  -> selected_office is retained in the same thread
  -> Appointment Simulator returns that office's demo date and open slots
User: Book 10:00
  -> the demo slot key is appended to booked_slots
  -> a repeated booking in this session is rejected
```

This context exists only in memory. Closing the process loses it. A new
session gets a new thread ID and does not inherit pending graph state. The
implementation does not provide general chat history, generic pronoun
resolution, or continuation for every clarification type.

## 12. End-to-End Examples

### Grounded checklist

```text
"What documents do I need for a passport?"
  -> Planner: requirements_checklist / passport / knowledge
  -> Knowledge Agent
  -> requirements-focused RAG retrieval
  -> trusted passport Required Documents chunks
  -> Checklist Builder formatting
  -> checklist + SourceRef entries
```

### Normal Knowledge answer

```text
"How long is a passport valid?"
  -> Planner: knowledge
  -> Knowledge Agent
  -> normal RAG retrieval
  -> grounded Gemini answer + sources
```

### Fee answer

```text
"How much does a passport cost?"
  -> Planner: fee_lookup / passport / knowledge
  -> fee-focused RAG retrieval
  -> high-confidence passport fee chunks
  -> grounded fee formatter + sources
```

### Direct Action

```text
"Find a passport office in Karachi."
  -> Planner: service_center_lookup / passport / action
  -> Action Agent
  -> Service Center Lookup
  -> Karachi records + sources
```

### Clarification continuation

```text
"Find a driving license center."
  -> Action lookup asks for location and stores pending context
"Attock"
  -> same session reconstructs request
  -> Attock Driving Licensing Branch
```

### Simulated appointment

```text
"Check passport appointment slots in Karachi."
  -> Planner: check_slots / passport / action
  -> Action Agent -> Service Center Lookup
  -> office selection when multiple matches exist
  -> Appointment Simulator -> demo date and available times
"Book 10:00"
  -> Planner: book_slot / passport / action
  -> session-local booking + DEMO reference
```

This result is explicitly a simulation, not live availability or a government
reservation.

## 13. Important Files at a Glance

- `main.py`: starts and maintains the CLI session.
- `backend/graph/state.py`: defines shared state and source references.
- `backend/graph/graph.py`: defines nodes, edges, routing, and contextual
  continuation.
- `backend/agents/planner.py`: converts user text into validated routing data.
- `backend/agents/knowledge.py`: coordinates RAG and all grounded response
  modes.
- `backend/agents/action.py`: dispatches supported actions.
- `backend/services/checklist_builder.py`: fact-free checklist selection and
  formatting rules.
- `backend/services/fee_lookup.py`: fact-free fee selection and formatting
  rules.
- `backend/services/service_centers.py`: deterministic JSON center lookup.
- `backend/services/appointment_simulator.py`: deterministic slot and booking
  rules.
- `data/appointment_slots.json`: immutable demo schedules.
- `backend/rag/`: loading, chunking, embeddings, FAISS, retrieval, and
  multimodal extraction.
- `scripts/build_index.py`: rebuilds the persistent official index.
- `knowledge_base/`: trusted Markdown guidance and center datasets.
- `tests/`: route, RAG, session, Action, checklist, fee, and appointment
  behavior.

## 14. If I Want to Change X, Where Do I Go?

- Change Planner classifications or routing guidance ->
  `backend/agents/planner.py`.
- Change graph branches or continuation rules -> `backend/graph/graph.py`.
- Add shared state -> `backend/graph/state.py`, then update every producer and
  consumer deliberately.
- Change grounded generation or response-mode coordination ->
  `backend/agents/knowledge.py`.
- Change Markdown parsing -> `backend/rag/loader.py`.
- Change chunk sizes/overlap -> `backend/rag/chunker.py`.
- Change embedding behavior -> `backend/rag/embeddings.py`.
- Change FAISS persistence/search mechanics -> `backend/rag/vector_store.py`.
- Change result merging, score thresholds, or top-k ->
  `backend/rag/retriever.py`.
- Change image/PDF extraction -> `backend/rag/multimodal.py`.
- Rebuild trusted vectors after approved KB changes ->
  `scripts/build_index.py`.
- Change checklist detection, trusted-section rules, or output instructions ->
  `backend/services/checklist_builder.py`.
- Change fee detection, reliability rules, or formatting instructions ->
  `backend/services/fee_lookup.py`.
- Add or modify an action -> `backend/agents/action.py`; keep its factual or
  dataset work in a separate service module.
- Change center matching -> `backend/services/service_centers.py`.
- Change demo schedule/time/booking rules ->
  `backend/services/appointment_simulator.py`.
- Change configured demo office dates or slots ->
  `data/appointment_slots.json`; keep it clearly simulated and immutable at
  runtime.
- Change the interactive loop, exits, or thread creation -> `main.py`.
- Add tests -> choose the focused file under `tests/`; session behavior belongs
  in `test_session_flow.py`, checklist/fee behavior belongs in
  `test_grounded_assistance.py`, and appointment behavior belongs in
  `test_appointment_simulator.py`.

When adding a future capability, first decide whether it is Knowledge or
Action. If it answers from trusted facts, extend the Knowledge path. If it
performs a deterministic operation, use Action plus a separate service.

## 15. What I Do Not Need to Understand Yet

To work productively at first, you do not need to study:

- FAISS's internal algorithms beyond “search normalized vectors by similarity”;
- transformer architecture beyond “similar meanings get nearby embeddings”;
- Gemini SDK internals beyond the structured Planner call and grounded
  generation calls;
- every regular expression in Markdown/location parsing;
- pickle/index binary formats; or
- every mock in the tests.

Start with `main.py`, state, graph, and the three agents. Then follow either the
Knowledge path into `backend/rag/` or the Action path into the relevant service
module depending on the feature you are changing.

## 16. Current Limitations and Next Areas

- Appointment availability is a small deterministic demo, not live government
  data, and no real reservation is created.
- Demo bookings and conversation state are process/thread-local; they do not
  persist across restarts or represent multi-user storage.
- Context supports location, office selection, appointment flow, and narrow
  fee continuation, not general chat memory.
- Driving-license numeric fees are not reliable enough to quote.
- Driving-license center coverage is incomplete.
- “Nearest” means textual location matching, not geographic distance.
- There is no API, frontend, production upload UI, database, authentication,
  voice layer, GPS/maps, or progress tracking.

The next planned area is Journey/Progress Tracking and Orchestration
Refinement. RAG latency profiling and optimization remains a technical
improvement area.
