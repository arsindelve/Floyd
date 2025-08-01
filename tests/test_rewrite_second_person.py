import importlib
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock


def load_rewriter(monkeypatch):
    client = MagicMock()
    openai_module = ModuleType('openai')
    openai_module.OpenAI = MagicMock(return_value=client)
    monkeypatch.setitem(sys.modules, 'openai', openai_module)
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(repo_root))
    if 'rewrite_second_person' in sys.modules:
        del sys.modules['rewrite_second_person']
    mod = importlib.import_module('rewrite_second_person')
    return mod, client, openai_module.OpenAI


def test_rewrite_returns_content(monkeypatch):
    mod, client, openai_cls = load_rewriter(monkeypatch)
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='out'))]
    )
    instance = mod.RewriteSecondPerson()
    result = instance.rewrite('hi')
    client.chat.completions.create.assert_called_once()
    assert result == 'out'


def test_lambda_handler_success(monkeypatch):
    mod, client, openai_cls = load_rewriter(monkeypatch)
    mock_rewriter = MagicMock()
    mock_rewriter.rewrite.return_value = 'rewritten'
    monkeypatch.setattr(mod, 'RewriteSecondPerson', MagicMock(return_value=mock_rewriter))
    event = {'prompt': 'hello'}
    resp = mod.lambda_handler(event, None)
    assert resp['statusCode'] == 200
    data = json.loads(resp['body'])
    assert data['results']['single_message'] == 'rewritten'
    mod.RewriteSecondPerson.assert_called_once_with()
    mock_rewriter.rewrite.assert_called_once_with('hello')


def test_lambda_handler_missing_prompt(monkeypatch):
    mod, _, _ = load_rewriter(monkeypatch)
    resp = mod.lambda_handler({}, None)
    assert resp['statusCode'] == 400
    assert json.loads(resp['body'])['error'] == 'Prompt is required'
