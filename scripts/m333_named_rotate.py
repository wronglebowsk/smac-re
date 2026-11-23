# -*- coding: utf-8 -*-
"""M333 headroom rotation (s313-chain1, docs/s313-caps).

`NAMED.md` sat at 246,504 / 250,000 B = 3,496 B headroom, UNDER the 5 KB trigger, so a
block has to be rotated BEFORE `## M333` is added (the pre-add size is the only safe
reading - s308 law).

The victim is `## M259-M261` (s204, PASS 14/14): the oldest still-full block of the
pre-mutation-law era (the harness era starts at `## M308`), settled by its own census and
corrected twice afterwards (M262 retracted part of M260, M259 retracted part of M240).
It moves VERBATIM into a NEW archive file - the s312 lesson is that appending a second
rotation to an archive whose earlier rotation hashed to EOF breaks that rotation's own
verification, so every region here is bounded by an explicit terminator line.

Triaged from the #347 review (all 4 findings against this file ACCEPTED, none weakened):
  F4  verify now pins the archived region to a LINE NUMBER in the archive and asserts the
      stub records that line, so re-wrapping the archive above the marker reddens verify;
      it also prints the FULL sha1 and refuses a 12-hex prefix that is not the full digest's
      own prefix AND asserts the stub is byte-identical to the STUB constant.
  F5  the stub cites the shipped byte-read for the M262 correction (G8/G10 lines of
      `evidence/m259_m261_census.txt`, M262's own census + archive) instead of prose only.
  F8  --restub anchors on the UNIQUE line that is the rotated stub (header AND §rotation-1),
      never on a bare "## M259-M261" prefix that any table row could match.
  F9  the perform path refuses an archive that already carries §rotation-1 (a reverted NAMED
      edit plus a live archive used to append a duplicate region that verify then hashed).

The two RETRACTIONS stay in the stub, in place: a retraction that lives only in the archive
lets the registry keep asserting the older, stronger claim (AGENTS.md invariant).

    python3 scripts/m333_named_rotate.py            # perform the move (guarded)
    python3 scripts/m333_named_rotate.py --restub   # rewrite the stub from the STUB constant
    python3 scripts/m333_named_rotate.py --verify   # re-hash + re-pin the archived region
"""
import argparse
import hashlib
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # s314 review F8 class: derive, never hardcode
NAMED = os.path.join(ROOT, "NAMED.md")
ARC = os.path.join(ROOT, "docs", "named-archive-m333-rows.md")

START = "## M259-M261 (s204, PASS 14/14)"
END = "## M262-M266 (s205-s206, PASS 11/11 + 12/12)"
MARK = "§rotation-1 (M259-M261, s313-chain1 headroom rotation)"
TERMINATOR = "(§rotation-1 ends; anything below belongs to a later rotation.)"
CENSUS = "evidence/m259_m261_census.txt"

STUB = """## M259-M261 (s204, PASS 14/14) — the per-faction mask band, the static map views, the 0x679f98 class — FULL rows VERBATIM at `docs/named-archive-m333-rows.md:ARC_LINE` (§rotation-1, s313-chain1 headroom rotation, sha1 `SHA12` — the region is bounded by an explicit terminator line, its line number AND full digest re-asserted by `scripts/m333_named_rotate.py --verify`); this stub governs. Pre-mutation-law registry (no MU ids — the harness era starts at `## M308`); the G-ids are the archive rows' own gates, and the byte-reads they printed are `CENSUS` (`:30` SUMMARY 14/14, one invocation, 3.3 s).
- M259 the band: terrain record bytes +16..+43 (dwords 4..10) = the FACTIONS 1..7 per-faction copies of the record's `+8` master mask, `[terrain_base + 0xc + (row*0xb + fac)*4]` (faction 0 uses `+8`; both whole-array refreshes guard `test ebx,ebx / je`); writers CLOSED at 10 indexed + 1 walk store, every site named (G1-G6); 44 indexed reads in 25 functions (G7). **RETRACTS M240's "a record is two 22-byte map columns" for bytes 16..43** — the `.MP` "7 equal dwords == +8" (planetx 8192/8192) IS this band.
- M260 the views: the live 0x224b8 spacing occurs 0 times in the 3,067,904-B image — `immediates naming 0x224b8: 0; 4-byte LE pattern ... offset -1` (G8, `CENSUS:16-17`); view 0 is static .bss at 0x8f79e0 (sole immediate store 0x5803e1, printed by G10 at `CENSUS:21`; ctor FUN_00518820's only call site 0x580406, G9); the ctor's stores reach `this+0x23bec` = 146,412 B > the 140,472 stride, so the stride is not an object size (G10 `CENSUS:20-21`); the save codec walks the 8 entries as POINTERS, clearing `*(p+0x1dd74)` for entries 1..7 only (G11). **CORRECTED IN PLACE by M262 — RETRACTED: "the ~140 KB views are not allocated"**: entries 1..7 ARE allocated at startup, 0x22480 B each, by the pointer-arithmetic `mov [esi],eax` at 0x5803bb (0 only on the alloc-failure path) — M262's own rows: `docs/named-archive-m332-rows.md` (G2), `evidence/m262_m264_census.txt:24` (11/11); 0x224b8 = 0x22480 + 0x38, a 56-B heap header (INFERRED).
- M261 the class: vtable 0x679f98 = 88 slots, 2 installs, 15 slots differ from ALL of 0x6717cc/0x671d94/0x67164c (G12); all 15 named with size + callee count (G13); ctor chains FUN_0062d630 <- FUN_0045a8b0(1)/FUN_005b3000(2)/FUN_00641f3c(3) and FUN_0062d764 <- 6 callers, incl. FUN_00636b1e = "Start a new session or..." (session chooser) and FUN_00493a10 = "Gamma Correction" (G14).

"""


