from groq import Groq
from dotenv import load_dotenv
from os import getenv
from .utils import get_response
import json
from copy import deepcopy
load_dotenv()

class GuardAgent():
    def __init__(self) -> None:
        self.client = Groq(api_key=getenv("GROQ_API_KEY"))
        self.model_name = getenv("MODEL_NAME")

    def respond(self, messages):
        messages = deepcopy(messages)

        system_prompt = """
        You are a helpful AI Assistant for a coffee shop application that sells drinks and pastries.
        Your job is to DETERMINE whether the User Input is RELEVANT to the Coffee Shop or NOT.

        The user is ALLOWED to:
        1. Ask questions about the coffee shop, like location, working hours, menu items and coffee shop related questions.
        2. Ask questions about menu items, they can ask for ingredients in an item and other details about the item.
        3. Make an order.
        4. Ask for recommendations of what to buy.

        The user is NOT allowed to:
        1. Ask questions about anything else other than the coffee shop.
        2. Ask questions about the staff or how to make a certain menu item.

        Your output should be in a structured json format like so. Each key is a string and each value is a string. Make sure to follow the format exactly:
        {
        "chain of thought": go over each of the points above and see if the input lies under this point or not. Then you write your thoughts about which point this input is relevant to.
        "decision": "allowed" or "not allowed". Pick one of those. and only write the word.
        "message": leave the message empty if it's allowed, otherwise write "Sorry, I can't help with that. Can I help you with your order?"
        }
        """

        input_messages = [{"role": "system", "content": system_prompt}] + \
                            [{"role": message['role'], "content": message["content"]} for message in messages[-3:]]

        response = get_response(self.client, self.model_name, input_messages)
        response = self.postprocess(response)

        return response

    def postprocess(self, response):
        try:
            response = json.loads(response)

            return {
                "role": "assistant",
                "content": response['message'],
                "metadata": {"agent": "guard agent",
                            "decision": response["decision"]}
                }

        except Exception:
            return {
                "role": "assistant",
                "content": "I didn't quite understand that, please say that again?",
                "metadata": {"agent": "guard agent",
                            "decision": "not allowed"}
                }