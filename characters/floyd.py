"""
Floyd's conversational brain, on the OpenAI Chat Completions API.

This replaces the retired router + nine specialist Assistants that AskFloydAsync used to reach.
The Assistants API was sunset on 2026-08-26 (every /v1/assistants and /v1/threads call now 404s),
which took Floyd's whole directed-command path down with it. Only the *composite* behavior of that
system survived, as a corpus of live prod outputs, so rather than guess at nine hidden prompts this
consolidates everything into ONE call: a single Chat Completion both replies in Floyd's voice AND
classifies the imperative intent the game consumes (see prompts.FLOYD_SYSTEM_PROMPT).

The output contract is unchanged from the game's point of view: process() returns Floyd's line, and
get_metadata()/respond() surface metadata.assistant_type == "PickUp" (parameters {object: ...}) or
"GoSomewhere" (parameters {direction: ...}), exactly what FloydLocationBehaviors reads on the C# side.
"""
import json
from typing import Optional, Tuple

from openai import OpenAI

from prompts import FLOYD_SYSTEM_PROMPT

# gpt-4o matches the model the C# narrator-Floyd path uses, so both voices stay consistent.
MODEL = "gpt-4o"
TEMPERATURE = 0.8


class Floyd:
    """Floyd's conversational assistant (Chat Completions)."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)

    def respond(self, prompt: str) -> Tuple[str, Optional[dict]]:
        """Return (message, metadata) for what the player said to Floyd.

        metadata is {"assistant_type": <intent>} plus, for the two imperative intents the game acts
        on, {"parameters": {"object"|"direction": <value>}}. metadata is None only when the model
        fails to return the JSON contract, in which case the raw text becomes Floyd's line.
        """
        completion = self.client.chat.completions.create(
            model=MODEL,
            temperature=TEMPERATURE,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": FLOYD_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        raw = completion.choices[0].message.content or ""
        return self._parse(raw)

    @staticmethod
    def _parse(raw: str) -> Tuple[str, Optional[dict]]:
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            # The model ignored the JSON contract; treat the whole reply as Floyd's line so the
            # player still hears something in-character rather than nothing.
            return raw.strip(), None

        if not isinstance(data, dict):
            return raw.strip(), None

        message = str(data.get("message") or "").strip() or raw.strip()
        intent = str(data.get("intent") or "Conversational").strip() or "Conversational"

        parameters = {}
        if intent == "PickUp" and data.get("object"):
            parameters["object"] = str(data["object"]).strip().lower()
        elif intent == "GoSomewhere" and data.get("direction"):
            parameters["direction"] = str(data["direction"]).strip().lower()

        metadata = {"assistant_type": intent}
        if parameters:
            metadata["parameters"] = parameters
        return message, metadata
