#!/usr/bin/env python3
"""review_lint (s291, review-round hardened): the MECHANICAL half of the
claim->mutant law.

SCOPE (honest, per #315 review): this lint checks NAMING + EXISTENCE +
ADDRESS-CONTACT + row-scoped digest presence + citation lines. It does NOT
decide the row->mutant->gate semantic relationship (which gate reads which
claim) — that stays with scripts/ai_review.py and the closing agent. A cited
mutant that exists but reddens an unrelated gate passes this lint and must
still be caught by the semantic review.

Checks on the milestone's NAMED.md block (## <ID> ... next ## header):
  L1 every V claim row cites >=1 mutant id (MU<n>, ranges expanded).
     Meta-row exemption is TIGHT: claim starts ACCEPT/REVIEW AND the row
     cites the harness (_mutate.py) or a digest — a factual claim cannot
     bypass L1 by prefixing itself with those words (#315 P1).
  L2 every cited mutant id EXISTS in scripts/<id>_mutate.py.
  L2b every cited CODE mutant's patch address appears in the milestone's
     instrument source (the mutant touches bytes the instrument reads).
  L3 every "digest <16-hex>" is present in an evidence file cited IN THE
     SAME ROW (or the last file cited before the row for prose mentions) —
     not just anywhere in the block (#315 P1/P2). The digest must be
     PRINTED there; whether it was computed from the claimed bytes is the
     harness baseline's + reviewer's job, not this lint's.
  L4 every full evidence/<file> citation carries :line; directory-shaped
     citations are not matched (file suffix required, isfile-guarded).

    python3 scripts/review_lint.py --id m318
    python3 scripts/test_review_lint.py     # fixtures: each check must bite
"""
import argparse
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MU_RX = re.compile(r"MU(\d+)")
MU_RANGE_RX = re.compile(r"MU(\d+)\s*[-–]\s*MU(\d+)")
DIGEST_RX = re.compile(r"digest\s+([0-9a-f]{16})", re.I)
EVID_RX = re.compile(r"evidence/[\w.-]+(?:/[\w.-]+)*\.[A-Za-z0-9]+")
CODE_MU_RX = re.compile(r'\("(MU\d+)",\s*"code",\s*"(0x[0-9a-fA-F]+)\|')


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
        if cells[-1].startswith("V"):
            rows.append((cells[0], line))
    return rows


def cited_mus(text):
    ids = set()
    for a, b in MU_RANGE_RX.findall(text):
        ids.update(range(int(a), int(b) + 1))
    stripped = MU_RANGE_RX.sub("", text)
    ids.update(int(n) for n in MU_RX.findall(stripped))
    return {"MU%d" % n for n in ids}


def lint_block(block, harness_src, evidence_files, instrument_src=""):
    """evidence_files: {path: content}. Returns failure strings (empty=PASS)."""
    fails = []
    if block is None:
        return ["block not found"]
    have = set(re.findall(r'"(MU\d+)"', harness_src or ""))
    code_addr = {mu: addr.lower() for mu, addr in CODE_MU_RX.findall(harness_src or "")}
    isrc = (instrument_src or "").lower()
    for claim, line in v_rows(block):
        meta = claim.startswith(("ACCEPT", "REVIEW")) and (
            "_mutate.py" in line or "digest" in line.lower())
        mus = cited_mus(line)
        if not meta:
            if not mus:
                fails.append("L1 no mutant cited: %s" % claim[:70])
        for mu in sorted(mus - have):
            fails.append("L2 mutant %s not in harness: %s" % (mu, claim[:50]))
        for mu in sorted(mus & set(code_addr)):
            if code_addr[mu][2:] not in isrc:
                fails.append("L2b %s patch addr %s not read by instrument: %s"
                             % (mu, code_addr[mu], claim[:40]))
    # L3: row-scoped digest resolution
    last_file = None
    for line in block.splitlines():
        row_files = EVID_RX.findall(line)
        for m in DIGEST_RX.finditer(line):
            d = m.group(1)
            candidates = set(row_files) | ({last_file} if last_file else set())
            if not any(d in (evidence_files.get(p) or "") for p in candidates):
                fails.append("L3 digest %s not printed in the row's cited evidence" % d)
        if row_files:
            last_file = row_files[-1]
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
    if not os.path.exists(hpath):
        print("FAIL: no harness scripts/%s_mutate.py" % mid)
        return 1
    harness = open(hpath).read()
    isrc = ""
    for p in glob.glob(os.path.join(ROOT, "scripts", "%s_*.py" % mid)):
        if p.endswith(("_mutate.py",)) or os.path.basename(p).startswith("test_"):
            continue
        isrc += open(p, errors="replace").read()
    evidence = {}
    for p in set(EVID_RX.findall(block)):
        fp = os.path.join(ROOT, p)
        if os.path.isfile(fp):
            evidence[p] = open(fp, errors="replace").read()
    fails = lint_block(block, harness, evidence, isrc)
    nrows = len(v_rows(block))
    if fails:
        for f in fails:
            print("FAIL:", f)
        print("== review_lint: %d failure(s) over %d V rows ==" % (len(fails), nrows))
        return 1
    print("== review_lint: PASS (%d V rows; mutants exist + touch instrument bytes; digests row-scoped; cites lined) ==" % nrows)
    return 0


if __name__ == "__main__":
    sys.exit(main())