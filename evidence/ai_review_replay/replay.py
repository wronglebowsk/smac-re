#!/usr/bin/env python3
"""Review-replay experiment: can candidate reviewer models catch the 8 known
findings from #309/#311 when handed the PRE-FIX diffs? No answer leakage:
the prompt states repo conventions (as Greptile had AGENTS.md) and asks for
an adversarial review; the known-finding list is NOT in the prompt.

4 runs: {strata, qwen36} x {m317, m318}, parallel. Outputs -> scratch/review_replay/.
"""
import json
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = "/home/paul/reverse/smac"
OUT = os.path.join(ROOT, "scratch/review_replay")

PROMPT = """You are an adversarial code reviewer for a reverse-engineering repository (Sid Meier's Alpha Centauri: static analysis of terran.exe via an objdump disassembly cache + Ghidra batch exports).

Repository conventions (from AGENTS.md):
- Every milestone answers ONE question; claims in NAMED.md are marked VERIFIED (V) only when a shipped gate (an assertion in scripts/<id>*.py) reads the claimed fact from the bytes, with evidence cited as path:line.
- A mutation harness (scripts/<id>_mutate.py) must redden each gate by rewriting measured literals or real parsed instructions; a gate that stays green under its own mutation is decoration.
- The repo gate (scripts/gate.py) audits docs/evidence/harness, NOT the acceptance itself.

Review the pull-request diff below. Find real defects, prioritized:
- correctness bugs in the instrument's logic (traces, classifiers, parsers, argument decoding),
- VERIFIED claims that the cited gates do not actually read, or that cannot fail on a real input,
- measurements whose definition does not match what the prose claims,
- evidence/citation defects and hygiene hazards.

For each finding give: severity (P1 blocker / P2 should-fix), file:line, what is wrong, and why it matters. Be specific and skeptical; do not pad with style nits; do not flag claims that are properly gated. At most 10 findings, most important first.

=== PR DIFF ===
"""

MODELS = {
    "strata": {
        "url": "http://192.168.1.12:8080/v1/chat/completions",
        "body": {"model": "qwen3.8-flash-next-iq3_xxs", "max_tokens": 8192,
                 "chat_template_kwargs": {"enable_thinking": True, "reasoning_effort": "xhigh"}},
    },
    "qwen36": {
        "url": "http://192.168.1.213:8010/v1/chat/completions",
        "body": {"model": "Qwen3.6-35B-A3B-int4-ov", "max_tokens": 8192},
    },
}
CASES = {"m317": "m317_prefix.diff", "m318": "m318_prefix.diff"}


def run(name, case):
    diff = open(os.path.join(OUT, CASES[case])).read()
    cfg = MODELS[name]
    body = dict(cfg["body"])
    body["messages"] = [{"role": "user", "content": PROMPT + diff}]
    req = urllib.request.Request(cfg["url"], data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=540) as r:
            resp = json.loads(r.read().decode())
        dt = time.time() - t0
        msg = resp["choices"][0]["message"]
        content = msg.get("content") or ""
        reasoning = msg.get("reasoning_content") or ""
        usage = resp.get("usage", {})
        with open(os.path.join(OUT, "%s_%s.json" % (name, case)), "w") as f:
            json.dump(resp, f, indent=1)
        with open(os.path.join(OUT, "%s_%s.md" % (name, case)), "w") as f:
            f.write(content)
        return "%s/%s: OK %.0fs, %d chars content, %d chars reasoning, usage=%s" % (
            name, case, dt, len(content), len(reasoning), json.dumps(usage))
    except Exception as e:
        return "%s/%s: FAILED after %.0fs: %r" % (name, case, time.time() - t0, e)


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(run, n, c) for n in MODELS for c in CASES]
        for f in futs:
            print(f.result(), flush=True)
    print("REPLAY DONE")