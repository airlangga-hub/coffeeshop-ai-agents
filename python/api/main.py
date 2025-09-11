from fastapi import FastAPI
from pydantic import BaseModel
from agent_controller import AgentController
from typing import Any, List, Dict

app = FastAPI(
    title="CoffeeShop AI Agents API",
    description="An API for a multi-agent AI system designed to assist with coffee shop operations."
)

agent_controller = AgentController()

class Message(BaseModel):
    role: str
    content: str
    metadata: Dict[str, Any] = {}

class Messages(BaseModel):
    messages: List[Message]

@app.post("/respond")
async def respond(input: Messages):
    response = agent_controller.respond(input.model_dump())
    return response

@app.get("/")
async def root():
    return {"message": "Welcome to the CoffeeShop AI Agents API"}