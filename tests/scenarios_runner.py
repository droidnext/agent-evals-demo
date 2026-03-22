#!/usr/bin/env python3
"""
Multi-turn scenario runner for ADK Cruise Booking Agent.

Loads scenario definitions from tests/scenarios/scenarios.yaml,
reads each referenced JSON file, and runs the multi-turn conversation
against the agent. Traces are captured to .traces_local/ (when enabled)
for offline evaluation via evals/tests/scenarios_llm_judge.py.

Usage:
    # Run all scenarios
    python tests/scenarios_runner.py

    # Run a specific scenario by title (substring match)
    python tests/scenarios_runner.py --scenario "Budget"

    # List available scenarios without running them
    python tests/scenarios_runner.py --list

    # Verbose output (full responses)
    python tests/scenarios_runner.py --verbose
"""

import os
import sys
import json
import asyncio
import argparse
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
SCENARIOS_DIR = Path(__file__).parent / "scenarios"
REPORTS_DIR = Path(__file__).parent / "reports"

sys.path.insert(0, str(PROJECT_ROOT / "agents"))


def load_scenarios(filter_title: str | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load scenario config from scenarios.yaml and attach turn data from each JSON.

    Returns (config, scenarios) where config contains top-level keys like
    app_name and user_id.
    """
    index_path = SCENARIOS_DIR / "scenarios.yaml"
    with open(index_path) as f:
        index = yaml.safe_load(f)

    config = {
        "app_name": index.get("app_name", "cruise_booking_multi_turn"),
        "user_id": index.get("user_id", "multi_turn_test_user"),
    }

    scenarios = []
    for entry in index["scenarios"]:
        if filter_title and filter_title.lower() not in entry["title"].lower():
            continue

        json_path = SCENARIOS_DIR / entry["file"]
        with open(json_path) as f:
            turns = json.load(f)

        sc = {
            "title": entry["title"],
            "description": entry["description"],
            "file": entry["file"],
            "turns": turns,
        }
        if "prepend_session_id" in entry:
            sc["prepend_session_id"] = entry["prepend_session_id"]
        scenarios.append(sc)

    return config, scenarios


async def run_scenario(
    runner,
    session_service,
    scenario: dict[str, Any],
    config: dict[str, Any],
    verbose: bool = False,
) -> dict[str, Any]:
    """Run a single multi-turn scenario against the agent.

    Returns a result dict with per-turn metrics (response length, timing, sub-agents).
    """
    from google.genai import types

    app_name = config["app_name"]
    user_id = config["user_id"]
    title = scenario["title"]
    turns = scenario["turns"]

    import uuid
    create_kwargs = {"app_name": app_name, "user_id": user_id}
    if "prepend_session_id" in scenario:
        create_kwargs["session_id"] = f"{scenario['prepend_session_id']}_{uuid.uuid4()}"
    session = await session_service.create_session(**create_kwargs)

    print(f"\n{'=' * 80}")
    print(f"SCENARIO: {title}")
    print(f"  {scenario['description'].strip()}")
    print(f"  Turns: {len(turns)}")
    print(f"  Session: {session.id}")
    print(f"{'=' * 80}")

    turn_results = []
    scenario_start = time.time()

    for turn in turns:
        turn_num = turn["turn"]
        raw_input = turn["input"]

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
            user_id=user_id,
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

        turn_results.append({
            "turn": turn_num,
            "input": raw_input,
            "response": response,
            "response_length": len(response),
            "elapsed_ms": elapsed_ms,
            "events": len(events),
            "sub_agents": list(sub_agents_used),
        })

    total_ms = (time.time() - scenario_start) * 1000

    summary = {
        "title": title,
        "file": scenario["file"],
        "session_id": session.id,
        "total_turns": len(turns),
        "total_ms": total_ms,
        "turn_results": turn_results,
    }

    print(f"\n>> Scenario completed ({total_ms:.0f}ms total)")
    return summary


def generate_reports(
    results: list[dict[str, Any]],
    total_duration_ms: float,
) -> Path:
    """Write execution reports (JSON + Markdown) to tests/reports/.

    Returns the path to the Markdown report.
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    model = os.getenv("LLM_MODEL", "unknown")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    total_turns = sum(r["total_turns"] for r in results)
    all_sub_agents: Counter[str] = Counter()
    for r in results:
        for t in r["turn_results"]:
            for sa in t["sub_agents"]:
                all_sub_agents[sa] += 1

    report_data = {
        "timestamp": ts,
        "model": model,
        "total_scenarios": len(results),
        "total_turns": total_turns,
        "total_duration_ms": round(total_duration_ms),
        "sub_agent_distribution": dict(all_sub_agents.most_common()),
        "scenarios": results,
    }

    json_path = REPORTS_DIR / f"exec_{ts}.json"
    json_path.write_text(json.dumps(report_data, indent=2, default=str), encoding="utf-8")

    lines = [
        f"# Execution Report — {ts}",
        "",
        f"**Model:** `{model}`  ",
        f"**Scenarios:** {len(results)}  ",
        f"**Total turns:** {total_turns}  ",
        f"**Duration:** {total_duration_ms / 1000:.1f}s  ",
        "",
    ]

    if all_sub_agents:
        lines.append("## Sub-Agent Distribution")
        lines.append("")
        lines.append("| Sub-Agent | Turns Used |")
        lines.append("|-----------|-----------|")
        for agent, count in all_sub_agents.most_common():
            lines.append(f"| {agent} | {count} |")
        lines.append("")

    lines.append("## Scenarios")
    lines.append("")

    for r in results:
        lines.append(f"### {r['title']}")
        lines.append("")
        lines.append(f"- **File:** `{r['file']}`")
        lines.append(f"- **Session:** `{r['session_id']}`")
        lines.append(f"- **Turns:** {r['total_turns']}")
        lines.append(f"- **Duration:** {r['total_ms'] / 1000:.1f}s")
        lines.append("")

        lines.append("| Turn | User Input | Response Length | Time | Sub-Agents |")
        lines.append("|------|-----------|----------------|------|------------|")

        for t in r["turn_results"]:
            user_text = t["input"] if isinstance(t["input"], str) else t["input"].get("text", "")
            truncated = user_text[:60] + "…" if len(user_text) > 60 else user_text
            sa = ", ".join(sorted(t["sub_agents"])) if t["sub_agents"] else "—"
            lines.append(
                f"| {t['turn']} | {truncated} | {t['response_length']} chars "
                f"| {t['elapsed_ms'] / 1000:.1f}s | {sa} |"
            )

        lines.append("")
        lines.append("<details><summary>Full responses</summary>")
        lines.append("")

        for t in r["turn_results"]:
            user_text = t["input"] if isinstance(t["input"], str) else t["input"].get("text", "")
            lines.append(f"**Turn {t['turn']} — User:** {user_text}")
            lines.append("")
            lines.append(f"**Agent** ({t['elapsed_ms']:.0f}ms):")
            lines.append("")
            lines.append(t["response"])
            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append("</details>")
        lines.append("")

    md_path = REPORTS_DIR / f"exec_{ts}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    return md_path


async def main():
    parser = argparse.ArgumentParser(
        description="Run multi-turn agent scenarios (YAML + JSON definitions)",
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
    args = parser.parse_args()

    config, scenarios = load_scenarios(filter_title=args.scenario)

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

    run_start = time.time()

    from cruise_booking.tracing_util import initialize_tracing
    initialize_tracing()

    from cruise_booking import root_agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    session_service = InMemorySessionService()
    runner = Runner(
        app_name=config["app_name"],
        agent=root_agent,
        session_service=session_service,
    )

    results = []
    for scenario in scenarios:
        result = await run_scenario(
            runner,
            session_service,
            scenario,
            config=config,
            verbose=args.verbose,
        )
        results.append(result)

    run_end = time.time()
    total_duration_ms = (run_end - run_start) * 1000

    report_path = generate_reports(results, total_duration_ms)

    print(f"\n{'=' * 80}")
    print("MULTI-TURN RUN SUMMARY")
    print(f"{'=' * 80}")

    for r in results:
        print(f"  {r['title']} ({r['total_turns']} turns, {r['total_ms']:.0f}ms)")

    print(f"\n  {len(results)} scenario(s) executed")
    print(f"  Total duration: {total_duration_ms:.0f}ms")
    print(f"  Report: {report_path.relative_to(PROJECT_ROOT)}")
    print(f"\n  Run evals/tests/scenarios_llm_judge.py to evaluate responses from captured traces.\n")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
