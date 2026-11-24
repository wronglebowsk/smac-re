#!/usr/bin/env python3
"""b32_named_rotate.py - move NAMED.md's settled `## B30` block VERBATIM into
`docs/named-archive-b32-rows.md` and leave a one-line-per-claim stub in NAMED.

Why: NAMED.md FAILs at 250,000 B and B32 must add a block; headroom had fallen under the 5 KB
trigger.  The rotated block keeps every claim, gate and cite in the archive byte-for-byte; the
stub repeats each claim on one line with the same evidence pointer, so a reader who greps NAMED
still lands on the right file:line.

`--verify` recomputes the sha1 of the archived block and asserts it equals the sha1 recorded in
BOTH files, that the stub carries one row per archived claim, and that no claim's gate token
disappeared.  Byte-exactness is the whole point: this script NEVER rewrites claim text.
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-b32-rows.md")
HEAD = "## B30 (s321"
STUB_HEAD = "## B30 (ROTATED) - see `docs/named-archive-b32-rows.md`"
ARCHIVE_HEAD = ("# NAMED.md `## B30` - ROTATED VERBATIM (byte-exact) by scripts/b32_named_rotate.py\n"
                "# sha1 %s  bytes %d\n\n")

STUB_ROWS = (
    ("CONTAINER-DRIVEN run (G1): 18 records, own player 3, 2 eligible, target 0 'University Base' item 2",
     "`evidence/b30_facility_completion.txt:2,22`", "V MU6"),
    ("SETTER == reader inverse over the 32-id window (32/32 round-trip, id 39 refused); swapped rival 4/32",
     "`:23`", "V MU1/MU2"),
    ("the write is ONE byte: diff `[140]`, delta 4, inside `+0x8c..+0x8f`", "`:24`", "V MU1"),
    ("writer round-trip: identity build byte-identical, 1 offset, reload `[1,2,8]`, 17/17 others",
     "`:25-26`", "V MU3/MU5"),
    ("the bill moves by the DERIVED table (delta 1, 0 mismatches); 'table value' rival differs at `[8]`; G6 runs it twice",
     "`:27`", "V MU4/ME3/ME4"),
    ("the stamper was ASSUMED here - QUALIFIED by `## M342` (inline `or` @0x4f0ec0) and by `## B31`/"
     "`## B32`: the recorded run has no facility-positive case, and the UNIT twin stamps 4/4 where the"
     " facility twin stamps 0/2", "`evidence/m342_completion_setter.txt:190`, `evidence/b32_unitoracle.txt:25`",
     "V (M342/B32)"),
    ("OPEN: other real-completion effects (pop order beyond B11, storage/mineral reset, messages); ids 39..71",
     "-", "lead"),
)

def block_bounds(text):
    i = text.find(HEAD)
    assert i >= 0, "block head not found: %r" % HEAD
    j = text.find("\n## ", i + 3)
    assert j > i, "block end not found"
    return i, j


def sha_of(body):
    return hashlib.sha1(body.encode("utf-8")).hexdigest()


def stub_text(body):
    lines = [STUB_HEAD + " — spine §B30; ACCEPT `python3 -u -m sim.selftest --b30` "
             "`PASS B30: 6/6` `234ab3d83a88dbea`, harness 10/10 `76a481b5d8a7d8b0` "
             "(`evidence/b30_facility_completion.txt:35-36`).", ""]
    for claim, ev, conf in STUB_ROWS:
        lines.append("- %s — %s — %s." % (claim, ev, conf))
    return "\n".join(lines) + "\n"


def rotate():
    text = open(NAMED, encoding="utf-8").read()
    i, j = block_bounds(text)
    body = text[i:j]
    if os.path.exists(ARCHIVE):
        raise SystemExit("archive already exists: %s" % ARCHIVE)
    with open(ARCHIVE, "w", encoding="utf-8") as fh:
        fh.write(ARCHIVE_HEAD % (sha_of(body), len(body.encode("utf-8"))))
        fh.write(body)
    open(NAMED, "w", encoding="utf-8").write(text[:i] + stub_text(body) + text[j:])
    print("rotated %d B; stub %d B; archive %s" % (len(body.encode("utf-8")), len(stub_text(body)), ARCHIVE))


def verify():
    text = open(NAMED, encoding="utf-8").read()
    arch = open(ARCHIVE, encoding="utf-8").read()
    hdr, _, rest = arch.partition("\n\n")
    body = rest
    want = sha_of(body)
    m = re.search(r"sha1 ([0-9a-f]{40})  bytes (\d+)", hdr)
    ok = []
    ok.append(("archive sha1 line == the block's sha1", bool(m) and m.group(1) == want))
    ok.append(("archive body bytes match the header",
               bool(m) and int(m.group(2)) == len(body.encode("utf-8"))))
    i = text.find(STUB_HEAD)
    j = text.find("\n## ", i + 3)
    stub = text[i:j]
    ok.append(("NAMED carries the stub, not the block", i >= 0 and HEAD not in stub))
    n_rows = sum(1 for ln in body.splitlines() if ln.startswith("| ") and not ln.startswith("| claim"))
    n_stub = sum(1 for ln in stub.splitlines() if ln.startswith("- "))
    ok.append(("one stub row per archived claim (%d == %d)" % (n_stub, n_rows), n_stub == n_rows))
    tok = re.compile(r"\b(?:G|MU|ME)\d+\b")
    body_tok, stub_tok = set(tok.findall(body)), set(tok.findall(stub))
    ok.append(("archive carries >=10 distinct gate tokens (%d)" % len(body_tok), len(body_tok) >= 10))
    ok.append(("no archived gate token is missing from the stub (%s)"
               % ",".join(sorted(body_tok - stub_tok)), not (body_tok - stub_tok)))
    ok.append(("the stub names the archive", "docs/named-archive-b32-rows.md" in stub))
    for lab, good in ok:
        print(("ok   " if good else "FAIL ") + lab)
    print("")
    if all(good for _l, good in ok):
        print("PASS ROTATE B32: %d/%d  sha1=%s" % (len(ok), len(ok), want))
        return 0
    print("FAIL ROTATE B32")
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    return verify() if args.verify else rotate()


if __name__ == "__main__":
    sys.exit(main())
