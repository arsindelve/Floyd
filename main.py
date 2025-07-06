import os
from floyd import Floyd
import json

def lambda_handler(event, context):
    try:
        # Parse the incoming request body for the question
        body = event.get('body')
        if body:
            data = json.loads(body)
        else:
            data = event

        question = data.get('question', 'What is your question?')

        # Initialize Floyd
        assistant_id = os.environ['OPENAI_ASSISTANT_ID']
        floyd = Floyd(assistant_id)

        # Use the question from the request
        response = floyd.chat(question)
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