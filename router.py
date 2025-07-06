from typing import Optional

from floyd import Floyd

class Router(Floyd):
    """Router class that determines which assistant to use based on a prompt."""

    def __init__(self, assistant_id: str, api_key: Optional[str] = None):
        super().__init__(assistant_id, api_key)

    def route(self, prompt: str) -> str:
        """Return the routing classification for the given prompt."""
        response = self.chat(prompt)
        return response.get('content')
