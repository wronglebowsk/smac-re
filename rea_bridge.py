#!/usr/bin/env python3
"""Persistent REA MCP server for the SMAC session.

`ensure()` starts a private `npx rea-agents@6.7.0 mcp` (stdio) bridged to TCP
127.0.0.1:<port recorded in ~/reverse/smac/.rea_port> if not already alive,
runs initialize + open_binary(terran.exe, ghidra).
`ask(name, args)` connects, sends tools/call, returns the parsed envelope.
The server (and its loaded Ghidra program) survives across script invocations.
"""
import json, os, socket, subprocess, sys, threading, time

PORT_FILE = '/home/n100/reverse/smac/.rea_port'
LOG = '/home/n100/reverse/smac/rea_bridge.log'
NPX = "/home/n100/.hermes/tools/npm-12.0.2-linux-x64/bin/npx"
NODE_BIN = "/home/n100/.hermes/tools/node-26.7.0-linux-x64/bin"
GHIDRA = "/home/n100/tools/ghidra_12.1.4_PUBLIC"
EXE = "/home/n100/reverse/smac/terran.exe"


def alive(port):
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=1.5)
        s.close()
        return True
    except OSError:
        return False


def _readline(f):
    while True:
        line = f.readline()
        if not line:
            raise RuntimeError("server stdout closed; see " + LOG)
        line = line.strip()
        if line:
            return line


class Client:
    def __init__(self, port, timeout=900):
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        self.f = self.sock.makefile("rw", buffering=1, encoding="utf-8")
        self.timeout = timeout

    def _send(self, obj):
        self.f.write(json.dumps(obj, separators=(",", ":")) + "\n")
        self.f.flush()

    def request(self, method, params, timeout=None):
        old = self.sock.gettimeout()
        self.sock.settimeout(timeout or self.timeout)
        try:
            self._rid = getattr(self, "_rid", 0) + 1
            self._send({"jsonrpc": "2.0", "id": self._rid,
                        "method": method, "params": params})
            while True:
                msg = json.loads(_readline(self.f))
                if msg.get("id") == self._rid and ("result" in msg or "error" in msg):
                    return msg
        finally:
            self.sock.settimeout(old)

    def tool(self, name, arguments, timeout=None):
        resp = self.request("tools/call", {"name": name, "arguments": arguments}, timeout)
        if "error" in resp:
            return {"_jsonrpc_error": resp["error"]}
        result = resp.get("result", {})
        texts = [c.get("text", "") for c in result.get("content", []) if c.get("type") == "text"]
        blob = "\n".join(texts)
        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            return {"_raw_text": blob, "_isError": result.get("isError", False)}

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def ensure(open_it=True, timeout=890):
    port = None
    if os.path.exists(PORT_FILE):
        port = int(open(PORT_FILE).read().strip())
        if alive(port):
            return Client(port, timeout=timeout)
    port = 39711
    env = dict(os.environ)
    env["PATH"] = NODE_BIN + ":/usr/bin:/bin:" + env.get("PATH", "")
    env["GHIDRA_INSTALL_DIR"] = GHIDRA
    env["REA_GHIDRA_STARTUP_TIMEOUT_MS"] = "900000"
    env["REA_PWNTOOLS_PYTHON"] = "/home/n100/.hermes/venvs/rea-pwntools/bin/python"
    proc = subprocess.Popen(
        ["python3", "-c", BRIDGE_SRC, str(port)],
        stdout=subprocess.DEVNULL, stderr=open(LOG, "ab"),
        cwd="/home/n100/reverse/smac", env=env, start_new_session=True)
    t0 = time.time()
    while not alive(port):
        if time.time() - t0 > 60:
            raise RuntimeError("bridge did not come up; see " + LOG)
        time.sleep(0.5)
    open(PORT_FILE, "w").write(str(port))
    c = Client(port, timeout=timeout)
    c.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                             "clientInfo": {"name": "hermes-rea-bridge", "version": "1.0"}},
              timeout=120)
    c._send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    if open_it:
        r = c.tool("open_binary", {"path": EXE, "provider_id": "ghidra"}, timeout=timeout)
        print("open_binary:", json.dumps(r)[:300], file=sys.stderr)
    return c


BRIDGE_SRC = r'''
import json, socket, subprocess, sys, threading
port = int(sys.argv[1])
proc = subprocess.Popen(["npx","-y","rea-agents@6.7.0","mcp"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr, cwd="/home/n100/reverse/smac")
lock = threading.Lock()
conns = []
def pump():
    # forward server stdout lines to all connected clients
    while True:
        line = proc.stdout.readline()
        if not line: break
        with lock:
            for c in conns[:]:
                try: c.sendall(line)
                except OSError:
                    if c in conns: conns.remove(c)
threading.Thread(target=pump, daemon=True).start()
srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
srv.bind(("127.0.0.1", port)); srv.listen(8)
def handle(c):
    f = c.makefile("rw", buffering=1, encoding="utf-8")
    for line in f:
        try: proc.stdin.write(line); proc.stdin.flush()
        except Exception: break
    conns.remove(c) if c in conns else None
while True:
    c,_ = srv.accept(); conns.append(c)
    threading.Thread(target=handle, args=(c,), daemon=True).start()
'''

if __name__ == "__main__":
    c = ensure()
    print("port:", open(PORT_FILE).read().strip())
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        r = c.tool("binary_overview", {})
        print(json.dumps(r)[:800])
