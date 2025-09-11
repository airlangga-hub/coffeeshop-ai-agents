from os import getenv
from dotenv import load_dotenv
import requests
load_dotenv()

ACCESS_TOKEN = getenv("ACCESS_TOKEN")
RECIPIENT_WA_NO = getenv("RECIPIENT_WA_NO")
VERSION = getenv("VERSION")
PHONE_NUMBER_ID = getenv("PHONE_NUMBER_ID")

if not ACCESS_TOKEN or not RECIPIENT_WA_NO or not VERSION or not PHONE_NUMBER_ID:
    raise ValueError("One or more environment variables are not set.")

def send_whatsapp_message():
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization" : "Bearer " + ACCESS_TOKEN if ACCESS_TOKEN else "",
        "Content-Type" : "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": RECIPIENT_WA_NO,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {
                "code": "en_US"
            }
        }
    }

    response = requests.post(url, headers=headers, json=data)

    return response

response = send_whatsapp_message()
print("\nStatus Code:", f"{response.status_code}\n")
print("Response Body:", f"{response.json()}\n")