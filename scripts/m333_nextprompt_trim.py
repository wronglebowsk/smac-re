# -*- coding: utf-8 -*-
"""M333 NEXT_PROMPT cap split (s313-chain1, docs/s313-caps).

NEXT_PROMPT.md was 11,986 / 12,000 B (14 B under the warn line; fail 16,000) — a milestone
may not start on a doc 30 B from a gate it has to write into, so the closed pick-row prose
moves VERBATIM to `docs/pick-archive.md` BEFORE `## M333` is added.

Two regions move, each bounded by its own MARKER + TERMINATOR so a later append to the same
archive can never silently change an earlier region's hash (the s312 `--verify` defect).

Triaged from the #347 review (all 3 findings against this file ACCEPTED, none weakened):
  F1  the "(ix)" survival assert was checking the WHOLE hot file while the sentence that
      explains (ix) had just been archived. The hot replacement text now CARRIES the
      `(ix) (live-box, operator-GATED)` clause, and the asserts name the exact phrases.
  F2  region-B was "marker to EOF" — the same class the PR claims to fix. It is now bounded
      by an explicit end anchor and the script refuses to run if ANYTHING else follows.
  F6  the region tags and the hot pointer now say what is actually hashed: the closed pick
      rows PLUS the superseded open-lead census.

    python3 scripts/m333_nextprompt_trim.py            # perform the moves
    python3 scripts/m333_nextprompt_trim.py --relabel  # re-emit pointer/tag text from the constants
    python3 scripts/m333_nextprompt_trim.py --verify   # re-hash both regions, check both pointers
"""
import argparse
import hashlib
import io
import os
import re
import sys

ROOT = os.path.expanduser("~/reverse/smac")
PROMPT = os.path.join(ROOT, "NEXT_PROMPT.md")
ARC = os.path.join(ROOT, "docs", "pick-archive.md")
CAP = 11800  # the fire's own floor, below the 12,000 warn, so the M333 row still fits

A_MARK_START = "  CLOSED pick rows (v = M319, vi = M321) VERBATIM"
A_MARK_END = "  Lists live in NAMED ## M310-M325 + the `## B<n>` blocks."
B_MARK_START = "M320/M323/M324 result one-liners VERBATIM"
B_MARK_END = "\n\n\nEND-OF-NEXT_PROMPT-MARKER-NEVER-PRESENT"  # replaced at runtime by EOF + assert

A_TAG = ("## §trim-s313-chain1 (M333 headroom) region-A: the closed pick rows "
         "(v/vi/vii/viii/x2/x3/x4) + the B27 row + the SUPERSEDED open-lead census they "
         "sat in, moved VERBATIM out of `NEXT_PROMPT.md`")
B_TAG = ("## §trim-s313-chain1 (M333 headroom) region-B: the merged result one-liner "
         "pointers (M320/M323/M324/M325/M326/M330/M331 + the #340 sidecar note), moved "
         "VERBATIM out of `NEXT_PROMPT.md`")
TERM = "(§trim-s313-chain1 ends; anything below belongs to a later trim.)"

# Every open lead stays in the hot file, INCLUDING the box-gated (ix) — the s313 review's F1:
# an assert that "(ix)" survived is only honest if the hot file still explains what (ix) is.
A_NEW = """  CLOSED pick rows + the superseded open-lead census they sat in (v = M319, vi = M321, vii = M327,
  viii = M329, x2 = M332, x3/x4 = M331, B27) VERBATIM at `docs/pick-archive.md` §trim-s313-chain1
  region-A (sha1 `SHA_A`, byte-exact asserted by `scripts/m333_nextprompt_trim.py --verify`); the
  per-id `NAMED ## <id>` blocks GOVERN and carry every ACCEPT/harness digest.
  **NO STATIC PICKS LEFT** except **(ix)** (live-box, operator-GATED), so the analysis-only
  option is this OPEN-LEADS
  list, each with a NAMED question: **(x1) the 34 feeder slots `0x984d48 + 48*slot` — the slot noun
  and why bit5 halves (M330 G10)**; (x5) the 'multi' label only (`92bdf8` = the pref `Top Menu`);
  (x6) NEW (M332): the difficulty INDEX->label order (cmps top out at 4, M330's k-table needs k=2
  at >=5); other writers of the 0x92bde8..0x92bf14 pref block; `0x8f0090`'s consumer; callee
  `0x5f1394`. Generate a combat/tech/victory pick before taking one: no footing exists.
"""

B_NEW = """Result one-liners M320/M323/M324/M325/M326/M330/M331 + the M330 #340 sidecar note:
`docs/pick-archive.md` §trim-s313-chain1 region-B (sha1 `SHA_B`, `--verify`); the per-id
`NAMED ## <id>` blocks GOVERN.
"""

# phrases the hot file must still carry after the trim (F1: exact phrases, not loose tokens)
MUST_KEEP = ["(x1) the 34 feeder slots", "bit5 halves", "92bdf8", "0x8f0090", "0x5f1394",
             "except **(ix)** (live-box, operator-GATED)", "NO STATIC PICKS LEFT",
             "(x6) NEW (M332)", "region-A (sha1", "region-B (sha1"]


def tag_line(text, which):
    """The one archive header for region-<which>, whatever its current wording (so a relabel of
    the wording can never blind the reader to the region it hashes)."""
    hits = [ln for ln in text.splitlines()
            if ln.startswith("## §trim-s313-chain1") and ("region-" + which) in ln]
    assert len(hits) == 1, "expected exactly one §trim-s313-chain1 region-%s tag, got %d" % (which, len(hits))
    return hits[0]


