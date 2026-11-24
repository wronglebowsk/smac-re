#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M335 doc-cap rotation: move the settled `## M246 .. ## M254` region of NAMED.md VERBATIM
into docs/named-archive-m246-m254.md and leave one compressed stub block per id.

Why: NAMED.md measured 249,465 B against the 250,000 B FAIL line (535 B headroom) at the start
of s317-chain2, and this milestone must add `## M335`. Rotation-1 (M259-M261), rotation-2
(M315), M316/M311/M329/M332/M333 all took the newer blocks; this region (s197-s201, the
save-stamp / region-map / region-verdict era) is the oldest still-full one.

Byte-exactness is asserted two ways: the archive must contain the region as a byte substring and
the sha1 of the region must equal the value printed here and pinned in `SHA1` after the first run.
Every stub keeps its block's numerals, its G-gates and its evidence-file names; the archive holds
the full rows and its line range is cited from each stub.

    python3 scripts/m335_named_rotate.py            # perform the move (guarded, refuses twice)
    python3 scripts/m335_named_rotate.py --verify   # re-hash the archived region at this head
"""
import argparse
import hashlib
import re
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCH = os.path.join(ROOT, "docs", "named-archive-m246-m254.md")
FAIL_LINE = 250000
START = "## M246 (s197)"
PROBE = "`FUN_00597ce0` takes `local_8 = timeGetTime()`"   # a moved-row line: proves the region left
END = "## M255-M258"
HEADS = ["## M246 ", "## M247 ", "## M248/M249 ", "## B3 ", "## M250 ", "## M251 ",
         "## M252 ", "## M253 ", "## M254 "]
SHA1 = "8c4762cc7523c392"  # measured by the first run (-u at s317-chain2)

STUBS = {}
STUBS["## M246 "] = """## M246 (s197) — the save's last 4 B are a `timeGetTime()` save-CREATION stamp
FULL rows VERBATIM at `docs/named-archive-m246-m254.md:ARC_M246` (§rotation-m335, sha1 `SHA12`); this stub governs.
- `FUN_00597ce0`: `local_8 = timeGetTime()` at entry, passed to `FUN_0064c9a0(&local_8,4,1,iVar2)` = the trailing dword, which the codec never reads; Δ(dword) vs Δ(mtime) <= 2.5 s on 5/5 same-session pairs (V).
- creation-stamped, not file-write-stamped: `0x15c79939` on 3 files 486,979 s apart, `0x2db1b939` on 2 files 71,224 s apart (census G3 over 17 saves) (V).
"""

STUBS["## M247 "] = """## M247 (s197) — the region map's row stride is `Rw>>1`, not `(Rw+1)/2`
FULL rows VERBATIM at `docs/named-archive-m246-m254.md:ARC_M247` (§rotation-m335, sha1 `SHA12`); this stub governs.
- `DAT_0092ae18` has 6 referencing functions; the only accessors `FUN_00582340`/`FUN_00582360` index `(p1>>1) + base + (0x92ad9c>>1)*p2`; `(Rw+1)/2` appears exactly once image-wide (the length) (census G4) (V).
- builder `FUN_0058ce00` walks y<Rh, x=(y&1) step 2 < Rw => write set 0..78 at Rw=Rh=13, slack Rh-1 when Rw odd; the slack bytes are `0xcd` (uninitialized) in 17/17 saves, both .MP have slack 0 (G5) (V). Byte VALUES: terrain record `+3` of the first qualifying tile (rule V, meaning OPEN).
"""

STUBS["## M248/M249 "] = """## M248/M249 (s198, PASS 5/5) — the region map's bytes are a per-region copy of terrain record +3 = the map's REGION LABEL
FULL rows VERBATIM at `docs/named-archive-m246-m254.md:ARC_M248` (§rotation-m335, sha1 `SHA12`); this stub governs.
- byte = record `+3` of the FIRST land tile of a centre-first 9-diamond sample at (x*5+dx, y*5+dy), 0 if no land; x wraps mod `0x92a378`, y bounded by `0x92a37c`; `(dx,dy)` read from 0x67850c/0x678990, G1 9/9 (V).
- stored == recomputed on 19 files (17 saves + 2 .MP), 1809 cells, 0 mismatches, 38 wrapped samples (G2, `evidence/m248_region_values.txt`) (V); exactly 1 reader (`FUN_00556690`) / 1 writer (`FUN_0058ce00`) (G3) (V).
- `+3`'s ONLY writer = byte setter `FUN_00582d00`, 4 sites all map generation (G4) (V); `+3<0x40` land / `>=0x41` water, 0x40 unused, 0 exceptions on 19 files (V); used as index into `DAT_0094eda8` (stride 0x20bc) and split at 0x40 (G5) — what NAMES the partition OPEN.
"""

STUBS["## B3 "] = """## B3 (s199, BUILD track, PASS 6/6) — `sim/turn.py`: M30's turn engine, executable, replays the recorded trace 67/67
FULL rows VERBATIM at `docs/named-archive-m246-m254.md:ARC_B3` (§rotation-m335, sha1 `SHA12`); this stub governs.
- parity rule: recorded rows are an ORDERED SUBSEQUENCE of the engine's emissions (the trace is a 0.2 s change-set sample); matched 67/67, 220 emitted, 154 collapsed (`evidence/b3_turn_replay.txt:2`) (V).
- 8 faction slots walked ASCENDING, our slot 3 the only one where tf==0 (21 rows) (G1/G2) (V); YEAR fires on the 7->0 edge while cur is still 7 (G3) (V); `tf` cleared ONE STEP AFTER cur_player:=3 (merge => 5/66) (G4) (V).
- 48 of 322,560 models reproduce the trace = 6 cyclic orders x 8 rotations, only {4,5,6}'s internal order free (G5) (V); 20 presses = 20 year bumps = 20 tf clears, 2213->2233 (G6) (V). OPEN: press transition (3,0)->(3,2) unobservable; `nb` (0x985AF4) unmodelled.
"""

STUBS["## M250 "] = """## M250 (s200, PASS 7/7) — the region generator: 3 callers, and the coarse map is built LAST inside it
FULL rows VERBATIM at `docs/named-archive-m246-m254.md:ARC_M250` (§rotation-m335, sha1 `SHA12`); this stub governs.
- `FUN_0058d390` (1293 B) has exactly 3 call sites: `0x5add8f`, `0x5af0c7`, `0x5b09e3` (G1) (V); inside it the flood-fill `call 0x58d120`@`0x58d47e` is enclosed by BOTH scan back edges, `FUN_0058ce00`@`0x58d88c` by NONE and is the last call but one (G3) (V).
- id bands land 1..0x3e / water 0x41..0x7e, 0x40 never assigned, overflow 0x3f/0x7f for border rings + band exhaustion (G4) (V); region table `DAT_00989ce0` stride 0x1c, dword 0 = tile count, `+0x14` = 8-byte adjacency bitmap (G4) (V).
- new-game driver `FUN_005b2970` (4 callers) runs placement -> generator -> retry vote (<=4); `FUN_005b09b0` = ALTERING WORLD CLIMATE re-runs it (G1) (V static / OPEN which site is NEW GAME). instrument `scripts/m250_region_generation.py` 7/7.
"""

STUBS["## M251 "] = """## M251 (s200, PASS 7/7) — `DAT_0094eda8` = the per-faction, per-REGION category byte (128 ids, 4 values)
FULL rows VERBATIM at `docs/named-archive-m246-m254.md:ARC_M251` (§rotation-m335, sha1 `SHA12`); this stub governs.
- shape `[region + faction*0x20bc]` byte array at exactly `0x94eda8`, 128 entries (`cmp reg,0x80`) (V); 79 refs in 18 functions, 6 store sites in 2 writers (`FUN_00556690` x5, `FUN_0055f650` x1), values {0,2,7,8} (G5) (V).
- effects: `<2` = +1000 preferred candidate; `==7` accepted at face score; `==8` accepted only if `DAT_00989ce0[region] < 0x96`; `==2` blocks the pick (V effects / OPEN names).
- reset: 4 reserved ids stamped 8, every water id ends at 7 (V). Siblings same index: `0x94e4a8` short x128, `0x94e5a8` byte SCORE, `0x94e628`, `0x94e7a8` (V addressing / OPEN meanings).
"""

STUBS["## M252 "] = """## M252 (s200, PASS 7/7) — the coarse region map has ONE consumer: `FUN_00556690`'s site search
FULL rows VERBATIM at `docs/named-archive-m246-m254.md:ARC_M252` (§rotation-m335, sha1 `SHA12`); this stub governs.
- accessor `FUN_00582340` called at exactly 2 sites, both inside `FUN_00556690` (`0x55878a`, `0x558812`) (G6/G7) (V); `FUN_00556690` called only from `FUN_005208f0`@`0x52094f` and `FUN_0059ce10`@`0x59dd43` (M94 upkeep) (V).
- the search walks the coarse grid by its own dims, keeps label-matching cells, converts cell->terrain x=cell*5, scores footprints; the winner is gated by terraform cost `FUN_004cc7b0` and issued as `FUN_0056d350(faction,0x29,2,x,y,-1)` (G6) (V). => the coarse map is the SPATIAL INDEX, not a minimap layer.
"""

STUBS["## M253 "] = """## M253 (s201, PASS 8/8) — the four region verdict codes are named by the guard that writes each
FULL rows VERBATIM at `docs/named-archive-m246-m254.md:ARC_M253` (§rotation-m335, sha1 `SHA12`); this stub governs.
- 8 = reserved ids with nothing scored (`and eax,0x3f` + zero test + `jmp 0x558b18`); 7 vs 8 = `sete dl; add dl,0x7`@`0x558516`; water band always ends at 7 (id>=0x40, `0x55856b`) (G4) (V).
- 0 = cleared-open under `test BYTE[ebp-0x40],0x2` (`0x558549`), 2 = contested under bit 1 (`0x55855e`), the 2-store AFTER the 0-store (V guards / INFERRED names); consumer domain of loads tests exactly {2,7,8}, 0 unclassified (G1/G2) (V).
"""

STUBS["## M254 "] = """## M254 (s201, PASS 8/8) — the two bits come from FUN_00531bf0: contact between two factions inside one region
FULL rows VERBATIM at `docs/named-archive-m246-m254.md:ARC_M254` (§rotation-m335, sha1 `SHA12`); this stub governs.
- the stage accumulator `[ebp-0x40]` has exactly ONE computed write, OR-ing only {1,2}, and only masks {1,2} are tested (G5) (V).
- `FUN_00531bf0(facA,facB,region,mode)` (505 B, 10 call sites, 2 in `FUN_00556690`) keeps a facA unit whose record byte +3 == region, seeks a facB unit in the same region, calls route/`FUN_0058cfc0`; returns 1 iff a route is found (V shape / INFERRED route). Pairing: bit1 -> 2 CONTESTED (blocks pick), bit2 -> 0 OPEN (+1000) (INFERRED).
- `FUN_0055f650`'s only store promotes 8 -> 7 at `0x564ad7` in the same window as `add WORD[eax+0x94eaa8],0xfff6` and `or BYTE[eax+0x94e7a8],0x9` (V code / INFERRED why).
"""


def region(text):
    a = text.index(START)
    b = text.index(END, a)
    # keep the blank separator lines that precede END out of the moved block
    body = text[a:b].rstrip("\n")
    return a, b, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--check-stubs", action="store_true")
    a = ap.parse_args()

    named = io.open(NAMED, encoding="utf-8").read()
    arc = io.open(ARCH, encoding="utf-8").read() if os.path.exists(ARCH) else ""

    if a.check_stubs:
        arc_lines = arc.split("\n")
        n_ok = 0
        nlines = named.split("\n")
        for h in HEADS:
            idx = [i for i, l in enumerate(nlines) if l.startswith(h)]
            assert len(idx) == 1, "expected one stub head %r, got %d" % (h, len(idx))
            blk = "\n".join(nlines[idx[0]:idx[0] + 4])
            m = re.search(r"named-archive-m246-m254\.md:(\d+)", blk)
            assert m, "stub for %r carries no archive cite" % h
            ln = int(m.group(1))
            name = h[3:].split("/")[0].strip()
            assert arc_lines[ln - 1].startswith(h.strip() if "/" in h else "## " + name), \
                "stub %r cites :%d which is %r" % (h, ln, arc_lines[ln - 1][:60])
            n_ok += 1
        print("PASS stub-cites: %d/%d stubs point at their own block head in the archive"
              % (n_ok, len(HEADS)))
        return 0

    if a.verify:
        # region now lives in the archive; locate it there and re-hash
        assert SHA1 != "PENDING", "SHA1 constant not pinned"
        s = arc.index(START)
        e = arc.index(END, s) if END in arc[s:] else len(arc)
        body = arc[s:e].rstrip("\n")
        sha = hashlib.sha1(body.encode("utf-8")).hexdigest()
        print("archive region bytes=%d sha1=%s" % (len(body.encode()), sha))
        print("SMAC verify head NAMED.md %d B (fail line %d, headroom %d)" %
              (len(named.encode()), FAIL_LINE, FAIL_LINE - len(named.encode())))
        assert sha.startswith(SHA1), "archived region sha1 %s != pinned %s" % (sha, SHA1)
        assert PROBE not in named, "NAMED.md still holds the rotated region"
        print("PASS rotate-verify: region re-hashes byte-exact to %s" % SHA1)
        return 0

    assert not arc, "archive already exists - refuses to rotate twice"
    assert SHA1 == "PENDING", "already applied"
    a0, b, body = region(named)
    sha = hashlib.sha1(body.encode("utf-8")).hexdigest()
    lines = body.split("\n")
    for h in HEADS:
        n = sum(1 for l in lines if l.startswith(h))
        assert n == 1, "expected exactly one block head %r, got %d" % (h, n)
    # line numbers of each block inside the moved region (1-based, archive header is 4 lines)
    arc_hdr_lines = 4
    marks, cur = {}, None
    for i, l in enumerate(lines):
        for h in HEADS:
            if l.startswith(h):
                marks[h] = arc_hdr_lines + i + 1
    stub_txt = []
    for h in HEADS:
        name = h[3:].split("/")[0].strip()          # s317 review F1: no [:-1] (ate a digit on "M248/M249")
        t = STUBS[h].replace("SHA12", sha[:12]).replace("ARC_" + name, str(marks[h]))
        # every stub must cite the archive line of its own block, as an EXACT token (F10)
        assert re.search(r"(?<!\d)%d(?!\d)" % marks[h], t), \
            "stub %r missing archive line %d" % (h, marks[h])
        assert "ARC_" not in t, "stub %r kept an unsubstituted placeholder" % h
        assert "docs/named-archive-m246-m254.md" in t
        stub_txt.append(t.rstrip("\n"))
    stub = "\n".join(stub_txt) + "\n"
    before = len(named.encode())
    new = named[:a0] + stub + "\n" + named[b:]
    nb = len(new.encode())
    after_headroom = FAIL_LINE - nb

    hdr = ("# M246..M254 rows, moved VERBATIM out of NAMED.md by scripts/m335_named_rotate.py\n"
           "# (doc-cap rotation, s317-chain2/M335; NAMED.md was at %d B).\n"
           "# sha1 of the moved region: %s\n\n" % (before, sha))
    arc_txt = hdr + body + "\n"
    print("moved region lines=%d bytes=%d sha1=%s" % (len(lines), len(body.encode()), sha))
    print("blocks: %s" % ", ".join("%s@%d" % (h.strip(), marks[h]) for h in HEADS))
    print("NAMED.md %d -> %d B (headroom vs %d B FAIL line: %d)" % (before, nb, FAIL_LINE, after_headroom))

    assert len(body.encode()) > 8000, "the region to rotate is implausibly small"
    assert nb < before - 5000, "rotation saved too little to be worth doing"
    assert after_headroom > 5500, "still little headroom after the rotation"
    open(ARCH, "w", encoding="utf-8").write(arc_txt)
    open(NAMED, "w", encoding="utf-8").write(new)
    chk = io.open(NAMED, encoding="utf-8").read()
    assert PROBE not in chk and body not in chk, "NAMED.md still holds the full region"
    arc2 = io.open(ARCH, encoding="utf-8").read()
    assert body in arc2 and sha in arc2, "archive is not byte-exact"
    print("PASS rotate-m335: region sha1 %s, archive %d B, NAMED.md %d B"
          % (sha[:12], len(arc2.encode()), len(chk.encode())))
    print("pin: SHA1 = %r" % sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
