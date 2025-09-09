from ast import literal_eval
from math import prod
from groq import Groq
from dotenv import load_dotenv
from os import getenv
from .utils import get_response
import json
import pandas as pd
from copy import deepcopy
from pathlib import Path
load_dotenv()

class RecommendationAgent():
    def __init__(self) -> None:
        self.client = Groq(api_key=getenv("GROQ_API_KEY"))
        self.model_name = getenv("MODEL_NAME")

        root_dir = Path(__file__).parent.parent.parent
        self.apriori_path = root_dir/"recommendation_objects"/"apriori_recommendations.json"
        self.popularity_path = root_dir/"recommendation_objects"/"popularity_recommendation.csv"

        self.popular_df = pd.read_csv(self.popularity_path)
        with open(self.apriori_path, 'r') as f:
            self.apriori_obj = json.load(f)

        self.products = self.popular_df['product'].unique().tolist()
        self.product_categories = self.popular_df['product_category'].unique().tolist()

    def get_popular_recommendation(self, product_categories=None, current_order=None, top_k=5):
        if isinstance(product_categories, str):
            product_categories = [product_categories]

        order = [dic['item'] for dic in current_order] if current_order else []

        df = self.popular_df

        if product_categories:
            df = df[df['product_category'].isin(product_categories)]

        df = df[~df['product'].isin(order)] if current_order else df

        df = df.sort_values('number_of_transactions', ascending=False)

        return df['product'].tolist()[:top_k]

    def get_apriori_recommendation(self, products, current_order=None, top_k=5):
        order = []
        if current_order:
            order = [dic['item'] for dic in current_order]

        recom_list = []
        for product in products:
            if product in self.apriori_obj:
                recom_list.extend(self.apriori_obj[product])

        # sort recom list by confidence
        recom_list = sorted(recom_list, key=lambda dic: dic['confidence'], reverse=True)

        # limit 2 recoms per category
        recoms = []
        category_counter = {}
        for dic in recom_list:
            if len(recoms) >= top_k:
                break

            category = dic['product_category']
            product = dic['product']

            if product in recoms or product in products or product in order:
                continue

            category_counter[category] = category_counter.get(category, 0) + 1

            if category_counter[category] > 2:
                continue

            recoms.append(product)

        return recoms

    def recommendation_classification(self, messages):
        current_order = None
        for message in reversed(messages):
            if message.get("metadata", {}).get("agent", "") == "order_agent":
                current_order = message['metadata']['order']
                break

        system_prompt = """ You are a helpful AI assistant for a coffee shop application which serves drinks and pastries. We have 3 types of recommendations:

        1. Apriori Recommendations: These are recommendations based on the user's order history. We recommend items that are frequently bought together with the items in the user's order.
        2. Popular Recommendations: These are recommendations based on the popularity of items in the coffee shop. We recommend items that are popular among customers.
        3. Popular by Category Recommendations: Here the user asks to recommend them product in a category. Like what coffee do you recommend me to get?. We recommend items that are popular in the user's requested category.

        Here is the user's current order:
        """ + (", ".join([dic['item'] for dic in current_order]) if current_order else "No current order") + """

        Make SURE all the items in the user's order match the items in the coffee shop. PAY ATTENTION to the list of items in the coffee shop below!!! If an item in the user's order looks very similar to an item in the coffee shop, but is not exactly the same, then change ONLY that item with the correct item from the coffee shop and KEEP EVERYTHING ELSE THE SAME!!!

        Here is the list of items in the coffee shop:
        """ + ", ".join(self.products) + """

        Here is the list of Categories we have in the coffee shop:
        """ + ", ".join(self.product_categories) + """

        Your task is to determine which type of recommendation to provide based on the user's message.

        Your output should be in a structured json format like so. Each key is a string and each value is a string. Make sure to follow the format exactly:
            {
            "chain of thought": Write down your critical thinking about what type of recommendation is this input relevant to.
            "recommendation_type": "apriori" or "popular" or "popular by category". Pick one of those and only write the word.
            "parameters": This is a python list. It's either a list of of items for apriori recommendations or a list of categories for popular by category recommendations. Leave it empty for popular recommendations. Make sure to use the exact strings from the list of items and categories above.
            }
        """

        input_messages = [{"role": "system", "content": system_prompt}] +\
                            [{"role": message['role'], "content": message['content']} for message in messages[-3:]]

        response = get_response(self.client, self.model_name, input_messages)

        return self.postprocess_classification(response, current_order)

    def postprocess_classification(self, response, current_order):
        try:
            response = literal_eval(response)

            return {
                "recommendation_type": response["recommendation_type"],
                "parameters": response["parameters"],
                "current_order": current_order if current_order else []
            }

        except:
            return {
                "recommendation_type": "popular",
                "parameters": "",
                "current_order": current_order if current_order else []
            }

    def get_recommendation_from_order(self, order, messages):
        messages = deepcopy(messages)

        products = [dic['item'] for dic in order]

        recoms = self.get_apriori_recommendation(products, order)
        recoms_str = ", ".join(recoms)

        system_prompt = """
        You are a helpful AI assistant for a coffee shop application which serves drinks and pastries.
        Your task is to recommend items to the user based on their order.

        I will provide what items you should recommend to the user based on their order in the user message.
        """

        prompt = f"""
        {messages[-1]['content']}

        STRICTLY Recommend The Following Items, DO NOT recommend anything else:
        {recoms_str}
        """

        messages[-1]['content'] = prompt

        input_messages = [{"role": "system", "content": system_prompt}] +\
                            [{"role": message['role'], "content": message['content']} for message in messages[-3:]]

        response = get_response(self.client, self.model_name, input_messages)

        return self.postprocess(response, "apriori", str(products))

    def postprocess(self, response, recommendation_type, parameters=None):
        return {
            "role": "assistant",
            "content": response,
            "metadata": {"agent": "recommendation_agent",
                         "recommendation_type": recommendation_type,
                         "parameters": parameters if parameters else ""}
        }

    def respond(self, messages):
        messages = deepcopy(messages)

        recommendation_classification = self.recommendation_classification(messages)
        recommendation_type = recommendation_classification['recommendation_type']
        current_order = recommendation_classification['current_order']

        if recommendation_type == "apriori":
            recommendations = self.get_apriori_recommendation(recommendation_classification['parameters'], current_order=current_order)

        elif recommendation_type == "popular":
            recommendations = self.get_popular_recommendation(current_order=current_order)

        elif recommendation_type == "popular by category":
            recommendations = self.get_popular_recommendation(recommendation_classification['parameters'], current_order=current_order)

        else:
            recommendations = []

        # print(recommendation_classification)

        if not recommendations:
            return {"role": "assistant", "content": "I can't recommend any items, can I help you with anything else?"}

        # Respond to User
        recommendations_str = ", ".join(recommendations)

        system_prompt = f"""
        You are a helpful AI assistant for a coffee shop application which serves drinks and pastries.
        Your task is to recommend items to the user based on their input message. And respond in a friendly but concise way. And put it an unordered list with a very small description.

        I will provide what items you should recommend to the user based on their order in the user message.
        """

        prompt = f"""
        {messages[-1]['content']}

        STRICTLY Recommend The Following Items, DO NOT recommend anything else:
        {recommendations_str}
        """

        messages[-1]['content'] = prompt

        input_messages = [{"role": "system", "content": system_prompt}] +\
                            [{"role": message['role'], "content": message['content']} for message in messages[-3:]]

        response = get_response(self.client,self.model_name,input_messages)

        return self.postprocess(response, recommendation_type, recommendation_classification['parameters'])