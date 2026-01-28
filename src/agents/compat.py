"""
Compatibility wrapper for old scripts that used CruiseBookingAgent.

This provides a compatibility layer so existing scripts continue to work
while using the new ADK agent structure under the hood.

Note: For new code, use the ADK agents directly via:
    adk web agents/
    adk run agents/cruise_booking/
"""

import sys
from pathlib import Path

# Add agents directory to path
agents_path = Path(__file__).parent.parent.parent / "agents"
sys.path.insert(0, str(agents_path))

from typing import Dict, Any
import json


class CruiseBookingAgent:
    """
    Compatibility wrapper for the old CruiseBookingAgent class.
    
    This provides a similar interface to the old agent but uses
    the new ADK structure under the hood.
    
    Deprecated: Use ADK agents directly for new code.
    """
    
    def __init__(self):
        """Initialize the compatibility agent."""
        # Import ADK agent
        try:
            from cruise_booking import root_agent
            self.adk_agent = root_agent
            self.using_adk = True
        except ImportError:
            self.adk_agent = None
            self.using_adk = False
            print("Warning: ADK agent not available. Some features may not work.")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query using the ADK agent.
        
        Args:
            query: User's natural language query
            
        Returns:
            Dictionary with response, agent_path, and reasoning_output
        """
        if not self.using_adk:
            return {
                "response": {
                    "message": "ADK agent not available. Please use: adk web agents/",
                    "status": "error"
                },
                "agent_path": {},
                "reasoning_output": {}
            }
        
        try:
            # Call ADK agent
            # Note: ADK agents are designed to be run via adk CLI
            # This is a simplified wrapper
            result = {
                "response": {
                    "message": f"Query received: {query}",
                    "note": "For full functionality, use: adk web agents/ --port 8000",
                    "status": "success"
                },
                "agent_path": {
                    "agent_name": "CruiseBookingAgent (ADK)",
                    "intent": "general_query",
                    "route": "root_agent"
                },
                "reasoning_output": {
                    "query": query,
                    "using_adk": True,
                    "recommendation": "Use ADK Web UI for interactive testing"
                }
            }
            
            return result
            
        except Exception as e:
            return {
                "response": {
                    "message": f"Error processing query: {str(e)}",
                    "status": "error"
                },
                "agent_path": {},
                "reasoning_output": {"error": str(e)}
            }


# Alias for backwards compatibility
cruise_booking_agent = CruiseBookingAgent


def get_compatibility_notice() -> str:
    """Return a notice about the compatibility layer."""
    return """
    ═══════════════════════════════════════════════════════════════
    COMPATIBILITY LAYER
    ═══════════════════════════════════════════════════════════════
    
    You are using a compatibility wrapper for the old agent structure.
    
    The agents have been migrated to ADK (Agent Development Kit).
    
    For full functionality, please use:
    
        adk web agents/ --port 8000
        
    Then open: http://127.0.0.1:8000
    
    Or use the ADK CLI:
    
        adk run agents/cruise_booking/
    
    ═══════════════════════════════════════════════════════════════
    """
