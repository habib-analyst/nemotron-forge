# Nemotron Forge — Architecture

## Overview
Nemotron Forge is a ReAct-style agentic coding engineer. Given a task in plain English, it autonomously plans, writes code, executes it in a sandbox, observes the results, reflects on failures, and iterates until the task is complete.

## The loop: plan → act → observe → reflect
1. **Plan** — the model decomposes the task into steps.
2. **Act** — one tool call per turn, as strict JSON (plan, write_file, read_file, run, done).
3. **Observe** — tool results (exit codes, pytest output) are fed back verbatim.
4. **Reflect** — on failure the model reads the traceback, revises the plan, patches the code, re-runs.
Loop terminates on `done` or the 12-iteration budget.

## Sandboxing
- **Path jail** — file paths resolved and checked inside the workspace; `../` escapes rejected.
- **Command timeouts** — shell commands die after 60s.
- **Output caps** — stdout/stderr truncated to 4k chars.

## Why Nemotron on Nebius
The loop's quality is bounded by the reasoning model's multi-step tool-use discipline: valid JSON every turn, reading tracebacks, revising plans. NVIDIA Nemotron's instruction tuning is strong at structured, long-horizon reasoning. Nebius Token Factory serves Nemotron behind an OpenAI-compatible API — zero vendor lock-in.

## Components
- `src/model.py` — OpenAI-compatible client, system prompt
- `src/tools.py` — Sandbox: path-jailed file I/O + shell execution
- `src/agent.py` — the plan→act→observe→reflect loop
- `src/scripted.py` — deterministic demo brain (reproducible runs, no key)
- `src/cli.py` — terminal entry point
- `demo/demo.py` — scripted end-to-end demo
- `web/` — demo web UI with live SSE transcript
