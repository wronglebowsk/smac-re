# NEXT_PROMPT — SMAC RE, session 66

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53m (**M53m done, session 65**); open: **M53n (THE PICK)**,
then the "Later" list.

## First actions
1. `grep -n '^## \|^- \*\*' ~/.hermes/skills/smac-cvr-format/SKILL.md` then `sed -n 'A,Bp'` on the 1-2
   bullets/sections you need (pitfalls + the code area). **Do NOT `skill_view` the whole file** (55 KB,
   ~90 % irrelevant per milestone).
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 65 (M53m) is the latest milestone.
3. `git status`; then `python3 scripts/milestone.py start <ID>` (never commit to main).
4. Live state: game up (`pgrep -x terran.exe` → 2124624), year 2380, cur_player 3 at last check —
   **re-verify `scripts/smac_state.py --json` before any our-turn assumption**, nb 76, era 2, mask
   0xff08, pid stable across sessions. Our base = idx 70 'Climactic Research' row **0x962d30**
   (= 0x95da10 + 70·0x130; NOT 0x962d50) — the ONLY base with owner byte@4 == 3. The Colony = idx 23, owner 2 (names NOT unique across factions — re-locate
   by owner byte + name). Unit slots SHUFFLE (array compaction, session 65): re-locate units by
   faction byte@14, never stale indices. Economy snapshot `scripts/m53l_snap.py` (cols after f98 are
   bc c0 c4 c8 d0 cc f0 — d0/cc swapped vs memory order per print stmt; header labels stale).

## Footing — the turn economy pipeline (M48d → M53m, VERIFIED unless marked)

### M53m (session 65): crawler sweep — `evidence/m53m_findings.md` (all cites there)
- **c6c/c70/c34 sole feeders = Supply Crawler**: plan(type+42)==10 (alpha PLANS[10] "Convoy/Resource
  Convoy"; ONLY plan-10 type = 5 = Supply Crawler, cost 3, #UNITS row 6) ∧ order(unit+17)==3 (alpha
  ORDERS[3] "Convoy") ∧ unit+14==base owner (gate 0x4e8e21). Branch A (bidx unit+46 u16 == cur base
  idx ∧ tile ti = y·40 + x>>1 (unit x@0 y@2) has (terr[8]&1)==0 || level>7): slot = unit+38; calls
  0x4e8efa→4e6960 / 0x4e8f0b→4e6d40 / 0x4e8f1c→4e7070 (slot 3 → 0 + 0x8f0cc8:=0); accumulate
  **0x4e8f35** `add [ecx*4+0x8f0c6c],eax`. Branch B (bidx≠cur ∧ ≥0 ∧ unit on base tile): **0x4e8e82**
  +1 to slot, then `jmp 0x4e9274` (c34 block UNREACHABLE from B). Good tile (bit0 set, level<8) ∧
  bidx==cur: **0x4e9009** `inc [cat*4+0x8f0c34]`. Zeroing 0x4e8d74 (c6c)/0x4e8d80 (c34) every sweep.
  Slots: c6c[0]→bc, c6c[1]=c70→c0, c34[0]→ec, c34[1]=c38→f0. Yield fns (fac,−1,x,y,0): tile
  y·40+x>>1, terrain +8/+0xc/+0&0xe0, call 0x5831a0; 4e7070 can return −1 — resource identity per
  slot INFERRED; slots 2/3 (0x8f0c74/78) consumers OPEN.
- **Live proof (4 rounds 2376→2380, poked 2 fake crawlers)**: c6c[0] 19 fires = 10× new=1 eip
  0x4e8f3c + 9× zeroing 0x4e8d79; c70 19 = 10× new=1 eip 0x4e8e89 + 9× zeroing; c34/38 0 (base 73
  'Factory Drift' is FACTION 2 — fac gate skips; names not unique). Sweep runs 2× per base per
  round. **Convoy order persists** 4 rounds; movement executor ignores route-less convoy but the
  sweep consumes records as INPUTS (refines skill poke-pitfall). Census (year 2376): NO unit had
  order 3 / plan 10 → structural zero (the M53l idempotency explanation). Unit layout: x@0 y@2
  type@10 hp@12 fac@14 order@17 dest@20/28 bidx@46 slot@38 (+38 semantics OPEN; census 0:338, 2:1).
