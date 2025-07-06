import os
from floyd import Floyd
from router import Router
from rewrite_second_person import RewriteSecondPerson
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

        if assistant_type == 'router':
            rewrite_id = ASSISTANT_MAP.get('RewriteSecondPerson')
            rewriter = RewriteSecondPerson(rewrite_id)
            new_prompt = rewriter.rewrite(prompt)
            if new_prompt.strip().lower() == 'no':
                return {
                    'statusCode': 200,
                    'body': json.dumps({'results': {'single_message': 'no'}})
                }
            prompt = new_prompt
            router = Router(assistant_id)
            route = router.route(prompt)
            assistant_id = ASSISTANT_MAP.get(route)
            if not assistant_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Unknown route'})
                }

        floyd = Floyd(assistant_id)
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
