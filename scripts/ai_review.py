#!/usr/bin/env python3
"""ai_review (s291): the SEMANTIC half of the review pipeline — a fresh-context
adversarial review on the fleet's primary local endpoint (Strata), replacing
Greptile while its credits are exhausted. Evidence base: docs/AI-REVIEW.md
(the 8-finding replay: Strata caught the algorithmic + coverage classes,
missed definition-mismatch — hence the explicit checklist below).

The reviewer is a RAW API call: no session history, no authorship context.
Endpoint resolves from $STRATA_URL or providers.qwen125b.base_url in
~/.hermes/config.yaml (no endpoint is committed — repo gate law).

    python3 scripts/ai_review.py <pr-number> [--dry-run]
    # posts findings as a PR comment (unless --dry-run), saves the raw
    # review under evidence/ai_review/, exit 0 = review produced.

Triage stays with the closing agent: read EVERY finding body, fix or dismiss
each in one reply comment, re-measure, then merge (same rule as Greptile).
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = "qwen3.8-flash-next-iq3_xxs"  # served alias on the primary endpoint

PROMPT = """You are an adversarial code reviewer for a reverse-engineering repository (Sid Meier's Alpha Centauri: static analysis of terran.exe via an objdump disassembly cache + Ghidra batch exports).

Repository conventions (from AGENTS.md):
- Every milestone answers ONE question; claims in NAMED.md are marked VERIFIED (V) only when a shipped gate (an assertion in scripts/<id>*.py) reads the claimed fact from the bytes, with evidence cited as path:line.
- A mutation harness (scripts/<id>_mutate.py) must redden each gate by rewriting measured literals or real parsed instructions; a gate that stays green under its own mutation is decoration. Every VERIFIED claim row must name the mutant that reddens it.
- The repo gate (scripts/gate.py) audits docs/evidence/harness, NOT the acceptance itself.

Review the pull-request diff below. Find real defects, prioritized:
- correctness bugs in the instrument's logic (traces, classifiers, parsers, argument decoding),
- VERIFIED claims that the cited gates do not actually read, or that cannot fail on a real input,
- measurements whose DEFINITION does not match the prose claim (wrong endpoint or window, source-only comparison where the claim is about the whole instruction, hidden caps),
- digests or hashes cited as verified but not computed and PRINTED by the instrument itself,
- evidence/citation defects (no path:line) and hygiene hazards.

For each finding give: severity (P1 blocker / P2 should-fix), file:line, what is wrong, and why it matters. Be specific and skeptical; do not pad with style nits or generic fragility complaints; do not flag claims that are properly gated. At most 10 findings, most important first. If the diff is docs-only movement of settled text, verify the movement is faithful and say so.

=== PR DIFF ===
"""


def endpoint():
    url = os.environ.get("STRATA_URL")
    if not url:
        cfg = open(os.path.expanduser("~/.hermes/config.yaml")).read()
        m = re.search(r"^  qwen125b:\n((?:    .*\n|\n)*)", cfg, re.M)
        if m:
            b = re.search(r'base_url:\s*["\']?([^"\'\n]+)', m.group(1))
            if b:
                url = b.group(1).strip()
    if not url:
        sys.exit("no endpoint: set STRATA_URL or providers.qwen125b.base_url")
    url = url.rstrip("/")
    if url.endswith("/v1"):
        return url + "/chat/completions"
    return url + "/v1/chat/completions"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pr", type=int)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    diff = subprocess.run(["gh", "pr", "diff", str(args.pr)], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout
    body = {"model": MODEL, "max_tokens": 16384,
            "chat_template_kwargs": {"enable_thinking": True, "reasoning_effort": "xhigh"},
            "messages": [{"role": "user", "content": PROMPT + diff}]}
    req = urllib.request.Request(endpoint(), data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    print("reviewing PR #%d (%d diff bytes) on %s ..." % (args.pr, len(diff), MODEL), flush=True)
    with urllib.request.urlopen(req, timeout=900) as r:
        resp = json.loads(r.read().decode())
    content = resp["choices"][0]["message"].get("content") or ""
    if not content.strip():
        sys.exit("empty review content")
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = os.path.join(ROOT, "evidence/ai_review")
    os.makedirs(outdir, exist_ok=True)
    base = os.path.join(outdir, "pr%d_%s" % (args.pr, stamp))
    with open(base + ".json", "w") as f:
        json.dump(resp, f, indent=1)
    with open(base + ".md", "w") as f:
        f.write(content)
    print(content)
    print("\n[saved %s.md; usage=%s]" % (base, json.dumps(resp.get("usage", {}))))
    if not args.dry_run:
        header = ("**Local review** (Strata / %s, fresh context — replaces Greptile while credits "
                  "are exhausted; methodology: `docs/AI-REVIEW.md`). Triage rule unchanged: every "
                  "finding fixed or dismissed in one reply, re-measured at head, then merge.\n\n" % MODEL)
        cfile = os.path.join(ROOT, "scratch", "ai_review_pr%d_comment.md" % args.pr)
        with open(cfile, "w") as f:
            f.write(header + content)
        subprocess.run(["gh", "pr", "comment", str(args.pr), "--body-file", cfile],
                       cwd=ROOT, check=True)
        print("[posted to PR #%d]" % args.pr)
    return 0


if __name__ == "__main__":
    sys.exit(main())