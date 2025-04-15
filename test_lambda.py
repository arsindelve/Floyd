import os
import json
import sys
from app.langgraph_logic import build_graph
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_lambda")


def test_graph_build(test_input=None):
    """Test function to specifically diagnose the graph building issue."""
    print("\n" + "=" * 50)
    print("Testing LangGraph Build")
    print("=" * 50)

    # Default test input if none provided
    if test_input is None:
        test_input = "How do I sort a list in Python?"

    # Verify API key
    api_key = os.environ.get("OPENAI_API_KEY", "")
    print(f"API key found: {'Yes' if api_key else 'No'}")
    print(f"API key length: {len(api_key)}")

    # Try building the graph
    try:
        print("\n[1] Building graph...")
        graph = build_graph()
        print("✓ Graph built successfully")

        # Try a simple invocation
        print("\n[2] Invoking graph with test input...")
        print(f"Test input: '{test_input}'")

        result = graph.invoke({"input": test_input})
        print("✓ Graph invocation successful")

        print("\n[3] Final result:")
        print(f"Result type: {type(result)}")
        print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dictionary'}")

        if isinstance(result, dict) and "output" in result:
            print("\n[4] Output value:")
            print("-" * 40)
            print(result["output"])
            print("-" * 40)
        else:
            print("\n[4] No 'output' key found in result!")
            print("Full result:")
            print(json.dumps(result, indent=2))

        if isinstance(result, dict) and "assistant_type" in result:
            print(f"\nSelected assistant type: {result['assistant_type']}")

    except Exception as e:
        print(f"ERROR building graph: {str(e)}")
        import traceback
        traceback.print_exc()


def show_test_menu():
    """Show a menu of predefined test inputs."""
    test_cases = {
        "1": "How do I sort a list in Python?",
        "2": "Write a poem about artificial intelligence.",
        "3": "Solve the equation 3x + 5 = 14.",
        "4": "What are the best practices for writing clean code?",
        "5": "Help me summarize an academic paper.",
        "6": "Calculate the derivative of x^2 + 3x - 7.",
        "7": "Custom input (enter your own query)"
    }

    print("\n=== Test Case Menu ===")
    for key, value in test_cases.items():
        print(f"{key}: {value}")

    choice = input("\nSelect a test case (1-7): ")

    if choice == "7":
        return input("Enter your custom test input: ")
    elif choice in test_cases:
        return test_cases[choice]
    else:
        print("Invalid choice. Using default test case.")
        return test_cases["1"]


if __name__ == "__main__":
    # Check if a test input was provided as a command-line argument
    if len(sys.argv) > 1:
        # Use the command-line argument as the test input
        test_input = " ".join(sys.argv[1:])
        test_graph_build(test_input)
    else:
        # If no command-line argument, show the menu
        test_input = show_test_menu()
        test_graph_build(test_input)