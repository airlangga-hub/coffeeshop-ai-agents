from groq import Groq
from dotenv import load_dotenv
from os import getenv
from .utils import get_response
from copy import deepcopy
from pinecone import Pinecone
from huggingface_hub import InferenceClient

load_dotenv()

class DetailsAgent():
    def __init__(self) -> None:
        self.client = Groq(api_key=getenv("GROQ_API_KEY"))
        self.model_name = getenv("MODEL_NAME")

        self.hf_client = InferenceClient(provider="hf-inference", api_key=getenv("HUGGINGFACE_TOKEN"))
        self.embedding_model_name = getenv("EMBEDDING_MODEL_NAME")

        self.pc = Pinecone(getenv("PINECONE_API_KEY "))
        self.index_name = getenv("INDEX_NAME", "coffeeshop")

    def query_pinecone(self,  input_embeddings, top_k=5):
        index = self.pc.Index(self.index_name)

        result = index.query(
            vector=input_embeddings,
            namespace='ns1',
            top_k=top_k,
            include_values=False,
            include_metadata=True
        )

        return result

    def respond(self, messages):
        messages = deepcopy(messages)
        user_input = messages[-1]['content']

        input_embeddings = self.hf_client.feature_extraction(user_input, model=self.embedding_model_name)

        result = self.query_pinecone(input_embeddings.tolist())

        context = "\n\n".join([x['metadata']['text'].strip() for x in result['matches']])

        system_prompt = """
        You are a friendly and knowledgeable waiter at a coffee shop. Your role is to provide accurate, helpful information about the menu, services, and policies.

        Key responsibilities:
        ✓ Answer questions about menu items, prices, and ingredients
        ✓ Provide store hours, location, and contact information
        ✓ Explain ordering processes and available services
        ✓ Share details about special offers or seasonal items
        ✓ Clarify dietary information and customization options

        Communication style:
        • Be warm, professional, and conversational
        • Use clear, concise language
        • Provide specific details when available
        • If you don't know something, be honest and suggest alternatives
        • Always maintain a helpful, customer-focused tone

        Important guidelines:
        - Only use information from the provided context
        - If the context doesn't contain relevant information, politely say you don't have those details
        - Stay in character as a coffee shop waiter
        - Focus on being HELPFUL rather than overly chatty
        """

        prompt = f"""
        Using the provided context, answer the query.

        Context:
        {context}

        Query:
        {user_input}
        """

        messages[-1]['content'] = prompt

        input_messages = [{"role": "system", "content": system_prompt}] + \
                            [{"role": message['role'], "content": message["content"]} for message in messages[-3:]]

        response = get_response(self.client, self.model_name, input_messages)

        return self.postprocess(response)

    def postprocess(self, response):
        return {
            "role": "assistant",
            "content": response,
            "metadata": {"agent": "details_agent"}
            }