from pydantic import BaseModel, Field
from typing import List, Literal

class RoutingInstructions(BaseModel):
    """Instructions for Layers 2 and 3."""
    
    # Must be either 'flash' (cheap/fast) or 'pro' (expensive/reasoning)
    model_tier: Literal['flash', 'pro'] = Field(
        description="The recommended model tier for this task."
    )
    
    max_cost_usd: float = Field(
        description="The maximum cost ceiling (in USD) for this entire task execution."
    )
    
    priority: Literal['high', 'normal', 'low'] = Field(
        description="The urgency of the task."
    )

class CognitiveStep(BaseModel):
    """A single cognitive action required for the task."""
    step_name: Literal['READ', 'ANALYZE', 'IMPLEMENT', 'VERIFY'] = Field(
        description="The action type. IMPLEMENT must follow ANALYZE."
    )
    description: str = Field(
        description="A brief description of the goal for this step."
    )

class PersonaContract(BaseModel):
    """The final, complete Persona contract for the MISO stack."""
    task_intent: str = Field(
        description="A concise, high-level summary of the user's ultimate goal."
    )
    routing_instructions: RoutingInstructions
    dependency_graph: List[CognitiveStep] = Field(
        description="The sequence of cognitive steps required to complete the task."
    )
