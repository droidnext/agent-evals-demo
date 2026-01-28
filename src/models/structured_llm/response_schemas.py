"""Per-agent structured response schemas for LLM calls.

Each ADK agent has its own output_schema. Used as output_schema on each
LlmAgent to enforce JSON-shaped responses and support needFollowUpInfo
when the agent requires additional user input.

See Google ADK docs: output_schema, output_key per agent.
"""

from typing import List

from pydantic import BaseModel, Field


class BaseStructuredLLMResponse(BaseModel):
    """Base schema shared by all agents.

    Set needFollowUpInfo=True when the agent needs additional information
    (e.g. dates, budget, preferences) before it can fully answer.
    """

    message: str = Field(
        description="Human-readable response. Summarize findings, answer the "
        "query, or explain what information is needed."
    )
    needFollowUpInfo: bool = Field(
        default=False,
        description="True when the agent needs more information from the user "
        "(e.g. travel dates, budget, preferences). Set to True if the query "
        "is vague or missing required details.",
    )
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Specific questions to ask when needFollowUpInfo is True. "
        "Empty if no follow-up needed.",
    )


class RootStructuredResponse(BaseStructuredLLMResponse):
    """Structured output for CruiseBookingAgent (root)."""

    pass


class ItineraryStructuredResponse(BaseStructuredLLMResponse):
    """Structured output for ItinerarySearchAgent."""

    pass


class SearchStructuredResponse(BaseStructuredLLMResponse):
    """Structured output for SemanticSearchAgent."""

    pass


class RecommendationStructuredResponse(BaseStructuredLLMResponse):
    """Structured output for RecommendationAgent."""

    pass


class PricingStructuredResponse(BaseStructuredLLMResponse):
    """Structured output for PricingAvailabilityAgent."""

    pass
