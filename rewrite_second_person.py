from typing import Optional

from floyd import Floyd


class RewriteSecondPerson(Floyd):
    """Assistant wrapper that rewrites prompts into second person."""

    def __init__(self, assistant_id: str, api_key: Optional[str] = None):
        super().__init__(assistant_id, api_key)

    def rewrite(self, prompt: str) -> str:
        """Return the rewritten prompt."""
        response = self.chat(prompt)
        return response.get('content')
