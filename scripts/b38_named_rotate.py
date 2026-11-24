#!/usr/bin/env python3
"""b38_named_rotate.py - move NAMED.md's settled `## B3` and `## B4` blocks VERBATIM into
`docs/named-archive-b3-b4-rows.md` and leave one-line-per-claim stubs in NAMED.

B38 must add a block and NAMED.md is 247,287 B against a 250,000 B FAIL (2,713 B of headroom,
under the 5 KB trigger).  B3 (`sim/turn.py`) and B4 (`sim/base.py`/`sim/economy.py`) are
settled BUILD rungs: every claim is superseded by B5-B37 and their numbers survive in
`evidence/b3_turn_replay.txt` / `evidence/b4_economy.txt`, which stay put.  The rotated text is
byte-for-byte what NAMED carried; each stub repeats every claim on one line with the same gate
id and the same `path:line`, so a grep of NAMED still lands on a file:line.

    python3 scripts/b38_named_rotate.py            # rotate (idempotent if already done)
    python3 scripts/b38_named_rotate.py --verify   # sha1 byte-exactness + claim tokens
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-b3-b4-rows.md")
ARCHIVE_HEAD = ("# NAMED.md `## B3` + `## B4` - ROTATED VERBATIM (byte-exact) by "
                "scripts/b38_named_rotate.py\n\n")

STUBS = {
    "## B3 ": """## B3 (s199, BUILD 6/6) - ROTATED VERBATIM to `docs/named-archive-b3-b4-rows.md` (sha1 `%s`): `sim/turn.py` replays M30's turn trace. One line per claim, same gates and `path:line`:
- parity rule = ORDERED SUBSEQUENCE (the trace is a 0.2 s change-set sample): matched 67/67, 220 emitted, 154 collapsed, 11/cycle - G1/G2 V (`evidence/b3_turn_replay.txt:2`)
- the engine walks the 8 faction slots ASCENDING; our slot 3 is the only slot where tf==0 is ever seen (21 rows, all cur==3; own==3 in 67/67) - G1/G2 V (`evidence/b3_turn_replay.txt:1-2`)
- the YEAR fires on the 7->0 edge while `cur` is still 7 (witness row 22 = t 88.631, cur 7, tf 2, year 2221); the other 7 edges score 22,22,10,0,0,0,6 /66 - G3 V (`evidence/b3_turn_replay.txt:3`)
- `tf` clears ONE STEP AFTER `cur_player`=3 (merged: 5/66); the 4 (3,2) rows are 5,14,23,40 - G4 V (`evidence/b3_turn_replay.txt:4`)
- 48 of 322,560 order x year-edge models reproduce the trace = 6 cyclic orders x 8 rotations; only {4,5,6}'s internal order is free - G5 V (`evidence/b3_turn_replay.txt:5`)
- 20 presses = 20 year bumps = 20 tf clears, 2213->2233, final (3,0,2233) == last row - G6 V (`evidence/b3_turn_replay.txt:6`)
- OPEN: the press transition (3,0)->(3,2) is unobservable (no_press variant still 66/66); `nb` (0x985AF4, 51->58) unmodelled - OPEN (cursor)
- instrument: `python3 -m sim.selftest --replay evidence/m30_turn_trace.jsonl` -> `PASS B3: 6/6 gates`, rc=0, 22.3 s, one invocation - V
""",
    "## B4 ": """## B4 (s203, BUILD 9/9) - ROTATED VERBATIM to `docs/named-archive-b3-b4-rows.md` (sha1 `%s`): `sim/base.py` + `sim/economy.py`, the round economy. One line per claim, same gates and `path:line`:
