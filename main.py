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
    
    def to_lambda_response(self) -> Dict[str, Any]:
        """Convert to AWS Lambda response format."""
        return {
            'statusCode': 200,
            'body': json.dumps({
                'results': {
                    'single_message': self.content
                }
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


class FloydAssistant(AssistantInterface):
    """Wrapper for Floyd routing assistant."""
    
    def __init__(self):
        self._floyd_assistant_id = os.environ.get("OPENAI_ROUTER_ASSISTANT_ID")
        if not self._floyd_assistant_id:
            raise AssistantError("Floyd assistant ID not configured", 500)
    
    def process(self, prompt: str) -> str:
        try:
            router = Floyd(self._floyd_assistant_id)
            route, assistant_id = router.route_and_get_assistant_id(prompt)
            client = OpenAIAssistantClient(assistant_id)
            response = client.chat(prompt)
            return response['content']
        except ValueError as e:
            raise AssistantError(str(e))


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
            response = AssistantResponse(content=content)
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
