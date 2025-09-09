from groq import Groq
from dotenv import load_dotenv
from os import getenv
from .utils import get_response
import json
from copy import deepcopy
load_dotenv()

class OrderAgent():
    def __init__(self, recommendation_agent) -> None:
        self.client = Groq(api_key=getenv("GROQ_API_KEY"))
        self.model_name = getenv("MODEL_NAME")

        self.recommendation_agent = recommendation_agent

    def respond(self, messages):
        messages = deepcopy(messages)

        system_prompt = """
            You are a customer support Chat Bot for a coffee shop application.

            Here is the menu for this coffee shop application.

            Cappuccino - $4.50
            Jumbo Savory Scone - $3.25
            Latte - $4.75
            Chocolate Chip Biscotti - $2.50
            Espresso shot - $2.00
            Hazelnut Biscotti - $2.75
            Chocolate Croissant - $3.75
            Dark chocolate (Drinking Chocolate) - $5.00
            Cranberry Scone - $3.50
            Croissant - $3.25
            Almond Croissant - $4.00
            Ginger Biscotti - $2.50
            Oatmeal Scone - $3.25
            Ginger Scone - $3.50
            Chocolate syrup - $1.50
            Hazelnut syrup - $1.50
            Carmel syrup - $1.50
            Sugar Free Vanilla syrup - $1.50
            Dark chocolate (Packaged Chocolate) - $3.00

            Things to NOT DO:
            * DON't ask how to pay by cash or Card.
            * Don't tell the user to go to the counter
            * Don't tell the user to go to place to get the order

            You're task is as follows:
            1. Take the User's Order
            2. Validate that all their items are in the menu
            3. if an item is not in the menu let the user repeat back the remaining valid order
            4. Ask them if they need anything else.
            5. If they do then repeat starting from step 3
            6. If they don't want anything else. Using the "order" object that is in the output. Make sure to hit all three points:
                1. list down all the items and their prices
                2. calculate the total.
                3. Thank the user for the order and close the conversation with no more questions

            The user message will contain the following:
            "order"
            "step number"
            please utilize this information to determine the next step in the process.

            Produce the following output without any additions, not a single letter outside of the structure bellow.
            Your output MUST be a VALID JSON in this EXACT format:
                {
                "chain of thought": Write down your critical thinking about what is the maximum task number the user is on right now. Then write down your critical thinking about the user input and it's relation to the coffee shop process. Then write down your thinking about how you should respond in the response parameter taking into consideration the Things to NOT DO section. and Focus on the things that you should not do.
                "step number": Determine which task you are on based on the conversation.
                "order": this is going to be a VALID Python List of Dictionaries like so. [{"item": put the item name, "quantity": put the number that the user wants from this item, "price": put the total price of the item }]. This MUST BE A VALID PYTHON LIST OF DICTIONARIES! Make sure this is NOT a string!
                "response": write a response to the user
                }

            IMPORTANT: Make sure NOT to delete anything from "order". ONLY EXTEND the list with the exact dictionary format specified above!
        """

        last_order_status = ""
        asked_recommendation_before = False

        for message in reversed(messages):
            if message.get("metadata", {}).get("agent", "") == "order_agent":
                step_number = message['metadata']['step number']
                order = message['metadata']['order']
                asked_recommendation_before = message['metadata']['asked_recommendation_before']

                last_order_status = f"""
                step number = {step_number}
                order = {order}
                """
                break

        if last_order_status:
            messages[-1]['content'] = last_order_status + "\n\n" + messages[-1]['content']

        input_messages = [{"role": "system", "content": system_prompt}] +\
                            [{"role": message["role"], "content": message["content"]} for message in messages[-3:]]

        response = get_response(self.client, self.model_name, input_messages)

        return self.postprocess(response, asked_recommendation_before, messages)

    def postprocess (self, response, asked_recommendation_before, messages):
        try:
            response = json.loads(response)

            if isinstance(response['order'], str):
                response['order'] = json.loads(response['order'])

            response = response['response']
            if not asked_recommendation_before and len(response['order']) > 1:
                asked_recommendation_before = True

                recommendation_output = self.recommendation_agent.get_recommendation_from_order(response['order'], messages)

                response = recommendation_output['content']

            return {
                "role": "assistant",
                "content": response,
                "metadata": {"agent": "order_agent",
                            "asked_recommendation_before": asked_recommendation_before,
                            "step number": response['step number'],
                            "order": response['order']}
            }

        except Exception:
            return {
                "role": "assistant",
                "content": "I didn't quite understand that, please say that again?",
                "metadata": {"agent": "order_agent",
                            "asked_recommendation_before": False,
                            "step number": 0,
                            "order": []}
            }