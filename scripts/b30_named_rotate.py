#!/usr/bin/env python3
"""B30 headroom rotation: move the settled M310 block VERBATIM out of NAMED.md.

NAMED.md sat at 246,635 B (3,365 B under its 250,000 B cap - inside the kickoff's 5 KB
rotate-first trigger) and this round must add a block, so the M310 block (settled: s272,
static, mutation-tested 14/14, no rung cites it) moves byte-exactly into
`docs/named-archive-b30-rows.md` and NAMED.md keeps a stub with ONE LINE PER CLAIM, same
gates, mutants and cites.  The moved region's sha1 is PINNED here and `--verify` re-asserts
it, so a later edit to either copy fails loudly instead of forking the registry.

  python3 scripts/b30_named_rotate.py            # do the move (idempotent no-op once done)
  python3 scripts/b30_named_rotate.py --verify   # re-assert sha1 + the full block's absence
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-b30-rows.md")
EXPECT_SHA1 = "ca3caf3785c9d6e91239fbff7d92f53fa733fcd1"
START = "## M310 (s272, STATIC, zero box"
END = "## B22 (s273, BUILD 12/12"
FULL_HEAD = "## M310 (s272, STATIC, zero box; mutation-tested) - FUN_00470b90 is the view object's"
HEADER = ("# NAMED archive - B30 headroom rotation (s321): the M310 block VERBATIM\n"
          "(moved by `scripts/b30_named_rotate.py`; the region's sha1 is pinned to `%s` -\n"
          "run `--verify` after any edit; NAMED.md's stub keeps one line per claim)\n\n"
          % EXPECT_SHA1)

STUB = """## M310 (s272, STATIC, zero box; mutation-tested 14/14) — `FUN_00470b90` = the view object's DEBUG-GATED GOAL duplicate-invalidator + one-char-token logger; it owns the GOAL kind<->token map. FULL-LENGTH TABLE VERBATIM at `docs/named-archive-b30-rows.md:5` (sha1 `ca3caf3785c9d6e9`); this stub governs, one line per claim

