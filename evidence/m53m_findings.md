# M53m — what makes c6c/c70 nonzero: Supply-Crawler convoy sweep (session 65)

## THE ANSWER (VERIFIED machine + alpha + live census)
`FUN_004e8d60` feeds the economy globals **only from unit records that are Supply Crawlers
(unit type 5, type-record plan byte +42 == 10 = alpha PLANS[10] "Convoy/Resource Convoy")
executing a Convoy order (unit+17 == 3 = alpha ORDERS[3] "Convoy", glyph O)**, matching the
swept base's owner. Three outcomes per crawler (all gated `unit+14 == base owner byte`,
machine 0x4e8e1c-0x4e8e21; plan check 0x4e8e42/0x4e8e94 `cmp BYTE [type*4+0x98adb2],0xa`;
order check 0x4e8e6b `cmp BYTE [esi-0x15],0x3`):

1. **Field yield (branch A)** — assigned base `unit+46 (u16) == DAT_0068cbb0` cur base idx
   (0x4e8e27-0x4e8e36 je 0x4e8e8e) AND crawler's tile is "unworked": terrain rec
   `0x92ae14 + ti*0x2c`, ti = y*40 + (x>>1) with unit x=u16@0, y=u16@2 (0x4e8ea2-0x4e8ebc),
   satisfying `(rec[8]&1)==0 || (rec[2]&0xf)>7` (0x4e8ec8-0x4e8ed6):
   switch unit+38 -> 0: call FUN_004e6960 @0x4e8efa; 1: FUN_004e6d40 @0x4e8f0b;
   2: FUN_004e7070 @0x4e8f1c; 3: eax=0 + `0x8f0cc8 := 0` @0x4e8f28. Accumulate
   **0x4e8f35 `add [ecx*4+0x8f0c6c], eax`** (scratch ecx = unit+38, int stride 4).
2. **Delivery +1 (branch B)** — `unit+46 != cur idx` (fall-through 0x4e8e3c) AND crawler
   stands exactly on the base tile (`cmp unit+0, [base+0]` / `cmp unit+2, [base+2]`
   0x4e8e50-0x4e8e65) AND `unit+46 >= 0` (0x4e8e75-78 jl): **0x4e8e82
   `inc DWORD [eax*4+0x8f0c6c]`**.
3. **Upkeep +1 (good tile)** — plan10 ∧ order3 ∧ `(rec[8]&1)!=0 ∧ 0<=(rec[2]&0xf)<8`
   (machine 0x4e8ff0-0x4e8fff): **0x4e9009 `inc [eax*4+0x8f0c34]`** (c34[cat], crawler
   upkeep, feeds ec/f0 — M53l/M53k). REACHABLE ONLY ON THE bidx==cur PATH: branch B
   short-circuits to end-of-iteration at 0x4e8e89 `jmp 0x4e9274`, and the faction gate
   0x4e8e21 `jne 0x4e9274` skips foreign-owned bases entirely.

Slot map (int stride 4): slot0 = 0x8f0c6c -> bc (M53l 0x4e9344); slot1 = 0x8f0c70 -> c0
gross (M53l 0x4e9459); c34[0]=0x8f0c34 -> ec (0x4e9362); c34[1]=0x8f0c38 -> f0 (M53k).
Zeroing each sweep: 0x4e8d74 (c6c), 0x4e8d80 (c34). Slots 2/3 (0x8f0c74/78): no consumer
pinned (OPEN).

## Yield functions (VERIFIED shape; resource identity INFERRED mineral/food/energy)
FUN_004e6960 (984 B, 10 callers), FUN_004e6d40 (814 B, 8), FUN_004e7070 (1.4 kB, 9):
args (fac, -1, x, y, 0); tile = y*40 + (x>>1) via 0x692184; read terrain dword +8, dword +0xc
(`sar 0x18` -> byte +0xf in 4e6d40/4e7070), byte +0 `&0xe0` vs 0x60 test; call 0x5831a0(x,y,0)
(4e6960 @0x4e69a6, 4e6d40 @0x4e6d7b); 4e7070 re-tests bit0/level<8 and can return -1
(0x4e70c0-0x4e70d0). Per-tile yield of the slot's resource at the crawler's position.

## Why c6c/c70 read 0 in this game (VERIFIED live census, year 2376, pid 2124624)
339 unit records: orders census {0:135, 2:145, 4:1, 6:1, 8:2, 10:2, 14:2, 24:50, 28:1} —
**no unit has order 3**; plans in use {-1:108, 0:59, 1:79, 2:49, 3:10, 4:2, 6:4, 7:7, 8:2,
9:16, 11:2, 12:1} — **no unit has plan 10**; of 151 live type rows exactly ONE has plan 10:
type 5 (+41 cost 3) = alpha #UNITS row 6 "**Supply Crawler**" (Infantry chassis, Supply
weapon; type idx = alpha json row − 1, plan column value 10 confirmed against alpha.txt
header ":551 `10 = Supply Convoy`"). No crawler exists and no convoy order is set, so the
crawler sweep contributes nothing and bc/c0/cc stay idempotent (explains M53l 75/75 stability).
Raw census: evidence/m53m_units.txt (+ evidence/m53m_ourunits.py output: all 9 of our units
parked at (45,11), bidx 70, good tile).

