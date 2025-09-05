from agents import (GuardAgent)
import os

def main():
    pass

if __name__ == "__main__":
    guard_agent = GuardAgent()

    messages = []

    while True:
        os.system("clear")

        print("\n Print Messages........\n")

        for message in messages:
            print(f"{message['role'].capitalize()}: {message['content']}")

        prompt = input("User: ")

        messages.append({"role": "user", "content": prompt})

        guard_response = guard_agent.respond(messages)

        if guard_response['metadata']['decision'] == "not allowed":
            messages.append(guard_response)