"""Scripted demo brain for Nemotron Forge.

Replays a realistic, deterministic agent run of the duplicate-file-finder
task through the REAL agent loop and REAL sandbox tools — only the model's
"thinking" is canned. This makes the demo reproducible for the hackathon
video and usable with zero API credits.
"""
import json

DUPFINDER_V1 = '''"""Find duplicate files in a directory."""
import os
from collections import defaultdict


def find_duplicates(root: str) -> list[list[str]]:
    """Return groups of duplicate file paths under root."""
    by_size: dict[int, list[str]] = defaultdict(list)
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                by_size[os.path.getsize(path)].append(path)
            except OSError:
                continue
    return [sorted(g) for g in by_size.values() if len(g) > 1]
'''

DUPFINDER_V2 = '''"""Find duplicate files in a directory by content hash."""
import hashlib
import os
from collections import defaultdict


def _sha256(path: str, chunk: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def find_duplicates(root: str) -> list[list[str]]:
    """Return groups of duplicate file paths under root."""
    if not os.path.isdir(root):
        return []
    by_size: dict[int, list[str]] = defaultdict(list)
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                by_size[os.path.getsize(path)].append(path)
            except OSError:
                continue
    duplicates = []
    for group in by_size.values():
        if len(group) < 2:
            continue
        by_hash: dict[str, list[str]] = defaultdict(list)
        for path in group:
            try:
                by_hash[_sha256(path)].append(path)
            except OSError:
                continue
        duplicates.extend(sorted(g) for g in by_hash.values() if len(g) > 1)
    return sorted(duplicates)
'''

TEST_DUPFINDER = '''import pytest
from dupfinder import find_duplicates


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "a.txt").write_text("hello world")
    (tmp_path / "b.txt").write_text("hello world")
    (tmp_path / "c.txt").write_text("HELLO WORLD")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "d.txt").write_text("hello world")
    return tmp_path


def test_finds_real_duplicates(tree):
    groups = find_duplicates(str(tree))
    flat = {p for g in groups for p in g}
    assert str(tree / "a.txt") in flat
    assert str(tree / "b.txt") in flat


def test_missing_dir_returns_empty():
    assert find_duplicates("/nonexistent-dir-xyz") == []
'''


def scripted_chat(python_exe: str = "python3"):
    seq = [
        {"tool": "plan", "steps": ["implement dupfinder.py", "write pytest suite", "run tests, fix failures"]},
        {"tool": "write_file", "path": "dupfinder.py", "content": DUPFINDER_V1},
        {"tool": "write_file", "path": "test_dupfinder.py", "content": TEST_DUPFINDER},
        {"tool": "run", "cmd": f"{python_exe} -m pytest test_dupfinder.py -q 2>&1 | tail -5"},
        {"tool": "plan", "steps": ["fix: compare SHA-256 content hashes within each size group"]},
        {"tool": "write_file", "path": "dupfinder.py", "content": DUPFINDER_V2},
        {"tool": "run", "cmd": f"{python_exe} -m pytest test_dupfinder.py -q 2>&1 | tail -3"},
        {"tool": "done", "summary": "dupfinder.py finds duplicate files by content hash. Tests pass."},
    ]
    calls = iter(json.dumps(c) for c in seq)
    def chat(client, model, messages):
        try:
            return next(calls)
        except StopIteration:
            return json.dumps({"tool": "done", "summary": "scripted sequence exhausted"})
    return chat


DEMO_TASK = (
    "Write a Python function that finds duplicate files in a directory "
    "by content hash, with tests"
)
