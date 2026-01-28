"""Constraint extraction and intent models."""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Task type classification."""
    DISCOVERY = "discovery"
    COMPARISON = "comparison"
    BOOKING_PREPARATION = "booking_preparation"


class Intent(str, Enum):
    """Intent classification."""
    CRUISE_SEARCH = "cruise_search"
    CRUISE_COMPARISON = "cruise_comparison"
    BOOKING_INQUIRY = "booking_inquiry"
    POLICY_INQUIRY = "policy_inquiry"


class Constraints(BaseModel):
    """Extracted constraints from user query."""
    
    departure_port: Optional[str] = Field(None, description="Departure port (city name)")
    date_range: Optional[str] = Field(None, description="Date range (e.g., 'June', 'March-April')")
    duration: Optional[int] = Field(None, description="Cruise duration in days")
    budget: Optional[float] = Field(None, description="Maximum budget in USD")
    cabin_type: Optional[str] = Field(None, description="Cabin type (Inside, Oceanview, Balcony, Suite)")
    traveler_type: Optional[str] = Field(None, description="Traveler type (Couple, Family, Solo)")
    destination: Optional[str] = Field(None, description="Destination region (Caribbean, Mediterranean, etc.)")
    amenities: Optional[List[str]] = Field(None, description="Desired amenities (spa, kids_program, etc.)")
    atmosphere: Optional[str] = Field(None, description="Desired atmosphere (romantic, family-friendly, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "departure_port": "Miami",
                "date_range": "June",
                "duration": 7,
                "budget": 3000,
                "cabin_type": "Balcony",
                "traveler_type": "Couple"
            }
        }


class ReasoningOutput(BaseModel):
    """Output from the reasoning phase."""
    
    intent: Intent
    constraints: Constraints
    task_type: TaskType
    required_agents: List[str] = Field(description="List of sub-agents to invoke")
    execution_plan: List[str] = Field(description="Ordered list of execution steps")
    
    class Config:
        json_schema_extra = {
            "example": {
                "intent": "cruise_search",
                "constraints": {
                    "departure_port": "Miami",
                    "date_range": "June",
                    "duration": 7,
                    "budget": 3000,
                    "cabin_type": "Balcony",
                    "traveler_type": "Couple"
                },
                "task_type": "discovery",
                "required_agents": [
                    "ItinerarySearchAgent",
                    "PricingAndAvailabilityAgent",
                    "RecommendationAgent"
                ],
                "execution_plan": [
                    "search_itineraries",
                    "fetch_pricing",
                    "rank_options"
                ]
            }
        }