| claim | evidence | conf |
|---|---|---|
| entry gate is the FIELD bit `and ecx,0x2000` on `[eax+0x1dd70]` (stowed this-pointer), landing on the single epilogue (`1` ret in 1020 B @0x470f89, `ret 0x8`) -> inert without the bit = diagnostics, not rules | `evidence/m310_goal_invalidator.txt` S2/S1 | V |
| loop nest blocks 1..7, filter `(ds:0x985ae8 & 0x80) \\|\\| block == ds:0x91b5b4`, scan bound `0x4b` = the 75-entry GOAL list (15 `imul r,r,0x20bc` 1:1 with 15 `shl r,0x4`; entry offsets touched {+0,+2,+4,+8} only) | `:S3,S4` | V |
| hit predicate `p1 == entry+4` && `p2 == entry+8` && `movsx kind >= 0` && `movsx prio != 0`; prio > 0 goes straight to the log tail with NO store | `:S4` | V |
| invalidation law: negative prio scans j != i for the same (p1,p2) AND `kind[j] == kind[i]` (folds re-seeded, encoding is the arbiter); the `0xffff` store is the only WORD store to +0 and writes entry i (0x470d5c); +2 has no store | `:S6` | V |
| post-store re-read (`movsx`+`test`/`jge 0x470d86`) skips negative kinds before the log tail | `:S6` | V |
| log tail call order: `FUN_00403a40` -> `FUN_00407520` -> `FUN_00423c20(block)`+`FUN_00405220` -> `BYTE ds:0x997121 = 0` -> token appends x8 -> `FUN_004237f0(abs prio)` -> 2 vtable calls -> `FUN_004081b0(ds:0x997120, buf)`; 9 targets == index.csv | `:S9,S11` | V (buffer's consumer OPEN) |
| kind->token map read from the PE BYTES (objdump misassembles both): dword table @0x470f8c = 8 handlers, 42-byte index @0x470fac behind `cmp [ebp-30],0x29 / ja`; tokens 0->'a',2->'d',3->'s',6->'n',8->'c',9->'f',41->'^'; kinds 1,4,5,7,10..40 + default share 0x470eb7 (pushes nothing) - the C's case list AGREES with the bytes | - (the source row carried NO cite) | INFERRED |
| args are a (p1,p2) COORDINATE pair: 5 call sites, each forwarding 2 closed stack slots; **CORRECTED by M312: all 4 forwarder sites push arg4=0 into the 0x471050 tail guard, so the site-1 path never executes -- see ## M312** | `:S5` | V (coordinate system INFERRED) |
| gates load-bearing: `scripts/m310_mutate.py` = 14/14, every mutant reddening its named check, the harness requiring the unmutated instrument to exit 0 and rejecting tracebacks | `evidence/m310_mutate.txt:17,18` | V |
| OPEN: GOAL semantics and the token alphabet; WHY a negative priority is the invalidation trigger; what `this+0x1ddb4/1ddb8` hold; what consumes `ds:0x997120`; save-carry of the GOAL list | - | lead |"""


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def region_of(text):
    """The block's bytes: START up to END in NAMED, START to EOF in the archive (the archive
    is header + region only, so its region has no successor heading)."""
    a = text.index(START)
    if END not in text[a:]:
        return text[a:]
    b = text.index(END)
    if b <= a:
        raise AssertionError("%r does not precede %r" % (START, END))
    return text[a:b]


def verify():
    named = open(NAMED, encoding="utf-8").read()
    arch = open(ARCHIVE, encoding="utf-8").read()
    reg = region_of(arch)
    ok_sha = sha1(reg.encode()) == EXPECT_SHA1
    ok_absent = FULL_HEAD not in named
    ok_stub = STUB.splitlines()[0] in named and "sha1 `%s`" % EXPECT_SHA1[:16] in named
    ok_pointer = "docs/named-archive-b30-rows.md:5" in named
    rows = lambda t: sum(1 for ln in t.splitlines()
                         if ln.startswith("| ") and not ln.startswith("| claim")
                         and not set(ln) <= set("|- "))
    ok_rows = rows(reg) == rows(STUB)
    print("archive region %d B sha1 %s pinned %s -> %s"
          % (len(reg.encode()), sha1(reg.encode())[:16], EXPECT_SHA1[:16],
             "PASS" if ok_sha else "FAIL"))
    print("full block absent from NAMED -> %s" % ("PASS" if ok_absent else "FAIL"))
    print("stub present with the pin -> %s" % ("PASS" if ok_stub else "FAIL"))
    print("stub's cite resolves -> %s" % ("PASS" if ok_pointer else "FAIL"))
    print("stub projects one row per archived claim (%d/%d) -> %s"
          % (rows(STUB), rows(reg), "PASS" if ok_rows else "FAIL"))
    return 0 if (ok_sha and ok_absent and ok_stub and ok_pointer and ok_rows) else 1


def main(argv):
    if "--verify" in argv:
        return verify()
    named = open(NAMED, encoding="utf-8").read()
    if START not in named:
        print("NAMED already rotated (the full M310 block is absent); verifying")
        return verify()
    reg = region_of(named)
    if sha1(reg.encode()) != EXPECT_SHA1:
        raise SystemExit("M310 region sha1 %s != pinned %s - refusing to move an edited block"
                         % (sha1(reg.encode()), EXPECT_SHA1))
    with open(ARCHIVE, "w", encoding="utf-8") as fh:
        fh.write(HEADER + reg)
    open(NAMED, "w", encoding="utf-8").write(named.replace(reg, STUB + "\n\n"))
    print("moved %d B to %s; NAMED now %d B"
          % (len(reg.encode()), os.path.basename(ARCHIVE), len(open(NAMED, "rb").read())))
    return verify()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