- base record: owner byte +4, pop +6, growth +7, name +19 (NUL, 32 B), storage +0x40, queue id +0x50, facility bitmap +0x8c, totals +0xc4/+0xd4/+0xe4/+0xf4, GROSS bucket +0xfc, others +0x100/+0x104/+0x108 - G4 13/13 V (`evidence/b4_economy.txt:20`)
- the name field is 32 B not 20 (names to 22 chars; `scripts/m46_econ.py:106` truncates); 0/311 records lack a NUL in 32 B - G5 V (`evidence/b4_economy.txt:21`)
- faction round: gross = sum base+0xfc; upkeep = sum per-facility alpha `#FACILITIES` col 3 at (id-1), 0 if disabled; net = gross - upkeep; energy' = max(0, energy+net-ledger) - G6 reproduces the HUD (2,2,0) both rounds, 19->19 V (`evidence/b4_economy.txt:22`)
- the aggregator also writes per-base upkeep 0x744f2c (75) and 39-wide item counts 0x745738; reproduced exactly - G7 V (`evidence/b4_economy.txt:23`)
- item upkeep for ids 1/3/6/7/8 = 0,0,1,1,1; sum 3 raw, 2 with item 8 disabled = recorded 0x744f28 - G8 V (`evidence/b4_economy.txt:24`)
- the model is the only one of four matching the recorded triple (no disabled list 2,3,-1; gross from +0x100 0,2,-2; alpha without the +1) - G9 V (`evidence/b4_economy.txt:25`)
- idle PRE-FOUNDING faction nets 0: 0 bases, energy 15 flat on 12/12 rounds; HUD reads 0/turn on all 3 legible rounds - G1-G3 V (`evidence/b4_economy.txt:17-19`)
- ANSWERED by B29: M46's live table is alpha-INDEX numbering (rec i = alpha row i-1), order IS alpha's for ids 1..38 - B29 G3 38/38 V (`evidence/b29_item_table.txt:78`); still OPEN: bitmap width past +0x8f; gifts and spending-ledger terms - OPEN
- instrument: `python3 -m sim.selftest --replay evidence/m44d_idle.json` -> `PASS B4: 9/9 gates`, rc=0, 1.3 s (invocation 1 failed 8/9 on the name width - that was the finding) - V
""",
}


def block(text, head):
    lines = text.splitlines(keepends=True)
    start = next(i for i, ln in enumerate(lines) if ln.startswith(head))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "".join(lines[start:end])


def sha1(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args(argv)
    named = open(NAMED, encoding="utf-8").read()

    if args.verify:
        arch_lines = open(ARCHIVE, encoding="utf-8").read().splitlines(keepends=True)
        ok = True
        for head, stub_t in STUBS.items():
            tag = head.split()[1]
            beg = "<<<%s\n" % tag
            endm = "%s>>>\n" % tag
            try:
                i = arch_lines.index(beg) + 1
                j = arch_lines.index(endm, i)
            except ValueError:
                print("FAIL: archive has no %s sentinel pair" % tag)
                return 1
            body = "".join(arch_lines[i:j])
            stub = block(named, head)
            m = re.search(r"sha1 `([0-9a-f]{40})`", stub)
            if not m:
                print("FAIL: no sha1 in the %s stub" % tag)
                return 1
            if sha1(body) != m.group(1):
                print("FAIL: %s archived block sha1 != stub sha1 (%s vs %s)"
                      % (tag, sha1(body), m.group(1)))
                ok = False
            for tok in re.findall(r"`([^`]*(?:evidence|NAMED|scripts)[^`]*)`", stub):
                if tok and tok not in "".join(arch_lines):
                    print("FAIL: %s stub token %r not in archive" % (tag, tok))
                    ok = False
            claims = len([ln for ln in stub.splitlines() if ln.startswith("- ")])
            print("%s: archived %d B sha1 %s, stub %d B, %d claim lines"
                  % (tag, len(body.encode()), sha1(body), len(stub.encode()), claims))
        print("VERIFY %s" % ("PASS" if ok else "FAIL"))
        return 0 if ok else 1

    if os.path.exists(ARCHIVE) and "## B3" in open(ARCHIVE, encoding="utf-8").read():
        print("already rotated; nothing to do (run --verify)")
        return 0

    out = [ARCHIVE_HEAD]
    new_named = named
    for head, stub_t in STUBS.items():
        body = block(new_named, head).rstrip("\n") + "\n"
        tag = head.split()[1]
        digest = sha1(body)
        out.append("<<<%s\n" % tag + body + "%s>>>\n" % tag)
        new_named = new_named.replace(block(new_named, head), stub_t % digest, 1)
        print("rotated %s: %d B -> %d B stub, sha1 %s"
              % (tag, len(body.encode()), len((stub_t % digest).encode()), digest))
    open(ARCHIVE, "w", encoding="utf-8").write("".join(out))
    open(NAMED, "w", encoding="utf-8").write(new_named)
    print("NAMED.md %d B (was %d B)" % (len(new_named.encode()), len(named.encode())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
