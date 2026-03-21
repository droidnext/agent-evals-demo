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
import os
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


def _generate_reports(
    results: list[dict[str, Any]],
    run_meta: dict[str, Any],
    report_dir: Path,
) -> tuple[Path, Path]:
    """Write JSON and Markdown reports for the test run. Returns (json_path, md_path)."""
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = run_meta["timestamp"]
    slug = ts.replace(":", "").replace("-", "").replace("T", "_").split("+")[0]

    # --- JSON report (full structured data) ---
    json_path = report_dir / f"report_{slug}.json"
    json_payload = {
        "meta": run_meta,
        "scenarios": results,
    }
    with open(json_path, "w") as f:
        json.dump(json_payload, f, indent=2, default=str)

    # --- Markdown report (human-readable) ---
    md_path = report_dir / f"report_{slug}.md"
    lines: list[str] = []

    total = len(results)
    judged = [r for r in results if r["passed"] is not None]
    passed_count = sum(1 for r in judged if r["passed"])
    failed_count = len(judged) - passed_count

    lines.append(f"# Scenario Test Report")
    lines.append("")
    lines.append(f"**Date:** {run_meta['timestamp']}  ")
    lines.append(f"**Model:** {run_meta.get('model', 'unknown')}  ")
    lines.append(f"**Judge model:** {run_meta.get('judge_model', 'unknown')}  ")
    lines.append(f"**Total duration:** {run_meta['total_duration_ms']:.0f} ms  ")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Scenarios run | {total} |")
    lines.append(f"| Scenarios passed | {passed_count} |")
    lines.append(f"| Scenarios failed | {failed_count} |")
    if judged:
        lines.append(f"| Pass rate | {passed_count / len(judged) * 100:.0f}% |")
    lines.append("")

    # Per-scenario detail
    lines.append("## Scenarios")
    lines.append("")
    for r in results:
        status_icon = {True: "PASS", False: "FAIL", None: "---"}[r["passed"]]
        lines.append(f"### [{status_icon}] {r['title']}")
        lines.append("")
        lines.append(f"**File:** `{r['file']}`  ")
        lines.append(f"**Turns:** {r['total_turns']}  ")
        lines.append(f"**Duration:** {r['total_ms']:.0f} ms  ")
        lines.append("")

        # Turn results table
        lines.append("| Turn | Input | Verdict | Reason | Time (ms) | Sub-agents |")
        lines.append("|------|-------|---------|--------|-----------|------------|")
        for t in r["turn_results"]:
            raw = t["input"]
            input_text = raw if isinstance(raw, str) else raw.get("text", str(raw))
            short_input = (input_text[:60] + "...") if len(input_text) > 60 else input_text
            short_input = short_input.replace("|", "\\|")

            if t["judge"]:
                verdict = "PASS" if t["judge"]["pass"] else "FAIL"
                reason = t["judge"].get("reason", "").replace("|", "\\|")
                short_reason = (reason[:80] + "...") if len(reason) > 80 else reason
            else:
                verdict = "---"
                short_reason = ""

            agents = ", ".join(t["sub_agents"]) if t["sub_agents"] else "—"
            lines.append(
                f"| {t['turn']} | {short_input} | {verdict} | {short_reason} "
                f"| {t['elapsed_ms']:.0f} | {agents} |"
            )
        lines.append("")

        # Failed turns detail
        failed_turns = [t for t in r["turn_results"] if t["judge"] and not t["judge"]["pass"]]
        if failed_turns:
            lines.append("<details>")
            lines.append("<summary>Failed turn details</summary>")
            lines.append("")
            for t in failed_turns:
                raw = t["input"]
                input_text = raw if isinstance(raw, str) else raw.get("text", str(raw))
                lines.append(f"**Turn {t['turn']}:** {input_text}")
                lines.append("")
                lines.append(f"*Expected:* {t['expected']}")
                lines.append("")
                resp_preview = t["response"][:400] + "..." if len(t["response"]) > 400 else t["response"]
                lines.append(f"*Response:* {resp_preview}")
                lines.append("")
                lines.append(f"*Judge:* {t['judge']['reason']}")
                lines.append("")
            lines.append("</details>")
            lines.append("")

    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    return json_path, md_path


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
    parser.add_argument(
        "--report-dir", type=str, default=str(REPORTS_DIR),
        help=f"Directory for JSON/Markdown reports (default: {REPORTS_DIR})"
    )
    parser.add_argument(
        "--no-report", action="store_true", help="Skip writing report files"
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

    run_start = time.time()

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

    run_end = time.time()
    total_duration_ms = (run_end - run_start) * 1000

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

    print(f"  {total} scenario(s) executed")
    print(f"  Total duration: {total_duration_ms:.0f}ms\n")

    # Generate reports
    if not args.no_report:
        judge_model = os.getenv("JUDGE_MODEL", os.getenv("LLM_MODEL", "gpt-4.1-mini"))
        run_meta = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": os.getenv("LLM_MODEL", "unknown"),
            "judge_model": judge_model,
            "scenarios_run": total,
            "scenarios_passed": passed,
            "scenarios_failed": len(judged) - passed,
            "total_duration_ms": total_duration_ms,
        }
        report_dir = Path(args.report_dir)
        json_path, md_path = _generate_reports(results, run_meta, report_dir)
        print(f"  Reports written:")
        print(f"    JSON: {json_path}")
        print(f"    Markdown: {md_path}\n")

    return 0 if all(r["passed"] for r in judged) else 1


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
