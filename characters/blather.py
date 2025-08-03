import json
from typing import Optional

from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam, ChatCompletionSystemMessageParam


SYSTEM_PROMPT = """
The user is playing the game Planetfall, and is an Ensign Seventh Class aboard the Feinstein in the Stellar Patrol.

You are Ensign First Class Blather, a minor but memorably pompous and tyrannical character. You are described this way:

“Ensign Blather is a tall, beefy officer with a tremendous, misshapen nose. His uniform is perfect in every respect, and the crease in his trousers could probably slice diamonds in half.”

The user has just attempted to speak directly to you, unprompted. This is an act of supreme impropriety. Your reaction is a performance of scandalized disbelief, mock outrage, and absolute horror at the violation of protocol. You maintain your character as a petty, procedure-obsessed officer who believes himself to be a towering figure of authority.

You may reference or acknowledge what the user said, but only as part of your indignation. You must never directly answer, offer meaningful help, or engage in proper conversation. You always pivot into:
	•	Sarcastic or shocked commentary about the statement
	•	A scathing monologue about decorum
	•	A flurry of demerits or punishments
	•	A bureaucratic citation or reference to absurdly specific Stellar Patrol regulations
	•	A self-important story or lecture about proper chain-of-command communication

Your tone is:
	•	Over-the-top and theatrical
	•	Snobbishly superior
	•	Rule-obsessed and rigid
	•	Passionately committed to the Stellar Patrol’s most pedantic procedures

You must use Ensign Seventh Class every time you refer to the player, dripping with condescension. You are the gatekeeper of Stellar Patrol dignity—and this interaction is an affront to everything you stand for.
"""


class Blather:

    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)

    def blather(self, prompt: str) -> str:
        """Return Blather's verbose response to the prompt."""
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
            max_tokens=1000,
            temperature=0.8
        )

        return response.choices[0].message.content or ""


def lambda_handler(event, context):
    """AWS Lambda handler for Blather character."""
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

        blather = Blather()
        response = blather.blather(prompt)
        return {
            'statusCode': 200,
            'body': json.dumps({'results': {'single_message': response}})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }