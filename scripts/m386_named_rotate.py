#!/usr/bin/env python3
"""m386_named_rotate.py - move NAMED.md's settled `## M342` block VERBATIM into
`docs/named-archive-m342-rows.md` and leave a one-line-per-claim stub in NAMED.

M386 must add a block and NAMED.md is 247,287 B against the 250,000 B FAIL (2,713 B of headroom,
under the 5 KB trigger).  M342 (s322-chain1) is a settled ANALYSE unit whose mutation-tested rows
are superseded by later rounds; its citations are carried into the stub so a grep of NAMED still
lands on a file:line.

    python3 scripts/m386_named_rotate.py            # rotate (idempotent if already done)
    python3 scripts/m386_named_rotate.py --verify   # sha1 byte-exactness + claim tokens
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m342-rows.md")
HEAD = "## M342 (s322-chain1"
ARCHIVE_HEAD = "# NAMED.md `## M342` - ROTATED VERBATIM (byte-exact) by scripts/m386_named_rotate.py\n"

STUB = """## M342 (s322-chain1, ANALYSE) - ROTATED VERBATIM to `docs/named-archive-m342-rows.md` (sha1 `%s`): the `base+0x8c` bit is SET by `or` through the mapper's mask at 11 addresses, the API `FUN_004e44f0` first; the queue-pop is a NON-writer. One line per claim, full rows in the archive.
- RECORD BASE `0x95da10` derived from 0x440dbc (`imul 0x130`); `0x95da9c` = rec+0x8c, matches the charge read 0x4f4837 - V MU1 (`evidence/m342_completion_setter.txt:4-8`)
- 2 writer idioms: 11 const-form stores in `FUN_0041cf20`/`FUN_004e47d0`, 9 `lea` sites 9/9 resolved - V MU2/MU8 (`evidence/m342_completion_setter.txt:9-72`, `evidence/m342_completion_setter.txt:86`, `evidence/m342_completion_setter.txt:204`)
- SET 11 `or` (4e4528 4e4b5a 4e4b87 4e4bec 4e4c16 4e4c3d 4e4c83 4e4d81 4f0ec0 4f3ebc 4f3f4c); CLEAR 3 `and` (4e4546 4f38bb 4f49e1) - V MU2/MU8 (`evidence/m342_completion_setter.txt:210-216`)
- API `FUN_004e44f0` = first SET 0x4e4528 (304-fold, out1 slot/out2 mask); AND twin 0x4e4546 - V MU3 (`evidence/m342_completion_setter.txt:99-113`, `evidence/m342_completion_setter.txt:205`)
- 27 call sites / 8 fns: 16 set=1, 8 set=0, 3 variable (M344 16-insn window) - V MU4 (`evidence/m342_completion_setter.txt:129-158`, `evidence/m342_completion_setter.txt:206`, `evidence/m344_completion_caller.txt:36-38`)
- queue-pop `FUN_004ef5d0`: 0 refs to `0x95da9c`, 0 API calls - V MU5 (`evidence/m342_completion_setter.txt:160-177`, `evidence/m342_completion_setter.txt:207`)
- inline grant `FUN_004e47d0`: 7 ORs + 3 copies, 7/7 masks from a stack slot - V MU6 (`evidence/m342_completion_setter.txt:180-191`, `evidence/m342_completion_setter.txt:208`)
- printed digest PINNED by G7 - V MU7 (`evidence/m342_completion_setter.txt:200`, `evidence/m342_completion_setter.txt:209`)
- ACCEPT `scripts/m342_completion_setter.py` 7/7 `2b88df5da5aeafe1` x2; harness 9/9, NO-OP [] - V (`evidence/m342_mutate.txt:2`, `evidence/m342_mutate.txt:12`)
- OPEN: the production-completion call site; 3 pointer writers 0x4f38b0/0x4f3eb1/0x4f3f3e; projects 39..71 unmeasured - lead
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
            raise SystemExit("FAIL: no sha1 in the M342 stub")
        if sha1(body) != m.group(1):
            raise SystemExit("FAIL: archived block sha1 != stub sha1 (%s vs %s)"
                             % (sha1(body), m.group(1)))
        claims = [ln for ln in body.splitlines()
                  if ln.startswith("| ") and not ln.startswith("|---") and "| claim |" not in ln]
        bullets = [ln for ln in stub.splitlines() if ln.startswith("- ")]
        if len(bullets) != len(claims):
            raise SystemExit("FAIL: stub carries %d claim bullets for %d archived rows"
                             % (len(bullets), len(claims)))
        refs = sorted({"%s:%s" % (f, ln) for c in claims
                       for f, ln in re.findall(r"([\w/\.\-]+\.txt):([0-9]+(?:-[0-9]+)?)", c)})
        missing = [r for r in refs if r not in stub]
        if missing:
            raise SystemExit("FAIL: stub drops the archived full citations %s" % missing)
        bare = re.findall(r"`:(?:\d[0-9,\-]*)`", stub)
        if bare:
            raise SystemExit("FAIL: stub carries bare section-relative cites %s" % bare)
        print("PASS m386_named_rotate --verify: sha1 %s, %d archived claim rows == %d stub bullets, "
              "%d full path:line cites carried, 0 bare"
              % (m.group(1), len(claims), len(bullets), len(refs)))
        return 0

    if "ROTATED VERBATIM by scripts/m386_named_rotate.py" in named:
        print("M342 already rotated; nothing to do")
        return 0
    blk = block(named, HEAD)
    if "ROTATED VERBATIM" in blk:
        raise SystemExit("FAIL: %s is already a stub - refusing to rotate a stub" % HEAD)
    stub = STUB % sha1(blk)
    if len(stub.encode()) > 2400:
        raise SystemExit("FAIL: stub is %d B" % len(stub.encode()))
    open(ARCHIVE, "w", encoding="utf-8").write(ARCHIVE_HEAD + "\n" + blk)
    open(NAMED, "w", encoding="utf-8").write(named.replace(blk, stub + "\n", 1))
    print("rotated %s: %d B -> archive %d B, stub %d B"
          % (HEAD.strip(), len(blk.encode()), len(blk.encode()), len(stub.encode())))
    print("sha1 %s" % sha1(blk))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
