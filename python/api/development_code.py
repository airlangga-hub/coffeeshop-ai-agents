from agents import GuardAgent, ClassifierAgent, AgentProtocol, DetailsAgent, RecommendationAgent, OrderAgent
import os

def main():

    # initialize agents
    guard_agent = GuardAgent()
    classifier_agent = ClassifierAgent()
    recommendation_agent = RecommendationAgent()

    agent_dict: dict[str, AgentProtocol] = {
        "details_agent": DetailsAgent(),
        "recommendation_agent": recommendation_agent,
        "order_agent": OrderAgent(recommendation_agent)
    }

    messages = []

    while True:
        # os.system("clear")

        print("\n==== CHAT HISTORY ====\n")

        for message in messages:
            print(f"{message['role'].capitalize()}: {message['content']}\n")

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
            # print(classifier_response)
            continue
        else:
            chosen_agent = classifier_response["metadata"]['decision']
            # print(classifier_response)

        # get chosen agent's response
        agent = agent_dict[chosen_agent]
        response = agent.respond(messages)
        # print(response)

        messages.append(response)

if __name__ == "__main__":
    main()