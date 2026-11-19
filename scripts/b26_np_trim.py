import hashlib
import re

NP = "NEXT_PROMPT.md"
AR = "docs/pick-archive.md"
np_src = open(NP, encoding="utf-8").read()
ar_src = open(AR, encoding="utf-8").read()
before = len(np_src.encode())

# ---- rotate the M323 RESULT line VERBATIM out of NEXT_PROMPT's tail ----
m = re.search(r"^M323 RESULT \(s295-chain2.*$", np_src, re.M)
assert m, "M323 RESULT line not found"
m323 = m.group(0)
assert np_src.count(m323) == 1

# ---- also rotate the B25 build-track detail block's tail sentence (already archived at
# trim-s298; NEXT_PROMPT keeps only the pointer) ----
old_bt = ("B25 (MERGED #319, main 1556ce9) ACCEPT anchors/digest, harness 13/13 + 3 "
          "declared NO-OP, the CONTAINER-owns-the-coordinate-space law, the "
          "tile-test-is-NOT-the-decoder lead (pick (vii)) and the M316/M315 summaries "
          "are VERBATIM at `docs/pick-archive.md` \u00a7trim-s298 (a); `NAMED ## B25` / "
          "`## M316` / `## M315` govern.")
assert old_bt in np_src, "B25 detail line not found verbatim"

# ---- the B26 build-track detail (replaces the 'next build is B26, not authored' text) ----
old_b26 = ("Next build **B26, NOT YET\n"
           "AUTHORED**: `BUILD_SPINE.md` ends at B25, so B26's rung text must be written BEFORE probing (one\n"
           "milestone = spine section + instrument). ")
assert old_b26 in np_src, "B26-not-authored line not found"
new_b26 = ("**B26 MERGED** (this PR, `NAMED ## B26` governs): the rung text AND the instrument were authored the same fire, as B14-B25 did - `BUILD_SPINE.md` now ends at B26. Next build **B27, NOT YET AUTHORED** - `BUILD_SPINE.md` ends at B26, so B27's rung text must be written BEFORE probing (one milestone = spine section + instrument). ")

out = np_src
out = out.replace(old_bt,
                  "B25/B26 (MERGED) ACCEPT anchors + digests, harness sets, the LOADED-container law B26 "
                  "adds to B25's CONTAINER-owns-the-coordinate-space one, the tile-test-is-NOT-the-decoder "
                  "lead (pick (vii)) and the M316/M315 summaries are VERBATIM at "
                  "`docs/pick-archive.md` \u00a7trim-s298 (a) + \u00a7trim-s299 (a); `NAMED ## B25` / `## B26` "
                  "/ `## M316` / `## M315` govern.", 1)
out = out.replace(old_b26, new_b26, 1)
out = out.replace("STATE: B1-B25 + M54A-M321 done; next BUILD is B26, spine text NOT authored",
                  "STATE: B1-B26 + M54A-M323 done; next BUILD is B27, spine text NOT authored", 1)
out = out.replace("B1-B25 MERGED**\n(B25 = #319, main 1556ce9)",
                  "B1-B26 MERGED**\n(B25 = #319 main 1556ce9; B26 = this PR)", 1)
out = out.replace("(M241 FAIL 2/5 #180).\n", "(M241 FAIL 2/5 #180). B26 ANSWERED the build rung.\n", 1)
out = out.replace(m323,
                  "M323 RESULT (s295-chain2) VERBATIM at `docs/pick-archive.md` \u00a7trim-s299 (b); "
                  "`NAMED ## M323` governs.", 1)
assert out != np_src

# ---- append the two rotated blocks to the archive, byte-for-byte ----
sha_m323 = hashlib.sha1(m323.encode()).hexdigest()[:16]
add = ("\n\n## \u00a7trim-s299 (a) the B26 build-track footer sentence, VERBATIM from "
       "NEXT_PROMPT.md \u00a7BUILD TRACK at the B26 close (retired so the file stays under "
       "the 12,000 B warn cap)\n\n"
       + old_bt.replace("`docs/pick-archive.md` \u00a7trim-s298 (a)", "\u00a7trim-s298 (a)")
       + "\n\n## \u00a7trim-s299 (b) the M323 result line, VERBATIM from the last line of "
       "NEXT_PROMPT.md\n\n" + m323 + "\n")
open(AR, "w", encoding="utf-8").write(ar_src + add)
open(NP, "w", encoding="utf-8").write(out)

chk = open(AR, encoding="utf-8").read()
assert m323 in chk, "M323 block did not land verbatim in the archive"
after = len(open(NP, encoding="utf-8").read().encode())
print("NEXT_PROMPT %d -> %d B (cap warn 12000)" % (before, after))
print("moved M323 line %d B, sha1 %s, byte-identical in archive: True"
      % (len(m323.encode()), sha_m323))
