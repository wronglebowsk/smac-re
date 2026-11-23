# -*- coding: utf-8 -*-
"""B28-session NAMED rotation (s316-chain1): move `## M246`..`## M248/M249` VERBATIM to a NEW
archive `docs/named-archive-b28-rows.md` (§rotation-1).

NAMED.md sits at 246,245/250,000 B (3,755 B headroom) — UNDER the 5 KB trigger, so a block had
to be rotated BEFORE `## B28` lands (the pre-add size is the only safe reading, s308 law).

Victim: the oldest still-full region of the registry — M246 (s197), M247 (s197) and M248/M249
(s198), 3,507 B of settled pre-mutation-law rows. Every claim keeps a line in the stub with its
own gate id and cite, and the two OPEN rows (M247's "what the byte VALUES mean", M249's "what
names the partition") stay IN THE STUB, not only in the archive (AGENTS.md invariant: a
retraction that lives only in the archive lets the registry assert the older claim).

    python3 scripts/b28_named_rotate.py            # perform the move (guarded)
    python3 scripts/b28_named_rotate.py --verify   # re-hash + re-pin the archived region
    python3 scripts/b28_named_rotate.py --restub   # rewrite the stub from the STUB constant
"""
import argparse
import hashlib
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # derive, never hardcode
NAMED = os.path.join(ROOT, "NAMED.md")
ARC = os.path.join(ROOT, "docs", "named-archive-b28-rows.md")

START = "## M246 (s197) — the save's last 4 B are a `timeGetTime()` save-CREATION stamp"
END = "## B3 (s199, BUILD track, PASS 6/6)"
MARK = "§rotation-1 (M246, M247, M248/M249, s316-chain1 headroom rotation)"
TERMINATOR = "(§rotation-1 ends; anything below belongs to a later rotation.)"
# a line that must NOT survive in NAMED.md once the region has moved
MOVED_PROBE = "| the slack is never written: bytes 79..90 are `0xcd`"

ARC_HEADER = """# named-archive-b28-rows.md — NAMED rows rotated out of the registry

Rotations append here VERBATIM; each region carries its own `§rotation-N` marker and its own
terminator line, so a later rotation never re-hashes an earlier region (the s312 lesson).
`scripts/b28_named_rotate.py --verify` re-derives the marker line, the archived block's header
line and the full sha1 of the region between marker and terminator.

"""

STUB = """## M246 (s197) — the save's last 4 B are a `timeGetTime()` save-CREATION stamp — FULL rows VERBATIM at `docs/named-archive-b28-rows.md:ARC_LINE` (§rotation-1 marker at `:MARKLINE`, s316-chain1 headroom rotation, sha1 `SHA12` — the region is bounded by its own terminator line, its line number AND full digest re-asserted by `scripts/b28_named_rotate.py --verify`); this stub governs.
- `FUN_00597ce0` writes the trailing dword from `timeGetTime()` (`local_8` line 15 → `FUN_0064c9a0(&local_8,4,1,iVar2)` line 44), the codec never reads it; Δ(dword) vs Δ(mtime) ≤ 2.5 s on 5/5 same-session pairs | shard_015.c | V
- creation-stamped, not file-write-stamped: `0x15c79939` on 3 files 486,979 s apart, `0x2db1b939` on 2 files 71,224 s apart | census G3, 17 saves | V

## M247 (s197) — the region map's row stride is `Rw>>1`, not `(Rw+1)/2` — rows in the same archived region; this stub governs.
- 6 referencing functions; the only element accessors `FUN_00582340`/`FUN_00582360` index `(param_1>>1)+DAT_0092ae18+(DAT_0092ad9c>>1)*param_2`; `(Rw+1)/2` occurs once image-wide (the length) | G4 | V
- builder `FUN_0058ce00` (y<Rh, x=(y&1) step 2<Rw) writes exactly bytes 0..78 at Rw=Rh=13; slack = Rh−1 for odd Rw, else 0 | G5 | V
- the slack is never written: bytes 79..90 = `0xcd` in 17/17 saves, none in 0..78; both .MP (even Rw) slack 0 | 17 saves + 2 .MP | V
- the byte VALUES: terrain record `+3` of the first of 9 sampled tiles with `+1 & 0xe0 > 0x5f`, else 0; `+3` unnamed | rule V, meaning OPEN

## M248/M249 (s198, PASS 5/5) — the region map's bytes are a per-region copy of terrain record +3, the map's REGION LABEL — rows in the same archived region; this stub governs.
- region byte = record +3 of the FIRST land tile of a centre-first 9-diamond sample at (x*5+dx, y*5+dy), 0 if no land; x wraps mod DAT_0092a378, y bounded by DAT_0092a37c; the 9 (dx,dy) read from 0x67850c/0x678990 | `FUN_0058ce00` shard_015.c:4690-4752, G1 9/9 | V
- stored == recomputed byte for byte: 19 files, 1809 cells, 0 mismatches, 38 wrapped samples | G2, `evidence/m248_region_values.txt` | V
- exactly 1 reader fn (`FUN_00556690`), 1 writer fn (`FUN_0058ce00`); 17 other refs = alloc/free/file-io/null-guard/clear | G3 | V
- record +3's ONLY writer is `FUN_00582d00`; 4 call sites, all map generation | G4 (18 record-array stores, 1 covers byte 3) | V
- +3 plane identical across 17 saves, turns 50,51,52,53,60 | G4 | V
- +3 < 0x40 on every land tile, >= 0x41 on every water tile, 0x40 unused (19 files); index into DAT_0094eda8 (stride 0x20bc), split at 0x40 | G5 | V (census), OPEN (what names the partition; 25 ids / 47 components, 130/16626 adjacencies differ)
- instrument `scripts/m248_region_values_census.py` -> `evidence/m248_region_values.txt` | rc=0 | H

"""


