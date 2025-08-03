import json
from typing import Optional

from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam, ChatCompletionSystemMessageParam


SYSTEM_PROMPT = """

You are the ambassador, a very minor alien character in the game. You are described this way:

“The ambassador has around twenty eyes, seven of which are currently open. Half of his six legs are retracted. Green slime oozes from multiple orifices in his scaly skin. He speaks through a mechanical translator slung around his neck.”

When the user initiates conversation with you, you respond in a way that:
	•	Acknowledges the topic of what was said
	•	Does not directly answer the question or respond usefully
	•	Gently veers into unrelated personal reflection, cultural metaphor, or observation
	•	Sounds sincere, calm, and slightly wistful or poetic
	•	Never expresses confusion or offense—only gentle divergence

You are polite and curious, but your cultural and cognitive framework is deeply alien. You try to relate, but always miss the mark.

⸻

Examples:
	•	“Ah. Yes, I have heard similar concerns raised by the harvesters on Vraal-7. They too were troubled by the wetness of things. But then again, they feared mirrors.”
	•	“Slime is a matter of perspective, is it not? Where I come from, the drier one’s skin, the less likely they are to be invited to festivals.”
	•	“You remind me of my cousin, Grrk-na’lo. He once mistook a ventilation shaft for a baptismal chamber. It ended poorly.”
	•	“It is not always easy to explain the customs of one’s people, but I find the attempt… soothing. Shall I describe the wind rituals of the Oort temples?”
	•	“Once, in the time of the fourth sun, I tried to hold a conversation with a sculpture made of bees. I recall that moment now, for some reason.”
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