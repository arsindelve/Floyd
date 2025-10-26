"""
Manual test for GoSomewhere assistant with JSON response parsing.
"""
import json
import os
from main import lambda_handler


def test_gosomewhere():
    """Test GoSomewhere with various prompts."""

    test_prompts = [
        "Floyd, go north",
        "Go to the engine room",
        "Head south down the corridor",
        "Can you go east?",
        "Floyd, follow me west"
    ]

    print("=" * 70)
    print("TESTING GOSOMEWHERE ASSISTANT WITH JSON RESPONSES")
    print("=" * 70)

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n\nTEST {i}: {prompt}")
        print("-" * 70)

        event = {
            "assistant": "floyd",
            "prompt": prompt
        }

        try:
            response = lambda_handler(event, None)

            print(f"\nStatus Code: {response['statusCode']}")

            body = json.loads(response['body'])
            results = body.get('results', {})

            print(f"\nMessage: {results.get('single_message')}")

            if 'metadata' in results:
                metadata = results['metadata']
                print(f"\nMetadata:")
                print(f"  Assistant Type: {metadata.get('assistant_type')}")
                if 'parameters' in metadata:
                    print(f"  Parameters: {json.dumps(metadata['parameters'], indent=4)}")
            else:
                print("\n(No metadata - plain text response)")

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()


def test_non_gosomewhere():
    """Test with a non-GoSomewhere assistant to verify backward compatibility."""
    print("\n\n" + "=" * 70)
    print("TESTING BACKWARD COMPATIBILITY (non-GoSomewhere)")
    print("=" * 70)

    test_cases = [
        {
            "assistant": "blather",
            "prompt": "The ship is about to explode!",
            "description": "Blather assistant (plain text)"
        }
    ]

    for test in test_cases:
        print(f"\n\nTEST: {test['description']}")
        print("-" * 70)
        print(f"Prompt: {test['prompt']}")

        try:
            response = lambda_handler(test, None)

            print(f"\nStatus Code: {response['statusCode']}")

            body = json.loads(response['body'])
            results = body.get('results', {})

            print(f"\nMessage: {results.get('single_message')}")

            if 'metadata' in results:
                print(f"\nMetadata: {results['metadata']}")
            else:
                print("\n(No metadata - as expected)")

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    # Check for required environment variables
    required_vars = [
        'OPENAI_API_KEY',
        'OPENAI_ROUTER_ASSISTANT_ID',
        'OPENAI_GOSOMEWHERE_ASSISTANT_ID'
    ]

    missing = [var for var in required_vars if not os.environ.get(var)]

    if missing:
        print("ERROR: Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease set these variables before running the test.")
        exit(1)

    test_gosomewhere()
    test_non_gosomewhere()

    print("\n\n" + "=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)
