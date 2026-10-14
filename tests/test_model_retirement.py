"""Guards for OpenAI's 2027-01-14 retirement of gpt-4o, gpt-4o-mini, gpt-4.1 and gpt-4.1-mini.

Once a model is retired every call to it fails, so a stray id left behind in the Lambda takes a
character down on the retirement date. These tests keep the retired ids out of production code, and
pin that each request really is sent with the module's configured model (so changing MODEL changes
behavior, and the eval harnesses -- which import MODEL -- test what production runs).
"""
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import rewrite_second_person as rsp
from characters import floyd as floyd_module

RETIRED = {"gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"}
ROOT = Path(__file__).resolve().parent.parent


def _client(content):
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )
    return client


def test_configured_models_are_not_retired():
    assert floyd_module.MODEL not in RETIRED
    assert rsp.MODEL not in RETIRED


def test_no_production_source_hardcodes_a_retired_model_id():
    # Production code only: tests/ may name the ids (this file does) and eval/ is a harness.
    sources = [p for p in ROOT.rglob("*.py")
               if not {"tests", "eval", ".venv", "venv"} & set(p.relative_to(ROOT).parts)
               and not p.name.startswith(("manual_test_", "test_"))]
    assert sources, "expected to find the Lambda's own source files"

    literal = re.compile(r"""["'](gpt-4o(?:-mini)?|gpt-4\.1(?:-mini)?)(?:-[\w.]+)?["']""")
    offenders = [f"{p.relative_to(ROOT)}:{n}: {line.strip()}"
                 for p in sources
                 for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
                 if literal.search(line) and not line.lstrip().startswith("#")]
    assert not offenders, "retired OpenAI model id still referenced:\n" + "\n".join(offenders)


def test_floyd_request_uses_configured_model_and_temperature():
    client = _client('{"message": "Hi", "intent": "Conversational"}')
    with patch("characters.floyd.OpenAI", return_value=client):
        floyd_module.Floyd().respond("floyd, hello")
    _, kwargs = client.chat.completions.create.call_args
    assert kwargs["model"] == floyd_module.MODEL
    assert kwargs["temperature"] == floyd_module.TEMPERATURE


def test_rewrite_request_uses_configured_model_and_temperature():
    client = _client("go west")
    with patch.object(rsp, "OpenAI", return_value=client):
        rsp.RewriteSecondPerson().rewrite("floyd, go west")
    _, kwargs = client.chat.completions.create.call_args
    assert kwargs["model"] == rsp.MODEL
    assert kwargs["temperature"] == rsp.TEMPERATURE
