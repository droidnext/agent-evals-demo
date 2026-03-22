#!/usr/bin/env python3
"""
Offline LLM-as-judge evaluator that reads captured OpenInference traces
from .traces_local/ and scores agent responses against scenario expectations.

Decouples evaluation from execution: run the agent once (with LOCAL_TRACE_ENABLED=true),
then judge as many times as you like without re-running the agent.

Spans are loaded into a pandas DataFrame (following Phoenix's json_lines_to_df pattern)
for structured querying — tool calls, agent routing, and system prompts are all accessible.

Usage:
    # Judge the most recent trace run against all scenarios
    python evals/tests/scenarios_llm_judge.py

    # Judge a specific trace run
    python evals/tests/scenarios_llm_judge.py --trace-dir .traces_local/20260321T142925Z

    # Filter to a specific scenario
    python evals/tests/scenarios_llm_judge.py --scenario "Search and Book"

    # Verbose output (show full responses)
    python evals/tests/scenarios_llm_judge.py --verbose
"""

from __future__ import annotations

import sys
import json
import asyncio
import argparse
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent
TRACES_DIR = PROJECT_ROOT / ".traces_local"
SCENARIOS_DIR = PROJECT_ROOT / "tests" / "scenarios"
REPORTS_DIR = Path(__file__).parent.parent / "reports"

ATTR_PREFIX = "attributes."


def find_latest_trace_dir(base: Path) -> Path | None:
    """Return the most recent trace run directory (alphabetical sort = chronological)."""
    dirs = sorted(
        (d for d in base.iterdir() if d.is_dir()),
        key=lambda p: p.name,
    )
    return dirs[-1] if dirs else None


# ---------------------------------------------------------------------------
# Span loading — DataFrame-based (follows Phoenix json_lines_to_df pattern)
# ---------------------------------------------------------------------------

def load_spans_df(trace_dir: Path) -> pd.DataFrame:
    """Load spans from a trace run's spans.jsonl into a flat DataFrame.

    Uses pd.json_normalize (same approach as Phoenix's json_lines_to_df) so
    every span attribute becomes a column like ``attributes.input.value``,
    ``attributes.openinference.span.kind``, etc.
    """
    spans_path = trace_dir / "spans.jsonl"
    data = []
    with open(spans_path) as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    if not data:
        return pd.DataFrame()
    return pd.concat(
        [pd.json_normalize(item, max_level=1) for item in data],
        ignore_index=True,
    )


def _attr(df: pd.DataFrame, col: str) -> pd.Series:
    """Safe accessor for an attributes column that may not exist."""
    full = f"{ATTR_PREFIX}{col}"
    if full in df.columns:
        return df[full]
    return pd.Series(dtype=object, index=df.index)


def _parse_user_input(input_json: str) -> str:
    """Extract the user's text from an invocation span's input.value JSON."""
    try:
        inp = json.loads(input_json)
        new_msg = inp.get("new_message", "")
        nm = json.loads(new_msg) if isinstance(new_msg, str) else new_msg
        parts = nm.get("parts", [])
        return parts[0].get("text", "") if parts else ""
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return ""


def _parse_agent_response(output_json: str) -> str:
    """Extract the agent's text from an invocation span's output.value JSON."""
    try:
        out = json.loads(output_json)
        resp_parts = out.get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in resp_parts if "text" in p)
    except (json.JSONDecodeError, KeyError, TypeError):
        return ""


def extract_tool_calls(df: pd.DataFrame, trace_id: str) -> list[str]:
    """Return a list of 'tool_name(args_summary)' strings for TOOL spans in a trace."""
    mask = (
        (df.get("context.trace_id") == trace_id)
        & (_attr(df, "openinference.span.kind") == "TOOL")
        & df["name"].str.startswith("execute_tool")
        & ~df["name"].str.contains("merged", na=False)
    )
    tools = df.loc[mask]
    calls = []
    for _, row in tools.iterrows():
        name = row.get(f"{ATTR_PREFIX}tool.name", row["name"])
        params = row.get(f"{ATTR_PREFIX}tool.parameters", "")
        if pd.notna(name):
            summary = str(name)
            if pd.notna(params) and params:
                try:
                    args = json.loads(params) if isinstance(params, str) else params
                    summary += f"({json.dumps(args, separators=(',', ':'))[:120]})"
                except (json.JSONDecodeError, TypeError):
                    pass
            calls.append(summary)
    return calls


