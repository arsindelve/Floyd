import importlib
import json
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest


def load_main(monkeypatch, assistant_id='aid', router_id='rid', route_ids=None):
    """Import main module with mocked dependencies."""
    openai_module = ModuleType('openai')
    openai_module.OpenAI = MagicMock(return_value=MagicMock())
    monkeypatch.setitem(sys.modules, 'openai', openai_module)
    monkeypatch.setenv('OPENAI_FLOYD_BASIC_RESPONSE_ASSISTANT_ID', assistant_id)
    monkeypatch.setenv('OPENAI_ROUTER_ASSISTANT_ID', router_id)
    if route_ids:
        for name, val in route_ids.items():
            monkeypatch.setenv(f'OPENAI_{name.upper()}_ASSISTANT_ID', val)
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(repo_root))
    if 'floyd' in sys.modules:
        del sys.modules['floyd']
    if 'router' in sys.modules:
        del sys.modules['router']
    if 'main' in sys.modules:
        del sys.modules['main']
    if 'rewrite_second_person' in sys.modules:
        del sys.modules['rewrite_second_person']
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


def test_lambda_router(monkeypatch):
    main = load_main(
        monkeypatch,
        router_id='rid',
        route_ids={'ASKQUESTION': 'qid'}
    )
    mock_router = MagicMock()
    mock_router.route.return_value = 'AskQuestion'
    monkeypatch.setattr(main, 'Router', MagicMock(return_value=mock_router))
    mock_floyd = MagicMock()
    mock_floyd.chat.return_value = {'role': 'assistant', 'content': 'resp'}
    monkeypatch.setattr(main, 'Floyd', MagicMock(return_value=mock_floyd))
    event = {'assistant': 'router', 'prompt': 'hello'}
    resp = main.lambda_handler(event, None)
    assert resp['statusCode'] == 200
    data = json.loads(resp['body'])
    assert data['results']['single_message'] == 'resp'
    main.Router.assert_called_once_with('rid')
    mock_router.route.assert_called_once_with('hello')
    main.Floyd.assert_called_once_with('qid')
    mock_floyd.chat.assert_called_once_with('hello')



def test_lambda_exception(monkeypatch):
    main = load_main(monkeypatch)
    monkeypatch.setattr(main, 'Floyd', MagicMock(side_effect=Exception('boom')))
    event = {'assistant': 'basic_response', 'prompt': 'hello'}
    resp = main.lambda_handler(event, None)
    assert resp['statusCode'] == 500
    assert json.loads(resp['body'])['error'] == 'boom'
