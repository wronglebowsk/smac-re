#!/usr/bin/env python3
"""B29 headroom rotation: move the settled M334 block VERBATIM out of NAMED.md.

NAMED.md hit 247,758 B (2.2 KB under its 250,000 B cap) and this rung must add a block, so the
M334 block (settled: merged #350, its review round closed) moves byte-exactly into
`docs/named-archive-b29-rows.md` and NAMED.md keeps a stub with ONE LINE PER CLAIM, same gates,
mutants and cites.  The moved region's sha1 is PINNED here and `--verify` re-asserts it, so a
later edit to either copy fails loudly instead of forking the registry.

  python3 scripts/b29_named_rotate.py            # do the move (idempotent no-op once done)
  python3 scripts/b29_named_rotate.py --verify   # re-assert sha1 + the stub's cite resolves
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-b29-rows.md")
EXPECT_SHA1 = "579f90da7d8cbeefaf218d9249a049bd10b7eef5"
START = "## M334 (s316-chain2"
END = "## B28 (s316 BUILD"
HEADER = ("# NAMED archive - B29 headroom rotation (s319): the M334 block VERBATIM\n"
          "(moved by `scripts/b29_named_rotate.py`; the region's sha1 is pinned to `%s` -\n"
          "run `--verify` after any edit; NAMED.md's stub keeps one line per claim)\n\n" % EXPECT_SHA1)


def stub(archive_line):
    return (
        "## M334 (s316-chain2, STATIC, zero box) - FUN_004f47f0's upkeep-FAILURE branch = a "
        "DIFFICULTY-GATED AUTO-SELL of one facility; ENERGY is ASSIGNED the price, not refunded "
        "(closes pick (x7); CORRECTS `docs/named-archive-m32-m84e.md:268`). FULL-LENGTH ROWS "
        "VERBATIM at `docs/named-archive-b29-rows.md:%d` (sha1 `579f90da7d8c`); this stub "
        "governs, one line per claim\n"
        "\n"
        "- 3-way dispatch after `ENERGY -= cost`: A `cmp [block+0x8],1` -> clamp, B "
        "`cmp [base+0x50],neg(item)` -> clamp, C sell; the zero source is `xor eax,eax` @0x4f4960 "
        "(`evidence/m334_powershort_census.txt:4-10`) - V MU1-6,MU35,ME2.\n"
        "- `block+0x8` = EFFECTIVE DIFFICULTY: create 0x59eed6 = `ds:0x985aec` / imm 3, save-load "
        "0x57ef57 through `[ecx*4+0x94d438]` with ecx = 2095*eax => difficulty<2 never sells "
        "(`:11-18`) - V MU7-9,MU26,MU33,MU38,ME1,ME5.\n"
        "- the sell clears the SAME bitmap bit the charge tests (derived 304*base + byte + "
        "0x95da9c) (`:19-24`) - V MU10-13,MU22-24,MU27,MU28,MU39,ME3 + RIVAL2.\n"
        "- `ENERGY := FUN_004e40a0(owner,1,-1) * row[item]+12` with 0 reads of block+0x220 => the "
        "archived \"refund (+=)\" is REFUTED (`:25-29`) - V MU14-17,MU29,MU30,MU36,MU37 + RIVAL1.\n"
        "- announced `FUN_0048f100('POWERSHORT',0x10000,0xe,'genwarning_sm.pcx',0)` + "
        "`FUN_006265a2(1,row[item]+0,-1,-1)` (`:30-34`) - V MU18-20,MU25,MU31,ME6.\n"
        "- no loop exit after a sale => several facilities can go in one round; 0 folded refs to "
        "block+0x220 (control: 10 image-wide) (`:35-39`) - V MU21,MU22,MU34,ME3,ME4.\n"
        "- INFERRED/OPEN: `base_rec+0x50` = queue head; `row+12` runtime value (.bss) => numeric "
        "ENERGY outcome; FUN_004e40a0 = ECONOMIC FACTOR - lead (`:39`).\n"
        "- ACCEPT `scripts/m334_powershort_census.py` 7/7 `5b5ece39af02baba`; harness 45/45 "
        "`a5a5091e533f7883`, selftest 6/6 (`evidence/m334_mutate.txt:47-49`).\n"
        "\n" % archive_line)


def sha1(t):
    return hashlib.sha1(t.encode("utf-8")).hexdigest()


def region_from(text, start, end):
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j]


def verify():
    named = open(NAMED, encoding="utf-8").read()
    arch = open(ARCHIVE, encoding="utf-8").read()
    blk = arch[arch.index(START):]
    ok_sha = sha1(blk) == EXPECT_SHA1
    m = re.search(r"docs/named-archive-b29-rows\.md:(\d+)", named)
    ok_cite = bool(m) and arch.splitlines()[int(m.group(1)) - 1] == blk.splitlines()[0]
    ok_stub = (START in named) and (END in named) and (len(blk) < 3300)
    print("archive sha1 %s %s" % (sha1(blk), "OK" if ok_sha else "MISMATCH vs " + EXPECT_SHA1))
    print("stub cite line %s %s" % (m.group(1) if m else "-",
                                    "resolves to the M334 header" if ok_cite else "BROKEN"))
    print("stub present %s" % ("OK" if ok_stub else "FAIL"))
    print("NAMED.md %d B" % len(named.encode("utf-8")))
    return 0 if (ok_sha and ok_cite and ok_stub) else 1


def main(argv):
    if "--verify" in argv:
        return verify()
    named = open(NAMED, encoding="utf-8").read()
    if not os.path.exists(ARCHIVE):
        blk = region_from(named, START, END)
        if sha1(blk) != EXPECT_SHA1:
            print("REFUSING: region sha1 %s != pinned %s" % (sha1(blk), EXPECT_SHA1))
            return 1
        arch = HEADER + blk
        line = HEADER.count("\n") + 1
        open(ARCHIVE, "w", encoding="utf-8").write(arch)
        new = named.replace(blk, stub(line))
        open(NAMED, "w", encoding="utf-8").write(new)
        print("moved %d B verbatim to %s:%d; NAMED %d -> %d B"
              % (len(blk), os.path.relpath(ARCHIVE, ROOT), line,
                 len(named.encode()), len(new.encode())))
    else:
        print("archive already exists; verifying instead")
    return verify()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