def region_bounds(text):
    """(line_no_of_marker, body) — the marker's 1-based line and the terminator-bounded body."""
    a = text.index(MARK)
    b = text.index(TERMINATOR, a)
    line_no = text.count("\n", 0, a) + 1
    return line_no, text[a + len(MARK):b].strip("\n")


def stub_for(sha, arc_line):
    return (STUB.replace("SHA12", sha[:12]).replace("ARC_LINE", str(arc_line))
            .replace("CENSUS", CENSUS))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--restub", action="store_true",
                    help="rewrite the in-registry stub from the STUB constant (headroom/cite retune)")
    args = ap.parse_args()

    src = io.open(NAMED, encoding="utf-8").read()
    arc = io.open(ARC, encoding="utf-8").read() if os.path.exists(ARC) else ""

    if args.restub:
        assert "§rotation-1" in src, "no rotated stub to rewrite"
        assert arc, "the archive must exist before a restub"
        arc_line, body = region_bounds(arc)
        sha = hashlib.sha1(body.encode("utf-8")).hexdigest()
        a = stub_anchor(src)
        b = src.index(END)
        new = src[:a] + stub_for(sha, arc_line) + src[b:]
        assert "**M259 the band** —" not in new, "the archived prose leaked back into NAMED.md"
        assert stub_for(sha, arc_line) in new
        io.open(NAMED, "w", encoding="utf-8").write(new)
        print("restubbed (archive §rotation-1 at :%d): NAMED.md %d -> %d B "
              "(headroom to 250,000: %d B)" % (arc_line, len(src.encode()), len(new.encode()),
                                               250000 - len(new.encode())))
        return 0

    if args.verify:
        arc_line, body = region_bounds(arc)
        sha = hashlib.sha1(body.encode("utf-8")).hexdigest()
        stubs = [ln for ln in src.splitlines() if "§rotation-1" in ln]
        assert len(stubs) == 1, "expected exactly one §rotation-1 line in NAMED.md, got %d" % len(stubs)
        stub = stubs[0]
        want = stub.split("sha1 `")[1].split("`")[0]
        assert len(want) == 12 and re.fullmatch(r"[0-9a-f]{12}", want), \
            "the stub does not record exactly a 12-hex digest: %r" % want
        assert sha.startswith(want), "sha1 %s does not match the recorded %s" % (sha[:12], want)
        # F4: the cite is pinned to the archive LINE the marker actually sits on. Re-wrapping
        # the archive above the marker, or moving the region, reddens this.
        cited = re.search(r"named-archive-m333-rows\.md:(\d+)", stub)
        assert cited, "the stub does not cite the archive with a :line"
        assert int(cited.group(1)) == arc_line, \
            "the stub cites :%s but §rotation-1 now sits at :%d" % (cited.group(1), arc_line)
        # the archived PROSE must not have come back, and the stub must equal the constant
        assert "**M259 the band** —" not in src, "the moved block came back into NAMED.md"
        assert stub_for(sha, arc_line) in src, "the NAMED stub no longer matches the STUB constant"
        # F9 (archive side): exactly one copy of the region may exist
        assert arc.count(MARK) == 1, "the archive carries %d copies of §rotation-1" % arc.count(MARK)
        print("archived region %d B | §rotation-1 at docs/named-archive-m333-rows.md:%d | full sha1=%s"
              % (len(body.encode("utf-8")), arc_line, sha))
        print("PASS rotate-verify: stub cites :%d + sha1 %s, the region re-hashes byte-exact, "
              "the stub equals the STUB constant and no copy came back" % (arc_line, want))
        return 0

    # ---- perform ----
    assert START in src and END in src, "anchors not found in NAMED.md"
    assert "§rotation-1" not in src, "rotation already applied to NAMED.md"
    assert MARK not in arc, ("the archive already carries §rotation-1 while NAMED.md does not — "
                             "a reverted edit; refusing to append a duplicate region (F9)")
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
    arc_line, body = region_bounds(back)
    assert body == block, "archive region is not byte-identical to the moved block"
    assert hashlib.sha1(body.encode("utf-8")).hexdigest() == sha

    new = src[:a] + stub_for(sha, arc_line) + src[b:]
    io.open(NAMED, "w", encoding="utf-8").write(new)
    print("moved %d B of rows to docs/named-archive-m333-rows.md:%d; sha1=%s" %
          (len(block.encode("utf-8")), arc_line, sha))
    print("NAMED.md %d -> %d B (headroom to 250,000: %d B)" %
          (len(src.encode()), len(new.encode()), 250000 - len(new.encode())))
    print("archive %d B" % len(io.open(ARC, 'rb').read()))
    return 0


def stub_anchor(text):
    """F8: the index of the ONE line that is the rotated stub — a header for this block AND
    carrying the rotation marker. A bare `## M259-M261` prefix could match a table row."""
    hits = [m.start() for m in re.finditer(r"(?m)^" + re.escape(START[:len("## M259-M261")]) + r".*§rotation-1.*$", text)]
    assert len(hits) == 1, "expected exactly one rotated-stub line, got %d" % len(hits)
    return hits[0]


if __name__ == "__main__":
    sys.exit(main())
