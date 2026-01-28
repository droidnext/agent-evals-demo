#!/usr/bin/env python3
"""Test Phoenix tracing integration."""

import sys
import asyncio
from pathlib import Path

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

print("🧪 Testing Phoenix Tracing Integration\n")

# Check configuration
from cruise_booking import config

print("📋 Configuration:")
print(f"  Phoenix Enabled: {config.PHOENIX_ENABLED}")
print(f"  Phoenix Project: {config.PHOENIX_PROJECT_NAME}")
print(f"  Phoenix Endpoint: {config.PHOENIX_COLLECTOR_ENDPOINT}")
print(f"  API Key: {'SET ✅' if config.PHOENIX_API_KEY else 'NOT SET ❌'}\n")

if not config.PHOENIX_ENABLED:
    print("❌ Phoenix is not enabled!")
    print("\nTo enable Phoenix tracing:")
    print("1. Add PHOENIX_API_KEY to your .env file")
    print("2. Restart the ADK server")
    sys.exit(1)

print("✅ Phoenix tracing is configured!\n")

# Test with a simple query
print("🧪 Testing trace generation...\n")

async def test_trace():
    """Send a test query and generate trace."""
    try:
        from cruise_booking import root_agent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
        
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
        
        # Test query
        query = "Find a cruise from Miami"
        print(f"📝 Query: {query}")
        
        # Wrap query in Content
        content = types.Content(parts=[types.Part(text=query)])
        
        # Run agent (this should generate traces)
        response_parts = []
        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=content
        ):
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_parts.append(part.text)
        
        response = ''.join(response_parts)
        print(f"\n📤 Response: {response[:200]}...\n")
        
        print("✅ Query executed successfully!")
        print("\n📊 Check your traces at:")
        print(f"   {config.PHOENIX_COLLECTOR_ENDPOINT}")
        print(f"   Project: {config.PHOENIX_PROJECT_NAME}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run test
success = asyncio.run(test_trace())

if success:
    print("🎉 Phoenix tracing test completed!")
    print("\n💡 Tips:")
    print("  - Traces may take a few seconds to appear in Phoenix")
    print("  - Check the 'Traces' tab in the Phoenix UI")
    print("  - Look for spans from 'cruise_booking' project")
else:
    print("❌ Phoenix tracing test failed")
    sys.exit(1)
