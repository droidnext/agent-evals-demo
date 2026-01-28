#!/usr/bin/env python3
"""
Test script for ADK Cruise Booking Agent.

This test suite validates the agent's functionality using the Google ADK framework.
Tests include query processing, sub-agent routing, tool usage, and response quality.

Usage:
    # Run all test queries
    python tests/test_agent_queries.py
    
    # Run single query
    python tests/test_agent_queries.py --query "Find a 7-day cruise from Miami"
    
    # Interactive mode
    python tests/test_agent_queries.py --interactive
    
    # Verbose output (show events)
    python tests/test_agent_queries.py --verbose
"""

import sys
import asyncio
from pathlib import Path

# Add agents directory to path for importing the agent
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "agents"))

import argparse
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Predefined test queries - updated for ADK architecture
TEST_QUERIES = [
    {
        "name": "Basic Search",
        "query": "I want a 7-day cruise from Miami in June under $3000",
        "description": "Tests basic itinerary search with constraints"
    },
    {
        "name": "Semantic Search",
        "query": "Find romantic cruises with spa and fine dining",
        "description": "Tests semantic search for amenities/features"
    },
    {
        "name": "Pricing Query",
        "query": "What are the prices for Alaska cruises in July?",
        "description": "Tests pricing information retrieval"
    },
    {
        "name": "Comparison Request",
        "query": "Compare Caribbean cruises versus Mediterranean cruises",
        "description": "Tests recommendation and comparison logic"
    },
    {
        "name": "Complex Multi-Part",
        "query": "Show me 10-day cruises from Miami under $5000 with balcony cabins",
        "description": "Tests multiple constraint handling"
    },
    {
        "name": "Family-Friendly Search",
        "query": "Find family-friendly cruises with kids programs and water slides",
        "description": "Tests amenity-based semantic search"
    },
    {
        "name": "Budget Search",
        "query": "What cruises are available under $2000 per person?",
        "description": "Tests price-based filtering"
    },
    {
        "name": "Data Statistics",
        "query": "What cruise data do you have available?",
        "description": "Tests root agent tools (data stats)"
    },
]


