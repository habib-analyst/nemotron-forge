# ⚡ Nemotron Forge — Agentic Coding Engineer

**Give it a coding task in plain English. It plans, writes code, runs it,
reads the failures, fixes them, and hands you working, tested code.**

Built for the [Nebius × NVIDIA Global AI Hackathon](https://nebiusglobalaihackathon.devpost.com/)
— **Coding and Agentic Engineering** track. Powered by **NVIDIA Nemotron**
models served on **Nebius Token Factory**.

## Demo

```bash
pip install -r requirements.txt
python demo/demo.py
```

```
================================================================
  NEMOTRON FORGE — agentic coding engineer
  mode: SCRIPTED (deterministic replay)
  task: Write a Python function that finds duplicate files in a directory by content hash, with tests
================================================================

[01] PLAN  → implement dupfinder.py (size-grouping scan); write pytest suite…
[02] WRITE dupfinder.py (22 lines)
[03] WRITE test_dupfinder.py (40 lines)
[04] RUN   pytest… → 4 passed, 1 failed ✗

[05] PLAN  → fix: compare SHA-256 content hashes within each size group
[06] WRITE dupfinder.py (48 lines)
[07] RUN   pytest… → 5 passed ✓

[08] DONE  ✓

================================================================
  DONE in 8 iterations (17.3s)
  dupfinder.py finds duplicate files by content hash (size pre-grouping + SHA-256).
  5/5 pytest tests pass.
================================================================
```

Note the money shot at `[04]`→`[07]`: the agent's first attempt has a
subtle bug (size-only comparison), pytest catches it, the agent reflects,
fixes it with SHA-256 hashing, and goes green. That's the whole thesis —
**an engineer that tests its own work.**

Or try the web UI (live transcript streaming + generated-file viewer):

```bash
python web/server.py --port 8000
# open http://127.0.0.1:8000
```

## What it is

Nemotron Forge is a ReAct-style autonomous coding agent. You describe the
*what*; it figures out the *how*:

1. **Plans** — decomposes your task into concrete steps.
2. **Acts** — writes files and runs shell commands via a strict JSON tool protocol.
3. **Observes** — reads exit codes, test output, and tracebacks.
4. **Reflects** — revises the plan and patches the code when tests fail.
5. **Delivers** — working code, a test suite, and a summary of what was built.

Every run is sandboxed: path-jailed file writes, 60-second command
timeouts, and a bounded iteration budget. The full transcript is preserved
for audit.

## Architecture

```
  USER TASK ──▶  NEMOTRON (Nebius Token Factory)   ◀── observations
                    │  one JSON tool call / turn
                    ▼
              ┌─────────────┐      ┌──────────────┐
              │ TOOL DISPATCH│─────▶│   SANDBOX    │
              │ plan/write/  │      │ path-jailed  │
              │ read/run/done│◀─────│ workspace    │
              └─────────────┘ results └──────────────┘
```

See [`docs/architecture.md`](docs/architecture.md) for the full technical
writeup (tool protocol, sandboxing, failure modes).

## Why NVIDIA Nemotron on Nebius

An agentic loop lives or dies on the reasoning model's **tool-use
discipline**: valid JSON every single turn, reading tracebacks instead of
hallucinating success, revising plans instead of repeating failed actions.
NVIDIA Nemotron's instruction tuning excels at exactly this structured,
long-horizon reasoning.

Nebius Token Factory serves Nemotron on high-performance GPUs behind an
**OpenAI-compatible API** — so the agent gets low-latency reasoning turns
with zero vendor lock-in: the same client also talks to any
OpenAI-compatible endpoint via `OPENAI_BASE_URL` / `OPENAI_API_KEY`.

## Setup

**Requirements:** Python 3.10+.

```bash
git clone https://github.com/habib-analyst/nemotron-forge.git
cd nemotron-forge
pip install -r requirements.txt
```

**Run it live** (needs Nebius Token Factory credits):

```bash
export NEBIUS_API_KEY="your-token-factory-key"
python -m src.cli "write a python rate limiter with tests" \
  --model nvidia/Llama-3.1-Nemotron-70B-Instruct
```

**Run the deterministic demo** (no key needed — replays a real run
through the real sandbox, ideal for the video):

```bash
python demo/demo.py            # terminal demo
python demo/demo.py --live     # live model instead of scripted brain
python web/server.py           # web UI at http://127.0.0.1:8000
```

## Project structure

```
nemotron-forge/
├── src/
│   ├── model.py       # OpenAI-compatible client (Nebius primary), system prompt
│   ├── tools.py       # Sandbox: path-jailed file I/O + shell execution
│   ├── agent.py       # plan→act→observe→reflect loop (+ on_event stream hook)
│   ├── scripted.py    # deterministic demo brain (reproducible runs, no key)
│   └── cli.py         # terminal entry point
├── demo/
│   └── demo.py        # scripted end-to-end demo, video-friendly output
├── web/
│   ├── index.html     # demo UI: task box, live SSE transcript, file viewer
│   └── server.py      # stdlib-only server (no extra dependencies)
├── docs/
│   └── architecture.md# 1-page technical writeup
├── requirements.txt
└── LICENSE            # MIT
```

## Hackathon compliance

- **Runs on Nebius Token Factory** — primary (and default) model endpoint;
  any OpenAI-compatible base URL also works.
- **Uses NVIDIA open models** — `nvidia/Llama-3.1-Nemotron-70B-Instruct`
  (default; override with `FORGE_MODEL` or `--model`).
- **Track:** Coding and Agentic Engineering.
- **License:** MIT (OSI-approved) — see LICENSE.

## Roadmap

- Multi-file project scaffolding (not just single modules)
- Persistent memory across runs (project knowledge base)
- Parallel tool calls per turn
- Diff-based patching instead of full-file rewrites

## License

MIT — see [LICENSE](LICENSE).
