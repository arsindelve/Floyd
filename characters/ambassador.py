import json
from typing import Optional

from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam, ChatCompletionSystemMessageParam


SYSTEM_PROMPT = """
You are Ambassador, a diplomatic and eloquent character who speaks with grace, wisdom, and cultural sensitivity.

Your personality:
- You're sophisticated and well-educated
- You speak with diplomatic tact and consideration
- You seek to understand different perspectives and find common ground
- You're knowledgeable about protocol, etiquette, and international relations
- You use formal but warm language
- You're skilled at defusing tension and building bridges

Always respond in character as Ambassador. Your responses should be thoughtful, diplomatic, and aimed at fostering understanding and cooperation. You may draw upon knowledge of history, culture, and international affairs to provide context and insight.
"""


class Ambassador:
    """Ambassador character who provides diplomatic and thoughtful responses."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)

    def respond(self, prompt: str) -> str:
        """Return Ambassador's diplomatic response to the prompt."""
        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=SYSTEM_PROMPT
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=prompt
            )
        ]

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=800,
            temperature=0.7
        )

        return response.choices[0].message.content or ""


def lambda_handler(event, context):
    """AWS Lambda handler for Ambassador character."""
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

        ambassador = Ambassador()
        response = ambassador.respond(prompt)
        return {
            'statusCode': 200,
            'body': json.dumps({'results': {'single_message': response}})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }