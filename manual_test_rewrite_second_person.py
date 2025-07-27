import json
from rewrite_second_person import lambda_handler


def main():
    """Load rewrite_event.json and invoke the rewrite lambda_handler."""
    with open('rewrite_event.json', 'r') as f:
        event = json.load(f)

    response = lambda_handler(event)
    print(json.dumps(response, indent=2))


if __name__ == '__main__':
    main()
