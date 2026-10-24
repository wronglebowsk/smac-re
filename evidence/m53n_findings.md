# M53n findings — the round call schedule of the economy block (VERIFIED live, round 2380→2381)

## Instrumentation (all live, pid 2124624)
Driver `scripts/m53n_drive.py` (arm/stop, pidfile, `stdbuf -o0` gdb, literal addresses, per-hit
`continue` blocks, cap 4000). Sites: int3 at `0x4f5a70` entry (VISIT: param_1 = base idx,
`*(int*)$esp` = caller return), `0x4e8d60` entry (SWEEPIN: c6c0/c70 as LEFT by the previous sweep),
`0x4e92c0` entry (RATEIN: c6c0 + bc as seen by the adder); hw DR: `hbreak *0x4e9331` (BCADD =
reached the bc-add region), watch `0x962dec` (base70 +0xbc), watch `0x962df0` (+0xc0), watch
`0x8f0d60` (cur-base pointer). Mid-body sites print 8 stack words; callers identified by matching
those words against the 12 statically-known return addresses (`evidence/m53n_callsites_raw.txt`).
Fake crawler re-poked per M53m recipe: slot 113 → x45 y10 typ5 fac3 ord3 b38=0 abase70
(readback OK, `evidence/m53n_orig.json`; restored at its post-compaction home slot 112, readback OK).
Log `evidence/m53n_watch.log` (980 lines); per-visit table `evidence/m53n_schedule.tsv`;
snapshots `evidence/m53n_pre.tsv` / `m53n_post.tsv`; state `evidence/m53n_state0.txt`.
Blocker during the run: a PROPOSAL vote pane ("GLOBAL TRADE PACT / Commerce Rates Doubled",
player bars YEA/NAY/ABSTAIN at y≈495, ABSTAIN center (485,495), then a single OK bar (393,495))
stalled the AI phase for ~5 min and the `smac_play.py --turns 1` driver returned STUCK; clicking
ABSTAIN then OK cleared it and the round completed. Measure FAILED (no rule change).

## 1. Who calls the block, and how often (VERIFIED census, one round)
`FUN_004f5a70(base_idx)` has exactly ONE call site in all of `.text`: `0x5206d3` in
`FUN_00520540` (turn machinery). Live VISIT hits = 76 = `DAT_00985af4` → **once per base per round**.
Visit order = grouped by owner byte@4 in faction-turn order, ascending base index inside each
group, 7 groups (fac 4,5,6,7,1,2,3): `evidence/m53n_schedule.tsv`; OUR faction (3, idx 70) is
processed LAST, immediately before the year ticks (log:935 `VISIT n=905 idx=70`, then year 2381).
The 5-call economy block `[4e8d60, 4e78e0, 4e92c0, 4e93f0, 4eaa10]` is verbatim replicated at 12
sites in 7 functions (3x 4f5a70 @4f5ac3/4f5b37/4f5c50, 2x 4ee410 @4ee6cf/4ee889, 2x 4ef6d0
@4efeb0/4f2207, 2x 4f41f0 @4f44ad/4f4563, 1x each 4e47d0 @4e4de2, 4eb6b0 @4eb6cc, 4f34b0 @4f3f85).
Live per-round multiplicity (SWEEPIN == RATEIN == BCADD == 247):
`4f5a70` pass1 76 + pass2 76 (both unconditional, every base) + `4f41f0` 2nd site 34, 1st site 4 +
`4eb6b0` (UI recompute) 55 + `4ee410` 2nd site 1 + `4f5a70` pass3 1 + `4ef6d0` 0 + `4f34b0` 0 +
`4e47d0` 0. Per-visit signatures (11 distinct, `m53n_schedule.tsv`): 26 visits = pass1+pass2 only;
25 = +4f41f0-B; 13 = +1..13 `4eb6b0` recomputes (max 13 on one visit); 1 visit = +4ee410-B+4f41f0-A;
1 visit = pass3 fired once. **Every 4e92c0 entry reached the bc-add region (247/247) → the add at
`0x4e9331-0x4e934a` is ungated.**
`DAT_008f0d60` store census live: `0x4f5a99` (4f5a70 pass1) x75, `0x4f5c41` (pass3) x1,
`0x4e3490` (`FUN_004e3470`, UI/selection path) x19; `4ef6d0`'s two sites never fired.

