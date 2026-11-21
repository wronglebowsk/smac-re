# -*- coding: utf-8 -*-
"""s311 close-out #2: NEXT_PROMPT.md patched BY SECTION, with the retired (x2)/(x3)/
(x4)/(x5) one-liners moved VERBATIM to docs/pick-archive.md §trim-s311-chain1
(sha1 byte-exactness asserted), the DOC CAP line re-measured, and the final size
asserted <= 12,000 B before anything is written."""
import hashlib, io, os, sys
ROOT = os.path.expanduser("~/reverse/smac")
NP = os.path.join(ROOT, "NEXT_PROMPT.md")
ARC = os.path.join(ROOT, "docs", "pick-archive.md")


def rd(p):
    return io.open(p, encoding="utf-8").read()


def wr(p, s):
    io.open(p, "w", encoding="utf-8").write(s)


s = rd(NP)
moves = []

# ---- 1. retire the answered (x2)..(x5) one-liners VERBATIM
A1 = "(x2) `ds:0x985aec`"
A2 = "the 'multi' menu label (M328)."
i1 = s.index(A1)
i2 = s.index(A2, i1) + len(A2)
chunk = s[i1:i2]
assert s.count(chunk) == 1, "chunk not unique"
moves.append(("the (x2)-(x5) OPEN-LEADS one-liners", chunk))
sha = hashlib.sha1(chunk.encode("utf-8")).hexdigest()

NEW = ("(x2) ANSWERED M332 (`ds:0x985aec` = the runtime mirror of the win-INI pref "
       "`\"Difficulty\"`; master `ds:0x92bde8`; pref map `0x92bde8..0x92bf14` - `## M332`); "
       "(x3)/(x4) ANSWERED M331; (x5) the 'multi' label only (`92bdf8` = the pref `Top Menu`); "
       "(x6) NEW (M332): the difficulty INDEX->label order (cmps top out at 4, M330's k-table "
       "needs k=2 at >=5); the pref block's other writers; `0x8f0090`'s consumer; callee "
       "`0x5f1394`")
s = s[:i1] + NEW + s[i2:]

# ---- 2. DOC CAP line re-measured
oldcap = "**DOC CAP: `NAMED.md` 244,581 B / 250,000 FAIL (5,419 B headroom, `wc -c` s309"
named = len(rd(os.path.join(ROOT, "NAMED.md")).encode())
head = 250000 - named
j = s.index(oldcap)
k = s.index("\n", j)
s = s[:j] + ("**DOC CAP: `NAMED.md` %d B / 250,000 FAIL (%d B headroom, `wc -c` s311) - AT the "
             "5 KB rotation trigger; `scripts/m332_named_rotate{,2}.py` did two sha1-asserted "
             "rotations this fire. ROTATE FIRST before adding a block.**" % (named, head)) + s[k:]

# ---- 2b. (there is no §FIRST section any more - it moved to the s299 archive; the
#      narrative trim there was dropped rather than guessed at)

# ---- 2c. the two stale tail pointer lines -> one compact line
L1 = "M325 VERBATIM: §trim-s301-chain2 (a); NAMED ## M325."
L2 = "M326 VERBATIM: §trim-s304-chain2 (a); NAMED ## M326."
_ti = s.index(L1)
_tj = s.index(L2, _ti) + len(L2)
_tail = s[_ti:_tj]
assert s.count(_tail) == 1
moves.append(("the M325/M326 tail pointer lines", _tail))
s = s[:_ti] + "Pointers: M325 §trim-s301-chain2 (a); M326 §trim-s304-chain2 (a); NAMED governs." + s[_tj:]

# ---- 3. THE PICK index line: the answered option, and the (x) list is still the option
s = s.replace("only (ix) left, box-GATED, and the **(x) OPEN-LEADS** list below is the "
              "analysis-only option;",
              "only (ix) left, box-GATED, and the **(x) OPEN-LEADS** list below is the "
              "analysis-only option (x2/x3/x4 answered);", 1)

out = s
n = len(out.encode())
print("NEXT_PROMPT would be %d/12000 B (moving out %d B in %d pieces)"
      % (n, sum(len(t.encode()) for _, t in moves), len(moves)))
assert n <= 12000, ("NEXT_PROMPT over cap", n)

# ---- 4. the archive append (every moved piece, sha1-asserted on read-back)
before = rd(ARC)
add = ""
for label, text in moves:
    add += ("\n\n## §trim-s311-chain1 (M332 headroom): %s, moved VERBATIM out of "
            "`NEXT_PROMPT.md` (sha1 %s, byte-exact asserted by `scripts/m332_trim_s311.py`; "
            "(x2) and half of (x5) ANSWERED by M332, (x3)/(x4) by M331)\n\n%s\n"
            % (label, hashlib.sha1(text.encode("utf-8")).hexdigest(), text))
wr(ARC, before + add)
back = rd(ARC)
for label, text in moves:
    assert text in back, "archive lost: " + label

wr(NP, out)
print("retired %d B to §trim-s311-chain1 (sha1 %s)" % (len(chunk.encode()), sha[:12]))
print("NEXT_PROMPT.md now %d/12000 B" % len(rd(NP).encode()))
