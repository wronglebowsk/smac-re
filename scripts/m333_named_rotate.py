# -*- coding: utf-8 -*-
"""M333 headroom rotation (s313-chain1, docs/s313-caps).

`NAMED.md` sat at 246,504 / 250,000 B = 3,496 B headroom, UNDER the 5 KB trigger, so a
block has to be rotated BEFORE `## M333` is added (the pre-add size is the only safe
reading - s308 law).

The victim is `## M259-M261` (s204, PASS 14/14): the oldest still-full block of the
pre-mutation-law era (the harness era starts at `## M308`), settled by its own census and
corrected twice afterwards (M262 retracted part of M260, M259 retracted part of M240).
It moves VERBATIM into a NEW archive file - the s312 lesson is that appending a second
rotation to an archive the earlier rotation hashed to EOF breaks that rotation's own
verification, so every region here is bounded by an explicit terminator line and
`--verify` re-reads exactly that region.

The two RETRACTIONS stay in the stub, in place: a retraction that lives only in the
archive lets the registry keep asserting the older, stronger claim (AGENTS.md invariant).

    python3 scripts/m333_named_rotate.py           # perform the move (idempotent-guarded)
    python3 scripts/m333_named_rotate.py --verify   # re-hash the archived region
"""
import argparse
import hashlib
import io
import os
import sys

ROOT = os.path.expanduser("~/reverse/smac")
NAMED = os.path.join(ROOT, "NAMED.md")
ARC = os.path.join(ROOT, "docs", "named-archive-m333-rows.md")

START = "## M259-M261 (s204, PASS 14/14)"
END = "## M262-M266 (s205-s206, PASS 11/11 + 12/12)"
MARK = "§rotation-1 (M259-M261, s313-chain1 headroom rotation)"
TERMINATOR = "(§rotation-1 ends; anything below belongs to a later rotation.)"

STUB = """## M259-M261 (s204, PASS 14/14) — the per-faction mask band, the static map views, the 0x679f98 class — FULL rows VERBATIM at `docs/named-archive-m333-rows.md` §rotation-1 (s313-chain1 headroom rotation, sha1 `SHA12`, region bounded by the terminator line, byte-exact asserted by `scripts/m333_named_rotate.py --verify`); this stub governs. Pre-mutation-law registry (no MU ids — the harness era starts at `## M308`); the G-ids are the archive rows' own gate ids. `evidence/m259_m261_census.txt` (SUMMARY M259/M260/M261: 14/14 gates PASS, 3.3 s, one invocation).
- M259 the band: terrain record bytes +16..+43 (dwords 4..10) = the FACTIONS 1..7 per-faction copies of the record's `+8` master mask, `[terrain_base + 0xc + (row*0xb + fac)*4]` (faction 0 uses `+8`; both whole-array refreshes guard `test ebx,ebx / je`); writers CLOSED at 10 indexed + 1 walk store, every site named (G1-G6); 44 indexed reads in 25 functions (G7). **RETRACTS M240's "a record is two 22-byte map columns" for bytes 16..43** — the `.MP` "7 equal dwords == +8" (planetx 8192/8192) IS this band.
- M260 the views: the live 0x224b8 spacing occurs 0 times in the 3,067,904-B image, as immediate AND as LE dword (G8); view 0 is static .bss at 0x8f79e0 (sole immediate store 0x5803e1; ctor FUN_00518820 has exactly that one call site 0x580406, G9); the ctor's stores reach `this+0x23bec` = 146,412 B > the 140,472 stride, so the stride is not an object size (G10); the save codec walks the 8 entries as POINTERS, clearing `*(p+0x1dd74)` for entries 1..7 only (G11). **CORRECTED IN PLACE by M262 — RETRACTED: "the ~140 KB views are not allocated"**: entries 1..7 ARE allocated at startup, 0x22480 B each, by the pointer-arithmetic `mov [esi],eax` at 0x5803bb (0 only on the alloc-failure path); 0x224b8 = 0x22480 + 0x38, a 56-B heap header (INFERRED).
- M261 the class: vtable 0x679f98 = 88 slots, 2 installs, 15 slots differ from ALL of 0x6717cc/0x671d94/0x67164c (G12); all 15 named with size + callee count (G13); ctor chains FUN_0062d630 <- FUN_0045a8b0(1)/FUN_005b3000(2)/FUN_00641f3c(3) and FUN_0062d764 <- 6 callers, incl. FUN_00636b1e = "Start a new session or..." (session chooser) and FUN_00493a10 = "Gamma Correction" (G14).

"""


