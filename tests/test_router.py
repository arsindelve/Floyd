import importlib
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock


def load_router(monkeypatch):
    """Import router module with mocked dependencies."""
    client = MagicMock()
    openai_module = ModuleType('openai')
    openai_module.OpenAI = MagicMock(return_value=client)
    monkeypatch.setitem(sys.modules, 'openai', openai_module)
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(repo_root))
    if 'floyd' in sys.modules:
        del sys.modules['floyd']
    if 'router' in sys.modules:
        del sys.modules['router']
    router = importlib.import_module('router')
    return router, client, openai_module.OpenAI


def test_route_returns_content(monkeypatch):
    router_mod, client, openai_cls = load_router(monkeypatch)
    instance = router_mod.Router('aid')
    monkeypatch.setattr(instance, 'chat', MagicMock(return_value={'content': 'AskQuestion'}))
    result = instance.route('hello')
    instance.chat.assert_called_once_with('hello')
    assert result == 'AskQuestion'
