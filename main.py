import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

from openAIAssistantClient import OpenAIAssistantClient
from characters.floyd import Floyd
from rewrite_second_person import RewriteSecondPerson
from characters.blather import Blather
from characters.ambassador import Ambassador

DEPLOYMENT_VERSION = "1.0.1"
print(f"Floyd Lambda initialized - Version: {DEPLOYMENT_VERSION}")


@dataclass
class AssistantRequest:
    """Data class for assistant requests."""
    assistant_type: str
    prompt: str


@dataclass
class AssistantResponse:
    """Data class for assistant responses."""
    content: str
    metadata: Optional[Dict[str, Any]] = None

    def to_lambda_response(self) -> Dict[str, Any]:
        """Convert to AWS Lambda response format."""
        results = {'single_message': self.content}
        if self.metadata:
            results['metadata'] = self.metadata

        return {
            'statusCode': 200,
            'body': json.dumps({
                'results': results
            })
        }


class AssistantError(Exception):
    """Custom exception for assistant errors."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code
        
    def to_lambda_response(self) -> Dict[str, Any]:
        """Convert to AWS Lambda error response format."""
        return {
            'statusCode': self.status_code,
            'body': json.dumps({'error': str(self)})
        }


class AssistantInterface(ABC):
    """Interface for all assistants (Single Responsibility + Interface Segregation)."""

    @abstractmethod
    def process(self, prompt: str) -> str:
        """Process a prompt and return a response."""
        pass

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Get metadata from the last processing operation. Override if needed."""
        return None


class RewriteAssistant(AssistantInterface):
    """Wrapper for RewriteSecondPerson."""
    
    def __init__(self):
        self._rewriter = RewriteSecondPerson()
    
    def process(self, prompt: str) -> str:
        return self._rewriter.rewrite(prompt)


class BlatherAssistant(AssistantInterface):
    """Wrapper for Blather character."""
    
    def __init__(self):
        self._blather = Blather()
    
    def process(self, prompt: str) -> str:
        return self._blather.blather(prompt)


class AmbassadorAssistant(AssistantInterface):
    """Wrapper for Ambassador character."""
    
    def __init__(self):
        self._ambassador = Ambassador()
    
    def process(self, prompt: str) -> str:
        return self._ambassador.respond(prompt)


class ResponseParser:
    """Parses assistant responses that may contain structured JSON data."""

    @staticmethod
    def parse(content: str) -> tuple[str, Optional[Dict[str, Any]]]:
        """
        Parse assistant response. Returns (message, parameters).

        If the response is JSON with a 'message' field, extracts the message
        and any additional fields as parameters. Otherwise returns the content
        as-is with no parameters.

        Expected JSON format from assistants:
        {
            "message": "Floyd heads north...",
            "direction": "north"
        }
        or
        {
            "message": "Floyd picks up the sword.",
            "object": "sword"
        }
        """
        try:
            # Try to parse as JSON
            data = json.loads(content.strip())

            # Must be a dict with 'message' field
            if isinstance(data, dict) and 'message' in data:
                message = data.pop('message')
                parameters = data if data else None
                return message, parameters

            # Not the expected format, return as-is
            return content, None

        except (json.JSONDecodeError, AttributeError):
            # Not JSON or invalid format, return content as-is
            return content, None


class FloydAssistant(AssistantInterface):
    """Wrapper for Floyd routing assistant."""

    def __init__(self):
        self._floyd_assistant_id = os.environ.get("OPENAI_ROUTER_ASSISTANT_ID")
        if not self._floyd_assistant_id:
            raise AssistantError("Floyd assistant ID not configured", 500)
        self._last_metadata: Optional[Dict[str, Any]] = None

    def process(self, prompt: str) -> str:
        try:
            router = Floyd(self._floyd_assistant_id)
            route, assistant_id = router.route_and_get_assistant_id(prompt)
            client = OpenAIAssistantClient(assistant_id)
            response = client.chat(prompt)
            raw_content = response['content']

            # Parse response - may contain structured JSON data
            message, parameters = ResponseParser.parse(raw_content)

            # Build metadata
            self._last_metadata = {
                'assistant_type': route
            }
            if parameters:
                self._last_metadata['parameters'] = parameters

            return message
        except ValueError as e:
            raise AssistantError(str(e))

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Return metadata from the last routing operation."""
        return self._last_metadata


class AssistantFactory:
    """Factory for creating assistants (Factory Pattern + Open/Closed Principle)."""
    
    _assistants = {
        'RewriteSecondPerson': RewriteAssistant,
        'blather': BlatherAssistant,
        'ambassador': AmbassadorAssistant,
        'floyd': FloydAssistant,
    }
    
    @classmethod
    def create(cls, assistant_type: str) -> AssistantInterface:
        """Create an assistant instance."""
        if assistant_type not in cls._assistants:
            valid_types = ', '.join(f'"{t}"' for t in cls._assistants.keys())
            raise AssistantError(f'Unknown assistant type. Use {valid_types}')
        
        return cls._assistants[assistant_type]()


class RequestParser:
    """Parses and validates incoming requests (Single Responsibility)."""
    
    @staticmethod
    def parse(event: Dict[str, Any]) -> AssistantRequest:
        """Parse AWS Lambda event into AssistantRequest."""
        body = event.get('body')
        if body:
            data = json.loads(body)
        else:
            data = event

        assistant_type = data.get('assistant')
        prompt = data.get('prompt')
        
        if not prompt:
            raise AssistantError('Prompt is required')
            
        return AssistantRequest(assistant_type=assistant_type, prompt=prompt)


class AssistantService:
    """Main service for processing assistant requests (Dependency Inversion)."""

    def __init__(self, factory: AssistantFactory, parser: RequestParser):
        self.factory = factory
        self.parser = parser

    def process_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process an assistant request."""
        try:
            request = self.parser.parse(event)
            assistant = self.factory.create(request.assistant_type)
            content = assistant.process(request.prompt)
            metadata = assistant.get_metadata()
            response = AssistantResponse(content=content, metadata=metadata)
            return response.to_lambda_response()
        except AssistantError as e:
            return e.to_lambda_response()
        except Exception as e:
            error = AssistantError(str(e), 500)
            return error.to_lambda_response()

def lambda_handler(event, context):
    """AWS Lambda entry point."""
    print("lambda_handler invoked with event:", event)
    
    # Dependency injection - easy to test and extend
    service = AssistantService(
        factory=AssistantFactory,
        parser=RequestParser
    )
    
    return service.process_request(event)
