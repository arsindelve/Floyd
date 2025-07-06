import json
from main import lambda_handler


def main():
    """Load event.json and invoke lambda_handler."""
    with open('event.json', 'r') as f:
        event = json.load(f)

    response = lambda_handler(event, None)
    print(json.dumps(response, indent=2))


if __name__ == '__main__':
    main()