- **bc += c6c[0] is UNCONDITIONAL (0x4e9331-44) yet bc netted +1 per 10 fires** — the add lands
  only when 4e92c0/4e93f0 run with the current base's own sweep result still hot (chain adjacency);
  inter-base zeroing eats the rest. Caller multiplicity/schedule = **M53n**. base73 (fac 2) c0 took
  stale +1 (a 4e93f0 call before its sweep zeroed c70 — INFERRED, OPEN).
- **Era writer closed**: sole direct store to DAT_00985aec = **0x4ddcf1** (cold `jge` 0x4ddb5a past
  the ret, inside FUN_004ddaa0 chooser/setup dialog, callers 0x51518b/0x517e1e; eax = 0x5f1394
  return ≥ 0; propagates same dword to 8 slots 0x94d438+f·0x20bc). M53l's "zero direct stores" was
  a grep-render miss (`a3` prints `mov ds:0x985aec,eax`). Loaded-scenario era = save load INFERRED.
### M53l (session 64): production inputs — `evidence/m53l_findings.md` (all cites there)
- **+0xcc (rate) sole writer 0x4e937b in FUN_004e92c0** (per-base; 12 callers = pipeline passes):
  `bc += DAT_008f0c6c` (0x4e9344); `ec = pop(base+6) × DAT_0092a27c(=2, store 0x5784f2) + DAT_008f0c34`
  (0x4e9362); `cc = bc − ec`; HQ-bit bump 0x8f0c48 := faction+0x2880 +2 (0x4e92f5-32a); progress clamp
  (cc<0 ∧ prog==0 → −1; cc≥0 ∧ prog<0 → 0); faction total `&DAT_0094dc2c[f·0x20bc] += max(cc,0)` cap 99
  iff DAT_008f0d64 == 1. Live Colony: 28 − 22 = 6 ✓ (22 = pop 11 × 2).
- **+0xc0 (gross) exactly 3 stores, all FUN_004e93f0:** 0x4e943f `×= 2` gated (DAT_00985ba8 ≥ 0 ∧
  base[ba8] same faction ∧ head ∈ [−37,−34]); 0x4e9459 `+= DAT_008f0c70`; 0x4e9525 `×= (esi+2)/2` where
  esi = count of FUN_00421fe0(19/20/21/22, cur_idx, 0) true + same-faction flags on bases DAT_00985bac
  /0x985bb0 (all −1 live → mult 1.0). d0 = c0 − (c38+c4c) − e0 and its stores stand from M53k.
- **bc/c0/cc PERSISTENT**: per-turn recompute is idempotent when c6c = c70 = 0 — live 75/75 stable
  (`evidence/m53l_delta.txt` + M53m). Income: 21/24 changed bases min += d0 exactly; 2 (UN DR, Hawk)
  += POST-recompute d0 → **income add reads d0 AFTER 4e93f0 in the same base pass**; 3 bases got
  +1..+3 EXTRA beyond d0 (UN HQ +3, UN Education +2, Morgan Metallurgy +1) — unexplained (M53n
  target); prog += cc 9/9 ✓ (0x4ee8c7).
- **Mask 0x985b10 = TWO BYTES** (b10 = facs 0-7, b11 = 8-15; 4e40a0 tests LOW byte only 0x4e40b5).
  5 writers pinned (5a0fa0/597ee0/59ec90/4df630/4e0720 — `m53l_mask_refs.txt`). INFERRED semantics:
  standard-rules set = player + aliens 8-15; the 7 AI human factions sit OUT (era prices, no clamp
  B, race-scan targets them).
