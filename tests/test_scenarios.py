#!/usr/bin/env python3
"""
Multi-turn scenario test runner for ADK Cruise Booking Agent.

Loads scenario definitions from tests/scenarios/scenarios.yaml,
reads each referenced JSON file, and runs the multi-turn conversation
against the agent. Each turn's response is checked against the
`expected` description using an LLM-as-judge evaluation.

Usage:
    # Run all scenarios
    python tests/test_multi_turn.py

    # Run a specific scenario by title (substring match)
    python tests/test_multi_turn.py --scenario "Budget"

    # List available scenarios without running them
    python tests/test_multi_turn.py --list

    # Verbose output (full responses)
    python tests/test_multi_turn.py --verbose

    # Skip LLM judge (just run conversations, no pass/fail)
    python tests/test_multi_turn.py --no-judge
"""

import sys
import json
import asyncio
import argparse
import time
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
SCENARIOS_DIR = Path(__file__).parent / "scenarios"

sys.path.insert(0, str(PROJECT_ROOT / "agents"))


def load_scenarios(filter_title: str | None = None) -> list[dict[str, Any]]:
    """Load scenario index from scenarios.yaml and attach turn data from each JSON."""
    index_path = SCENARIOS_DIR / "scenarios.yaml"
    with open(index_path) as f:
        index = yaml.safe_load(f)

    scenarios = []
    for entry in index["scenarios"]:
        if filter_title and filter_title.lower() not in entry["title"].lower():
            continue

        json_path = SCENARIOS_DIR / entry["file"]
        with open(json_path) as f:
            turns = json.load(f)

        scenarios.append({
            "title": entry["title"],
            "description": entry["description"],
            "file": entry["file"],
            "turns": turns,
        })

    return scenarios


async def run_scenario(
    runner,
    session_service,
    scenario: dict[str, Any],
    verbose: bool = False,
    use_judge: bool = True,
) -> dict[str, Any]:
    """
    Run a single multi-turn scenario against the agent.

    Returns a result dict with per-turn outcomes and an overall pass/fail.
    """
    from google.genai import types

    title = scenario["title"]
    turns = scenario["turns"]

    print(f"\n{'=' * 80}")
    print(f"SCENARIO: {title}")
    print(f"  {scenario['description'].strip()}")
    print(f"  Turns: {len(turns)}")
    print(f"{'=' * 80}")

    session = await session_service.create_session(
        app_name="cruise_booking_multi_turn",
        user_id="multi_turn_test_user",
    )

    turn_results = []
    scenario_start = time.time()

    for turn in turns:
        turn_num = turn["turn"]
        raw_input = turn["input"]
        expected = turn["expected"]

        # input can be a plain string or a JSON object with at least a "text" field
        if isinstance(raw_input, str):
            user_text = raw_input
        else:
            user_text = raw_input["text"]

        print(f"\n--- Turn {turn_num} ---")
        print(f"  User: {user_text}")
        if isinstance(raw_input, dict):
            extras = {k: v for k, v in raw_input.items() if k not in ("role", "text")}
            if extras:
                print(f"  Input metadata: {json.dumps(extras, default=str)}")

        content = types.Content(parts=[types.Part(text=user_text)])

        start = time.time()
        response_parts = []
        events = []
        sub_agents_used: set[str] = set()

        async for event in runner.run_async(
            user_id="multi_turn_test_user",
            session_id=session.id,
            new_message=content,
        ):
            events.append(event)
            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_parts.append(part.text)
            if hasattr(event, "author") and event.author:
                if event.author != "CruiseBookingAgent":
                    sub_agents_used.add(event.author)

        elapsed_ms = (time.time() - start) * 1000
        response = "".join(response_parts)

        if verbose:
            display = response if len(response) <= 600 else response[:600] + "..."
            print(f"  Agent: {display}")
        else:
            print(f"  Agent: ({len(response)} chars, {elapsed_ms:.0f}ms)")

        if sub_agents_used:
            print(f"  Sub-agents: {', '.join(sorted(sub_agents_used))}")

        judge_result = None
        if use_judge and response:
            judge_result = await _llm_judge(user_text, response, expected)
            verdict = "PASS" if judge_result["pass"] else "FAIL"
            print(f"  Judge: {verdict} — {judge_result['reason']}")

        turn_results.append({
            "turn": turn_num,
            "input": raw_input,
            "expected": expected,
            "response": response,
            "response_length": len(response),
            "elapsed_ms": elapsed_ms,
            "events": len(events),
            "sub_agents": list(sub_agents_used),
            "judge": judge_result,
        })

    total_ms = (time.time() - scenario_start) * 1000
    passed = all(
        t["judge"]["pass"] for t in turn_results if t["judge"] is not None
    )
    judged = use_judge and any(t["judge"] is not None for t in turn_results)

    summary = {
        "title": title,
        "file": scenario["file"],
        "total_turns": len(turns),
        "total_ms": total_ms,
        "turn_results": turn_results,
        "passed": passed if judged else None,
    }

    status = "PASSED" if passed else "FAILED" if judged else "RAN (no judge)"
    print(f"\n>> Scenario result: {status} ({total_ms:.0f}ms total)")
    return summary


