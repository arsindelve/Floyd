from pydantic import BaseModel
from typing import Optional

class GraphState(BaseModel):
    input: str
    message: Optional[str] = None  # Now optional