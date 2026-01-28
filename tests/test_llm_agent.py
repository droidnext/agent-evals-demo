#!/usr/bin/env python3
"""Simple test script for LLM Agent."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "agents"))

def test_agent_basic():
    """Test basic agent functionality."""
    import asyncio
    from google.genai import types
    
    async def run_tests():
        print("=" * 60)
        print("🧪 Testing LLM Agent")
        print("=" * 60)
        
        try:
            # Import the agent, runner, and session service
            print("\n1️⃣  Importing agent...")
            from cruise_booking import root_agent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            print(f"   ✅ Agent loaded: {root_agent.name}")
            print(f"   ✅ Model: {root_agent.model}")
            
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
            print(f"   ✅ Session created: {session.id}")
            
            # Test queries
            test_queries = [
                "Hello, can you help me find a cruise?",
                "Show me 7-day cruises from Miami",
                "What cruise destinations do you have?"
            ]
            
            for i, query in enumerate(test_queries, 1):
                print(f"\n{i + 1}️⃣  Testing query: '{query}'")
                print("-" * 60)
                
                try:
                    # Wrap query in Content
                    content = types.Content(parts=[types.Part(text=query)])
                    
                    # Run the agent with runner
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
                    
                    # Print response
                    print(f"\n📤 Response:")
                    print(f"{response}")
                    print("\n✅ Query successful!")
                    
                except Exception as e:
                    print(f"\n❌ Query failed: {e}")
                    import traceback
                    traceback.print_exc()
            
            print("\n" + "=" * 60)
            print("✅ All tests completed!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    asyncio.run(run_tests())


def test_agent_async():
    """Test async agent functionality with event streaming."""
    import asyncio
    from google.genai import types
    
    print("\n" + "=" * 60)
    print("🧪 Testing LLM Agent (Async/Event Streaming)")
    print("=" * 60)
    
    async def run_test():
        try:
            # Import the agent, runner, and session service
            print("\n1️⃣  Importing agent...")
            from cruise_booking import root_agent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            print(f"   ✅ Agent loaded: {root_agent.name}")
            
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
            query = "Find me a Caribbean cruise"
            print(f"\n2️⃣  Testing async query: '{query}'")
            print("-" * 60)
            
            # Wrap query in Content
            content = types.Content(parts=[types.Part(text=query)])
            
            # Run the agent asynchronously and collect events
            events = []
            async for event in runner.run_async(
                user_id="test_user",
                session_id=session.id,
                new_message=content
            ):
                events.append(event)
                print(f"\n📦 Event: {type(event).__name__}")
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(f"   Text: {part.text[:100]}...")
            
            print(f"\n✅ Received {len(events)} events")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Async test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(run_test())


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LLM Agent")
    parser.add_argument(
        "--mode",
        choices=["sync", "async", "both"],
        default="sync",
        help="Test mode: sync, async, or both"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Custom query to test"
    )
    
    args = parser.parse_args()
    
    # Custom query test
    if args.query:
        import asyncio
        from google.genai import types
        
        async def run_custom():
            print("=" * 60)
            print("🧪 Testing Custom Query")
            print("=" * 60)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
            from cruise_booking import root_agent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            
            print(f"\n📝 Query: {args.query}")
            print("-" * 60)
            
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
            
            # Wrap query in Content
            content = types.Content(parts=[types.Part(text=args.query)])
            
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
            print(f"\n📤 Response:")
            print(f"{response}")
            print("\n✅ Done!")
        
        asyncio.run(run_custom())
        sys.exit(0)
    
    # Run tests based on mode
    if args.mode in ["sync", "both"]:
        test_agent_basic()
    
    if args.mode in ["async", "both"]:
        test_agent_async()
