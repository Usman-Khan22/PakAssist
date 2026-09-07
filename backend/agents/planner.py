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
from typing import Any, Literal, Mapping

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
    Understand natural Urdu and Roman Urdu requests such as "mujhe passport
    banwana hai", "documents kya chahiye", "fee kitni hai", "office kahan hai",
    and "appointment book karni hai" using the same intents as English.
- next_step: which downstream capability this should eventually go to.
  - "knowledge"   - the user wants information or guidance about a service.
    Requirements/checklist questions and fee/cost questions must use this route.
    Use intent "requirements_checklist" for documents/what-to-bring requests,
    and "fee_lookup" for fee or cost requests.
    Broad goals such as applying for, getting, or renewing a supported service
    are journey guidance, not executable actions. Use intent "service_journey"
    and next_step "knowledge".
    Requests to inspect, read, explain, summarize, identify, extract, or describe
    an uploaded image, document, notice, form, letter, or screenshot also use
    "knowledge". Use intent "inspect_upload". The service_type may remain
    "unknown" when the user is only asking what the uploaded content says.
  - "action"      - the user wants a supported executable operation, such as
    locating a service center/office. For a service-center lookup, use intent
    "service_center_lookup". For prototype appointment availability, use intent
    "check_slots" and next_step "action". For a prototype slot booking, use
    intent "book_slot" and next_step "action".
    For a request to show journey/progress or what remains, use intent
    "journey_summary" and next_step "action".
  - "appointment" - reserved for a real appointment capability that is not
    currently connected.
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


def _planner_input(user_input: str, context: Mapping[str, Any] | None) -> str:
    """Build a compact turn prompt without adding full conversation history."""
    if not context:
        return user_input
    return (
        "Current conversation context (use only when the new message depends on "
        "it; explicit service changes take precedence):\n"
        f"{json.dumps(dict(context), ensure_ascii=False)}\n\n"
        f"New user message:\n{user_input}"
    )


def run_planner(
    user_input: str, context: Mapping[str, Any] | None = None
) -> PlannerOutput:
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
            contents=_planner_input(user_input, context),
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
