"""Model client: OpenAI-compatible API (Nebius Token Factory primary)."""
import os
from openai import OpenAI


def get_client() -> OpenAI:
    base_url = os.environ.get(
        "OPENAI_BASE_URL", "https://api.tokenfactory.nebius.com/v1"
    )
    api_key = os.environ.get("NEBIUS_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set NEBIUS_API_KEY (Nebius Token Factory) or OPENAI_API_KEY."
        )
    return OpenAI(base_url=base_url, api_key=api_key)


DEFAULT_MODEL = os.environ.get(
    "FORGE_MODEL", "nvidia/Llama-3.1-Nemotron-70B-Instruct"
)

SYSTEM_PROMPT = """You are Forge, an expert autonomous coding engineer powered by NVIDIA Nemotron.
You solve coding tasks by reasoning step by step and using tools.

Available tools (call exactly one per turn, as JSON):
- {"tool": "plan", "steps": ["step 1", ...]} — lay out or revise your plan
- {"tool": "write_file", "path": "relative/path.py", "content": "..."} — create/overwrite a file
- {"tool": "run", "cmd": "shell command"} — run a command in the workspace (use for pytest, python, etc.)
- {"tool": "read_file", "path": "relative/path.py"} — read a file back
- {"tool": "done", "summary": "..."} — task complete; summarize what was built and test results

Rules:
1. Always start with a plan.
2. Write code, then RUN it. Never claim tests pass without running them.
3. When a test fails, read the error, fix the code, re-run. Max 8 iterations.
4. Keep code clean, typed, and documented. Include a test file.
5. Reply with ONLY the JSON tool call each turn, no prose.
"""


def chat(client: OpenAI, model: str, messages: list) -> str:
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=0.2, max_tokens=4096
    )
    return resp.choices[0].message.content.strip()
