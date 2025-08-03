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
        elif assistant_type == 'floyd':
            floyd_assistant_id = os.environ.get("OPENAI_ROUTER_ASSISTANT_ID")
            if not floyd_assistant_id:
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': 'Floyd assistant ID not configured'})
                }
            try:
                router = Floyd(floyd_assistant_id)
                route, assistant_id = router.route_and_get_assistant_id(prompt)
                client = OpenAIAssistantClient(assistant_id)
                print(f"Chatting with assistant id: {assistant_id}")
                response = client.chat(prompt)
                result1 = {"single_message": response['content']}
            except ValueError as e:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': str(e)})
                }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unknown assistant type. Use "floyd" or "RewriteSecondPerson"'})
            }

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
