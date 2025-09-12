from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from httpx import get
from pydantic import BaseModel
from agent_controller import AgentController
from typing import Any, List, Dict, Literal
from dotenv import load_dotenv
from os import getenv
load_dotenv()

VERIFY_TOKEN = getenv("VERIFY_TOKEN")

app = FastAPI(
    title="CoffeeShop AI Agents API",
    description="An API for a multi-agent AI system designed to assist with coffee shop operations."
)

agent_controller = AgentController()

class Message(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content: str
    metadata: Dict[str, Any] = {}

class Messages(BaseModel):
    messages: List[Message]

@app.get("/respond")
async def verify_webhook(request: Request):
    hub_mode = request.query_params.get("hub.mode")
    hub_challenge = request.query_params.get("hub.challenge")
    hub_verify_token = request.query_params.get("hub.verify_token")

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        # print("✅ Webhook verified successfully!")
        return PlainTextResponse(content=hub_challenge)
    else:
        # print("❌ Verification failed: Invalid token or mode.")
        return Response(status_code=403)

@app.post("/respond")
async def respond(input: Messages):
    response = agent_controller.respond(input.model_dump())
    return response

@app.get("/")
async def root():
    return {"message": "Welcome to the CoffeeShop AI Agents API"}