### M53k (session 63): accumulation side — `evidence/m53k_findings.md` (d0 sole writer 4e93f0
0x4e9557/57f mirror +0x94; +0x40 per-turn writers all in 4ef6d0: income add 0x4ef7f6 gated d0≥0 ∧
head≠−38 ∧ +0x30&2, unit spend 0x4efedd + clamp A, project spend 0x4f0ca1-6, drain 0x4f1e3f; clamp B
0x4f0cc3-e9 in-mask payers → max(0,min(10,d0)); mirror +0x98 := +0x40 always; ARM = STOCK ≥ FULL price
gate 0x4f0a3d (edi = 4e40a0 × table +0xc); race scan 0x4f0af0 out-mask currents only, defers to
funded in-mask rivals; +0x3c progress DISPLAY-only 0x4ee8c7; claims: projects 39-71 need slot −1
0x4ef925, facilities ≤ 34 need bitmap bit clear 0x4ef982)
### M53j (session 62): claim array + completion — `evidence/m53j_findings.md` (claims 33 dwords @
0x985b3c idx = project−0x27; completion writer 0x4f0d83; THE POP = FUN_004ef5d0: counter −=1, queue
shift, +0x4c −=1, re-arm 5a6e70/5a73f0)
### Standing (do not re-derive)
- **Base record (REAL byte offsets, array 0x95da10 stride 0x130):** x u16@0, y u16@2, **owner byte@4 =
  faction** (machine: 4e92c0/4e93f0 use it as `f·0x20bc` record index; ground truth idx 70 ours = 3,
  idx 8 UN = 7; byte@5 usually == byte@4, idx 0 differs 2/6 — OPEN), pop byte@6, +0x30 flags (bits 23
  /31 completion path, bit 1 gates income add), +0x3c progress, +0x40 minerals, +0x44 active mirror,
  +0x4c pending (cap 9), queue @0x50..0x74, +0x8c..0x90 40-bit facility bitmap (bit i at +0x8c+(i>>3),
  `DAT_0095da9c`), +0x94 d0 mirror, +0x98 minerals mirror (equal 75/75), +0xbc bc accumulator, +0xc0
  gross, +0xc4/+0xc8 semi-active (values 5..11; 2 changed −1/−2 in one turn — OPEN), +0xcc rate, +0xd0
  net income, +0xe0 (zeroed per turn), +0xec upkeep (pop×2 + c34), +0xf0 upkeep sum, +0xfc; f38 =
  0x00dfbe41. 4ef6d0 loop ptr 0x95da14 = base+4. **Per-base pipeline:** FUN_004f5a70(base_idx) runs
  4e8d60 → 4e78e0 → 4e92c0 → 4e93f0 → 4eaa10 → 4ef6d0 → 4f26e0 → 4ee410 per base per round (+ second
  pass with DAT_008f0d64 = 1; NAMED.md 4f5a70 row).
- **Globals:** year 0x985b00, cur 0x985dcc, nb 0x985af4, unit count 0x985af0 (339; slots shuffle),
  mask 0x985b10 (0xff08), era 0x985aec (2; writer 0x4ddcf1 chooser), 0x985b30 (2), era table 0x68cbb8
  {13,12,11,10,8,7}, solo 0x920434, cap 0x92a370 (10), cur base ptr 0x8f0d60, cur base INDEX 0x68cbb0,
  difficulty 0x92a290/94 (10/10), 0x92ada8 (2), economy block 0x8f0c2c/34/38/48/4c/6c/70/d38 (per-base
  by 4e8d60; feeders = M53m crawlers), upkeep into d0 = 0x8f0c38+c4c, base array 0x95da10/0x130, unit
  array 0x933278/52, type records 0x98ad88/52 (+41 cost factor, +42 plan), faction records 0x92ae14+
  f·0x20bc (+0x2880 = `&DAT_0094d694`, +0x2e18 = 0x94dc2c production total; terrain line
  `DAT_0092ae14 + tile·0x2c` = VALUE not address — verify), built counters 0x94de84[f·0x20bc+t],
  scratch 0x94d684/dc24, map width 0x692184 = 40, 0x92a378/37c = 80, claims 0x985b3c[33], scenario
  flags 0x985ac4 (bit31 blocks projects > 38; 0x800 Ascent), special base idxs 0x985ba8/bac/bb0 (−1),
  perception, faction names 0x927894+f·0x24 (mostly empty live).
