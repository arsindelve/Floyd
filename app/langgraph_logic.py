from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
import openai
import os
import json
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("langgraph_logic")


class GraphState(TypedDict):
    input: str
    messages: List
    output: Optional[str]
    assistant_type: Optional[str]
    routing_thoughts: Optional[str]


def route_with_llm(state: GraphState) -> GraphState:
    """
    Use LLM to route the input to the appropriate assistant.
    """
    logger.info(f"🔀 ROUTER: Starting routing for input: '{state.get('input', '')[:50]}...'")

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    system_message = """You are an intelligent router that determines which assistant type should handle a user query. 
    You have the following assistants at your disposal:
    
    1. Coding Assistant: For programming-related queries including coding problems, debugging, and software development questions.
    2. Writing Assistant: For writing tasks, language assistance, creative writing, and text composition.
    3. Math Assistant: For mathematical problems, calculations, and numerical reasoning.
    
    Analyze the user query carefully and determine which assistant would be most appropriate.
    Respond with ONLY ONE of the following assistant types:
    - coding
    - writing
    - math
    
    Start your response with "I think this query should be routed to the" and then include your reasoning.
    """

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": state["input"]}
    ]

    logger.info("🔀 ROUTER: Calling OpenAI API for routing decision...")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0,
        max_tokens=300
    )

    response_content = response.choices[0].message.content.strip()
    logger.info(f"🔀 ROUTER: Received routing thoughts: '{response_content[:100]}...'")

    # Extract just the assistant type
    assistant_type = None
    if "coding" in response_content.lower():
        assistant_type = "coding"
    elif "writing" in response_content.lower():
        assistant_type = "writing"
    elif "math" in response_content.lower():
        assistant_type = "math"
    else:
        # Default to writing if no clear match
        assistant_type = "writing"

    logger.info(f"🔀 ROUTER: Selected assistant type: {assistant_type}")

    # Return updated state
    updated_state = {
        "assistant_type": assistant_type,
        "routing_thoughts": response_content
    }

    # Maintain the input from the original state
    if "input" in state:
        updated_state["input"] = state["input"]

    logger.info(f"🔀 ROUTER: Returning updated state: {updated_state}")
    return updated_state


def format_messages(state: GraphState) -> GraphState:
    """
    Format the messages for the appropriate assistant.
    """
    logger.info(f"📝 FORMAT: Formatting messages for assistant type: {state.get('assistant_type')}")

    user_input = state.get("input", "")
    assistant_type = state.get("assistant_type", "writing")

    system_messages = {
        "coding": "You are an expert programming assistant. Help users with code, debugging, and software development questions.",
        "writing": "You are an expert writing assistant. Help users with writing tasks, language, and composition.",
        "math": "You are an expert math assistant. Help users solve mathematical problems with clear step-by-step solutions."
    }

    # Use the appropriate system message based on assistant type
    system_message = system_messages.get(assistant_type, system_messages["writing"])

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_input}
    ]

    logger.info(f"📝 FORMAT: Created {len(messages)} messages with system prompt for {assistant_type}")

    # Create a new state dict to avoid modifying the original
    updated_state = dict(state)
    updated_state["messages"] = messages

    logger.info(f"📝 FORMAT: Returning state with keys: {list(updated_state.keys())}")
    return updated_state


def call_coding_assistant(state: GraphState) -> GraphState:
    """
    Call the specialized coding assistant.
    """
    logger.info("💻 CODING: Calling coding assistant")
    logger.info(f"💻 CODING: Input message: '{state.get('messages', [{}])[-1].get('content', '')[:50]}...'")

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    messages = state.get("messages", [])
    logger.info(f"💻 CODING: Sending {len(messages)} messages to OpenAI")

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.2,
        max_tokens=1000
    )

    output = response.choices[0].message.content
    logger.info(f"💻 CODING: Received response of length {len(output)}: '{output[:100]}...'")

    # Create a new state dict to avoid modifying the original
    updated_state = dict(state)
    updated_state["output"] = output

    logger.info(f"💻 CODING: Returning state with keys: {list(updated_state.keys())}")
    return updated_state


