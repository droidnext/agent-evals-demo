"""ADK-compatible Cruise Booking Agent (Root Agent)."""

from .tracing_util import initialize_tracing
initialize_tracing()

from google.adk.agents.llm_agent import Agent

from .config import get_model_instance
from .prompt_loader import load_agent_instruction
from .sub_agents import (
    itinerary_agent,
    pricing_agent,
    search_agent,
    recommendation_agent,
)
from .tools.data_search_tools import get_data_stats, escalate_to_human

MODEL = get_model_instance()
INSTRUCTION = load_agent_instruction('root_agent')

_instruction_suffix = """

After receiving data from sub-agents or tools, produce a clear, helpful text response
summarizing the results. Do not call the same sub-agent repeatedly for the same purpose.
One round of delegation then respond."""
ROOT_INSTRUCTION = INSTRUCTION.rstrip() + _instruction_suffix

# Root agent is a pure orchestrator — no output_schema so the model can't
# short-circuit with set_model_response before delegating. Sub-agents keep
# their own output_schemas for structured data.
root_agent = Agent(
    model=MODEL,
    name='CruiseBookingAgent',
    instruction=ROOT_INSTRUCTION,
    description='Main orchestrator for cruise booking; routes to sub-agents and returns structured responses.',
    sub_agents=[
        itinerary_agent,
        pricing_agent,
        search_agent,
        recommendation_agent,
    ],
    tools=[get_data_stats, escalate_to_human],
)


# This is the entry point for ADK
root = root_agent
