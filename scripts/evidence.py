#!/usr/bin/env python3
"""Evidence lifecycle: read cheaply, keep citations honest, prune the working tree.

The repo is the archive: anything pruned is still in git history, and `.prune_log.jsonl`
records the commit that removed it. The working tree holds the hot set only.

    python3 scripts/evidence.py budget                  # sizes vs context/disk budgets
    python3 scripts/evidence.py show m50a_watch.log:185  # one cited window, not a 5k-line log
    python3 scripts/evidence.py digest evidence/m50a_watch.log
    python3 scripts/evidence.py prune --dry-run         # what would be removed
    python3 scripts/evidence.py prune --apply
    python3 scripts/evidence.py log                     # what has been pruned
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
DIGESTS = os.path.join(EVID, "digests")
PRUNE_LOG = os.path.join(EVID, ".prune_log.jsonl")

# Context budget: 262,144 tokens ≈ 1.05M chars at ~4 chars/token.
CHARS_PER_TOKEN = 4
CONTEXT_TOKENS = 262_144

DOC_BUDGETS = {          # warn, fail — BYTES (cmd_budget compares os.path.getsize, not characters)
    "NEXT_PROMPT.md": (12_000, 16_000),
    "SESSION_NOTES.md": (110_000, 150_000),
    "NAMED.md": (150_000, 250_000),
    "skill/SKILL.md": (55_000, 70_000),
    "AGENTS.md": (6_000, 10_000),
}
ALWAYS_LOADED = ("AGENTS.md", "NEXT_PROMPT.md", "skill/SKILL.md")
LOOKUP_ONLY = ("NAMED.md", "SESSION_NOTES.md")
EVIDENCE_MB = (20, 30)   # warn, fail
SINGLE_FILE_MB = (1, 4)

CITE_RE = re.compile(r"^([A-Za-z0-9_./-]+?):(\d+)(?:-(\d+))?$")


def rel(p):
    return os.path.relpath(p, ROOT)


def load_cites():
    """Patterns for every evidence filename mentioned in the docs (globs honoured)."""
    pats = set()
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in
                       (".git", "node_modules", "__pycache__", "evidence", "programs", "glsmac")]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            try:
                text = open(os.path.join(dirpath, fn), encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            # .jsonl is the format every trace uses — it was missing here, so NO trace could
            # ever be "cited" and the audit reported 12.7 MB of live evidence as garbage (M62).
            for m in re.finditer(r"[A-Za-z0-9_.*-]+\.(?:png|log|gdb|txt|jsonl|json|csv)", text):
                pats.add(m.group(0).replace("*", ".*"))
    return [re.compile(f"^(?:.*/)?{p}$") for p in pats]


def is_cited(name, pats):
    return any(p.match(name) for p in pats)


def human(n):
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{n / 1e3:.0f} KB"


def cmd_budget(_args):
    print(f"context: {CONTEXT_TOKENS:,} tokens ≈ {CONTEXT_TOKENS * CHARS_PER_TOKEN / 1e6:.2f}M chars\n")
    print(f"{'artifact':22} {'bytes':>9} {'~tokens':>9}  {'% ctx':>6}  status")
    always = lookups = 0
    bad = 0
    for name, (warn, fail) in DOC_BUDGETS.items():
        path = os.path.join(ROOT, name)
        if not os.path.isfile(path):
            continue
        n = os.path.getsize(path)
        if name in ALWAYS_LOADED:
            always += n
            kind = "always"
        else:
            lookups += n
            kind = "lookup"
        tok = n / CHARS_PER_TOKEN
        status = "ok"
        if n > fail:
            status = "FAIL"
            bad += 1
        elif n > warn:
            status = "warn"
        print(f"{name:22} {n:9,} {tok:9,.0f}  {100 * tok / CONTEXT_TOKENS:5.1f}%  {status:4} ({kind})")
    print(f"{'always loaded':22} {always:9,} {always / CHARS_PER_TOKEN:9,.0f}  "
          f"{100 * always / CHARS_PER_TOKEN / CONTEXT_TOKENS:5.1f}%   ← paid every session")
    print(f"{'lookups (never whole)':22} {lookups:9,} {lookups / CHARS_PER_TOKEN:9,.0f}  "
          f"{100 * lookups / CHARS_PER_TOKEN / CONTEXT_TOKENS:5.1f}%   ← grep / tail only")
    print(f"{'ritual target':22} {60_000:9,} {15_000:9,.0f}  {100 * 15_000 / CONTEXT_TOKENS:5.1f}%"
          f"   (skill + prompt + 2 sessions + ~10 evidence windows)")
    print()

    ev_size = sum(os.path.getsize(os.path.join(d, f))
                  for d, _, fs in os.walk(EVID) for f in fs)
    files = sum(len(fs) for _, _, fs in os.walk(EVID))
    imgs = [os.path.join(d, f) for d, _, fs in os.walk(EVID) for f in fs if f.endswith(".png")]
    img_size = sum(os.path.getsize(p) for p in imgs)
    warn_mb, fail_mb = EVIDENCE_MB
    status = "FAIL" if ev_size > fail_mb * 1e6 else ("warn" if ev_size > warn_mb * 1e6 else "ok")
    if status == "FAIL":
        bad += 1
    print(f"evidence/: {human(ev_size)} in {files} files ({len(imgs)} images, {human(img_size)})"
          f"  budget {warn_mb}/{fail_mb} MB  [{status}]")
    biggest = sorted(((os.path.getsize(os.path.join(d, f)), os.path.join(d, f))
                      for d, _, fs in os.walk(EVID) for f in fs), reverse=True)[:5]
    if biggest and biggest[0][0] > SINGLE_FILE_MB[0] * 1e6:
        print("  largest: " + ", ".join(f"{rel(p)} {human(s)}" for s, p in biggest[:3]))
        print("  → digest or prune these; read them with `evidence.py show`")
    print()
    print("evidence is append-only; pruning never deletes history (git keeps it).")
    return 1 if bad else 0


def resolve(cite):
    """Resolve path:line to (path, start, end) or exit with a clear reason."""
    m = CITE_RE.match(cite)
    if m:
        name, start, end = m.group(1), int(m.group(2)), m.group(3)
        end = int(end) if end else start
    else:
        name, start, end = cite, 1, 0
    for cand in (os.path.join(ROOT, name), os.path.join(EVID, name), os.path.join(ROOT, "evidence", name)):
        if os.path.isfile(cand):
            return cand, start, end
    raise SystemExit(f"{name}: not in the working tree (pruned?). Check `evidence.py log`, or "
                     f"`git log --all --diff-filter=D -- {name}`")


def cmd_show(args):
    path, start, end = resolve(args.cite)
    text = open(path, encoding="utf-8", errors="replace").read().splitlines()
    if not end:
        end = start
    lo = max(1, start - args.context)
    hi = min(len(text), end + args.context)
    print(f"# {rel(path)} lines {lo}-{hi} of {len(text)}")
    for i in range(lo, hi + 1):
        mark = ">" if start <= i <= end else " "
        print(f"{mark}{i:6}  {text[i - 1][:400]}")
    if len(text) > hi:
        print(f"# ... {len(text) - hi} more lines; digest: evidence/digests/{os.path.basename(path)}.md")
    return 0


def cmd_digest(args):
    path, _, _ = resolve(args.cite)
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    os.makedirs(DIGESTS, exist_ok=True)
    counts, samples = {}, {}
    for ln in lines:
        key = ln.split()[0] if ln.split() else "(blank)"
        key = re.sub(r"\d+$", "", key)
        counts[key] = counts.get(key, 0) + 1
        samples.setdefault(key, [])
        if len(samples[key]) < 3:
            samples[key].append(ln)
    out = [f"# Digest — {rel(path)}", "",
           f"{len(lines)} lines, {os.path.getsize(path) / 1e3:.0f} KB. "
           f"Read this instead of the log; open windows with "
           f"`evidence.py show {os.path.basename(path)}:<line>`.", "", "## Line kinds", ""]
    for k, n in sorted(counts.items(), key=lambda kv: -kv[1])[:12]:
        out.append(f"- `{k}` × {n}")
    out += ["", "## Samples (first 3 of each kind)", ""]
    for k in sorted(samples, key=lambda k: -counts[k])[:8]:
        for s in samples[k]:
            out.append(f"- `{s[:220]}`")
    out += ["", f"last line: `{lines[-1][:200] if lines else ''}`"]
    dest = os.path.join(DIGESTS, os.path.basename(path) + ".md")
    open(dest, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"wrote {rel(dest)} ({os.path.getsize(dest)} bytes)")
    return 0


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_prune(args):
    pats = load_cites()
    now = time.time()
    keep_days = args.keep_days
    victims, kept = [], 0
    for dirpath, _, files in os.walk(EVID):
        for fn in files:
            p = os.path.join(dirpath, fn)
            if p == PRUNE_LOG or "digests" in p:
                continue
            if not fn.endswith(".png"):
                continue  # text evidence is cheap; never prune it
            if is_cited(fn, pats):
                kept += 1
                continue
            if now - os.path.getmtime(p) < keep_days * 86400:
                kept += 1
                continue
            victims.append(p)
    total = sum(os.path.getsize(p) for p in victims)
    print(f"cited/young images kept: {kept}")
    print(f"uncited images older than {keep_days}d: {len(victims)} ({human(total)})")
    for p in victims[:10]:
        print(f"  - {rel(p)}")
    if len(victims) > 10:
        print(f"  ... {len(victims) - 10} more")
    if args.dry_run:
        print("\ndry run — rerun with --apply")
        return 0
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    os.makedirs(EVID, exist_ok=True)
    with open(PRUNE_LOG, "a", encoding="utf-8") as log:
        for p in victims:
            log.write(json.dumps({"path": rel(p), "sha256": sha256(p),
                                  "bytes": os.path.getsize(p), "at_commit": commit,
                                  "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\n")
            os.remove(p)
    print(f"pruned {len(victims)} images, reclaimed {human(total)}; history retained in git")
    return 0


def cmd_audit(args):
    """Which evidence files does NO document cite? (M62)

    The budget gate FAILs at 30 MB and a session adds ~0.7 MB, so the honest lever is
    "delete what nothing cites" — never "raise the gate". Citation is decided by the same
    load_cites() that the gate uses, so the audit cannot disagree with the gate.
    """
    pats = load_cites()
    # A file can also be live because CODE names it (classifier frames, fixture traces,
    # expected artefacts). Deleting those breaks a test, so they count as used.
    code = ""
    for d, _, fs in os.walk(os.path.join(ROOT, "scripts")):
        for f in fs:
            if f.endswith(".py"):
                code += open(os.path.join(d, f), encoding="utf-8", errors="ignore").read()
    rows = []
    for dirpath, _, files in os.walk(EVID):
        for fn in files:
            p = os.path.join(dirpath, fn)
            if p == PRUNE_LOG or "digests" in p:
                continue
            if is_cited(fn, pats) or fn in code:
                continue
            rows.append((os.path.getsize(p), p))
    rows.sort(reverse=True)
    total = sum(s for s, _ in rows)
    print(f"uncited evidence: {len(rows)} file(s), {human(total)} "
          f"(of {sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(EVID) for f in fs) / 1e6:.1f} MB)")
    for s, p in rows[:15]:
        print(f"  {human(s):>8}  {rel(p)}")
    if len(rows) > 15:
        print(f"  ... {len(rows) - 15} more")
    if not args.delete:
        print("\nrerun with --delete to remove them (git keeps the history)")
        return 0
    for _, p in rows:
        os.remove(p)
    print(f"\ndeleted {len(rows)} uncited file(s), reclaimed {human(total)}")
    return 0


def cmd_log(_args):
    if not os.path.isfile(PRUNE_LOG):
        print("nothing pruned yet")
        return 0
    rows = [json.loads(l) for l in open(PRUNE_LOG, encoding="utf-8") if l.strip()]
    print(f"{len(rows)} pruned file(s), {human(sum(r['bytes'] for r in rows))}")
    for r in rows[-10:]:
        print(f"  {r['path']}  {human(r['bytes'])}  at {r['at_commit']}  {r['sha256'][:12]}")
    print("\nrecover one: git log --all --diff-filter=D -- <path>  →  git show <commit>^:<path>")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("budget").set_defaults(fn=cmd_budget)
    s = sub.add_parser("show"); s.add_argument("cite"); s.add_argument("--context", type=int, default=3)
    s.set_defaults(fn=cmd_show)
    s = sub.add_parser("digest"); s.add_argument("cite"); s.set_defaults(fn=cmd_digest)
    s = sub.add_parser("prune")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--apply", dest="dry_run", action="store_false")
    s.add_argument("--keep-days", type=int, default=7)
    s.set_defaults(fn=cmd_prune, dry_run=True)
    s = sub.add_parser("audit"); s.add_argument("--delete", action="store_true")
    s.set_defaults(fn=cmd_audit)
    sub.add_parser("log").set_defaults(fn=cmd_log)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
