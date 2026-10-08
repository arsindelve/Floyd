import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

from openai_key import ensure_openai_key
from characters.floyd import Floyd
from rewrite_second_person import RewriteSecondPerson
from characters.blather import Blather
from characters.ambassador import Ambassador

DEPLOYMENT_VERSION = "1.0.1"
print(f"Floyd Lambda initialized - Version: {DEPLOYMENT_VERSION}")

# Once per cold start, before any request builds an OpenAI client. See openai_key.py.
ensure_openai_key()


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


class FloydAssistant(AssistantInterface):
    """Floyd's conversational assistant, now backed by Chat Completions.

    The router + specialist Assistants this used to orchestrate were retired with the Assistants
    API (2026-08-26). characters.floyd.Floyd now handles voice AND intent classification in a
    single call and hands back the metadata the game reads (PickUp / GoSomewhere).
    """

    def __init__(self):
        self._floyd = Floyd()
        self._last_metadata: Optional[Dict[str, Any]] = None

    def process(self, prompt: str) -> str:
        message, self._last_metadata = self._floyd.respond(prompt)
        return message

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Return metadata from the last Floyd response."""
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
