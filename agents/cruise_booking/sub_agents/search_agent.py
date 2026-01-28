"""Semantic search sub-agent for cruise booking."""

from google.adk.agents.llm_agent import Agent

from src.models.structured_llm import SearchStructuredResponse

from ..config import get_model_instance
from ..prompt_loader import load_agent_instruction
from ..tools.semantic_search_tools import semantic_search_cruises, find_similar_cruises
from ..tools.data_search_tools import get_cruise_by_id

MODEL = get_model_instance()
INSTRUCTION = load_agent_instruction('search_agent')

search_agent = Agent(
    model=MODEL,
    name='SemanticSearchAgent',
    instruction=INSTRUCTION,
    output_schema=SearchStructuredResponse,
    output_key='search_structured_response',
    tools=[semantic_search_cruises, find_similar_cruises, get_cruise_by_id],
)
