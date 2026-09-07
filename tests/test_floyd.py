"""Tests for Floyd's Chat Completions dispatcher (characters/floyd.py).

These replace the old Assistants-API tests (thread/run mocking), which went away with the
Assistants API on 2026-08-26. The seam under test is now a single chat.completions.create call
whose JSON reply carries Floyd's line plus the intent the game reads.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from characters.floyd import Floyd


def _fake_client(content):
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )
    return client


def _respond(content, prompt="floyd, hi"):
    with patch("characters.floyd.OpenAI", return_value=_fake_client(content)):
        return Floyd().respond(prompt)


def test_pickup_intent_yields_object_metadata():
    content = json.dumps({"message": 'Floyd shrugs. "If you say so."',
                          "intent": "PickUp", "object": "Board"})
    message, metadata = _respond(content, "floyd, take board")
    assert message == 'Floyd shrugs. "If you say so."'
    # assistant_type + a lower-cased object are exactly what FloydLocationBehaviors matches on.
    assert metadata == {"assistant_type": "PickUp", "parameters": {"object": "board"}}


def test_gosomewhere_intent_yields_direction_metadata():
    content = json.dumps({"message": "Okay, Floyd will look.",
                          "intent": "GoSomewhere", "direction": "North"})
    _, metadata = _respond(content, "floyd, go north")
    assert metadata == {"assistant_type": "GoSomewhere", "parameters": {"direction": "north"}}


def test_conversational_reply_has_no_parameters():
    content = json.dumps({"message": "Hello! Floyd is really glad you are here.",
                          "intent": "Conversational"})
    message, metadata = _respond(content, "floyd, hello")
    assert message.startswith("Hello!")
    assert metadata == {"assistant_type": "Conversational"}


def test_pickup_without_object_emits_no_parameters():
    # Defensive: an intent label with no slot value must not fabricate an empty parameter.
    content = json.dumps({"message": "Floyd is not sure what to grab.", "intent": "PickUp"})
    _, metadata = _respond(content, "floyd, take")
    assert metadata == {"assistant_type": "PickUp"}


def test_non_json_reply_falls_back_to_plain_message():
    message, metadata = _respond("Floyd waves happily.", "floyd, hi")
    assert message == "Floyd waves happily."
    assert metadata is None


def test_request_uses_json_mode_and_floyd_system_prompt():
    client = _fake_client(json.dumps({"message": "Hi", "intent": "Conversational"}))
    with patch("characters.floyd.OpenAI", return_value=client):
        Floyd().respond("floyd, hello")
    _, kwargs = client.chat.completions.create.call_args
    assert kwargs["response_format"] == {"type": "json_object"}
    assert kwargs["messages"][0]["role"] == "system"
    assert "You are Floyd" in kwargs["messages"][0]["content"]
    assert kwargs["messages"][1] == {"role": "user", "content": "floyd, hello"}
