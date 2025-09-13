# Project Overview
This is a **WhatsApp Chatbot** with 5 **AI Agents** running on the Backend:
* Guard Agent - filter irrelevant inputs
* Classifier Agent - route user input to the appropriate agent
* Details Agent - give store information using RAG
* Recommendation Agent - recommend items using:
  * Market Basket Analysis
  * Popularity
* Order Agent - handle user's order

This **WhatsApp Chatbot** serves as an AI Assistant for a Coffee Shop.

# Topology
Below is an overview of the whole system:

<img width="2827" height="1661" alt="topology" src="https://github.com/user-attachments/assets/5c5e8a71-07a2-472a-82b0-af13b1ca4ce0" />

# Pre-requisites
To run the project online, you need:
* Meta Developer Account: This is used to create webhook to listen to incoming messages.
* Ngrok: This is to expose the localhost to the internet.

To set up both Meta Developer Account and Ngrok, please refer to [this video](https://www.youtube.com/watch?v=3YPeh-3AFmM&t=1230s) and [this repo.](https://github.com/daveebbelaar/python-whatsapp-bot/tree/main)

# Running the FastAPI and Ngrok
First, cd into python/api directory
```bash
cd python/api
```
Second, run the local server
```bash
uvicorn main:app --reload --port 8000
```
Third, expose the localhost to ngrok
```bash
ngrok http 8000 --domain=<your free static domain from ngrok>.ngrok-free.app
```

# Attribution
This project is based on [Abdullah Tarek's](https://github.com/abdullahtarek) [repository.](https://github.com/abdullahtarek/coffee_shop_customer_service_chatbot/tree/main) \
For more details, go watch [his tutorial video.](https://www.youtube.com/watch?v=KyQKTJhSIak&t=4826s)