def region_bounds(arc_text):
    a = arc_text.index(MARK)
    b = arc_text.index(TERMINATOR, a)
    line_no = arc_text.count("\n", 0, a) + 1
    return line_no, arc_text[a + len(MARK):b].strip("\n")


def stub_for(sha, arc_line):
    # arc_line is the MARKER line; the cite must land on the moved block's header (marker + 2)
    return (STUB.replace("SHA12", sha[:12]).replace("ARC_LINE", str(arc_line + 2))
            .replace("MARKLINE", str(arc_line)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--restub", action="store_true",
                    help="rewrite the in-registry stub from the STUB constant")
    args = ap.parse_args()

    src = io.open(NAMED, encoding="utf-8").read()
    arc = io.open(ARC, encoding="utf-8").read() if os.path.exists(ARC) else None

    if args.restub:
        arc_line, body = region_bounds(arc)
        sha = hashlib.sha1(body.encode("utf-8")).hexdigest()
        old = [ln for ln in src.splitlines()
               if ln.startswith("## M246") and "§rotation-1" in ln
               and "named-archive-b28-rows.md" in ln]
        assert len(old) == 1, "expected exactly one rotation-1 stub line, got %d" % len(old)
        new_stub_first = stub_for(sha, arc_line).splitlines()[0]
        new = src.replace(old[0], new_stub_first)
        assert new_stub_first in new and old[0] not in new
        io.open(NAMED, "w", encoding="utf-8").write(new)
        print("restubbed: cite now :%d (marker :%d) | NAMED.md %d -> %d B"
              % (arc_line + 2, arc_line, len(src.encode()), len(new.encode())))
        return 0

    if args.verify:
        arc_line, body = region_bounds(arc)
        sha = hashlib.sha1(body.encode("utf-8")).hexdigest()
        stubs = [ln for ln in src.splitlines()
                 if ln.startswith("## M246") and "§rotation-1" in ln
                 and "named-archive-b28-rows.md" in ln]
        assert len(stubs) == 1, "expected exactly one §rotation-1 line in NAMED.md, got %d" % len(stubs)
        stub = stubs[0]
        want = stub.split("sha1 `")[1].split("`")[0]
        assert len(want) == 12 and re.fullmatch(r"[0-9a-f]{12}", want), \
            "the stub does not record exactly a 12-hex digest: %r" % want
        assert sha.startswith(want), "sha1 %s does not match the recorded %s" % (sha[:12], want)
        cited = re.search(r"named-archive-b28-rows\.md:(\d+)", stub)
        assert cited, "the stub does not cite the archive with a :line"
        assert int(cited.group(1)) == arc_line + 2, \
            "the stub cites :%s but the moved block's header sits at :%d" % (cited.group(1), arc_line + 2)
        assert MOVED_PROBE not in src, "the moved block came back into NAMED.md"
        assert arc.count(MARK) == 1, "the archive carries %d copies of §rotation-1" % arc.count(MARK)
        print("PASS b28 rotate-verify: NAMED stub cites sha1 %s, cites the archive at :%d "
              "(marker :%d), cites the region re-hashes byte-exact (%d B) and no copy came back"
              % (want, arc_line + 2, arc_line, len(body.encode("utf-8"))))
        return 0

    # perform
    assert arc is None or MARK not in arc, "the archive already carries §rotation-1 — refusing a duplicate region"
    assert src.count(START) == 1 and src.count(END) == 1, "START/END must be unique"
    a = src.index(START)
    b = src.index(END)
    moved = src[a:b]
    assert MOVED_PROBE in moved, "the victim region does not contain the expected row: %r" % moved[:80]
    assert moved.rstrip().endswith("| H |"), "the region does not end where expected: %r" % moved[-60:]
    base = arc if arc is not None else ARC_HEADER
    arc_line = base.rstrip("\n").count("\n") + 3   # blank line, then the marker
    new_arc = (base.rstrip("\n") + "\n\n" + MARK + "\n\n" + moved.rstrip("\n") + "\n\n"
               + TERMINATOR + "\n")
    body = new_arc[new_arc.index(MARK) + len(MARK):new_arc.index(TERMINATOR)].strip("\n")
    sha = hashlib.sha1(body.encode("utf-8")).hexdigest()
    new_src = src[:a] + stub_for(sha, arc_line) + src[b:]
    io.open(ARC, "w", encoding="utf-8").write(new_arc)
    io.open(NAMED, "w", encoding="utf-8").write(new_src)
    print("rotated: NAMED.md %d -> %d B (headroom to 250,000: %d B) | §rotation-1 at :%d sha1=%s"
          % (len(src.encode()), len(new_src.encode()), 250000 - len(new_src.encode()),
             arc_line, sha[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
