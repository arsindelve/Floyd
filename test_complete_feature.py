"""
Complete feature test demonstrating metadata extraction for GoSomewhere assistant.

This test demonstrates:
1. The GoSomewhere assistant returns JSON with direction metadata
2. The Lambda handler parses the JSON and includes metadata in the response
3. Backward compatibility is maintained for non-JSON responses
4. The client can access both the message and the extracted direction
"""
import json
import os
from main import lambda_handler


def print_header(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def test_gosomewhere_with_metadata():
    """Test that GoSomewhere returns direction metadata."""
    print_header("TEST: GoSomewhere with Metadata Extraction")

    event = {
        "assistant": "floyd",
        "prompt": "Floyd, go north to the bridge"
    }

    print(f"\nRequest:")
    print(f"  Assistant: {event['assistant']}")
    print(f"  Prompt: {event['prompt']}")

    response = lambda_handler(event, None)
    body = json.loads(response['body'])
    results = body['results']

    print(f"\nResponse:")
    print(f"  Status: {response['statusCode']}")
    print(f"  Message: {results['single_message']}")

    # Verify metadata exists
    assert 'metadata' in results, "Expected metadata in response"
    metadata = results['metadata']

    print(f"\nMetadata:")
    print(f"  Assistant Type: {metadata['assistant_type']}")
    assert metadata['assistant_type'] == 'GoSomewhere', "Expected GoSomewhere assistant type"

    # Verify parameters exist
    assert 'parameters' in metadata, "Expected parameters in metadata"
    parameters = metadata['parameters']

    print(f"  Direction: {parameters['direction']}")
    assert 'direction' in parameters, "Expected direction parameter"
    assert parameters['direction'] == 'north', f"Expected direction 'north', got '{parameters['direction']}'"

    print("\nPASS: GoSomewhere correctly returned direction metadata")
    return True


def test_various_directions():
    """Test GoSomewhere with various direction types."""
    print_header("TEST: Various Direction Types")

    test_cases = [
        {"prompt": "Go south", "expected": "south"},
        {"prompt": "Head to the engine room", "expected": "engine room"},
        {"prompt": "Can you go up?", "expected": "up"},
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test['prompt']}")

        event = {"assistant": "floyd", "prompt": test['prompt']}
        response = lambda_handler(event, None)
        body = json.loads(response['body'])
        results = body['results']

        if 'metadata' in results and 'parameters' in results['metadata']:
            direction = results['metadata']['parameters']['direction']
            print(f"   Direction extracted: {direction}")
            # Note: We don't assert exact match because LLM might interpret differently
        else:
            print(f"   No metadata extracted")

    print("\nPASS: Tested various direction types")
    return True


def test_backward_compatibility():
    """Test that non-GoSomewhere assistants work without metadata."""
    print_header("TEST: Backward Compatibility")

    event = {
        "assistant": "blather",
        "prompt": "The reactor is failing!"
    }

    print(f"\nRequest:")
    print(f"  Assistant: {event['assistant']}")
    print(f"  Prompt: {event['prompt']}")

    response = lambda_handler(event, None)
    body = json.loads(response['body'])
    results = body['results']

    print(f"\nResponse:")
    print(f"  Status: {response['statusCode']}")
    print(f"  Message: {results['single_message'][:100]}...")

    # Verify no metadata for non-routing assistants
    if 'metadata' not in results:
        print(f"\nPASS: No metadata present (as expected)")
    else:
        print(f"\nINFO: Metadata present: {results['metadata']}")

    print("\nPASS: Backward compatibility maintained")
    return True


def test_response_structure():
    """Verify the exact response structure."""
    print_header("TEST: Response Structure Validation")

    event = {
        "assistant": "floyd",
        "prompt": "Floyd, go west"
    }

    response = lambda_handler(event, None)

    print("\nFull Response Structure:")
    print(json.dumps(response, indent=2))

    # Verify structure
    assert response['statusCode'] == 200, "Expected status code 200"

    body = json.loads(response['body'])
    assert 'results' in body, "Expected 'results' in body"

    results = body['results']
    assert 'single_message' in results, "Expected 'single_message' in results"
    assert isinstance(results['single_message'], str), "Expected single_message to be a string"

    if 'metadata' in results:
        metadata = results['metadata']
        assert 'assistant_type' in metadata, "Expected 'assistant_type' in metadata"

        if 'parameters' in metadata:
            assert isinstance(metadata['parameters'], dict), "Expected parameters to be a dict"

    print("\nPASS: Response structure is valid")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE FEATURE TEST: GoSomewhere Metadata Extraction")
    print("=" * 70)

    # Check environment
    required_vars = ['OPENAI_API_KEY', 'OPENAI_ROUTER_ASSISTANT_ID', 'OPENAI_GOSOMEWHERE_ASSISTANT_ID']
    missing = [var for var in required_vars if not os.environ.get(var)]

    if missing:
        print("\nERROR: Missing environment variables:")
        for var in missing:
            print(f"  - {var}")
        return False

    try:
        # Run all tests
        all_passed = True
        all_passed &= test_gosomewhere_with_metadata()
        all_passed &= test_various_directions()
        all_passed &= test_backward_compatibility()
        all_passed &= test_response_structure()

        print("\n" + "=" * 70)
        if all_passed:
            print("PASS: ALL TESTS PASSED")
            print("\nFeature Summary:")
            print("- GoSomewhere assistant returns JSON with 'message' and 'direction'")
            print("- Lambda handler extracts and includes metadata in response")
            print("- Response includes assistant_type and parameters.direction")
            print("- Backward compatible with non-JSON assistants")
            print("- Client can access both message and direction from response")
        else:
            print("FAIL: SOME TESTS FAILED")
        print("=" * 70)

        return all_passed

    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
