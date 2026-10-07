#!/usr/bin/env python3
"""Nemotron Forge — scripted end-to-end demo."""
import argparse
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import agent
from src.scripted import scripted_chat, DEMO_TASK

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKDIR = os.path.join(PROJECT_DIR, "demo-output")


def venv_python() -> str:
    cand = os.path.join(PROJECT_DIR, ".venv", "bin", "python")
    return cand if os.path.exists(cand) else "python3"


def pytest_line(obs: str) -> str:
    m = re.search(r"(\d+)\s+failed,\s*(\d+)\s+passed", obs)
    if m:
        return f"{m.group(2)} passed, {m.group(1)} failed"
    m = re.search(r"(\d+)\s+passed", obs)
    if m:
        return f"{m.group(1)} passed"
    m = re.search(r"exit=(\d+)", obs)
    return f"exit={m.group(1)}" if m else "done"


def main() -> None:
    ap = argparse.ArgumentParser(description="Nemotron Forge demo")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--workdir", default=WORKDIR)
    args = ap.parse_args()

    if os.path.exists(args.workdir):
        shutil.rmtree(args.workdir)

    mode = "LIVE (Nemotron via Nebius Token Factory)" if args.live else "SCRIPTED (deterministic replay)"
    print("=" * 64)
    print("  NEMOTRON FORGE — agentic coding engineer")
    print(f"  mode: {mode}")
    print(f"  task: {DEMO_TASK}")
    print("=" * 64)

    if not args.live:
        agent.chat = scripted_chat(venv_python())
        agent.get_client = lambda: None

    def show(i, tool, call, obs):
        if tool == "plan":
            steps = call.get("steps", [])
            print(f"\n[{i:02d}] PLAN  → " + "; ".join(steps))
        elif tool == "write_file":
            n = len(call.get("content", "").splitlines())
            print(f"[{i:02d}] WRITE {call.get('path')} ({n} lines)")
        elif tool == "run":
            verdict = pytest_line(obs or "")
            mark = "✗" if "failed" in verdict else "✓"
            print(f"[{i:02d}] RUN   {call.get('cmd', '')[:60]}… → {verdict} {mark}")
        elif tool == "done":
            print(f"\n[{i:02d}] DONE  ✓")
        time.sleep(0.4)

    t0 = time.time()
    result = agent.run_task(DEMO_TASK, args.workdir, verbose=False, on_event=show)
    dt = time.time() - t0

    print("\n" + "=" * 64)
    print(f"  {result['status'].upper()} in {result['iterations']} iterations ({dt:.1f}s)")
    print(f"  {result.get('summary', '')}")
    for cache in (".pytest_cache", "__pycache__"):
        shutil.rmtree(os.path.join(args.workdir, cache), ignore_errors=True)
    files = sorted(os.listdir(args.workdir))
    print(f"  workspace files: {', '.join(files)}")
    print("=" * 64)


if __name__ == "__main__":
    main()
