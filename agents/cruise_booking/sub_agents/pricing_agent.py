"""Pricing and availability sub-agent for cruise booking."""

from google.adk.agents.llm_agent import Agent

from src.models.structured_llm import PricingStructuredResponse

from ..config import get_model_instance
from ..prompt_loader import load_agent_instruction
from ..tools.data_search_tools import (
    search_cruises,
    get_pricing_info,
    search_by_price_range,
    get_cruise_by_id,
)

MODEL = get_model_instance()
INSTRUCTION = load_agent_instruction('pricing_agent')

pricing_agent = Agent(
    model=MODEL,
    name='PricingAvailabilityAgent',
    instruction=INSTRUCTION,
    output_schema=PricingStructuredResponse,
    output_key='pricing_structured_response',
    tools=[search_cruises, get_pricing_info, search_by_price_range, get_cruise_by_id],
)
