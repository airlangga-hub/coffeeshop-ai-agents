from agents import (GuardAgent,
                    ClassifierAgent,
                    DetailsAgent,
                    OrderAgent,
                    RecommendationAgent,
                    AgentProtocol
                    )

class AgentController():
    def __init__(self):
        self.guard_agent = GuardAgent()
        self.classifier_agent = ClassifierAgent()
        self.recommendation_agent = RecommendationAgent()

        self.agent_dict: dict[str, AgentProtocol] = {
            "details_agent": DetailsAgent(),
            "order_agent": OrderAgent(self.recommendation_agent),
            "recommendation_agent": self.recommendation_agent
        }

    def respond(self, messages: list):
        
        # Get GuardAgent's response
        guard_agent_response = self.guard_agent.respond(messages)
        if guard_agent_response["metadata"]["decision"] == "not allowed":
            return guard_agent_response

        # Get ClassifierAgent's response
        classifier_response = self.classifier_agent.respond(messages)
        if classifier_response['metadata']['decision'] == 'unknown':
            return classifier_response
        else:
            chosen_agent = classifier_response["metadata"]['decision']

        # Get the chosen agent's response
        agent = self.agent_dict[chosen_agent]
        response = agent.respond(messages)

        return response