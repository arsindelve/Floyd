import os
from floyd import Floyd
import json


def lambda_handler(event, context):
    try:
        # Initialize Floyd
        assistant_id = os.environ['OPENAI_ASSISTANT_ID']
        floyd = Floyd(assistant_id)

        # Test a single message
        response = floyd.chat("Write a haiku about programming")
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