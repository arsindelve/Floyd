import os

# main.py resolves the OpenAI key at import time, reading Secrets Manager when OPENAI_API_KEY is
# unset. A dummy key here keeps the suite offline. test_openai_key.py clears it per test.
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
