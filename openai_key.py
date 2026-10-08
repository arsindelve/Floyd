"""
Where this Lambda gets its OpenAI key: the Secrets Manager secret OpenAiApiKey.

That secret is the single home for the key across ZorkAI's Lambdas (the Zork, Planetfall and
Stationfall game functions read the same one), so rotating it is one put-secret-value. The key used
to be a plain OPENAI_API_KEY in template.yaml, which is why template.yaml was gitignored.

Every OpenAI client here is built as OpenAI(), which reads OPENAI_API_KEY from the environment, so
this only has to make sure that variable is set before the first client is created. An existing
OPENAI_API_KEY wins, so local runs with a .env file never touch AWS.
"""
import logging
import os
from typing import Callable

ENV_VAR = "OPENAI_API_KEY"
SECRET_NAME = "OpenAiApiKey"

logger = logging.getLogger(__name__)


def _read_secret(secret_id: str) -> str:
    # Imported here so local runs and tests never need boto3; the Lambda runtime ships it.
    import boto3

    return boto3.client("secretsmanager").get_secret_value(SecretId=secret_id)["SecretString"]


def ensure_openai_key(fetch_secret: Callable[[str], str] = _read_secret) -> bool:
    """Make sure OPENAI_API_KEY holds a key, reading the secret if the environment has none.

    Never raises: if the secret is missing or unreadable the environment is left alone, so the
    OpenAI client fails on first use with its own clear "api_key must be set" error rather than
    the whole cold start dying here. Returns True when a key is now in the environment.
    """
    if os.environ.get(ENV_VAR, "").strip():
        return True

    try:
        secret = (fetch_secret(SECRET_NAME) or "").strip()
    except Exception:
        logger.exception("Could not read secret %s; OpenAI calls will fail.", SECRET_NAME)
        return False

    if not secret:
        logger.error("Secret %s is empty; OpenAI calls will fail.", SECRET_NAME)
        return False

    os.environ[ENV_VAR] = secret
    # print, not logger.info: the Lambda runtime drops INFO by default, and this line is the
    # CloudWatch evidence that the secret path ran.
    print(f"Resolved the OpenAI key from secret {SECRET_NAME}.")
    return True
