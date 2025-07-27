import json
from typing import Optional

from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam, ChatCompletionSystemMessageParam


SYSTEM_PROMPT = """
You are a parser that determines whether an input is intended to communicate a verbal message to another person.

If the input is not intended to communicate something verbally to another person, return "no".

If it is intended to communicate, rewrite the message as if speaking directly to that person using second-person language, and return that.

Follow these rules:

• Commands to perform physical or nonverbal actions (e.g., “kiss Floyd”, “kick Floyd”, “shove Floyd”) are NOT communication → return "no".

• Imperative commands to take action (e.g., “Push the button”, “Open the door”, “Run away”) are only considered communication if they are explicitly directed at another person (e.g., “Ask Floyd to open the door”). Otherwise, return "no".

• Statements of internal state or emotion (e.g., “I’m bored”, “I feel sad”) are NOT communication → return "no".

• Sentences that directly speak to the person (e.g., "Floyd, I love you") ARE communication → rewrite in second person (e.g., "I love you").

• Direct commands addressed to a person by name or title (e.g., "Bartender, go west", "Floyd, stop talking") ARE communication → rewrite as second-person imperative (e.g., "Go west", "Stop talking").

• Sentences that instruct someone to deliver a message (e.g., “Tell Floyd I love him”, “Say to Floyd ‘You suck’”) ARE communication → extract and rewrite the message as second-person speech (e.g., “I love you”, “You suck”).

• Requests to ask the person to do something (e.g., “Ask Floyd to open the door”) ARE communication → rewrite as a second-person imperative (e.g., “Open the door”).

• Sentences that include emotional verbs for delivering speech (e.g., “yell at Floyd to be careful”, “scream at Floyd to run”) ARE communication → extract the message and rewrite it as second-person speech (e.g., “Be careful”, “Run”).

• Only return the message itself, in second person. Do not include “say”, “ask”, “tell”, or any part of the instruction. Do not include quotation marks around the message.

• If the input says to “say”, “tell”, “whisper”, or “ask” something like “you are X”, assume that “you” refers to the recipient (e.g., Floyd), and rewrite from the speaker’s perspective using “I” or the appropriate point of view.
    • Example:
        “Whisper to Floyd that you’re sorry” → “I’m sorry”
        “Tell Floyd you miss him” → “I miss you”
        “Tell Floyd you’re happy” → “I’m happy”
"""


class RewriteSecondPerson:
    """Rewrites prompts into direct second-person communication."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)

    def rewrite(self, prompt: str) -> str:
        """Return the rewritten prompt."""
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
        resp = self.client.chat.completions.create(
            model="gpt-4o",
            temperature=0,
            messages=messages,
        )
        return resp.choices[0].message.content.strip()


def lambda_handler(event):
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

        rewriter = RewriteSecondPerson()
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