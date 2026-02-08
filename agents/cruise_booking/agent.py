"""ADK-compatible Cruise Booking Agent (Root Agent)."""

from google.adk.agents.llm_agent import Agent

from .config import get_model_instance
from .prompt_loader import load_agent_instruction
from .sub_agents import (
    itinerary_agent,
    pricing_agent,
    search_agent,
    recommendation_agent,
)
from .tools.data_search_tools import get_data_stats
from src.models.structured_llm import RootStructuredResponse

MODEL = get_model_instance()
INSTRUCTION = load_agent_instruction('root_agent')

# Reinforce bounded behavior: use tools/sub-agents only when needed, then respond.
# RunConfig.max_llm_calls (passed at run time via Runner.run_async) enforces hard limits.
_instruction_suffix = """

After you have enough information from sub-agents or tools, produce your structured response. Do not call the same tool or sub-agent repeatedly for the same purpose. Prefer one round of delegation then respond."""
ROOT_INSTRUCTION = INSTRUCTION.rstrip() + _instruction_suffix

# Root agent: own output_schema and output_key (ADK: per-agent structured output).
# With tools, ADK injects set_model_response; result stored in session state.
root_agent = Agent(
    model=MODEL,
    name='CruiseBookingAgent',
    instruction=ROOT_INSTRUCTION,
    description='Main orchestrator for cruise booking; routes to sub-agents and returns structured responses.',
    output_schema=RootStructuredResponse,
    output_key='root_structured_response',
    sub_agents=[
        itinerary_agent,
        pricing_agent,
        search_agent,
        recommendation_agent,
    ],
    tools=[get_data_stats],
)


# This is the entry point for ADK
root = root_agent
