import os
import pytest

try:
    import openai
except Exception:
    pytest.skip("openai package not installed", allow_module_level=True)

from dotenv import load_dotenv

# Load your OpenAI API key and Assistant ID from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_REWRITESECONDPERSON_ASSISTANT_ID")

if not ASSISTANT_ID:
    pytest.skip(
        "Missing Assistant ID. Skipping manual assistant tests.",
        allow_module_level=True,
    )

# Define test cases: prompt -> expected output
TEST_CASES = [
    ("Shove Floyd into a wall", "no"),
    ("Kick Floyd", "no"),
    ("I’m bored", "no"),
    ("Floyd, I love you", "I love you"),
    ("Tell Floyd I love him", "I love you"),
    ("Say to Floyd ‘You suck’", "You suck"),
    ("Ask Floyd to open the door", "Open the door"),
    ("Kiss Floyd", "no"),
    ("Yell at Floyd to shut up and be quiet", "Shut up and be quiet"),
    ("Yell at Floyd to go slowly and be careful", "Go slowly and be careful"),
    ("Ask Floyd if he’s okay", "Are you okay?"),
    ("Scream at Floyd to run and hide", "Run and hide"),
    ("Whisper to Floyd that you’re sorry", "I'm sorry"),
    ("Tell Jack I hate him", "I hate you"),
    ("Push Floyd", "no"),
    ("Floyd, can you help me?", "Can you help me?"),
    ("Tell Floyd he’s amazing", "You're amazing"),
    ("Say to Floyd ‘Thanks for everything’", "Thanks for everything"),
    ("Ask Floyd to please forgive me", "Please forgive me"),
    ("Ask Floyd to wait here", "Wait here"),
    ("Tell Floyd not to touch anything", "Don't touch anything"),
    ("Whisper to Floyd that I believe in him", "I believe in you"),
    ("Say to Floyd 'You really hurt me'", "You really hurt me"),
    ("Ask Floyd to stay safe", "Stay safe"),
    ("Tell Floyd he can do it", "You can do it"),
    ("Yell at Floyd to get out now", "Get out now"),
    ("Ask Floyd if he needs help", "Do you need help?"),
    ("Tell Floyd ‘I miss you’", "I miss you"),
    ("Say to Floyd 'We're all counting on you'", "We're all counting on you"),
    ("Look at Floyd", "no"),
    ("Pick up Floyd", "no"),
    ("Push the red button", "no"),
    ("Run away from Floyd", "no"),
    ("Smile at Floyd", "no"),
    ("Wave to Floyd", "no"),
    ("Think about Floyd", "no"),
    ("Feel nervous", "no"),
    ("Sit down", "no"),
    ("Walk toward Floyd", "no"),
    ("Hug Floyd tightly", "no"),
    ("Cry", "no"),
    ("Imagine a world without Floyd", "no")
]

# Normalize by stripping extra quotes and whitespace
def normalize(text):
    return text.strip().strip('"').strip("'")

def run_test(prompt, expected):
    try:
        thread = openai.beta.threads.create()
        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )
        # Poll until run is complete
        while True:
            run = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status in ["completed", "failed"]:
                break

        if run.status != "completed":
            print(f"❌ Test failed: '{prompt}' (Run error: {run.status})")
            return

        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        output = messages.data[0].content[0].text.value.strip()

        # Normalize
        def normalize(text):
            return text.strip().strip('"').strip("'").lower()

        expected_norm = normalize(expected)
        output_norm = normalize(output)

        result = "✅" if output_norm == expected_norm else "❌"
        print(f"{result} Prompt: '{prompt}' → Got: '{output}' | Expected: '{expected}'")

    except Exception as e:
        print(f"❌ Exception for prompt '{prompt}': {e}")

if __name__ == "__main__":
    for prompt, expected in TEST_CASES:
        run_test(prompt, expected)