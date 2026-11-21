# -*- coding: utf-8 -*-
"""M333 NEXT_PROMPT cap split (s313-chain1, docs/s313-caps).

NEXT_PROMPT.md was 11,986 / 12,000 B (14 B under the warn line, and the fail line is
16,000) — a milestone may not start on a doc 30 B from a gate it has to write into, so the
closed pick-row prose moves VERBATIM to `docs/pick-archive.md` BEFORE `## M333` is added.

Two regions move, each bounded by its own MARKER + TERMINATOR so a later append to the same
archive can never silently change an earlier region's hash (the s312 `--verify` defect: the
first rotation hashed to EOF and broke the moment the second one appended).  The OPEN leads
stay in NEXT_PROMPT — retiring the ANSWERED rows is what frees the bytes, not hiding the
next pick.

    python3 scripts/m333_nextprompt_trim.py           # perform the moves
    python3 scripts/m333_nextprompt_trim.py --verify   # re-hash both archived regions
"""
import argparse
import hashlib
import io
import os
import sys

ROOT = os.path.expanduser("~/reverse/smac")
PROMPT = os.path.join(ROOT, "NEXT_PROMPT.md")
ARC = os.path.join(ROOT, "docs", "pick-archive.md")
CAP = 11500  # the fire's own floor: leaves >500 B before the 12,000 warn for the M333 row

A_MARK_START = "  CLOSED pick rows (v = M319, vi = M321) VERBATIM"
A_MARK_END = "  Lists live in NAMED ## M310-M325 + the `## B<n>` blocks."
B_MARK_START = "M320/M323/M324 result one-liners VERBATIM"

A_TAG = "## §trim-s313-chain1 (M333 headroom) region-A: the closed pick rows (v/vi/vii/viii/x2/x3/x4) + the B27 row, moved VERBATIM out of `NEXT_PROMPT.md`"
B_TAG = "## §trim-s313-chain1 (M333 headroom) region-B: the merged result one-liner pointers, moved VERBATIM out of `NEXT_PROMPT.md`"
TERM = "(§trim-s313-chain1 ends; anything below belongs to a later trim.)"

A_NEW = """  CLOSED pick rows (v = M319, vi = M321, vii = M327, viii = M329, x2 = M332, x3/x4 = M331, B27)
  VERBATIM at `docs/pick-archive.md` §trim-s313-chain1 region-A (sha1 `SHA_A`, byte-exact asserted
  by `scripts/m333_nextprompt_trim.py --verify`); the per-id `NAMED ## <id>` blocks GOVERN and carry
  every ACCEPT/harness digest. OPEN analysis-only leads, each with a NAMED question: **(x1) the 34
  feeder slots `0x984d48 + 48*slot` — the slot noun and why bit5 halves (M330 G10)**; (x5) the
  'multi' label only (`92bdf8` = the pref `Top Menu`); (x6) NEW (M332): the difficulty INDEX->label
  order (cmps top out at 4, M330's k-table needs k=2 at >=5); other writers of the
  0x92bde8..0x92bf14 pref block; `0x8f0090`'s consumer; callee `0x5f1394`. Generate a
  combat/tech/victory pick before taking one: no footing exists.
"""

B_NEW = """Result one-liners M320/M323/M324/M325/M326/M330/M331 + the M330 #340 sidecar note:
`docs/pick-archive.md` §trim-s313-chain1 region-B (sha1 `SHA_B`, `--verify`); the per-id
`NAMED ## <id>` blocks GOVERN.
"""


def regions(text):
    """(regionA, regionB) re-read from the archive, each bounded by TAG..TERMINATOR."""
    out = []
    for tag in (A_TAG, B_TAG):
        a = text.index(tag)
        b = text.index(TERM, a)
        out.append(text[a + len(tag):b].strip("\n"))
    return out[0], out[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    arc = io.open(ARC, encoding="utf-8").read()

    if args.verify:
        ra, rb = regions(arc)
        sha_a, sha_b = (hashlib.sha1(r.encode("utf-8")).hexdigest() for r in (ra, rb))
        prompt = io.open(PROMPT, encoding="utf-8").read()
        cited = {t: [ln for ln in prompt.splitlines() if ("region-" + t) in ln and "sha1 `" in ln]
                 for t in ("A", "B")}
        for t, want in (("A", sha_a[:12]), ("B", sha_b[:12])):
            assert len(cited[t]) == 1, "region-%s: expected exactly 1 citing line, got %d" % (t, len(cited[t]))
            got = cited[t][0].split("sha1 `")[1].split("`")[0]
            assert got == want, "region-%s sha1 mismatch: recorded %s, recomputed %s" % (t, got, want)
        print("region-A %d B sha1=%s\nregion-B %d B sha1=%s" %
              (len(ra.encode()), sha_a[:12], len(rb.encode()), sha_b[:12]))
        for tag, region_ in ((A_TAG, ra), (B_TAG, rb)):
            assert "VERBATIM" in tag and region_, "empty region " + tag
        assert "region-A (sha1" in prompt, "the pointer to region-A vanished"
        print("PASS trim-verify: both regions re-hash byte-exact against the pointers in NEXT_PROMPT.md")
        return 0

    src = io.open(PROMPT, encoding="utf-8").read()
    for anchor in (A_MARK_START, A_MARK_END, B_MARK_START):
        assert anchor in src, "anchor missing from NEXT_PROMPT.md: " + anchor[:40]
    assert "§trim-s313-chain1" not in src, "trim already applied"
    assert "§trim-s313-chain1" not in arc, "archive already carries the s313 trim"

    a1 = src.index(A_MARK_START)
    a2 = src.index(A_MARK_END)
    assert a1 < a2
    region_a = src[a1:a2].rstrip("\n")
    b1 = src.index(B_MARK_START)
    assert b1 > a2
    region_b = src[b1:].rstrip("\n")
    sha_a = hashlib.sha1(region_a.encode("utf-8")).hexdigest()
    sha_b = hashlib.sha1(region_b.encode("utf-8")).hexdigest()

    io.open(ARC, "a", encoding="utf-8").write(
        "\n\n%s\n\n%s\n\n%s\n\n%s\n\n%s\n\n%s\n" % (A_TAG, region_a, TERM, B_TAG, region_b, TERM))

    back = io.open(ARC, encoding="utf-8").read()
    ra, rb = regions(back)
    assert ra == region_a and rb == region_b, "an archived region is not byte-identical"

    new = src[:a1] + A_NEW.replace("SHA_A", sha_a[:12]) + src[a2:b1] + B_NEW.replace("SHA_B", sha_b[:12]) + "\n"
    assert len(new.encode("utf-8")) <= CAP, "NEXT_PROMPT only got to %d B" % len(new.encode("utf-8"))
    # nothing that names an OPEN lead may have been dropped
    for token in ("0x984d48", "bit5 halves", "92bdf8", "0x8f0090", "0x5f1394", "(ix)"):
        assert token in new, "the trim lost an open-lead token: " + token
    io.open(PROMPT, "w", encoding="utf-8").write(new)
    print("region-A %d B sha1=%s | region-B %d B sha1=%s" %
          (len(region_a.encode()), sha_a[:12], len(region_b.encode()), sha_b[:12]))
    print("NEXT_PROMPT.md %d -> %d B (warn 12,000; headroom %d B) | pick-archive + %d B" %
          (len(src.encode()), len(new.encode()), 12000 - len(new.encode()),
           len(back.encode()) - len(arc.encode())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
