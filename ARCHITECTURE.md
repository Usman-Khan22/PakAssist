# PakAssist — Architecture

## What is PakAssist?

PakAssist is an agentic AI assistant designed to help Pakistani citizens
understand and navigate public/government services (for example, driving
licenses, passports, and appointments). It is being built incrementally as
a hackathon project, with the backend foundation established first and
additional capabilities layered on over time.

This document describes the **current** architecture as implemented today,
and separately outlines the **planned** architecture the project is being
built toward. The two are clearly distinguished throughout.

---

## Current Architecture

At this stage, PakAssist consists of a minimal backend only. There is no
frontend, no API layer, no database, and no real agents yet — the current
code exists to establish a working LangGraph foundation that future work
will build on.

```
backend/
├── main.py            # CLI entry point
├── agents/             # Empty — reserved for future agent implementations
└── graph/
    ├── state.py         # Shared LangGraph state definition
    └── graph.py         # LangGraph graph construction
```

### Current Request Flow

The system currently runs as a terminal (CLI) program, not a service:

```
User types input in terminal
        │
        ▼
backend/main.py
  - loads environment variables (.env)
  - builds the graph
  - creates initial PakAssistState
  - invokes the graph
        │
        ▼
LangGraph graph (backend/graph/graph.py)
  START → passthrough → END
        │
        ▼
Resulting state printed to terminal
```

There is no HTTP/API layer, no persistent storage, and no external
service calls in the current flow.

### Current LangGraph Structure

The graph is a `StateGraph` built on `PakAssistState`, with a single
placeholder node:

```
START → passthrough → END
```

- **`passthrough`** is a temporary node that returns the state unchanged.
- It exists solely to verify that the LangGraph wiring (state → node →
  compiled graph) works end to end.
- It does **not** perform intent detection, routing, or any AI reasoning.

### Role of `PakAssistState`

Defined in `backend/graph/state.py` as a `TypedDict`, `PakAssistState` is
the shared state object passed between nodes in the graph. All nodes read
from and/or write to this state.

Current fields:

| Field          | Purpose (current)                                   |
|----------------|------------------------------------------------------|
| `user_input`   | The raw text entered by the user                     |
| `intent`       | Reserved for future intent classification            |
| `service_type` | Reserved for future service routing (e.g. license)   |
| `next_step`    | Reserved for future workflow/routing decisions       |

At this stage, only `user_input` is populated meaningfully; the other
fields are initialized empty and are not yet used by any logic.

### Role of `main.py`

`backend/main.py` is the current application entry point. It:

1. Loads environment variables via `python-dotenv`.
2. Builds the LangGraph workflow via `build_graph()`.
3. Accepts a single user message from the terminal.
4. Constructs the initial `PakAssistState`.
5. Invokes the compiled graph with that state.
6. Prints the resulting state to the terminal.

It is intentionally simple — a CLI harness for exercising the graph, not
a production entry point.

### Role of `graph.py`

`backend/graph/graph.py` is responsible for constructing and compiling the
LangGraph `StateGraph`. Currently it defines:

- One node (`passthrough`) that returns state unchanged.
- The graph edges: `START → passthrough → END`.
- A `build_graph()` function that returns the compiled graph.

This file is the intended location for wiring in future agent nodes and
routing logic as they are implemented.

### Current Limitations

- No real agents exist — the graph does no AI reasoning yet.
- No API layer (e.g. FastAPI) — the app only runs via the terminal.
- No frontend integration.
- No RAG, document understanding, or knowledge retrieval.
- No persistent storage or database.
- No appointment booking or service-center lookup.
- No Urdu/regional language or voice support.
- No authentication or multi-user handling.

---

## Planned Architecture (Not Yet Implemented)

The following describes the intended direction of the project. **None of
this is implemented yet** — it is documented here to give new developers
context on where the current foundation is headed.

### Planned High-Level Flow

```
Frontend
   │
   ▼
Backend / API layer
   │
   ▼
LangGraph workflow
   │
   ├── Planner Agent        (decides which agent(s)/steps to invoke)
   ├── Knowledge/RAG Agent   (retrieves info from official sources)
   ├── Action Agent          (performs actions / tool calls)
   └── Appointment Agent     (handles appointment-related workflows)
   │
   ▼
Response back to frontend
```

### How Planned Components Are Expected to Fit In

- **Planner Agent**: Expected to be added as a node (or set of nodes) in
  `graph.py`, likely replacing the current `passthrough` node. It would
  read `user_input`, populate `intent`/`service_type`, and decide
  `next_step` to route the state to the appropriate downstream agent.

- **Knowledge/RAG Agent**: Expected to be introduced as a separate agent
  module under `backend/agents/`, invoked by the Planner Agent when a
  user's query requires information from official/government sources.

- **Action Agent**: Expected to handle tool-calling for concrete actions
  (e.g. form submission, status checks), added as another node/agent
  under `backend/agents/`.

- **Appointment Agent**: Expected to manage appointment-related workflows
  (e.g. booking, checking slots), likely requiring its own state fields
  and, eventually, persistent storage.

- **Document Understanding**: Expected to be added as a capability that
  processes uploaded documents (e.g. ID cards, forms) — likely a new
  agent or tool integrated into the graph, with new state fields for
  document data.

- **Urdu/regional language & voice interaction**: Expected to affect the
  input/output layer (parsing user input, generating responses) rather
  than the graph structure itself; likely implemented as pre/post-processing
  around the graph invocation.

- **Frontend**: The `frontend/` directory is currently empty. Once an API
  layer exists on the backend, the frontend is expected to communicate
  with it over HTTP rather than calling backend code directly.

- **Persistent application data**: Currently there is no database. Future
  stages handling appointments, user history, or documents will likely
  require introducing persistent storage, to be decided when that work
  begins.

Each of these will be added incrementally, in line with the project's
existing modular structure — new agents under `backend/agents/`, new graph
nodes/edges in `graph.py`, and new state fields in `state.py` only as
genuinely needed.