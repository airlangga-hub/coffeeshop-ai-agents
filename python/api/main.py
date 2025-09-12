from fastapi import FastAPI, Request, Response, Body
from fastapi.responses import PlainTextResponse, JSONResponse
from agent_controller import AgentController
from typing import Any, Dict, List
from dotenv import load_dotenv
from os import getenv

load_dotenv()

VERIFY_TOKEN = getenv("VERIFY_TOKEN", "171295")  # Fallback if .env missing

app = FastAPI(
    title="CoffeeShop AI Agents API",
    description="An API for a multi-agent AI system designed to assist with coffee shop operations."
)

agent_controller = AgentController()

# In-memory storage for chat history (key: wa_id, value: list of messages)
USER_CHAT_HISTORY: Dict[str, List[Dict[str, Any]]] = {}

# ================
# GET /respond — For Webhook Verification
# ================
@app.get("/respond")
async def verify_webhook(request: Request):
    hub_mode = request.query_params.get("hub.mode")
    hub_challenge = request.query_params.get("hub.challenge")
    hub_verify_token = request.query_params.get("hub.verify_token")

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge)
    else:
        return Response(status_code=403)

# ================
# POST /respond — For Receiving WhatsApp Messages
# ================
@app.post("/respond")
async def respond(input: Dict[Any, Any] = Body(...)):
    try:
        if not input:
            return JSONResponse(
                content={"error": "Empty payload"},
                headers={"ngrok-skip-browser-warning": "true"}
            )

        # Extract message data
        entry = input["entry"][0]
        change = entry["changes"][0]
        value = change["value"]

        messages = value.get("messages", [])
        if not messages:
            return JSONResponse(
                content={"error": "No messages in payload"},
                headers={"ngrok-skip-browser-warning": "true"}
            )

        first_msg = messages[0]
        if first_msg.get("type") != "text" or not first_msg.get("text"):
            return JSONResponse(
                content={"error": "Only text messages are supported"},
                headers={"ngrok-skip-browser-warning": "true"}
            )

        user_message_body = first_msg["text"]["body"]
        contacts = value.get("contacts", [])
        wa_id = contacts[0]["wa_id"] if contacts else "unknown_user"
        phone_number_id = value.get("metadata", {}).get("phone_number_id", "unknown")
        display_phone_number = value.get("metadata", {}).get("display_phone_number", "unknown")

        # Initialize or retrieve chat history for this user
        if wa_id not in USER_CHAT_HISTORY:
            USER_CHAT_HISTORY[wa_id] = []

        chat_history = USER_CHAT_HISTORY[wa_id]

        # Append new user message
        chat_history.append({
            "role": "user",
            "content": user_message_body,
            "metadata": {
                "wa_id": wa_id,
                "phone_number_id": phone_number_id,
                "display_phone_number": display_phone_number
            }
        })

        # Pass FULL history to agent controller
        internal_input = {"messages": chat_history}
        agent_response = agent_controller.respond(internal_input)

        # Append agent's response to history
        chat_history.append(agent_response)

        # Return only the latest response to WhatsApp
        return JSONResponse(
            content=agent_response,
            headers={"ngrok-skip-browser-warning": "true"}
        )

    except Exception as e:
        return JSONResponse(
            content={"error": f"Processing failed: {str(e)}"},
            headers={"ngrok-skip-browser-warning": "true"},
            status_code=500
        )

# ================
# GET / — Root Endpoint
# ================
@app.get("/")
async def root():
    return JSONResponse(
        content={"message": "Welcome to the CoffeeShop AI Agents API"},
        headers={"ngrok-skip-browser-warning": "true"}
    )