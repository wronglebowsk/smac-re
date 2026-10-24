# Session notes archive — sessions 66-66

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 66 (2026-10-24) — M53n: **THE ROUND SCHEDULE IS PINNED — `FUN_004f5a70(base_idx)` runs exactly once per base per round (76/76 live), grouped by owner faction in faction-turn order with OUR faction LAST; the economy block executes 2x per visit unconditionally (pass1 d64=0, pass2 d64=1) plus event/UI extras (247 block executions per round, every 4e92c0 entry reaching the ungated bc-add); `DAT_0068cbb4` is a freshness marker that makes `4ef6d0`'s two nested recomputes structurally unreachable (0 hits); AND bc/c0 are REBUILT inside the block by `FUN_004e78e0` (seed store 0x4e79a5, add-loop 0x4e7be3-0x4e7c28) before 4e92c0/4e93f0 add the crawler values — which resolves M53m's "+1 bc per 10 sweep-fires"** — write-up `evidence/m53n_findings.md`
- **Census method (VERIFIED live, one full round 2380→2381).** `scripts/m53n_drive.py` (arm/stop,
  pidfile, `stdbuf -o0` gdb, literal addresses, printing `continue` blocks, cap): int3 at
  `4f5a70`/`4e8d60`/`4e92c0` entries (entry ⇒ `*(int*)$esp` = caller return address) + 4 hw DR
  (`hbreak *0x4e9331` bc-add region, watch base70 `+0xbc`/`+0xc0`, watch `DAT_008f0d60`); mid-body
  hits dump 8 stack words, matched against the 12 statically-known return addresses → caller
  identified with no breakpoints inside the block. Log `evidence/m53n_watch.log` (980 lines),
  per-visit table `evidence/m53n_schedule.tsv`, pre/post `m53n_{pre,post}.tsv`. One crawler re-poked
  (M53m recipe, slot 113→112, restored readback-OK).
- **Schedule (VERIFIED).** 4f5a70 has ONE call site in `.text` (`0x5206d3`, `FUN_00520540` turn
  machinery); 76 VISIT hits = nb, order grouped by owner byte@4 into 7 faction groups (fac 4,5,6,7,
  1,2,3), ascending base index within a group, faction 3 (us, idx 70) LAST right before year++
  (log:935). Block multiplicity per round: pass1 76 + pass2 76 + `4f41f0`-B 34 + `-A` 4 + `4eb6b0`
  (UI recompute via `4ef6d0→4e5ae0→4f6030→4eb6b0`) 55 + `4ee410`-B 1 + pass3 1 = 247, and
  SWEEPIN == RATEIN == BCADD == 247 → **the bc-add at 0x4e9331-0x4e934a is ungated**. `4ef6d0`,
  `4f34b0`, `4e47d0` fired 0x. 11 distinct per-visit signatures (26 visits = pass1+pass2 only …
  1 visit had 13 extra `4eb6b0` recomputes).
- **Freshness marker (VERIFIED).** `4f5a70` stamps `DAT_0068cbb4 = param_1` at entry (fn:21) and
  again before pass2 (fn:41); its 3rd block + both `4ef6d0` blocks are guarded `if (DAT_0068cbb4 !=
  idx)` → `4ef6d0`'s sites can never fire inside a visit (0 hits live), pass3 fired exactly 1x (the
  visit whose nested UI chain moved the marker). `4f41f0`/`4ee410` stamp + run unconditionally but
  are gated by their own production/queue conditions.
- **bc/c0 REBUILD (VERIFIED live + machine).** Base70 pass1 (log 935-956): sweep sets c6c0=1 →
  `BCCHG new=0 eip=0x4e79a8` (store `0x4e79a5 mov [esi+edx*1],ecx`, edx=`ds:0x8f0d60`, esi walks
  `0xbc..0xc8` per `mov esi,0xbc`/`cmp esi,0xc8`, ecx=`[eax*4+0x94dc34]`, `eax=local+2095·ebx` →
  ×4 = `+0x20bc·ebx` faction-record stride) → 8 `BCCHG` at `0x4e7c19` (bc 0→11) + 6 `C0CHG`
  (c0 0→7): store `0x4e7c15` in loop `0x4e7be3-0x4e7c28` (`edi=0xbc` step 4 to `0xcc`, args
  `(ebx,?,0,DAT_0068cbb0,byte[base+4])` → `FUN_004e75f0`, eax added to `base[edi]` + running total
  `[ebp-0x48]`; outer counter `DAT_0x8f0c68` set `0x4e7904`, dec `0x4e85d8`) → `RATEIN c6c0=1 bc=11`
  → `BCCHG new=12 eip=0x4e934a`. Pass2 (d64=1) rebuilds identically to 12. ⇒ crawler adds +1 to the
  FINAL rebuilt value per visit (not per block execution) = M53m's +1/10-fires; M53l's "stable 75/75"
  = idempotent rebuild. **M53l's "bc/c0/cc PERSISTENT" premise is retired.** +0xc4/+0xc8 = the
  3rd/4th dwords of the same vector (contents OPEN). Post-round base70 bc 12 c0 7 c4 4 c8 0 d0 1
  cc −2 minerals 16.
- **Safety/method.** Pokes idle + readback; gdb armed after poking, stopped via
  `scripts/m53n_drive.py --mode stop` (SIGINT pidfile + `kill -CONT`), never by name. **New pitfall:
  a PROPOSAL vote pane ("GLOBAL TRADE PACT / Commerce Rates Doubled") stalled the AI phase ~5 min and
  made `smac_play.py --turns 1` return STUCK** — the vote bars are YEA (310,495) / NAY (398,495) /
  ABSTAIN (485,495) in true window coords, then a single OK bar (393,495); the "YEA: 2 NAY: 3" line
  is the vote TALLY, not a key hint (keys 2/3 do nothing). Clicked ABSTAIN → OK → measure FAILED,
  rule unchanged. TracerPid 0 + game idle on our turn at year 2381; no crawler-shaped unit remains.
- **Next:** `NEXT_PROMPT.md` rewritten for session 67; **THE PICK = M53o** (what the rebuilt
  production vector IS: `FUN_004e75f0` item/field semantics, the `0x94dc34 + 0x20bc·ebx` seed table
  identity, `DAT_008f0c68` item count, the 13x `4eb6b0` UI-recompute chain, then the M53l income-extra
  anomaly and +0xc4/+0xc8 contents).