## Static-reading kit
- **Cached whole-`.text` disassembly: `evidence/m53j_text.txt.gz`** (790702 lines, objdump -d -M intel
  of `programs/terran.exe`). Locate VA: `zgrep -n '  4ef7f6:' evidence/m53j_text.txt.gz`; windows via
  `grep -B/-A '  4ee8ca:'` — sed range anchors must be REAL instruction boundaries (mid-encoding anchors
  silently print nothing or run to EOF = 25 MB). VA→fn by bisecting `ghidra_out/index.csv` —
  **COMMA-separated** (col 0 addr `0x004ddaa0` style, col 1 name). **VA = file offset + 0x400000.**
- **POINTER-TYPE SCALES IN PSEUDOCODE — the trap:** Ghidra typed `DAT_008f0d60` copies `short *` in
  4ef6d0 renderings, so offsets there are HALF the byte offset (`psVar22 + 0x28` == machine +0x50;
  `* 0x98` == 0x130 stride); `int *` DATs scale ×4; 4ef6d0's loop pointer = base+4. But 4e92c0/4e93f0
  renderings are UNSCALED (verified vs disasm twice). `DAT_008f0d60[3]` = byte +0x6 (pop). NEVER trust
  a pseudocode field offset: pin against machine disp or live pread.
- Pseudocode `scripts/fn.py 0xADDR > evidence/<id>_fn.txt` (cite evidence-file line numbers); corpus
  `grep -rn <pat> ghidra_out/shard_*.c`; enclosing fn via `grep -n '^// ==== ' ghidra_out/shard_N.c |
  awk -F: -v L=<line> '$1<L' | tail -1`.
- **Alpha comment headers name the columns** (`alpha.txt` `:348 #CHASSIS`, `:387 #WEAPONS`, `:422
  #DEFENSES`, `:471 #ABILITIES`, `:560 #UNITS`, `:590 #FACILITIES`); `scripts/parse_alpha.py` →
  `data/alpha.json` (list index = live project idx − 1; UNITS: type idx = json row − 1; PLANS/ORDERS
  sections are value tables).
## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800×600).
  Preflight: no gdb, TracerPid 0, `ptrace_scope` 0.
- **Turn driver:** `python3 scripts/smac_play.py --turns N` (background OK with notify true). Stop a
  driver ONLY with `scripts/smac_play.py --mode stop` — never signal by name. After a run cur may sit
  on an AI faction — drive until cur_player == 3. A "Do you really want to quit?" dialog popped
  mid-drive (session 65): Escape onto "Oops, no, wait!", NEVER click. **Economy snapshot:** `python3
  scripts/m53l_snap.py > evidence/x.tsv` — read-only `/proc/pid/mem` walk of all bases (header
  `# year cur nb era mask pid`; after f98 the cols are bc c0 c4 c8 d0 cc f0); diff two snapshots by
  NAME. **Watchpoints: x86 DR budget = 4 hw watches** (8-byte windows need 8-alignment = 2 DRs each);
  pair with the 10 Hz /proc-mem poller `scripts/m53m_poll.py` for base rows. `scripts/m53k_watch2.gdb`
  pattern — bake addresses as LITERALS, printing `commands … continue end` per watch, `gdb -batch
  -nx -q -p PID -x scripts/x.gdb` under `timeout` backgrounded + drive + snapshot in ONE job.
  **Watchpoints fire on VALUE CHANGE, not stores.** Pokes via /proc/pid/mem while idle (no tracer) +
  readback; unit slots shuffle — restore at the record's NEW home if the array compacted.
