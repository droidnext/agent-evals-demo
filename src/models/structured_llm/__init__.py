"""Per-agent structured LLM response schemas."""

from .response_schemas import (
    BaseStructuredLLMResponse,
    RootStructuredResponse,
    ItineraryStructuredResponse,
    SearchStructuredResponse,
    RecommendationStructuredResponse,
    PricingStructuredResponse,
)

# Alias for backwards compatibility
StructuredLLMResponse = RootStructuredResponse

__all__ = [
    "BaseStructuredLLMResponse",
    "RootStructuredResponse",
    "ItineraryStructuredResponse",
    "SearchStructuredResponse",
    "RecommendationStructuredResponse",
    "PricingStructuredResponse",
    "StructuredLLMResponse",
]
