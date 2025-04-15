import json
from main import handler

# Simulated API Gateway v2 event
event = {
    "version": "2.0",
    "routeKey": "$default",
    "rawPath": "/chat",
    "rawQueryString": "",
    "headers": {
        "Content-Type": "application/json"
    },
    "requestContext": {
        "accountId": "123456789012",
        "apiId": "api-id",
        "domainName": "test.execute-api.amazonaws.com",
        "domainPrefix": "test",
        "http": {
            "method": "POST",
            "path": "/chat",
            "protocol": "HTTP/1.1",
            "sourceIp": "127.0.0.1",
            "userAgent": "curl/7.68.0"
        },
        "requestId": "some-request-id",
        "routeKey": "$default",
        "stage": "$default",
        "time": "12/Mar/2022:19:03:58 +0000",
        "timeEpoch": 1647102238000
    },
    "body": json.dumps({"input": "Hello from Lambda test!"}),
    "isBase64Encoded": False
}

# Dummy context for Lambda
class DummyContext:
    def __init__(self):
        self.function_name = "testFunction"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:testFunction"
        self.aws_request_id = "test_request_id"

context = DummyContext()

response = handler(event, context)
print("Lambda response:", response)