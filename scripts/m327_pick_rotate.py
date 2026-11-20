#!/usr/bin/env python3
# s305 docs rotation (NEXT_PROMPT.md cap): the M327 ANSWERED-PICK paragraph is retired
# VERBATIM from §THE PICK of NEXT_PROMPT.md to docs/pick-archive.md §trim-s305-chain1 (a),
# replaced by a one-line pointer. The script asserts (a) the block it lifts appears exactly
# once, (b) the bytes appended to the archive are byte-identical to the lifted block
# (sha1 printed), (c) the file shrinks. Run from the repo root.
import hashlib, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NP = os.path.join(ROOT, "NEXT_PROMPT.md")
ARC = os.path.join(ROOT, "docs", "pick-archive.md")

BLOCK = (
    "  ANSWERED PICK (vii) -> **M327** (s304, zero box): +10 is a SIGNED TYPE INDEX into the save's OWN\n"
    "  512x52 B type array (26,624 B at count_off+4+count_len+3584, 4,096 B before the unit array;\n"
    "  +10//64 == owner on 25/25) — the 25 exempt records ARE units; the coord exemption is OURS and bites\n"
    "  only on the self-poked m113map.SAV. RETRACTS `sim/save.py:52` + ## B25's trap-14 in place. 11/11\n"
    "  ee77ddb39e8ec202 (`m327_typeband_census.txt:769`), harness 22/22; `NAMED ## M327` governs.\n"
)
POINTER = ("  CLOSED pick row (vii = M327) VERBATIM at §trim-s305-chain1 (a) "
           "(sha1 %s); `NAMED ## M327` governs (harness 23/23 since s305).\n")
HEAD = (
    "\n## §trim-s305-chain1 (a) the ANSWERED PICK (vii) -> M327 paragraph, VERBATIM from §THE PICK of\n"
    "NEXT_PROMPT.md at the M327 landing (s305) (retired so the file stays under the 12,000 B warn cap;\n"
    "sha1 %s of the block below, byte-exact). `NAMED ## M327` governs; the harness count moved to 23/23\n"
    "at s305 when the `+12` census became a G3 clause (MU23) — `NAMED ## M327` carries the current number.\n\n"
)


def main():
    np_txt = open(NP, encoding="utf-8").read()
    n = np_txt.count(BLOCK)
    if n != 1:
        print("FAIL: the block to rotate occurs %d times (want 1)" % n)
        return 1
    sha = hashlib.sha1(BLOCK.encode()).hexdigest()[:12]
    arc = open(ARC, encoding="utf-8").read()
    if not arc.endswith("\n"):
        arc += "\n"
    new_arc = arc + (HEAD % sha) + BLOCK
    new_np = np_txt.replace(BLOCK, POINTER % sha, 1)
    before, after = len(np_txt.encode()), len(new_np.encode())
    # byte-exactness of what moved
    if new_arc.count(BLOCK) != 1:
        print("FAIL: lifted block not byte-exact in the archive")
        return 1
    if after >= before:
        print("FAIL: NEXT_PROMPT did not shrink (%d -> %d)" % (before, after))
        return 1
    open(NP, "w", encoding="utf-8").write(new_np)
    open(ARC, "w", encoding="utf-8").write(new_arc)
    print("OK rotated: NEXT_PROMPT %d -> %d B (sha1 %s); archive %d B"
          % (before, after, sha, len(new_arc.encode())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