async def _llm_judge(user_input: str, response: str, expected: str) -> dict:
    """
    Use an LLM to judge whether the agent response meets the expected behavior.

    Uses litellm so it works with the same API keys / providers as the agent.
    Falls back to the model in LLM_MODEL env var, or gpt-4.1-mini by default.

    Returns {"pass": bool, "reason": str}.
    """
    try:
        import litellm
        import os

        judge_model = os.getenv("JUDGE_MODEL", os.getenv("LLM_MODEL", "gpt-4.1-mini"))

        prompt = f"""You are an evaluator for a cruise booking AI agent.

Given a user query, the agent's response, and a description of what was expected,
decide whether the response satisfies the expectation.

USER QUERY:
{user_input}

AGENT RESPONSE:
{response}

EXPECTED BEHAVIOR:
{expected}

Respond in exactly this JSON format (no markdown fences):
{{"pass": true/false, "reason": "<one sentence explanation>"}}"""

        result = await litellm.acompletion(
            model=judge_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=256,
        )
        text = result.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except Exception as e:
        return {"pass": False, "reason": f"Judge error: {e}"}


async def main():
    parser = argparse.ArgumentParser(
        description="Run multi-turn agent test scenarios",
    )
    parser.add_argument(
        "--scenario", type=str, help="Filter scenarios by title (substring match)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List scenarios without running them"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show full agent responses"
    )
    parser.add_argument(
        "--no-judge", action="store_true", help="Skip LLM-as-judge evaluation"
    )
    args = parser.parse_args()

    scenarios = load_scenarios(filter_title=args.scenario)

    if not scenarios:
        print("No matching scenarios found.")
        return 1

    if args.list:
        print("Available multi-turn scenarios:\n")
        for s in scenarios:
            print(f"  {s['title']}")
            print(f"    File:  {s['file']}")
            print(f"    Turns: {len(s['turns'])}")
            print(f"    {s['description'].strip()}\n")
        return 0

    from cruise_booking import root_agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    session_service = InMemorySessionService()
    runner = Runner(
        app_name="cruise_booking_multi_turn",
        agent=root_agent,
        session_service=session_service,
    )

    results = []
    for scenario in scenarios:
        result = await run_scenario(
            runner,
            session_service,
            scenario,
            verbose=args.verbose,
            use_judge=not args.no_judge,
        )
        results.append(result)

    print(f"\n{'=' * 80}")
    print("MULTI-TURN TEST SUMMARY")
    print(f"{'=' * 80}")

    for r in results:
        status = (
            "PASS" if r["passed"]
            else "FAIL" if r["passed"] is not None
            else "---"
        )
        print(f"  [{status}] {r['title']} ({r['total_turns']} turns, {r['total_ms']:.0f}ms)")

    total = len(results)
    judged = [r for r in results if r["passed"] is not None]
    passed = sum(1 for r in judged if r["passed"])

    if judged:
        print(f"\n  {passed}/{len(judged)} scenarios passed")

    print(f"  {total} scenario(s) executed\n")
    return 0 if all(r["passed"] for r in judged) else 1


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
