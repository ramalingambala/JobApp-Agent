#!/usr/bin/env python3
"""
Job Application Agent — CLI runner.

Usage:
  python main.py --url "https://linkedin.com/jobs/view/..."
  python main.py --search "Principal Engineer Agentic AI Bangalore"
  python main.py --refresh-profiles   # re-index profiles into Chroma
"""

import ssl_patch  # must be first — patches REQUESTS_CA_BUNDLE for corporate proxies
import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# LangSmith tracing — set LANGCHAIN_TRACING_V2=true in .env to enable
os.environ.setdefault("LANGCHAIN_TRACING_V2",
                      os.getenv("LANGCHAIN_TRACING_V2", "false"))
os.environ.setdefault("LANGCHAIN_PROJECT",     os.getenv(
    "LANGCHAIN_PROJECT", "job-application-agent"))


def run_agent(job_url: str = "", search_query: str = ""):
    from agents.graph import graph

    initial_state = {
        "job_url":      job_url,
        "search_query": search_query,
        "raw_jd":       "",
        "parsed_jd":    None,
        "ic_score":     None,
        "leadership_score": None,
        "best_profile": None,
        "strengths":    [],
        "gaps":         [],
        "ats_entry":    "",
        "messages":     [],
    }

    print("\n🚀 Running Job Application Agent...\n")
    print("=" * 60)

    final_state = None
    for step, state in graph.stream(initial_state, stream_mode="updates"):
        node_name = list(step.keys())[0] if isinstance(
            step, dict) else str(step)
        current = list(step.values())[0] if isinstance(step, dict) else {}

        # Print last message from each node
        msgs = current.get("messages", [])
        if msgs:
            print(f"  [{node_name}] {msgs[-1].content}")

        final_state = state

    if not final_state:
        print("❌ Agent returned no state.")
        return

    # Merge all state updates for final output
    merged = {**initial_state}
    for update in graph.stream(initial_state, stream_mode="values"):
        merged = update  # last value is the fully merged state

    print("\n" + "=" * 60)
    print("📊 SCORES")
    print("=" * 60)
    print(f"  IC Profile:         {merged.get('ic_score', '?')}/100")
    print(f"  Leadership Profile: {merged.get('leadership_score', '?')}/100")
    print(f"  Best Profile:       {merged.get('best_profile', '?')}")

    print("\n📋 GAPS")
    for gap in merged.get("gaps", []):
        print(f"  ❌ {gap}")

    print("\n💡 LEVERS")
    for lever in merged.get("levers", []):
        print(f"  ✅ {lever}")

    print("\n📝 ATS ENTRY")
    print(merged.get("ats_entry", ""))

    # Save outputs
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    company = merged.get("parsed_jd", {}).get(
        "company", "unknown").replace(" ", "_")
    title = merged.get("parsed_jd", {}).get(
        "title", "role").replace(" ", "_")[:30]
    slug = f"{company}_{title}"

    results_path = output_dir / f"results_{slug}.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({
            "title":            merged.get("parsed_jd", {}).get("title"),
            "company":          merged.get("parsed_jd", {}).get("company"),
            "ic_score":         merged.get("ic_score"),
            "leadership_score": merged.get("leadership_score"),
            "best_profile":     merged.get("best_profile"),
            "gaps":             merged.get("gaps"),
            "levers":           merged.get("levers"),
            "ats_entry":        merged.get("ats_entry"),
        }, f, indent=2)
    print(f"💾 Results saved:      {results_path}")


def main():
    parser = argparse.ArgumentParser(description="Job Application Agent")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--url",    type=str, help="Job posting URL")
    group.add_argument("--search", type=str,
                       help="Search query for job (e.g. 'Principal Engineer AI Bangalore')")
    parser.add_argument("--refresh-profiles", action="store_true",
                        help="Re-index profiles into Chroma and exit")

    args = parser.parse_args()

    if args.refresh_profiles:
        from tools.vector_store import refresh_profiles
        refresh_profiles()
        sys.exit(0)

    if not args.url and not args.search:
        parser.print_help()
        sys.exit(1)

    run_agent(
        job_url=args.url or "",
        search_query=args.search or "",
    )


if __name__ == "__main__":
    main()
