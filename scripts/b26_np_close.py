#!/usr/bin/env python3
"""One-shot doc rotation for the B26 close (s299).

Moves the B26 RESULT blob VERBATIM out of NEXT_PROMPT.md's BUILD TRACK line into
`docs/pick-archive.md` §trim-s299 (e), leaving a compact numbers+pointer in its place,
and repairs the `.:` join artifact the earlier one-shot (b26_np_add.py) left behind.

Byte-identity is ASSERTED: the blob is taken out of the file as a literal substring and
required to reappear unchanged in the archive, with its sha1 printed. Run once; after the
commit its anchors are stale by construction (same convention as s292_cap_check.py).
"""
import hashlib

NP, AR = "NEXT_PROMPT.md", "docs/pick-archive.md"
np_src = open(NP, encoding="utf-8").read()
ar_src = open(AR, encoding="utf-8").read()
before = len(np_src.encode())

# idempotence: if a previous run of this one-shot already appended (e)/(f), cut them off
CUT = "\n## \u00a7trim-s299 (e) the B26 RESULT blob"
if CUT in ar_src:
    ar_src = ar_src[:ar_src.index(CUT)]
    print("archive: previous (e)/(f) append removed, re-running cleanly")

START = "**B26 RESULT (s299, BUILD)**"
END = "as B14-B25 did"                       # retire through here; keep ' - `BUILD_SPINE...`'
s = np_src.index(START)
e = np_src.index(END, s) + len(END)
blob = np_src[s:e]
assert blob.startswith(START) and blob.endswith(END), (blob[:30], blob[-20:])
assert ").:" in blob, "the join artifact this rotation also repairs is gone"
assert np_src.count(blob) == 1, "blob not unique"

KEEP = ("**B26 (s299, BUILD) ACCEPT**: `python3 -u -m sim.selftest --b26` -> "
        "`PASS B26: 9/9 gates`, anchor `1721afbdd1439ec1` "
        "(`evidence/b26_selftest.txt:48`, gate line `:58`), stdout byte-identical to "
        "`python3 -u -m sim.composedsave` and to a re-run; harness `python3 -u "
        "scripts/b26_mutate.py` -> **14/14 scored, 0 NO-OP** "
        "(`evidence/b26_mutate.txt:18`), `--selftest` -> **5/5 perturbed declarations "
        "REJECTED** (`evidence/b26_mutate_selftest.txt:11`). Its three laws (the "
        "container is LOADED, not just written; a round-aligned load is CONFLUENT; the "
        "non-carry is the in-progress MP budget, 69 units / 69 x-bytes vs control 0) "
        "and the four defects the gates caught are VERBATIM at §trim-s299 (e); `NAMED "
        "## B26` governs. The rung text AND the instrument were authored the same fire, "
        "as B14-B25 did")

out = np_src[:s] + KEEP + np_src[e:]
assert ").:" not in out, "join artifact still present"
assert out != np_src

# ---- second move: the B26 CLOSED block in §THE PICK, which the §BUILD TRACK line above
# now covers in full (result + next rung). Retired VERBATIM as §trim-s299 (f). ----
PICK_HEAD = ("  CLOSED (B26, this PR) the BUILD-track rung track_mode asked for "
             "(`MODE=BUILD`, next_rung B26):\n")
p1 = out.index(PICK_HEAD)
p2 = out.index("(B25's own rule: rung text FIRST).\n") + len("(B25's own rule: rung text FIRST).\n")
pick_blob = out[p1:p2]
assert pick_blob.count("\n") == 4, "unexpected block shape"
out = out[:p1] + out[p2:]

HEADS = [
    ("\n\n## §trim-s299 (e) the B26 RESULT blob, VERBATIM from NEXT_PROMPT.md "
     "§BUILD TRACK at the B26 close (retired so the file stays under the 12,000 B "
     "warn cap; `NAMED ## B26` + the two evidence files are the record)\n\n", blob),
    ("\n\n## §trim-s299 (f) the B26 CLOSED entry from NEXT_PROMPT.md §THE PICK, VERBATIM "
     "(the §BUILD TRACK line of the same close carries the result and names B27, so this "
     "block was pure duplication)\n\n", pick_blob),
]
add = "".join(h + b + "\n" for h, b in HEADS)
open(AR, "w", encoding="utf-8").write(ar_src + add)
open(NP, "w", encoding="utf-8").write(out)

chk = open(AR, encoding="utf-8").read()
for _h, b in HEADS:
    assert b in chk, "NOT VERBATIM IN ARCHIVE: %r" % b[:40]
after = len(open(NP, encoding="utf-8").read().encode())
print("NEXT_PROMPT %d -> %d B (warn 12000, target 11700)" % (before, after))
for _h, b in HEADS:
    print("moved %5d B sha1 %s verbatim-in-archive True | head %r"
          % (len(b.encode()), hashlib.sha1(b.encode()).hexdigest()[:16], b[:34]))
print("under 12000: %s | under target 11700: %s" % (after <= 12000, after <= 11700))