## Unit record layout additions (VERIFIED via machine disp + census)
x u16@0, y u16@2, type u16@10, hp byte@12, faction byte@14, order byte@17 (alpha ORDERS has
9 entries 0..8; live 24/28 = engine-internal values — consistent with skill pitfall "poke
0x18 inert"), dest u16@20/+28, assigned/home base u16@46 (census −1:3, else 0..74; −1 = none),
slot byte +38 (census 0:338, 2:1 — the outlier is a Former, order 28). +38 semantics OPEN
(convoied-resource slot selector?); +46 = convoy home base INFERRED (branch A vs B split).

## SIDE QUEST CLOSED — DAT_00985aec (era) writer (VERIFIED machine)
Sole direct store whole-.text: **0x4ddcf1 `mov ds:0x985aec,eax`** — cold branch reached only
by `jge 0x4ddcf1` (0x4ddb5a) past the `ret` at 0x4ddcf0, inside FUN_004ddaa0 (862 B, 2 callers:
0x51518b, 0x517e1e — UI dialog range; C++ exception frame, 0x5390-byte frame = chooser/setup
dialog). Flow: era snapshot to [ebp-0x494c] (0x4ddb3e-4d), call 0x5f1394(this,0,0); if return
>= 0: era := return value AND propagate the same dword into 8 faction-record slots
`[0x94d438 + f*0x20bc]` loop 0x4ddcf6-0x4ddd09. M53l's "zero direct stores" was a grep-render
miss (the `a3` mov-to-mem form prints `mov ds:0x985aec,eax`, not `mov DWORD PTR ds:`).
Loaded-scenario era arrives via pointer-based save load (INFERRED; all other 19 refs are
reads/cmps). Era-advance-by-year is NOT this store (chooser/setup path).

## Live delta (VERIFIED; year 2376 -> 2380 = 4 rounds + partial 5th)
Logs: evidence/m53m_watch.log (gdb), m53m_poll.log (10 Hz /proc poller — x86 hw watch
budget is 4 DRs, so only the 4 globals were watchable), m53m_pre/post.tsv,
m53m_poke_log.txt, m53m_orig.json. Pokes (idle, no tracer, readback-verified): u300 ->
type 5 / order 3 / cat 0 / bidx 70, moved to (45,10) [ti 422: rec[8]=0, level 0 =
yield-OK]; u279 -> type 5 / order 3 / cat 1 / bidx 73, left on base-70 tile (45,11)
[ti 462: rec[8]=0xf3 bit0 set, level 0 = good].
- **0x8f0c6c: 19 fires = 10 x `new=1 eip=0x4e8f3c`** (return of the branch-A accumulate
  0x4e8f35) **+ 9 x `new=0 eip=0x4e8d79`** (zeroing 0x4e8d74). **0x8f0c70: 19 fires =
  10 x `new=1 eip=0x4e8e89`** (return of the branch-B inc 0x4e8e82) **+ 9 x `new=0
  eip=0x4e8d80`.** Eip histogram 0x4e8f3c/0x4e8e89/0x4e8d79/0x4e8d80 only — all inside
  FUN_004e8d60. Yield fn returned 1 for that tile. Sweep ran 2x per base per round.
- 0x8f0c34/38: 0 fires — consistent: u279's bidx 73 = Factory Drift = FACTION 2 base
  (fac u16 514 = 0x202; names not unique), faction gate 0x4e8e21 skips the fac-3 unit in
  that sweep; branch B short-circuits before the c34 block for base 70.
- **Convoy order persists**: poked +17=3 survived 4 rounds untouched; unit array
  compacted mid-run (u300->u252, u279->u273, values moved intact); the movement executor
  ignored the route-less convoy (skill pitfall stands: order fields are executor OUTPUTS —
  but the economy sweep consumes them as INPUTS directly).
- **base70 'Climactic Research' row = 0x962d30** (= 0x95da10 + 70*0x130; NOT 0x962d50 —
  my spec arithmetic was wrong; child corrected via name+owner byte). pre->post: bc 11->12,
  c0 7->8, cc -3->-2, d0 0->3, minerals 0->15, progress 22->12, f0 7->5. cc = bc - ec
  (ec 14 = pop 7x2) and d0 = c0 - f0 - e0 (8-5-0=3) hold live ✓; income applied 4x,
  progress += cc 4x ✓.
- **bc/c0 net +1 despite 10 accumulate fires each**: `bc += c6c[0]` is UNCONDITIONAL
  (machine 0x4e9331-0x4e9344: mov ecx,[0x8f0c6c]; add edx,ecx; mov [eax+0xbc]) — the
  accumulation lands only when 4e92c0/4e93f0 run with the current base's sweep result
  still hot; inter-base zeroing (0x4e8d74/80 fire at every base's sweep) eats the rest.
  Exact per-round caller multiplicity OPEN (M53n).
- base73 'Factory Drift' (owner 2) pre->post: bc 12->12, c0 2->3 (+1 — plausibly a 4e93f0
  call ordered before base 73's sweep zeroed the stale c70=1; INFERRED, OPEN).
- After: year 2380, cur 3 (our turn), nb 75->76 (new base appeared during run — game
  progression), era 2, mask 0xff08, pid 2124624, TracerPid 0, idle clean. "Do you really
  want to quit?" dialog popped after 4/8 turns — cleared via Escape onto "Oops, no,
  wait!" (never clicked, per skill rule). Restore OK (originals back at new homes
  u252/u273 bytes 0..48; slots 279/300 recycled by the game); re-census: 0 crawler-shaped
  units remain -> c6c/c70 back to structural 0.
