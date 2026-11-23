# -*- coding: utf-8 -*-
"""M333-session NAMED rotation 2 (s314): move `## M315` VERBATIM to the m333 archive.

NAMED.md sat at 245,072/250,000 B (4,928 B headroom) — UNDER the 5 KB trigger, so a block
had to be rotated BEFORE `## M333` lands (the pre-add size is the only safe reading, s308
law; the trigger binds even when the add cannot cross the fail line).

Victim: `## M315` (s284, 10/10 digest 3976ca97eedc1e19, harness 29/29) — the oldest
still-full block after rotation-1 took M259-M261. Its two later corrections (M318 answered
the callees; M319 REFUTED the caller-guard reading) stay IN THE STUB, in place — a
retraction that lives only in the archive lets the registry assert the older claim.

The region appends AFTER rotation-1's terminator and carries its OWN terminator, so
rotation-1's --verify (which hashes MARK..TERMINATOR-1) is untouched (the s312 lesson).

    python3 scripts/m333_named_rotate2.py            # perform the move (guarded)
    python3 scripts/m333_named_rotate2.py --verify   # re-hash + re-pin the archived region
"""
import argparse
import hashlib
import io
import os
import re
import sys

ROOT = os.path.expanduser("~/reverse/smac")
NAMED = os.path.join(ROOT, "NAMED.md")
ARC = os.path.join(ROOT, "docs", "named-archive-m333-rows.md")

START = "## M315 (s284, STATIC, zero box; mutation-tested 29/29 post-review)"
END = "## B25 (s294 BUILD"
MARK = "§rotation-2 (M315, s314 headroom rotation)"
TERMINATOR = "(§rotation-2 ends; anything below belongs to a later rotation.)"

STUB = """## M315 (s284, STATIC, zero box; mutation-tested 29/29 post-review) - pick (ii) CLOSED: `ds:0x68cbb4` is the REFRESH MEMO of the record-selection chain - "the index the refresh pair has already run for" - not a second cursor, and M311's 19 unexplained writers all close. FULL-LENGTH ROWS VERBATIM at `docs/named-archive-m333-rows.md:ARC_LINE` (§rotation-2, s314 headroom rotation, sha1 `SHA12` — the region is bounded by its own terminator line, its line number AND full digest re-asserted by `scripts/m333_named_rotate2.py --verify`); this stub governs.
- THE FIELD + PARTITION LAW: the 22 stores split 12 fed by the index or a caller slot (each followed by the refresh pair `call 0x4e8d60` + `call 0x4e78e0`) vs 10 `-1` sentinel clears with ZERO calls to either callee in the next 60 instructions (A2+A3, exact 12-element distance list); NO independent value ever enters — 8x `mov r,ds:0x68cbb0` + 4x caller slot, totals sum to exactly 22 (A2b+A9; proven CODE mutants PC1/PC2 rewrite those instructions).
- DEDUP GUARD PARTIAL, NOT UNIVERSAL: only 4 of the 12 memo sites carry a local guard (`0x4eb6c7`, `0x4efeaa`, `0x4f2201`, `0x4f5c4a`); the other 8 refresh unconditionally. ~~the 8 are guarded by their callers (pick (v))~~ **REFUTED by M319** — no hoisted guard exists; the single memo-reading caller is itself a memo-site owner (NAMED ## M319, `evidence/m319_guard_hoist.txt:69-71`). Still UNVERIFIED: that the 4 stack-slot stores carry an index; coherence across record deletion (A9 tail).
- M311's "19 writers unexplained" closes as 10 sentinel clears + 9 memo updates — its window was FORWARD `0..+32 B` (`m311_recidx.py:449`), not symmetric (A5); the image initialises BOTH `ds:0x68cbb0` and `ds:0x68cbb4` to `0xffffffff` (A7); `0x4e8d60`/`0x4e78e0` ANSWERED by M318 (NAMED ## M318).
- ACCEPTANCE `scripts/m315_bb4_census.py` -> 10/10, digest `3976ca97eedc1e19`, 2 runs byte-identical; `scripts/m315_bb4_mutate.py` -> 29/29 reddening EXACTLY their declared gate SETS (22 literal + 7 CODE mutants via `M315_PATCH`); coverage gap MEASURED: exactly 1 of 22 stores (`0x4f3f7f`) sits outside every `index.csv` function range — the only site where the def-walk falls back to a 36-instruction cap (A10; mutant MU19_unclaimed reddens exactly A10).

"""


