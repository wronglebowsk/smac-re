# Session notes archive — sessions 52-52

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 52 (2026-10-23) — M52b: edi at the SPENDA store is `0x4e40a0(owner,1,−1) × 0x5ac950(queue_type, idx, 0)` = 10 × 1 — M49a's "sweep-entry index" is FALSE at its first link (0x4f5aa9 loads the OWNER BYTE), and 0x4eaa10 preserves edi

**The provenance chain, measured end to end in one run** (3 rounds, 2360→2363, 0 OCR passes,
`evidence/m52b_run.out`; seven new EDI_* breakpoints added to `scripts/m51a_drive.py`):
1. `EDI_ENTRY 74 eip=0x4f5aa9 idx=70 owner_byte=3 name=Climactic Research` (`m52b_watch.log:386`) — edi is
   assigned at `0x4f5aa9 mov edi,edx`, and edx comes from `0x4f5a9c mov dl,BYTE PTR [ecx+0x4]` after
   `xor edx,edx` (`m52b_fn4f5a70_4eaa10_disasm.txt:17,19`) ⇒ **edi := the base's OWNER BYTE, not the sweep
   index**. Fired 222× (3 rounds × 74 bases) and the printed byte matches every base's owner (Morgan bases 4,
   Sparta 5, Assassin's 6, U.N. 7 — `:62, :94, :109, :139`), so this is a general property of `0x4f5a70`,
   not a one-off. M49a's chain broke here.
2. `EDI_QGATE q50=2 st=200` (`:388`) — `0x4ef88b mov ecx,[eax+0x50]` = 2 ≥ 0 ⇒ the `jge 0x4efa2c` branch.
   The negative-queue branch (which would set `edi = 0x4e40a0(...)` at `0x4ef8e2` and imul the item table at
   `0x4ef8ed`) never ran for us: **0 EDI_NEGPATH / EDI_NEGMUL hits**.
3. `EDI_POSPATH factor_eax=10` (`:389`) — `0x4efa3c call 0x4e40a0(owner=3, 1, −1)` returned **10** and
   `0x4efa4b mov edi,eax` overwrites the owner byte. Statically confirmed: with arg2 == 1 the function jumps
   to the government switch at `0x4e421f` (`m52a_fn4e40a0_disasm.txt:137`), index =
   `faction[p].int[20]@0x94d6a0+p·0x20bc + 7` = 0+7 = 7, and the jump table (`x/12wx 0x4e4318`) sends 7 to
   `0x4e430f = mov eax,esi` — the **×1 case** (cases 0-4 are `(esi·13+9)/10` = ×1.3, case 5 another
   multiplier; the table implements per-government economy scaling).
4. `EDI_POSMUL edi_before=10 ret_5ac950=1` (`:390`) — `0x4efa4d call 0x5ac950(2, 70, 0)` returned **1** and
   `0x4efa52 imul edi,eax` leaves edi = 10. `FUN_005ac950` (`m52b_fn5ac950_disasm.txt:6,12,13,25,26,119,123`):
   `esi = arg1` is a **unit type id** (it indexes the type table at `0x98ad88 + type·52`), it loads
   `bl = byte[type+0x29]` (+41) for every type and only clamps it to [1, 999] when the class byte
   (+0x2a) == 8 and arg2 ≥ 0, then for `type < 0x40` jumps to the tail `mov eax,ebx` — so the return is the
   **+41 byte**. Live type table: Colony Pod +41=3, Formers +41=2, **Scout Patrol +41=1** (class 3),
   Transport Foil +41=3; the neighbouring +0x2b (+43) byte holds 10 for Scout Patrol (40/41/39 for the others).
5. `EDI_SPENDA edi=10 st=200 q50=2 m1c=104 m2c=8` (`:391`) → `0x4efedb sub esi,edi` →
   `W40_SPENDA old=200 new=190 edi=10` (`:392`) → `W40_CLAMP1 old=190 new=0 cap=10 d0=0` (`:400`).

**Verdict on the two competing claims.**
- M49a's "edi = the base's SWEEP-ENTRY INDEX" is **falsified twice**: the index is 70 (not 10) and the
  assignment at 0x4f5aa9 loads the owner byte (3). The value that survives to the store is the queue-path
  product.
- M48d's original reading — "Scout Patrol cost 10" — is **restored in substance**: the subtrahend is the
  queued item's production cost, computed as `economic factor (10 = our government's ×1 case) × a per-type
  byte`. INFERRED label on the byte's meaning: +41 is a per-type production weight, NOT the mineral cost
  itself (the +43 byte is the one that reads 10 for Scout Patrol, and alpha `#UNITS` documents its own Cost
  field as "0 = Autocalculate", i.e. the engine computes it).
- The milestone's hypothesis that `0x4eaa10` (called 20 bytes earlier at 0x4efec4) leaves the residue is
  **statically refuted**: it pushes edi at `0x4eaa41` and pops it at `0x4eb672`
  (`m52b_fn4f5a70_4eaa10_disasm.txt:396, 1357`) — callee-saved, restored on the normal path.

**Side results.**
- `base+0x50` is the **queued production item id**, not anonymous scratch: 2 = unit type 2 = "Scout Patrol"
  (name read from the type record at `0x98ad88+2·52`). QGATE decodes it as: `0xffffffda` = empty; ≥ 0 = the
  id; < 0 = `|q|` with `[ebp-0x1c] = |q| − 39` and flags set by the 34/39 thresholds (`0x4ef8a1-0x4ef8c9`).
  `0x5ac950` treats `type ≥ 0x40` as the facility case (checks `byte[type·52+0x30] & 4`, a per-64 group flag
  at `0x927a98`, and `0x94d438`) — consistent with M46's "runtime item = alpha #FACILITIES idx + 1".
- Government economy multipliers live in the `0x4e40a0` switch at `0x4e4318` (12 entries, indexed by
  `faction[p].int[20] + 7`): ours (int[20] = 0) is the ×1 case; case 0-4 = ×1.3, case 5 = another ratio.
- IADD fired 2× in 3 rounds (both d0 = 0, no-op writes); SPENDA/CLAMP1 once, on the round a completion ran.
  The clamp story from M52a is unchanged.

Next: **M53a** — the `base+0x50` queue record end to end (id encoding, where the build progress counter
lives, what fires COMPLET 0x4efe41) and whether the charge `factor × type+41` is the whole cost story.
Footing rewritten in NEXT_PROMPT.md (session 53).
