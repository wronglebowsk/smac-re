#!/usr/bin/env python3
"""m348_named_rotate.py -- move settled NAMED.md blocks VERBATIM into
`docs/named-archive-*-rows.md` and leave a one-line-per-claim stub behind.

Why: NAMED.md must add the M348 block and was 2,175 B from its 250,000 B FAIL.
Each archived block keeps every claim, gate and cite byte-for-byte; the stub
repeats each claim on ONE line with the same evidence pointer and confidence, so
a grep on NAMED still lands on the right file.

`--verify` recomputes the sha1 of each archived block, asserts it equals the
sha1 recorded in BOTH files, and that each stub carries one row per claim.

    python3 scripts/m348_named_rotate.py            # rotate (idempotent)
    python3 scripts/m348_named_rotate.py --verify
"""
import argparse
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
SENT = "<!-- block: every byte below is the original NAMED.md block -->"

BLOCKS = [
    {
        "head": "## B28 ",
        "archive": "named-archive-b28-feeder-rows.md",
        "note": ("acceptance `python3 -u -m sim.selftest --b28` -> **`PASS B28: 8/8 gates`** "
                 "`705a4520c08c4062`, harness `scripts/b28_mutate.py` -> **18/18** `3974d739da3af55f`."),
        "rows": [
            ("`ds:0x985ba0` CARRIED in the state header (file offset 244), reads -1 in m54b_clean; "
             "the 4f48dc sign skip fires, halving runs 0 times", "`evidence/b28_feeder_exec.txt:5`", "V"),
            ("the container's own `+300` octet = the feeder's full-price total 8/8; the no-list rival "
             "is exactly 7/8, miss `[own_player=3]`", "`:8`", "V"),
            ("bounds are the parsed immediates 1 / 0x22 / 0x27: VISITS 1..38, CHARGES 1..34, upkeep "
             "dword at row+0x10", "`:3`", "V"),
            ("charged only when the base's own `+0x8c` bitmap bit is set (18/18); ids 32..38 inert "
             "here (0/18 vs 14/18 control)", "`:4`", "V; width past +0x8f OPEN"),
            ("charge = `trunc((cost+carry)/2)` (cdq/sub/sar), parity written back into bit5; "
             "full-price leaves the carry", "`:6`", "V"),
            ("FIXTURE-ONLY persistence: no carry in the save's own run; honest run touches `[]` and "
             "rewrites bit5 unchanged", "`:7`", "V (fixture-only)"),
            ("the NOUN of `ds:0x985ba0`; `ebx` == the charged base's owner", "M333 G6", "INFERRED"),
        ],
    },
    {
        "head": "## M343 ",
        "archive": "named-archive-m343-a40-rows.md",
        "note": ("acceptance `scripts/m343_a40_writer.py` -> **`PASS M343: 9/9`** "
                 "`bcdace84a0352b4a` x2; harness 12/12 `[]`."),
        "rows": [
            ("census: 97 refs name 0xa40 = 25 indexed (12 fns) + 72 field, all dword (47 stores / "
             "25 reads); 0 `lea ..+0xa40`, 0 `,0xa40` immediate", "`evidence/m343_a40_writer.txt:5-22`", "V MU1"),
            ("writers: FUN_005f5759 x4, FUN_005f58fa x3, FUN_005f5a11 x2 (ds:0x9977f0); runner "
             "FUN_005f1394 = 1 read, 0 stores; ctor FUN_00405ef0 0 refs", "`:66-77`,`:24-26`", "V MU4,MU5,MU2"),
            ("receiver fingerprint = {[+0x21d0] container, [+0x2350] state}: exactly 4 fns; the "
             "'>=3 of {21d0,2350,30a8,3100}' rival admits 2 more", "`:28-64`", "V MU3,MU9"),
            ("identity chain 0x5f13b2 -> 0x5f3f45 `[ebp-0x394]+0xa40`; 5a11 reloads ds:0x9977f0 "
             "and both stores reach it (10 links, adjacency asserted)", "`:79-88`", "V MU7,MU10"),
            ("value law: each writer publishes {0, `[this+0x2228]->[+8]->+0xec`, "
             "`FUN_005fdcf7(+0x21d0)`}; the -1 @0x5f581c needs arg==-2 and `[+0x30a8]&0x40`", "`:89-99`", "V MU6,MU8,MU11"),
            ("OPEN: dispatcher of the +0x64 slot (19 `call [reg+0x64]`, 0 direct); the container "
             "past +0xec; consumers of `[this+0x3100]`", "-", "lead"),
        ],
    },
    {
        "head": "## M345 ",
        "archive": "named-archive-m345-rows.md",
        "note": ("acceptance `m345_slot64_dispatch` -> **`PASS M345: 12/12`** `833faf38e189ad40` x2; "
                 "harness 11/11 `[]`."),
        "rows": [
            ("slot `0x5f58fa` = 5 data dwords, all a family vt+0x64; 0 `.text` operands",
             "`evidence/m345_slot64_dispatch.txt:3-10`", "V MU1,MU3,MU2"),
            ("ctor 0x405ef0: 0x67164c at +0, CPane 0x671644 at +0x444 -> its `+0x6c` IS the primary `+0x64`",
             "`:16,:93`", "V MU1,MU4"),
            ("trio `+0x60`/`+0x64`/`+0x68` = 5f59bf ret8 / 5f58fa ret4 / 5f59e8", "`:12-15`", "V MU5"),
            ("universe = 19 `[r+0x64]` + 18 `[r+0x6c]` calls, 0 jmp, 0 in the dialog module",
             "`:18-57,:86-89`", "V MU6,MU10"),
            ("arity {0:3,1:5,5:8,6:3}: 5 fit ret 4 = 3 MEMBER + 2 self, none a dialog", "`:59-65,:100`", "V MU8,MU9"),
            ("module's 4 `[r+0x64]` are movs; 5f49ad/b9 swaps `[this+0x2240]+0x64`", "`:67-77,:102`", "V MU7,MU10"),
            ("OPEN: MEMBER-receiver classes (+0xf624/+0xd9ec/+0x3870/+0x270c) untyped", "-", "lead"),
        ],
    },
]


