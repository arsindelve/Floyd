"""
Simple test script to verify metadata extraction works correctly.
Tests the ParameterExtractor without requiring OpenAI API calls.
"""
import json
from main import ParameterExtractor, AssistantResponse


def test_parameter_extractor():
    """Test parameter extraction for GoSomewhere and PickUp."""
    print("Testing ParameterExtractor...")

    # Test GoSomewhere
    print("\n1. Testing GoSomewhere:")
    gosomewhere_responses = [
        "Floyd heads north towards the castle.",
        "Moving south to the dungeon!",
        "Going east into the forest.",
        "Floyd walks forward carefully.",
    ]
    for response in gosomewhere_responses:
        params = ParameterExtractor.extract('GoSomewhere', response)
        print(f"  Content: '{response}'")
        print(f"  Extracted: {params}")

    # Test PickUp
    print("\n2. Testing PickUp:")
    pickup_responses = [
        "Floyd picks up the sword.",
        "You grab the key from the table.",
        "Taking the coin from the ground.",
        "Floyd gets the torch.",
    ]
    for response in pickup_responses:
        params = ParameterExtractor.extract('PickUp', response)
        print(f"  Content: '{response}'")
        print(f"  Extracted: {params}")

    # Test non-extractable assistant
    print("\n3. Testing non-extractable assistant:")
    params = ParameterExtractor.extract('basic_response', "Floyd says hello!")
    print(f"  Extracted: {params}")


def test_assistant_response():
    """Test AssistantResponse with and without metadata."""
    print("\n\nTesting AssistantResponse...")

    # Test without metadata (backward compatible)
    print("\n1. Response without metadata:")
    response1 = AssistantResponse(content="Floyd says hello!")
    lambda_response1 = response1.to_lambda_response()
    print(json.dumps(lambda_response1, indent=2))

    # Test with metadata
    print("\n2. Response with GoSomewhere metadata:")
    response2 = AssistantResponse(
        content="Floyd heads north towards the castle.",
        metadata={
            'assistant_type': 'GoSomewhere',
            'parameters': {'direction': 'north'}
        }
    )
    lambda_response2 = response2.to_lambda_response()
    print(json.dumps(lambda_response2, indent=2))

    # Test with PickUp metadata
    print("\n3. Response with PickUp metadata:")
    response3 = AssistantResponse(
        content="Floyd picks up the sword.",
        metadata={
            'assistant_type': 'PickUp',
            'parameters': {'object': 'sword'}
        }
    )
    lambda_response3 = response3.to_lambda_response()
    print(json.dumps(lambda_response3, indent=2))


if __name__ == '__main__':
    test_parameter_extractor()
    test_assistant_response()
    print("\n✅ All tests completed!")
