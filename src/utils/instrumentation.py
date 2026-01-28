"""Instrumentation for agent path tracking."""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from ..models.agent_path import AgentPath, Phase, EventType


class Instrumentation:
    """Handles instrumentation and logging of agent execution paths."""
    
    def __init__(self):
        self.path: Optional[AgentPath] = None
        self.start_time: Optional[datetime] = None
    
    def start_tracking(self, query: str):
        """Start tracking a new agent execution."""
        self.path = AgentPath(query=query)
        self.start_time = datetime.now()
    
    def log_reasoning(self, agent: str, event_type: EventType, data: Dict[str, Any]):
        """Log a reasoning phase event."""
        if self.path:
            self.path.add_event(Phase.REASONING, agent, event_type, data)
    
    def log_routing(self, agent: str, event_type: EventType, data: Dict[str, Any]):
        """Log a routing phase event."""
        if self.path:
            self.path.add_event(Phase.ROUTING, agent, event_type, data)
    
    def log_action(self, agent: str, event_type: EventType, data: Dict[str, Any]):
        """Log an action phase event."""
        if self.path:
            self.path.add_event(Phase.ACTION, agent, event_type, data)
    
    def set_reasoning_output(self, reasoning_output: Dict[str, Any]):
        """Set the reasoning phase output."""
        if self.path:
            self.path.reasoning_output = reasoning_output
    
    def finish_tracking(self, final_response: Optional[Dict[str, Any]] = None):
        """Finish tracking and calculate execution time."""
        if self.path and self.start_time:
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds() * 1000
            self.path.execution_time_ms = duration
            self.path.final_response = final_response
    
    def get_path(self) -> Optional[AgentPath]:
        """Get the current agent path."""
        return self.path
    
    def get_path_dict(self) -> Optional[Dict[str, Any]]:
        """Get the agent path as a dictionary."""
        if self.path:
            return self.path.to_dict()
        return None
    
    def save_to_file(self, filepath: str):
        """Save the agent path to a JSON file."""
        if self.path:
            with open(filepath, 'w') as f:
                json.dump(self.get_path_dict(), f, indent=2)
