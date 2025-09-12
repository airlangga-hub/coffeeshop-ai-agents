from fastapi import FastAPI, Request, Response, Body
from fastapi.responses import PlainTextResponse, JSONResponse
from agent_controller import AgentController
from typing import Any, Dict
from dotenv import load_dotenv
from os import getenv

load_dotenv()

VERIFY_TOKEN = getenv("VERIFY_TOKEN", "171295")  # Fallback if .env missing

app = FastAPI(
    title="CoffeeShop AI Agents API",
    description="An API for a multi-agent AI system designed to assist with coffee shop operations."
)

agent_controller = AgentController()

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
    """
    Accepts raw JSON from Meta webhook.
    Logs it, extracts message, and passes to agent controller.
    """
    # print("\n" + "="*70)
    # print("📩 INCOMING RAW PAYLOAD FROM META:")
    # print(input)
    # print("="*70 + "\n")

    try:

        if not input:
            return JSONResponse(
                content={"error": "Empty payload"},
                headers={"ngrok-skip-browser-warning": "true"}
            )

        # Process first event
        messages = input["entry"][0]["changes"][0]["value"].get("messages", [])

        if not messages:
            return JSONResponse(
                content={"error": "No messages in payload"},
                headers={"ngrok-skip-browser-warning": "true"}
            )

        # Get first message
        first_msg = messages[0]
        if first_msg.get("type") != "text" or not first_msg.get("text"):
            return JSONResponse(
                content={"error": "Only text messages are supported"},
                headers={"ngrok-skip-browser-warning": "true"}
            )

        user_message = first_msg["text"]["body"]

        contacts = input["entry"][0]["changes"][0]["value"].get("contacts", [])
        wa_id = contacts[0]["wa_id"] if contacts else None
        phone_number_id = input["entry"][0]["changes"][0]["value"].get("metadata", {}).get("phone_number_id", "unknown")
        display_phone_number = input["entry"][0]["changes"][0]["value"].get("metadata", {}).get("display_phone_number", "unknown")

        # Convert to your agent's expected format
        internal_messages = {
            "messages": [
                {
                    "role": "user",
                    "content": user_message,
                    "metadata": {
                        "wa_id": wa_id,
                        "phone_number_id": phone_number_id,
                        "display_phone_number": display_phone_number
                        # Optional: keep original for debugging
                        # "original_payload": input
                    }
                }
            ]
        }

        # Get response from your agent system
        agent_response = agent_controller.respond(internal_messages)

        # Return with ngrok header to suppress warning page
        return JSONResponse(
            content=agent_response,
            headers={"ngrok-skip-browser-warning": "true"}
        )

    except Exception as e:
        # print("❌ Error processing payload:", str(e))
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