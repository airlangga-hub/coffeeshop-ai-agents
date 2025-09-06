from agents import GuardAgent, ClassifierAgent, AgentProtocol, DetailsAgent
import os

def main():
    pass

if __name__ == "__main__":
    # initialize agents
    guard_agent = GuardAgent()
    classifier_agent = ClassifierAgent()

    agent_dict: dict[str, AgentProtocol] = {
        "details_agent": DetailsAgent()
    }

    messages = []

    while True:
        os.system("clear")

        print("\n Print Messages........\n")

        for message in messages:
            print(f"{message['role'].capitalize()}: {message['content']}")

        # user input
        prompt = input("User: ")
        messages.append({"role": "user", "content": prompt})

        # guard agent
        guard_response = guard_agent.respond(messages)
        if guard_response['metadata']['decision'] == "not allowed":
            messages.append(guard_response)
            continue

        # classifier agent
        classifier_response = classifier_agent.respond(messages)
        if classifier_response['metadata']['decision'] == 'unknown':
            messages.append(classifier_response)
            continue
        else:
            chosen_agent = classifier_response["metadata"]['decision']

        # get chosen agent's response
        agent = agent_dict[chosen_agent]
        response = agent.respond(messages)

        messages.append(response)