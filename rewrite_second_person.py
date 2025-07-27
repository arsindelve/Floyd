from typing import Optional
import os
import json

from floyd import Floyd


class RewriteSecondPerson(Floyd):
    """Assistant wrapper that rewrites prompts into second person."""

    def __init__(self, assistant_id: str, api_key: Optional[str] = None):
        super().__init__(assistant_id, api_key)

    def rewrite(self, prompt: str) -> str:
        """Return the rewritten prompt."""
        response = self.chat(prompt)
        return response.get('content')


def lambda_handler(event, context):
    """AWS Lambda entrypoint for the rewrite API."""
    try:
        body = event.get('body')
        if body:
            data = json.loads(body)
        else:
            data = event

        prompt = data.get('prompt')
        if not prompt:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Prompt is required'})
            }

        assistant_id = os.environ.get('OPENAI_REWRITESECONDPERSON_ASSISTANT_ID')
        rewriter = RewriteSecondPerson(assistant_id)
        rewritten = rewriter.rewrite(prompt)
        return {
            'statusCode': 200,
            'body': json.dumps({'results': {'single_message': rewritten}})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

