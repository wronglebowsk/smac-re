Findings, most important first:

1. **P1** — `NAMED.md:1289` (`A = UNIT-SUPPORT CENSUS`) vs `scripts/m318_refresh_pair.py:139-175` (`C2`)
   Several details inside the “V (structure)” A claim are not read by the gate.  
   `C2` pins:
   - count/global `985af0`
   - unit stride `0x34`
   - selected-index load `ds:0x68cbb0`
   - some bit mask `and/or` literals
   - six global stores

   It does **not** read:
   - the claimed home-base equality `unit+0x2e == ds:0x68cbb0`
   - the faction filter
   - the “over-capacity limit `94d684` clamped `0..7`”
   - the foreign-tile key comparison `94d690 == -3/<-3`
   - that the triad is “switched on `unit+0x26`”

   Why it matters: `NAMED.md` marks the structural part verified, but those exact measurements can change or be absent without reddening the shipped gate. This is a classic non-failing VERIFIED claim.

2. **P1** — `NAMED.md:1289-1291` vs `scripts/m318_refresh_pair.py:101-132` (`C1`)
   The claim says the triad is “yield triad … switched on `unit+0x26`,” and the foreign-tile logic is “keyed `94d690 == -3/<-3`.”  
   `C1` only verifies:
   - four call sites from A, including the triad and `4e3b50`
   - a callee multiset in B

   It never reads the branch condition, switch operand `unit+0x26`, or any comparison involving `94d690`.  
   Why it matters: the instrument proves the callees are called, not that they are used in the claimed decision structures. The “switched on” / “keyed on” structural claims are unsupported by the cited gate.

3. **P1** — `NAMED.md:1289` vs `evidence/m318_refresh_pair.txt:37-65` / `scripts/m318_refresh_pair.py:139-175`
   The evidence cited for the A claim cannot fail on the claimed “home-base filter” or “limit/key” facts.  
   For example, the A evidence lines show:
   - a load of `ds:0x68cbb0`
   - stride and flag ORs
   - six global stores

   But no evidence line or assertion contains:
   - `cmp` / `je` for `unit+0x2e`
   - `94d684`
   - clamp behavior
   - `94d690`
   - `unit+0x26` switch structure

   Why it matters: under the repo convention, a claim is VERIFIED only when the shipped gate reads the claimed fact from bytes. Here the gate reads only adjacent facts, so the VERIFIED marker overstates coverage.

4. **P1** — `NAMED.md:1289` (“faction + home-base filter …”)
   The home-base filter itself is the core “selected-base” semantic for calling A a “selected-base UNIT-SUPPORT CENSUS,” but the gate only proves that `ds:0x68cbb0` is loaded somewhere in the function.  
   It does not prove:
   - that the loaded value is used to filter units
   - that it is compared against `unit+0x2e`
   - that unrelated units are skipped on that predicate

   Why it matters: “uses the selection index” and “filters units by selected base” are different facts. The stronger fact is not gated, so the semantic label is under-verified.

5. **P2** — `NAMED.md:1287` (`PAIR` claim) vs `scripts/m318_refresh_pair.py:69-99` (`G2`/`G3`)
   The claim says the 12 pair sites are “= M315's 12 memo sites.”  
   The code verifies:
   - 12 A call sites and 12 B call sites
   - zipped gap `5`
   - seven owners equal a literal owner set
   - a `ds:0x68cbb4` store exists within 17 bytes before each A site

   It does **not** pin the 12 memo-store addresses as a set, nor does it compare them to M315’s measured memo sites. `G3` only asserts `store is not None`, not exact store identities.  
   Why it matters: the equality to M315’s 12 memo sites is not a measured gate; a different set of preceding stores could keep the gate green.

6. **P2** — `scripts/m318_refresh_pair.py:17` and `SESSION_NOTES.md` / `NAMED.md`
   The script docstring says the pair is called “from the same 12 sites in 8 owners,” while `OWNERS`, `G2`, and `NAMED.md` all say **7 owners**.  
   Why it matters: this is not cosmetic if the docstring is used as provenance. It contradicts the shipped gate’s owner set and can confuse future reviewers about the measured fact.

7. **P2** — `NAMED.md:1291` (`B = PANE REFRESH`) vs `scripts/m318_refresh_pair.py:176-206` (`C3`)
   The claim includes “rows from faction array `94dc34` **into pane+0xbc..**.”  
   The gate only pins:
   - `mov ecx,DWORD PTR [eax*4+0x94dc34]`
   - some region/base/countdown instructions
   - counts of selected-index reads and base-flag reads

   It does not read a store to `pane+0xbc` or any display-row write.  
   Why it matters: “from `94dc34` into `pane+0xbc`” is a stronger structural claim than “some function reads `94dc34`.” The second half is not verified.

8. **P2** — `NAMED.md:1293` (`KIND LAW SHARED`) vs `scripts/m318_refresh_pair.py:208-217` (`C4`)
   The gate pins dispatcher calls, `cmp eax,0x3`, and `mov DWORD PTR ds:0x8f0cc8,0x0`, but it hard-codes `D + 116` without a baseline size/coverage assertion for `FUN_004e75f0`.  
   Why it matters: `C4` can silently stop seeing the relevant dispatcher tail if the function boundary/index row drifts, while still passing the three checked instructions if they remain in the window. This weakens the “shared law” claim compared to `G1`, which explicitly pins size/instruction count for A and B.

9. **P2** — `scripts/m318_refresh_pair.py:84-99` (`G3`)
   `G3` scans backward at most 12 instructions and also uses a 17-byte reach window. The prose/evidence only advertise “within 17 B,” not “within 17 B and at most 12 backward instructions.”  
   Why it matters: the measurement definition and the stated claim do not exactly match. If a valid store were within 17 bytes but farther back than 12 instructions, the gate would false-negatively red the baseline despite satisfying the claimed fact. The claim should either be narrowed in prose or the implementation should not impose the extra hidden instruction cap.

10. **P2** — `NAMED.md:1287` and `NEXT_PROMPT.md` / `SESSION_NOTES.md` (“REFRESH tuple holds TARGETS”)
   The M315 “tuple holds TARGETS” fact is used to interpret `0x4e8d60`/`0x4e78e0` as callees, but no shipped M318 gate reads `scripts/m315_bb4_census.py:31` or re-verifies that the tuple contains targets rather than call-site addresses.  
   Why it matters: the PR relies on an earlier fact as interpretive grounding, but the new milestone’s VERIFIED table cites it as part of the pair claim without a local gate. It may be acceptable if already VERIFIED elsewhere, but it should be kept out of the new gate’s proof unless actually re-read by `m318_refresh_pair.py`.