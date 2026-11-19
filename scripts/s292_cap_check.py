#!/usr/bin/env python3
"""s292 cap-split checker (SHIPPED, so the "moved VERBATIM" acceptance is reproducible).

Three measured checks, table FIRST then asserts (review #316 P2/P3 demanded a committed
checker instead of an ad-hoc heredoc):

  C1 NEXT_PROMPT.md is under the budget warn cap AND actually shrank vs `main`.
  C2 every fenced block under docs/pick-archive.md §trim-s292 (a)/(b) is BYTE-EXACT inside
     `main:NEXT_PROMPT.md` (the moved text), printed with per-block sha256 + length.
  C3 the SESSION_NOTES.md "Older sessions:" pointer chain reaches EVERY archive on disk
     (no orphan archives - the defect #316's review found in scripts/session_rotate.py).

`--selftest` perturbs MEASURED INPUTS (a byte of an archived block, a dropped pointer, a
cap set one below the measured size) and requires each perturbation to REDDEN its check:
a gate that cannot fail is a defect, not a gate.

STATUS (moved out of NEXT_PROMPT.md at s297 to buy the hot doc its headroom back): C1/C2
fail BY DESIGN now that #316's split is in main; only C3 (the archive pointer chain) stands.

  python3 -u scripts/s292_cap_check.py
  python3 -u scripts/s292_cap_check.py --selftest
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCH = os.path.join(REPO, "docs", "sessions")
PROMPT = os.path.join(REPO, "NEXT_PROMPT.md")
NOTES = os.path.join(REPO, "SESSION_NOTES.md")
PICKARCH = os.path.join(REPO, "docs", "pick-archive.md")
CAP = 12_000                 # budget's NEXT_PROMPT warn, in BYTES
HEADERS = ("## §trim-s292 (a)", "## §trim-s292 (b)")
POINTER_RX = re.compile(r"Older sessions: `docs/sessions/([\w.-]+\.md)`")
rows, verdicts = [], []


def ck(name, ok, det=""):
    verdicts.append(bool(ok))
    rows.append((name, ok))
    print(("OK   " if ok else "FAIL ") + name + ": " + det)


def git_show(rev, path):
    return subprocess.run(["git", "-C", REPO, "show", f"{rev}:{path}"],
                          capture_output=True, text=True, check=True).stdout


def fenced_blocks(text, header):
    """The fenced blocks under `header` up to the next '## ' header."""
    i = text.index(header)
    rest = text[i + len(header):]
    nxt = re.search(r"^## ", rest, re.M)
    if nxt:
        rest = rest[:nxt.start()]
    return [b.rstrip("\n") for b in re.findall(r"```\n(.*?)```", rest, re.S)]


def c1_size(main_text, head_text, cap=CAP):
    a, b = len(main_text.encode()), len(head_text.encode())
    ck("C1 NEXT_PROMPT under cap AND shrank vs main",
       b <= cap and b < a, f"main={a} B  head={b} B  cap={cap} B  delta={b - a} B")
    return b


def c2_verbatim(main_text, blocks):
    exact = 0
    for blk in blocks:
        h = hashlib.sha256(blk.encode()).hexdigest()[:16]
        hit = blk in main_text
        exact += hit
        print("     block sha256=%s len=%-5d first=%s  byte-exact-in-main-NEXT_PROMPT=%s"
              % (h, len(blk), blk.splitlines()[0][:52], hit))
    ck("C2 all moved blocks BYTE-EXACT vs main:NEXT_PROMPT.md",
       len(blocks) == 4 and exact == len(blocks), f"blocks={len(blocks)} byte-exact={exact}")
    return exact


def walk_chain(texts, on_disk=None):
    """Follow 'Older sessions:' pointers from SESSION_NOTES.md; return (visited, orphans)."""
    if on_disk is None:
        on_disk = set(n for n in os.listdir(ARCH) if re.fullmatch(r"sessions-\d+-\d+\.md", n))
    else:
        on_disk = set(on_disk)
    start = POINTER_RX.search(texts["SESSION_NOTES.md"] or "")
    visited, queue = set(), [start.group(1)] if start else []
    while queue:
        nm = queue.pop()
        if nm in visited or nm not in on_disk:
            continue
        visited.add(nm)
        nxt = POINTER_RX.search(texts.get(nm, ""))
        if nxt:
            queue.append(nxt.group(1))
    return visited, sorted(on_disk - visited)


def c3_chain(texts):
    visited, orphans = walk_chain(texts)
    for nm in sorted(visited):
        print("     reachable: %s" % nm)
    for nm in orphans[:8]:
        print("     ORPHAN   : %s" % nm)
    ck("C3 every archive reachable from SESSION_NOTES.md by pointer",
       not orphans, f"archives={len(visited) + len(orphans)} reachable={len(visited)} orphans={len(orphans)}")
    return orphans


def load_texts(ref=None):
    """ref=REV reads the hot file + archives from a commit, so the PRE-FIX orphan count stays
    measurable after the repair (the s292 review asked that the defect's size be checkable)."""
    if not ref:
        texts = {"SESSION_NOTES.md": open(NOTES, encoding="utf-8").read()}
        for nm in os.listdir(ARCH):
            if re.fullmatch(r"sessions-\d+-\d+\.md", nm):
                texts[nm] = open(os.path.join(ARCH, nm), encoding="utf-8").read()
        return texts
    names = [l.split()[-1] for l in subprocess.run(
        ["git", "-C", REPO, "ls-tree", "-r", "--name-only", ref, "--", "docs/sessions"],
        capture_output=True, text=True).stdout.splitlines() if l.strip()]
    texts = {"SESSION_NOTES.md": git_show(ref, "SESSION_NOTES.md")}
    for path in names:
        nm = os.path.basename(path)
        if re.fullmatch(r"sessions-\d+-\d+\.md", nm):
            texts[nm] = git_show(ref, path)
    return texts


def selftest(main_text, head_text, blocks, texts, measured_bytes):
    print("-- SELFTEST: perturb MEASURED INPUTS, each must redden its check --")
    bad = list(blocks)
    mid = len(bad[0]) // 2   # perturb a byte that MUST exist: flip the middle character
    midc = "X" if bad[0][mid] != "X" else "Y"
    bad[0] = bad[0][:mid] + midc + bad[0][mid + 1:]
    assert bad[0] != blocks[0], "selftest perturbation did nothing"
    start = len(verdicts)
    c2_verbatim(main_text, bad)
    s2 = verdicts[start] is False
    t2 = dict(texts)
    t2["SESSION_NOTES.md"] = POINTER_RX.sub("Older sessions: (dropped)", texts["SESSION_NOTES.md"], count=1)
    p = len(verdicts)
    orph = c3_chain(t2)
    s3 = verdicts[p] is False and len(orph) > 0
    q = len(verdicts)
    c1_size(main_text, head_text, cap=measured_bytes - 1)
    s1 = verdicts[q] is False
    # drop the verdicts the selftest added so they cannot pollute the real exit code
    del verdicts[start:]
    rows.clear()
    ck("SELFTEST S1/S2/S3 reddened cap / verbatim / chain",
       s1 and s2 and s3, f"cap_fail={s1} verbatim_fail={s2} chain_fail={s3} (orphans={len(orph)})")
    return verdicts[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--ref", metavar="REV", default=None,
                    help="INFO-only, never a gate: measure the session-chain reachability at REV "
                         "(so the pre-fix orphan count stays checkable after the repair)")
    args = ap.parse_args()
    if args.ref:
        t = load_texts(args.ref)
        on_disk = [n for n in t if n != "SESSION_NOTES.md"]
        visited, orphans = walk_chain(t, on_disk)
        print("INFO chain at %s: archives=%d reachable=%d orphans=%d (first 3: %s)"
              % (args.ref, len(on_disk), len(visited), len(orphans), orphans[:3]))
        return 0
    main_text = git_show("main", "NEXT_PROMPT.md")
    head_text = open(PROMPT, encoding="utf-8").read()
    arch = open(PICKARCH, encoding="utf-8").read()
    blocks = [b for h in HEADERS for b in fenced_blocks(arch, h)]
    texts = load_texts()
    print("-- the measurements --")
    print("NEXT_PROMPT.md main=%d B head=%d B | pick-archive §trim-s292 blocks=%d | archives on disk=%d"
          % (len(main_text.encode()), len(head_text.encode()), len(blocks),
             len([n for n in os.listdir(ARCH) if n.endswith(".md")])))
    print("-- C1 sizes --")
    measured = c1_size(main_text, head_text)
    print("-- C2 verbatim moves --")
    c2_verbatim(main_text, blocks)
    print("-- C3 session pointer chain --")
    c3_chain(texts)
    if args.selftest:
        selftest(main_text, head_text, blocks, texts, measured)
    n_ok = sum(verdicts)
    print("== s292 cap check: %d/%d checks green ==" % (n_ok, len(verdicts)))
    return 0 if n_ok == len(verdicts) else 1


if __name__ == "__main__":
    sys.exit(main())
