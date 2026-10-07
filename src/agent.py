"""Forge agent loop: plan -> act -> observe -> repeat until done."""
import json
import re
from .model import get_client, chat, SYSTEM_PROMPT, DEFAULT_MODEL
from .tools import Sandbox

MAX_ITERS = 12


def extract_tool_call(text: str) -> dict:
    """Pull the JSON tool call out of model output (tolerant of prose)."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"No JSON tool call found in: {text[:200]}")
    return json.loads(m.group(0))


def run_task(task: str, workdir: str, model: str = DEFAULT_MODEL,
             max_iters: int = MAX_ITERS, verbose: bool = True,
             on_event=None) -> dict:
    """Run the agent loop.

    on_event(iter_no, tool_name, call, observation) is an optional callback
    fired after each tool execution (observation=None for 'done'). Used by
    the web UI to stream the transcript.
    """
    client = get_client()
    sandbox = Sandbox(workdir)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"TASK: {task}\nWorkspace is empty. Begin with a plan."},
    ]
    transcript = []
    for i in range(max_iters):
        raw = chat(client, model, messages)
        messages.append({"role": "assistant", "content": raw})
        try:
            call = extract_tool_call(raw)
        except ValueError as e:
            obs = f"ERROR: {e}. Reply with ONLY a JSON tool call."
            messages.append({"role": "user", "content": obs})
            continue
        name = call.get("tool")
        if verbose:
            print(f"[{i+1:02d}] {name}: {str(call)[:120]}")
        transcript.append({"iter": i + 1, "call": call})
        if name == "done":
            if on_event:
                on_event(i + 1, name, call, None)
            return {"status": "done", "summary": call.get("summary", ""),
                    "iterations": i + 1, "transcript": transcript}
        elif name == "plan":
            obs = "Plan noted. Execute step 1: write the first file."
        elif name == "write_file":
            obs = sandbox.write_file(call["path"], call["content"])
        elif name == "read_file":
            obs = sandbox.read_file(call["path"])
        elif name == "run":
            obs = sandbox.run(call["cmd"])
        else:
            obs = f"ERROR: unknown tool '{name}'."
        transcript[-1]["observation"] = obs[:2000]
        if on_event:
            on_event(i + 1, name, call, obs[:2000])
        messages.append({"role": "user", "content": f"OBSERVATION:\n{obs}\nNext tool call (JSON only):"})
    return {"status": "max_iters", "iterations": max_iters, "transcript": transcript}
