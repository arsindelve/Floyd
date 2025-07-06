import os
from floyd import Floyd
import sys
from dotenv import load_dotenv

load_dotenv()

FloydBasicResponseAssistantId = os.getenv('OPENAI_FLOYD_BASIC_RESPONSE_ASSISTANT_ID')
if not FloydBasicResponseAssistantId:
    raise ValueError("OPENAI_FLOYD_BASIC_RESPONSE_ASSISTANT_ID environment variable is not set")

def test_floyd():
    # Initialize Floyd
    floyd = Floyd(FloydBasicResponseAssistantId)
    
    # Test a single message
    print("\nTesting single message:")
    response = floyd.chat("Write a haiku about programming")
    print(f"Assistant: {response['content']}")
    
    # Test conversation thread
    print("\nTesting conversation thread:")
    thread_id = floyd.create_thread()
    
    # First message
    floyd.add_message(thread_id, "What are the three laws of robotics?")
    response = floyd.run_assistant(thread_id)
    print(f"Question 1 - Assistant: {response['content']}")
    
    # Follow-up question in the same thread
    floyd.add_message(thread_id, "Who created these laws?")
    response = floyd.run_assistant(thread_id)
    print(f"Question 2 - Assistant: {response['content']}")
    
    return True

if __name__ == "__main__":
    try:
        success = test_floyd()
        print("\nTest completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        sys.exit(1)