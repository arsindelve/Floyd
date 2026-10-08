"""Tests for openai_key.ensure_openai_key — where the Lambda gets its OpenAI key.

The key lives in the Secrets Manager secret OpenAiApiKey (shared with the ZorkAI game Lambdas), not
in the function's environment. OPENAI_API_KEY still wins when set, so local runs are unchanged.
"""
from unittest.mock import MagicMock

import pytest

import openai_key
from openai_key import ensure_openai_key, ENV_VAR, SECRET_NAME


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)


def test_existing_env_var_wins_and_secret_is_not_read(monkeypatch):
    monkeypatch.setenv(ENV_VAR, "sk-from-env")
    fetch = MagicMock()

    assert ensure_openai_key(fetch) is True
    fetch.assert_not_called()
    assert openai_key.os.environ[ENV_VAR] == "sk-from-env"


def test_missing_env_var_is_filled_from_the_secret():
    fetch = MagicMock(return_value="sk-from-secret")

    assert ensure_openai_key(fetch) is True
    fetch.assert_called_once_with(SECRET_NAME)
    assert openai_key.os.environ[ENV_VAR] == "sk-from-secret"


def test_secret_value_is_trimmed():
    assert ensure_openai_key(MagicMock(return_value="  sk-from-secret\n")) is True
    assert openai_key.os.environ[ENV_VAR] == "sk-from-secret"


def test_blank_env_var_counts_as_missing(monkeypatch):
    monkeypatch.setenv(ENV_VAR, "   ")

    assert ensure_openai_key(MagicMock(return_value="sk-from-secret")) is True
    assert openai_key.os.environ[ENV_VAR] == "sk-from-secret"


def test_blank_secret_leaves_env_untouched():
    assert ensure_openai_key(MagicMock(return_value="  ")) is False
    assert ENV_VAR not in openai_key.os.environ


def test_unreadable_secret_does_not_raise():
    # Failing here would take down the whole cold start; leaving the env empty instead lets the
    # OpenAI client raise its own explicit "api_key must be set" on the first call.
    assert ensure_openai_key(MagicMock(side_effect=RuntimeError("AccessDenied"))) is False
    assert ENV_VAR not in openai_key.os.environ