def bounds(lines, head):
    start = None
    for i, l in enumerate(lines):
        if l.startswith(head):
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
    lines = named.split("\n")
    for blk in BLOCKS:
        path = os.path.join(ROOT, "docs", blk["archive"])
        arch = open(path).read()
        body = (arch.split(SENT + "\n", 1)[1] if SENT in arch else "").rstrip("\n")
        h = sha1(body)
        s, e = bounds(lines, blk["head"])
        stub = lines[s:e] if s is not None else []
        hi = None
        for line in stub[:3]:
            if "sha1 `" in line:
                hi = line.split("sha1 `")[1].split("`")[0]
        ha = None
        for line in arch.splitlines()[:4]:
            if "sha1 `" in line:
                ha = line.split("sha1 `")[1].split("`")[0]
        n_rows = sum(1 for l in stub if l.startswith("| ") and "---" not in l
                     and not l.startswith("| claim"))
        good = h.startswith(hi or "-") and ha == h and n_rows == len(blk["rows"]) \
            and "stub governs" in "\n".join(stub)
        print("%-10s %s sha1 %s (%d B) stub %d/%d" % (
            blk["head"].strip(), "PASS" if good else "FAIL", h[:16],
            len(body.encode()), n_rows, len(blk["rows"])))
        ok = ok and good
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def rotate():
    named = open(NAMED).read()
    lines = named.split("\n")
    for blk in BLOCKS:
        s, e = bounds(lines, blk["head"])
        if s is None:
            print("%s not found" % blk["head"].strip())
            return 1
        block = "\n".join(lines[s:e]).rstrip("\n")
        path = os.path.join(ROOT, "docs", blk["archive"])
        if "stub governs" in block or os.path.exists(path):
            print("%s already rotated" % blk["head"].strip())
            continue
        h = sha1(block)
        with open(path, "w") as f:
            f.write("# NAMED.md `%s` - ROTATED VERBATIM (byte-exact) by "
                    "scripts/m348_named_rotate.py\n\nrotated by `scripts/m348_named_rotate.py`; "
                    "sha1 `%s` of the block below.\n%s\n%s\n"
                    % (blk["head"].strip(), h, SENT, block))
        stub = [lines[s].rstrip(), "",
                "ROTATED VERBATIM to `docs/%s` (sha1 `%s`); this stub governs: one line per claim; %s"
                % (blk["archive"], h[:16], blk["note"]), "",
                "| claim (one line each; full rows in the archive) | evidence | conf |", "|---|---|---|"]
        stub += ["| %s | %s | %s |" % (a, b, c) for a, b, c in blk["rows"]]
        lines = lines[:s] + stub + lines[e:]
        print("%s rotated %d B -> %s (sha1 %s)" % (blk["head"].strip(), len(block.encode()),
                                                   blk["archive"], h[:16]))
    out = "\n".join(lines)
    with open(NAMED, "w") as f:
        f.write(out)
    print("NAMED now %d B" % len(out.encode()))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    sys.exit(verify() if a.verify else rotate())
