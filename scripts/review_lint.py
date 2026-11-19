#!/usr/bin/env python3
"""review_lint (s291): the MECHANICAL half of the claim->mutant law.

The mutation harness proves gates BITE; this lint proves the NAMED block's
VERIFIED rows actually NAME their mutants, and that cited digests/citations
are real. Model-independent, runs at close BEFORE submit. The semantic half
(definition-mismatch scrutiny) belongs to scripts/ai_review.py.

Checks on the milestone's NAMED.md block (## <ID> ... next ## header):
  L1 every V claim row cites >=1 mutant id (MU<n>, ranges expanded);
     ACCEPT/REVIEW meta-rows are exempt (they cite the harness + digest).
  L2 every cited mutant id EXISTS in scripts/<id>_mutate.py.
  L3 every 16-hex digest quoted in the block appears in at least one
     evidence file the block cites (a digest the instrument never printed
     is the #311 P2 class).
  L4 every full evidence/<file> citation in the block carries :line.

    python3 scripts/review_lint.py --id m318 [--base main]
    python3 scripts/test_review_lint.py     # fixtures: each check must bite
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MU_RX = re.compile(r"MU(\d+)")
MU_RANGE_RX = re.compile(r"MU(\d+)\s*[-–]\s*MU(\d+)")
DIGEST_RX = re.compile(r"\b[0-9a-f]{16}\b")
EVID_RX = re.compile(r"evidence/[\w./-]+")


def block_for(named_text, mid):
    m = re.search(r"^## %s\b" % re.escape(mid.upper()), named_text, re.M)
    if not m:
        return None
    rest = named_text[m.start():]
    nxt = re.search(r"^## ", rest[3:], re.M)
    return rest[:nxt.start() + 3] if nxt else rest


def v_rows(block):
    rows = []
    for line in block.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] in ("claim", "---") or set(cells[0]) <= {"-"}:
            continue
        conf = cells[-1]
        if conf.startswith("V"):
            rows.append((cells[0], line))
    return rows


def cited_mus(text):
    ids = set()
    for a, b in MU_RANGE_RX.findall(text):
        ids.update(range(int(a), int(b) + 1))
    stripped = MU_RANGE_RX.sub("", text)
    ids.update(int(n) for n in MU_RX.findall(stripped))
    return {"MU%d" % n for n in ids}


def lint_block(block, harness_src, evidence_files):
    """evidence_files: {path: content} for the files the block cites.
    Returns a list of failure strings (empty = PASS)."""
    fails = []
    if block is None:
        return ["block not found"]
    have = set(re.findall(r'"(MU\d+)"', harness_src or ""))
    for claim, line in v_rows(block):
        meta = claim.startswith("ACCEPT") or claim.startswith("REVIEW")
        mus = cited_mus(line)
        if not meta:
            if not mus:
                fails.append("L1 no mutant cited: %s" % claim[:70])
            for mu in sorted(mus - have):
                fails.append("L2 mutant %s not in harness: %s" % (mu, claim[:50]))
    cited_paths = set(EVID_RX.findall(block))
    for d in sorted(set(DIGEST_RX.findall(block))):
        if not any(d in (evidence_files.get(p) or "") for p in cited_paths):
            fails.append("L3 digest %s not printed in any cited evidence file" % d)
    for m in EVID_RX.finditer(block):
        tail = block[m.end():m.end() + 12]
        if not re.match(r":\d+", tail):
            fails.append("L4 citation without :line — %s" % m.group(0))
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="milestone id, e.g. m318")
    args = ap.parse_args()
    mid = args.id.lower()
    named = open(os.path.join(ROOT, "NAMED.md")).read()
    block = block_for(named, mid)
    if block is None:
        print("FAIL: no ## %s block in NAMED.md" % mid.upper())
        return 1
    hpath = os.path.join(ROOT, "scripts", "%s_mutate.py" % mid)
    harness = open(hpath).read() if os.path.exists(hpath) else ""
    if not harness:
        print("FAIL: no harness scripts/%s_mutate.py" % mid)
        return 1
    evidence = {}
    for p in set(EVID_RX.findall(block)):
        fp = os.path.join(ROOT, p.split(":")[0])
        if os.path.exists(fp):
            evidence[p] = open(fp, errors="replace").read()
    fails = lint_block(block, harness, evidence)
    nrows = len(v_rows(block))
    if fails:
        for f in fails:
            print("FAIL:", f)
        print("== review_lint: %d failure(s) over %d V rows ==" % (len(fails), nrows))
        return 1
    print("== review_lint: PASS (%d V rows, all mutants exist, digests printed, cites lined) ==" % nrows)
    return 0


if __name__ == "__main__":
    sys.exit(main())