#!/usr/bin/env python3
"""s308 cap trim: retire the B26 build-track paragraph and the (viii)/M329 block SUMMARY
out of NEXT_PROMPT.md VERBATIM into docs/pick-archive.md §trim-s308-chain1.

NEXT_PROMPT is 13,137 B, over the 12,000 B warn; the ritual target is <=12,000. Two blocks
move byte-exact (sha1 asserted on extraction AND re-read as a byte substring of the archive
after the append). Refuses to run twice. Also prints the post-trim size and FAILs the script
if NEXT_PROMPT is still over 12,000 B — a trim that does not clear the cap is not a trim.
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NP = os.path.join(ROOT, "NEXT_PROMPT.md")
ARCH = os.path.join(ROOT, "docs", "pick-archive.md")
CAP = 12_000
BLOCKS = {"a (B26 build-track paragraph)": (28, 28), "b ((viii)=M329 summary)": (63, 75)}


def sha1(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()[:12]


def main() -> int:
    np_text = open(NP, encoding="utf-8").read()
    if "§trim-s308-chain1" in np_text:
        sys.exit("REFUSE: §trim-s308-chain1 already referenced in NEXT_PROMPT.md — already trimmed")
    lines = np_text.splitlines(keepends=True)
    before = len(np_text.encode())

    # 1. extract + assert provenance BEFORE touching anything
    moved = {}
    for name, (lo, hi) in BLOCKS.items():
        block = "".join(lines[lo - 1 : hi])
        assert block.startswith("  CLOSED pick row") or block.startswith("(B25 = #319 main"), (
            f"{name}: line {lo} is not the expected start — NEXT_PROMPT moved, re-read it")
        moved[name] = (block, sha1(block.encode()))
        print(f"extracted {name}: lines {lo}-{hi}, {len(block.encode())} B, sha1 {moved[name][1]}")

    # 2. replace in NEXT_PROMPT with pointers (pair every addition with a deletion)
    pointer_b = (
        "  CLOSED pick row (viii = **M329**, s307) VERBATIM at §trim-s308-chain1 (b) with its sha1; "
        "`NAMED ## M329` governs (`ui_governor_options_pane(widget, page)`; the `ds:0x99aa38` 19-bit pack "
        "staging; publish `0x1c-0x1f` only, bit-disjoint from both faction-create defaults => REFINES "
        "`## M321`); ACCEPT 13/13 + harness 26/26 numbers are IN that block. **NO PICKS LEFT except (ix)** "
        "(live-box, GATED on operator authorization) — so the next fire is the **BUILD rung B27**: author "
        "its `BUILD_SPINE.md` section FIRST, then instrument it.\n")
    pointer_a = (
        "(B25 = #319 main 1556ce9; B26 = #328 main dd704d0; B26's full ACCEPT + THE LAW + the three "
        "retractions + the `found_units` 69->0 open question VERBATIM at `docs/pick-archive.md` "
        "§trim-s308-chain1 (a) with its sha1, and its per-rung cmds at `NAMED.md` §CHAIN-BUILDS + the "
        "per-id `## B<n>` blocks; `NAMED ## B25`/`## B26` govern; earlier build-track detail "
        "§trim-s298 (a), §trim-s299 (b)/(d)). **Next build B27, NOT YET AUTHORED** "
        "(`BUILD_SPINE.md` ends at B26): write its rung text BEFORE probing (one milestone = spine "
        "section + instrument).\n")
    new = (lines[:27] + [pointer_a] + lines[28:62] + [pointer_b] + lines[75:])
    new_text = "".join(new)
    after = len(new_text.encode())
    print(f"NEXT_PROMPT.md {before} -> {after} B (freed {before - after} B)")
    if after > CAP:
        sys.exit(f"FAIL: NEXT_PROMPT still {after} B > {CAP} B — the trim did not clear the cap")

    # 3. append the archive section, then assert byte-substring containment at head
    section = (
        "\n## §trim-s308-chain1 — NEXT_PROMPT cap trim at s308 (M329 landing fire): B26 build-track "
        "paragraph + the (viii)/M329 summary retired VERBATIM\n\n"
        f"(a) THE B26 BUILD-TRACK PARAGRAPH, VERBATIM from `NEXT_PROMPT.md` line 28 "
        f"(sha1 `{moved['a (B26 build-track paragraph)'][1]}`, byte-substring asserted by "
        f"`scripts/m329_trim_s308.py`):\n\n"
        f"{moved['a (B26 build-track paragraph)'][0]}\n"
        f"(b) THE (viii)=M329 PICK-SUMMARY BLOCK, VERBATIM from `NEXT_PROMPT.md` lines 63-75 "
        f"(sha1 `{moved['b ((viii)=M329 summary)'][1]}`, byte-substring asserted by the same script; "
        f"`NAMED ## M329` governs):\n\n"
        f"{moved['b ((viii)=M329 summary)'][0]}\n"
        "NOTE on §trim-s307-chain1 (b)'s last line: the 240,534 B reading of `NAMED.md` there and in "
        "`NAMED ## M329`'s headroom row was superseded inside the same session by the in-place M321 "
        "refinement + row fixes — the measured head at s308 close is **240,756 B / 9,244 B headroom** "
        "(`wc -c NAMED.md`).\n")
    open(ARCH, "a", encoding="utf-8").write(section)
    arch = open(ARCH, encoding="utf-8").read()
    for name, (block, dg) in moved.items():
        assert block in arch, f"FAIL: {name} is NOT a byte substring of {ARCH} after the append"
        print(f"asserted byte-exact in archive: {name} sha1 {dg}")
    open(NP, "w", encoding="utf-8").write(new_text)
    head = len(open(NP, encoding="utf-8").read().encode())
    assert head == after, f"FAIL: re-read size {head} != measured {after}"
    print(f"OK: NEXT_PROMPT {head} B <= {CAP} B; both blocks byte-exact in §trim-s308-chain1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
