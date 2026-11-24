#!/usr/bin/env python3
"""M342 headroom rotation: move the settled M329 block VERBATIM out of NAMED.md.

NAMED.md sat at 246,313 B (3,687 B under its 250,000 B cap - inside the kickoff's 5 KB
rotate-first trigger) and M342 must add a block, so the M329 block (settled: s307, static,
zero box, 13/13 + 26/26, no rung cites it) moves byte-exactly into
`docs/named-archive-m329-rows.md`; NAMED.md keeps a stub with the ACCEPT header (digest,
harness counts) and ONE LINE PER CLAIM.  The moved region's sha1 is PINNED and `--verify`
re-asserts it, so an edit to either copy fails loudly instead of forking the registry.

  python3 scripts/m342_named_rotate.py            # do the move (no-op once done)
  python3 scripts/m342_named_rotate.py --verify   # re-assert sha1 + the full block's absence
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCHIVE = os.path.join(ROOT, "docs", "named-archive-m329-rows.md")
EXPECT_SHA1 = "ccee72a56f16b4b43829b904945cee08ac827410"
START = "## M329 (s307, pick (viii), STATIC, zero box"
END = "## B27 (s309 BUILD, zero box)"
HEADER = ("# NAMED archive - M342 headroom rotation (s322): the M329 block VERBATIM\n"
          "(moved by `scripts/m342_named_rotate.py`; the region's sha1 is pinned to `%s` -\n"
          "run `--verify` after any edit; NAMED.md's stub keeps the ACCEPT header + one line per claim)\n\n")

STUB = """## M329 (s307, pick (viii), STATIC, zero box; ACCEPT `python3 -u scripts/m329_scratchtree.py` -> 13/13, digest `757e40a7ed04abda`, 2 runs byte-identical; harness `scripts/m329_mutate.py` 26/26, base reddened `[]`) - `FUN_0041a8f0` = `ui_governor_options_pane(widget, page)`. FULL-LENGTH TABLE VERBATIM at `docs/named-archive-m329-rows.md:5` (sha1 `%s`); this stub governs, one line per claim

| # | claim (one line) | conf |
|---|---|---|
| 1 | `FUN_0041a8f0` (1,403 B) is a thiscall member of the widget singleton `0x6a9480` (`mov edi,ecx`) | V |
| 2 | exactly 4 direct `e8` call sites / 4 owners (`0x41e3bd`, `0x49b306`, `0x4a9e0e`, +1) | V |
| 3 | naming basis: the only `push imm32>=0x400000` in frame = `0x6899ec`='GOVOPTIONS' @`0x41aba5` -> save writer `0x6267a5` | V |
| 4 | 3 chains in the frame fold to stride 304 = the own-faction base array `304*idx+0x95da10` | V |
| 5 | `ds:0x99aa38` = the pack staging dword: 20 stores, 19 legs, 19 distinct record masks | V |
| 6 | write-back: of the 19 legs, 11 resolve to a direct `or mask @addr` on the record | V |
| 7 | `0x94d600`-field census: exactly 8 refs, 3 writers (2 textual forms of one site) | V |
| 8 | `[rec+0x38]` bit `0x40` = the ARRIVAL test @`0x41ade4`, after the publish, arg==0 phase only | V |
| 9 | 6 rivals refuted on the printed numbers (free function / cursor-driven / unit array / dword overwrite / ...) | V |
| 10 | mutant sets MEASURED (`M329_MUT_MEASURE=1`): 25 scored + 1 NO-OP, every gate covered | V |
| 11 | OPEN: what the 19 record bits MEAN (4 published, 15 stay); who fills the scratch `+0x00..+0x18` in other frames | OPEN |
| 12 | REVIEW meta: this rotation family (`m329_named_rotate*.py`) already moved two settled blocks out of NAMED.md | meta |
| 13 | REVIEW box time: ZERO - everything is `scratch/m574/text.txt` + `ghidra_out/index.csv` | meta |
"""


def region(lines):
    """The FULL block, never the stub: the stub is identified by the same START prefix, so the
    block only counts when it still carries the original claim table header."""
    try:
        i = next(k for k, l in enumerate(lines) if l.startswith(START))
        j = next(k for k, l in enumerate(lines) if k > i and l.startswith(END))
    except StopIteration:
        return None, None, None
    block = lines[i:j]
    if "| claim | evidence | conf |" not in block:
        return None, None, None
    return i, j, "".join(l + "\n" for l in block)


def main(argv):
    verify = "--verify" in argv
    text = open(NAMED, encoding="utf-8").read()
    lines = text.split("\n")
    i, j, blob = region(lines)
    arch = open(ARCHIVE, encoding="utf-8").read() if os.path.exists(ARCHIVE) else None
    if verify:
        assert arch is not None, "archive missing"
        k = arch.find(START)
        assert k >= 0, "archive does not carry the M329 region"
        moved = arch[k:]
        moved = moved[:moved.find(END)] if END in moved else moved
        got = hashlib.sha1(moved.encode()).hexdigest()
        assert got == EXPECT_SHA1, "archive sha1 drift: %s" % got
        assert blob is None, "the FULL block is still in NAMED.md"
        assert len(text.encode()) < 250000, "NAMED.md over cap"
        print("VERIFY ok: archive sha1 %s, full block absent from NAMED.md, NAMED %d B"
              % (EXPECT_SHA1[:16], len(text.encode())))
        return 0
    if blob is None:
        print("already rotated (stub in place, archive %s)" % ("present" if arch else "MISSING"))
        return 0 if arch else 1
    sha = hashlib.sha1(blob.encode()).hexdigest()
    moved = HEADER % sha + blob
    if arch:
        moved = arch + "\n" + blob
    open(ARCHIVE, "w", encoding="utf-8").write(moved)
    stub = STUB % sha[:16]
    new = "".join(l + "\n" for l in lines[:i]) + stub + "".join(l + "\n" for l in lines[j:])
    open(NAMED, "w", encoding="utf-8").write(new)
    print("moved M329 (%d B) to %s, sha1 %s; NAMED %d -> %d B"
          % (len(blob), os.path.relpath(ARCHIVE, ROOT), sha, len(text.encode()), len(new.encode())))
    print("NOTE: pin EXPECT_SHA1 in this script to %s before --verify" % sha)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
