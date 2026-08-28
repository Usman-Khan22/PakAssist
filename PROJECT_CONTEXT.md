# PakAssist - Project Context for AI Coding Agents

This document is concise context for Copilot Agent, Claude, Antigravity, and
other coding agents working in this repository.

## Purpose

PakAssist helps Pakistani citizens understand and navigate public/government
services such as driving licenses and passports. Development is incremental.

## Current Status

Implemented backend-only CLI milestone:

1. Planner Agent
2. Pydantic-validated structured Planner output
3. LangGraph integration
4. Conditional routing from the Planner's `next_step`
5. Clarification path for unknown or unclear requests

The graph is no longer `START -> planner -> END`:

```
START -> planner -> knowledge/action/clarification -> END
```

`knowledge` and `action` are minimal routing placeholders. They only write a
routing message; they are not RAG or real action agents. There is no
appointment node, so `appointment` currently falls back to clarification.

## Important Files

- `backend/main.py`: Loads `.env`, accepts one CLI message, invokes the graph,
  and reports `PlannerError`.
- `backend/agents/planner.py`: Calls Gemini and validates `PlannerOutput`.
- `backend/graph/graph.py`: Defines Planner, placeholder terminal nodes, and
  conditional routing.
- `backend/graph/state.py`: Defines shared `PakAssistState`.
- `tests/test_planner.py`: Offline mocked Planner and graph routing tests.
- `tests/conftest.py`: Adds the project root to `sys.path` for pytest.
- `requirements.txt`: Runtime and test dependencies.
- `ARCHITECTURE.md`: Detailed implemented/planned architecture.

## Current Workflow and State

`main.py` initializes `user_input`, `intent`, `service_type`, `next_step`, and
`response`. The Planner node fills the three classification fields. Routing
uses known `intent` and `service_type` plus `next_step`:

- known `knowledge` -> knowledge placeholder
- known `action` -> action placeholder
- unknown/unclear fields or unsupported route -> clarification node

The selected terminal node fills `response` before the state is printed.

## Gemini and AFC Constraint

The Planner uses the direct `google-genai` client. It reads `GEMINI_API_KEY`
from the environment and uses `GEMINI_MODEL`, defaulting to
`gemini-2.5-flash`. Never hardcode credentials.

Structured output uses Gemini native JSON schema settings:

- `response_mime_type="application/json"`
- `response_schema=PlannerOutput`
- no tools
- `automatic_function_calling.disable=True`

The AFC issue was resolved by explicitly disabling automatic function calling.
Do not reintroduce AFC or tool calling for the direct
`models.generate_content` call. The Planner needs text-in/JSON-out structured
classification. It parses the response with `json.loads` and validates it
with Pydantic before graph state is updated.

## Current Milestone

Prove that the Planner controls LangGraph workflow selection while keeping
downstream capabilities as minimal placeholders.

## Next Planned Milestone

Connect one explicitly selected downstream capability to its route, starting
with real knowledge retrieval only when that feature is scheduled. Do not
build RAG, real actions, appointments, an API, frontend, database, document
processing, voice, or dedicated Urdu/regional-language handling as part of
this routing milestone.

## Development Rules

- Implement only the requested task.
- Do not rebuild the Planner, structured-output path, or routing already here.
- Do not implement planned features without explicit instruction.
- Keep changes simple, beginner-readable, and limited to relevant files.
- Preserve the Planner -> LangGraph design and existing state contract.
- Add state fields only for a real current requirement.
- Keep agents under `backend/agents/` and graph changes under
  `backend/graph/`.
- Do not add an API framework or database until genuinely required.
- Do not expose or commit API keys or other secrets; use `.env`.
- Run the tests before considering a change complete.

## Git and Branching Rules

- Do not commit directly to `main`.
- Work on feature branches.
- Keep commits focused on one logical change.
- Use conventional commit messages such as `feat:`, `fix:`, `docs:`, and
  `chore:`.
