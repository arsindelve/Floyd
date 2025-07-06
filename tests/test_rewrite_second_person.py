import importlib
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock


def load_rewriter(monkeypatch):
    client = MagicMock()
    openai_module = ModuleType('openai')
    openai_module.OpenAI = MagicMock(return_value=client)
    monkeypatch.setitem(sys.modules, 'openai', openai_module)
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(repo_root))
    if 'floyd' in sys.modules:
        del sys.modules['floyd']
    if 'rewrite_second_person' in sys.modules:
        del sys.modules['rewrite_second_person']
    mod = importlib.import_module('rewrite_second_person')
    return mod, client, openai_module.OpenAI


def test_rewrite_returns_content(monkeypatch):
    mod, client, openai_cls = load_rewriter(monkeypatch)
    instance = mod.RewriteSecondPerson('aid')
    monkeypatch.setattr(instance, 'chat', MagicMock(return_value={'content': 'out'}))
    result = instance.rewrite('hi')
    instance.chat.assert_called_once_with('hi')
    assert result == 'out'
