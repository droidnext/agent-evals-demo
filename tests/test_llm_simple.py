#!/usr/bin/env python3
"""Ultra-simple test for LLM Agent - just one query."""

import sys
import asyncio
from pathlib import Path

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

print("🧪 Testing LLM Agent...\n")

# Import agent, runner, and session service
from cruise_booking import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Test query
query = "Hello! Can you help me find a cruise?"
print(f"📝 Query: {query}\n")

async def run_test():
    """Run the agent using ADK Runner."""
    try:
        # Create session service and runner
        session_service = InMemorySessionService()
        runner = Runner(
            app_name="cruise_booking",
            agent=root_agent,
            session_service=session_service
        )
        
        # Create session
        session = await session_service.create_session(
            app_name="cruise_booking",
            user_id="test_user"
        )
        
        response_parts = []
        print("📡 Calling agent...\n")
        
        # Wrap query in Content
        content = types.Content(parts=[types.Part(text=query)])
        
        # Run agent
        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=content
        ):
            # Print event type
            event_type = type(event).__name__
            print(f"  Event: {event_type}")
            
            # Extract text from content
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_parts.append(part.text)
                        print(f"    Text: {part.text[:100]}...")
        
        response = ''.join(response_parts)
        print(f"\n📤 Full Response:")
        print(f"{response}\n")
        print("✅ Test passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

# Run async test
asyncio.run(run_test())
