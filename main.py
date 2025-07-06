import os
from floyd import Floyd
import json

# Map assistant types to their OpenAI assistant IDs
ASSISTANT_MAP = {
    "basic_response": os.environ.get("OPENAI_FLOYD_BASIC_RESPONSE_ASSISTANT_ID")
}

def lambda_handler(event, context):
    try:
        # Parse the incoming request body for the prompt and assistant type
        body = event.get('body')
        if body:
            data = json.loads(body)
        else:
            data = event

        assistant_type = data.get('assistant')
        prompt = data.get('prompt')
        if not prompt:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Prompt is required'})
            }

        assistant_id = ASSISTANT_MAP.get(assistant_type)
        if not assistant_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unknown assistant type'})
            }

        # Initialize Floyd with the matching assistant ID
        floyd = Floyd(assistant_id)

        # Use the prompt from the request
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
