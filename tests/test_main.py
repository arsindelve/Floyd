import importlib
import json
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest


def load_main(monkeypatch, assistant_id='aid'):
    """Import main module with mocked dependencies."""
    openai_module = ModuleType('openai')
    openai_module.OpenAI = MagicMock(return_value=MagicMock())
    monkeypatch.setitem(sys.modules, 'openai', openai_module)
    monkeypatch.setenv('OPENAI_FLOYD_BASIC_RESPONSE_ASSISTANT_ID', assistant_id)
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(repo_root))
    if 'floyd' in sys.modules:
        del sys.modules['floyd']
    if 'main' in sys.modules:
        del sys.modules['main']
    main = importlib.import_module('main')
    return main


def test_lambda_missing_prompt(monkeypatch):
    main = load_main(monkeypatch)
    event = {'assistant': 'basic_response'}
    resp = main.lambda_handler(event, None)
    assert resp['statusCode'] == 400
    assert json.loads(resp['body'])['error'] == 'Prompt is required'


def test_lambda_unknown_assistant(monkeypatch):
    main = load_main(monkeypatch)
    event = {'assistant': 'unknown', 'prompt': 'hi'}
    resp = main.lambda_handler(event, None)
    assert resp['statusCode'] == 400
    assert json.loads(resp['body'])['error'] == 'Unknown assistant type'


def test_lambda_success(monkeypatch):
    main = load_main(monkeypatch, assistant_id='aid')
    mock_floyd = MagicMock()
    mock_floyd.chat.return_value = {'role': 'assistant', 'content': 'resp'}
    monkeypatch.setattr(main, 'Floyd', MagicMock(return_value=mock_floyd))
    event = {'assistant': 'basic_response', 'prompt': 'hello'}
    resp = main.lambda_handler(event, None)
    assert resp['statusCode'] == 200
    data = json.loads(resp['body'])
    assert data['results']['single_message'] == 'resp'
    main.Floyd.assert_called_once_with('aid')
    mock_floyd.chat.assert_called_once_with('hello')


def test_lambda_exception(monkeypatch):
    main = load_main(monkeypatch)
    monkeypatch.setattr(main, 'Floyd', MagicMock(side_effect=Exception('boom')))
    event = {'assistant': 'basic_response', 'prompt': 'hello'}
    resp = main.lambda_handler(event, None)
    assert resp['statusCode'] == 500
    assert json.loads(resp['body'])['error'] == 'boom'
