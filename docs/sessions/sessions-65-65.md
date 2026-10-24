# Session notes archive — sessions 65-65

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 65 (2026-10-23) — M53m: **c6c/c70 ARE FED ONLY BY SUPPLY CRAWLERS (plan 10 = type 5) EXECUTING CONVOY ORDERS (3) — three-branch filter pinned to machine addresses and proven live (c6c[0] 0→1 via 0x4e8f35, c70 0→1 via 0x4e8e82, ×10 each over 4 rounds, 2 sweeps/base/round); ERA WRITER = 0x4ddcf1 COLD CHOOSER PATH (sole direct store)** — write-up `evidence/m53m_findings.md`
- **Filter (VERIFIED machine + live).** 4e8d60 accumulates economy slots only for units with
  unit+14==base owner ∧ plan(type+42)==10 == alpha PLANS[10] "Convoy/Resource Convoy" ∧
  order(unit+17)==3 == alpha ORDERS[3] "Convoy" (glyph O). ONLY plan-10 type: 5 = Supply
  Crawler (cost 3, alpha #UNITS row 6; 1/151 live rows). Branch A: bidx(unit+46 u16)==cur
  base ∧ tile (ti = y·40 + x>>1, unit x@0 y@2) has (terr[8]&1)==0 || level>7 → add
  FUN_004e6960/4e6d40/4e7070 result (slot = unit+38; calls 0x4e8efa/0x4e8f0b/0x4e8f1c) at
  **0x4e8f35** `add [ecx*4+0x8f0c6c],eax`. Branch B: bidx≠cur ∧ ≥0 ∧ unit on base tile →
  **0x4e8e82** `inc [eax*4+0x8f0c6c]` +1, then short-circuit `jmp 0x4e9274`. Good tile ∧
  bidx==cur → **0x4e9009** `inc [cat*4+0x8f0c34]` (upkeep). Slots: c6c[0]→bc, c70→c0,
  c34[0]→ec, c38→f0. Yield fns: tile = y·40+x>>1, terrain +8/+0xc/+0&0xe0, call 0x5831a0
  (shape VERIFIED; resource identity INFERRED).
- **Why zero (VERIFIED census).** 339 units: no order 3, no plan 10 → structural zero —
  explains M53l 75/75 idempotency.
- **Live delta (VERIFIED).** Poked 2 of our units into fake crawlers (u300→field tile
  (45,10) yield-OK cat 0 bidx 70; u279→porch (45,11) cat 1 bidx 73); 4 hw watchpoints (x86
  DR budget 4 — base rows via 10 Hz `/proc` poller `scripts/m53m_poll.py`); drove
  2376→2380: c6c[0] 19 fires (10× new=1 eip 0x4e8f3c + 9× zeroing 0x4e8d79), c70 19 fires
  (10× new=1 eip 0x4e8e89 + 9× zeroing), c34/38 0 fires (base 73 'Factory Drift' is
  FACTION 2 — fac gate 0x4e8e21 skips; names not unique). **Convoy order persists** 4
  rounds; movement executor ignores route-less convoy but the sweep consumes records as
  INPUTS (refines skill poke-pitfall). base70 row = **0x962d30** (= 0x95da10+70·0x130, NOT
  0x962d50): bc 11→12, c0 7→8, cc −3→−2, d0 0→3, minerals 0→15, progress 22→12; cc=bc−ec
  and d0=c0−f0−e0 hold live; income + progress applied 4×. **bc/c0 net +1 despite 10 fires
  each: `bc += c6c[0]` UNCONDITIONAL (0x4e9331-44) — lands only when 4e92c0/4e93f0 run
  adjacent to the same base's sweep; inter-base zeroing eats the rest (multiplicity =
  M53n).** base73 c0 +1 via stale c70 (INFERRED, open).
- **Era writer closed (VERIFIED).** Sole direct store to 0x985aec: **0x4ddcf1** (cold `jge`
  0x4ddb5a past the ret 0x4ddcf0, inside FUN_004ddaa0 chooser/setup dialog, callers
  0x51518b/0x517e1e; eax = 0x5f1394(this,0,0) return ≥ 0; also writes same dword to
  0x94d438+f·0x20bc ×8). M53l "zero direct stores" = grep-render miss (`a3` prints
  `mov ds:0x985aec,eax`). Loaded-scenario era = pointer-based save load INFERRED.
- Safety/method: pokes idle + readback-verified; driver 4/8 turns then "Do you really want
  to quit?" popped → cleared via Escape onto "Oops, no, wait!" (never clicked); unit array
  compacted mid-run (poked records moved slots u300→u252, u279→u273; restored at new
  homes; slots 279/300 recycled by game); nb 75→76 (new base, game progression); re-census
  0 crawler-shaped units remain; game idle on our turn, year 2380, TracerPid 0.
- **Next:** `NEXT_PROMPT.md` rewritten for session 66; **THE PICK = M53n** (round call
  schedule: per-round order/multiplicity of the 4e8d60/4e92c0/4e93f0 callers — which see
  c6c/c70 hot vs stale; why base73 c0 took stale +1; close the 3-base extra-income anomaly,
  +0xc4/+0xc8 meanings, founding c0 via 4e47d0; unit+38 semantics).
