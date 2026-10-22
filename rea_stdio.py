"""Minimal MCP stdio driver for the REA server (rea-agents 6.7.0).

Spawns `npx -y rea-agents@6.7.0 mcp` with GHIDRA_INSTALL_DIR exported and
drives JSON-RPC over newline-delimited stdio. Keeps ONE server process alive
so the Ghidra import happens once and later queries answer in ~0.1 s.

Usage (inside the Hermes execute_code kernel):
    import rea_stdio as R
    R.start()                      # spawn + initialize
    R.call("open_binary", {...})   # tools/call -> parsed envelope dict
    R.stop()
"""
import json, os, subprocess, sys, threading, time

REA_VERSION = "6.7.0"
NODE_BIN = "/home/n100/.hermes/tools/node-26.7.0-linux-x64/bin"
NPX = "/home/n100/.hermes/tools/npm-12.0.2-linux-x64/bin/npx"
GHIDRA = "/home/n100/tools/ghidra_12.1.4_PUBLIC"

_proc = None
_lock = threading.Lock()
_next_id = 0
_stderr_path = None


def start(log_path="/home/n100/reverse/smac/rea_stdio.log"):
    global _proc, _stderr_path
    if _proc and _proc.poll() is None:
        return True
    env = dict(os.environ)
    env["PATH"] = NODE_BIN + ":/usr/bin:/bin:" + env.get("PATH", "")
    env["GHIDRA_INSTALL_DIR"] = GHIDRA
    env["REA_GHIDRA_STARTUP_TIMEOUT_MS"] = "900000"
    env["REA_PWNTOOLS_PYTHON"] = "/home/n100/.hermes/venvs/rea-pwntools/bin/python"
    _stderr_path = log_path
    _proc = subprocess.Popen(
        [NPX, "-y", f"rea-agents@{REA_VERSION}", "mcp"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=open(log_path, "ab"), env=env, cwd="/home/n100/reverse/smac",
    )
    init = call("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "hermes-rea-stdio", "version": "1.0"},
    }, timeout=120)
    notify("notifications/initialized", {})
    server = init.get("result", {}).get("serverInfo", {})
    print("server:", server, file=sys.stderr)
    return True


def _send(obj):
    _proc.stdin.write((json.dumps(obj, separators=(",", ":")) + "\n").encode())
    _proc.stdin.flush()


def notify(method, params):
    with _lock:
        _send({"jsonrpc": "2.0", "method": method, "params": params})


def call(method, params, timeout=900):
    """JSON-RPC request; returns the full response dict (result or error)."""
    global _next_id
    if not _proc or _proc.poll() is not None:
        raise RuntimeError("rea server not running; call start()")
    with _lock:
        if _proc.poll() is not None:
            raise RuntimeError(f"rea server died; see {_stderr_path}")
        _next_id += 1
        rid = _next_id
        _send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        deadline = time.time() + timeout
        while True:
            remain = deadline - time.time()
            if remain <= 0:
                raise TimeoutError(f"id {rid} ({method}) exceeded {timeout}s")
            line = _proc.stdout.readline()
            if not line:
                raise RuntimeError(f"stdout closed while awaiting id {rid}; see {_stderr_path}")
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("id") == rid and ("result" in msg or "error" in msg):
                return msg
            # otherwise: notification (progress etc.) — skip


def call_tool(name, arguments, timeout=900, unwrap=True):
    """tools/call -> parsed payload. The server returns content[0].text as a
    JSON string (the fat envelope). unwrap=True parses and returns that dict."""
    resp = call("tools/call", {"name": name, "arguments": arguments}, timeout=timeout)
    if "error" in resp:
        return {"_jsonrpc_error": resp["error"]}
    result = resp.get("result", {})
    texts = [c.get("text", "") for c in result.get("content", []) if c.get("type") == "text"]
    blob = "\n".join(texts)
    if not unwrap:
        return result
    try:
        parsed = json.loads(blob)
    except json.JSONDecodeError:
        return {"_raw_text": blob, "_isError": result.get("isError", False)}
    return parsed


def raw_result(env):
    """Pull the actual payload out of REA's fat envelope (raw_result key)."""
    if isinstance(env, dict):
        if "raw_result" in env:
            return env["raw_result"]
        for k in ("result", "data", "outcome"):
            v = env.get(k)
            if isinstance(v, dict) and "raw_result" in v:
                return v["raw_result"]
    return env


def stop():
    global _proc
    if _proc and _proc.poll() is None:
        try:
            call("close_binary", {}, timeout=120)
        except Exception:
            pass
        _proc.terminate()
        try:
            _proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _proc.kill()
    _proc = None
