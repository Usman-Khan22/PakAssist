from typing import TypedDict


class PakAssistState(TypedDict):
    user_input: str
    intent: str
    service_type: str
    next_step: str
    response: str