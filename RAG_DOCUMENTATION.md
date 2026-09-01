# PakAssist Multimodal RAG — Developer Documentation

This document explains what the RAG (Retrieval-Augmented Generation) system
in this delivery does, how its pieces fit together, and how to run/extend
it. It covers the `pakassist_rag` package as delivered, before the
project-specific integration edits (renaming `user_query`→`user_input`,
`knowledge_response`→`response`, switching to the `google-genai` client)
that were applied on top when merging into the real PakAssist repo. Folder
structure and file purposes below match the delivered zip.

---

## 1. What this system does

PakAssist's Knowledge route needs to answer citizen questions about
government services (e.g. "what documents do I need for a driving
license?") **grounded in trusted sources**, not the model's general
knowledge. This package implements that: it turns a folder of Markdown
service documents (and, optionally, a user-uploaded photo or PDF) into a
searchable index, retrieves the most relevant pieces for a given question,
and asks Gemini to answer **using only that retrieved material** — refusing
to guess when nothing relevant is found.

It intentionally does **not** implement: appointment booking, an Action
Agent, a frontend upload UI, authentication, a database, or advanced
retrieval (hybrid search/reranking/agentic retrieval). Those are explicitly
out of scope for this milestone.

---

## 2. Folder structure

```text
pakassist_rag/
├── .env.example                  # template for required environment variables
├── README.md                     # setup/usage quick-start
├── requirements.txt              # minimal dependency list
│
├── knowledge_base/                # the trusted service documents (input to RAG)
│   ├── passport.md                # one service = one Markdown file
│   ├── driving_license.md
│   └── sources.md                 # URL log — NOT ingested as retrievable content
│
├── backend/
│   ├── agents/
│   │   ├── knowledge.py           # ★ the Knowledge Agent — main integration point
│   │   └── planner.py             # illustrative stand-in only, see §7
│   │
│   ├── graph/
│   │   ├── state.py               # shared LangGraph state (TypedDict)
│   │   └── graph.py               # illustrative stand-in only, see §7
│   │
│   └── rag/                       # the actual RAG pipeline, framework-agnostic
│       ├── loader.py              # Markdown → section-aware RagDocuments
│       ├── chunker.py             # RagDocuments → embeddable RagChunks
│       ├── embeddings.py          # text → vectors (sentence-transformers)
│       ├── vector_store.py        # FAISS wrapper (add/search/save/load)
│       ├── multimodal.py          # image/PDF → text (Gemini + PyMuPDF)
│       └── retriever.py           # ties embeddings + vector_store together
│
├── scripts/
│   ├── build_index.py             # CLI: rebuild the FAISS index from knowledge_base/
│   └── query_test.py              # CLI: test retrieval only, no Gemini call
│
└── tests/
    ├── conftest.py                 # pytest path setup + kb_dir fixture
    ├── test_loader.py              # ingestion correctness
    ├── test_chunker.py             # chunking correctness
    ├── test_embeddings.py          # embedding shape/normalization
    ├── test_retrieval.py           # end-to-end retrieval quality
    ├── test_unknown_query.py       # no-hallucination fallback (mocked)
    └── test_multimodal.py          # image/PDF extraction (mocked Gemini calls)
```

---

## 3. End-to-end data flow

### 3a. Building the index (offline, run whenever `knowledge_base/*.md` changes)

```text
knowledge_base/*.md
      │
      ▼
loader.py          — splits each file on "## Heading" sections, pulls
                      source_url/confidence out of the "Metadata" section,
                      and stamps every other section with that same
                      metadata → one RagDocument per section
      │
      ▼
chunker.py         — sections that already fit in max_chars (default 800)
                      become exactly one chunk; longer sections are split
                      on paragraph boundaries with a configurable overlap
                      → list of RagChunk(text, metadata)
      │
      ▼
embeddings.py      — sentence-transformers/all-MiniLM-L6-v2 embeds each
                      chunk's text, L2-normalized (so inner product ==
                      cosine similarity)
      │
      ▼
vector_store.py    — vectors + texts + metadata go into a FAISS
                      IndexFlatIP, then persisted to disk
                      (data/faiss_index/index.faiss + store.pkl)
```

Run with: `python scripts/build_index.py`

### 3b. Answering a question (online, per user turn)

```text
User's question (state["user_input"])
      │
      ▼
retriever.py       — embeds the query the same way, searches the
                      persisted knowledge-base FAISS index (and, if the
                      user uploaded a file this turn, an in-memory
                      per-session FAISS index built from it — see 3c)
      │
      ▼
  results below min_score (default 0.15)?
      │                              │
     yes                            no
      │                              │
      ▼                              ▼
"I couldn't find reliable      Build a numbered, source-labeled
information..." — returned      context block from the top-k chunks
directly, Gemini is NEVER            │
called for this turn                 ▼
                                Gemini (system prompt forces it to
                                answer only from the context, flag
                                low-confidence info, and say what's
                                missing rather than guess)
                                      │
                                      ▼
                                state["response"] = answer
                                state["sources"]  = deduped list of
                                                     {label, origin,
                                                     service, section,
                                                     source_url,
                                                     confidence}
```

This is implemented in `backend/agents/knowledge.py::knowledge_agent()`,
which is the single function meant to be wired into the LangGraph
"knowledge" node.

### 3c. Handling an uploaded image or PDF (optional, same turn)

```text
uploaded_files: ["photo.jpg"] or ["form.pdf"]
      │
      ▼
multimodal.py
  ├── image (.png/.jpg/.jpeg/.webp)
  │     → Gemini multimodal call describes everything factual visible
  │       in the image, in plain text
  │
  └── PDF
        → PyMuPDF extracts real text per page
        → any page with < 20 extractable characters is treated as
          "likely scanned": rasterized to PNG and sent through the same
          Gemini image path instead
      │
      ▼
Each page/image becomes a RagDocument (document_type="user_image" or
"user_pdf") → chunked → embedded → added to a FAISS index that lives
only in memory for that session (never written to disk, never mixed
into the persisted knowledge-base index)
      │
      ▼
retriever.retrieve() merges knowledge-base + user-upload results, but
tags each one's `origin` so the UI/agent can always tell which is which
```

Nothing here uses Gemini's Automatic Function Calling (AFC) — every
`generate_content` call passes no `tools` argument, matching the
project's existing AFC fix.

---

## 4. Module reference

| File | Responsibility | Key exports |
|---|---|---|
| `backend/rag/loader.py` | Parse Markdown into per-section documents; extract file-level `source_url`/`confidence` from the "Metadata" section | `RagDocument`, `load_knowledge_base()`, `load_markdown_file()` |
| `backend/rag/chunker.py` | Turn documents into size-bounded, metadata-preserving chunks | `RagChunk`, `chunk_documents()` |
| `backend/rag/embeddings.py` | Lazy-loaded singleton around `SentenceTransformer`; normalizes output | `embed_texts()`, `get_embedder()` |
| `backend/rag/vector_store.py` | FAISS `IndexFlatIP` wrapper with save/load; the only file that imports `faiss` directly, so it can be swapped later | `FaissVectorStore` |
| `backend/rag/multimodal.py` | Gemini image understanding + PyMuPDF/Gemini PDF text extraction | `extract_text_from_image()`, `extract_text_from_pdf()` |
| `backend/rag/retriever.py` | Combines the persisted KB store with an ephemeral per-session user-upload store; applies `min_score` filtering | `Retriever`, `RetrievedChunk` |
| `backend/agents/knowledge.py` | The Knowledge Agent: orchestrates retrieval + uploaded-file ingestion + grounded generation; owns the no-hallucination fallback | `knowledge_agent()` |
| `backend/graph/state.py` | Shared `TypedDict` state contract | `PakAssistState`, `SourceRef` |

---

## 5. Configuration (environment variables)

| Variable | Purpose | Default |
|---|---|---|
| `GEMINI_API_KEY` | Auth for Gemini calls (image/PDF extraction + answer generation) | *(required, no default)* |
| `GEMINI_MODEL` | Which Gemini model to call | `gemini-2.5-flash` |
| `EMBEDDING_MODEL` | Sentence-transformers model name | `sentence-transformers/all-MiniLM-L6-v2` |
| `KB_DIR` | Folder of Markdown service docs | `knowledge_base` |
| `KB_INDEX_DIR` | Where the built FAISS index is saved/loaded | `data/faiss_index` |
| `RAG_TOP_K` | Max chunks returned per query | `5` |
| `RAG_MIN_SCORE` | Cosine-similarity floor below which a chunk is discarded | `0.15` |

None of these are hardcoded anywhere in the code — all read via `os.getenv`.

---

## 6. Design decisions worth knowing (and re-checking)

- **Section = smallest retrievable unit.** A Markdown "## Required
  documents" heading becomes its own chunk whenever it fits under
  `max_chars` (800 by default), so a query like "what documents do I
  need" retrieves that section precisely instead of the whole service
  page. Only oversized sections get further split.
- **Metadata inheritance.** Only the file's "## Metadata" section is
  parsed for `source_url`/`confidence`; every other section in that file
  inherits those two values. If a file has no Metadata section, both are
  `None` — this is silent, not an error, so it's worth spot-checking new
  knowledge-base files have one.
- **No-context short-circuit.** If retrieval returns nothing above
  `RAG_MIN_SCORE`, the agent returns the safe fallback message and
  **skips the Gemini call entirely** — cheaper and removes an entire class
  of hallucination risk, rather than relying on prompt instructions alone.
- **User uploads never touch the persisted index.** They're embedded into
  a fresh, in-memory `FaissVectorStore` per `Retriever` instance/session,
  so one user's uploaded document can never leak into another user's
  retrieval results or into the on-disk knowledge base.
- **Scanned-PDF detection is a simple heuristic** — any page with fewer
  than 20 characters of extractable text is treated as scanned and sent
  to Gemini as an image instead. This is intentionally simple for a
  hackathon; a page with a large image and one short caption would also
  trigger this path, which is fine (Gemini just describes what's there).
- **`RAG_MIN_SCORE` of 0.15 is a starting guess**, not a tuned value —
  worth revisiting once there's real query traffic to check against.

---

## 7. Files that are illustrative only

`backend/agents/planner.py` and `backend/graph/graph.py` in this delivery
are **minimal mocks**, built only so the Knowledge Agent could be
demonstrated wired into a Planner → routing → agent flow without access to
the real PakAssist Planner/graph code. They are **not** meant to be merged
into the real project — the real repo already has its own `planner.py`
and `graph.py`; only `backend/agents/knowledge.py` needs to be added as a
new node function there, and `backend/graph/state.py` needs one new field
(`sources`) merged into the real state contract.

---

## 8. Testing

```bash
pip install -r requirements.txt
pytest tests/ -v
```

- Tests requiring `sentence-transformers`/`faiss`/PyMuPDF/Pillow skip
  cleanly via `pytest.importorskip` if those packages aren't installed.
- All Gemini-dependent behavior is tested with `unittest.mock.patch` —
  no network call or API key is needed to run the suite, and the tests
  assert that `tools` is never passed and AFC is explicitly disabled on
  every call.

---

## 9. Known limitations

- `knowledge_base/*.md` in this delivery are **placeholder** stand-ins,
  not the team's real, verified service documents.
- Retrieval is pure semantic similarity — no hybrid search, reranking, or
  agentic multi-step retrieval.
- Only `.pdf` and common image formats are handled; other upload types
  are silently ignored by `_extract_uploaded_files`.
- The vector store is a flat, in-memory-loaded FAISS index — fine at
  hackathon scale, but would need an approximate index (e.g. IVF/HNSW) if
  the knowledge base grew into the tens of thousands of chunks.