def call_writing_assistant(state: GraphState) -> GraphState:
    """
    Call the specialized writing assistant.
    """
    logger.info("✍️ WRITING: Calling writing assistant")
    logger.info(f"✍️ WRITING: Input message: '{state.get('messages', [{}])[-1].get('content', '')[:50]}...'")

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    messages = state.get("messages", [])
    logger.info(f"✍️ WRITING: Sending {len(messages)} messages to OpenAI")

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )

    output = response.choices[0].message.content
    logger.info(f"✍️ WRITING: Received response of length {len(output)}: '{output[:100]}...'")

    # Create a new state dict to avoid modifying the original
    updated_state = dict(state)
    updated_state["output"] = output

    logger.info(f"✍️ WRITING: Returning state with keys: {list(updated_state.keys())}")
    return updated_state


def call_math_assistant(state: GraphState) -> GraphState:
    """
    Call the specialized math assistant.
    """
    logger.info("🔢 MATH: Calling math assistant")
    logger.info(f"🔢 MATH: Input message: '{state.get('messages', [{}])[-1].get('content', '')[:50]}...'")

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    messages = state.get("messages", [])
    logger.info(f"🔢 MATH: Sending {len(messages)} messages to OpenAI")

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.1,
        max_tokens=800
    )

    output = response.choices[0].message.content
    logger.info(f"🔢 MATH: Received response of length {len(output)}: '{output[:100]}...'")

    # Create a new state dict to avoid modifying the original
    updated_state = dict(state)
    updated_state["output"] = output

    logger.info(f"🔢 MATH: Returning state with keys: {list(updated_state.keys())}")
    return updated_state


def call_openai_assistant(state: GraphState) -> GraphState:
    """
    Call an OpenAI Assistant API instead of ChatGPT API.
    This is an alternative implementation that can be used instead of the specialized assistants.
    """
    logger.info("🤖 OPENAI ASSISTANT: This function is not currently being used in the graph")
    # Implementation remains the same as before
    return {"output": "OpenAI Assistant not implemented in the current graph"}


def build_graph():
    """Build and return the LangGraph for our assistant router."""
    logger.info("🔧 BUILD: Starting to build the graph")

    builder = StateGraph(state_schema=GraphState)
    logger.info("🔧 BUILD: Created StateGraph with schema")

    # Add nodes
    builder.add_node("llm_router", route_with_llm)
    builder.add_node("format_messages", format_messages)
    builder.add_node("coding_assistant", call_coding_assistant)
    builder.add_node("writing_assistant", call_writing_assistant)
    builder.add_node("math_assistant", call_math_assistant)
    logger.info("🔧 BUILD: Added all nodes to the graph")

    # Add edge from router to format_messages
    builder.add_edge("llm_router", "format_messages")
    logger.info("🔧 BUILD: Added edge from llm_router to format_messages")

    # Define a routing function to return the next node based on assistant_type
    def router(state):
        logger.info(f"🔀 ROUTER FUNCTION: Deciding next node based on assistant_type: {state.get('assistant_type')}")
        assistant_type = state.get("assistant_type")
        next_node = None

        if assistant_type == "coding":
            next_node = "coding_assistant"
        elif assistant_type == "writing":
            next_node = "writing_assistant"
        elif assistant_type == "math":
            next_node = "math_assistant"
        else:
            # Default to writing if no valid type
            next_node = "writing_assistant"

        logger.info(f"🔀 ROUTER FUNCTION: Selected next node: {next_node}")
        return next_node

    # Add conditional edges using the router function
    builder.add_conditional_edges(
        "format_messages",
        router
    )
    logger.info("🔧 BUILD: Added conditional edges from format_messages")

    # Mark each assistant as an end node
    builder.add_edge("coding_assistant", END)
    builder.add_edge("writing_assistant", END)
    builder.add_edge("math_assistant", END)
    logger.info("🔧 BUILD: Marked all assistant nodes as END nodes")

    # Set entry point
    builder.set_entry_point("llm_router")
    logger.info("🔧 BUILD: Set llm_router as entry point")

    logger.info("🔧 BUILD: Compiling graph...")
    compiled_graph = builder.compile()
    logger.info("🔧 BUILD: Graph compiled successfully!")

    return compiled_graph