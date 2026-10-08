# Floyd - OpenAI Assistant Router System

## Project Overview
Floyd is an AWS Lambda-based system that routes user prompts to specialized OpenAI assistants based on intent classification. The system uses a two-stage process: prompt rewriting (to second person) and routing to the appropriate assistant.

## Architecture

### Core Components

1. **Floyd** (`floyd.py`) - Base wrapper for OpenAI Assistants API
   - Handles thread creation, message management, and assistant execution
   - Provides simple chat interface with automatic thread management

2. **Router** (`router.py`) - Intent classification system
   - Inherits from Floyd
   - Determines which assistant to use based on prompt analysis
   - Returns assistant type strings

3. **RewriteSecondPerson** (`rewrite_second_person.py`) - Prompt preprocessor
   - Inherits from Floyd
   - Rewrites prompts into second person format
   - Can return "no" to short-circuit the routing process

4. **Main Lambda Handler** (`main.py`) - AWS Lambda entry point
   - Orchestrates the entire flow: rewrite → route → respond
   - Maps assistant types to OpenAI assistant IDs via environment variables

### Assistant Types
The system supports these specialized assistants:
- `basic_response` - General responses
- `router` - Routes to other assistants
- `DoSomething` - Action-oriented tasks
- `PickUp` - Object pickup tasks (returns JSON with `object` parameter)
- `GoSomewhere` - Movement/navigation (returns JSON with `direction` parameter)
- `AskQuestion` - Question handling
- `GiveInstruction` - Instruction giving
- `SocialEmotional` - Social/emotional interactions
- `MetaCommand` - Meta commands
- `Nonsense` - Nonsense handling
- `RewriteSecondPerson` - Prompt rewriting

### Structured Responses
Some assistants return structured JSON responses to provide metadata about the action:

**GoSomewhere** - Returns direction information:
```json
{
  "message": "Floyd heads north towards the castle.",
  "direction": "north"
}
```

**PickUp** - Returns object information:
```json
{
  "message": "Floyd picks up the sword.",
  "object": "sword"
}
```

The Lambda handler automatically parses these JSON responses and includes the metadata in the response:
```json
{
  "statusCode": 200,
  "body": {
    "results": {
      "single_message": "Floyd heads north towards the castle.",
      "metadata": {
        "assistant_type": "GoSomewhere",
        "parameters": {
          "direction": "north"
        }
      }
    }
  }
}
```

Assistants that don't return JSON will work as before (backward compatible).

### Flow
1. User sends prompt with `assistant: "router"`
2. System rewrites prompt to second person
3. If rewrite returns "no", process stops
4. Router classifies the rewritten prompt
5. System routes to appropriate specialized assistant
6. Assistant generates final response

## Key Files

### Production Code
- `main.py` - Lambda handler with routing logic
- `floyd.py` - OpenAI Assistants API wrapper
- `router.py` - Intent classification
- `rewrite_second_person.py` - Prompt preprocessing
- `requirements.txt` - Python dependencies
- `template.yaml` - AWS SAM template for deployment
- `samconfig.toml` - SAM configuration

### Test Files
- `tests/test_*.py` - Unit tests for each component
- `manual_test_*.py` - Manual testing scripts
- `event.json` - Sample event for testing
- `response.json` - Sample response

## Environment Variables
- `OPENAI_API_KEY` - OpenAI API key. **In AWS it is not set on the function**: `openai_key.py` reads it
  at cold start from the Secrets Manager secret `OpenAiApiKey`, shared with the ZorkAI game Lambdas, so
  a key rotation is one `put-secret-value` plus a cold start. Locally, set it in `.env` and the secret
  is never read.
- The old `OPENAI_*_ASSISTANT_ID` variables are gone. They died with the Assistants API (see `MIGRATION.md`).

## Testing
- Use `manual_test_main.py` to test locally with `event.json`
- Unit tests cover all components with proper mocking
- Tests verify routing logic, error handling, and edge cases

## Development Notes
- The system is designed for AWS Lambda deployment
- All assistants inherit from the base Floyd class
- Error handling returns appropriate HTTP status codes
- Logging throughout for debugging assistance
- The router short-circuits on "no" rewrite responses

## Security Considerations
`template.yaml` and `samconfig.toml` hold no secrets and are committed. Keep it that way: the OpenAI
key belongs in the `OpenAiApiKey` secret, never in the template (it used to be there, which is why
these files were once gitignored). Deploy with `sam build && sam deploy`. The build runs in a container
because the runtime is python3.13, and the deploy uses the `delve` AWS profile (account 576431164672).

## Git Status
- Modified: `event.json` (test event)
- Untracked: `response.json` (test response)