# PakAssist — Multimodal RAG Foundation

Hackathon-sized RAG pipeline for the Knowledge route: Markdown knowledge
base + user-uploaded images/PDFs → MiniLM embeddings → FAISS → Gemini
grounded generation.

> **Note:** `knowledge_base/passport.md`, `driving_license.md`, and
> `sources.md` in this repo are **placeholders**, not Member 4's real
> content — I only had the team's README files describing that content,
> not the files themselves. Drop the real files into `knowledge_base/`
> before rebuilding the index for actual use.

## 1. Install

```bash
pip install -r requirements.txt
cp .env.example .env
# then edit .env and set GEMINI_API_KEY
```

## 2. Build/rebuild the knowledge index

Run this whenever `knowledge_base/*.md` changes:

```bash
python scripts/build_index.py
```

This loads every `.md` file (except `sources.md`), splits it into
section-aware chunks, embeds them with
`sentence-transformers/all-MiniLM-L6-v2`, and saves a FAISS index to
`data/faiss_index/`.

## 3. Test retrieval only (no Gemini call)

```bash
python scripts/query_test.py "What documents do I need for a driving license?"
python scripts/query_test.py "What are the requirements for a Pakistani passport?"
```

Each result shows its score, service, section, source URL, and confidence
— useful for sanity-checking retrieval before wiring in generation.

## 4. Test an image or PDF

```python
from backend.rag.multimodal import extract_text_from_image, extract_text_from_pdf

print(extract_text_from_image("path/to/photo.jpg"))
print(extract_text_from_pdf("path/to/document.pdf"))
```

Requires `GEMINI_API_KEY` to be set (image extraction, and scanned-page
extraction, call Gemini; normal PDF text extraction uses PyMuPDF only and
needs no API key).

## 5. Run the Knowledge Agent end-to-end

```python
from backend.agents.knowledge import knowledge_agent

state = {
    "user_query": "What documents do I need for a driving license?",
    "uploaded_files": [],  # optional: ["path/to/id_photo.jpg"]
}
result = knowledge_agent(state)
print(result["knowledge_response"])
print(result["sources"])
```

## 6. Run tests

```bash
pytest tests/ -v
```

Tests that need `sentence-transformers`/`faiss` skip cleanly if those
aren't installed (`pytest.importorskip`). Gemini-dependent behavior is
tested with mocks, so no live API key or network call is required to run
the suite.

## Where this plugs into the real repo

- `backend/graph/state.py` — copy the two new fields (`knowledge_response`,
  `sources`) into the real `state.py` instead of replacing it.
- `backend/agents/knowledge.py` — this is the real deliverable; wire it
  into the existing Knowledge node in place of `backend/agents/planner.py`
  and `backend/graph/graph.py`, which are illustrative stand-ins only
  (I don't have the actual planner/graph code).
- `backend/rag/*` — self-contained, no changes needed to plug in.
