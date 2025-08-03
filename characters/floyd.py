import os
from typing import Optional, Dict, Tuple

from openAIAssistantClient import OpenAIAssistantClient

class Floyd(OpenAIAssistantClient):
    """Floyd class that determines which assistant to use based on a prompt."""

    def __init__(self, assistant_id: str, api_key: Optional[str] = None):
        super().__init__(assistant_id, api_key)
        self.assistant_map = {
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

    def route(self, prompt: str) -> str:
        """Return the routing classification for the given prompt."""
        response = self.chat(prompt)
        return response.get('content')

    def route_and_get_assistant_id(self, prompt: str) -> Tuple[str, str]:
        """Route the prompt and return the route and corresponding assistant ID."""
        print("Processing router assistant type")
        print(f"Routing with assistant id: {self.assistant_id}")
        route = self.route(prompt)
        print("Router selected route:", route)
        assistant_id = self.assistant_map.get(route)
        if not assistant_id:
            print(f"Unknown route returned: {route}")
            raise ValueError(f"Unknown route: {route}")
        return route, assistant_id
