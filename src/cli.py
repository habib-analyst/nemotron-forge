"""CLI: python -m src.cli "task description" [--model ...] [--workdir ...]"""
import argparse
import sys
from .agent import run_task, DEFAULT_MODEL


def main() -> None:
    ap = argparse.ArgumentParser(description="Nemotron Forge — agentic coding engineer")
    ap.add_argument("task", help="Coding task in plain English")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--workdir", default="./forge-workspace")
    ap.add_argument("--max-iters", type=int, default=12)
    args = ap.parse_args()

    print(f"Forge starting | model={args.model} | workdir={args.workdir}\n")
    result = run_task(args.task, args.workdir, model=args.model,
                      max_iters=args.max_iters)
    print(f"\n=== {result['status'].upper()} after {result['iterations']} iterations ===")
    if result["status"] == "done":
        print(result["summary"])
    else:
        print("Hit iteration budget. Partial transcript kept in workdir.")
        sys.exit(1)


if __name__ == "__main__":
    main()
