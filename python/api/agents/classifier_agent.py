from ast import literal_eval
from groq import Groq
from dotenv import load_dotenv
from os import getenv
from .utils import get_response
from copy import deepcopy
load_dotenv()

class ClassifierAgent():
    def __init__(self) -> None:
        self.client = Groq(api_key=getenv("GROQ_API_KEY"))
        self.model_name = getenv("MODEL_NAME")

    def respond(self, messages):
        messages = deepcopy(messages)

        system_prompt = """
        You are a classifier AI assistant for a coffee shop application that serves drinks and pastries. Your sole job is to determine which specialized agent should handle the user's input.

        Available Agents:
        1. details_agent - Handles: location, working hours, menu items, delivery areas, general info about the coffee shop
        2. order_agent - Handles: taking food/drink orders, order modifications, order confirmations
        3. recommendation_agent - Handles: suggesting menu items, personalized recommendations

        Instructions:
        - Analyze the user's most recent message
        - Choose EXACTLY ONE agent from: "details_agent", "order_agent", or "recommendation_agent"
        - Respond STRICTLY with VALID JSON in this exact format:
            {
            "chain of thought": "<brief reasoning>",
            "decision": "details_agent" or "order_agent" or "recommendation_agent"
            }

        CRITICAL:
        - Do NOT call any tools or functions
        - Do NOT add extra fields
        - Do NOT include markdown formatting
        - Return ONLY the JSON object
        """

        input_messages = [{"role": "system", "content": system_prompt}] +\
                            [{"role": message["role"], "content": message["content"]} for message in messages[-3:]]

        response = get_response(self.client, self.model_name, input_messages)

        return self.postprocess(response)

    def postprocess(self, response):
        try:
            response = literal_eval(response)

            return {
                "role": "assistant",
                "content": "",
                "metadata": {"agent": "classifier agent",
                            "decision": response["decision"]}
                }

        except:
            return {
                "role": "assistant",
                "content": "I didn't quite understand that, please say that again?",
                "metadata": {"agent": "classifier_agent",
                            "decision": "unknown"}
                }