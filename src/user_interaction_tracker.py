from typing import List, Dict

# Assuming interactions are stored in a simple in-memory list for prototyping.
interactions = []

def track_interaction(event_name: str, user_id: str, metadata: dict):
    # Implementation for tracking user interactions
    interaction = {'event_name': event_name, 'user_id': user_id, 'metadata': metadata}
    interactions.append(interaction)


def get_interactions(user_id: str) -> List[Dict]:
    # Implementation to retrieve user interactions
    return [interaction for interaction in interactions if interaction['user_id'] == user_id]