def region_bounds(text):
    a = text.index(MARK)
    b = text.index(TERMINATOR, a)
    line_no = text.count("\n", 0, a) + 1
    return line_no, text[a + len(MARK):b].strip("\n")


def stub_for(sha, arc_line):
    return STUB.replace("SHA12", sha[:12]).replace("ARC_LINE", str(arc_line))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    src = io.open(NAMED, encoding="utf-8").read()
    arc = io.open(ARC, encoding="utf-8").read()

    if args.verify:
        arc_line, body = region_bounds(arc)
        sha = hashlib.sha1(body.encode("utf-8")).hexdigest()
        stubs = [ln for ln in src.splitlines() if "§rotation-2" in ln and "named-archive-m333-rows.md" in ln]
        assert len(stubs) == 1, "expected exactly one §rotation-2 line in NAMED.md, got %d" % len(stubs)
        stub = stubs[0]
        want = stub.split("sha1 `")[1].split("`")[0]
        assert len(want) == 12 and re.fullmatch(r"[0-9a-f]{12}", want), \
            "the stub does not record exactly a 12-hex digest: %r" % want
        assert sha.startswith(want), "sha1 %s does not match the recorded %s" % (sha[:12], want)
        cited = re.search(r"named-archive-m333-rows\.md:(\d+)", stub)
        assert cited, "the stub does not cite the archive with a :line"
        assert int(cited.group(1)) == arc_line, \
            "the stub cites :%s but §rotation-2 now sits at :%d" % (cited.group(1), arc_line)
        assert "| THE PARTITION LAW (the load-bearing claim)" not in src, "the moved block came back into NAMED.md"
        assert arc.count(MARK) == 1, "the archive carries %d copies of §rotation-2" % arc.count(MARK)
        print("archived region %d B | §rotation-2 at docs/named-archive-m333-rows.md:%d | full sha1=%s"
              % (len(body.encode("utf-8")), arc_line, sha))
        return 0

    # perform
    assert MARK not in arc, "the archive already carries §rotation-2 — refusing a duplicate region"
    assert "§rotation-1" in arc and "(§rotation-1 ends" in arc, "rotation-1's terminator missing — do not append blind"
    a = src.index(START)
    b = src.index(END)
    assert src.count(START) == 1 and src.count(END) == 1, "START/END must be unique"
    moved = src[a:b]
    assert moved.rstrip().endswith("| V |"), "the M315 block does not end where expected: %r" % moved[-40:]
    arc_line = arc.count("\n") + 2  # marker will sit after a blank line appended at EOF
    new_arc = arc.rstrip("\n") + "\n\n" + MARK + "\n\n" + moved.rstrip("\n") + "\n\n" + TERMINATOR + "\n"
    sha = hashlib.sha1(moved.strip("\n").encode("utf-8")).hexdigest()
    # region_bounds hashes MARK..TERMINATOR body; make the stored body match exactly
    body = new_arc[new_arc.index(MARK) + len(MARK):new_arc.index(TERMINATOR)].strip("\n")
    sha = hashlib.sha1(body.encode("utf-8")).hexdigest()
    new_src = src[:a] + stub_for(sha, arc_line) + src[b:]
    io.open(ARC, "w", encoding="utf-8").write(new_arc)
    io.open(NAMED, "w", encoding="utf-8").write(new_src)
    print("rotated: NAMED.md %d -> %d B (headroom to 250,000: %d B) | §rotation-2 at :%d sha1=%s"
          % (len(src.encode()), len(new_src.encode()), 250000 - len(new_src.encode()), arc_line, sha[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
