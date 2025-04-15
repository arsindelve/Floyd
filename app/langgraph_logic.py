from pydantic import BaseModel
from typing import Optional
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph

class GraphState(BaseModel):
    input: str
    message: Optional[str] = None

def my_custom_node(state: GraphState):
    print("Received state:", state)
    return {"message": f"You said: {state.input}"}

def build_graph():
    builder = StateGraph(state_schema=GraphState)
    builder.add_node("echo_node", my_custom_node)
    builder.set_entry_point("echo_node")
    return builder.compile()