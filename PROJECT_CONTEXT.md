# PakAssist — Project Context for AI Coding Agents

This document is written for AI coding agents (Claude, GitHub Copilot,
Antigravity, etc.) working on this repository. Read it before making any
changes.

## Project Purpose

PakAssist is an agentic AI assistant that helps Pakistani citizens
understand and navigate public/government services (e.g. driving
licenses, passports, appointments). It is being built incrementally as a
hackathon project.

## Current Implementation Status

The backend foundation only. There are:

- No real AI agents yet.
- No API layer.
- No frontend implementation.
- No RAG, document processing, or appointment booking.
- No database.

The graph currently contains a single temporary passthrough node used to
verify the LangGraph wiring works. See `ARCHITECTURE.md` for full details.

## Current Architecture

```
backend/main.py  →  backend/graph/graph.py (StateGraph)  →  backend/graph/state.py (PakAssistState)
```

- `main.py`: CLI entry point. Loads env vars, builds the graph, takes one
  terminal input, invokes the graph, prints the result.
- `graph.py`: Builds the LangGraph `StateGraph`. Currently: `START → passthrough → END`.
- `state.py`: Defines `PakAssistState` (TypedDict) with fields
  `user_input`, `intent`, `service_type`, `next_step`.
- `agents/`: Empty. Reserved for future agent modules.
- `frontend/`: Empty. Not yet started.

## Important Files

| File | Purpose |
|---|---|
| `backend/main.py` | Application entry point |
| `backend/graph/graph.py` | Graph construction and compilation |
| `backend/graph/state.py` | Shared state definition |
| `backend/agents/` | Future location for agent implementations |
| `requirements.txt` | Python dependencies |
| `ARCHITECTURE.md` | Full technical architecture (current + planned) |

## Development Principles

- Build incrementally — one stage at a time.
- Keep the architecture modular and simple.
- Do not build ahead of what has been explicitly requested.
- Prefer clarity and readability over cleverness.

## Coding Guidelines

- Python, beginner-readable code.
- Comment only where something is non-obvious.
- Avoid large amounts of boilerplate.
- Do not create placeholder/fake functionality just to look complete.
- Keep state (`PakAssistState`) minimal — add fields only when a real,
  current need exists, not speculatively for future features.

## Architecture Constraints

- New agents belong under `backend/agents/`.
- New graph nodes/edges belong in `backend/graph/graph.py`.
- New state fields belong in `backend/graph/state.py`, added only when
  genuinely needed by current work.
- No API framework (e.g. FastAPI) until it is genuinely required.
- No database until a feature genuinely requires persistence.
- Frontend and backend remain decoupled; frontend should talk to the
  backend over an API layer once one exists — not import backend code
  directly.

## Git / Branching Rules

- Do not commit directly to `main`.
- Work on feature branches.
- Keep commits focused (one logical change per commit).
- Use conventional commit messages (e.g. `feat:`, `fix:`, `docs:`, `chore:`).

## Rules for AI Coding Agents

- Implement only the requested task — nothing more.
- Do not implement future/planned features unless explicitly requested.
- Do not modify unrelated files.
- Do not unnecessarily refactor existing code.
- Reuse the existing architecture rather than introducing new patterns.
- Keep components modular.
- Prefer simple, maintainable implementations over complex ones.
- Explain any important architectural changes made.
- Test changes before considering the task complete.
- Never expose or commit API keys/secrets (use `.env`, which is
  git-ignored).
- Do not commit directly to `main` — use feature branches.
- Keep commits focused and use conventional commit messages.

## Current Milestone

Backend foundation setup (LangGraph wiring verified end to end via a CLI
entry point and a passthrough node).

## Completed Work

- Project structure (`backend/`, `agents/`, `graph/`, `frontend/`) established.
- `PakAssistState` defined.
- Minimal LangGraph graph (`START → passthrough → END`) built and verified to compile/run.
- CLI entry point (`main.py`) wired to the graph.
- `requirements.txt`, `README.md`, `.gitignore` set up.

## Next Planned Work

Not yet scheduled/confirmed — do not begin without explicit instruction.
Likely candidates based on the project vision (see `ARCHITECTURE.md`):
a Planner Agent, intent/service routing, and eventually Knowledge/RAG,
Action, and Appointment agents.