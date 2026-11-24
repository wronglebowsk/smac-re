#!/usr/bin/env python3
"""m346_named_rotate.py -- move NAMED.md's settled `## M313` block VERBATIM into
`docs/named-archive-m313-rows.md` and leave a one-line-per-claim stub behind.

Why: NAMED.md is 2,221 B from its 250,000 B FAIL and M346 must add a block.  The
archived block keeps every claim, gate and cite byte-for-byte; the stub repeats
each claim on ONE line with the same evidence pointer and confidence, so a grep
on NAMED still lands on the right file.

`--verify` recomputes the sha1 of the archived block and asserts it equals the
sha1 recorded in BOTH files and that the stub carries one row per archived claim.
Byte-exactness is the point: this script never rewrites claim text.

    python3 scripts/m346_named_rotate.py            # rotate (idempotent: skips if done)
    python3 scripts/m346_named_rotate.py --verify
"""
import argparse
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m313-rows.md")
HEAD = "## M313 "
ARCHIVE_HEAD = ("# NAMED.md `## M313` - ROTATED VERBATIM (byte-exact) by "
                "scripts/m346_named_rotate.py")
SENT = "<!-- block: every byte below is the original NAMED.md block -->"

# one line per archived claim: (label, evidence pointer, conf)
STUB_ROWS = [
    ("BAND LAW: both trunks converge on [0x50bb20,0x5175b4) - 20/28 + 9 owners, 8 off-band hub owners "
     "pinned, 53 sites by address list",
     "`evidence/m313_event_map.txt:1-6` + `evidence/m313_mutate.txt:2,3,5`", "V"),
    ("THE PUMPS: FUN_00512b40 -> 8 in-band + 4 off-band; FUN_00516b80 -> 5 + 5 and (M314) also "
     "FUN_004d3f70 @0x517858; 7 + 6 hub sites by address",
     "`evidence/m313_event_map.txt:7,8,9,10,12` + `evidence/m313_mutate.txt:6-9,11`", "V"),
    ("PUMPA = command dispatcher (byte map 0x5165ec + 8-slot jump 0x5165cc; VK map 0x516638 + 4-slot "
     "0x516628); PUMPB = order-key `lea ebx-0x51 / cmp 0xc` + 13-slot table 0x5181d0",
     "`evidence/m313_event_map.txt:15-19` + `evidence/m313_mutate.txt:16-21`", "V encoding / INFERRED meaning"),
    ("PUMPA'S DOOR: FUN_0041bda0 has zero refs; a stored u32 at 0x6724a8 lies in a 490-pointer "
     "multi-class run at 0x672290 (f2e2c9dfae9ba011) - the word 'slot' retired",
     "`evidence/m313_event_map.txt:13,14` + `evidence/m313_mutate.txt:12-15`", "V entries"),
    ("MOUSE PATH: map_click_handler FUN_00476580 calls 4 in-band members + 004739a0 - a map click "
     "reaches the goal check with no pump",
     "`evidence/m313_event_map.txt:11` + `evidence/m313_mutate.txt:10`", "V"),
    ("PUMPB ENTRY: FUN_005186b0 has 0 call/jmp refs and exactly ONE stored u32 (imm32 of `push 0x5186b0` "
     "at 0x51892d in FUN_00518820, from init FUN_00580260)",
     "`evidence/m313_event_map.txt:20,21` + `evidence/m313_mutate.txt:22-24`", "V census / INFERRED install"),
    ("CLOSED by M314: the 'dialog-family' census and FUN_004d3f70's band calls (exactly 1 band member, "
     "FUN_0050cab0 x2); GOAL game-meaning still open (M310)",
     "`evidence/m314_tour_family.txt`", "V"),
]


def block_bounds(lines):
    start = None
    for i, l in enumerate(lines):
        if l.startswith(HEAD):
            start = i
            break
    if start is None:
        return None, None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return start, end


def sha1(text):
    return hashlib.sha1(text.encode()).hexdigest()


def verify():
    ok = True
    named = open(NAMED).read()
    arch = open(ARCHIVE).read()
    body = (arch.split(SENT + "\n", 1)[1] if SENT in arch else "").rstrip("\n")
    h = sha1(body)
    hi = None
    for line in named.splitlines():
        if line.startswith(HEAD) and "sha1 `" in line:
            hi = line.split("sha1 `")[1].split("`")[0]
    ha = None
    for line in arch.splitlines()[:4]:
        if "sha1 `" in line:
            ha = line.split("sha1 `")[1].split("`")[0]
    print("archive block sha1 : %s (%d B, %d lines)" % (h, len(body.encode()), body.count("\n") + 1))
    print("recorded in NAMED : %s" % hi)
    print("recorded in archive: %s" % ha)
    if not (h.startswith(hi or "-") and ha == h):
        print("FAIL: sha1 mismatch - the archive is not byte-exact")
        ok = False
    rows = [l for l in named.splitlines() if l.startswith("| ") and l.count("|") >= 4]
    # stub rows live between the M313 head and the next '## '
    lines = named.split("\n")
    s, e = block_bounds(lines)
    stub = lines[s:e] if s is not None else []
    n_rows = sum(1 for l in stub if l.startswith("| ") and "---" not in l
                 and not l.startswith("| claim"))
    print("stub rows: %d (archived claims: %d)" % (n_rows, len(STUB_ROWS)))
    if n_rows != len(STUB_ROWS):
        print("FAIL: stub lost a claim")
        ok = False
    if "stub governs" not in "\n".join(stub):
        print("FAIL: M313 head does not declare the stub")
        ok = False
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def rotate():
    named = open(NAMED).read()
    lines = named.split("\n")
    s, e = block_bounds(lines)
    if s is None:
        print("no `%s` block found" % HEAD)
        return 1
    block = "\n".join(lines[s:e]).rstrip("\n")
    if "stub governs" in lines[s]:
        print("already rotated - nothing to do")
        return 0
    h = sha1(block)
    rec = "%s\n\nrotated by `scripts/m346_named_rotate.py`; sha1 `%s` of the block below.\n%s\n" % (
        ARCHIVE_HEAD, h, SENT)
    with open(ARCHIVE, "w") as f:
        f.write(rec + block + "\n")
    # stub
    title = lines[s]
    stub = [title.replace(
        " - pick (i') CLOSED",
        " - ROTATED VERBATIM to `docs/named-archive-m313-rows.md` (sha1 `%s`) - "
        "pick (i') CLOSED" % h[:12]), "",
        "| claim (one line each; full rows in the archive) | evidence | conf |", "|---|---|---|"]
    for label, ev, conf in STUB_ROWS:
        stub.append("| %s | %s | %s |" % (label, ev, conf))
    stub.append("this stub governs: one line per claim. Acceptance `python3 -u "
                "scripts/m313_event_map.py` -> **21/21**, digest 5e14170de426d127, x2 identical; "
                "`scripts/m313_mutate.py` -> **23/23**.")
    new = lines[:s] + stub + lines[e:]
    out = "\n".join(new)
    with open(NAMED, "w") as f:
        f.write(out)
    print("rotated %d B -> archive (sha1 %s); NAMED now %d B" % (len(block), h[:16], len(out)))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    sys.exit(verify() if a.verify else rotate())