async def run_single_query(
    runner, 
    session_id: str,
    user_id: str,
    query: str, 
    show_details: bool = True,
    show_events: bool = False
) -> Dict[str, Any]:
    """
    Run a single query against the ADK agent.
    
    Args:
        runner: ADK Runner instance
        session_id: Session ID to use
        user_id: User ID for session
        query: Query string to test
        show_details: Whether to show detailed output
        show_events: Whether to show event stream
        
    Returns:
        Dict with success status, response, events, and metrics
    """
    from google.genai import types
    
    print(f"\n{'=' * 80}")
    print(f"Query: {query}")
    print('-' * 80)
    
    try:
        # Wrap query in Content
        content = types.Content(parts=[types.Part(text=query)])
        
        # Track metrics
        start_time = time.time()
        events = []
        response_parts = []
        tool_calls = []
        sub_agents_used = set()
        
        # Run the agent and collect events
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            events.append(event)
            
            if show_events:
                print(f"  📦 Event: {type(event).__name__}")
            
            # Collect response text
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_parts.append(part.text)
            
            # Track agent and tool usage
            if hasattr(event, 'author'):
                if event.author and event.author != 'CruiseBookingAgent':
                    sub_agents_used.add(event.author)
            
            # Track tool calls (if available in event)
            if hasattr(event, 'function_calls') and event.function_calls:
                for fc in event.function_calls:
                    tool_calls.append(fc.name if hasattr(fc, 'name') else str(fc))
        
        execution_time_ms = (time.time() - start_time) * 1000
        response = ''.join(response_parts)
        
        # Display results
        print(f"\n✅ Success")
        print(f"   Response length: {len(response)} chars")
        print(f"   Events received: {len(events)}")
        print(f"   Sub-agents used: {len(sub_agents_used)}")
        if sub_agents_used:
            print(f"   Agents: {', '.join(sorted(sub_agents_used))}")
        print(f"   Execution time: {execution_time_ms:.0f}ms")
        
        if show_details and response:
            print(f"\n📤 Response:")
            # Show first 500 chars
            if len(response) > 500:
                print(f"{response[:500]}...")
            else:
                print(response)
        
        return {
            'success': True,
            'query': query,
            'response': response,
            'events': events,
            'event_count': len(events),
            'sub_agents': list(sub_agents_used),
            'tool_calls': tool_calls,
            'execution_time_ms': execution_time_ms,
            'response_length': len(response)
        }
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        if show_details:
            traceback.print_exc()
        
        return {
            'success': False,
            'query': query,
            'error': str(e),
            'execution_time_ms': (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
        }


async def run_test_suite(show_details: bool = False, show_events: bool = False):
    """
    Run all predefined test queries against the ADK agent.
    
    Args:
        show_details: Whether to show detailed output for each test
        show_events: Whether to show event stream for each test
        
    Returns:
        Exit code (0 = all passed, 1 = some failed)
    """
    print("=" * 80)
    print("ADK AGENT QUERY TEST SUITE")
    print("=" * 80)
    print()
    
    # Import ADK components
    from cruise_booking import root_agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    
    print(f"Agent: {root_agent.name}")
    print(f"Model: {root_agent.model}")
    print(f"Sub-agents: {len(root_agent.sub_agents)}")
    print(f"Test queries: {len(TEST_QUERIES)}")
    print()
    
    # Create session service and runner
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="cruise_booking_test",
        agent=root_agent,
        session_service=session_service
    )
    
    user_id = "test_user"
    results = []
    
    # Create a session for all tests
    session = await session_service.create_session(
        app_name="cruise_booking_test",
        user_id=user_id
    )
    
    # Run tests
    for i, test in enumerate(TEST_QUERIES, 1):
        print(f"\n{'=' * 80}")
        print(f"Test {i}/{len(TEST_QUERIES)}: {test['name']}")
        print(f"Description: {test['description']}")
        print('=' * 80)
        
        result = await run_single_query(
            runner=runner,
            session_id=session.id,
            user_id=user_id,
            query=test['query'],
            show_details=show_details,
            show_events=show_events
        )
        
        results.append({**test, **result})
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print(f"\nTotal tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if passed > 0:
        # Calculate metrics
        avg_time = sum(r['execution_time_ms'] for r in results if r['success']) / passed
        total_events = sum(r.get('event_count', 0) for r in results if r['success'])
        avg_response_len = sum(r.get('response_length', 0) for r in results if r['success']) / passed
        
        print(f"\nPerformance Metrics:")
        print(f"  Average execution time: {avg_time:.0f}ms")
        print(f"  Total events: {total_events}")
        print(f"  Average response length: {avg_response_len:.0f} chars")
    
    # Show failed tests
    if failed > 0:
        print(f"\n❌ Failed Tests:")
        for r in results:
            if not r['success']:
                print(f"  • {r['name']}: {r.get('error', 'Unknown error')}")
    
    print()
    return 0 if failed == 0 else 1


async def interactive_mode(show_events: bool = False):
    """
    Interactive mode for testing queries.
    
    Args:
        show_events: Whether to show event stream for queries
        
    Returns:
        Exit code
    """
    print("=" * 80)
    print("INTERACTIVE ADK AGENT TESTER")
    print("=" * 80)
    print()
    print("Commands:")
    print("  • Type a query to test the agent")
    print("  • 'help' - Show example queries")
    print("  • 'quit', 'exit', 'q' - Exit interactive mode")
    print()
    
    # Import ADK components
    from cruise_booking import root_agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    
    print(f"Agent loaded: {root_agent.name}")
    print(f"Model: {root_agent.model}")
    print()
    
    # Create session service and runner
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="cruise_booking_interactive",
        agent=root_agent,
        session_service=session_service
    )
    
    user_id = "interactive_user"
    
    # Create a session for interactive mode
    session = await session_service.create_session(
        app_name="cruise_booking_interactive",
        user_id=user_id
    )
    
    while True:
        try:
            query = input("\n🔍 Query: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Exiting interactive mode...")
                break
            
            if query.lower() == 'help':
                print("\n📚 Example queries:")
                for test in TEST_QUERIES:
                    print(f"  • {test['query']}")
                continue
            
            await run_single_query(
                runner=runner,
                session_id=session.id,
                user_id=user_id,
                query=query,
                show_details=True,
                show_events=show_events
            )
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user")
            break
        except EOFError:
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    return 0


async def run_single_test(query: str, show_details: bool = True, show_events: bool = False):
    """
    Run a single query test.
    
    Args:
        query: Query string to test
        show_details: Whether to show detailed output
        show_events: Whether to show event stream
        
    Returns:
        Exit code
    """
    print("=" * 80)
    print("SINGLE QUERY TEST")
    print("=" * 80)
    print()
    
    # Import ADK components
    from cruise_booking import root_agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    
    print(f"Agent: {root_agent.name}")
    print(f"Model: {root_agent.model}")
    print()
    
    # Create session service and runner
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="cruise_booking_single",
        agent=root_agent,
        session_service=session_service
    )
    
    # Create session
    session = await session_service.create_session(
        app_name="cruise_booking_single",
        user_id="single_test_user"
    )
    
    result = await run_single_query(
        runner=runner,
        session_id=session.id,
        user_id="single_test_user",
        query=query,
        show_details=show_details,
        show_events=show_events
    )
    
    return 0 if result['success'] else 1


def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(
        description="Test ADK Cruise Booking Agent with queries",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Single query to test"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output (response text)"
    )
    parser.add_argument(
        "--show-events",
        action="store_true",
        help="Show event stream details"
    )
    parser.add_argument(
        "--list-tests",
        action="store_true",
        help="List all available test queries"
    )
    
    args = parser.parse_args()
    
    # List tests
    if args.list_tests:
        print("Available test queries:")
        print()
        for i, test in enumerate(TEST_QUERIES, 1):
            print(f"{i}. {test['name']}")
            print(f"   Query: {test['query']}")
            print(f"   Description: {test['description']}")
            print()
        return 0
    
    # Interactive mode
    if args.interactive:
        return asyncio.run(interactive_mode(show_events=args.show_events))
    
    # Single query mode
    if args.query:
        return asyncio.run(run_single_test(
            query=args.query,
            show_details=args.verbose,
            show_events=args.show_events
        ))
    
    # Default: run full test suite
    return asyncio.run(run_test_suite(
        show_details=args.verbose,
        show_events=args.show_events
    ))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
