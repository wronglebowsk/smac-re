B22 **MERGED** (#286, main `3f645e1`, 12/12 gates, `evidence/b22_composedgrowth.txt`). Nothing unmerged.

TRACK STATE (re-read it, it just flipped): `python3 scripts/track_mode.py` ->
**MODE=ANALYSE  analyse_since_build=0  last_build=B22  next_rung=B23**.
=> THIS FIRE ANALYSES a census pick. **B23 is QUEUED, not next** (the spine's R2 queue waits for the
track to return to BUILD; do not build while MODE=ANALYSE).

ANALYSE PICKS open, in the order s272/s273 left them:
  (a) `ds:0x68cbb0` - `.data`, 340 xrefs, EXACTLY 6 stores, all inside `0x4e3000-0x4f6000`;
  (b) the 304-B table at `0x95da40`, bit `0x20`;
  (c) M310's neighbours `FUN_00470fe0` / `FUN_004715d0` / `FUN_00471fd0`.
Zero box time. Reuse `scripts/m308_site_list.py` (`parse_text`) and the disassembly cache
`scratch/m574/text.txt`; `ghidra_out/index.csv` is the function index.

WHAT B22 ESTABLISHED (the part worth carrying forward):
- the save's TWO record arrays grow in ONE `savewriter.build_image(bases_override=..., append_units=...)`
  call, and the writer's layout is a FIVE-BAND map, not one uniform lift:
  `[unit originals 3484][the ONE new unit 52][base originals 5472][the grown bases 1520][tail 10800]`.
- the inbound half of the round-trip is proved: `record_from_image(image, idx, head)` composes B12's unit
  from CONTAINER bytes, and G12's in-process mutation experiment (rebind that leg to read the model,
  restore in `finally`) shows G9's record collapsing onto the model's own (27,29) fac 1 - so the falsifier
  discriminates. G3 is DECLARED blind to that mutation (fixture: model tuple == container tuple).
- `sim/save`'s shape scan confirms only the 18 NAMED bases of a 23-base grown container (M282's founders
  write an empty name span; `_base_ok` wants `[ -~]{3,30}\x00` at +19). It costs nothing: `units_off` is
  derived FROM `bases_off`, and per-image `bases_pred == bases_off` with `closes` True on all three.

TWO MISTAKES OF THIS FIRE, so they are not repeated: (1) I asserted a count-vs-shape "disagreement" by
comparing image A's count formula against image B's scan anchor - Greptile's P1; a locator claim is a claim
about ONE image's bytes. (2) A `git add -A && git commit` chain ran after my docs-patch script had aborted
on a stale multi-line anchor, so one commit shipped corrected code with stale prose - patch steps and
commit steps never get chained, and prose anchors that span wrapped text get matched by line number.

NEXT FIRE: `milestone.py start M311` (or the next free M id) and take pick (a).
