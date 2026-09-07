"""Tests for the Lambda handler wiring (main.py) after the Chat Completions migration.

The floyd path no longer routes through a router assistant + assistant IDs; FloydAssistant now
delegates to characters.floyd.Floyd and surfaces its (message, metadata).
"""
import json
from unittest.mock import MagicMock, patch

import main


def test_lambda_missing_prompt_returns_400():
    resp = main.lambda_handler({'assistant': 'floyd'}, None)
    assert resp['statusCode'] == 400
    assert json.loads(resp['body'])['error'] == 'Prompt is required'


def test_lambda_unknown_assistant_returns_400():
    resp = main.lambda_handler({'assistant': 'nope', 'prompt': 'hi'}, None)
    assert resp['statusCode'] == 400
    assert 'Unknown assistant type' in json.loads(resp['body'])['error']


def test_lambda_floyd_success_passes_message_and_metadata_through():
    fake = MagicMock()
    fake.respond.return_value = ("Floyd waves.",
                                 {"assistant_type": "PickUp", "parameters": {"object": "board"}})
    with patch.object(main, 'Floyd', return_value=fake):
        resp = main.lambda_handler({'assistant': 'floyd', 'prompt': 'floyd, take board'}, None)
    assert resp['statusCode'] == 200
    results = json.loads(resp['body'])['results']
    assert results['single_message'] == 'Floyd waves.'
    assert results['metadata'] == {"assistant_type": "PickUp", "parameters": {"object": "board"}}
    fake.respond.assert_called_once_with('floyd, take board')


def test_lambda_floyd_conversational_omits_metadata_block_when_none():
    fake = MagicMock()
    fake.respond.return_value = ("Floyd beeps.", None)
    with patch.object(main, 'Floyd', return_value=fake):
        resp = main.lambda_handler({'assistant': 'floyd', 'prompt': 'floyd, hi'}, None)
    results = json.loads(resp['body'])['results']
    assert results['single_message'] == 'Floyd beeps.'
    assert 'metadata' not in results


def test_lambda_floyd_exception_returns_500_with_message():
    fake = MagicMock()
    fake.respond.side_effect = Exception('boom')
    with patch.object(main, 'Floyd', return_value=fake):
        resp = main.lambda_handler({'assistant': 'floyd', 'prompt': 'hi'}, None)
    assert resp['statusCode'] == 500
    assert json.loads(resp['body'])['error'] == 'boom'
