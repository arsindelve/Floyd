import os
from openAIAssistantClient import OpenAIAssistantClient
from characters.floyd import Floyd
from rewrite_second_person import RewriteSecondPerson
import json

# Deployment version marker - increment this when making changes
DEPLOYMENT_VERSION = "1.0.1"
print(f"Floyd Lambda initialized - Version: {DEPLOYMENT_VERSION}")

# Deployment version marker - increment this when making changes
DEPLOYMENT_VERSION = "1.0.1"
print(f"Floyd Lambda initialized - Version: {DEPLOYMENT_VERSION}")

# Map assistant types to their OpenAI assistant IDs
ASSISTANT_MAP = {
    "basic_response": os.environ.get("OPENAI_FLOYD_BASIC_RESPONSE_ASSISTANT_ID"),
    "floyd": os.environ.get("OPENAI_ROUTER_ASSISTANT_ID"),
    "DoSomething": os.environ.get("OPENAI_DOSOMETHING_ASSISTANT_ID"),
    "PickUp": os.environ.get("OPENAI_PICKUP_ASSISTANT_ID"),
    "GoSomewhere": os.environ.get("OPENAI_GOSOMEWHERE_ASSISTANT_ID"),
    "AskQuestion": os.environ.get("OPENAI_ASKQUESTION_ASSISTANT_ID"),
    "GiveInstruction": os.environ.get("OPENAI_GIVEINSTRUCTION_ASSISTANT_ID"),
    "SocialEmotional": os.environ.get("OPENAI_SOCIALEMOTIONAL_ASSISTANT_ID"),
    "MetaCommand": os.environ.get("OPENAI_METACOMMAND_ASSISTANT_ID"),
    "Nonsense": os.environ.get("OPENAI_NONSENSE_ASSISTANT_ID")
}

def lambda_handler(event, context):
    try:
        print("lambda_handler invoked with event:", event)
        # Parse the incoming request body for the prompt and assistant type
        body = event.get('body')
        if body:
            print("Found body in event")
            data = json.loads(body)
        else:
            print("No body field in event; using event directly")
            data = event

        assistant_type = data.get('assistant')
        prompt = data.get('prompt')
        if not prompt:
            print("Prompt missing from request")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Prompt is required'})
            }

        if assistant_type == 'RewriteSecondPerson':
            print("Processing RewriteSecondPerson locally")
            rewriter = RewriteSecondPerson()
            rewritten = rewriter.rewrite(prompt)
            result1 = {"single_message": rewritten}
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'results': {
                        **result1
                    }
                })
            }

        assistant_id = ASSISTANT_MAP.get(assistant_type)
        if not assistant_id:
            print(f"Unknown assistant type: {assistant_type}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unknown assistant type'})
            }

        if assistant_type == 'floyd':
            try:
                router = Floyd(assistant_id)
                route, assistant_id = router.route_and_get_assistant_id(prompt)
            except ValueError as e:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': str(e)})
                }
        
        client = OpenAIAssistantClient(assistant_id)
        print(f"Chatting with assistant id: {assistant_id}")
        response = client.chat(prompt)
        result1 = {"single_message": response['content']}

        return {
            'statusCode': 200,
            'body': json.dumps({
                'results': {
                    **result1
                }
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
