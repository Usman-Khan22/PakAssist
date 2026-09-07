"""
Planner Agent for PakAssist.

Responsible for interpreting a user's raw input and determining:
- intent
- service_type
- next_step

Calls Gemini for a single plain text-in / JSON-out completion
and validates the result against PlannerOutput before it flows
into the graph state.
"""

import json
import os
import time
from typing import Any, Literal, Mapping

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError


class PlannerOutput(BaseModel):
    """Structured output produced by the Planner Agent."""

    intent: str = Field(
        ...,
        description=(
            "User's high-level goal, e.g. 'apply_for_service', "
            "'renew_service', 'book_appointment'. "
            "Use 'unknown' if unclear."
        ),
    )

    service_type: str = Field(
        ...,
        description=(
            "Government service involved, e.g. 'driving_license', "
            "'passport'. Use 'unknown' if unclear. "
            "Never guess a specific service."
        ),
    )

    next_step: Literal[
        "knowledge",
        "action",
        "appointment",
        "clarify",
    ] = Field(
        ...,
        description=(
            "Which downstream capability this should eventually route to."
        ),
    )


class PlannerError(RuntimeError):
    """Raised when the Planner Agent fails to produce valid structured output."""


_SYSTEM_PROMPT = """You are the Planner for PakAssist, an assistant that helps
Pakistani citizens navigate public/government services such as driving licenses,
passports, and appointments.

Given a single user message, which may be in English, Urdu, Roman Urdu,
or mixed Urdu-English, determine:

- intent:
  The user's high-level goal in short snake_case.

  Examples:
  "apply_for_service"
  "renew_service"
  "book_appointment"

  Use "unknown" if unclear.

- service_type:
  The specific government service involved.

  Examples:
  "driving_license"
  "passport"

  Use "unknown" if it is not clearly implied by the message.
  Never invent or guess a specific service.

- next_step:
  Which downstream capability the request should route to.

Routing rules:

- "knowledge"
  Use when the user wants information or guidance about a service.

  Requirements/checklist questions and fee/cost questions must use this route.

  Use intent "requirements_checklist" for:
  - required documents
  - what documents are needed
  - what to bring
  - checklist requests

  Use intent "fee_lookup" for:
  - fee
  - fees
  - cost
  - price
  - how much

  Broad goals such as applying for, getting, or renewing a supported
  government service are journey guidance, not executable actions.

  For those requests use:
  intent = "service_journey"
  next_step = "knowledge"

  Requests to inspect, read, explain, or describe information visible
  in an uploaded image or document also use "knowledge".

  For uploaded content inspection use:
  intent = "inspect_upload"

- "action"
  Use when the user wants a supported executable operation.

  For locating a service center or office use:
  intent = "service_center_lookup"

  For prototype appointment availability use:
  intent = "check_slots"
  next_step = "action"

  For prototype slot booking use:
  intent = "book_slot"
  next_step = "action"

  For a request to show journey progress or what remains use:
  intent = "journey_summary"
  next_step = "action"

- "appointment"
  Reserved for a real appointment capability that is not currently connected.

- "clarify"
  Use when the request is ambiguous, off-topic, or you are not confident
  enough to classify it.

If unsure, prefer:
intent = "unknown"
service_type = "unknown"
next_step = "clarify"

Do not guess.

Respond only with the requested structured fields.
Do not include extra commentary.
"""


def _get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise PlannerError(
            "GEMINI_API_KEY is not set in the environment."
        )

    return genai.Client(api_key=api_key)


def _planner_input(
    user_input: str,
    context: Mapping[str, Any] | None,
) -> str:
    """Build a compact turn prompt without adding full conversation history."""

    if not context:
        return user_input

    return (
        "Current conversation context "
        "(use only when the new message depends on it; "
        "explicit service changes take precedence):\n"
        f"{json.dumps(dict(context), ensure_ascii=False)}\n\n"
        f"New user message:\n{user_input}"
    )


def run_planner(
    user_input: str,
    context: Mapping[str, Any] | None = None,
) -> PlannerOutput:
    """
    Interpret user_input and return validated planner output.

    Tries the primary Planner model first.
    If the primary model keeps failing, switches to the fallback model.

    Raises:
        PlannerError:
            If all model attempts fail or the response is invalid.
    """

    primary_model = os.environ.get(
        "PLANNER_MODEL",
        "gemini-3.5-flash-lite",
    )

    fallback_model = os.environ.get(
        "PLANNER_FALLBACK_MODEL",
        "gemini-3.1-flash-lite",
    )

    client = _get_client()

    models_to_try = [
        primary_model,
        fallback_model,
    ]

    response = None
    final_error = None

    for model_name in models_to_try:

        print(f"Planner using model: {model_name}")

        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=_planner_input(
                        user_input,
                        context,
                    ),
                    config=types.GenerateContentConfig(
                        system_instruction=_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=PlannerOutput,
                        automatic_function_calling=(
                            types.AutomaticFunctionCallingConfig(
                                disable=True
                            )
                        ),
                    ),
                )

                final_error = None

                print(
                    f"Planner succeeded with model: {model_name}"
                )

                break

            except Exception as exc:
                final_error = exc

                print(
                    f"Planner {model_name} attempt "
                    f"{attempt + 1}/2 failed:",
                    exc,
                )

                if attempt < 1:
                    print(
                        "Retrying in 1.5 seconds..."
                    )

                    time.sleep(1.5)

        if response is not None:
            break

        print(
            f"Planner switching from {model_name} "
            "to fallback model..."
        )

    if response is None:
        raise PlannerError(
            f"All Planner models failed: {final_error}"
        ) from final_error

    raw_text = getattr(
        response,
        "text",
        None,
    )

    if not raw_text:
        raise PlannerError(
            "Gemini returned an empty Planner response."
        )

    try:
        data = json.loads(raw_text)

        return PlannerOutput.model_validate(
            data
        )

    except (
        json.JSONDecodeError,
        ValidationError,
    ) as exc:
        raise PlannerError(
            f"Planner returned invalid structured output: {exc}"
        ) from exc