## Milestone options (pick ONE)
- **M53n — the round call schedule (THE PICK).** Instrument ONE round: per-round order + multiplicity
  of the 4e8d60 / 4e92c0 / 4e93f0 callers (12 xrefs each: 4ef6d0 ×2, 4ee410 ×2, 4f5a70 ×3, 4f41f0 ×2,
  4f34b0, founder 4e47d0, 4eb6b0, 4f4060 ...) — which calls run with c6c/c70 HOT (chain adjacency) vs
  stale; why crawler base70 netted bc +1 per 10 sweep-fires; why fac-2 Factory Drift c0 took the stale
  +1. Approach: re-poke ONE crawler (m53m recipe: evidence/m53m_poke_log.txt, scripts/m53m_rw.py),
  watch c6c[0] (zeroing-fire eips = sweep callers; accumulate-fire = hot chain), watch DAT_008f0d60
  stores (current-base pointer = chain start — census its writers first), poller for base rows; drive
  to year+1. Close together: the 3-base extra-income anomaly (UN HQ +3 etc. — 4cce50 trio or other
  +0x40 writers firing on those bases?), +0xc4/+0xc8 meanings, who first sets c0 at founding (4e47d0 →
  4e93f0 with what c70). **Done when** the schedule is pinned to addresses with a live eip census.
- **Later:** unit+38 slot semantics + consumers of 0x8f0c74/78; 0x984d38 table writer/loader + who
  fills the 0x2100000 string arena; 4e4350 return-code semantics + `DAT_0092a368` source; tech table
  0x92fdd4 record layout (research tree); abandon path 0x4f07c2 + Ascent special 0x4f072e; +0x30 bit 1
  writer; who sets +0xe0 between recomputes (always 0 live); `FUN_004fe670` research-scaled table
  bytes; `FUN_0059ce10`'s trigger + random claim grant; why 74/75 bases show pending 0 with a
  non-empty head; byte@5 meaning; M50c-e, M51b.
- **Retired premises, do not resurrect:** the full chooser-era list lives in SESSION_NOTES sessions
  55-65; the live set: **"bc/c0/cc are recomputed from scratch each turn"** (PERSISTENT; per-turn pass
  idempotent when c6c = c70 = 0); **"Colony fac 3"** (owner byte@4 = 2 at idx 23); **"era table =
  pointer array"** (direct dwords {13,12,11,10,8,7} @ 0x68cbb8); **"4e40a0 tests the whole mask
  dword"** (LOW byte only); **"UN price 0 = literal price"** (race-scan unpaid path INFERRED);
  **"byte@4 is type/cluster"** (it IS faction); **"snap column labels are trustworthy"** (unpack
  contiguous ranges, label from true offsets); "5a6e70's return is a cost index" (boolean); "aa0 =
  completion count" (base index); "claim table is 0x985aa0[72]" (33 @ 0x985b3c, idx−0x27); "the pay
  pool is base+0xcc + 0x3c" (real:
  +0xd0 + +0x40); "pseudocode offsets are byte offsets" (short* ×2, int* ×4, loop ptr base+4);
  "bitmap at base+0x8a" (0x8c..0x90); "projects accumulate to completion" (gate is STOCK ≥ full price;
  +0x3c display); "clamp B applies to every payer" (mask-gated); "the −e0 term is active" (e0 zeroed
  before use); "M48's pinned-zero is
  unexplained" (income gate + clamp B); "The Colony @ 0x95f568" (idx 23 = 0x95f560); **"base70 row @
  0x962d50"** (it is 0x962d30); **"era DAT_00985aec has zero direct stores"** (0x4ddcf1 — a3 grep
  miss); **"c34 upkeep reachable from branch B"** (0x4e8e89 `jmp 0x4e9274` short-circuits); **"order
  pokes are inert for the economy sweep"** (the sweep consumes them as inputs; only the movement
  executor ignores route-less convoy); **"bc/c0 gain per sweep fire"** (+= unconditional but lands
  only on chain adjacency — net +1 per 10 fires).
