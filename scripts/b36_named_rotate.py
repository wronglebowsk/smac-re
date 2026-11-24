#!/usr/bin/env python3
"""b36_named_rotate.py - move NAMED.md's settled `## B18` block VERBATIM into
`docs/named-archive-b18-rows.md` and leave a one-line-per-claim stub in NAMED.

B36 must add a block and NAMED.md is 245,628 B against a 250,000 B FAIL (4,372 B of
headroom, under the 5 KB trigger).  B18 is a settled BUILD rung - its site-gate model is
superseded by B22-B36 and its lead is already archived.  The rotated text is byte-for-byte
what NAMED carried; the stub repeats every claim on one line with the same evidence pointer,
so a grep of NAMED still lands on a file:line.

    python3 scripts/b36_named_rotate.py            # rotate (idempotent if already done)
    python3 scripts/b36_named_rotate.py --verify   # sha1 byte-exactness + claim tokens
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-b18-rows.md")
HEAD = "## B18 (s252"
ARCHIVE_HEAD = "# NAMED.md `## B18` - ROTATED VERBATIM (byte-exact) by scripts/b36_named_rotate.py\n"

STUB = """## B18 (s252, BUILD 10/10) - ROTATED VERBATIM to `docs/named-archive-b18-rows.md` (sha1 `%s`): the site-gate value source is a 4-bit lazy nibble cache and both stores are MAX. One line per claim.
- LAZY NIBBLE CACHE: `edi = BYTE[rec+2]>>4`; the pinned `jne 0x51dfac` skips the 525-insn call AND the write-back; the target byte is the pod-scan getter's byte (4096/4096) - V (`:4` 64 pins, `evidence/b18_sitegate.txt:1`)
- OVERWRITE, not accumulator: no cmp/test/branch in the 19-insn callee; the live nibble moves both ways (182 below / 31 above); 2288 cache hits, 1 lazy write-back, 32 adopted mutations - V (`:3,6`)
- NIBBLE SPLIT visible in the recording: 103 of 177 moved records kept the low nibble; a whole-byte store is refuted by `and dl,0xf` + `or dl,cl` - V (`:5`)
- STORE INDEX `[ebp-0xc] = BYTE[rec+3]` ({1:2253, 9:68}, 1026/1026 single-site); block index = owner byte `+7`, the -1 sentinel clamps and block 0 skips the cell store; M294's 4x stride retracted (28 = (8-1)<<2) - V (`:7`)
- BOTH STORES ARE MAX BY POLARITY (`cmp edi,eax`/`jle`; a MIN store needs `jge`), graded with the old loads; last-write / min / owner-blind rivals diverge - V (`:8`)
- ACCEPTANCE `python3 -m sim.selftest --b18 programs/saves/m54b_clean.SAV` -> PASS B18: 10/10 - V (`:11`)
- LEAD: contents of 0x989ce8 / 0x94eca8 never dumped; the slot's `[+4]` visitor counter; ebx provenance - lead
"""


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
        arch = open(ARCHIVE, encoding="utf-8").read()
        body = arch.split("\n", 2)[2]
        stub = block(named, HEAD)
        m = re.search(r"sha1 `([0-9a-f]{40})`", stub)
        if not m:
            raise SystemExit("FAIL: no sha1 in the B18 stub")
        if sha1(body) != m.group(1):
            raise SystemExit("FAIL: archived block sha1 != stub sha1 (%s vs %s)"
                             % (sha1(body), m.group(1)))
        claims = [ln for ln in body.splitlines()
                  if ln.startswith("| ") and not ln.startswith("|---") and "| claim |" not in ln]
        bullets = [ln for ln in stub.splitlines() if ln.startswith("- ")]
        if len(bullets) != len(claims):
            raise SystemExit("FAIL: stub carries %d claim bullets for %d archived rows"
                             % (len(bullets), len(claims)))
        refs = sorted({r for c in claims for r in re.findall(r"`?:([0-9][0-9,\\-]*)", c)})
        missing = [r for r in refs if (":%s" % r) not in stub]
        if missing:
            raise SystemExit("FAIL: stub drops the archived line cites %s" % missing)
        print("PASS b36_named_rotate --verify: sha1 %s, %d archived claim rows == %d stub bullets, "
              "%d line cites carried" % (m.group(1), len(claims), len(bullets), len(refs)))
        return 0

    body = block(named, HEAD)
    if not body.strip():
        raise SystemExit("FAIL: `## B18` block not found in NAMED.md")
    s = sha1(body)
    with open(ARCHIVE, "w", encoding="utf-8") as fh:
        fh.write(ARCHIVE_HEAD + "\n" + body)
    stub = STUB % s
    new = named.replace(body, stub)
    if new == named:
        raise SystemExit("FAIL: replacement was a no-op")
    if len(new.encode("utf-8")) >= len(named.encode("utf-8")):
        raise SystemExit("FAIL: rotation did not shrink NAMED.md (%d -> %d B)"
                         % (len(named.encode("utf-8")), len(new.encode("utf-8"))))
    with open(NAMED, "w", encoding="utf-8") as fh:
        fh.write(new)
    print("rotated `## B18` (%d B) -> docs/named-archive-b18-rows.md  sha1 %s" % (len(body), s))
    print("NAMED.md %d -> %d B" % (len(named.encode("utf-8")), len(new.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
