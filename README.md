# PakAssist

PakAssist is an agentic AI assistant that helps Pakistani citizens understand and
navigate government and public services (e.g. driving licenses, passports,
appointments, and document requirements). The project is being built
incrementally, feature by feature.

## Current Stage

This stage sets up the backend foundation only:

- A `PakAssistState` shared state definition used by LangGraph.
- A minimal LangGraph graph with a single placeholder node, to confirm the
  graph compiles and runs correctly.
- A simple command-line entry point (`backend/main.py`) for testing the
  foundation.

No agents, RAG, document processing, appointment booking, or frontend
functionality have been implemented yet — those will be added in later
stages on top of this foundation.

## Project Structure

```
PakAssist/
│
├── backend/
│   ├── main.py              # Application entry point
│   ├── agents/               # Future home for agent implementations
│   └── graph/
│       ├── state.py          # Shared LangGraph state
│       └── graph.py          # LangGraph graph construction
│
├── frontend/                 # Future frontend (not implemented yet)
├── requirements.txt
└── README.md
```

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root for any environment variables
   (e.g. API keys) you'll need as the project grows. None are required yet
   at this stage.

## Running

From the project root:

```bash
python -m backend.main
```

You'll be prompted for input in the terminal. The input is passed through
the LangGraph graph and the resulting state is printed back — this confirms
the backend foundation is wired correctly.

## Roadmap

Future stages will add: a planner agent, intent/service routing, document
understanding, RAG over official government sources, Urdu/regional language
and voice interaction, checklists, and action-based workflows.