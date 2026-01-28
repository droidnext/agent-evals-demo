"""Itinerary search sub-agent for cruise booking."""

from google.adk.agents.llm_agent import Agent

from src.models.structured_llm import ItineraryStructuredResponse

from ..config import get_model_instance
from ..prompt_loader import load_agent_instruction
from ..tools.data_search_tools import search_cruises, get_cruise_by_id

MODEL = get_model_instance()
INSTRUCTION = load_agent_instruction('itinerary_agent')

itinerary_agent = Agent(
    model=MODEL,
    name='ItinerarySearchAgent',
    instruction=INSTRUCTION,
    output_schema=ItineraryStructuredResponse,
    output_key='itinerary_structured_response',
    tools=[search_cruises, get_cruise_by_id],
)
