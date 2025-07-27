import os
from floyd import Floyd
from router import Router
import json

# Map assistant types to their OpenAI assistant IDs
ASSISTANT_MAP = {
    "basic_response": os.environ.get("OPENAI_FLOYD_BASIC_RESPONSE_ASSISTANT_ID"),
    "router": os.environ.get("OPENAI_ROUTER_ASSISTANT_ID"),
    "DoSomething": os.environ.get("OPENAI_DOSOMETHING_ASSISTANT_ID"),
    "PickUp": os.environ.get("OPENAI_PICKUP_ASSISTANT_ID"),
    "GoSomewhere": os.environ.get("OPENAI_GOSOMEWHERE_ASSISTANT_ID"),
    "AskQuestion": os.environ.get("OPENAI_ASKQUESTION_ASSISTANT_ID"),
    "GiveInstruction": os.environ.get("OPENAI_GIVEINSTRUCTION_ASSISTANT_ID"),
    "SocialEmotional": os.environ.get("OPENAI_SOCIALEMOTIONAL_ASSISTANT_ID"),
    "MetaCommand": os.environ.get("OPENAI_METACOMMAND_ASSISTANT_ID"),
    "Nonsense": os.environ.get("OPENAI_NONSENSE_ASSISTANT_ID"),
    "RewriteSecondPerson": os.environ.get("OPENAI_REWRITESECONDPERSON_ASSISTANT_ID"),
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

        assistant_id = ASSISTANT_MAP.get(assistant_type)
        if not assistant_id:
            print(f"Unknown assistant type: {assistant_type}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unknown assistant type'})
            }

        if assistant_type == 'router':
            print("Processing router assistant type")
            router = Router(assistant_id)
            print(f"Routing with assistant id: {assistant_id}")
            route = router.route(prompt)
            print("Router selected route:", route)
            assistant_id = ASSISTANT_MAP.get(route)
            if not assistant_id:
                print(f"Unknown route returned: {route}")
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Unknown route'})
                }

        floyd = Floyd(assistant_id)
        print(f"Chatting with assistant id: {assistant_id}")
        response = floyd.chat(prompt)
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
