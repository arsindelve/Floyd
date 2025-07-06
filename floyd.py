from typing import Optional, Dict, Any
import time

from openai import OpenAI


class Floyd:
    def __init__(self, assistant_id: str, api_key: Optional[str] = None):
        """
        Initialize Floyd with an existing OpenAI assistant ID.

        Args:
            assistant_id: The ID of the existing OpenAI assistant to use
            api_key: Optional OpenAI API key. If not provided, will use environment variable
        """
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id

    def create_thread(self) -> str:
        """Create a new conversation thread."""
        thread = self.client.beta.threads.create()
        return thread.id

    def add_message(self, thread_id: str, content: str) -> None:
        """
        Add a message to an existing thread.

        Args:
            thread_id: The ID of the thread to add the message to
            content: The message content
        """
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=content
        )

    def run_assistant(self, thread_id: str, instructions: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the assistant on the current thread and wait for completion.

        Args:
            thread_id: The ID of the thread to run the assistant on
            instructions: Optional override instructions for this run

        Returns:
            Dict containing the assistant's response
        """
        # Create and start the run
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant_id,
            instructions=instructions
        )

        # Wait for run to complete
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run.status in {
                "completed",
                "failed",
                "cancelled",
                "expired",
                "requires_action",
            }:
                break
            # Avoid hammering the API in a tight loop
            time.sleep(1)

        # Get messages
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)

        # Return the latest assistant message
        for msg in messages.data:
            if msg.role == "assistant":
                return {
                    "role": msg.role,
                    "content": msg.content[0].text.value
                }

        return {"role": "assistant", "content": "No response generated"}

    def chat(self, message: str, thread_id: Optional[str] = None,
             instructions: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message and get a response in a single call.
        Creates a new thread if thread_id is not provided.

        Args:
            message: The message to send
            thread_id: Optional thread ID to continue an existing conversation
            instructions: Optional override instructions for this run

        Returns:
            Dict containing the assistant's response
        """
        if thread_id is None:
            thread_id = self.create_thread()

        self.add_message(thread_id, message)
        return self.run_assistant(thread_id, instructions)
