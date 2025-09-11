import re
from groq import Groq
from dotenv import load_dotenv
from os import getenv
from .utils import get_response
from ast import literal_eval
from copy import deepcopy
load_dotenv()

class GuardAgent():
    def __init__(self) -> None:
        self.client = Groq(api_key=getenv("GROQ_API_KEY"))
        self.model_name = getenv("MODEL_NAME")

    def respond(self, messages):
        messages = deepcopy(messages)

        system_prompt = """
        You are a helpful AI assistant for a coffee shop app that SERVES DRINKS and PASTRIES.
        Your task is to decide whether the user input is APPROPRIATE and RELEVANT to the coffee shop.

        ✅ ALLOW if the user is asking about:
        - Ordering items (e.g., "I want a latte")
        - Menu items (e.g., "What's in the menu?")
        - Recommendations (e.g., "What pastry goes with coffee?", "Recommend a bakery item")
        - Coffee shop info (e.g., "What are your hours?")

        🚫 NOT ALLOWED if the user asks about:
        - Irrelevant topics (e.g., "How to fix my car?", "Tell me a joke")
        - Competitors (e.g., "What does Starbucks sell?")
        - Inappropriate/offensive content

        Respond STRICTLY with VALID JSON in this exact format:
            {
            "chain of thought": "<brief reasoning>",
            "decision": "allowed" or "not allowed",
            "message": if not allowed, write "Sorry I can't help with that, can I help you with your order?", else leave it empty.
            }

        CRITICAL:
        - Do NOT call any tools or functions
        - Do NOT add extra fields
        - Do NOT include markdown formatting
        - Return ONLY the JSON object
        """

        input_messages = [{"role": "system", "content": system_prompt}] + \
                            [{"role": message['role'], "content": message["content"]} for message in messages[-3:]]

        response = get_response(self.client, self.model_name, input_messages)
        # print(response)

        return self.postprocess(response)

    def postprocess(self, response):
        try:
            response = literal_eval(response)

            return {
                "role": "assistant",
                "content": response['message'] or "",
                "metadata": {"agent": "guard agent",
                            "decision": response["decision"]}
                }

        except:
            return {
                "role": "assistant",
                "content": "I didn't quite understand that, please say that again?",
                "metadata": {"agent": "guard_agent",
                            "decision": "not allowed"}
                }