def region(archive_text):
    a = archive_text.index(MARK)
    b = archive_text.index(TERMINATOR, a)
    body = archive_text[a + len(MARK):b].strip("\n")
    # the archived payload is the block itself, verbatim, bracketed by blank lines
    return body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--restub", action="store_true",
                    help="rewrite the in-registry stub from the STUB constant (headroom retune)")
    args = ap.parse_args()

    src = io.open(NAMED, encoding="utf-8").read()
    arc = io.open(ARC, encoding="utf-8").read() if os.path.exists(ARC) else ""

    if args.restub:
        assert "§rotation-1" in src, "no rotated stub to rewrite"
        assert os.path.exists(ARC), "the archive must exist before a restub"
        body = region(io.open(ARC, encoding="utf-8").read())
        sha = hashlib.sha1(body.encode("utf-8")).hexdigest()
        a = src.index(STUB.split(" —")[0])
        b = src.index(END)
        new = src[:a] + STUB.replace("SHA12", sha[:12]) + src[b:]
        assert "**M259 the band** —" not in new, "the archived prose leaked back into NAMED.md"
        assert STUB.replace("SHA12", sha[:12]) in new
        io.open(NAMED, "w", encoding="utf-8").write(new)
        print("restubbed: NAMED.md %d -> %d B (headroom to 250,000: %d B)" %
              (len(src.encode()), len(new.encode()), 250000 - len(new.encode())))
        return 0

    if args.verify:
        body = region(arc)
        sha = hashlib.sha1(body.encode("utf-8")).hexdigest()
        recorded = [ln for ln in src.splitlines() if "§rotation-1" in ln]
        assert len(recorded) == 1, "expected exactly one §rotation-1 line in NAMED.md"
        want = recorded[0].split("sha1 `")[1].split("`")[0]
        print("archived region %d B sha1=%s" % (len(body.encode("utf-8")), sha))
        assert sha.startswith(want), "sha1 %s does not match the recorded %s" % (sha[:12], want)
        # the archived PROSE must not have come back, and the registry stub must be
        # byte-identical to the STUB constant that produced it (no silent drift)
        assert "**M259 the band** —" not in src, "the moved block came back into NAMED.md"
        assert STUB.replace("SHA12", want) in src, "the NAMED stub no longer matches the STUB constant"
        print("PASS rotate-verify: NAMED stub cites sha1 %s, cites the archive, and the region re-hashes byte-exact" % want)
        return 0

    src = io.open(NAMED, encoding="utf-8").read()
    assert START in src and END in src, "anchors not found in NAMED.md"
    assert "§rotation-1" not in src, "rotation already applied"
    a = src.index(START)
    b = src.index(END)
    block = src[a:b].rstrip("\n")
    sha = hashlib.sha1(block.encode("utf-8")).hexdigest()

    head = ""
    if not arc:
        head = ("# named-archive-m333-rows.md — `NAMED.md` rows rotated out for headroom, VERBATIM.\n"
                "`NAMED.md` keeps one line per claim with the same gates and cites; this file is the\n"
                "full text. The registry (NAMED) governs; this is the detail.\n")
    io.open(ARC, "a", encoding="utf-8").write("%s\n\n%s\n\n%s\n\n%s\n" % (head, MARK, block, TERMINATOR))

    back = io.open(ARC, encoding="utf-8").read()
    assert region(back) == block, "archive region is not byte-identical to the moved block"
    assert hashlib.sha1(region(back).encode("utf-8")).hexdigest() == sha

    new = src[:a] + STUB.replace("SHA12", sha[:12]) + src[b:]
    io.open(NAMED, "w", encoding="utf-8").write(new)
    print("moved %d B of rows; sha1=%s" % (len(block.encode("utf-8")), sha))
    print("NAMED.md %d -> %d B (headroom to 250,000: %d B)" %
          (len(src.encode()), len(new.encode()), 250000 - len(new.encode())))
    print("archive %d B" % len(io.open(ARC, 'rb').read()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
