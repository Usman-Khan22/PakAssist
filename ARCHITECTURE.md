# PakAssist - Architecture

## Implementation Status

### Implemented

PakAssist currently has a backend CLI with one real agent: the Planner
Agent. The Planner classifies a user's message into structured planning
fields, and LangGraph uses that decision to select a workflow path.

The current repository contains:

```
backend/
├── main.py                 # CLI entry point
├── agents/
│   └── planner.py          # Gemini-backed Planner Agent
└── graph/
    ├── state.py            # Shared LangGraph state
    └── graph.py            # LangGraph construction and routing
```

There is no API, frontend, database, RAG system, real action execution,
appointment booking, document processing, voice support, or full
Urdu/regional-language feature.

### Planned

The routing structure is intended to provide connection points for future
specialized capabilities. Those capabilities are not implemented yet.

## Current Request Flow

The application handles one request from the terminal:

```
User enters a message
        |
        v
backend/main.py
  - loads .env values
  - builds the compiled graph
  - creates PakAssistState
  - invokes the graph
        |
        v
LangGraph: START -> planner
        |
        v
Planner Agent calls Gemini and validates PlannerOutput
        |
        v
Conditional route based on next_step and known fields
        |
   +----+-------------+----------------+
   |                  |                |
knowledge          action       clarification
   |                  |                |
   +------------------+----------------+
                      |
                      v
                    END
        |
        v
Updated state is printed to the terminal
```

`main.py` reports a `PlannerError` as a CLI message. The application has no
HTTP endpoint and does not persist data.

## Planner Agent

`backend/agents/planner.py` defines `PlannerOutput` with three fields:

- `intent`: the user's high-level goal, such as `apply_for_service`,
  `renew_service`, or `book_appointment`.
- `service_type`: the government service, such as `driving_license` or
  `passport`, or `unknown` when it is not clear.
- `next_step`: one of `knowledge`, `action`, `appointment`, or `clarify`.

The Planner prompt covers English, Urdu, and Roman Urdu input and instructs
Gemini to use conservative classifications. It prefers `unknown` and
`clarify` when the request is ambiguous. This prompt does not constitute a
separate Urdu or regional-language feature.

## LLM and Structured Output

The Planner uses the `google-genai` client directly. It reads the API key
from `GEMINI_API_KEY` and the model from `GEMINI_MODEL`, defaulting to
`gemini-2.5-flash`. No credentials are hardcoded.

Gemini is called with native structured JSON output:

- `response_mime_type="application/json"`
- `response_schema=PlannerOutput`
- no tools
- `automatic_function_calling.disable=True`

The response text is parsed with `json.loads` and validated with
`PlannerOutput.model_validate`. API failures, empty responses, invalid JSON,
and schema validation failures become `PlannerError`.

AFC is explicitly disabled because this Planner uses a direct
`models.generate_content` call and has no tools or chat session. The current
approach is native Gemini JSON schema output, not automatic function calling.

## Shared State

`backend/graph/state.py` defines `PakAssistState` as a `TypedDict`:

| Field | Current purpose |
|---|---|
| `user_input` | Raw terminal input passed to the Planner |
| `intent` | Planner-produced high-level goal |
| `service_type` | Planner-produced service or `unknown` |
| `next_step` | Planner-produced workflow decision |
| `response` | Message written by the selected terminal workflow node |

`main.py` initializes all fields. The Planner node updates `intent`,
`service_type`, and `next_step`; the selected downstream node updates
`response`.

## Current Graph Nodes and Routing

`backend/graph/graph.py` builds this graph:

```
START -> planner -> conditional route -> knowledge/action/clarification -> END
```

- `planner`: calls the Planner Agent and writes its three structured fields
  into graph state.
- `knowledge`: minimal routing placeholder that writes
  `Request routed to knowledge.` It does not perform RAG or retrieve data.
- `action`: minimal routing placeholder that writes
  `Request routed to action.` It does not execute actions.
- `clarification`: writes a request for the user to clarify the government
  service.
- conditional routing: sends known `knowledge` decisions to `knowledge`,
  known `action` decisions to `action`, and unknown/unclear decisions to
  `clarification`. The currently valid `appointment` label also falls back
  to clarification because appointment handling is not implemented.

The graph tests mock the Planner and verify the knowledge, action, and
clarification paths without making network calls.

## Current Limitations

- The CLI handles one request at a time.
- Knowledge and action nodes are routing placeholders only.
- Appointment routing has no appointment node and falls back to clarification.
- There is no real information retrieval, action execution, or appointment
  booking.
- There is no API, frontend, database, authentication, or multi-user state.
- There is no document processing or voice interaction.
- Urdu and Roman Urdu are accepted as possible Planner input, but there is
  no dedicated regional-language or voice pipeline.

## Planned Architecture

Future work may connect specialized agents to the existing conditional
routing points:

```
Frontend/API (planned)
        |
        v
LangGraph Planner
        |
        +--> Knowledge capability (planned RAG/retrieval)
        +--> Action capability (planned tool/action execution)
        +--> Appointment capability (planned booking workflow)
        +--> Clarification path
```

An API, frontend, persistence, document understanding, authentication,
regional-language processing, and voice interaction are all planned only.
They must not be treated as implemented until corresponding code exists.
