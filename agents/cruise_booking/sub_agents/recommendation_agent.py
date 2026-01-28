"""Recommendation sub-agent for cruise booking."""

from google.adk.agents.llm_agent import Agent

from src.models.structured_llm import RecommendationStructuredResponse

from ..config import get_model_instance
from ..prompt_loader import load_agent_instruction
from ..tools.semantic_search_tools import semantic_search_cruises, find_similar_cruises
from ..tools.data_search_tools import search_cruises, get_all_cruises, get_data_stats

MODEL = get_model_instance()
INSTRUCTION = load_agent_instruction('recommendation_agent')

recommendation_agent = Agent(
    model=MODEL,
    name='RecommendationAgent',
    instruction=INSTRUCTION,
    output_schema=RecommendationStructuredResponse,
    output_key='recommendation_structured_response',
    tools=[
        semantic_search_cruises,
        find_similar_cruises,
        search_cruises,
        get_all_cruises,
        get_data_stats,
    ],
)
