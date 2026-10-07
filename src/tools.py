"""Sandboxed tools: file writes and shell execution inside the workspace."""
import os
import subprocess
from pathlib import Path


class Sandbox:
    def __init__(self, root: str, timeout: int = 60):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout

    def _safe(self, path: str) -> Path:
        p = (self.root / path).resolve()
        if not str(p).startswith(str(self.root)):
            raise ValueError(f"Path escapes workspace: {path}")
        return p

    def write_file(self, path: str, content: str) -> str:
        p = self._safe(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Wrote {len(content)} chars to {path}"

    def read_file(self, path: str) -> str:
        p = self._safe(path)
        if not p.exists():
            return f"ERROR: {path} does not exist"
        text = p.read_text()
        return text[:6000] + ("...[truncated]" if len(text) > 6000 else "")

    def run(self, cmd: str) -> str:
        try:
            r = subprocess.run(
                cmd, shell=True, cwd=self.root, capture_output=True,
                text=True, timeout=self.timeout,
            )
            out = (r.stdout + r.stderr)[-4000:]
            return f"exit={r.returncode}\n{out}"
        except subprocess.TimeoutExpired:
            return f"ERROR: command timed out after {self.timeout}s"
        except Exception as e:  # noqa: BLE001
            return f"ERROR: {e}"
