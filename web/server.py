#!/usr/bin/env python3
"""Nemotron Forge demo web server (stdlib only)."""
import argparse, json, os, queue, threading, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import agent
from src.scripted import scripted_chat, DEMO_TASK

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
RUNS_DIR = os.path.join(PROJECT_DIR, "runs")
os.makedirs(RUNS_DIR, exist_ok=True)
RUN_LOCK = threading.Lock()
RUNS: dict = {}

def venv_python() -> str:
    cand = os.path.join(PROJECT_DIR, ".venv", "bin", "python")
    return cand if os.path.exists(cand) else "python3"

def worker(run_id: str, task: str, mode: str):
    run = RUNS[run_id]
    q: queue.Queue = run["queue"]
    try:
        if mode == "scripted":
            old_chat, old_client = agent.chat, agent.get_client
            agent.chat = scripted_chat(venv_python())
            agent.get_client = lambda: None
            try:
                result = agent.run_task(task, run["workdir"], verbose=False,
                    on_event=lambda i, tool, call, obs: q.put({"type": "event", "iter": i, "tool": tool,
                        "call": {"path": call.get("path"), "cmd": call.get("cmd"), "steps": call.get("steps"), "summary": call.get("summary")},
                        "observation": (obs or "")[:1500]}))
            finally:
                agent.chat, agent.get_client = old_chat, old_client
        else:
            if not (os.environ.get("NEBIUS_API_KEY") or os.environ.get("OPENAI_API_KEY")):
                q.put({"type": "error", "message": "Live mode needs NEBIUS_API_KEY."})
                run["status"] = "error"
                return
            result = agent.run_task(task, run["workdir"], verbose=False,
                on_event=lambda i, tool, call, obs: q.put({"type": "event", "iter": i, "tool": tool, "call": {}, "observation": (obs or "")[:1500]}))
        run["status"] = result["status"]
        run["summary"] = result.get("summary", "")
        run["iterations"] = result["iterations"]
        q.put({"type": "result", "status": result["status"], "summary": result.get("summary", ""), "iterations": result["iterations"]})
    except Exception as e:
        q.put({"type": "error", "message": str(e)})
        run["status"] = "error"
    finally:
        q.put({"type": "finished"})
        RUN_LOCK.release()

class Handler(BaseHTTPRequestHandler):
    server_version = "ForgeDemo/1.0"
    def log_message(self, *args): pass
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/events":
            run_id = parse_qs(parsed.query).get("run_id", [None])[0]
            run = RUNS.get(run_id)
            if not run: return self._json({"error": "unknown run_id"}, 404)
            q = run["queue"]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                while True:
                    try: item = q.get(timeout=15)
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n"); self.wfile.flush(); continue
                    self.wfile.write(b"data: " + json.dumps(item).encode() + b"\n\n")
                    self.wfile.flush()
                    if item.get("type") == "finished": break
            except (BrokenPipeError, ConnectionResetError): pass
            return
        if parsed.path == "/api/files":
            run_id = parse_qs(parsed.query).get("run_id", [None])[0]
            run = RUNS.get(run_id)
            if not run: return self._json({"error": "unknown run"}, 404)
            files = []
            if os.path.isdir(run["workdir"]):
                for dp, dn, fn in os.walk(run["workdir"]):
                    dn[:] = [d for d in dn if d not in ("__pycache__", ".pytest_cache")]
                    for f in sorted(fn): files.append(os.path.relpath(os.path.join(dp, f), run["workdir"]))
            return self._json({"files": sorted(files), "status": run["status"], "summary": run["summary"]})
        path = os.path.join(BASE_DIR, "index.html")
        with open(path, "rb") as f: body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_POST(self):
        if urlparse(self.path).path != "/api/run": return self._json({"error": "not found"}, 404)
        if not RUN_LOCK.acquire(blocking=False): return self._json({"error": "a run is already in progress"}, 409)
        n = int(self.headers.get("Content-Length", 0))
        try: data = json.loads(self.rfile.read(n) or b"{}")
        except Exception: RUN_LOCK.release(); return self._json({"error": "invalid JSON"}, 400)
        task = (data.get("task") or DEMO_TASK).strip()
        mode = data.get("mode", "scripted")
        run_id = uuid.uuid4().hex[:8]
        workdir = os.path.join(RUNS_DIR, run_id)
        RUNS[run_id] = {"queue": queue.Queue(), "workdir": workdir, "status": "running", "summary": ""}
        threading.Thread(target=worker, args=(run_id, task, mode), daemon=True).start()
        return self._json({"run_id": run_id})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Forge demo UI: http://127.0.0.1:{args.port}")
    srv.serve_forever()

if __name__ == "__main__":
    main()
