"""Agent path tracking models for evaluation."""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Phase(str, Enum):
    """Agent execution phases."""
    REASONING = "reasoning"
    ROUTING = "routing"
    ACTION = "action"


class EventType(str, Enum):
    """Types of events in agent path."""
    CONSTRAINT_EXTRACTION = "constraint_extraction"
    INTENT_IDENTIFICATION = "intent_identification"
    EXECUTION_PLAN = "execution_plan"
    AGENT_INVOCATION = "agent_invocation"
    TOOL_CALL = "tool_call"
    DATA_RETRIEVAL = "data_retrieval"
    ERROR = "error"


class PathEvent(BaseModel):
    """A single event in the agent path."""
    
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    phase: Phase
    agent: str
    event_type: EventType
    data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-15T10:30:00Z",
                "phase": "reasoning",
                "agent": "CruiseBookingAgent",
                "event_type": "constraint_extraction",
                "data": {
                    "extracted_constraints": {
                        "departure_port": "Miami",
                        "duration": 7
                    }
                }
            }
        }


class AgentPath(BaseModel):
    """Complete agent execution path for evaluation."""
    
    query: str
    events: List[PathEvent] = Field(default_factory=list)
    reasoning_output: Optional[Dict[str, Any]] = Field(None)
    agents_invoked: List[str] = Field(default_factory=list)
    execution_time_ms: Optional[float] = Field(None)
    final_response: Optional[Dict[str, Any]] = Field(None)
    
    def add_event(self, phase: Phase, agent: str, event_type: EventType, data: Dict[str, Any] = None):
        """Add an event to the path."""
        event = PathEvent(
            phase=phase,
            agent=agent,
            event_type=event_type,
            data=data or {}
        )
        self.events.append(event)
        
        # Track agent invocations
        if event_type == EventType.AGENT_INVOCATION and agent not in self.agents_invoked:
            self.agents_invoked.append(agent)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "query": self.query,
            "events": [event.dict() for event in self.events],
            "reasoning_output": self.reasoning_output,
            "agents_invoked": self.agents_invoked,
            "execution_time_ms": self.execution_time_ms,
            "final_response": self.final_response
        }
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "7-day cruise from Miami in June",
                "events": [],
                "agents_invoked": ["ItinerarySearchAgent", "PricingAndAvailabilityAgent"]
            }
        }
