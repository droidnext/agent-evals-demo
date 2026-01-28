"""Response models for agent outputs."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CruiseOption(BaseModel):
    """A single cruise option."""
    
    cruise_id: str
    ship_name: str
    departure_port: str
    departure_date: str
    duration: int
    ports_of_call: List[str]
    cabin_type: str
    price_per_person: float
    total_price: float
    availability: str  # "available", "limited", "sold_out"
    amenities: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "cruise_id": "CRUISE_001",
                "ship_name": "Ocean Explorer",
                "departure_port": "Miami",
                "departure_date": "2024-06-15",
                "duration": 7,
                "ports_of_call": ["Nassau", "Cozumel", "Key West"],
                "cabin_type": "Balcony",
                "price_per_person": 1200.0,
                "total_price": 2400.0,
                "availability": "available",
                "amenities": ["spa", "fine_dining", "pool"]
            }
        }


class AgentResponse(BaseModel):
    """Final response from the agent."""
    
    query: str
    intent: str
    cruise_options: List[CruiseOption] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list, description="Recommendation explanations")
    policies: Optional[Dict[str, Any]] = Field(None, description="Relevant policies and restrictions")
    pricing_summary: Optional[Dict[str, Any]] = Field(None, description="Pricing breakdown")
    message: str = Field(description="Human-readable response message")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "I want a 7-day cruise from Miami in June",
                "intent": "cruise_search",
                "cruise_options": [],
                "recommendations": [],
                "message": "I found 3 cruises matching your criteria..."
            }
        }
