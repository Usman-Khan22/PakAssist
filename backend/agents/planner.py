"""
Planner Agent for PakAssist.

Responsible for interpreting a user's raw input and determining:
- intent
- service_type
- next_step

Calls Gemini for a single plain text-in / JSON-out completion (no
function/tool calling is configured), and validates the result against
PlannerOutput before it's allowed to flow into the graph state.


"""

import json
import os
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError


class PlannerOutput(BaseModel):
    """Structured output produced by the Planner Agent."""

    intent: str = Field(
        ...,
        description="User's high-level goal, e.g. 'apply_for_service', "
        "'renew_service', 'book_appointment'. Use 'unknown' if unclear.",
    )
    service_type: str = Field(
        ...,
        description="Government service involved, e.g. 'driving_license', "
        "'passport'. Use 'unknown' if unclear — never guess a specific service.",
    )
    next_step: Literal["knowledge", "action", "appointment", "clarify"] = Field(
        ..., description="Which downstream capability this should eventually route to."
    )


class PlannerError(RuntimeError):
    """Raised when the Planner Agent fails to produce valid structured output."""


_SYSTEM_PROMPT = """You are the Planner for PakAssist, an assistant that helps \
Pakistani citizens navigate public/government services (e.g. driving licenses, \
passports, appointments).

Given a single user message (which may be in English, Urdu, or Roman Urdu), \
determine:

- intent: the user's high-level goal, in short snake_case (e.g. \
"apply_for_service", "renew_service", "book_appointment"). Use "unknown" if unclear.
- service_type: the specific government service involved (e.g. "driving_license", \
"passport"). Use "unknown" if it isn't clearly implied by the message — never \
invent or guess a specific service.
- next_step: which downstream capability this should eventually go to.
  - "knowledge"   - the user wants information or guidance about a service.
  - "action"      - the user wants to perform a concrete action (apply, renew, etc.).
  - "appointment" - the user wants to book or check an appointment.
  - "clarify"     - the request is ambiguous, off-topic, or you're not confident \
enough to classify it.

If you are unsure, prefer "clarify" with "unknown" intent/service_type rather than \
guessing. Respond only with the requested structured fields — no extra commentary.
"""


def _get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise PlannerError("GEMINI_API_KEY is not set in the environment.")
    return genai.Client(api_key=api_key)


def run_planner(user_input: str) -> PlannerOutput:
    """Interpret `user_input` and return validated planner output.

    Raises:
        PlannerError: if the API call fails, or the response doesn't
            match the expected schema.
    """
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    client = _get_client()

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=PlannerOutput,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )
    except Exception as exc:
        raise PlannerError(f"Gemini API call failed: {exc}") from exc

    raw_text = getattr(response, "text", None)
    if not raw_text:
        raise PlannerError("Gemini returned an empty response.")

    try:
        data = json.loads(raw_text)
        return PlannerOutput.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise PlannerError(f"Planner returned invalid structured output: {exc}") from exc