def extract_turns(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Extract per-turn data from invocation root spans in the DataFrame.

    Each invocation root span (name starts with 'invocation', no parent)
    produces one turn dict with user_input, response, tool_calls, etc.
    """
    if df.empty:
        return []

    is_invocation = df["name"].str.startswith("invocation")
    is_root = df["parent_id"].isna()
    roots = df[is_invocation & is_root].sort_values("start_time")

    turns: list[dict[str, Any]] = []
    for _, row in roots.iterrows():
        input_val = row.get(f"{ATTR_PREFIX}input.value", "")
        output_val = row.get(f"{ATTR_PREFIX}output.value", "")
        user_text = _parse_user_input(input_val if pd.notna(input_val) else "")
        response = _parse_agent_response(output_val if pd.notna(output_val) else "")
        trace_id = row.get("context.trace_id", "")

        tool_calls = extract_tool_calls(df, trace_id) if trace_id else []

        if user_text:
            turns.append({
                "user_input": user_text,
                "response": response,
                "trace_id": trace_id,
                "session_id": row.get(f"{ATTR_PREFIX}session.id", ""),
                "start_time": row.get("start_time", ""),
                "tool_calls": tool_calls,
            })

    return turns


# ---------------------------------------------------------------------------
# Scenario loading & matching
# ---------------------------------------------------------------------------

def load_scenarios(
    filter_title: str | None = None,
) -> list[dict[str, Any]]:
    """Load scenario definitions with their expected turn descriptions."""
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


def match_turns_to_scenarios(
    trace_turns: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Match extracted trace turns to scenario turn definitions by user input text."""
    trace_lookup: dict[str, dict] = {}
    for t in trace_turns:
        key = t["user_input"].strip().lower()
        trace_lookup[key] = t

    matched = []
    for scenario in scenarios:
        for turn_def in scenario["turns"]:
            raw_input = turn_def["input"]
            expected_text = raw_input if isinstance(raw_input, str) else raw_input.get("text", "")
            key = expected_text.strip().lower()

            trace_turn = trace_lookup.get(key)
            if trace_turn:
                matched.append({
                    "scenario_title": scenario["title"],
                    "scenario_file": scenario["file"],
                    "turn_num": turn_def["turn"],
                    "user_input": trace_turn["user_input"],
                    "response": trace_turn["response"],
                    "expected": turn_def["expected"],
                    "trace_id": trace_turn["trace_id"],
                    "session_id": trace_turn["session_id"],
                    "tool_calls": trace_turn.get("tool_calls", []),
                })
            else:
                matched.append({
                    "scenario_title": scenario["title"],
                    "scenario_file": scenario["file"],
                    "turn_num": turn_def["turn"],
                    "user_input": expected_text,
                    "response": None,
                    "expected": turn_def["expected"],
                    "trace_id": None,
                    "session_id": None,
                    "tool_calls": [],
                })

    return matched


# ---------------------------------------------------------------------------
# LLM judge
# ---------------------------------------------------------------------------

async def _llm_judge(user_input: str, response: str, expected: str) -> dict:
    """Use an LLM to judge whether the agent response meets the expected behavior."""
    try:
        import litellm

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


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def _generate_reports(
    results: list[dict[str, Any]],
    run_meta: dict[str, Any],
    report_dir: Path,
) -> tuple[Path, Path]:
    """Write JSON and Markdown reports. Returns (json_path, md_path)."""
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = run_meta["timestamp"]
    slug = ts.replace(":", "").replace("-", "").replace("T", "_").split("+")[0]

    json_path = report_dir / f"judge_{slug}.json"
    with open(json_path, "w") as f:
        json.dump({"meta": run_meta, "results": results}, f, indent=2, default=str)

    md_path = report_dir / f"judge_{slug}.md"
    lines: list[str] = []

    judged = [r for r in results if r.get("judge")]
    passed_count = sum(1 for r in judged if r["judge"]["pass"])
    failed_count = len(judged) - passed_count
    missing = [r for r in results if r["response"] is None]

    lines.append("# Trace-Based Judge Report")
    lines.append("")
    lines.append(f"**Date:** {run_meta['timestamp']}  ")
    lines.append(f"**Trace dir:** `{run_meta.get('trace_dir', 'unknown')}`  ")
    lines.append(f"**Agent model:** {run_meta.get('agent_model', 'unknown')}  ")
    lines.append(f"**Judge model:** {run_meta.get('judge_model', 'unknown')}  ")
    lines.append(f"**Duration:** {run_meta.get('judge_duration_ms', 0):.0f} ms  ")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Turns judged | {len(judged)} |")
    lines.append(f"| Passed | {passed_count} |")
    lines.append(f"| Failed | {failed_count} |")
    if missing:
        lines.append(f"| Missing from traces | {len(missing)} |")
    if judged:
        lines.append(f"| Pass rate | {passed_count / len(judged) * 100:.0f}% |")
    lines.append("")

    lines.append("## Turn Results")
    lines.append("")
    lines.append("| Scenario | Turn | Input | Tools | Verdict | Reason |")
    lines.append("|----------|------|-------|-------|---------|--------|")
    for r in results:
        short_input = r["user_input"][:50].replace("|", "\\|")
        tools_str = ", ".join(t.split("(")[0] for t in r.get("tool_calls", []))[:40] or "—"
        if r["response"] is None:
            verdict = "MISS"
            reason = "Not found in traces"
        elif r.get("judge"):
            verdict = "PASS" if r["judge"]["pass"] else "FAIL"
            reason = r["judge"].get("reason", "").replace("|", "\\|")
            reason = (reason[:80] + "...") if len(reason) > 80 else reason
        else:
            verdict = "---"
            reason = ""
        lines.append(
            f"| {r['scenario_title']} | {r['turn_num']} | {short_input} | {tools_str} | {verdict} | {reason} |"
        )
    lines.append("")

    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    return json_path, md_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(
        description="Judge agent responses from captured traces",
    )
    parser.add_argument(
        "--trace-dir", type=str,
        help="Path to a specific trace run directory (default: latest in .traces_local/)",
    )
    parser.add_argument(
        "--scenario", type=str, help="Filter scenarios by title (substring match)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show full responses",
    )
    parser.add_argument(
        "--report-dir", type=str, default=str(REPORTS_DIR),
        help=f"Directory for reports (default: {REPORTS_DIR})",
    )
    parser.add_argument(
        "--no-report", action="store_true", help="Skip writing report files",
    )
    args = parser.parse_args()

    # Resolve trace directory
    if args.trace_dir:
        trace_dir = Path(args.trace_dir)
    else:
        trace_dir = find_latest_trace_dir(TRACES_DIR)

    if not trace_dir or not trace_dir.exists():
        print("No trace directory found. Run the agent with LOCAL_TRACE_ENABLED=true first.")
        return 1

    # Load metadata
    meta_path = trace_dir / "metadata.json"
    trace_meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    print(f"{'=' * 80}")
    print("TRACE-BASED JUDGE")
    print(f"{'=' * 80}")
    print(f"  Trace dir:   {trace_dir}")
    print(f"  Agent model: {trace_meta.get('model', 'unknown')}")
    print()

    # Load spans into DataFrame and extract turns
    df = load_spans_df(trace_dir)
    trace_turns = extract_turns(df)
    print(f"  Spans loaded:    {len(df)}")
    print(f"  Turns extracted: {len(trace_turns)}")

    # Load scenarios
    scenarios = load_scenarios(filter_title=args.scenario)
    if not scenarios:
        print("  No matching scenarios found.")
        return 1

    total_scenario_turns = sum(len(s["turns"]) for s in scenarios)
    print(f"  Scenario turns:  {total_scenario_turns}")
    print()

    # Match and judge
    matched = match_turns_to_scenarios(trace_turns, scenarios)

    judge_model = os.getenv("JUDGE_MODEL", os.getenv("LLM_MODEL", "gpt-4.1-mini"))
    print(f"  Judge model: {judge_model}")
    print()

    judge_start = time.time()
    for m in matched:
        print(f"--- {m['scenario_title']} / Turn {m['turn_num']} ---")
        print(f"  User: {m['user_input'][:80]}")

        if m["response"] is None:
            print("  MISSING — turn not found in traces")
            print()
            continue

        if m.get("tool_calls"):
            print(f"  Tools: {', '.join(t.split('(')[0] for t in m['tool_calls'])}")

        if args.verbose:
            display = m["response"] if len(m["response"]) <= 600 else m["response"][:600] + "..."
            print(f"  Agent: {display}")

        judge_result = await _llm_judge(m["user_input"], m["response"], m["expected"])
        m["judge"] = judge_result
        verdict = "PASS" if judge_result["pass"] else "FAIL"
        print(f"  Judge: {verdict} — {judge_result['reason']}")
        print()

    judge_duration_ms = (time.time() - judge_start) * 1000

    # Summary
    judged = [m for m in matched if m.get("judge")]
    passed = sum(1 for m in judged if m["judge"]["pass"])
    missing = sum(1 for m in matched if m["response"] is None)

    print(f"{'=' * 80}")
    print("JUDGE SUMMARY")
    print(f"{'=' * 80}")
    print(f"  Passed: {passed}/{len(judged)}")
    if missing:
        print(f"  Missing from traces: {missing}")
    print(f"  Judge duration: {judge_duration_ms:.0f}ms")
    print()

    # Reports
    if not args.no_report:
        run_meta = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_dir": str(trace_dir),
            "trace_run": trace_meta.get("run_timestamp", "unknown"),
            "agent_model": trace_meta.get("model", "unknown"),
            "judge_model": judge_model,
            "turns_judged": len(judged),
            "turns_passed": passed,
            "turns_failed": len(judged) - passed,
            "turns_missing": missing,
            "judge_duration_ms": judge_duration_ms,
        }
        report_dir = Path(args.report_dir)
        json_path, md_path = _generate_reports(matched, run_meta, report_dir)
        print(f"  Reports written:")
        print(f"    JSON: {json_path}")
        print(f"    Markdown: {md_path}")
        print()

    return 0 if passed == len(judged) and missing == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
