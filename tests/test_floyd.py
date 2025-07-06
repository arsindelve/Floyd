import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest


def load_floyd(monkeypatch):
    """Import floyd module with a mocked openai dependency."""
    client = MagicMock()
    openai_module = ModuleType('openai')
    openai_module.OpenAI = MagicMock(return_value=client)
    monkeypatch.setitem(sys.modules, 'openai', openai_module)
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(repo_root))
    if 'floyd' in sys.modules:
        del sys.modules['floyd']
    floyd = importlib.import_module('floyd')
    return floyd, client, openai_module.OpenAI


def test_init_sets_attributes(monkeypatch):
    floyd, client, openai_cls = load_floyd(monkeypatch)
    instance = floyd.Floyd('aid', api_key='key')
    openai_cls.assert_called_with(api_key='key')
    assert instance.client is client
    assert instance.assistant_id == 'aid'


def test_create_thread(monkeypatch):
    floyd, client, _ = load_floyd(monkeypatch)
    client.beta.threads.create.return_value = SimpleNamespace(id='tid')
    instance = floyd.Floyd('aid')
    tid = instance.create_thread()
    assert tid == 'tid'
    client.beta.threads.create.assert_called_once_with()


def test_add_message(monkeypatch):
    floyd, client, _ = load_floyd(monkeypatch)
    instance = floyd.Floyd('aid')
    instance.add_message('tid', 'hello')
    client.beta.threads.messages.create.assert_called_once_with(
        thread_id='tid', role='user', content='hello'
    )


def test_run_assistant(monkeypatch):
    floyd, client, _ = load_floyd(monkeypatch)
    client.beta.threads.runs.create.return_value = SimpleNamespace(id='run1')
    client.beta.threads.runs.retrieve.side_effect = [
        SimpleNamespace(id='run1', status='in_progress'),
        SimpleNamespace(id='run1', status='completed'),
    ]
    assistant_msg = SimpleNamespace(
        role='assistant',
        content=[SimpleNamespace(text=SimpleNamespace(value='hi'))]
    )
    client.beta.threads.messages.list.return_value = SimpleNamespace(data=[assistant_msg])
    monkeypatch.setattr(floyd.time, 'sleep', lambda x: None)

    instance = floyd.Floyd('aid')
    result = instance.run_assistant('tid')
    assert result == {'role': 'assistant', 'content': 'hi'}
    client.beta.threads.runs.create.assert_called_once_with(
        thread_id='tid', assistant_id='aid', instructions=None
    )
    assert client.beta.threads.runs.retrieve.call_count == 2


def test_run_assistant_no_message(monkeypatch):
    floyd, client, _ = load_floyd(monkeypatch)
    client.beta.threads.runs.create.return_value = SimpleNamespace(id='run1')
    client.beta.threads.runs.retrieve.return_value = SimpleNamespace(id='run1', status='completed')
    client.beta.threads.messages.list.return_value = SimpleNamespace(data=[])
    monkeypatch.setattr(floyd.time, 'sleep', lambda x: None)
    instance = floyd.Floyd('aid')
    result = instance.run_assistant('tid')
    assert result['content'] == 'No response generated'


def test_chat_creates_thread(monkeypatch):
    floyd, _, _ = load_floyd(monkeypatch)
    instance = floyd.Floyd('aid')
    monkeypatch.setattr(instance, 'create_thread', MagicMock(return_value='tid'))
    monkeypatch.setattr(instance, 'add_message', MagicMock())
    monkeypatch.setattr(instance, 'run_assistant', MagicMock(return_value={'role': 'assistant', 'content': 'resp'}))
    resp = instance.chat('hello')
    instance.create_thread.assert_called_once_with()
    instance.add_message.assert_called_once_with('tid', 'hello')
    instance.run_assistant.assert_called_once_with('tid', None)
    assert resp['content'] == 'resp'


def test_chat_existing_thread(monkeypatch):
    floyd, _, _ = load_floyd(monkeypatch)
    instance = floyd.Floyd('aid')
    monkeypatch.setattr(instance, 'create_thread', MagicMock())
    monkeypatch.setattr(instance, 'add_message', MagicMock())
    monkeypatch.setattr(instance, 'run_assistant', MagicMock(return_value={'role': 'assistant', 'content': 'resp'}))
    resp = instance.chat('hello', thread_id='tid')
    instance.create_thread.assert_not_called()
    instance.add_message.assert_called_once_with('tid', 'hello')
    instance.run_assistant.assert_called_once_with('tid', None)
    assert resp['content'] == 'resp'
