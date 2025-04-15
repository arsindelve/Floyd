from fastapi import FastAPI, Request
from mangum import Mangum
from app.langgraph_logic import build_graph

app = FastAPI()
graph = build_graph()

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_input = body.get("input", "")
    result = graph.invoke({"input": user_input})
    return result

handler = Mangum(app)  # Lambda entry point