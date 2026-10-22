#!/usr/bin/env python3
"""FIFO-driven persistent REA MCP server for the SMAC session.

Layout (all under ~/reverse/smac/.rea/):
  in.fifo  — write JSON-RPC lines here (one kept-open writer = `cat > in.fifo`
             background process feeds the server's stdin)
  out.txt  — server stdout; `ask()` parses new lines from a persisted offset
  server.pid / writer.pid / out.offset

Start with rea_fifo.start_server() from a `terminal(background=true)` wrapper:
  python3 rea_fifo.py start        # spawns writer + server, detached
Then any script: import rea_fifo as F; F.tool("xrefs", {...})
The server (and its loaded Ghidra program) survives across script invocations.
"""
import json, os, subprocess, sys, time

DIR = '/home/n100/reverse/smac/.rea'
FIFO = DIR + '/in.fifo'
OUT = DIR + '/out.txt'
ERR = DIR + '/err.txt'
OFFSET = DIR + '/out.offset'
NPX = "/home/n100/.hermes/tools/npm-12.0.2-linux-x64/bin/npx"
NODE_BIN = "/home/n100/.hermes/tools/node-26.7.0-linux-x64/bin"
GHIDRA = "/home/n100/tools/ghidra_12.1.4_PUBLIC"
EXE = "/home/n100/reverse/smac/terran.exe"
ENV = dict(os.environ,
           PATH=NODE_BIN + ":/usr/bin:/bin:" + os.environ.get("PATH", ""),
           GHIDRA_INSTALL_DIR=GHIDRA,
           REA_GHIDRA_STARTUP_TIMEOUT_MS="900000",
           REA_PWNTOOLS_PYTHON="/home/n100/.hermes/venvs/rea-pwntools/bin/python")

_rid = 0


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError, ValueError):
        return False


def _pid_alive(path):
    if not os.path.exists(path):
        return False
    try:
        return _alive(int(open(path).read()))
    except ValueError:
        return False


def start_writer():
    """One long-lived kept-open FIFO writer. O_WRONLY|O_NONBLOCK open succeeds
    with no reader attached, so this never deadlocks against the server's
    blocking O_RDONLY open; holding the fd keeps the server's stdin open."""
    wp = DIR + '/writer.pid'
    if _pid_alive(wp):
        return int(open(wp).read())
    subprocess.Popen(
        ["setsid", "python3", "-c",
         f"import os,time\n"
         f"_d=os.open({FIFO!r}, os.O_RDWR|os.O_NONBLOCK)\n"
         f"open({wp!r},'w').write(str(os.getpid()))\n"
         f"while True: time.sleep(3600)\n"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env=ENV, start_new_session=True)
    t0 = time.time()
    while not os.path.exists(wp) and time.time() - t0 < 15:
        time.sleep(0.2)
    return int(open(wp).read())


def start_server():
    os.makedirs(DIR, exist_ok=True)
    if os.path.exists(FIFO) and not (os.stat(FIFO).st_mode & 0o170000 == 0o020000):
        os.remove(FIFO)
    if not os.path.exists(FIFO):
        os.mkfifo(FIFO)
    start_writer()                      # writer first: unblocks the server's fifo open
    if _pid_alive(DIR + '/server.pid'):
        return int(open(DIR + '/server.pid').read())
    p = subprocess.Popen(
        ["setsid", "bash", "-c",
         f"{NPX} -y rea-agents@6.7.0 mcp < {FIFO} >> {OUT} 2>> {ERR} & echo $! > {DIR}/server.pid; wait"],
        cwd="/home/n100/reverse/smac", env=ENV,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    t0 = time.time()
    while not os.path.exists(DIR + '/server.pid') and time.time() - t0 < 20:
        time.sleep(0.3)
    print("server spawned")
    return int(open(DIR + '/server.pid').read())


def _next_rid():
    global _rid
    p = DIR + '/rid'
    last = int(open(p).read()) if os.path.exists(p) else 0
    _rid = last + 1
    open(p, 'w').write(str(_rid))
    return _rid


def _write(line):
    with open(FIFO, 'wb') as f:    # opens, writes, closes; kept-open writer keeps pipe alive
        f.write(line.encode() + b"\n")
        f.flush()


def initialize(timeout=120):
    rid = _next_rid()
    _write(json.dumps({"jsonrpc": "2.0", "id": rid, "method": "initialize",
                       "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                  "clientInfo": {"name": "hermes-rea-fifo", "version": "1"}}}))
    resp = await_id(rid, timeout)
    _write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}))
    return resp


def await_id(rid, timeout=900, poll=0.25):
    """Read OUT from persisted byte offset until a line with matching id appears."""
    off = int(open(OFFSET).read()) if os.path.exists(OFFSET) else 0
    deadline = time.time() + timeout
    buf = b""
    while True:
        with open(OUT, 'rb') as f:
            f.seek(off)
            chunk = f.read()
        if chunk:
            buf += chunk
            lines = buf.split(b"\n")
            buf = lines.pop()               # keep incomplete tail
            off += sum(len(l) + 1 for l in lines)
            open(OFFSET, 'w').write(str(off))
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line.decode('utf-8', 'replace'))
                except json.JSONDecodeError:
                    continue
                if msg.get("id") == rid and ("result" in msg or "error" in msg):
                    return msg
        if time.time() > deadline:
            raise TimeoutError(f"id {rid} not seen in {timeout}s")
        time.sleep(poll)


def tool(name, arguments, timeout=900):
    rid = _next_rid()
    _write(json.dumps({"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                       "params": {"name": name, "arguments": arguments}}))
    resp = await_id(rid, timeout)
    if "error" in resp:
        return {"_jsonrpc_error": resp["error"]}
    result = resp.get("result", {})
    texts = [c.get("text", "") for c in result.get("content", []) if c.get("type") == "text"]
    blob = "\n".join(texts)
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return {"_raw_text": blob, "_isError": result.get("isError", False)}


def request(method, params, timeout=120):
    rid = _next_rid()
    _write(json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params}))
    return await_id(rid, timeout)


def open_binary(timeout=880):
    return tool("open_binary", {"path": EXE, "provider_id": "ghidra"}, timeout=timeout)


if __name__ == "__main__":
    if sys.argv[1] == "start":
        start_server()
