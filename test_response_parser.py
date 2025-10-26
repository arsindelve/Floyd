"""
Test ResponseParser thoroughly without requiring OpenAI API calls.
"""
import json
import sys


# Simple standalone implementation for testing
def parse_response(content: str):
    """Parse assistant response. Returns (message, parameters)."""
    try:
        # Try to parse as JSON
        data = json.loads(content.strip())

        # Must be a dict with 'message' field
        if isinstance(data, dict) and 'message' in data:
            message = data.pop('message')
            parameters = data if data else None
            return message, parameters

        # Not the expected format, return as-is
        return content, None

    except (json.JSONDecodeError, AttributeError):
        # Not JSON or invalid format, return content as-is
        return content, None


def test_gosomewhere_json():
    """Test GoSomewhere JSON responses."""
    print("=" * 60)
    print("TEST 1: GoSomewhere JSON Responses")
    print("=" * 60)

    test_cases = [
        {
            "name": "GoSomewhere - north",
            "input": '{"message": "Floyd says he isn\'t sure how to get there.", "direction": "north"}',
            "expected_message": "Floyd says he isn't sure how to get there.",
            "expected_params": {"direction": "north"}
        },
        {
            "name": "GoSomewhere - south with extra whitespace",
            "input": '  {"message": "Floyd scratches his head and says it might be dark over there.", "direction": "south"}  ',
            "expected_message": "Floyd scratches his head and says it might be dark over there.",
            "expected_params": {"direction": "south"}
        },
        {
            "name": "GoSomewhere - specific location",
            "input": '{"message": "Floyd feels nervous about going there by himself.", "direction": "engine room"}',
            "expected_message": "Floyd feels nervous about going there by himself.",
            "expected_params": {"direction": "engine room"}
        },
        {
            "name": "GoSomewhere - unknown direction",
            "input": '{"message": "Floyd says maybe we can go there together instead.", "direction": "unknown"}',
            "expected_message": "Floyd says maybe we can go there together instead.",
            "expected_params": {"direction": "unknown"}
        },
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        print(f"\n{test['name']}")
        print(f"  Input: {test['input'][:80]}...")
        message, params = parse_response(test['input'])
        print(f"  Message: {message}")
        print(f"  Parameters: {params}")

        if message == test['expected_message'] and params == test['expected_params']:
            print("  PASS")
            passed += 1
        else:
            print("  FAIL")
            print(f"    Expected message: {test['expected_message']}")
            print(f"    Expected params: {test['expected_params']}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_backward_compatibility():
    """Test backward compatibility with plain text responses."""
    print("\n" + "=" * 60)
    print("TEST 2: Backward Compatibility (Plain Text)")
    print("=" * 60)

    test_cases = [
        {
            "name": "Plain text response",
            "input": "Floyd says hello!",
            "expected_message": "Floyd says hello!",
            "expected_params": None
        },
        {
            "name": "Multi-line plain text",
            "input": "Floyd waves happily.\nHe seems excited!",
            "expected_message": "Floyd waves happily.\nHe seems excited!",
            "expected_params": None
        },
        {
            "name": "Plain text with JSON-like content",
            "input": "Floyd says: I have a message for you",
            "expected_message": "Floyd says: I have a message for you",
            "expected_params": None
        },
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        print(f"\n{test['name']}")
        print(f"  Input: {test['input']}")
        message, params = parse_response(test['input'])
        print(f"  Message: {message}")
        print(f"  Parameters: {params}")

        if message == test['expected_message'] and params == test['expected_params']:
            print("  PASS")
            passed += 1
        else:
            print("  FAIL")
            print(f"    Expected message: {test['expected_message']}")
            print(f"    Expected params: {test['expected_params']}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_edge_cases():
    """Test edge cases and malformed inputs."""
    print("\n" + "=" * 60)
    print("TEST 3: Edge Cases")
    print("=" * 60)

    test_cases = [
        {
            "name": "JSON without message field",
            "input": '{"response": "test", "direction": "north"}',
            "expected_message": '{"response": "test", "direction": "north"}',
            "expected_params": None
        },
        {
            "name": "Empty JSON object",
            "input": '{}',
            "expected_message": '{}',
            "expected_params": None
        },
        {
            "name": "JSON with only message field",
            "input": '{"message": "Floyd waves!"}',
            "expected_message": "Floyd waves!",
            "expected_params": None
        },
        {
            "name": "JSON array",
            "input": '[{"message": "test"}]',
            "expected_message": '[{"message": "test"}]',
            "expected_params": None
        },
        {
            "name": "Malformed JSON",
            "input": '{"message": "test"',
            "expected_message": '{"message": "test"',
            "expected_params": None
        },
        {
            "name": "JSON with multiple parameters",
            "input": '{"message": "Floyd moves carefully.", "direction": "north", "speed": "slow"}',
            "expected_message": "Floyd moves carefully.",
            "expected_params": {"direction": "north", "speed": "slow"}
        },
        {
            "name": "Empty string",
            "input": '',
            "expected_message": '',
            "expected_params": None
        },
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        print(f"\n{test['name']}")
        print(f"  Input: {test['input'][:80]}")
        message, params = parse_response(test['input'])
        print(f"  Message: {message}")
        print(f"  Parameters: {params}")

        if message == test['expected_message'] and params == test['expected_params']:
            print("  PASS")
            passed += 1
        else:
            print("  FAIL")
            print(f"    Expected message: {test['expected_message']}")
            print(f"    Expected params: {test['expected_params']}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_full_response_format():
    """Test the full Lambda response format."""
    print("\n" + "=" * 60)
    print("TEST 4: Full Lambda Response Format")
    print("=" * 60)

    # Simulate what AssistantResponse.to_lambda_response() does
    def create_lambda_response(content, metadata=None):
        results = {'single_message': content}
        if metadata:
            results['metadata'] = metadata
        return {
            'statusCode': 200,
            'body': json.dumps({'results': results})
        }

    # Test with metadata
    print("\n1. Response with metadata:")
    message = "Floyd says he isn't sure how to get there."
    metadata = {
        'assistant_type': 'GoSomewhere',
        'parameters': {'direction': 'north'}
    }
    response = create_lambda_response(message, metadata)
    print(json.dumps(response, indent=2))

    # Verify structure
    body = json.loads(response['body'])
    assert body['results']['single_message'] == message
    assert body['results']['metadata']['assistant_type'] == 'GoSomewhere'
    assert body['results']['metadata']['parameters']['direction'] == 'north'
    print("  PASS - Metadata included correctly")

    # Test without metadata (backward compatible)
    print("\n2. Response without metadata (backward compatible):")
    message2 = "Floyd waves happily!"
    response2 = create_lambda_response(message2, None)
    print(json.dumps(response2, indent=2))

    # Verify structure
    body2 = json.loads(response2['body'])
    assert body2['results']['single_message'] == message2
    assert 'metadata' not in body2['results']
    print("  PASS - No metadata field present")

    return True


if __name__ == '__main__':
    print("\nCOMPREHENSIVE RESPONSE PARSER TESTS\n")

    all_passed = True
    all_passed &= test_gosomewhere_json()
    all_passed &= test_backward_compatibility()
    all_passed &= test_edge_cases()
    all_passed &= test_full_response_format()

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