## 2. Why the nested recomputes are skipped: DAT_0068cbb4 is a freshness marker (VERIFIED)
`FUN_004f5a70` line 21 (`evidence/m53n_fn4f5a70.txt:21`) sets `DAT_0068cbb4 = param_1` at entry and
line 41 again before pass2; its third block is guarded `if (DAT_0068cbb4 != param_1)` (lines 77-84).
`4ef6d0`'s two block sites are guarded the same way (`evidence/m53n_fn4ef6d0.txt:273` and `:1583`)
— and they fired 0x this round, while `4f5a70` pass3 (same guard) fired exactly 1x (the visit whose
nested `4eb6b0`/`4e5ae0` chain moved the marker). `4f41f0`/`4ee410` instead stamp
`DAT_0068cbb4 = DAT_0068cbb0` and run unconditionally, but are gated by their own production/queue
conditions (`m53n_fn4f41f0.txt:73-85`, `m53n_fn4ee410.txt:82-88`). So: **within one visit the
guarded sites can never re-run; only event-gated sites (4f41f0/4ee410) and the UI path add extra
executions.** `4e47d0` = founding-only, `4f34b0` gated by `DAT_00985afc>5 || solo || flag` — 0 hits.

## 3. bc/c0 are REBUILT inside the block — M53m's "+1 per 10 sweep-fires" resolved (VERIFIED live)
Base70 visit, pass1 (log lines 935-956): `VISIT idx=70` (c6c0=0) → `BASEPTR 0x4f5a99` → `SWEEPIN
ret=0x4f5ac8` (sweep computes c6c0=1) → **`BCCHG new=0 eip=0x4e79a8`** and `C0CHG new=0` (the store
that faults is `0x4e79a5 mov [esi+edx*1],ecx`, edx = `ds:0x8f0d60`, esi = field offset walking
`0xbc..0xc8` per `0x4e7963 mov esi,0xbc` / `0x4e7975 cmp esi,0xc8`, ecx = `[eax*4+0x94dc34]` with
`eax = local(ebp-4) + 2095*ebx` → ×4 = `+0x20bc*ebx` = a faction-record-stride table) → **8 more
`BCCHG` at `eip=0x4e7c19`** (bc 3,4,5,6,7,8,10,11) with 6 interleaved `C0CHG` (c0 2..7): the store
is `0x4e7c15 mov [edi+ecx*1-4],edx` inside the loop `0x4e7be3-0x4e7c28` (`0x4e7bdb mov edi,0xbc`,
`edi += 4`, `cmp edi,0xcc; jl`, item/field args `(ebx, ?, 0, DAT_0068cbb0, byte[base+4])` pushed to
`FUN_004e75f0`, its eax added to `base[edi]` and to a running total `[ebp-0x48]`; outer repeat
counter `DAT_008f0c68`, set `0x4e7904`, `dec 0x4e85d8`) → `RATEIN c6c0=1 bc=11 ret=0x4f5ad2` →
`BCADD` → **`BCCHG new=12 eip=0x4e934a`** = the `bc += DAT_008f0c6c` add. Pass2 (d64=1, log
957-976) repeats the identical rebuild and lands 12 again.
⇒ **bc/c0 are not persistent accumulators: `FUN_004e78e0` (block step 2) seeds `base+0xbc..0xc8`
from a 0x20bc-stride record table and adds per-item contributions, and only then does `4e92c0`
add the crawler value once.** Because the block runs 2-13x per visit and bc is rebuilt each time,
the crawler contributes +1 to the FINAL value per visit, not per block execution — exactly the
M53m "+1 per 10 fires" observation, and the reason M53l saw bc/c0 "stable 75/75" (idempotent
rebuild when the inputs are unchanged). Chain adjacency is guaranteed *inside* the block, not by
caller scheduling. Post-round base70: bc 12, c0 7 (was 8), c4 4, c8 0, d0 1, cc −2, minerals 16.

## 4. Side gains
`+0xc4`/`+0xc8` (M53l "semi-active, OPEN") are simply the 3rd/4th dwords of the same rebuilt vector
(`edi` walks 0xbc,0xc0,0xc4,0xc8) — contents of their contributions still OPEN. Income anomaly
(3 bases +1..+3 extra, M53l): consistent with `4ef6d0`'s income add reading `d0` written by the
pass1 `4e93f0`, while event/UI recomputes re-write `d0` afterwards — NOT closed.

## Still open
`FUN_004e75f0` = the per-(item, field) contribution function (what an "item" is: facility? tile?);
the seed table `0x94dc34 + 0x20bc·ebx` identity (faction record field? which ebx); why
`4eb6b0` fires up to 13x on one visit (its `4e5ae0`/`4f6030` UI chain); `DAT_008f0c68` item count
source; `FUN_004e3470` (19 cur-base-pointer stores) trigger; income-extra anomaly; +0xc4/+0xc8
meaning; founding-time c0 (`4e47d0` never ran this round).