def regions(text):
    """(regionA, regionB) re-read from the archive, each bounded by TAG..TERMINATOR."""
    out = []
    for which in ("A", "B"):
        tag = tag_line(text, which)
        a = text.index(tag)
        b = text.index(TERM, a)
        out.append(text[a + len(tag):b].strip("\n"))
    return out[0], out[1]


def shas(arc):
    ra, rb = regions(arc)
    return hashlib.sha1(ra.encode("utf-8")).hexdigest(), hashlib.sha1(rb.encode("utf-8")).hexdigest(), ra, rb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--relabel", action="store_true",
                    help="re-emit the hot pointers + archive tags from the constants (no move)")
    args = ap.parse_args()
    src = io.open(PROMPT, encoding="utf-8").read()
    arc = io.open(ARC, encoding="utf-8").read()

    if args.verify:
        sha_a, sha_b, ra, rb = shas(arc)
        for t, want in (("A", sha_a[:12]), ("B", sha_b[:12])):
            cited = [ln for ln in src.splitlines() if ("region-" + t) in ln and "sha1 `" in ln]
            assert len(cited) == 1, "region-%s: expected exactly 1 citing line, got %d" % (t, len(cited))
            got = cited[0].split("sha1 `")[1].split("`")[0]
            assert got == want, "region-%s sha1 mismatch: recorded %s, recomputed %s" % (t, got, want)
            assert len(re.findall(r"[0-9a-f]{12}", got)) == 1, "region-%s digest is not 12 hex" % t
        for tag in (A_TAG, B_TAG):
            assert arc.count(tag) == 1, "archive tag not unique: " + tag[:40]
        for phrase in MUST_KEEP:
            assert phrase in src, "the hot file lost a required phrase: " + phrase
        print("region-A %d B sha1=%s\nregion-B %d B sha1=%s" %
              (len(ra.encode("utf-8")), sha_a[:12], len(rb.encode("utf-8")), sha_b[:12]))
        print("PASS trim-verify: both regions re-hash byte-exact against the pointers in "
              "NEXT_PROMPT.md, both tags unique, every open-lead phrase still in the hot file")
        return 0

    if args.relabel:
        sha_a, sha_b, _, _ = shas(arc)
        a1 = src.index("  CLOSED pick rows")
        a2 = src.index(A_MARK_END)
        b1 = src.index("Result one-liners M320")
        new = (src[:a1] + A_NEW.replace("SHA_A", sha_a[:12]) + src[a2:b1]
               + B_NEW.replace("SHA_B", sha_b[:12]) + "\n")
        for phrase in MUST_KEEP:
            assert phrase in new, "relabel dropped a required phrase: " + phrase
        assert len(new.encode("utf-8")) <= CAP, "NEXT_PROMPT at %d B after relabel" % len(new.encode("utf-8"))
        io.open(PROMPT, "w", encoding="utf-8").write(new)
        # the archive tags move to the new wording in place; the hashed BODIES do not change,
        # so both digests stay valid (that is what --verify re-proves right after)
        back = io.open(ARC, encoding="utf-8").read()
        old_tags = [ln for ln in back.splitlines() if ln.startswith("## §trim-s313-chain1")]
        assert len(old_tags) == 2, "expected 2 s313 tags in the archive, got %d" % len(old_tags)
        for old in old_tags:
            want = A_TAG if "region-A" in old else B_TAG
            back = back.replace(old, want, 1)
        io.open(ARC, "w", encoding="utf-8").write(back)
        print("relabeled: NEXT_PROMPT %d -> %d B; archive tags rewritten, region bodies untouched" %
              (len(src.encode()), len(new.encode())))
        return 0

    # ---- perform ----
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
    # F2: a BOUNDED region. Everything from the marker to EOF is only allowed if what follows
    # the marker's own paragraph is whitespace — otherwise refuse, never silently archive it.
    tail_after = src[b1:]
    paras = tail_after.split("\n\n")
    region_b = paras[0].rstrip("\n")
    rest = "\n\n".join(paras[1:]).strip()
    assert rest == "", ("region-B would swallow %d B that follow it; add a B_MARK_END anchor "
                        "before proceeding" % len(rest.encode("utf-8")))
    sha_a = hashlib.sha1(region_a.encode("utf-8")).hexdigest()
    sha_b = hashlib.sha1(region_b.encode("utf-8")).hexdigest()

    io.open(ARC, "a", encoding="utf-8").write(
        "\n\n%s\n\n%s\n\n%s\n\n%s\n\n%s\n\n%s\n" % (A_TAG, region_a, TERM, B_TAG, region_b, TERM))

    back = io.open(ARC, encoding="utf-8").read()
    ra, rb = regions(back)
    assert ra == region_a and rb == region_b, "an archived region is not byte-identical"

    new = src[:a1] + A_NEW.replace("SHA_A", sha_a[:12]) + src[a2:b1] + B_NEW.replace("SHA_B", sha_b[:12]) + "\n"
    assert len(new.encode("utf-8")) <= CAP, "NEXT_PROMPT only got to %d B" % len(new.encode("utf-8"))
    for phrase in MUST_KEEP:
        assert phrase in new, "the trim lost a required phrase: " + phrase
    io.open(PROMPT, "w", encoding="utf-8").write(new)
    print("region-A %d B sha1=%s | region-B %d B sha1=%s" %
          (len(region_a.encode()), sha_a[:12], len(region_b.encode()), sha_b[:12]))
    print("NEXT_PROMPT.md %d -> %d B (warn 12,000; headroom %d B) | pick-archive + %d B" %
          (len(src.encode()), len(new.encode()), 12000 - len(new.encode()),
           len(back.encode()) - len(arc.encode())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
