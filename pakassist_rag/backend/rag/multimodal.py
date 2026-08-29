"""
Extracts textual representations from user-uploaded images and PDFs so they
can be embedded and retrieved the same way as knowledge-base text.

Uses the same `google-genai` client the Planner already uses (see
backend/agents/planner.py and PROJECT_CONTEXT.md), with the same AFC fix
applied: no `tools`, and automatic function calling explicitly disabled.
This module doesn't need structured JSON output (unlike the Planner) so it
skips `response_schema`, but keeps the AFC-disable setting for consistency
and safety.
"""

import os
from pathlib import Path
from typing import List, Tuple

MIN_CHARS_FOR_REAL_TEXT = 20  # below this, treat a PDF page as "likely scanned"

_IMAGE_EXTRACTION_PROMPT = (
    "You are helping extract information from a document image for a "
    "Pakistani government-services assistant. Describe, in plain text, "
    "every piece of factual information visible in this image that could "
    "help answer a citizen's question (form fields, printed text, dates, "
    "fees, stamps, instructions). Do not add any information that is not "
    "visible in the image. If the image is unclear or unrelated to a "
    "government service, say so briefly instead of guessing."
)

_client = None


def _get_client():
    global _client
    if _client is None:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=api_key)
    return _client


def _generate_content(contents):
    """Single place that calls Gemini — no tools, AFC disabled, matching the Planner's fix."""
    from google.genai import types

    client = _get_client()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    return (response.text or "").strip()


def extract_text_from_image(image_path: str, extra_context: str = "") -> str:
    """Use Gemini multimodal understanding to turn an image into text."""
    import PIL.Image

    prompt = _IMAGE_EXTRACTION_PROMPT
    if extra_context:
        prompt += f"\n\nUser-provided context: {extra_context}"

    # Load pixel data into memory and close the file handle before returning.
    # PIL.Image.open() is lazy and otherwise keeps the file open, which is
    # harmless on Linux/Mac but blocks a subsequent delete of the same file
    # on Windows (e.g. the temp PNG created for scanned PDF pages).
    with PIL.Image.open(image_path) as image:
        image.load()
        return _generate_content([prompt, image])


def extract_text_from_pdf(pdf_path: str) -> List[Tuple[int, str, str]]:
    """
    Extract text page-by-page from a PDF.

    Returns a list of (page_number, text, extraction_method) tuples, where
    extraction_method is "pymupdf" for normal text extraction or "gemini"
    for pages that looked scanned/image-heavy and were rasterized and sent
    to Gemini instead.
    """
    import fitz  # PyMuPDF

    results: List[Tuple[int, str, str]] = []
    doc = fitz.open(pdf_path)

    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            text = page.get_text().strip()

            if len(text) >= MIN_CHARS_FOR_REAL_TEXT:
                results.append((page_index + 1, text, "pymupdf"))
                continue

            # Likely a scanned/image-heavy page — rasterize and let Gemini read it.
            pix = page.get_pixmap(dpi=150)
            tmp_path = Path(pdf_path).with_suffix(f".page{page_index + 1}.png")
            pix.save(str(tmp_path))
            try:
                extracted = extract_text_from_image(str(tmp_path))
                results.append((page_index + 1, extracted, "gemini"))
            finally:
                tmp_path.unlink(missing_ok=True)
    finally:
        doc.close()

    return results