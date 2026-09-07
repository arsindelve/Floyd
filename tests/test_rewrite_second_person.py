"""Tests for the RewriteSecondPerson preprocessor (already on Chat Completions).

Rewritten to patch the OpenAI client seam directly rather than fake the whole `openai` module,
which broke once the module started importing `openai.types.chat`.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import rewrite_second_person as rsp


def _fake_client(content):
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )
    return client


def test_rewrite_returns_trimmed_content():
    with patch.object(rsp, 'OpenAI', return_value=_fake_client('  go west  ')):
        result = rsp.RewriteSecondPerson().rewrite('floyd, go west')
    assert result == 'go west'


def test_lambda_handler_success():
    fake = MagicMock()
    fake.rewrite.return_value = 'rewritten'
    with patch.object(rsp, 'RewriteSecondPerson', return_value=fake):
        resp = rsp.lambda_handler({'prompt': 'hello'})
    assert resp['statusCode'] == 200
    assert json.loads(resp['body'])['results']['single_message'] == 'rewritten'
    fake.rewrite.assert_called_once_with('hello')


def test_lambda_handler_missing_prompt():
    resp = rsp.lambda_handler({})
    assert resp['statusCode'] == 400
    assert json.loads(resp['body'])['error'] == 'Prompt is required'
