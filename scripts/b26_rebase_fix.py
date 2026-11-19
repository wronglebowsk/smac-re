#!/usr/bin/env python3
"""One-shot conflict-resolution repair for the s299 rebase onto chain 2's M324 merge.

Chain 2 (the M324 fire) invented `docs/pick-archive.md` §trim-s299 (a) = the M323 result
line, while chain 1's s299 rotation invented a DIFFERENT (a) (the B26 footer sentence) and
a (b) holding the SAME M323 line chain 2 already archived. The rebase merged the two files
textually, so the archive ended up with two (a) headings and a duplicate M323 block.

Measured before editing: the two M323 blocks are byte-identical inside, so chain 1's (b)
carries no information chain 2's (a) lacks. Resolution: keep chain 2's (a); DELETE chain 1's
duplicate (b); re-letter chain 1's (a) as (b) and fix the one NEXT_PROMPT pointer that named
it. Asserted, not assumed.
"""
import hashlib
import re

AR, NP = "docs/pick-archive.md", "NEXT_PROMPT.md"
ar = open(AR, encoding="utf-8").read()
np_txt = open(NP, encoding="utf-8").read()
before_ar, before_np = len(ar.encode()), len(np_txt.encode())
assert not re.search(r"^(<<<<<<<|=======|>>>>>>>)", ar, re.M), "conflict markers left in archive"

# --- locate the six s299 headings ---
H = "## \u00a7trim-s299 (%s) "
heads = [(m.start(), m.group(1)) for m in re.finditer(r"^## \u00a7trim-s299 \((\w)\) ", ar, re.M)]
assert [l for _, l in heads] == ["a", "a", "b", "c", "d", "e", "f"], heads
# order in the file: [theirs a][mine a][mine b][c][d][e][f]

def section(letter_pos, next_pos):
    return ar[letter_pos:next_pos]

theirs_a = section(heads[0][0], heads[1][0])
mine_a = section(heads[1][0], heads[2][0])
mine_b = section(heads[2][0], heads[3][0])

# --- ASSERT the duplicate: the M323 sentence chain 1 archived is inside chain 2's block ---
line = [l for l in mine_b.splitlines() if l.startswith("M323 RESULT (s295-chain2")]
assert len(line) == 1
m323 = line[0]
assert m323 in theirs_a, "chain 2's (a) does NOT contain the same M323 line - not a duplicate"
print("duplicate confirmed: M323 line (%d B, sha1 %s) present verbatim in chain 2's (a)"
      % (len(m323.encode()), hashlib.sha1(m323.encode()).hexdigest()[:16]))

# --- rebuild the archive: theirs (a) | mine re-lettered (b) | (c) (d) (e) (f) ---
mine_a_body = mine_a.replace("## \u00a7trim-s299 (a) ", "## \u00a7trim-s299 (b) ", 1)
new = (ar[:heads[0][0]] + theirs_a + mine_a_body + ar[heads[3][0]:])
assert re.findall(r"^## \u00a7trim-s299 \((\w)\) ", new, re.M) == list("abcdef"), "letters"
assert mine_a.replace("## \u00a7trim-s299 (a) ", "## \u00a7trim-s299 (b) ", 1) in new
open(AR, "w", encoding="utf-8").write(new)

# --- fix the one NEXT_PROMPT pointer that named chain 1's old (a) ---
old_ptr = "\u00a7trim-s298 (a) + \u00a7trim-s299 (a) + \u00a7trim-s299 (d)"
new_ptr = "\u00a7trim-s298 (a) + \u00a7trim-s299 (b) + \u00a7trim-s299 (d)"
assert np_txt.count(old_ptr) == 1, np_txt.count(old_ptr)
np_txt = np_txt.replace(old_ptr, new_ptr, 1)

# --- and shrink the B26 ACCEPT line: the laws themselves live in NAMED + trim-s299 (e) ---
old_laws = ("Its three laws (the container is LOADED, not just written; a round-aligned load "
            "is CONFLUENT; the non-carry is the in-progress MP budget, 69 units / 69 x-bytes "
            "vs control 0) and the four defects the gates caught are VERBATIM at "
            "\u00a7trim-s299 (e); `NAMED ## B26` governs.")
new_laws = ("THE LAW: the container is LOADED, not just written - the three laws and the four "
            "defects the gates caught are VERBATIM at \u00a7trim-s299 (e); `NAMED ## B26` governs.")
assert np_txt.count(old_laws) == 1
np_txt = np_txt.replace(old_laws, new_laws, 1)
open(NP, "w", encoding="utf-8").write(np_txt)

after_ar, after_np = len(new.encode()), len(np_txt.encode())
print("pick-archive %d -> %d B | NEXT_PROMPT %d -> %d B (warn 12000)"
      % (before_ar, after_ar, before_np, after_np))
print("under 12000: %s" % (after_np <= 12000))
