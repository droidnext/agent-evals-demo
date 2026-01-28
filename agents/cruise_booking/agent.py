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

# Root agent: own output_schema and output_key (ADK: per-agent structured output).
# With tools, ADK injects set_model_response; result stored in session state.
root_agent = Agent(
    model=MODEL,
    name='CruiseBookingAgent',
    instruction=INSTRUCTION,
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
