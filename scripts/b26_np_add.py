import hashlib

NP, AR = "NEXT_PROMPT.md", "docs/pick-archive.md"
s = open(NP, encoding="utf-8").read()
a = open(AR, encoding="utf-8").read()
before = len(s.encode())
moved = []


def sub(old, new):
    global s
    assert s.count(old) == 1, "anchor x%d: %r" % (s.count(old), old[:70])
    s = s.replace(old, new, 1)


# ---- retire 1: the M321 pick-(vi) closure block -> §trim-s299 (c) VERBATIM ----
old_vi = ("  CLOSED + MERGED (pick (vi) = M321): FUN_004ee410 = the base FOOD/POPULATION status emitter,\n"
          "  FUN_004f41f0 = the base TALENT/PSYCH-REQUEST emitter (both push PE-read labels into `call\n"
          "  0x48f100`; 7 vs 1, disjoint); the shared `test BYTE PTR [rec+0x38],0x40` gates base_array\n"
          "  field 56 bit 6. Text VERBATIM at \u00a7trim-s297 of `docs/pick-archive.md`; `NAMED ## M321` governs\n"
          "  (#324 hardened at review: 7/7 + 22/22, digest f304cf871a971a3d; a3-form owners = 1, not 2).\n")
assert s.count(old_vi) == 1, "M321 closure block anchor failed"
s = s.replace(old_vi,
              "  CLOSED + MERGED (pick (vi) = M321): `NAMED ## M321` governs (#324 hardened at review:\n"
              "  7/7 + 22/22, digest f304cf871a971a3d; a3-form owners = 1, not 2); its OPEN-pick text sits\n"
              "  at \u00a7trim-s297 and its CLOSED block moved VERBATIM to \u00a7trim-s299 (c).\n", 1)
moved.append(("(c) the M321 pick-(vi) closure block, VERBATIM from NEXT_PROMPT.md \u00a7THE PICK", old_vi))

# ---- retire 2: the B25/B26 detail sentence -> §trim-s299 (d) VERBATIM ----
old_det = ("B25/B26 (MERGED) ACCEPT anchors + digests, harness sets, the LOADED-container law B26 "
           "adds to B25's CONTAINER-owns-the-coordinate-space one, the tile-test-is-NOT-the-decoder "
           "lead (pick (vii)) and the M316/M315 summaries are VERBATIM at "
           "`docs/pick-archive.md` \u00a7trim-s298 (a) + \u00a7trim-s299 (a); `NAMED ## B25` / `## B26` "
           "/ `## M316` / `## M315` govern.")
assert s.count(old_det) == 1, "B25/B26 detail anchor failed"
s = s.replace(old_det,
              "B25/B26 build-track detail (ACCEPT anchors, digests, harness sets, the laws, the "
              "tile-test lead = pick (vii), the M316/M315 summaries) VERBATIM at "
              "`docs/pick-archive.md` \u00a7trim-s298 (a) + \u00a7trim-s299 (a) + \u00a7trim-s299 (d); "
              "`NAMED ## B25` / `## B26` / `## M316` / `## M315` govern.", 1)
moved.append(("(d) the B25/B26 build-track detail sentence, VERBATIM from NEXT_PROMPT.md "
              "\u00a7BUILD TRACK", old_det))

# ---- add: the B26 result line ----
sub("**B26 MERGED** (this PR, `NAMED ## B26` governs):",
    "**B26 MERGED** (this PR, `NAMED ## B26` governs). **B26 RESULT (s299, BUILD)**: "
    "`python3 -u -m sim.selftest --b26` -> `PASS B26: 9/9 gates`, digest(B26 measured rows) "
    "`1721afbdd1439ec1` (`evidence/b26_selftest.txt:48`, gate line `:58`), byte-identical to "
    "`python3 -u -m sim.composedsave` and to a re-run; harness `python3 -u scripts/b26_mutate.py` "
    "-> **14/14 scored** (`evidence/b26_mutate.txt`), `--selftest` **5/5 perturbed declarations "
    "REJECTED** (`evidence/b26_mutate_selftest.txt`). Three laws, each falsified-and-repaired: "
    "(i) THE CONTAINER IS *LOADED*, NOT JUST WRITTEN - the resumed run rebuilds model + ledger + "
    "engine from the re-parsed image and reads no pre-boundary object (MU2/MU3 name it); (ii) a "
    "ROUND-ALIGNED load is CONFLUENT - byte-equal final image AND per-unit tiles vs the "
    "uninterrupted run (MU3/MU6); (iii) what does NOT carry is MEASURED: the only thing the "
    "container cannot carry is the in-progress MP budget - **69 units / 69 x-bytes** diverge at a "
    "mid-gesture boundary while the control (same split, budget re-granted) diverges by **0** "
    "(MU8/MU9 name the half that does carry). Four real defects the gates caught, all in "
    "`NAMED ## B26`: per-round rebase double-appended the arrivals (72 units vs 71); the writer "
    "skipped the APPENDED records so arrivals froze at their create tile (diff "
    "`226267`/`226319`, x 7 vs 63); the `model` rival passed G8 by coincidence; and the split's "
    "arrival never moved the round it was created (B12 press-before-CREATE order).:")

# ---- ledger line ----
sub("Merged M54A-M309 + B0-B21 + hygiene #254-#280.",
    "Merged M54A-M323 + B0-B26 + hygiene #254-#280.")

# ---- the pick list: name what the build track needs next ----
sub("  NEVER bp mid-instruction (s213). OPEN shortlist detail: `docs/pick-archive.md` \u00a7trim-s269 (b).",
    "  NEVER bp mid-instruction (s213). OPEN shortlist detail: `docs/pick-archive.md` \u00a7trim-s269 (b).\n"
    "  CLOSED (B26, this PR) the BUILD-track rung track_mode asked for (`MODE=BUILD`, next_rung B26):\n"
    "  the SAVE/LOAD boundary, rung text authored into `BUILD_SPINE.md` in the same fire, instrument\n"
    "  `sim/composedsave.py` + harness `scripts/b26_mutate.py`; `NAMED ## B26` governs. **Next build\n"
    "  rung B27 is UNAUTHORED** - `BUILD_SPINE.md` ends at B26 (B25's own rule: rung text FIRST).")

open(NP, "w", encoding="utf-8").write(s)
add = "\n"
for title, body in moved:
    add += ("\n## \u00a7trim-s299 %s\n\n%s\n" % (title, body))
open(AR, "w", encoding="utf-8").write(a + add)

chk = open(AR, encoding="utf-8").read()
for _t, body in moved:
    assert body in chk, "not verbatim in archive: " + _t[:40]
after = len(open(NP, encoding="utf-8").read().encode())
print("NEXT_PROMPT %d -> %d B (warn 12000)" % (before, after))
for t, body in moved:
    print("moved %s: %d B sha1 %s verbatim-in-archive True"
          % (t.split()[0], len(body.encode()), hashlib.sha1(body.encode()).hexdigest()[:16]))
