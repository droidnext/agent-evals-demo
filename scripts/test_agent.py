#!/usr/bin/env python3
"""
Test script to run the Cruise Booking Agent with queries.

This script allows you to:
- Test the agent with predefined queries
- Run custom queries interactively
- See detailed execution paths
- Test intent detection

Usage:
    # Run predefined test queries
    python scripts/test_agent.py
    
    # Run a single custom query
    python scripts/test_agent.py --query "Find me a 7-day Caribbean cruise"
    
    # Interactive mode
    python scripts/test_agent.py --interactive
    
    # Run specific test case
    python scripts/test_agent.py --test-case booking_inquiry
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.compat import get_compatibility_notice

# Show compatibility notice
print(get_compatibility_notice())

import argparse
import json
from dotenv import load_dotenv

from src.agents.cruise_booking_agent import CruiseBookingAgent
from src.utils.logging_config import get_logger

# Load environment
load_dotenv()

logger = get_logger(__name__)


# Predefined test queries
TEST_QUERIES = {
    "cruise_search": "I want a 7-day cruise from Miami in June for two people under $3000, balcony preferred",
    "comparison": "Compare Caribbean cruises versus Mediterranean cruises",
    "booking_inquiry": "How do I book a cruise and what payment options are available?",
    "policy_inquiry": "What's the cancellation policy for cruises?",
    "amenity_search": "Show me romantic cruises with spa and fine dining",
    "family_cruise": "Find family-friendly cruises with kids programs",
    "budget_search": "What cruises are available under $2000 per person?",
    "destination": "Show me Alaska cruise itineraries in July",
}


def print_result(query: str, result: dict):
    """Print query result in a formatted way."""
    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)
    
    # Intent and confidence
    reasoning = result.get("reasoning_output", {})
    print(f"\n📍 Intent: {reasoning.get('intent', 'unknown')}")
    print(f"🎯 Task Type: {reasoning.get('task_type', 'unknown')}")
    print(f"🤖 Required Agents: {', '.join(reasoning.get('required_agents', []))}")
    print(f"📋 Execution Plan: {' → '.join(reasoning.get('execution_plan', []))}")
    
    # Constraints
    constraints = reasoning.get('constraints', {})
    if constraints:
        print(f"\n🔍 Extracted Constraints:")
        for key, value in constraints.items():
            if value is not None:
                print(f"   {key}: {value}")
    
    # Response
    response = result.get("response", {})
    options = response.get("options", [])
    print(f"\n✨ Results: {len(options)} options found")
    
    if options:
        print("\nTop 3 Options:")
        for i, option in enumerate(options[:3], 1):
            print(f"\n  {i}. {option.get('name', 'Unknown')}")
            if 'departure_port' in option:
                print(f"     From: {option['departure_port']}")
            if 'duration' in option:
                print(f"     Duration: {option['duration']} days")
            if 'price' in option:
                print(f"     Price: ${option['price']}")
    
    # Agent path
    agent_path = result.get("agent_path", {})
    print(f"\n⏱️  Execution Time: {agent_path.get('execution_time_ms', 0):.2f}ms")
    print(f"📊 Agents Used: {len(agent_path.get('logs', []))} events logged")


def run_predefined_tests():
    """Run all predefined test queries."""
    print("=" * 80)
    print("RUNNING PREDEFINED TEST QUERIES")
    print("=" * 80)
    
    agent = CruiseBookingAgent()
    
    for test_name, query in TEST_QUERIES.items():
        print(f"\n\n🧪 Test: {test_name}")
        print("-" * 80)
        
        try:
            result = agent.process_query(query)
            print_result(query, result)
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✓ ALL TESTS COMPLETE")
    print("=" * 80)


def run_single_query(query: str):
    """Run a single query."""
    print("=" * 80)
    print("RUNNING SINGLE QUERY")
    print("=" * 80)
    
    agent = CruiseBookingAgent()
    
    try:
        result = agent.process_query(query)
        print_result(query, result)
        return 0
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_interactive():
    """Run in interactive mode."""
    print("=" * 80)
    print("INTERACTIVE MODE")
    print("=" * 80)
    print("\nEnter queries to test the agent (type 'quit' or 'exit' to stop)")
    print("Type 'help' to see example queries")
    print()
    
    agent = CruiseBookingAgent()
    
    while True:
        try:
            query = input("🔍 Query: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if query.lower() == 'help':
                print("\nExample queries:")
                for name, example in TEST_QUERIES.items():
                    print(f"  • {example}")
                print()
                continue
            
            result = agent.process_query(query)
            print_result(query, result)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")


def run_test_case(test_case: str):
    """Run a specific test case."""
    if test_case not in TEST_QUERIES:
        print(f"✗ Unknown test case: {test_case}")
        print(f"\nAvailable test cases:")
        for name in TEST_QUERIES.keys():
            print(f"  • {name}")
        return 1
    
    query = TEST_QUERIES[test_case]
    return run_single_query(query)


def main():
    parser = argparse.ArgumentParser(description="Test Cruise Booking Agent with queries")
    parser.add_argument(
        "--query",
        help="Run a single custom query"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--test-case",
        choices=list(TEST_QUERIES.keys()),
        help="Run a specific test case"
    )
    parser.add_argument(
        "--list-tests",
        action="store_true",
        help="List all available test cases"
    )
    
    args = parser.parse_args()
    
    # List tests
    if args.list_tests:
        print("Available test cases:")
        for name, query in TEST_QUERIES.items():
            print(f"\n  {name}:")
            print(f"    {query}")
        return 0
    
    # Interactive mode
    if args.interactive:
        run_interactive()
        return 0
    
    # Single query
    if args.query:
        return run_single_query(args.query)
    
    # Specific test case
    if args.test_case:
        return run_test_case(args.test_case)
    
    # Default: run all tests
    run_predefined_tests()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
