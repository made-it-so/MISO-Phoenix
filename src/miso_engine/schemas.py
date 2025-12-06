from pydantic import BaseModel, Field
from typing import Dict, Any

class Action(BaseModel):
    """A validated schema for a single tool call."""
    tool_name: str = Field(..., description="The exact name of the tool to be used.")
    parameters: Dict[str, Any] = Field(..., description="The parameters for the tool call.")

class Plan(BaseModel):
    """A validated schema for the complete output from a specialist agent."""
    thought: str = Field(..., description="The reasoning behind the action.")
    action: Action = Field(..., description="The single, validated action to be taken.")
