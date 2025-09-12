from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from httpx import get
from pydantic import BaseModel
from agent_controller import AgentController
from typing import List, Optional
from pydantic import Field
from dotenv import load_dotenv
from os import getenv
load_dotenv()

VERIFY_TOKEN = getenv("VERIFY_TOKEN")

app = FastAPI(
    title="CoffeeShop AI Agents API",
    description="An API for a multi-agent AI system designed to assist with coffee shop operations."
)

agent_controller = AgentController()

class WhatsAppText(BaseModel):
    body: str

class WhatsAppMessage(BaseModel):
    from_: str = Field(..., alias="from")  # "from" is a reserved keyword
    id: str
    timestamp: str
    type: str
    text: Optional[WhatsAppText] = None

class WhatsAppContactProfile(BaseModel):
    name: str

class WhatsAppContact(BaseModel):
    profile: WhatsAppContactProfile
    wa_id: str

class WhatsAppMetadata(BaseModel):
    display_phone_number: str
    phone_number_id: str

class WhatsAppValue(BaseModel):
    messaging_product: str
    metadata: WhatsAppMetadata
    contacts: List[WhatsAppContact]
    messages: List[WhatsAppMessage]

class MetaWebhookRequest(BaseModel):
    field: str
    value: WhatsAppValue

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
async def respond(input: MetaWebhookRequest):
    # Extract the first message body
    if input.value.messages:
        first_message = input.value.messages[0]
        if first_message.type == "text" and first_message.text:
            user_message = first_message.text.body

            # Convert to your internal format
            internal_messages = {
                "messages": [
                    {
                        "role": "user",
                        "content": user_message,
                        "metadata": {
                            "wa_id": input.value.contacts[0].wa_id if input.value.contacts else None,
                            "phone_number_id": input.value.metadata.phone_number_id
                            # "original_payload": input.model_dump()  # optional: keep original for debugging
                        }
                    }
                ]
            }

            # Pass to your agent system
            response = agent_controller.respond(internal_messages)
            return response

    return {"error": "No valid message found"}

@app.get("/")
async def root():
    return {"message": "Welcome to the CoffeeShop AI Agents API"}