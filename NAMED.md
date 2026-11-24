## B10 (s226, BUILD, base-founder/destroyer leg - R2's new-game leg) 18/18 — FULL rows moved VERBATIM to `docs/named-archive-b10-rows.md` (s304-chain2 headroom rotation, sha1 d298981e8ece0d6e, byte-exact asserted); this stub governs.

- Ledger = M282 founder FUN_004e47d0(faction,x,y) + destroyer FUN_004e4e10 + golden-curve pairing (B3 engine pressed through the trace's 40 turns, 8 per-turn deltas t8..t34).
- FOUNDER: count<0x200 guard; 304-B record appended at start+count*0x130 (x u16+0, y u16+2, faction +4/+5); count+1. DESTROYER: count-1 with LAST-record compaction.
- CURVE: n_bases 18->26 on all 40 snapshots; t23 -1 = real destruction. WRITE: only the bases-count prefix dword changes, tail byte-identical, re-parse n_bases 19, founded record shape-invisible to the name scan.
- RIVALS: no-leg keeps 18 (32 divergences); all-events-on-turn-0 diverges at t0. BOUNDED BY B21: delta-derived schedules are LOSSY about ops (7-op curve vs 9-op log, 7/9 rows) - for OPS use the log.
- Command: `python3 -m sim.selftest --b10 programs/saves/m54b_clean.SAV` -> `PASS B10: 18/18 gates` (evidence/b10_basefound.txt); CLI exit 0; B8/B9 green; box untouched.

# NAMED — founding function table: moved VERBATIM to `docs/named-archive-founding-table.md` (s304-chain2, sha1 5e1635282e3cf2c9, byte-exact asserted); grep there for the evidence. One line per name kept:

- `0x5c9fc5` `ui_layout_three_parts(rect, obj)` (M)
- `0x5dd09c` `draw_rect_stateful(x, y, w, h, a, b)` (M)
- `0x598340` `file_open_and_dispatch(file)` — magic sniffing (H)
- `0x597a70` `load_map_or_scenario(file, mode, is_map)` (H)
- `0x596540` `read_decode_block(dest, nbytes, count=1, file)` (H)
- `0x596850` `load_save_state(file, mode)` (M)
- `0x64b9e0` compiler helper (security cookie / `_ftol2` class) (H)
- `0x4d3770` `unit_order_hold(unit_index, u16 mode)` — writes the order byte (H)
- `0x5ab240` `unit_remove_from_map(unit_index)` — unlink + sentinel (H)
- `0x584350` `unit_broadcast(idx)` — event `0x2101` (M)
- `0x5ab320` `unit_set_position(unit_index, x, y)` — **the move-exec primitive** (H)
- `0x5a58e0` `unit_move_stack(unit_index, x, y)` — move every unit stacked on this one's tile (H)
- `0x5a5a80` `unit_restack(unit_index)` — clear the tile to scratch (-3,-3), then move the stack back (H)
- `0x5a5cd0` `unit_park(unit_index, mode)` — push a unit off the map to scratch (M)
- `0x502c40` `unit_step(unit_index, dir, parity, …)` — one tile in one of 8 directions (H)
- `0x502cd0` `unit_move_to(unit_index, ?, dest_x, dest_y, …)` — the move executor (H)
- `0x4bf1e0` `unit_commit_move(unit_index, from_x, from_y, to_x, to_y)` — mover + effects + message (M)
- `0x585720` `unit_action_resolve(unit, param, mode)` — per-unit action executor (AI + end of turn) (M)
- `0x5abb40` `unit_array_compact()` — slides records down with `rep movsd` (H)

## Not yet named (candidates, ranked by `COVERAGE.md`)
- `0x5f6de9` — 305 callers, 550 B, 118 insns, no string literals
- `0x483470` — 292 callers, 556 B, 141 insns, no string literals
- `0x584010` — 249 callers, 108 B. **Known from M8**: the solo netcode "send" path that never fired in solo turns.
- `0x5a6330` — 224 callers, 1,596 B, 442 insns (big; likely a container/allocator helper)

## Method that worked (steps kept; the s32-s60 row pile rotated VERBATIM to `docs/named-archive-method-b10-era.md`)
Hygiene rotation #2 at s307 (M329 headroom, paired with `scripts/m329_named_rotate.py`'s M255-M258 move): 56 lines, 12,564 B, sha1 `16cd10eb5fc0`, byte-exactness asserted by `scripts/m329_named_rotate2.py`; git history is the trail.

1. `scripts/coverage.py` ranks by in-degree *after* removing compiler helpers.
2. `scripts/fn.py <addr> --max 40` - read the shape: parameter types, which globals it touches, what it calls, whether string literals appear (`grep -oE '"[^"]{4,40}"'` on the body; none => pure logic => look at field offsets instead).
3. Follow one callee to see what the primitive is (here `0x5dd09c` => graphics state wrapper => the caller is a drawing routine, not a data routine).
4. Write the row with the offsets that justify it, so a later session can falsify it fast.

The rotated tail is the B10 `## Not yet named` candidates plus the M24-M28 gdb/watchpoint rows, one line per row, gates/cites unchanged in the archive:
`0x582260 map_load_arrays` (2,724 -> `0x92a378`, 140,800 = W*H*22, 128) | `0x596850 save_load` (796 -> `DAT_00985ab8`, section table) | `0x597a70 load_save_blocks` (**corrected** from the `.MP` map loader) | `0x95da10 base_array` (37 x 304 B, count `0x985af4`, name +19, x +0, y +2) | `0x933278 unit_array` (119 x 52 B; +10 owner? no - **+10 is the TYPE INDEX per `## M327`**, owner +14) | `0x8f79e0 ui_singleton_base` (= what Ghidra prints as `in_ECX`; `+0x23bd4` = `0x91b5b4`) | `0x91b5bc selected_unit_index` | `0x91b5b8 orders_mode_flag` | `0x91b5c4 order_menu_pending` | `0x91b5f0`/`0x91b670 cursor_x_list`/`cursor_y_list` | `0x4d3f70 activate_at_tile` | `0x476580 map_widget_click`/`map_click_handler` | `0x4cffa0 issue_move`/`issue_attack_or_engage` | `0x4cdc70 exec_action_with_target`/`bombard_resolve` | `0x528930 submit_unit_action` | `0x512450 hotkey_dispatch_unit`/`order_menu_command` | `0x511960 hotkey_dispatch_cursor` | `0x512b40 key_handler` (+ the arrow-key block M27) | `0x920434 netgame_flag` | `0x92ae14`/`0x692184 tile_record_array` / map row-count | `0x934aa4`/`0x934ba8` unit records 119/124 | `0x5acc00 unit_can_act` (M327-corrected) | `0x5acab0 unit_idle_and_own` | `0x5acdb0 consume_all_movement` | `0x5ac650 unit_movement_total` | `0x529090 solo_order_dispatch` | `0x4d6fb0 issue_order` | `0x4cce50` named-order engine | `0x50cab0 refresh_selection_state` | `0x5010d0 tile_cursor_display` | `0x50ba00`/`0x50ba90 set_map_pane_mode` | the unit-record field map (`+17` order byte, `+18/+19` waypoint legs, `+20/+28` order tiles, `+40` MP used, `+41` last dir, `+42` watchdog) | movement cost 3 MP/tile, 6 MP/turn | `0x4e1f90`/`0x5255e0` arrow-move pre-gates. Load-bearing successors: `## M327` (+10), `## B25` (the container owns the coordinate space), `docs/named-archive-m32-m84e.md` (M32-M84e).

## (ARCHIVE) M89-M221: moved VERBATIM to `docs/named-archive-m89-m221.md` (s251 hygiene split - 619 lines, 55 headings; grep there for per-id semantics of M89-M221 incl. UNMERGED M101/M103/M109; git history is the trail)
## (ARCHIVE) M227-M245 + B1-B2: moved VERBATIM to `docs/named-archive-m227-m245.md` (s254 hygiene split - 133 lines, 10 headings; grep there for per-id semantics; git history is the trail)
## M246 (s197) — the save's last 4 B are a `timeGetTime()` save-CREATION stamp — FULL rows VERBATIM at `docs/named-archive-b28-rows.md:10` (§rotation-1 marker at `:8`, s316-chain1 headroom rotation, sha1 `fcd4989fdf15` — the region is bounded by its own terminator line, its line number AND full digest re-asserted by `scripts/b28_named_rotate.py --verify`); this stub governs.
- `FUN_00597ce0` writes the trailing dword from `timeGetTime()` (`local_8` line 15 → `FUN_0064c9a0(&local_8,4,1,iVar2)` line 44), the codec never reads it; Δ(dword) vs Δ(mtime) ≤ 2.5 s on 5/5 same-session pairs | shard_015.c | V
- creation-stamped, not file-write-stamped: `0x15c79939` on 3 files 486,979 s apart, `0x2db1b939` on 2 files 71,224 s apart | census G3, 17 saves | V

## M247 (s197) — the region map's row stride is `Rw>>1`, not `(Rw+1)/2` — rows in the same archived region; this stub governs.
- 6 referencing functions; the only element accessors `FUN_00582340`/`FUN_00582360` index `(param_1>>1)+DAT_0092ae18+(DAT_0092ad9c>>1)*param_2`; `(Rw+1)/2` occurs once image-wide (the length) | G4 | V
- builder `FUN_0058ce00` (y<Rh, x=(y&1) step 2<Rw) writes exactly bytes 0..78 at Rw=Rh=13; slack = Rh−1 for odd Rw, else 0 | G5 | V
- the slack is never written: bytes 79..90 = `0xcd` in 17/17 saves, none in 0..78; both .MP (even Rw) slack 0 | 17 saves + 2 .MP | V
- the byte VALUES: terrain record `+3` of the first of 9 sampled tiles with `+1 & 0xe0 > 0x5f`, else 0; `+3` unnamed | rule V, meaning OPEN

## M248/M249 (s198, PASS 5/5) — the region map's bytes are a per-region copy of terrain record +3, the map's REGION LABEL — rows in the same archived region; this stub governs.
- region byte = record +3 of the FIRST land tile of a centre-first 9-diamond sample at (x*5+dx, y*5+dy), 0 if no land; x wraps mod DAT_0092a378, y bounded by DAT_0092a37c; the 9 (dx,dy) read from 0x67850c/0x678990 | `FUN_0058ce00` shard_015.c:4690-4752, G1 9/9 | V
- stored == recomputed byte for byte: 19 files, 1809 cells, 0 mismatches, 38 wrapped samples | G2, `evidence/m248_region_values.txt` | V
- exactly 1 reader fn (`FUN_00556690`), 1 writer fn (`FUN_0058ce00`); 17 other refs = alloc/free/file-io/null-guard/clear | G3 | V
- record +3's ONLY writer is `FUN_00582d00`; 4 call sites, all map generation | G4 (18 record-array stores, 1 covers byte 3) | V
- +3 plane identical across 17 saves, turns 50,51,52,53,60 | G4 | V
- +3 < 0x40 on every land tile, >= 0x41 on every water tile, 0x40 unused (19 files); index into DAT_0094eda8 (stride 0x20bc), split at 0x40 | G5 | V (census), OPEN (what names the partition; 25 ids / 47 components, 130/16626 adjacencies differ)
- instrument `scripts/m248_region_values_census.py` -> `evidence/m248_region_values.txt` | rc=0 | H

## B3 (s199, BUILD track, PASS 6/6) — `sim/turn.py`: M30's turn engine, executable, replays the recorded trace 67/67

| claim | evidence | conf |
|---|---|---|
| parity rule: the recorded rows are an ORDERED SUBSEQUENCE of the engine's emissions, because the trace is a 0.2 s change-set sample (`turn_trace.py:59`) | `sim/selftest.py::run_replay`; matched=67/67, 220 emitted, 154 collapsed, 11/cycle — `evidence/b3_turn_replay.txt:2` | V |
| the engine walks the 8 faction slots ASCENDING; our slot is 3 and is the only slot at which tf==0 is ever seen (21 rows, all cur==3; own==3 in 67/67) | G1/G2 — `evidence/b3_turn_replay.txt:1-2` | V |
| the YEAR fires on the 7→0 edge while `cur` is still 7 (witness row 22 = t 88.631, cur 7, tf 2, year 2221); the other 7 edges score 22, 22, 10, 0, 0, 0, 6 /66 | G3 — `evidence/b3_turn_replay.txt:3` | V |
| `tf` is cleared ONE STEP AFTER `cur_player` is written to 3 (merge them and parity is 5/66); the 4 (3,2) rows are 5, 14, 23, 40 | G4 — `evidence/b3_turn_replay.txt:4` | V |
| 48 of 322,560 candidate models (cyclic order × year edge) reproduce the trace = 6 cyclic orders × 8 rotations; all 48 share 0→1, 1→2, 2→3, 7→0 and year@7; only {4,5,6}'s internal order is free | G5 — `evidence/b3_turn_replay.txt:5` | V |
| 20 presses = 20 year bumps = 20 tf clears, year 2213→2233, final (3,0,2233) == last row | G6 — `evidence/b3_turn_replay.txt:6` | V |
| OPEN: the press transition (3,0)→(3,2) is unobservable (no_press variant still 66/66) — does the engine write turn_flags before cur_player?; `nb` (base count, 0x985AF4, 51→58 with one decrease at row 28) is unmodelled | G4 line, cursor | OPEN |
| instrument: `python3 -m sim.selftest --replay evidence/m30_turn_trace.jsonl` → `PASS B3: 6/6 gates` | rc=0, 22.3 s, one invocation | V |

## M250-M254 (s200-s201; PASS 7/7 + 7/7 + 7/7 + 8/8 + 8/8) — the region generator, the per-faction per-region verdict byte, the coarse map's single consumer, the four verdict codes, and the contact bits — FULL rows VERBATIM at `docs/named-archive-b28-rows.md:41` (§rotation-2 marker at `:40`, s316-chain1 review-round headroom rotation #2, sha1 `c839a606651b` — the region is bounded by its own terminator line, its line number AND the full digest re-asserted by `scripts/b28_named_rotate2.py --verify`); this stub governs. M254's bit-naming row stays INFERRED (named); every other row is V.
## M255-M258 (s201-s202, PASS 8/8) - ROTATED VERBATIM to `docs/named-archive-m255-m258.md`
Hygiene rotation at s307 (M329 headroom): 36 lines, 6,734 B, sha1 `9111d3b24758`, asserted byte-exact by `scripts/m329_named_rotate.py`; the archive holds the full rows, git history is the trail. One line per claim, gates and cites unchanged:

| claim | evidence | conf |
|---|---|---|
| `FUN_005b2970` has exactly 4 call sites, one per caller: `0x4e1151`, `0x4e122b`, `0x57d2a0`, `0x57f1ec` | G6, `evidence/m253_region_categories.txt:6` | V |
| the 4 callers' gates: `57c550`'s skipped by `je`/`jne 0x57d2a5` on `ds:0x9264d8` (written only `0x57e495`=1, `0x57e900`=0) + `bl & 2`; `57ecf0`'s ungated and preceded by 6 stores to the world-dim globals `ds:0x92ad??`; `4e10c0` ORs `0x80` into `ds:0x985ae8`, `4e11b0` ANDs `0x7f` | G6, `:6` | V |
| modes from literals: `57ecf0` = {FACTIONS, WORLDSIZE, SCENARIO, INTRO} + 2x alpha-section opener `FUN_005ea431`; `57c550` = {RULES, USERULES, RELOADFAC, DIFFICULTY, CUSTOMNAMES, FACTION}, 0 openers; caller sets `512b40`/`516b80` (pair), `57e890`/`57f740` (`57c550`), `522850`/`57f740` (`57ecf0`) | G7, `:7` | V |
| **exactly ONE caller satisfies ungated + world-dim stores + alpha reads + scenario literals: `FUN_0057ecf0` = NEW GAME**; `57c550` = scenario/MAP-FILE load; `4e10c0`/`4e11b0` = menu/editor REGENERATE pair (accept vs retry-vote) | G8, `:8` | V (discriminators), INFERRED (naming) |
| M256: the worth test deciding 7 vs 8 is `cmp edx,ecx`@`0x5584b4` (`jle`->0) + leg2 `cmp eax,ecx`@`0x5584d8`, legs ANDed, `or eax,ecx`@`0x5584eb` with the 4-bit reason word, `sete dl`@`0x55850e` | G1-G2, `evidence/m256_worth_operands.txt:5-6` | V |
| M256: LHS = `2 * ((DWORD[block+0x94d810] - DWORD[block+0x94d818] + [ebp-0x60]) * [ebp-0x3c])` (loads `0x55848f`/`0x558495`/`0x55849b`, `imul` `0x5584a2`, `shl 1` `0x5584a8`); `[ebp-0x3c]` = BYTE[block+region+0x94e5a8] | G3/G5, `:7,9` | V |
| M256: `[ebp-0x60]`'s live def at the test is `0x558424` = 3 + (ds:0x985afc > 75) + `FUN_00531090(ds:0x985b30,0)` + (BYTE[block+region+0x94eca8] < 4 ? 1 : 0) + the fold count; reason word = bit3 of WORD[0x94e7a8+row] \| mult>=0x14 \| WORD[0x94eaa8+row]-WORD[0x94eba8+row]<4 \| (mult!=0 and 0x94eca8 byte<2) | G3/G4, `:7-8` | V (chain), OPEN (why the fold sum is overwritten) |
| M257: RHS = WORD[0x94eaa8 + 2*region] (`0x5584aa`) + WORD[0x94eaa8 + esi] (`0x558452`), summed `0x5584b2` after `xor ecx,ecx` `0x5584a0`; region loop `[ebp-0x10]` 1..127 (`inc/cmp 0x80/jl` `0x558b1b`-`0x558b25`); 0x94eaa8 refs image-wide = 4 | G4-G5, `:8-9` | V |
| M257: `esi = [ebp-0x18]` = the row slot - **superseded by M273-M276**: the fold is `2*region + 8380*arg` (not 188), the live region count is 91 < the 94-slot row, and the scaled reads of regions 94..127 land INSIDE the sibling verdict array at `0x94eba8` (gap 256) | `evidence/m273w3.gdblog`, `scripts/m273_rowstride_watch.py --replay` 7/7, M274 G2/G6 | CLOSED (was OPEN) |
| M258: `0x94e4a8, 0x94e5a8, 0x94e628, 0x94e6a8, 0x94e7a8, 0x94e8a8, 0x94e9a8, 0x94eaa8, 0x94eba8, 0x94eca8, 0x94ed28, 0x94eda8` (end `0x94ee28`) = 12 per-region arrays, every gap 0x80 (byte) or 0x100 (word), ZERO dword accesses, 128 entries each | G8, `:11` | V |
| M258: **RETRACTION of the s201 row** "0x94e7a8 flag bytes" - it is a per-region WORD array (whole-word ops `0x5577e9`/`0x5577f8`/`0x5580d6`/`0x5580ed`, 28 refs to the +1 high byte), gap 0x100 | G8, `:11` | V |
| M258: the 8-slot fold (`0x558075`-`0x5583ac`) walks WORD[0x950764 + 2*region] and BYTE[0x950664 + region] stepped by the faction stride `0x20bc`, doubling the pair per set bit of BYTE[block+0x94d44c]; accumulators `[ebp-0x60]`/`[ebp-0x6c]`, count `[ebp-0x68]` | G6, `:10` | V |
| M258: the fold's second row is 0x200 below (`mov bx,[eax-0x200]` `0x558082` = `0x950564 + 2*region`); `0x950564` is its own table base (`lea esi,[esi*2+0x950564]` `0x4f7a0a`); both tables lie past the 3,067,904-B file image (ends VA `0x6ed000`) | G7, `:11` | V (pcs), OPEN (extents) |

## B4 (s203, BUILD track, PASS 9/9) — `sim/base.py` + `sim/economy.py`: the round economy, executable

| claim | evidence | conf |
|---|---|---|
| base record a reimplementation needs: owner byte +4, pop +6, growth +7, name +19 (NUL, within 32 B), storage +0x40, queue item id +0x50, completed-facility bitmap +0x8c (byte item>>3, bit 1<<(item&7)), totals +0xc4/+0xd4/+0xe4/+0xf4, **GROSS energy bucket +0xfc**, other buckets +0x100/+0x104/+0x108 | G4 decodes the recorded 76-dword live read (`evidence/m46e_econ.json:16215`) → 13/13 of the harness's own field values — `evidence/b4_economy.txt:20` | V |
| the name field is 32 B, not 20: names run to 22 chars ("Morgan Energy Monopoly", "U.N. Court of Justice", "Valley of the Faithful") and `scripts/m46_econ.py:106` (`r[19:39]`) truncates them; 0/311 records over 17 saves lack a NUL in the 32-B window | G5 — `evidence/b4_economy.txt:21` | V |
| faction round: gross = Σ base+0xfc; upkeep = Σ per-facility cost, 0 if the item is on the faction's disabled list; net = gross − upkeep; energy′ = max(0, energy + net − ledger) | G6 reproduces the game's own HUD globals (2,2,0) on both recorded rounds and the energy 19→19 — `evidence/b4_economy.txt:22` | V |
| the aggregator also writes per-base upkeep (0x744f2c, 75 entries, nonzero only on the player's own base) and 39-wide item counts (0x745738); the engine reproduces both arrays exactly | G7 — `evidence/b4_economy.txt:23` | V |
| item upkeep = alpha `#FACILITIES` column 3 at line (runtime id − 1), names matching, for ids 1/3/6/7/8 = 0,0,1,1,1; Σ 3 raw, 2 with item 8 disabled = the recorded 0x744f28 | G8 — `evidence/b4_economy.txt:24` | V (the five pinned ids) |
| the model is the only one of four that matches the recorded triple: no disabled list (2,3,−1); gross from +0x100 (0,2,−2); alpha indexed without the +1 (2,3,−1) | G9 — `evidence/b4_economy.txt:25` | V |
| an idle PRE-FOUNDING faction nets 0: 0 bases ⇒ gross 0, upkeep 0, net 0, energy 15 flat on 12/12 rounds, and the recorded HUD panel reads 0/turn on all 3 legible rounds | G1-G3 — `evidence/b4_economy.txt:17-19`, `evidence/m44d_idle.json:138,150,811` | V |
| ANSWERED by B29: alpha's column vs M46's live table (Fusion Lab 3/4, Quantum Lab 4/3, Nanoreplicator 6/4, Quantum Converter 5/6) is M46's alpha-INDEX numbering — under rec i = alpha row i-1 the derived table reproduces all four values at that index, and the order IS alpha's for ids 1..38 (B29 G3 38/38 name+upkeep, mutants MU1/MU3; `evidence/b29_item_table.txt:78`); still OPEN: the facility bitmap's width past +0x8f; the gifts and spending-ledger terms | `evidence/b4_economy.txt:14-17` | V / OPEN |
| instrument: `python3 -m sim.selftest --replay evidence/m44d_idle.json` → `PASS B4: 9/9 gates` | rc=0, 1.3 s, one invocation (invocation 1 failed 8/9 on the name width — that was the finding) | V |

## M259-M261 (s204, PASS 14/14) — the per-faction mask band, the static map views, the 0x679f98 class — FULL rows VERBATIM at `docs/named-archive-m333-rows.md:6` (§rotation-1, s313-chain1 headroom rotation, sha1 `f78e7ef04359` — the region is bounded by an explicit terminator line, its line number AND full digest re-asserted by `scripts/m333_named_rotate.py --verify`); this stub governs. Pre-mutation-law registry (no MU ids — the harness era starts at `## M308`); the G-ids are the archive rows' own gates, and the byte-reads they printed are `evidence/m259_m261_census.txt` (`:30` SUMMARY 14/14, one invocation, 3.3 s).
- M259 the band: terrain record bytes +16..+43 (dwords 4..10) = the FACTIONS 1..7 per-faction copies of the record's `+8` master mask, `[terrain_base + 0xc + (row*0xb + fac)*4]` (faction 0 uses `+8`; both whole-array refreshes guard `test ebx,ebx / je`); writers CLOSED at 10 indexed + 1 walk store, every site named (G1-G6); 44 indexed reads in 25 functions (G7). **RETRACTS M240's "a record is two 22-byte map columns" for bytes 16..43** — the `.MP` "7 equal dwords == +8" (planetx 8192/8192) IS this band.
- M260 the views: the live 0x224b8 spacing occurs 0 times in the 3,067,904-B image — `immediates naming 0x224b8: 0; 4-byte LE pattern ... offset -1` (G8, `evidence/m259_m261_census.txt:16-17`); view 0 is static .bss at 0x8f79e0 (sole immediate store 0x5803e1, printed by G10 at `evidence/m259_m261_census.txt:21`; ctor FUN_00518820's only call site 0x580406, G9); the ctor's stores reach `this+0x23bec` = 146,412 B > the 140,472 stride, so the stride is not an object size (G10 `evidence/m259_m261_census.txt:20-21`); the save codec walks the 8 entries as POINTERS, clearing `*(p+0x1dd74)` for entries 1..7 only (G11). **CORRECTED IN PLACE by M262 — RETRACTED: "the ~140 KB views are not allocated"**: entries 1..7 ARE allocated at startup, 0x22480 B each, by the pointer-arithmetic `mov [esi],eax` at 0x5803bb (0 only on the alloc-failure path) — M262's own rows: `docs/named-archive-m332-rows.md` (G2), `evidence/m262_m264_census.txt:24` (11/11); 0x224b8 = 0x22480 + 0x38, a 56-B heap header (INFERRED).
- M261 the class: vtable 0x679f98 = 88 slots, 2 installs, 15 slots differ from ALL of 0x6717cc/0x671d94/0x67164c (G12); all 15 named with size + callee count (G13); ctor chains FUN_0062d630 <- FUN_0045a8b0(1)/FUN_005b3000(2)/FUN_00641f3c(3) and FUN_0062d764 <- 6 callers, incl. FUN_00636b1e = "Start a new session or..." (session chooser) and FUN_00493a10 = "Gamma Correction" (G14).

## M262-M266 (s205-s206, PASS 11/11 + 12/12) — EVERY address and gate body VERBATIM at `docs/named-archive-m332-rows.md` (s311-chain1 headroom rotation, sha1 `4dc92495311e`, byte-exact asserted by `scripts/m332_named_rotate.py`); this stub governs. Pre-mutation-law registry (no MU ids — the harness era starts at `## M308`); the G-ids are the archive rows' own gate ids. `evidence/m262_m264_census.txt:24` (11/11), `evidence/m265_m266_census.txt:13` (12/12).

- M262 the view-table band `0x7cdecc..0x7cdee8`: 426 mentions, exactly 1 store names it (`0x5803e1`, entry 0 = the static object), all 39 indexed `[reg*4+0x7cdecc]` mentions in 12 functions are reads/cmps, 0 indexed stores (G1); entries 1..7 come from FUN_00580260's 7-iteration loop at `0x580392` — alloc `0x22480` -> 515-B SEH ctor `0x469650` (not the view ctor `0x518820`) -> `mov [esi],eax` at `0x5803bb`, with `xor eax,eax` only on the alloc-failure path, which is why M260 read the loop as a zero-fill (G2); `0x22480` named once image-wide, `0x224b8` zero, delta `0x38` (G3); 35 address-of-band sites, 4 escapes all handing out `&DAT_007cdecc`, the 4 lea'd cursors re-read only (G4); entry 1: 32 reads in >=12 functions, and the load-side FUN_00597ee0 walks entries 2..7 from `0x597f6d` clearing `*(entry+0x1dd74)` + calling FUN_00479e90(entry) (G5).
- M263 the band on LOAD: writer set 8 functions / 10 indexed stores + FUN_0051c750's walk store `0x51ca52` (G6); only FUN_00596850 (`0x596fd0`) and FUN_00597a70 (`0x597cc0`) call map_load_arrays `0x582260`, and their depth-9 forward closure + 4 callers = 276 functions meets the writer set in ZERO with no band writer in a vtable slot -> **the LOAD trusts the file's band bytes** (G7); FUN_00583c70 has 0 references so its band store `0x583e1d` can never execute; the other writers hang off gameplay passes (G8).
- M264 allocator + record cursor: FUN_005be090 (72 B) is operator-new -> `0x649e00` -> `0x649e70(size, ds:0x99d5f8 = the heap handle,1,0,0)`, the NULL path reports through the global fn ptr `ds:0x671320` ("FATAL ERROR" / "Windows has run out of virtual memory...") (G9); 119 direct sites in 74 functions, and the 14 sites in 13 functions storing `[obj+4]` within 8 insns are store-after-alloc, not dispatch (G10); `ds:0x9965b8` = 6 mentions = 3 RMW pairs is a LINEAR RECORD CURSOR: FUN_005dbb5f stamps a blank record (10 zero stores + `[rec+8]=9`) and `add ecx,0x2c`, FUN_005dbbe6 rewinds by `[rec+0x10]*[rec+0x14]` and frees `[rec+4]` via FUN_0064a7f0, FUN_005dbdc0 (1303 B) is the FILLER that allocs / stores / advances by the same product (G11).
- M265 the 7 blocks are class-`0x675964` objects: ctor FUN_00469650, exactly 7 call sites, `[ebp+0x8]` gates `mov [this+0],0x675964` (the only mention image-wide) (G1/G2); `[desc+4]` IS the base-subobject offset (`0x675964->0x21a6c`, `0x6763fc->0x22050`, `0x678458->0x23d94`, each matching the `add ecx,K` feeding `call 0x5e3b80`) (G5); `+0xc..+0x1dd6c` = **201 x 608-B elements** (ctor/dtor `0x62514b`/`0x62516c`), the 201st ending 8 B before the `+0x1dd74` the load-side clears (G3); the `0x6725ac`/`0x6725a4` vptr pair (delta `0x444`) is stored at 5 sites in 1 ctor + 4 destructors (G4, roles corrected by `## M267-M268`); `0x21a6c + 0xa14 = 0x22480` = the allocation exactly (G6); dispatch goes through `[desc+4]` (G7).
- M266 FUN_00583c70 is dead code, not a split body or a duplicate: 0 occurrences in .text operands AND 0 as an LE dword anywhere in the image, all 8 sections (G8); `0x583c20` rets at `0x583c6b` + four `0x90` pads + a real prologue (G9); 1 of 8 functions in `0x583000..0x584300` with `n_callers==0`, all 8 with 0 address-taken dwords (G10); its 159-insn mnemonic signature matches 0 other functions >=40 insns (G12); it is a terrain-record helper of FUN_00583c20's family (G11).

## B5 (s207, BUILD track, PASS 9/9) — `sim/units.py`: the arrow-key step and its movement-point economy, executable

`python3 -m sim.selftest --replay-m27` -> `PASS B5: 9/9 gates on evidence/m27_solowrap.log + evidence/m27_solowrap2.log` (rc=0, green on inv 1; console `evidence/b5_replay_m27.txt`). Model: DIR_DX (1,2,1,0,-1,-2,-1,0) / DIR_DY (-1,0,1,2,1,0,-1,-2) = the 8-entry ring read out of the image at `0x6784a0`/`0x6784c4` (`evidence/m248_region_values.txt:3`, ring-first; the centre-first `0x67850c`/`0x678990` readout at `:2` is the same ring shifted one index — checked, and all 8 pairs preserve (x+y) parity). `STEP_MP = 3` = alpha `#RULES` field 0, the scale FUN_005ac550 multiplies (`return DAT_0092a278 * moves`); `MP_PER_TURN = 6` = 2 moves. can-act = FUN_005acc00's `total - spent > 0` (admits spent 0 and 3, refuses at 6). x wraps by the width as FUN_00502c40 does (79+2 -> 1, 0-2 -> 78 on the 80-wide map); y is bounds-checked, never wrapped (y=79 + dir 3 refused). Tile view `(w/2)*y + (x>>1)` with the column in `x&1` reads the same 22 B as `sim/map.py`'s `cell_index` and as the packed 44-B record. Parity: the trace-proven start 117@(43,11) -> (45,11) == recorded; 6/6 re-stamps of other units match the replay's held positions; from the §M27 pre-state (41,11) the destinations are 2/2/1/1 steps = 6/6/3/3 MP, all within the 6-MP round. OPEN: per-terrain move cost (ASSUMED uniform 3), the bonus behind `moves = 2`, and rec118's first step (outside the trace window).

## M267-M271 (s208/s210, PASS 14/14 + 10/10) — FULL rows VERBATIM at `docs/named-archive-m332-rows.md` §rotation-2 (s311-chain1 headroom rotation #2, sha1 `fc92a881bd31`, byte-exact asserted by `scripts/m332_named_rotate2.py`); this stub governs. Pre-mutation-law registry (no MU ids); G-ids are the archive rows' own. `evidence/m267_m268_census.txt:17` (SUMMARY 14/14), `evidence/m269_m271_census.txt:120` (SUMMARY 10/10).

- M267 the `0x6725ac`/`0x6725a4` pair is ONE vtable (291 slots, entry points 8 B apart, code run ending `0x672a38`) shared by 1 ctor (FUN_00469650) + 4 destructors (FUN_00421950, FUN_00518980, FUN_0059bec0, FUN_0059c1e0) of 4 variants of the virtual base at `[desc+4]`; 5 pair stores each side; 0 address-taken dwords for any installer -> direct call, not a vmethod; the pair is the vptr pair of a VIRTUAL BASE: `[vptr-4] = [desc+4] - 0x21a6c`, recomputed by all 5 installers within 14 insns.
- M268 element ctor `0x62514b` / dtor `0x62516c` write the same 2 POD stores {dword0 = 3, dword1 = 0}, no vptr, no callee; 4 at `+0xc` + 196 at `+0x98c` + 1 at `+0x1db0c` = 201 x 608 = **122,208 B** ending `+0x1dd6c` (corrects the 200 x 608 figure); all 21 `0x260` immediates in .text are iterator args or their EH unwind records, ZERO arithmetic uses 0x260; the 94 folded displacements with `(d-0xc) % 608 == 0` occur in NO function that loads a view pointer from `DAT_007cdecc`; the per-view save routine FUN_00596620 touches only `+0x1dd70..+0x1dda0` (the block is never saved).
- M269 the `[vptr-4] = [desc+4] - K` delta is an IMAGE-WIDE mechanism: a 3-level symbolic shadow accepts a store only at `field + [desc+4] - 4` -> 41 delta stores / 31 functions / 8 K; the 5 K=`0x21a6c` functions are EXACTLY M267's 5 installers (two independent detectors agree, G1/G2); plus 177 vptr installs through a vbptr of 33 rdata tables and 9 primary/secondary pairs 8 B apart with identical install counts — M267's pair is the rule (G4-G6).
- M271 32 of the 247 distinct rdata immediates stored through a register are vbtable descriptors (`dword[0]` and `dword[+4]` both |v| < 0x40000, neither a code pointer); their `[+4]` values are 21 virtual-base offsets and every K the delta census found is one of them; `[0x675964]=0,[+4]=0x21a6c` is installed only by FUN_00469650 and `[0x678458+4]=0x23d94` only by FUN_0050aa60, both carrying a delta store at their own K (G3/G9/G10).
- M270 the `0x678e40` class has ONE 152,856-B stack instance: `0x678e40` and its secondary `0x678e38` (+0x2444) are each stored EXACTLY once image-wide (`0x59bf1c`, `0x59bf26`, both inside FUN_0059bec0) — never heap-allocated; slot 0 of each is its deleting-dtor wrapper (`0x59c380`/`0x59c3b0`); layout `+0` the `0x5e3b80/0x5e3ced` class, `+0x2320` the `0x675964` class, `+0x247a0` M215's `0xb4c` row, virtual base at `+0x23d8c = 0x2320+0x21a6c`, size `0x25318` = the only such immediate in the image (the `_alloca_probe` at `0x59bed1`). **RETRACTS part of M267 (kept here on purpose):** FUN_0059bec0 is NOT a destructor (4 ctors run before it installs `0x678e40`; the same objects die at its tail) and its `0x67194c/0x671944` are the ROW subobject at `+0x247a0`/`+0x247a0+0x444`, never `[this+0]` — the installer of `0x67194c` at `[this+0]` is FUN_005faec0 (M215).

## M272 (s211, PASS 5/5) - `FUN_0057ecf0` does NOT run on a LOAD; the .SAV restore chain is live-proven

| fact | evidence | status |
|---|---|---|
| LOAD window (ROUND sentinel -39 -> 50 read back, counts == m104 image): 0 events at `FUN_005b2970`, its 4 call sites (0x4e1151/0x4e122b/0x57d2a0/0x57f1ec) and all 4 caller entries | `evidence/m272w9.gdblog`, `scripts/m272_acceptance.py` G4 | V |
| the .SAV opener `FUN_00597ee0` fires INSIDE the load (event prints round=-39, the live sentinel; ret 0x5992f2), then the fread wrapper `FUN_0064cc00` fires at round=50 with dest 0x927590 (8x1436 faction array), ret 0x596edb = inside `FUN_00596850` | same log, lines 52-53; conditional bp design in `scripts/m272_gen_load_watch.py` | V (M106 chain, now LIVE-proven) |
| entry bps at 0x597ee0 / 0x596850 never fire although the chain runs - entry is reached MID-BODY (or via a twin); a chain is proved by call-site RETs, not entry hits | same log (0 ENT events at both, 2 CTRL rets into their bodies) | V (instrument law) |
| boot window control: `FUN_005791c0` x7 (ret 0x579eaf) - bps live at process start; GEN 0 at boot is NOT a control (attach ~3.5 s post-launch) | same log, STARTUP window | V |
| new-game generation and save-load are DISJOINT paths: a LOAD never regenerates the world | G4 + M255 (57ecf0 = new-game caller) | V |

## B6 (s212, PASS 6/6) - `sim/headless.py`: the headless run; R1 DONE

| fact | evidence | status |
|---|---|---|
| `python3 -m sim.headless --sav programs/saves/m54b_clean.SAV --map programs/maps/planet.MP --turns 10 --dump sim_state.json` exits 0 and prints PASS B6 | `evidence/b6_headless.txt:1-5` (the direct run) | V (runnable) |
| year 2150 -> 2160 = exactly +1/press per the B3 engine (year_after = order[-1] = 7); ends (cur,tf) = (3,0) = the human phase | same, gates 1-2 | V (parity vs B3's recorded model) |
| the dump is DETERMINISTIC: two runs -> identical bytes, sha256 2efbc782e2075a26... , 8,455 B | `python3 -m sim.selftest --b6 <sav> <map> --turns 10` -> `PASS B6: 6/6 gates`, `evidence/b6_headless.txt:6-12` | V |
| economy runs for the 7 base-owning factions every round with the B4 floor (energy >= 0); initial faction energy = 0 is ASSUMED (no pinned .SAV read) and listed in the dump's `assumed` array | dump `schema smac-sim-state/1` | ASSUMED (declared) |
| units re-charge 6 MP per round (0x51f730 REFRESH, M37) and never move - R1 has no AI; declared in `assumed` | same | ASSUMED (declared) |

## M273 (s213, PASS 7/7) - the row stride 188 is a FIXED 94-slot capacity; no spill on the live map

| fact | evidence | status |
|---|---|---|
| live region count DAT_0092ada4 = 91, stable pre AND post the window, == save-derived ((64+4)/5+1)/2×13 = 91; ad9c=ada0=13 | `evidence/m273w3_proc.json` (written by the live run), `evidence/m273w3.gdblog` window, gate G1 | V (live) |
| 188 = 2×94 slots is a FIXED capacity: 8380/188 = 44.47 NOT integral (8380 mod 188 = 108) - the per-faction row is NOT derived from the faction block stride; the live count fits its row with 6 B slack, so the M256 "regions 94..127 spill" is UNREACHABLE on the 64×64 map | gate G2 + G6 (below) | V |
| scaled-indexing identity: 7/7 SCALED events at 0x5584b2 have 2×edi == the loop slot [ebp-0x10] (=1) - the scaled form's index register IS the region counter | `evidence/m273w3.gdblog`, gate G5 | V (live) |
| the UNSCALED row register is a per-faction TABLE CURSOR (LIVE): row mod 8380 = 2 for all 7 events, every successive delta a whole faction stride 8380, walking with cp=4,5,6,7,...; **M275 (s215) PROVED this contradicts the static fold** (row = 2·region + 130·arg, and 8380 mod 130 = 60 ≠ 0) -> the value at the read site is NOT produced by the fold as written; the writer is an unmodeled ALIAS/other-leg (OPEN, hw-watchpoint pick) | gate G6 + `scripts/m275_rowslot_defuse.py` G4/G7 | V (live), CONTRADICTED (static chain) |
| the full region loop was NOT exercised in the window: observed s10 stays 1 while cp walks phases (7+7 events, balanced); depth per phase OPEN (new pick) | gate G4 + info line | OPEN (recorded) |
| acceptance is OFFLINE over the recorded window: `python3 scripts/m273_rowstride_watch.py --replay evidence/m273w3.gdblog` -> `ACCEPTANCE M273 PASS 7/7` (`evidence/m273_acceptance.txt`); the /proc facts ship in `evidence/m273w3_proc.json` | same | V |

## M274 (s214, PASS 6/6) - the region loop is NEVER clamped to the 94-slot row; the spill lands in the sibling verdict array

| fact | evidence | status |
|---|---|---|
| the region loop has exactly ONE bound: `cmp ecx,0x80` at 0x558b1c (constant 128); ZERO capacity clamps (94/93/91) in the 4,235-insn body of FUN_00556690 | `scripts/m274_rowcap_census.py` G1, `evidence/m274_census.txt` | V (bytes) |
| **M277 RETRACTS (s218)** the SCALED reads of regions 94..127 land inside the SIBLING verdict array at 0x94eba8 - the max byte touched is +255 and the sibling starts at +256, so they read 68 B of rows 94..127 INSIDE the row's own cell. The loop-bound half (ONE bound 0x80, zero capacity clamps) and the verdict-array store census STAND. See `## M277` G3/G4 | G2 | SUPERSEDED by M277 |
| the row slot [ebp-0x18] read by the UNSCALED site has **15 stores** in the body (the fold 0x558038 among them) - single-writer attribution is UNSOUND; M273's whole-8380 cursor comes from one of the other writers (def-use pick) | G3 | V (bytes), OPEN (which writer) |
| a region whose verdict byte is nonzero gets `mov BYTE [ebx+rcx+0x94eda8],0x8` (0x557fdf) then `jmp 0x558b18` (0x557fe7) - it NEVER reaches either read site: this, not a shallow loop, explains M273's sparse events | G4 | V (bytes) |
| the verdict array 0x94eda8 has exactly 5 store sites: 0x557fdf=0x8 (skip), 0x558516=dl (7-or-8), 0x558549=0x0, 0x55855e=0x2, 0x55856b=0x7 | G5 | V (bytes) |
| the fold, RE-DERIVED from bytes: `add eax,edi; lea eax,[edi+eax*2]; shl 4; sub eax,edi; lea esi,[ecx+eax*2]; shl esi,1` = **esi = 2{m}region + 188{m}(E+edi)**. **M276 CORRECTION (s217): the 188 multiplier is WRONG** - evaluated SYMBOLICALLY end-to-end the same chain is `esi = 2{m}region + 8380{m}arg`; the 188 reading sliced it at `add eax,edi`. The 8380 mod 188 = 108 arithmetic is true but MOOT: 8380 IS the coefficient | G6 | SUPERSEDED by M276 |
| method law (s214): an objdump `--start-address` that lands INSIDE an instruction silently misaligns the whole window (invents `.byte` lines, breaks reachability) - read windows from the aligned scratch/m574/text.txt cache or from the function ENTRY | this file's first run | V (instrument) |

## M275 (s215, PASS 8/8) - the row slot's only reaching def at the read site IS the fold - and the live cursor CONTRADICTS the fold's arithmetic

| fact | evidence | status |
|---|---|---|
| CFG of FUN_00556690 (4,235 insns) is sound: ZERO indirect jumps - reaching-defs is decidable statically | `scripts/m275_rowslot_defuse.py` G1, `evidence/m275_defuse.txt` | V (bytes) |
| the slot [ebp-0x18]: 15 direct defs, 19 loads; at the read-site feeder load 0x55844b the **reaching-def set = {0x558038}** (the fold) - M274's "15 writers, unattributable" is narrowed to ONE on the CFG | G2-G4 | V (bytes) |
| the fold's multiplier: `mov eax,edi; shl 6; add eax,edi` = 65{m}edi; `lea eax,[edi+eax*2]` = 131{m}edi; `shl 4; sub eax,edi` = **2095{m}edi**; `lea esi,[ecx+eax*2]; shl esi,1` = **esi = 2{m}ecx + 8380{m}edi**. **M276 CORRECTION (s217)**: this gate's `130{m}edi` was a hand-written expression at the chain's MIDPOINT (65{m}2) that never evaluated the tail; edi = the FUNCTION ARGUMENT stands | G6-G7 | SUPERSEDED by M276 G3 |
| ~~THE FINDING~~ -> **M276 CORRECTION (s217): no contradiction.** The corrected form `slot = 2{m}region + 8380{m}arg` fits M273's recorded live rows **7/7** with the multiplier == `cur_player` (cp 1..7), and neither 130 nor 188 divides a single one of them. The s215 verdict was this instrument's arithmetic, not the game's | `scripts/m276_fold_stride.py` G3/G6/G7 + `evidence/m273w3.gdblog` | V (bytes + live log), CORRECTS M275 |
| alias census: 14 dword stores through a block base [reg+0x94dXXX] exist in the body; ZERO at the slot's absolute faces (0x94d6e8 / 0x92dcd0) - the missing writer is not a displacement form this class sees | G8 | V (bytes) |
| resolution pick (queued): hw-watchpoint the FRAME SLOT while the auto-manager runs | - | **CLOSED UNRUNNED by M276** (a decode slip, not a missing writer - no box time needed) |

## B7 (s216, PASS 6/6) - `sim/movesim.py`: the move slice - save-loaded units walk the recorded M27 gesture

| fact | evidence | status |
|---|---|---|
| `python3 -m sim.movesim --sav programs/saves/m54b_clean.SAV --map programs/maps/planet.MP --turns 5 --dump sim_move_state.json` exits 0 | `evidence/b7_moveslice.txt:1-6` (the inner run via selftest) | V (runnable) |
| 67 units built from the .SAV's own record array; 5 rounds x 3 east-presses each: **670 accepted / 335 refused** - every unit accepted exactly 2 (6 MP / 3 MP) then refused (FUN_005acc00 total-spent>0) with spent == 3*accepted | `evidence/b7_moveslice.txt:3-4` | V (parity vs the M27 economy) |
| every accepted press moved by the trace's ring delta (+2,0), x wrapped by the **map file's** width (80) — MODULUS CORRECTED by B25 (row split at s295, #319 review f.2 — these are TWO MEASUREMENTS OF DIFFERENT RUNS, not one): **(a) B7's own run, in memory** — wrapped by 80, **10 of 67** final tiles end outside this save's own 64x64 grid (4 of 67 at B7's accepted `--turns 5`); **(b) B25's `mpwidth` rival, composed THROUGH the writer** — 37 records written outside the container, 27 returning as a later read, that parse's `found_units` 67 -> 4. B25 never re-parses B7's own final state, so (a) carries no parser-acceptance claim and (b) is not B7's run. The (+2,0) delta and the 2-accept/1-refuse budget stand | `evidence/b7_moveslice.txt:3` (its own tiles); `evidence/b25_selftest.txt:38` (a: table F) and `:52`, `:64` (b: table I + G5, the rival's parse) | V (delta/budget; (a) and (b) each measured); **retracted modulus** |
| year 2150 -> 2155 == +1/press (B3), ends (cur,tf)=(3,0); economy identical to B6's per-faction round | `evidence/b7_moveslice.txt:1-2,5` | V |
| deterministic: two runs -> byte-identical 67,790-B dump, sha256 3b62847494b252ad... | `evidence/b7_moveslice.txt:5` (`python3 -m sim.selftest --b7 ...` -> `PASS B7: 6/6 gates`) | V |
| declared ASSUMED in the dump `smac-sim-move/1`: positions come from the save (load-restore not modeled - M106 kernel write); the gesture is applied to EVERY unit (the trace's 117-120 live in a different save); uniform 3 MP cost | dump `assumed` | ASSUMED (declared) |

## M277 (s218, PASS 6/6) - the scaled read is the permanent block-0 view; M274 G2's spill landing is arithmetically dead — FULL rows VERBATIM at `docs/named-archive-m337-rows.md:8` (§rotation-1 marker at `:7`, s318-chain1 headroom rotation, sha1 `653c93cda817` — the region is bounded by its own terminator line, its line number AND the full digest re-asserted by `scripts/m337_named_rotate.py --verify`); this stub governs. Every row is V; the M278 refinement (the player-index-0 real row) is archived with them.
## M278 (s219, PASS 7/7) - block 0 is the player-index-0 real row AND the unowned fallback; no neutral/player slot

| fact | evidence | status |
|---|---|---|
| writer1 block index (inc 0x51df61, FUN_0051dcb0): ebx = BYTE[0x95da14+304*i], i returned by FUN_004e37f0 (base-table walk: `mov ebx,0x95da14`, `add ebx,0x130`, count ds:0x985af4, distance global ds:0x8f0d34, returns the record index) = base+4 = **owner player index** (M43 identity, 167/167 live); ebx-writer census up to the store = exactly 6 (3 sentinel `or ebx,-1`, zero-extend `xor`, owner-byte load, clamp `xor`) | `scripts/m278_block0_semantics.py` G2-G3, `evidence/m278_block0.txt` | V (bytes) |
| no qualifying base -> ebx=-1 and the clamp `xor ebx,ebx` (0x51df24) lands it in BLOCK 0 immediately before the fold; the only ebx-conditional branches in the function re-enter the clamp/fold (guard-attributed census), none skips the store at ebx==0 | G2, G6 | V (bytes) |
| writer2 block index (add -10 0x564ab1, FUN_0055f650 AI hub): esi=[ebp-0xc] with ONE store (0x55f71d) = BYTE[52*arg+0x933286] = the acting unit's **owner** (unit array 0x933278, owner @+14), `and eax,0xff`; entry cross-checks it vs ds:0x91b5b4 (current player) | G4 | V (bytes) |
| domain: the zero-init sweep 0x94eca8->0x95f288 steps 0x20bc exactly 8 times and the per-block min/max loop walks esi 0..7 - the row family is EXACTLY 8 player-indexed blocks (fold stride 8380 = the step); no ninth neutral block, no +1 bias; the human is not block 0 by definition (M43: human cur=3; player 0 = destroyed-but-visited faction owning 199 tiles; "no separate faction-ID namespace") | G5-G6 + M43 recorded live | V (bytes), V (recorded) |

ANSWER (s218 pick (a)): block 0 = player/faction-index-0's REAL row, DOUBLED as the
unowned-verdict fallback via writer1's clamp - not a dedicated neutral column, not a player slot.

Acceptance: `python3 scripts/m278_block0_semantics.py` -> `SUMMARY M278: 7/7 gates PASS`; zero box time.

## M279 (s221, PASS 7/7) - the row-family layout: e8a8 is the same fold row as eaa8, byte arrays index block*8380+region, e9a8 is read-only

| fact | evidence | status |
|---|---|---|
| e8a8's ONLY writer 0x51df3d (FUN_0051dcb0) is reached through the SAME fold chain as the eaa8 store: eax = 8380*b + 2*s at both stores; eax has 0 intervening writers between them | `scripts/m279_row_family_layout.py` G1, `evidence/m279_row_family.txt` | V (bytes) |
| the three writer1 stores are a NESTED counter family: e8a8 UNCONDITIONAL (every walked tile), eaa8 behind {cl&0x18==0}+{[edi+5]&0xc0<0x80}+{[edi+8]&0x20==0}, eba8 behind those PLUS {ch&0x10} - 4 branches 0x51df49/59/5f/6e, all to 0x51df77 | G2 | V (bytes) |
| e8a8's ONLY reader 0x45c088 (FUN_0045a920): `imul eax,eax,0x20bc` then WORD read at [eax+ecx*2+0x94e8a8] = 8380*[ebp-0x34] + 2*[ebp-0x64] - the per-block fold form; rival "block-0-only" refuted (no 8380 term there) | G3 | V (bytes) |
| the FUN_00556690 ENTRY fold (0x556699-0x5566bc) evaluates to edx = 8380*arg stored at [ebp-0xc]; the BYTE arrays e5a8/e628/eca8/ed28/eda8 index [ebp-0xc] + region*1 = block*8380 + region, NOT the 2*region word form | G4 | V (bytes) |
| image-wide census: 13 bases 0x94e4a8..0x94ee28, gaps all in {0x100 (WORD cell), 0x80 (BYTE cell)}; 7 pure-WORD (e4a8,e6a8,e8a8,e9a8,eaa8,eba8,ee28), 5 pure-BYTE (e5a8,e628,eca8,ed28,eda8); e7a8 mixed 14B/13W = WORD with byte sub-accesses (M256 stands) | G5 | V (bytes) |
| e9a8: 2 sites, ZERO writers, both readers; readers DO ride the block fold - 0x568038 chain WITH seeds (edi=[ebp-0xc] OWNER, 65*edi opener @0x568021-29) = 8380*block+2*region, same at 0x5a9fd5 (block=arg, region=loop counter); G6's "(30,64,0)" was a mid-chain WINDOW ARTIFACT, RETRACTED by M280 | G6 (corrected), M280 | V (bytes) |

ANSWER (s220 pick (b)): 0x94e8a8 is the same per-block WORD row as 0x94eaa8 -
the writer1 fold feeds both (e8a8 unconditionally, eaa8/eba8 gated), and its
only reader also carries the 8380 block stride. The family's WORD rows take the
fold form 8380*block + 2*region; the BYTE rows take block*8380 + region.

Acceptance: `python3 scripts/m279_row_family_layout.py` -> `SUMMARY M279: 7/7 gates PASS`; zero box time.

## M281 (s224, PASS 7/7) - NO region id >=128 exists: the generator bands cap ids at 0x7f, so the 0x80 loops cover the whole id space; the "338" is the coarse-map CELL count, never an id bound
Who reads region ids >=128 on 128x128 maps (pick (c))? NOBODY - the region generator FUN_0058d390
(shard_015.c) assigns land ids 1..0x3e and water ids 0x41..0x7e with overflow relocation to the
slot uVar12+1 = 0x3f/0x7f when a band fills, so the largest assignable id is 0x7f=127. The loops
`cmp edi,0x80` @0x556737 and `cmp ecx,0x80` @0x558b1c (both FUN_00556690) therefore cover the whole
id space on every map size; M251's "128 entries = the whole id space" STANDS. The 338 is the coarse
region map's length ((W+4)/5+1)/2*(H+4)/5 = cell count (accessors FUN_00582340/2360 index
(x>>1)+(Rw>>1)*y); its holder DAT_0092ada4 has exactly 4 refs - alloc-expr, alloc-arg, file-write,
file-read (shard_014) - and the image has no cmp-vs-0x152, no *0x152 scale, no cmp-vs-DAT_0092ada4.
The per-region table DAT_00989ce0 save section is 3584 B at stride 0x1c = exactly 128 rows. Tile
record+3 labels max 0x7f (planet.MP), 0x48 (planetx), 0x46 (saves); zero labels >=0x80 in any
shipped map/save. | V (shard body + disasm cache + file census) | scripts/m281_region_id_cap.py
-> SUMMARY M281: 7/7 gates PASS (evidence/m281_region_id_cap.txt); s200 M250/M251 literature

## M280 (s222, PASS 7/7) - the e9a8 readers ride the block fold; M279 G6's "(30,64,0)" was a mid-chain window artifact

| fact | evidence | status |
|---|---|---|
| e9a8 read-only stands: exactly 2 sites (0x568038, 0x5a9fd5), both READS, zero writer stores image-wide | `scripts/m280_e9a8_fold.py` G1 | V (bytes) |
| reader 0x568038 (FUN_0055f650, AI hub) full chain WITH seeds: [ebp-0xc] = OWNER byte (sole writer 0x55f71d, BYTE[52*edi+0x933286] = unit+14 owner, M278); mov edx,edi; shl edx,6; add edx,edi = 65*edi; lea ecx,[edi+edx*2] = 131*edi; shl 4 = 2096*edi; sub = 2095*edi; lea edx,[eax+ecx*2] = eax + 4190*edi; load [edx*2+0x94e9a8] -> byte index 8380*block + 2*region - THE WORD fold | G2 | V (bytes) |
| reader 0x5a9fd5 (FUN_005a90a0) same: edi = [ebp+0xc] (arg), edx = region loop counter (mov edx,1 @0x5a9f85; inc @0x5a9fe6; back-edge @0x5a9fed); ecx = edx + 4190*edi; load -> 8380*block + 2*region | G3 | V (bytes) |
| artifact proof: M279's window [0x56802b,0x568035) with FREE atoms gives edx=(30,64,0); substituting the excluded seed edx:=65*edi gives 4190*edi = SAME 8380 stride - the "different idiom" was the truncated-window form (computed, not asserted) | G4 | V (bytes) |
| provenance: OWNER-keyed read (reader1 block index = acting unit's owner row; the M278 writers target the same owner blocks) | G5, G6 | V (bytes) |

ANSWER (s221 G6 open lead): the e9a8 "(30,64,0) different index idiom" is RETRACTED.
Both e9a8 readers evaluate to the per-block WORD fold 8380*block + 2*region; e9a8 stays
a read-only WORD row of the M256 family (no writer anywhere). The G6 anomaly was the
evaluator window opening at 0x56802B - INSIDE the chain, after mov edx,edi/shl 6/add edi
had already folded edx = 65*[ebp-0xc]; a chain-eval window must include the fold seeds.
Open lead successors: pick (c) who reads regions >=128 (loop bound 0x80 vs counts 338).

Acceptance: `python3 scripts/m280_e9a8_fold.py` -> `SUMMARY M280: 7/7 gates PASS`; zero box time.

## M276 (s217, PASS 8/8) - the fold's coefficient IS the faction stride: row slot = 2·region + 8380·arg

| fact | evidence | status |
|---|---|---|
| the fold chain 0x557ffd-0x558038 in FUN_00556690 evaluated SYMBOLICALLY (registers carry linear forms over the two atoms; the 20-insn window writes NEITHER atom): `esi = 8380·edi + 2·ecx + 0` | `scripts/m276_fold_stride.py` G1-G3, `evidence/m276_fold.txt` | V (bytes) |
| the atoms: edi's last writer before the chain = 0x557fbb `mov edi,[ebp+0x8]` (the FUNCTION ARGUMENT); ecx's = 0x557fac `mov ecx,[ebp-0x10]` (the region counter; loop bound `cmp ecx,0x80` at 0x558b1c) | G4 | V (bytes) |
| 8380 = 2095 dwords x 4 = the per-faction block stride `docs/field-atlas-faction.md` already records, so the auto-manager indexes these arrays BY FACTION BLOCK (`[esi+0x94e4a8]` = base + 8380·arg + 2·region): the row riding the faction stride is the DESIGN, not an anomaly | G5 | V |
| LIVE FIT 7/7 over M273's recorded log, no box time: every slot value == 2*s10 + 8380·cp with cp == `cur_player`; successive deltas whole 8380 strides (-50280 = -6·8380 at the round-52->53 wrap) | G6, `evidence/m273w3.gdblog` | V (live log, offline) |
| DISCRIMINATOR: the rival published coefficients fit **0/7** each (130 = M275 G6, 188 = M274 G6) - the fit above is not a shape every model shares | G7 | V |
| ROOT CAUSE + instrument fix: `m275_rowslot_defuse.py` G6 asserted `2*(64+1)==130`, a hand-written expression at the chain's midpoint; it now imports this evaluator, asserts (8380,2,0) and re-runs **8/8** with G7/G8 carrying the correction | `scripts/m275_rowslot_defuse.py` (re-run in `evidence/m276_fold.txt`) | V (instrument) |
| NEW LEAD from the same window: the SCALED site 0x5584aa indexes 0x94eaa8 by `edi*2` with **no** faction term while the UNSCALED 0x558452 indexes the same base by the fold value **with** 8380·arg - the two read sites do not address one row, and M274's "regions 94..127 spill into the sibling verdict array 0x94eba8" claim rides on which row each owns (static pick) | `evidence/m276_fold.txt` window | OPEN (observed) |
| METHOD LAW -> skill `references/instrument-laws.md`: EVALUATE a multiplier chain, never slice it | this file | V (method) |

Acceptance: `python3 scripts/m276_fold_stride.py` -> `ACCEPTANCE M276 PASS 8/8`; zero box time.

## B8 (s220, PASS 10/10) - `sim/savewriter.py`: the save-WRITE leg - a .SAV recomposed from the state model
- Identity round-trip: an unmutated `build_image(m54b_clean.SAV)` == the original 242,539 B
  byte-for-byte; `scripts/decode_save.py --sections --anchors` prints the identical table for both.
- MODELED bytes (composed from the model, never lifted): version word, n_units/n_bases,
  year@84 (0x985B00), cur_player@800 (0x985DCC), turn_flags@60 bit 1 (0x985AE8; remaining bits
  pass-through), own player@808 (DAT_0091b5b4), map dims @79,372, each unit record's x/y.
  PASS-THROUGH (declared): block A/B, small table, 16,000 section, middles 3,584+26,624+4,096,
  grid, coarse region map, tail incl. the trailer, un-modeled record bytes.
- Mutation fit: 5 engine presses -> written year 2150->2155 re-parses; diff confined to modeled
  spans (1 B); move x->x+2 lands exactly in record 0's x-bytes (222,783). Rivals fail the SAME
  fit: the pure re-emitter (lift_all) passes identity but carries the OLD year; UNIT_LEN+4 fails
  identity (242,807 B). Gate-shape lesson: cross-file map-dims equality is a false premise
  (m54b_clean is a 64x64 save; planet.MP is 80x80) - the identity gate arbitrates dims.
- Command: `python3 -m sim.selftest --b8 programs/saves/m54b_clean.SAV programs/maps/planet.MP
  --turns 5` -> `PASS B8: 10/10 gates` (`evidence/b8_savewrite.txt`).

## B9 (s223, BUILD, golden-trace pairing - R3's first piece) 7/7
- The golden trace evidence/trace_m54b40b_20261024_212833.jsonl is the ORIGINAL terran.exe on the SAME
  save the sim loads (m54b_clean.SAV, 2150, our 3): 40 presses, one row per turn, state_before/after of
  (year, cur_player, turn_flags, n_bases). sim/parity.py presses the B3 engine that many turns and pairs
  every recorded snapshot as an ordered subsequence of the emission (m30 law: recorded rows may not be
  skipped, model rows may be extra). 41/41 snapshots covered, 0 missing; before(0)==save start,
  before(t)==after(t-1); year_before==2150+turn all 40.
- RIVALS: swapped order and year_after=0 each miss the (2190,7,2) witness (recorded turn 39: year fired
  while cur is still 7) - one snapshot pins both the walk order and the year edge.
- FRONTIER: n_bases model const 18 vs recorded 18->26 (delta +8) - the sim has no AI base-founder; the
  delta is the finding (census pick), not a gate input.
- Command: `python3 -m sim.selftest --b9 programs/saves/m54b_clean.SAV` -> `PASS B9: 7/7 gates`
  (`evidence/b9_golden_parity.txt`); `python3 -m sim.parity` CLI exit 0.

## M282 (s225, 7/7 static) - AI bases are founded by the SAME function as the player's; FUN_004e47d0 is the only live base-array creator
- BASE ARRAY = DAT_0095da10, record stride 0x130 (304 B, = the .SAV 304-B stride), count
  DAT_00985af4, cap 0x200 (512 slots). FOUNDER = FUN_004e47d0(faction,x,y): guard
  `count < 0x200`, `count = count + 1` @0x4e484a, writes new record at
  &DAT_0095da10 + old*0x130 (x short +0, y +2, faction bytes +4/+5), faction base counter
  DAT_0094e488[faction*0x82f] += 1 (0x82f*4 = 0x20bc = faction-record stride, M280).
- CALLERS (exactly 3): FUN_004cca50 (LIVE: player 'b' hotkey case 0x62 -> FUN_004d1280;
  action dispatcher FUN_0052bce0 case 0x4408; AI hub FUN_0055f650), FUN_0059ce10 (new-game
  placement, sole caller FUN_005a0fa0), FUN_0059ec90 (faction-create, via FUN_005a0aa0
  called by AI mover FUN_00585720 / step exec FUN_00502cd0 / energy FUN_005208f0).
- COUNT WRITERS = 12 sites / 11 funcs: +1 idiom ONLY in the founder (0x4e484a) and the
  load-time scenario-table rebuild FUN_0059b830 (0x59b842/0x59b8c3); -1 ONLY 0x4e515d
  (FUN_004e4e10 destroy+compact, moves LAST record into freed slot = m46e reorder); all
  other sites store 0 (0x52283f prelude `xor eax,eax` verified from exe bytes).
- B9 FRONTIER EXPLAINED: sim has no founder and no case-0x4408 leg -> n_bases stays const
  at the save's 18 while the real game grows to 26. Models replay TURN-COMPLETE presses
  only; a colony-pod founding leg does not exist in B3.
- ACCEPTANCE: `python3 scripts/m282_base_founder.py` -> SUMMARY M282: 7/7 gates PASS
  (evidence/m282_base_founder.txt).
## M283 (s227, PASS 17/17) - decode_save --sections walks 64x64 saves; the coarse-region-map length is dims-derived, not a hardcoded 80x80 128
- The MAP branch hardcoded the coarse region map at 128 B. That map is
  ((W+4)/5+1)/2 * (H+4)/5 bytes (FUN_00582000, shard_014.c:27263-27265; same formula as
  sim/save.py region_len): 128 for 80x80, 91 for 64x64, 338 for 128x128. With 128 hardcoded,
  every 64x64 save mis-read the count-prefixed section 37 B early and --sections died with
  "no 52/304 split of a 0-byte region" (rc=1). walk() now reads W,H from the map header
  struct and computes the length; the section table sums to the file byte on all 17 repo
  saves (all 64x64) and the count u32 sits at 188,299 on all of them (sim/save.py predicted).
- Acceptance: `python3 scripts/m283_sections_64x64.py` -> 17/17 gates
  (`evidence/m283_sections_64x64.txt`). B10's gate that encoded the OLD failure ("rc == rc;
  --sections fails on both") was updated to require rc 0 == rc 0 plus the grown image showing
  exactly one more 304-B record (67x52+19x304 vs 67x52+18x304); B8/B9/B10 regressions green.
## M284
- **LIVE HALF INSTRUMENT-INVALID (s240/M293):** the SITE guard
  `if $reg >= 0x1000000` excluded every image-range vtable (the five family
  vtables 0x67164c/0x6717cc/0x6728c0/0x675cc4/0x6776c8 are all < 0x1000000),
  so a real family dispatch printed NOTHING: the live 0-fired rows here are
  instrument-silence, RETRACTED as evidence (static claims stand; guard now
  >= 0x400000; a re-armed census is an open lead).

M284 (s228, ANALYSE, MEASURED-NEGATIVE static 4/4): WHO dispatches the dialog family's +0x4c
(FUN_005f6aa3, 5 vtables 0x67164c/0x6717cc/0x6728c0/0x675cc4/0x6776c8, 466 installs, 0 direct
calls - M214).  The 12 image-wide `call [reg+0x4c]` sites are the EXHAUSTIVE dispatch-form set:
whole-image load-then-call census = 0 pairs, direct = 0 (scripts/m284_dialog_dispatch.py
--static, evidence/m284_dialog_dispatch.txt).  LIVE: 3 real clicks on the m54b_clean base
display (wndproc 0x5d0c33 WM_LBUTTONDOWN control fired 3x) dispatched +0x4c of NONE of the 12
sites, FUN_005f6aa3 never entered, modal pump 0x5f1394 never ran - the base display is a CPane
screen, not a Script.txt dialog class; the family dispatcher must sit on the Script.txt
chooser/menu path (untestable in this save: empty queue opens no chooser).


## M285 (s229, MEASURED-NEGATIVE w/ falsifier, static 5/5) - the REAL Script.txt production chooser is class 0x672298 (NOT family) and its clicks dispatch +0x4c through none of the 12 sites; the family +0x4c dispatcher lives on other dialogs (OK/CANCEL 0x67164c x7 live, menus, REALLYQUIT)
- **LIVE HALF INSTRUMENT-INVALID (s240/M293):** the SITE guard
  `if $reg >= 0x1000000` excluded every image-range vtable (the five family
  vtables 0x67164c/0x6717cc/0x6728c0/0x675cc4/0x6776c8 are all < 0x1000000),
  so a real family dispatch printed NOTHING: the live 0-fired rows here are
  instrument-silence, RETRACTED as evidence (static claims stand; guard now
  >= 0x400000; a re-armed census is an open lead).

- evidence/m285_chooser_dispatch.txt; scripts/m285_chooser_dispatch.py (--static 5/5, --live STATE 4).
- New settled fact: the production item chooser's class vptr 0x672298 (M53g) has
  +0x4c = 0x404ed0 (return-0 stub), +0xa8 = 0x496950 (the M53g bar switch) - it is a
  distinct dialog class, NOT one of the 5 family vtables, so its bar/cell clicks cannot
  dispatch the family +0x4c by construction.
- Live: chooser opened for real (INSERT landed item 193 at minerals 0/credit 0), the
  click-time dialog object was 0x6a9e9c with vptr 0x672298, family vptr occurrences
  live (0x67164c x7), yet 0/12 sites fired, FUN_005f6aa3 never entered, pump 0x5f1394
  never ran - with 6 wndproc-delivered clicks. STATE 4 measured-negative.
- Consequence: M284's "base display is CPane" + M285's "production chooser is 0x672298"
  push the family dispatcher to the remaining Script.txt dialog paths: the message
  OK/CANCEL dialog (FUN_005f1394's own class 0x67164c - its instances are the x7 live),
  menu panes, or the REALLYQUIT prompt.
## B11 (s230, BUILD, production-queue mechanics leg - R2's "build" slice) 13/13
- sim/queue.py: the M68-M72 queue law executable. INSERT = queue[pos]=item with pos = the
  queue widget's cursor row (shift min(9,max(pending+1,cursor))..cursor+1 up one, store at the
  ORIGINAL cursor, pending++ only when pending<9, enqueue tail parks cursor at rows+1, 0x4d00
  zeroes it). Duplicate id refused. Negative slot = the TYPE's (195->-3, 196->-6 verbatim;
  mapping rule OPEN). Head sentinel 0xffffffd9 = -39 (NOT -38). POP = ONE item, for k in
  range(pending): slots[k]=slots[k+1], pending-=1 -> queue[pending] keeps its STALE id
  (measured [2,193,192,0]->[193,192,192,0]). Affordability = the visitor's OWN edi at 0x4efa5e
  (head 193 wants 27, price_of says 18).
- PASS: python3 -m sim.selftest --b11 programs/saves/m54b_clean.SAV -> 13/13
  (evidence/b11_queue_mechanics.txt; sha256 29753b325093c6e1). Replays the game's OWN
  m69_cursor.jsonl (poked cursor 4, INSERT 0 -> [4,0], p4->5, stale 193->5, cursor 6),
  m70_cursor_events.jsonl (rowclick 3->1; insert193@1 p1 cur2; insert192@2 p2 cur3; 0x4d00->0),
  m71pop_seq/m71pop3_seq, m72gate4 (18 vs 27 BAILS x2) + m72gate5 (27 PAYS) - byte-for-byte.
- RIVALS fail the same fit: shift-left-by-K -> [193,192,0..]; price_of 18 pays (game bails).
- WRITE: queue_bytes() composes pending@0x4c + slots@0x50..0x77 into a 304-B base record;
  savewriter lift patches exactly those dwords, tail byte-exact, decode_save re-reads
  pending 1 head 988, section walk rc 0. B8/B9/B10 regressions green.
- FRONTIER (declared): the M282 G5 found-event SCHEDULING (which turns found/write) is NOT
  modeled - B11 replays recorded queue states only. OPEN: cursor-vs-pending store order on the
  write side; negative-id table stride (-v)*48 vs *16 (M70).

## M286 (s231) REALLYQUIT message dialog IS family (0x67164c) but does NOT dispatch +0x4c on clicks (static 5/5, live STATE 4 measured-negative w/ falsifier)
- **LIVE HALF INSTRUMENT-INVALID (s240/M293):** the SITE guard
  `if $reg >= 0x1000000` excluded every image-range vtable (the five family
  vtables 0x67164c/0x6717cc/0x6728c0/0x675cc4/0x6776c8 are all < 0x1000000),
  so a real family dispatch printed NOTHING: the live 0-fired rows here are
  instrument-silence, RETRACTED as evidence (static claims stand; guard now
  >= 0x400000; a re-armed census is an open lead).

- The +0x4c slot (FUN_005f6aa3) is the dialog ROW-CLICK dispatcher
  (76-B body: FUN_005e7917 row finder over 0x18-stride rows, idx/-1, then
  (**(code **)(*ecx + 0xa8))(local_c)) - so a family dialog click SHOULD
  enter one of the 12 sites with slot 0x5f6aa3.
- Live: raised REALLYQUIT (Escape on bare HUD after closing base display),
  read the dialog vptr AT the click: obj 0x014d7458 -> vptr 0x67164c FAMILY;
  clicked the safe 'oops' row + OK; pump FUN_005f1394 ran (1), wndproc
  LBUTTONDOWN 2, pane closed (DIALOG_CUR 0).  Sites 0/12, ENTRY 0.
- Conclusion: the message OK/CANCEL class (0x67164c) click path dispatches
  the row callback INLINE in the pump, NOT via the +0x4c slot.  M284+M285+
  M286 = three live paths, zero observed +0x4c dispatch.
- Evidence: evidence/m286_reallyquit_dispatch.txt; script
  scripts/m286_reallyquit_dispatch.py (--static 5/5, --live STATE 4).

## M287 (s232) in-game game MENU pane is NOT family - FOUR click paths measured, zero +0x4c dispatch (static 5/5, live STATE 4 measured-negative w/ falsifier)
- **LIVE HALF INSTRUMENT-INVALID (s240/M293):** the SITE guard
  `if $reg >= 0x1000000` excluded every image-range vtable (the five family
  vtables 0x67164c/0x6717cc/0x6728c0/0x675cc4/0x6776c8 are all < 0x1000000),
  so a real family dispatch printed NOTHING: the live 0-fired rows here are
  instrument-silence, RETRACTED as evidence (static claims stand; guard now
  >= 0x400000; a re-armed census is an open lead).

The last click-path candidate of M286: the in-game game menu (MENU button
(61,369) -> console bar -> GAME row -> 12-row popup: Switch To Simple Menus /
Preferences... / ... / Save Game / Load Game / Resign / Start New Game / Quit).
Static: the console bar is CHROME - GAME/HQ/NETWORK/.../EDIT MAP/HELP in NO
Script.txt pane (g4); the popup is the real menu.  LIVE: bar raised, GAME
clicked at (26,190) (GAME row never OCRs; NETWORK anchors y226 with 18-px
stride - geometry from two independent frames), popup OPEN (vision-verified).
FALSIFIER at the click: menu obj 0x03cbc0c8 vptr 0x0067919c NOT FAMILY (run 2
read DIALOG_CUR=0 - the pane isn't a DIALOG_CUR dialog that run).  Safe-row
click (Preferences, (172,350), vision coords; NEVER y>=548 Resign/Start/Quit)
landed but opened no new dialog; vptr scan delta all 0.  Site bps 0/12 x2,
entry 0.  STATE 4 measured-negative with the falsifier - the family +0x4c
slot (FUN_005f6aa3) fires through NONE of the 12 sites and has still NEVER
been observed entered from any live click.  Combined with M284 (base
display), M285 (chooser) and M286 (REALLYQUIT IS family but its row cb is
INLINE in the pump): +0x4c is NOT dispatched on ANY click path - the next
shape is dialog CREATE-time (FUN_00405ef0) or the Return-key path.

## M288 (s233, static 5/5, merged PR pending submit) - +0x4c CLOSED (s240: stands on STATIC evidence alone - the four live click-path legs M284-M287 are instrument-invalid); neither dialog CREATE-time nor the Return-key path dispatches the family +0x4c slot; FUN_005f6aa3 is reachable only through a live family +0x4c dispatch, and NO reachable path takes it
- FUN_005f6aa3 (the family +0x4c slot target = dialog row-click dispatcher:
  FUN_005e7917 row finder + [ecx+0xa8] row-cb): ZERO direct callers image-
  wide; its only 5 data refs are the 5 family vtables' +0x4c entries
  (FAMILY[i]+0x4c = 0x671698/0x671818/0x67290c/0x675d10/0x677714).
- CREATE-time: 466 family-vptr install sites in 72 owner functions; install-
  owner set INTERSECT site-owner set EMPTY.  The 0x67164c installer
  FUN_00405ef0 and its callees FUN_005ee350/FUN_005f6b8c contain no +0x4c
  call and no 0x5f6aa3 ref.  A vptr install never dispatches the slot.
- Return-key: WM_KEYDOWN(0x100) -> FUN_005d1576 -> vtable +0x12c (all 5
  family vtables = 0x5d629d hotkey dispatcher) -> FUN_005cf43a -> vtable
  +0x60; WM_CHAR -> FUN_005d15d5; WM_SYSKEYDOWN -> FUN_005d1601; pump
  FUN_005f1394 (INLINE row cb, M286).  NONE of the six contains a +0x4c CALL
  dispatch (M284 forms; the one data load 0x5d632d `mov eax,[edx+0x4c]`
  feeds FUN_00631070(hotkey-table+0x4c) - a hotkey binding read, not a
  dispatch).  Family +0x12c==0x5d629d all 5.
- Key-chain slots dispatch +0x12c/+0x60; the row callback lives INLINE in the
  pump (M286).  Closing the M284-M287 series: +0x4c never dispatches on any
  click, key or create path.  Acceptance: STATIC PASS 5/5 (one invocation).
## B12
COMPLETION CREATE LEG (s234, BUILD, 12/12, MERGED #240): `sim/production.py` - the
M56/M59/M61 completion law executable: GATE storage+income >= price (income add
inside the visit) -> PAY storage -= price -> CREATE a NEW 52-B unit record
APPENDED at units_off + n_units*52 (x@0 u16, y@2 u16, flag@4 u32=0, type@10 u16
= queue head, owner@14 u8 = base faction, order@17 u8 = 0, nlegs@18 u8 = 0; rest
declared unmodeled) -> POP one (B11 law, stale tail). Parity vs the ORIGINAL
game's own m56 trace (trace_m56_build_20261026_145157.jsonl): +1 (29,42,2,3,0)
at r0 only, record at idx n_units-1, storage 8+1-9=0 + queue [2,2,2,2,0] pend 0
== recorded r1; rivals (wrong tile, order 2, no income term) all fail.
savewriter.append_units= grows the array: only prefix byte [68] + the record
change; grown image re-parses n_units 68, written_sha256 259bd5ab.  Command:
`python3 -m sim.selftest --b12 <sav> <trace>`.

## M290 (s236, ANALYSE 9/9, MERGED #242) - the hub's founding DECISION: own-tile-gated dispatch, founder args = pod record coords

- Dispatch (bytes; s240 CORRECTED per M293 - the claim "NONZERO -> msg
  0x2408" is RETRACTED): hub 0x563d3c cmp [ebp-0x44],8 (settle case);
  0x563d46 test esi,esi (esi = scan's ring entry). NONZERO -> 0x563d48 jne
  0x563dfa: the DISTANT leg (esi>=9 walk order 0x62 at ring tile; 1-8 dec
  + continue) - NO founder AND NO msg. Only esi==0 (own tile) falls
  through to the SECOND gate [ebp-0xa4] (read 0x563d4e; set once at
  0x55f6d6 = (ds:0x920434 != 0) AND (owner == ds:0x91b5b4); live solo
  probe ds:0x920434=0 -> msg leg inert in solo): je 0x563d57 (flag==0) ->
  0x563d82-86 call FUN_004cca50 (ret 0x4ccbe2 = census FOUND ret);
  flag!=0 -> msg block 0x563d59-0x563d7d push 0x2408 + call FUN_00583fa0
  ("Auto-sending BUILD BASE message", s 0x691368, pod unit) + jmp 0x56c925,
  no founder. Own-tile gating + "NO channel from a scanned candidate tile
  to the founder" STAND (scripts/m290_hub_decision.py:160 real CFG gate;
  evidence/m290_hub_decision.txt:33).
- Vector (bytes): FUN_004cca50 prologue 0x4cca57-0x4cca74 folds 52*u;
  loads cl=[+14] owner, eax=s16[+10] y, edi=s16[+8] x; 0x4ccbda-dc push
  y/x/owner -> 0x4ccbdd call FUN_004e47d0.  FOUNDER GUARD = capacity only
  (DAT_00985af4 < 0x200).  => founding tile = pod tile; legality is the
  hub's scan alone.
- Fit (scripts/m290_hub_decision.py, evidence/m290_hub_decision.txt; s240
  re-run PASS 9/9 with the corrected G4):
  PASS M290: 9/9 - 7/7 sites land (cat 3-6, 44-B record view) + new;
  ledger 18+7-2=23 peak 24 = jsonl curve; B10 first-unoccupied REFUTED
  (ranks 542-1691/2146).  Trap: save 22-B column byte 0 is NOT the live
  category; use record view rec=(W/2)*y+(x>>1)*44 at grid_off.

## M289 (s235, LIVE 7/7, PASS 6/6, MERGED #241) - the recorded AI founds through the AI HUB: FUN_0055f650 -> FUN_004cca50 -> founder FUN_004e47d0; the 0x4408 action-dispatch leg and the 5a0aa0 faction-create chain complete ZERO foundings in the same window
- One silent bp per vector at the call site UNIQUE to it: hotkey 0x4d1d9c
  (FUN_004d1280), v4408 0x52e0cc (FUN_0052bce0 case 0x4408), hub 0x563d86
  (FUN_0055f650), chain 0x5a0b39 (FUN_005a0aa0 -> FUN_0059ec90), place
  0x5a123e/0x5a1277 (FUN_005a0fa0); founder entry 0x4e47d0 (ret addr on stack
  = 0x4ccbe2 via CC50 / 0x5a01fd via EC90 / 0x59d899 via 59ce10).
- RESULT (30-turn m54b_clean window, --no-orders, year 2150->2180): 7 founder
  hits, EVERY one vec=hub; fac 6x4/5/7/1 at (20,48)(63,51)(12,48)(27,19)(23,33)
  (27,29)(1,43); count 18->23 with 2 destroys, every FOUND/DESTROY printed
  count == the expected walk (late=0); 1627 control sweep rows.
- The chain (5a0aa0) was ENTERED 3x but its EC90 path completed no founding
  (bailed inside) - reachable-but-inert in this window; v4408 and the player
  hotkey: 0 entries.  M282's G5 static thesis (AI rides the 0x4408 dispatch
  leg) is REFUTED live; the founder's live caller is the hub's DIRECT call.
- SIM IMPACT: basefound.py (B10) assumed faction/coords; the m289 trace
  (evidence/trace_m289_20261110_071759.jsonl) now gives 7 REAL (fac,x,y)
  foundings to fit a hub-decision rule against.
- ACCEPTANCE: python3 scripts/m289_founder_vector.py 30 (rc 0, MEASURED) and
  the independent re-walk python3 scripts/m289_accept.py -> PASS M289: 6/6.
- BOX: m289_founder_vector.py restores yama to the PRE-toggle value (the box's
  working default is ptrace_scope=0; 1 blocks n100's own /proc/pid/mem reads).

## B13 (s237, BUILD 12/12) - the pod-driven founding-dispatch leg: sim/hubfound.py turns the M290 law executable
- `dispatch(pod_rec, target, auto_build_flag=False)` (s240-corrected legs,
  sim/hubfound.py:94): distant target -> ("distant",) - the 0x563dfa leg,
  NEVER founds AND NEVER msgs (the old "distant -> msg 0x2408" claim is
  RETRACTED per M293); own tile + flag True -> ("msg", 0x2408); own tile +
  flag False -> ("found", owner, x, y) read FROM THE POD RECORD (the live
  vector's owner+14/y+10/x+8 loads are M290's byte facts, gated in
  scripts/m290_hub_decision.py). Pods compose via B12's create_record, read
  back at the save-view fields x@0 y@2 owner@14.
- Parity = the M289 record: 7 FOUND (all ret 0x4ccbe2) + 2 DESTROY rows in
  evidence/m289_gdb_raw.log; ALL 9 pre-op ledger cnts agree with the replay;
  end 23 peak 24 == the trace_m289_20261110_071759.jsonl curve; legality in
  the 44-B record view (all 7 land cat 3, none a base tile). RIVALS: ungated
  distant dispatch invents 7 tuples, 0 in the record; B10 placeholder
  reproduces 0/7. Written image: bases_override grows the ledger +5, prefix
  diff is ONLY dword 72, tail byte-identical, re-parses n_bases 23. Destroy
  slot ASSUMED last (rows carry cnt only). The pod WALK (score law
  0x563c00-0x563d40) stays DECLARED - the next ANALYSE frontier.
- Acceptance: `python3 -m sim.selftest --b13 programs/saves/m54b_clean.SAV`
  -> PASS B13: 12/12 (`evidence/b13_hubfound.txt`).

## M291 - the hub founding SCAN law (s238, 10/10, no box)
FUN_0055f650 scan body 0x5638a9-0x563cb3: candidate ring = tables 0x67850c(dx)/
0x678990(dy), 25 dwords (.rdata): idx0 own tile, 1-8 manhattan-2 diamond, 9-24
manhattan-4, ascending. Eligibility: (byte0 top-3-bits < 3) == [ebp-0x58],
rec byte3 == [ebp-0x34], rec+9 bit 0x20 clear (+ 0x4e3c00 no-go, 0x56391d-57
sub-gates). Score FUN_0046e770 = rec byte2 high nibble (sar 4; 0 when rec+8 bit
0x1000; lazy FUN_005aff90 when 0). Selection: STRICT max (cmp esi,eax, jle
0x563cb3); ties keep the closer entry. DAT_008f0d34 = nearest-location distance
(FUN_004e3620: 9999 sentinel, 152-B list stride, max(dx,dy)-((dx+dy)/2-min+1)/2
map-wrapped); value >= 2*(8-that) bypasses gates 0x94e5a8/0x94eca8. The footing
(dist*10000)/(value+1) REFUTED: no 0x2710 in the 54,483-B body. Fit: scripts/
m291_pod_scan.py - 7/7 recorded sites self-argmax, no-owngate 6/7 (loses fac1
(27,29)), B10 placeholder 0/7, null 0.307 (p 2.6e-4).

## M292 (s239, 5/5, BOX) - the POD MOVEMENT law
Hub vector FUN_0055f650 arg1 = UNIT INDEX (negative args normalize -u-1);
52-B unit record at 0x933278+52u (x u16@+0, y u16@+2, owner byte@+14);
"own" flag = owner == ds:0x91b5b4, live value 3 = the HUMAN faction.
Exactly two callers image-wide: 0x50dd84 in FUN_0050d140 (live: 26 rows =
once per round, negative-form args) and 0x56cf12 in FUN_0056cdf0 (live:
2282 rows = per-unit). The founding dispatch at 0x563d46 keys on esi = the
M291 RING ENTRY INDEX (0-24): esi==0 not-own -> 0x563d82-86 push u, call
FUN_004cca50 (FOUND leg - founds where the pod stands); esi==0 + second
gate [ebp-0xa4] set -> push 0x2408 / call FUN_00583fa0 (MSG leg - s240:
the gate is (ds:0x920434!=0 AND owner==ds:0x91b5b4), NOT own-ness alone;
live 0x920434=0 -> msg leg INERT in solo, so "0 live rows" is structural,
not our-side-inert); 1<=esi<9 ->
dec esi at 0x563e06, continue, NO order; esi>=9 -> ring tables
0x678990[esi]/0x67850c[esi] + own tile, wrap FUN_00469010, then 0x563e3b
FUN_005560f0(u, 0x62, tile) = issue order b at the ring tile = the pod
WALK. Live 26-turn window (m54b_clean t0): FOUND=9 ALL via the hub leg
(ret 0x4ccbe2), cnt 18->27, every FOUND paired same-segment with its
HUBFOUND tile, 2 walked pods, own-flag law 29/29.
Instrument: scripts/m292_pod_movement.py.

## M293 (s240, CORRECTION, MERGED #250) - three verified Greptile P1s fixed; two registry claims retracted
- D1 hub dispatch (the M290/B13 correction above; bytes re-derived from the
  disasm cache): msg block [0x563d4e,0x563d7d] entered ONLY by the esi==0 +
  flag!=0 fallthrough - no branch in .text targets it from outside
  (scripts/m290_hub_decision.py:160, G4 = real CFG parse: branch table
  0x563d40->0x563e48, 0x563d48->0x563dfa, 0x563d57->0x563d82,
  0x563d7d->0x56c925, 0x563e04->0x563e12; [ebp-0xa4] single writer
  0x55f6d6, producer chain 0x55f6b0/0x55f6c0/0x55f6c6/0x55f6cd/0x55f6d1
  bytes asserted). The OLD G4 sliced its own address table at
  0x563d4e..0x563d81 - vacuous (the founder je-target 0x563d82 abuts the
  end). ACCEPTANCE: python3 scripts/m290_hub_decision.py
  programs/saves/m54b_clean.SAV evidence/m289_gdb_raw.log
  evidence/trace_m289_20261110_071759.jsonl -> PASS M290: 9/9
  (evidence/m290_hub_decision.txt:33). 3 runs; runs 1-2 were the
  instrument (byte transcription; in-block skip), floors never cut.
- D1b read-only /proc probe (pid 4087359, TracerPid 0): ds:0x920434=0,
  ds:0x91b5b4=3, ds:0x9208f8=0 -> the msg leg is UNREACHABLE in this solo
  save; name of 0x920434 OPEN (scenario/multiplayer gate?).
- D2 sim/hubfound.py:94 legs (distant/msg/found): ACCEPTANCE
  python3 -m sim.selftest --b13 programs/saves/m54b_clean.SAV -> PASS
  B13: 12/12 (evidence/b13_hubfound.txt:4).
- D3 guards >=0x1000000 -> >=0x400000 in m284_dialog_dispatch.py:246,
  m285_chooser_dispatch.py:185, m286_reallyquit_dispatch.py:181,
  m287_menu_dispatch.py:279; M284-M287 live claims now carry INVALID
  banners in their blocks. Static closure (0 direct callers of
  FUN_005f6aa3, create/key-path containment) UNAFFECTED.
- D4 sim/selftest.py:177 (run_save): walk() returns (rows, notes) and
  prints nothing - the old redirect+splitlines()[-1] raised IndexError
  every run (the except caught only SystemExit). ACCEPTANCE
  python3 -m sim.selftest --sav programs/saves/m54b_clean.SAV -> PASS
  B2: 7/7 (evidence/s240_b2_run.txt:2 "21 sections, 0 problems").
- Cites per AGENTS.md:50 (path:line) added to every claim touched here.

## B14 (s241, BUILD 10/10) - the hub scan + walk dispatch EXECUTABLE: sim/podscan.py
Ring tables as literals RING_DX/RING_DY (25 entries; provenance
evidence/b14_ring_table.txt, the file-image dump of .rdata 0x67850c dx /
0x678990 dy via scripts/b14_ring_dump.py; sim/ never loads the exe). Order
facts: 0=(0,0); 1-8 the m2 diamond (1,-1)(2,0)(1,1)(0,2)(-1,1)(-2,0)(-1,-1)
(0,-2); 9-24 the m4 diamond ascending, 21=(4,0) 22=(-4,0) 23=(0,4) 24=(0,-4).
scan_esi = M291 strict site-value argmax (score = rec byte2 high nibble;
eligibility cat-flag equality + byte3 owner-equality + rec+9 bit 0x20 clear +
unoccupied; ties keep the closer); a site is self-argmax iff scan_esi == 0.
dispatch_leg: esi 0 -> founder, or msg 0x2408 under msg_gate(global!=0 AND
owner==human) (s240); 1..8 continue (no order); 9..24 walk (order 0x62 at
walk_target = pod tile + ring entry, map-wrapped). The live ISS tile= field
records the target X ONLY. ACCEPTANCE: python3 -m sim.selftest --b14
programs/saves/m54b_clean.SAV -> PASS B14: 11/11 (evidence/b14_podscan.txt:23).
s241 review round (both P1s CONFIRMED by bytes, fixed): the scan keeps
best VAL [ebp-0x24]/best INDEX [ebp-0x84] with strict updates (full
argmax, no first-better shortcut); candidates are X-WRAPPED (0x469010,
call 0x5638b9) but Y BOUNDS-CHECKED (0x469060, call 0x5638d2) - Y never
wraps; the ISS tile arg is the wrapped X only. DECLARED UNMODELED: 0x94e5a8/0x94eca8 tables, the
0x4e3c00 no-go, the rec+8 bit-0x1000 zero-leg / FUN_005aff90 lazy value,
the ISS target-Y field.

## CHAIN-BUILDS (s242 overflow from NEXT_PROMPT.md - grep only; NEXT_PROMPT cites this section)

Build-rung ledger VERBATIM as it stood in s241's footing: B4 DONE (s203) 9/9, **B5 DONE (s207)** 9/9, **B6 DONE
(s212)** = R1 DONE (6/6), **B7 DONE (s216)** = R2's move leg (6/6) - commands per-id in `NAMED.md` §B4-§B7.
**B8 DONE (s220)** save-WRITE leg: `python3 -m sim.selftest --b8 <sav> <map> --turns 5` 10/10
(`evidence/b8_savewrite.txt`, `NAMED.md` §B8). **B9 DONE (s223)** golden-trace pairing:
`python3 -m sim.selftest --b9 <sav>` 7/7 (`evidence/b9_golden_parity.txt`, `NAMED.md` §B9). **B10 DONE (s226)**
18/18: `python3 -m sim.selftest --b10 <sav>` (`evidence/b10_basefound.txt`, `NAMED.md` §B10). **B11 DONE
(s230)** 13/13: `python3 -m sim.selftest --b11 <sav>` (`evidence/b11_queue_mechanics.txt`) - the M68-M72 queue
law, replayed against the game's own states. **B12 DONE (s234)** 12/12:
`python3 -m sim.selftest --b12 <sav> <trace>` (`evidence/b12_production.txt`, `NAMED.md` §B12) - completion
CREATE: gate->pay->52-B record (29,42,2,3,order0) at array end->pop vs the game's OWN m56 trace, 3 rivals miss,
grown image re-parses. **B13 DONE (s237)** 12/12: `python3 -m sim.selftest --b13 <sav>`
(`evidence/b13_hubfound.txt`, `NAMED.md` §B13) - (s240-corrections in header + NAMED). **B14 DONE (s241)**
11/11 post-Greptile: `python3 -m sim.selftest --b14 <sav>` (`evidence/b14_podscan.txt:23`) - M291 scan (full
argmax; X wraps, Y bounds-checks) + M292 esi-dispatch/walk EXECUTABLE (sim/podscan.py), ring recorded
(evidence/b14_ring_table.txt). **B1-B14 DONE.**

**B26 DONE (s299; PR #328 TRIAGE s300)** `python3 -u -m sim.selftest --b26` ->
`PASS B26: 10/10 gates`, anchor `ae43e0ab9c8cfc3d` (`evidence/b26_selftest.txt:52`, gate line
`:63`); harness `python3 -u scripts/b26_mutate.py` -> **19/19 scored + 1 declared NO-OP**
(`evidence/b26_mutate.txt:24`), `--selftest` **8/8 REJECTED**
(`evidence/b26_mutate_selftest.txt:14`), **ENTRY-POINT IDENTITY 2/2** (`evidence/b26_mutate.txt:25-30`)
- the save/load boundary rung, the container is LOADED not just written; full claims and the
THREE RETRACTIONS the review forced (smuggler-blind F1, refusal totals F3, owner offset F7) in
`NAMED.md` §B26. (MEASURED: this ledger
has carried no new row since B14 - grep `DONE (` above stops there; B15-B25's per-rung
commands live only in the per-id `## B<n>` blocks.)

## CHAIN-PICKS (s242 overflow from NEXT_PROMPT.md - grep only; NEXT_PROMPT cites this section)

Pick history VERBATIM as it stood in s241's footing: ANSWERED s227-M289, s234-B12, s236-M290, s237-B13
(own-tile-gated dispatch + SECOND gate [ebp-0xa4] - NAMED M290/M293). ANSWERED s238=M291 (10/10; ring + value
laws in NAMED.md). ANSWERED s239=M292 (5/5, 26-turn BOX; law NAMED.md): law + s240 correction in NAMED
M292/M293 (msg 0x2408 leg = own-tile + [ebp-0xa4], NOT distant; live 0x920434=0 -> msg inert). ANSWERED
s241=B14 (scan+dispatch+walk executable). NEW pick (s239, taken s242 as THE PICK): UNMODELED 0x94e5a8/0x94eca8
per-site gate tables + FUN_004e3c00 no-go (STATIC census + fit vs recorded sites; the fits passed WITHOUT
modeling them). Also open: who gates hub visits (both callers entry tests); the 0x56c6de continue-leg target;
name ds:0x920434 (msg-leg gate, =0 solo, s240 probe). STATIC PICKS (no box time): (c) ANSWERED s224=M281 (no
region id >=128; 338 = coarse-map CELL count; NAMED). s240=M293 CORRECTION (msg retraction; live censuses
INVALID, guards fixed >=0x400000 - re-arm before ANY reuse; B2 7/7). NAMED M290/M293. DIALOG +0x4c CLOSED
(M284-M288; live half INVALID s240, static stands): slot not on any click/key/create path; menu pane NOT family
(0x67919c); full shape in NAMED M288. M282 G5 CLOSED (s235 hub, s236 fit). 188-row cursor caller OPEN.
s242 = CONTEXT-HYGIENE (no pick; budget/retention work only, PR to be numbered here).

## B15 (s243, BUILD 7/7) - gate tables NAMED: site_score 0x94e5a8 / site_gate 0x94eca8; ds:0x920434 = published_window_id

| claim | evidence | conf |
|---|---|---|
| `0x94e5a8` = **site_score**: `BYTE[fac*8380 + region + 0x94e5a8]` (0x94d448 block family: base+0x1160; the M92 divisor-block view is +0x120 from 0x94e488; byte x128); 99 refs / 24 funcs / 5 stores (M94 writers 0x556721/0x556b5a); FUN_0055f650 holds 22 refs / 0 writes; the same array feeds the M91/M92 research tail and FUN_004f6030 (15 refs, uncensused) | `evidence/b15_name_disp_0x94e5a8.txt:1,3` | V |
| `0x94eca8` = **site_gate**: `BYTE[... + 0x94eca8]` (blk+0x1860); 7 refs / 4 funcs; **ZERO direct stores** - the only writer is FUN_0051dcb0: zero sweep `0x51dcd1`/`0x51dce7` + lea-copied address `0x51dfe2` -> `mov BYTE PTR [ecx],al` `0x51dff3` (trap-3: store-shape greps miss it); FUN_0051dcb0 also RMWs the 0x94e8a8/0x94eaa8/0x94eba8 word arrays and 0x989ce8/0x989cec; value source (via 0x582cc0) CLOSED by M298 (lazy-0x5aff90 value CACHE WRITE-BACK to BYTE[rec+2] high nibble) | `evidence/b15_name_disp_0x94eca8.txt:1`, `evidence/b15_gate_window.txt` (writer windows) | V (writer), OPEN (values) |
| the pod-scan PRICE GATE, executable and byte-verified (branches): skip if value <= best; ACCEPT bypass `value >= 2*(8 - nearest_dist ds:0x8f0d34)`; ACCEPT `site_score==0`; ACCEPT `[blk+0x94e488] < 2`; thr = (pod-region verdict byte==8)?1:4, thr = max(thr, site_gate); ACCEPT value>=thr; else SKIP legs `case!=8`, `BYTE[unitrec+0x11]==0x18`, `DWORD[0x989ce4+28*region] >= 6*(site_score+1)` (edx@0x563c8e = the dl stored at 0x563c3d - NOT the ring index) | `evidence/b15_gate_window.txt` (scan-gate window 0x563bf7-0x563cbf); `sim/gatetables.py`; interpreter==closed form 14,520 cases; rivals 81/146/236/2851 | V |
| gate operand def-use (FUN_0055f650 prologue): region = record-view byte 3 of the POD tile `0x55f79f/0x55f7a5`; blk = owner*8380 fold `0x55f80e`; pod-region verdict -> `[ebp-0x8c]` `0x55f811/0x55f81b`; case = type-record plan byte +42 (M127) `0x55f73a/0x55f74a`; msg flag `[ebp-0xa4]` writer `0x55f6d6` (M290/M293 stand) | `evidence/b15_gate_window.txt` (prologue windows) | V |
| `ds:0x920434` = **published_window_id** (supersedes the old netgame_flag row): 634 refs, exactly 15 stores, pcs == the M125 set (G2 asserts); solo live 0 (M293 D1b); 0x55f6b0 = the msg-leg gate | `evidence/b15_name_ds_0x920434.txt:1`, NAMED M125/M293 | V (census), INFERRED (name) |
| recorded winners: 27 events (7 m289 + 9 m292 foundings + 11 walks) all modelled: 24 accept via the recorded bypass, 3 row-dependent: m292found(22,14)v1,d3; m292walk(18,2)v7,d2; m292found(18,2)v7,d2 - the box follow-up prints their site_score/site_gate/verdict rows | `evidence/b15_gate_tables.txt` (G5) | V (law), OPEN (live rows) |
| ACCEPTANCE `python3 -m sim.selftest --b15 programs/saves/m54b_clean.SAV` -> **PASS B15: 7/7** | `evidence/b15_gate_tables.txt:1` | V |

## M294 (s244, PR #257) - pod-scan loop LIVE-VERIFIED: B15 gate law predicts every recorded dispatch from printed rows
| claim | evidence | conf |
|---|---|---|
| the 25-slot scan loop 0x5638a9-0x563cbd is ONE function with the hub vector (FUN_0055f650 size 0xD513); 7 eligibility pre-checks precede the B15 price gate and jump STRAIGHT to the 0x563cb3 tail: walk `call 0x469060==0` (0x5638dc), terrain mask vs [ebp-0x58] (0x563917), elevation band (0x563928/0x56393e), region `BYTE[tileview+3]!=[ebp-0x34]` (0x56394e - **[ebp-0x34] stays the POD region whole-loop**: gate region = pod region), occ `dh&0x20` (0x563954), no-go `call 0x4e3c00(owner,X,Y)>=0` (0x563963; B16 corrects M294's arg order - owner = BYTE[0x933286+52u] stored [ebp-0xc] at 0x55f71d, push order 0x56395d-0x563962) | scratch/m71/dis.py 0x5638a9-0x563bf7; evidence/m294_gate_rows.txt (guardfail 0) | V |
| live parity: recorded y2188+24-turn window (m54b_clean; yama-pre 0): 2129 hub-vector visits, 2321 gate-decision slots, 260 accepts - price_gate over printed GDEEP/GACC rows reproduces every accept-set, every winner (tail win field == DISP esi), every leg; 0 disagreements; census selftest 3/3 (scratch/m294_model_test.py) | evidence/m294_gate_rows.txt VERDICT PASS; raw evidence/m294_gate_rows_raw.txt | V |
| the GDEEP/GACC `x=`/`y=` fields are the Y-leg ([ebp-0x8]) and the X-leg ([ebp-0x4]) - B16 reader law, read those rows transposed (M294's own replay never read them, so its verdict is unaffected)
| tail $esi = slot/x garbage on pre-check-skip paths -> GROW.val counts ONLY where the same slot has a GDEEP/GACC row (instrument law -> skill instrument-laws) | evidence/m294_gate_rows_run1_note.txt (run-1 2129/2129, 0 direction-of-law) | V |
| FUN_0051dcb0 (sole site_gate writer): EXACTLY 11 e8-callers 0x41dc7e/0x4e145e/**0x4e4dc8 (founder vector FUN_004e47d0)**/0x4e5540/0x4f3e08/0x508b48/0x51f71e/0x543bc6/0x59b8ce/0x59dd3a/0x5b09f6; the 0x51dff3 store = max(cell@0x51dfeb, edi); edi = `BYTE[rec+2]>>4` when nonzero (0x51df85-8a, je 0x51dfac) ELSE the `call 0x5aff90` result copied at 0x51df9f - the following `call 0x582cc0` CONSUMES edi (push 0x51dfa1) and its return is DISCARDED (eax reloaded at 0x51dfac); cell addr = 0x94eca8 + 8380*ebx + [ebp-0xc] (ebx = scan idx, nonzero; the slot store 0x51dfcb = max(edi,[site*28+0x989ce8]) - the earlier 4*min value-indexed phrasing RETRACTED by M298 R3) | scripts/m294_callers.py -> evidence/m294_sitegate_callers.txt | V (sets); CLOSED by M298 (0x582cc0 = lazy-nibble cache write-back, edi survives; [ebp-0xc] = BYTE[rec+3], sole store 0x51dd57 - callers REFUTED; cell-addr phrasing fixed M298 R3) |

## B16 (s245, BUILD 7/7) - pod-scan loop HEAD PRE-CHECK CHAIN named, pinned, executable (sim/precheck.py)
| claim | evidence | conf |
|---|---|---|
| the 7 loop-head tests resolve entirely to the 44-B tile-record view (tileview = ds:0x92ae14 + 44*(ds:0x692184*Y + X>>1), 0x55f768-0x55f77e): bounds `call 0x469060` 0x5638d2 range-tests BOTH legs (ds:0x92a378 / ds:0x92a37c; X arrives pre-wrapped from 0x469010 at 0x5638b9, so only Y bites); class (byte0&0xe0)<0x60 == [ebp-0x58] 0x56390b-0x563917; byte8&0x20 needs cat<2 0x56391d-0x563928; elevation band byte5&0xc0 > 0x40 needs cat<3 0x563930-0x56393e; region byte3 == [ebp-0x34] 0x563944-0x56394e; occ byte9&0x20 0x563954; no-go `call 0x4e3c00(owner,X,Y)` >= 0 0x56395d-0x56396d (push order 0x56395d-0x563962: owner first) | evidence/b16_precheck_window.txt (250 insns, objdump -M intel from the entry 0x55f650); sim/precheck.py PINS 31/31 | V |
| [ebp-0x58] ORIGIN = ([ebp-0x40]==1) at 0x563814 where [ebp-0x40] = BYTE[0x92ae81+144*BYTE[0x98adac+52*type]] (the unit TYPE's required-class byte, 0x55f74f-0x55f765: stride 0x90 - lea*9 then shl4, Greptile #258 P2 fix s246); the `cmp ecx,eax / jne 0x563f18` at 0x563812-0x563817 gates the WHOLE scan on equality with the POD tile's own water flag [ebp-0x74] (0x55f783-0x55f79c) - THEOREM: required class == classflag(pod tile). [ebp-0x34] = BYTE[tileview(pod)+3], stored once at 0x55f7a5 (the gate region IS the pod region, M294) | evidence/b16_precheck_window.txt | V |
| LOG READER LAW: the m294 GDEEP/GACC `x=` field is *(int*)($ebp-0x8) = the Y leg and `y=` is *(int*)($ebp-0x4) = the X leg (the record formula multiplies [ebp-0x8] and >>1's [ebp-0x4]) - read those rows TRANSPOSED | sim/precheck.py G2: 1026/1026 pod recoveries consistent, 201/201 vs the DISP unit-record x/y; untransposed reading 638 and 0 | V |
| live parity over 25650 (pod,slot) tests: 0 recorded decision slots fail bounds, elev or occ; fail&skip per check bounds 110 / class 5036 / b8_bit20 9311 / elev 3304 / region 5880 / occ 389 (solo 0/0/5775/2181/185/212 - bounds and class never exclude ALONE in this window); every visit's decision rows share ONE class flag and ONE region byte (0 mixed of 1026) | evidence/b16_precheck_chain.txt (PASS B16 7/7) | V |
| DECLARED UNMODELED: the 0x4e3c00(owner,X,Y) no-go - **8482** tests pass all 6 static checks yet printed NO decision row (the missing-row population = no-go rejects UNION the value<=best skip at 0x563c11, NOT the no-go set alone - s246 Greptile P1); plus save-vs-window drift (graded save y2150, window y2188+24) = the class fail&rec 106 / region fail&rec 192 counts, all-or-nothing per visit (106 all, 0 some), so the laws hold and the stale pod-state read is the wrong side | evidence/b16_precheck_chain.txt | CLOSED s246 by M295 (see ## M295: rule NAMED + MEASURED INERT here) |

## M295 (s246) - FUN_004e3c00 = the pod-scan territory NO-GO (human-mask-gated); MEASURED INERT here

| rule | evidence | V |
|---|---|---|
| FUN_004e3c00(owner,X,Y) (B16 leg 7, called 0x563963): iv = FUN_004e3b50(owner,X,Y,&out,0); NO-GO (out >= 0) iff tile7 = (signed)BYTE[44-B tileview+7] >= 1 AND != owner AND human-mask BYTE[0x985b10] (M96; masked 0xff, 0x4e3c34) has an owner-or-tile bit AND pair-flagword bit 4 CLEAR; else -1. tileview = B16's 44-B view (movsx BYTE[+7] at 0x4e3b76). M308 bounds the "human-mask" wording: 0x985b10 is ONE byte (0 array forms) whose bit index is a RUNTIME value - at the M303 dispatch it is 1<<block/1<<row, so "per-faction" stays INFERRED | evidence/m295_nogo_window.txt (scripts/m295_nogo_window.py, 129 insns) | V |
| 0x4e3b50 = owner_of_tile_visible (tile7 < 1 -> -1; visibility = BYTE[0x985ae8] bit 0x80, else flagword bits 3+27 (immediate 0x08000008, evidence/m295_nogo_window.txt:45,:46). pair-flagword = per-faction block BASE 0x94d430 (disasm constant, 170 uses, e.g. 0x429ab9; NOT the atlas 0x94d104 phrasing - 0 disasm uses, lead to fix field-atlas-faction.md:4) + owner*8380, pair array at block+0x18 = [owner*2095+tile7]*4 at 0x94d448 (M143); bit 4 = alliance, bits 3|27 = met/seen. out = FUN_004e37f0 nearest-base sweep, writes DAT_008f0d34 = M294's dist (sentinel 9999 -> >= 0) | evidence/m295_nogo_window.txt:19:45,:46:120:122 | V |
| MEASURED `python3 scripts/m295_nogo_fit.py` -> evidence/m295_nogo_fit.txt:4-8: the full rule R4 rejects 0 in the GRADED SUBSET (owner-known 697 visits; 329 unresolvable; save y2150 vs window y2188+ - the live no-go question STAYS OPEN, Greptile #259 P1c). Rivals collide recorded slots: foreign-only 1045, +mask 124, +not-ally 119. t7 dist of the 8482: 255:2490, 4:2058, 6:1822, 5:1190, 2:872, 1:45, 3:4, 7:1; human_mask 0x8, feat 0x0 | evidence/m295_nogo_fit.txt | V |
| callers 0x5597ea, 0x563963, 0x5643e9, 0x5647a1 (last three inside FUN_0055f650) - lead | scratch/m250_text.txt | lead |


## M296 (s247, PASS 9/9, no box; Greptile r1: 4 P2s fixed - saved REPORT lines, S0 coverage pins, byte9 labels, softened tie-claim) - the value-vs-best ARGMAX leg FITTED; best_init law NAMED
| 0x563836-0x56389f (FUN_0055f650) | best-init chain: `cmp esi,8 / mov [ebp-0x24],0x0 / jne 0x5638a2` zeroes best EVERY scan; override ONLY for case-8 + `cmp BYTE[unit+17],0x18` (move-to-base order, NAMED 0x4d3770; unit +20/+28 u16 = the target BASE tile, NAMED 0x4d6fb0) + wrapped-diff gate `call 0x46e540; call 0x46e5a0; cmp eax,2; jle 0x5638a2`; then `call 0x46e770 / dec eax / mov [ebp-0x24],eax` = **value(base tile)-1**: a move-to-base pod accepts candidates >= its base's value. Accept store `mov [ebp-0x24],esi` 0x563caa | `scripts/m296_init_window.py` -> `evidence/m296_init_window.txt:1` (11 pins) | V (bytes); 1 live sighting (u=45 best=5) w/ save-stale dest - value leg live-closer OPEN |
| score 0x1000 leg | `and eax,0x1000` 0x46e792 = dword[tileview+8] bit 0x1000 = **byte9 bit4** (fixes the byte8 shorthand elsewhere): score 0 when set; 1083 in-window tests, pool-side only | `evidence/m296_argmax_fit.txt:11` | V |
| FIT (M295-inversion) | `python3 scripts/m296_argmax_fit.py` -> `evidence/m296_argmax_fit.txt:2-10` **PASS M296: 9/9**: val>best 2321/2321; best==max(init,prior accepts) 2321/2321; GROW best replay 25650/25650; case-8 leg 1/1; rivals (low 105, cat 98, full 0, b8hi 0 of 2321) and `value>=best` never observed (0 of 2321 rows has val==best; 5721 static tie candidates corroborate); bypass law 61/61 + 0 GDEEP rows at/over cap. Pool 8482: **6048 explained as val<=best skips** (5721 ties; 904 via the 0x1000 zero), 2434 = live-mutation class; static val coverage 1931/2321 (390 rows = LIVE byte2 mutation, 9 tiles w/ 2+ machine-attested vals) | `evidence/m296_argmax_fit.txt` | V (leg FITTED); the 2434 + M295 P1c share ONE closer: the live-map flag-matched census - LEAD |

## B17 (s248, BUILD 10/10) - the pod-scan DECISION CORE composed executable (sim/scanleg.py)
| claim | evidence | conf |
|---|---|---|
| the whole leg chain is ONE replay: model best_init (M296 law; save record read only on case-8 legs) -> per-slot gt.price_gate over RECORDED machine val/gate bytes -> accept store (0x563caa) moves best AND winner -> 25-slot trajectory; reproduces every m294 window row incl. the S2 incoming-best check 2321/2321 | evidence/b17_scanleg_chain.txt:1-11 | V |
| NEW parity: GROW WIN column = last accepted slot (strict argmax, ties keep the earlier) replays 25650/25650 next to best; predicted final winner == DISP esi 201/201 | b17_scanleg_chain.txt G3/G4/G6 | V |
| accept funnel from the REPLAYED best: 260/260 GACC slots; bypass 61 / value 4 / bases 192 / mult0 2 / case8open 1; 0 GDEEP at/over cap | b17_scanleg_chain.txt G5 | V |
| best_init law-vs-machine 990/1026 (the zero-leg `cmp esi,8` needs NO unit record; 362 scans name post-save units, never graded as saved state - Greptile #261 P2); m2b class 36 = 3 save-recorded (u=45 machine-5 vs save-dest -1; 2 save-invisible dests) + 33 unit-not-in-save; the u=45 value leg STAYS OPEN (live-map census) | b17_scanleg_chain.txt G2 | V chain; OPEN value leg |

## M297 (s249) - LIVE-MAP flag-matched census: residue CLOSED, no-go INERT live, u=45 DEST-MOVED; strict row law 2102/2321 = the finding
| claim | evidence | conf |
|---|---|---|
| one read-only /proc pass over the 8482-cell pool (NO gdb, M293 D1b; TracerPid 0->0; yama 0 recorded unchanged; yr 2212 cnt 30 pinned before AND after; base=dword[0x92ae14]=0x40a5cd0, 44Bx2048 recs, mult 32=W/2, bounds 64/64, identity 2100/2321): tie 7518 / lt 287 / live-static-fail 677 / no-go 0 / UNEXPLAINED 0; the 2434 = tie 2146 + lt 35 + fail 253 - residue CLOSED; END-WINDOW (addendum A5): closed up to post-grading drift only - a live tie now != a tie at the skip | scripts/s249_livecensus.py S4 + evidence/s249_live_census.txt, evidence/s249_live_map.bin, addendum A3/A5 | V |
| no-go R4 (M295 rule, live t7/flagwords 0x94d448/mask 0x8/vis 0x0, nonzero words 36/64) rejects 0/8482 pool AND 0/2321 recorded - INERT on live flags, 0 of the residue; rivals refuted live: R1 1538, R2 42, R3 42 recorded collisions; ge-argmax 7518 ties printed no row; all on the LAST-TURN flags (A5); P6 PARTIAL-MISS: R2/R3 42 fell under the predicted >=50 floors (save-side 124/119; live mask 0x8 shrinks mask-gated collisions) | evidence/s249_live_census.txt S6/S7, addendum A1-P6 | V |
| u=45 value-leg CLOSED (dest-moved): live unit-45 order+17=0x00 dest(+20/+28)=(9,47) owner 6 vs save 0x18/(19,6); live (19,6) byte2=0x5 byte9=0x10; machine init 5 stays a DECLARED input | evidence/s249_live_census.txt S5, addendum A1-P5 | V |
| S3 finding (documented FAIL, floor unweakened): strict live law 2102/2321 exact, lazy 0, misses 219 = bit4-flips 134 (117 flip-attested) + nibble 85 (84 change-attested), 201 machine-attested / 18 not; end-window snapshots grade only the last turn; bit4 flips are val-INVISIBLE (M296 S3b under-attests); s250 instrument fix: attestation = a grading event LATER on the same tile (drift_taxonomy), A0 shipped-verify 25/25, A6 amends the S8 starttime token | evidence/s249_live_census.txt S3, addendum A2/A0/A6 | V |

## M298 (s251, STATIC, zero box) - the last two FUN_0051dcb0 holes CLOSED: 0x582cc0 = lazy-nibble CACHE WRITE-BACK (edi survives); [ebp-0xc] = BYTE[rec+3] (callers EXONERATED)
| claim | evidence | conf |
|---|---|---|
| 0x582cc0 does NOT mutate edi: callee = push/pop ebp + eax/ecx/edx clobber only, zero edi/esi/ebx writes (full 19-insn body pinned) - the 0x5aff90 lazy value (edi 0x51df9f) survives into min 0x51dfc3 + max 0x51dfee-51dff3 with no reload; the discarded return is eax = rec base (lea 0x582ce6), overwritten by `mov eax,[ebp-0xc]` 0x51dfac; side-effect = BYTE[rec2+2] = (old&0x0F)\|(edi<<4), rec2 = [0x92ae14]+0x2c*([0x692184]*param_2+sar(param_1,1)) (both globals LOADED first: mov 0x582cc3/0x582cd3) - the SAME byte +2 high nibble the cached-path test 0x51df85 reads: lazy value (0x5aff90 = 525 insns) written back as a cache | evidence/s251_statics_fn51dcb0.txt A+B windows (objdump verbatim) | V |
| [ebp-0xc] has NO caller writer (M294 question REFUTED): FUN_0051dcb0 builds its own frame (0x51dcb1 mov ebp,esp; 0x51dcb3 sub esp,0x1c), is void/0-args - the 11 e8-callers cannot reach a below-ebp slot; the 386-insn body has EXACTLY ONE store: 0x51dd57 mov [ebp-0xc],ecx = zero-extended BYTE[rec+3] (xor ecx,ecx 0x51dd48; mov cl,[edi+3] 0x51dd4f), edi = record cursor (base [0x92ae14] 0x51dd1e; +0x2c tail 0x51e128, reload 0x51e133); the other 5 refs (0x51dd9f/0x51df28/0x51dfac/0x51e021/0x51e0cc) are loads; store precedes first load - no uninit read. The site/region index rides IN the record array (byte +3), per record | evidence/s251_statics_fn51dcb0.txt C windows + full-body ref grep | V |
| M294 phrasing FIXED: the 0x51dfe2 cell addr contains NO min - the slot store 0x51dfcb = max(edi,[site*28+0x989ce8]) (cmp edi,eax / jle 0x51dfc5 keeps the OLD slot when edi<=old, else mov eax,edi) on the 28B/site slot (esi = (x*8-x)<<2 = 28*[ebp-0xc], 0x51dfb1-ba); addr = 0x94eca8 + 4*(2095*ebx) + [ebp-0xc] (0x51dfd3-e0: 65x,131x,<<4,-x; 4*2095 = 8380 = M297 faction-block stride), cell byte = max(edi,old) 0x51dfeb-51dff3; ebx = scan index (xor 0x51ddf5; -1 sentinel clamped to 0 0x51df22-24) and ebx==0 SKIPS the cell store (test ebx/je 0x51dfd1) while the min store stands; ebx's walked "table" (0x51de2c-0x51df1d) = NOT a table: 243 B of code, the base_array walk + its exit block - CLOSED/REFUTED by M301 (see §M301) | evidence/s251_statics_fn51dcb0.txt D windows | V |

## B18 (s252, BUILD 10/10) - the site-gate VALUE SOURCE + MAX STORES named, pinned and executable (sim/sitegate.py)
| claim | evidence | conf |
|---|---|---|
| the FUN_0051dcb0 value feed is a 4-bit LAZY NIBBLE CACHE: `edi = BYTE[rec+2]>>4`, and the pinned `jne 0x51dfac` (0x51df8d) skips BOTH the 525-insn FUN_005aff90 call and the FUN_00582cc0 write-back on a cache hit; the write-back target rec2+2 IS the byte the pod-scan score getter 0x46e770 reads (address identity on 4096/4096 tiles; s253: the byte is graded against the INDEPENDENTLY shipped podscan Grid.rb view and the callee fold DECODES to the 44-B stride / +2 field from the pinned text) | `evidence/s251_statics_fn51dcb0.txt:4` (64 pins), `evidence/b18_sitegate.txt:1` | V |
| the cache is an OVERWRITE, not an accumulator: no cmp/test/branch anywhere in the 19-insn callee, and against the recorded vals the live nibble moves BOTH ways (182 rows below / 31 above). Sticky law over the recorded walk: 2288 cached hits / 0 zero-nibble-zero-val lazy resolutions / 1 lazy write-back / 32 adopted live mutations of 2321 rows over 101 tiles (s253: ANY zero nibble takes the lazy path, whatever the val); the replayed end-state nibble still matches the s249 dump on 86/101 tiles (the A5 drift on the 15) | `evidence/b18_sitegate.txt:3` , `:6` | V (law), MEASURED (classes) |
| the nibble-split is visible in the recorded map: of the 177 records whose byte2 HIGH nibble moved y2150->y2212, 103 kept the LOW nibble; a whole-byte store is refuted by the pinned `and dl,0xf` + `or dl,cl`; the lazy class in the snapshot is 0 (a recorded nonzero val never meets a zeroed nibble) - M297 S3's numbers reproduced by the shipped model | `evidence/b18_sitegate.txt:5` | V (bytes), corroborated (live) |
| the store index `[ebp-0xc]` = `BYTE[rec+3]` (graded rows carry {1: 2253, 9: 68}, max site under the 128-entry per-region bound, 1026/1026 visits single-site) and the cell's block index = `BYTE[rec+7]`, the record's owner byte: the -1 sentinel clamps to 0 and block 0 SKIPS the cell store (277 recorded rows) while the slot store stands - and NO record in either view carries a legitimate 0 owner, so the skip class is exactly the unowned tiles. M294's retracted 4x-value stride is refuted by the stride DECODED from the pinned chain (28 = (8-1)<<2, the counter dword at +4 INSIDE the slot) | `evidence/b18_sitegate.txt:7` | V (bytes), MEASURED (populations) |
| BOTH stores are MAX by BRANCH POLARITY (`cmp edi,eax` / `jle L` landing over the `mov eax,edi` take and at-or-before the store, with no branch between L and the store; a MIN store would need `jge`) - decoded by the shipped checker WITH the old loads graded (cell: `xor eax,eax`+`mov al,[ecx]` zero-extension immediately before the cmp; slot: the full-dword load) - not asserted; the recorded walk leaves every table monotone, each slot AND every (block, site) cell at the recorded per-pair MAX (0 disagreements), and the last-write / min / owner-block-blind rivals diverge on 1 slot / 1 slot + 5 cells / 4 cells | `evidence/b18_sitegate.txt:8` | V (polarity) |
| OPEN (LEAD): the CONTENTS of 0x989ce8 / 0x94eca8 were never dumped (a read-only /proc window grades the funnel absolutely); the slot's `[+4]` visit counter (its ++ is gated on call 0x5832b0); ebx's walked-table provenance beyond the owner-byte reading | - | lead |
| ACCEPTANCE `python3 -m sim.selftest --b18 programs/saves/m54b_clean.SAV` -> **PASS B18: 10/10** (no box, no /proc, no gdb) | `evidence/b18_sitegate.txt:11` | V |
## M299 (s254, STATIC, zero box) - the slot [+4] VISIT COUNTER and its FUN_005832b0 GATE decoded from pinned bytes
| claim | evidence | conf |
|---|---|---|
| `FUN_0051dcb0` 0x51dffd `call 0x5832b0` + `test eax,eax` + `je 0x51e11d`: the fall-through is exactly `inc` of the dword at [esi+0x989cec] = **slot[site].counter** (0x989ce8 base + 4 + 28*site; esi fold re-decoded 0x51dfac-ba, NO esi write to the store, and 0x5832b0 pops ebx/esi/edi on ALL 6 rets); args = the pinned (x,y) pair ([ebp-0x10],[ebp-0x8], same push slots as the 0x5aff90/0x582cc0 calls) => **the visit counter increments iff FUN_005832b0(x,y) != 0** (B18 G8's UNMODELED lead CLOSED) | `evidence/m299_visitgate.txt` W1:5, G4:170 | V |
| `FUN_005832b0(x,y)` is a PURE predicate (0 memory stores; 13/13 constants agree ghidra-vs-objdump): shared tile_record_array fold rec = ds:0x92ae14 + 44*(ds:0x692184*y + (x>>1)) (graded 4096/4096 incl. sar); ladder on dword[rec+8]: 0x102000 -> FALSE (byte9 bit5 = the B16 occ bit; byte10 bit4 unnamed); ds:0x985ac4 bit 0x2000 -> (dword & 0xc000000) ? 2 : 0; 0x10000000 -> TRUE; ds:0x92a380 == 0 -> FALSE (**rand+1**, MAP_FORMAT.md:116); then parity h=(x+y)>>1, d=x-h, index (h&3)+4*(d&3): class (byte0&0xe0)>=0x60 tests == (rand - 5*(h>>2) - 3*(d>>2)) & 0xf (exactly 1 of 16 lattice classes; 36/36), else == (rand + 8 + tdiv4(h)*ds:0x692210 + tdiv4(d)*ds:0x69220c) & 0x1f (stride VALUES unrecorded - ported only) | W2:52, G3:169, G5:171, G6:172 | V (decode), MEASURED (s249 inputs: rung1-close 481/2048, occ 16, bits26/27 12, rung3 5, class>=0x60 1087, G7:173) |
| DECLARED: counter VALUES, ds:0x92a380/0x692210/0x69220c VALUES, 0x985ac4 bit 0x2000 semantics NEVER recorded; the byte read 0x51e02c [site + 8380*block + 0x94ed28] (region array, NAMED:371) is a LEAD; 0x5832b0 has 24 callers (lattice family - CENSUSED by M300: 21 truth-branch, 2 stored, 1 mask-converted; only 0x51dffd gates [+4]) | witness block `evidence/m299_visitgate.txt:175-181` + `evidence/m300_callers.txt` | lead -> V (M300) |
| ACCEPTANCE `python3 scripts/m299_visitgate.py` -> **PASS M299: 7/7** (zero box, zero /proc, zero gdb; `scripts/gate.py --base main` GREEN) | `evidence/m299_visitgate.txt:183` | V |

## M300 (s255, STATIC, zero box) - census of the 24 callers of FUN_005832b0: which paths can reach the slot [+4] write
| claim | evidence | conf |
|---|---|---|
| 24 `call 0x5832b0` sites in the full .text dump == index.csv n_callers=24 (objdump + Ghidra agree); the address NEVER appears outside a call rel32 => no indirect/vtable use of the predicate | `evidence/m300_callers.txt` S1 | V |
| the 24 sites span 13 caller functions; gates supplied: 21 truth-branch (test eax,eax + je/jne; 0x50e216 also pushes raw value as arg, leg-ambiguous), 2 store raw to frame slot (0x4cf907->[ebp-0x1c], 0x5858fa->[ebp-0x7c]), 1 neg/sbb/and sign->0x200 mask (0x568567); biggest caller FUN_0055f650 (7 sites, contains the OPEN 0x56c6de continue-leg lead) | S2/S3w tables + raw windows | V (containment via index.csv; class = label, windows = witness) |
| the [+4] counter dword has NO writer outside FUN_0051dcb0: all 5 whole-dump mentions of 0x989cec are in FUN_0051dcb0 (lone STORE 0x51e01b) and the only slot-base materialization elsewhere is 0x51dd05 `mov eax,0x989ce8`, same function. LIMIT (declared): pointer-passthrough / non-literal addressing outside static scope; the live any-other-writer watchpoint remains OPEN | S4/S5 | V (static scope) |
| reach of callers to the write's owner (reverse BFS, DIRECT call edges only; 11 direct call sites of 0x51dcb0): 1 site feeds the counter gate (0x51dffd); 1 reaches directly (0x59ddf4 FUN_0059ce10, M94 per-player walker); 15 sites / 7 fns transitive depth 2-8 (FUN_0055f650x7, FUN_00585720x3, FUN_0050d140x2, FUN_004c40e0, FUN_004cf4c0, FUN_0051c750, FUN_0059e2c0); 6 sites CANNOT-REACH: FUN_0046a610, FUN_004e63b0 (M53q scan-pool rebuild), FUN_0058b1b0x3, FUN_005aff90 (B18 value body = SIBLING consumer of the same (x,y) fold, not nested in the counter path) | S6/S7 | V (direct edges; indirect calls not in the graph) |
| LEADS: which loop in FUN_0055f650 chooses among its 7 predicate sites + readers of the stored predicate slots [ebp-0x7c]/[ebp-0x1c] + the 0x56c6de continue-leg **CLOSED by M304** (case ladder + per-arm loops; the slots are FOREIGN frames, one reader each; the leg = 8-pred common exit) - see ## M304; sibling 0x5831a0 called with the same (x,y) right after the predicate at 0x4c4901/0x50e216 still OPEN | - | lead -> V (M304) |
| ACCEPTANCE `python3 scripts/m300_callers.py` -> **PASS M300: 12/12** (zero box, zero /proc, zero gdb) | `evidence/m300_callers.txt` tail | V |

## M301 (s256, STATIC, zero box) - the lead "ebx's walked table 0x51de2c-0x51df1d" REFUTED: it is a base_array walk, not a table
| claim | evidence | conf |
|---|---|---|
| ZERO entries: the lead's range is 0xf3 = 243 B of .text ending on the last byte of `test ebx,ebx` 0x51df1d - 60 dword slots + 3 B leftover, 0 dwords (aligned OR at any byte offset) resolving into .text; the span tiles gap-free as 81 instructions = 68 of ONE loop (0x51de27-0x51deef, sole back edge `jl 0x51de27`) + 13 of its exit block, and holds 4 `call 0x64b870` | `scripts/m301_ebxtable.py` A1/A2, `evidence/m301_ebxtable.txt:95-104` | V |
| nature = EXECUTABLE CODE, not addresses/pointers/masks/offsets: the same 243 B read from the PE file image (programs/terran.exe .text, file off 0x11de2c) are byte-identical to the dump; Ghidra n_insns 386 == the dump's insn count over the function window; 0 indirect jmp/call in FUN_0051dcb0; 0 lea/mov/push of any range address image-wide; all 4 external edges target the exit block 0x51defd, none enters the walk | A0/A3/A7, `evidence/m301_ebxtable.txt:115,:191` | V |
| what it walks = the NAMED base_array 0x95da10 (NAMED.md:74): cursor eax = 0x95da12 (base+2, init 0x51de1f, spill [ebp-0x14]), rows `add eax,0x130` 0x51dee2 = 304 B, index = trip counter [ebp-0x18] vs the BSS row count ds:0x985af4; body reads row x(+0)/y(+2)/flag(+4) + the 44-B tile-record view; the compared ebx = BYTE[304*i + 0x95da14] (0x51ddff), i = FUN_004e37f0's return (0x51ddb1) - scale chain 0x51ddf2/f7/fa evaluates to 304*i | A4/A5 | V |
| it GATES NOTHING of the 0x51dffd decision: 4 bypass legs land on its exit block which falls through to the call; of 11 branches between the range exit and the call, 0 land past it (ebx==0 leg `je 0x51dff5` 0x51dfd1 = the pre-call block); ebx feeds only the cell stores 0x51dfc9/0x51dfd3-e0 and the post-store byte read 0x51e02c, never the counter address (esi = the 28-B fold of [ebp-0xc], M299); FUN_005832b0's eax has one consumer (`test eax,eax` 0x51e005), is overwritten 0x51e024, and 0 backward edges from after the call reach the range | A6 | V |
| OPEN: whose record the exit block's BYTE[edi+0x7] is (edi = [ebp-0x4], sole pre-range writer 0x51dd28); the walk's meaning (tile-class filter 0x51de5b-61 + distance vs ds:0x8f0d34 0x51dece-0x51ded0 + 3 `or ebx,-1` sentinels) - shape V, semantics INFERRED | `evidence/m301_ebxtable.txt:132-146` | lead |
| ACCEPTANCE `python3 scripts/m301_ebxtable.py` -> **PASS M301: 8/8** (zero box, zero /proc, zero gdb) | `evidence/m301_ebxtable.txt` tail | V |

## B19 (s257, BUILD 10/10) - the slot [+4] visit counter made EXECUTABLE (sim/visitcounter.py)
| claim | evidence | conf |
|---|---|---|
| the gated inc: `[0x989ce8+28*site+4]++` runs IFF `FUN_005832b0(x,y) != 0` at 0x51dffd - the inc block 0x51e00d-0x51e01b (load [esi+0x989cec] / inc / store) is entered ONLY by fall-through (je 0x51e11d past the store, no branch into the interior), the counter field DECODES to MAX operand +4 on the same pinned 28-B esi; every model constant read out of the W1/W2 windows embedded in the M299 evidence file (rung 0x102000 / flag 0x2000@0x985ac4 / sel 0xc000000 / rung3 0x10000000 / rand 0x92a380 / strides 0x69220c+0x692210 / coefs -5*sar(h,2)-3*sar(d,2) mask 0xf, B mask 0x1f + trunc4); branch-A lattice runs as TWO agreeing implementations + the RECORDED 36/36 theorem | `sim/visitcounter.py`, `evidence/b19_visitcounter.txt:10,:13` (G1/G4), pins `evidence/m299_visitgate.txt:5,:52` | V |
| replay over the 2321 recorded decision rows (B17 loader + B16 transposition + B18 site_of): sites {1:2253, 9:68} == B18 anchor (counter table = MAX table, +4 vs +0); census {'branchA':1099,'rung1':1222}; 1222 CERTAIN-refuse / 0 CERTAIN-accept / 1099 possible; DECLARED baseline Live(flag2000=False,rand=1): 20 eax=2 accepts, 1079 undecided (branch-A miss -> never-recorded branch-B stride lattice); eax=1 return STRUCTURAL-ONLY in this window (0 rows, 5 dump records) | `evidence/b19_visitcounter.txt:5-9,:17-18` (G8/G9 + table) | V (law + brackets); the counts' LIVE side OPEN (values unrecorded) |
| the M300 24-caller census + the M301 eax-witness re-graded against the W1 BYTES inside the sim (21/2/1, 17/1/6, single IN-WRITER 0x51dffd line-for-line; 0 backward edges, je 0x51dff5 pre-call) | `evidence/b19_visitcounter.txt:15-16` (G6/G7) vs `evidence/m300_callers.txt` S2, `evidence/m301_ebxtable.txt` A6 | V |
| DECLARED UNMODELED: live VALUES ds:0x92a380/0x69220c/0x692210/0x985ac4-bit2000 (address witnesses only `evidence/m299_visitgate.txt:175-178`) - one read-only /proc pass dumping these four + the 0x989ce8/0x94eca8 tables grades every B19 count ABSOLUTELY (LEAD, sharpens B18's); counter-table CONTENTS; the 0x51e02c 0x94ed28 post-read downstream; which REACHES callers run | docstring, `evidence/b19_visitcounter.txt:14,:18` | lead |
| ACCEPTANCE `python3 -m sim.selftest --b19 programs/saves/m54b_clean.SAV` -> **PASS B19: 10/10**, two runs byte-identical (zero box, zero /proc, zero gdb) | `evidence/b19_visitcounter.txt:20` | V |

## M302 (s258, BOX-READ read-only /proc) - B19's unmodeled live values pinned; the 1099 undecided rows collapse to a point
| claim | evidence | conf |
|---|---|---|
| live VALUES y2150 (m54b_clean): ds:0x92a380 rand+1=9661 (&0xf=13), ds:0x69220c=61, ds:0x692210=11, ds:0x985ac4=0x1a0e -> bit 0x2000 CLEAR, flag2000=False (B19's declared baseline bit-state CONFIRMED) | `scripts/m302_livepins.py`, `evidence/m302_livepins.txt:4-7,:150` | V (read-only pread, TracerPid 0 both sides, year/round unchanged) |
| the 0x989ce8 slot region 128/128 readable (28 B): site 1 MAX 15 CNT 40, site 9 MAX 3 CNT 2; nonzero MAX [1,3,4,5,6,7,9,10,13,14,15,16,65,66,69,70], CNT [1,6,9,13,16,63,65,70]; CNT>MAX at [1,63,65] - NO landed cross-field law (printed not asserted); table nonzero at idle load -> carried or rebuilt (OPEN); monotone two-pass (only writers MAX store + ++) | `evidence/m302_livepins.txt` (128-slot dump; :A4, :A5) | V (dump); table provenance OPEN |
| the pinned replay grades B19 ABSOLUTELY: 2321 rows -> 38 CERTAIN-accept / 2283 CERTAIN-refuse / 0 undecided; the 1099 branchA undecided -> 38 accept (37 eax=2 branchA hits, residue 13; 1 eax=1 branchB - FIRST non-structural eax=1 row) / 1061 refuse; the 1222 rung1 unchanged; B19's 20 baseline (rand=1) accepts all flip | `evidence/m302_livepins.txt:151-154` (:A6,:A7,:A8) | V (shipped sim + pinned values) |
| ACCEPTANCE `python3 scripts/m302_livepins.py` -> **PASS M302: 10/10** (A1-A10; box left running, no writes) | `evidence/m302_livepins.txt:170` | V |

## M303 (s259, STATIC, zero box) - the 0x51e02c "post-counter read" is the LOAD HALF of a byte CNT++ on the per-block BYTE twin of the slot table
| claim | evidence | conf |
|---|---|---|
| index algebra: fold 0x51e013-2a (BYTE-IDENTICAL copy 0x51dfd3-e0, rematerialized across the 0x51dffd call) evaluates edx=65*ebx -> eax=(131*ebx<<4)-ebx=2095*ebx, load scale *4 -> byte addr = **[ebp-0xc] + 8380*block + 0x94ed28 = site + 8380*block + 0x94ed28** (shadow-evaluated). B18-law-28 REFUTED for THIS expression: (site*8-site)<<2 = 28*site is the esi fold 0x51dfb1-ba in the SAME window (SIB 8d 34 c5 vs 8d 04 53) feeding the DWORD twin | `evidence/m303_downstream.txt` S1/S2 (A2,A3) | V |
| inputs: ebx = BYTE[304*i+0x95da14] (base_array row flag = BLOCK id; 304-fold shadow-verified; -1 sentinels clamped to 0 at 0x51df22-24 BEFORE the fold); ecx = [ebp-0xc] = site = BYTE[tile_record+3] (sole in-function writer 0x51dd57); edx = 65*ebx - a copy, NOT a coordinate | S3 (A4) | V |
| the table 0x94ed28 = 0x94eca8+0x80: per-block visit-CNT byte array, twin of the MAX byte array at 0x94eca8; entry width 1 B (init `mov BYTE` step +1; all 11 corpus mentions BYTE PTR), 128 entries/field (init cmp ecx,0x80), block stride 8380 B = the init `add edx,0x20bc` (stride derived TWICE: fold AND init, (0x95f288-0x94eca8)/8380 = 8 blocks); the *4 scale is multiplier placement (8380/4=2095), proven against the sibling WORD array 0x94e8a8 (scale *2 = its width, SAME 8380 phase) | S4/S1 (A5) | V |
| CONSUMERS: 0x51e02c is load++store (0x51e033 lea SAME SIB+disp / 0x51e03a inc dl / 0x51e03e mov [eax],dl; no branch in between, store unconditional; je 0x51e040 tests `test ebx,ebx` flags not the byte; dl DEAD after 0x51e03e); family census = 11 literal mentions whole .text: MAX 6 external readers + max-store 0x51dff3 (ebx!=0-gated), CNT 1 external reader FUN_004f6030 0x4f946d `test al,al`/jne (visited? gate); ALL external consumers terminate in cmp/test; NO family byte feeds the DWORD 0x989ce8 (both MAX stores take the walk candidate edi); NO store outside FUN_0051dcb0 (11 sites: 6 init-zero + 5 update); name_global --disp "0 writes" = the register-after-lea pointer-form blind spot | S0/S5/S6/S6b/S8 (A1,A6,A7,A8,A10) | V |
| dispatch AFTER the store (branching on block, never on the byte): ebx!=0 -> 1<<block tested in BYTE[tile+4] (or ds:0x985b10 bit, or ds:0x985aec>3) -> call FUN_0056d480(block,3,1,x,y); ebx==0 -> 8-row walk of byte field 0x950664 (+0x20bc advance, bound 8) -> FUN_0056d630(block,3,x,y) + row finder 0x4e37f0 -> call FUN_0056d480 | S7 (A9) | V (static shape); callee semantics ANSWERED by ## M308 (SITE-list insert + probe; and the (block,3,1,x,y) literal pair is only ONE of KIND {0,3,8}) |
| OPEN: live values of the byte MAX/CNT fields; live upper bound of the block byte (<8 implied by the init span, unproven); semantics of the sibling fields in the 8380-B record (word @+0 witness 0x94e8a8, dword 0x94f4ec, byte 0x950664, word 0x950a64); save-carry vs rebuild of the BYTE family (STILL OPEN, and M308 adds the SITE list to the same question) | S9 | lead |
| ANSWERED since this block (## M308, `evidence/m308_site_list.txt`): FUN_0056d480/FUN_0056d630 = the 25-entry SITE list (stride 0x10, {+0 KIND,+2 PRIORITY,+4 X,+8 Y}) of the 8380-B record at 0x94f2d8, insert-or-max with an evict-by-priority rule / pure probe; ds:0x985aec = a dword enum (cmp-only {1,2,3,4}, 0 arithmetic, 4 writers, 2 mirror ds:0x92bde8, 1 fed by movsx BYTE ds:0x8f0c11); ds:0x985b10 = ONE byte bit-mask (544 refs, 0 array forms, 12 byte stores, 95 register-bit tests; rebuilt as OR(1<<BYTE[rec]) over stride-0x19c records from 0x91e494) | S9 | V |
| ACCEPTANCE `python3 scripts/m303_downstream.py` -> **PASS M303: 10/10** (A1-A10 table-then-assert; 2 runs byte-identical; zero box, zero /proc, zero gdb) | `evidence/m303_downstream.txt` tail | V |

## M304 (s260, STATIC, zero box) - the seven FUN_0055f650 predicate sites: case-ladder chooser, per-arm loops, 0x56c6de = the hub common exit
| claim | evidence | conf |
|---|---|---|
| chooser = the [ebp-0x44] case LADDER (31 `cmp [ebp-0x44],imm` in-window; sole prologue producer 0x55f74a = type-record plan byte, M127/B15) + per-arm loops; NO loop covers >2 sites (max=2: the 0x56b061..0x56c6a0 nest holds sites 6+7) and ALL 7 sites sit inside loop spans - both shortlist rivals (one-loop / zero-loop) FAIL on the printed tables | `scripts/m304_chooser.py` S1b/S1c/S5b, `evidence/m304_chooser.txt:152-161` | V |
| per-site guards table (closest pred jcc <- flag-setter <- decider <- in-block producer): site 1 is the ONLY one directly case-gated (`cmp eax,3` vs [ebp-0x44] before 0x56429c); 0x568567 has NO real local guard (its only pred edge is a VACUOUS jump-to-next jne 0x56855f) - chooser is upstream (18 must-pass legs); 0x56b77c/0x56c5f4 arrive via 3/4 OR'd jcc legs + fall-through | S2 rows, `evidence/m304_chooser.txt` S2 | V (bytes); arm-case of sites 2-5 INFERRED |
| 0x56c6de = block head with 8 preds: 7 unconditional `jmp 0x56c6de` (one per arm region, skipping 3669..16060 insns) + fall-through after `BYTE[unit+0x2b]=0x78` = the hub arms' COMMON EXIT; the leg re-tests [ebp-0x84] best-direction (0 dominating writers) -> act 0x56c966 or clear unit-flag bit 0x10000 + order byte -> jmp 0x56cafa | S3, `evidence/m304_chooser.txt` S3 | V (edges/bytes); act-vs-cleanup semantics INFERRED |
| CORRECTION of the M300 lead: the "predicate frame slots [ebp-0x7c]/[ebp-0x1c]" are NOT hub slots (hub = 0/7 STORED-class consumptions; [ebp-0x1c] 126 acc/79 writers hot scratch; [ebp-0x7c] 0 writers inside the nest). The stores live in FUN_004cf4c0 (0x4cf920 -> its [ebp-0x1c]) and FUN_00585720 (0x5858ff -> its [ebp-0x7c]), EACH WITH EXACTLY ONE READER (0x4cfef2 / 0x589fe5) - the M300 readers-lead CLOSED | S4/S5, `evidence/m304_chooser.txt` S4/S5 | V |
| ACCEPTANCE `python3 scripts/m304_chooser.py` -> **PASS M304: 12/12** (A1-A12; 2 runs byte-identical; zero box, zero /proc, zero gdb) | `evidence/m304_chooser.txt` tail | V |

## B20 (s261, BUILD 10/10) - the BYTE-twin visit counter made EXECUTABLE (sim/bytecounter.py)
| claim | evidence | conf |
|---|---|---|
| the byte law executed: index site+8380*block+0x94ed28 {MAX@+0,CNT@+128} width 1 B, 128/field, 8 blocks (fold 65/131/2095*4 AND init add edx,0x20bc - stride twice); ++ unconditional behind je 0x51e007 (hex-decoded target 0x51e11d past the store; je 0x51e040 tests test ebx,ebx flags) - all constants decoded from the windows embedded in the M303 evidence file | `sim/bytecounter.py`, `evidence/b20_bytecounter.txt:16-19` (G1/G2/G3), source `evidence/m303_downstream.txt` S1/S4/S5 | V |
| PARITY vs the DWORD twin: the SAME accepted fall-through feeds both - 38 pinned accepts -> 38 dword CNT (site 1) == sum_blocks byte CNT {(0,1):1,(3,1):17,(6,1):20}; per-site equality both record views; byte MAX keeps B18's block-0 skip (cells {(2,1):4,(3,1):7,(4,1):3,(5,1):2,(6,1):6}, 277 skips) while byte CNT does NOT; censuses grade against numbers PARSED from m302_livepins.txt + b18_sitegate.txt, anchor coherence itself gated | `evidence/b20_bytecounter.txt:32-35` (G4/G6/G7), `:37-38` (G8/G9 rivals 2283/1/2/1/2/38) | V (law+replay); live byte CONTENTS unmodeled |
| MEASURED: exactly 1 accepted row on block 0; no byte wrap (max MAX 7, max CNT 20); live-view accepts 7 vs save 38, byte CNT diverges on 3 entries (the B18/B19 record drift, counted); m302's per-site split column covers the 1099 branchA rows ONLY (grading gotcha) | `evidence/b20_bytecounter.txt:23-29` (tables), `:32` (G4) | V |
| ACCEPTANCE `python3 -m sim.selftest --b20 programs/saves/m54b_clean.SAV` -> **PASS B20: 10/10** (G10 two runs byte-identical; zero box, zero /proc, zero gdb) | `evidence/b20_bytecounter.txt:39` (9/9 module line; G10 in selftest stdout) | V |
| DECLARED UNMODELED: live byte-table contents; block upper bound (<8 implied); per-call zero-rebuild cadence (FUN_0051dcb0 callers OPEN); dispatch/settle-nest meaning (M303 S7, M304); save-carry vs rebuild; 8380-B siblings | docstring + BUILD_SPINE §B20 | lead |

## M305 (s263, ANALYSE, zero box) - FUN_0051dcb0 = the zero-rebuild OWNER: 11 single-site callers, one loop-enclosed, a round-mod-4 gate
| claim | evidence | conf |
|---|---|---|
| IDENTITY: FUN_0051dcb0 zeroes-then-rebuilds BOTH counter tables. Zero window covers BYTE base 0x94eca8 stride 8380(=0x20bc) x 8 blocks x 128 entries (term 0x95f288) and DWORD 0x989ce8 x 128 slots x 28 B {MAX@+0,CNT@+4} (term 0x98aae8), residual 0 both | `evidence/m305_identity.txt:29` (byte), `:31` (dword), A1-A5 @`:36-40` | V |
| REBUILD: the walk re-visits all 2048 tile records EXACTLY ONCE (32/row uniform, W=H=64, mult=32, x=(y&1), x+=2, shared cursor) with 0 fold mismatches vs `base+0x2c*(32*y+(x>>1))`; the decoded cursor step IS the 44-B stride (2048 gapless byte offsets, span 0x16000); rival x-stride-1 (4064 visits, 4063 mismatches), outer-bound-1 (32), cursor-reset-per-row (2016) all FAIL on the printed numbers | `evidence/m305_identity.txt:73-83` (walk, 4 rivals, A18) | V |
| CALLERS: 11 direct sites == index.csv n_callers=11, in 11 DISTINCT functions, each calling ONCE; 0 stored-dword occurrences of the VA in terran.exe -> no vtable/callback entry (a rel32 call never stores it). RIVAL "one hub calls it repeatedly" FAILS (max mult 1). Loop enclosure (P1 fix - the first scan was vacuous): exactly 1 site, 0x59dd3a in FUN_0059ce10 (back-jump 0x59e2a6 -> 0x59ce92) | `evidence/m305_identity.txt:120-139` (census, A10-A14) | V |
| CADENCE: 5/11 sites sit under a decompiled conditional, 2 are skipped by the immediately-preceding branch, 4 are top-level; 0x51f71e gated `(round & 3) == bl` with bl==1 on a path that reaches the gate (the only competing ebx write, `pop ebx` 0x51f5a2, is an exit path - `inc;ret` follows) -> once per 4 rounds at round%4==1; 0x5b09f6 gated `ds:0x99180c==0`; triad `call 0x5a2ae0/add esp,8/call` at 0x4f3e08+0x508b48+0x543bc6; row-table builder (loop writing ds:0x985af4) runs immediately before 0x59b8ce | `evidence/m305_identity.txt:122-127`, A15/A16 @`:136-137`, A19 @`:139` | V (static); live per-turn cadence unmeasured |
| EXPORT HOLE: site 0x4f3e08 is outside its index.csv owner FUN_004f34b0(+298 -> 0x4f35da); the sole prologue in the gap is 0x4f35e0, a real 2673-B function spanning [0x4f35e0,0x4f4051) with NO index row of its own -> index.csv is not a total function map. **CORRECTED by M306**: the code IS decompiled — Ghidra folded the region into FUN_004f4060's body via the tail-jump 0x4f4133 -> 0x4f35e0, so the earlier "no body" phrasing was wrong (body exists, mis-parented) | `evidence/m305_identity.txt:130`, A17 @`:138`; refuted-in-part by `evidence/m306_owner.txt` A17/A21 | V (coverage), owner body UNKNOWN |
| ACCEPTANCE `python3 scripts/m305_identity.py` -> **19/19 OK**, exit 0; rerun diff = 0 lines. Zero box, zero /proc, zero gdb | `evidence/m305_identity.txt:154` | V |
| DECLARED UNKNOWN: U1 0x4f35e0 owner guards/preds — **NARROWED by M306** (bounds/callees/no-guard settled; per-branch meaning still open); U2 per-block/per-slot MEANING (M302/M303 scope); U3 live per-turn cadence (zero box) | `evidence/m305_identity.txt` §UNKNOWN | lead |

## M306 (s264, STATIC, zero box) - 0x4f35e0 = a real 2673-B function absorbed by tail-jump folding; the export's "hole" is an index.csv size/containment lie
| claim | evidence | conf |
|---|---|---|
| BOUNDS: [0x4f35e0, 0x4f4051) — fresh prologue after 6 aligner nops; CFG 846 insns contiguous; 3 rets / 3 pop-triple epilogues, last ret 0x4f4050 + 15 nops; ZERO CFG edges leave the span | `evidence/m306_owner.txt:2-8` (prologue/prologue-CFG/padding/epilogue census), A1-A7 @`:64-70` | V |
| IDENTITY: per-object routine on ds:0x8f0d60; 23 callees/36 sites (_rand x3, FUN_00507410 x6). The FUN_0051dcb0 call 0x4f3e08 has NO branch predecessor — it is a fall-through from a 21-iteration loop (`cmp eax,0x54; jl 0x4f3c0a`), NOT a branch target. **That does NOT make it unconditional**: all 3 of 3 rets are reachable without executing it (0x4f36b9 / 0x4f38ef / 0x4f4050), so early exits skip the counter rebuild (P1, Greptile s264) | `evidence/m306_owner.txt:41-49` (preds, loop predicate), A8/A9 @`:71-72`, A23 @`:87` | V (static); semantics OPEN |
| ENTRY: zero direct calls, zero stored-dword pointers (scan live via 164 control hits); single entry = backward jmp 0x4f4133 from inside FUN_004f4060, reachable by fall-through (no branch preds -> live edge) | `evidence/m306_owner.txt:50-54` A10-A13 @`:73-76` | V |
| WHY MISSED: Ghidra folded the region into FUN_004f4060's body (triad at body-line 388, `< 0x54`, DAT_00985af0 x5, rand x3) while index.csv size=3058 stops at 0x4f4c52 — code modelled, function never created, index row never sized | `evidence/m306_owner.txt:55-63` (body, fingerprint, triad), A21 @`:85` | V (absorption); folding rule INFERRED |
| ACCEPTANCE `python3 scripts/m306_owner.py` -> **23/23 OK**, exit 0; rerun diff 0 | `evidence/m306_owner.txt:93` | V |
| UNKNOWN: live execution of the entry (zero box); body per-branch semantics; Ghidra's exact fold rule. ~~0x54-cap meaning~~ and ~~FUN_005a2ae0 args~~ ANSWERED by M307 (21-pair even-parity neighborhood tables; args = (record-index, bit-index)) - see ## M307 | `evidence/m306_owner.txt:88-92`; `evidence/m307_folded_body.txt:19-44` | lead -> V (M307) |

## M307 (s266, STATIC, zero box) - the 0x4f35e0 body's 21x loop = two 21-pair even-parity neighborhood tables; triad args = (record-index, bit-index); _rand x3 = 2 gates + 1 draw
| claim | evidence | conf |
|---|---|---|
| LOOP: cap is immediate 0x54 (1 site), index [ebp-0xc] zeroed per entry @0x4f3bf1, sole back-edge -> exactly 21 passes; reads T_x=[idx+0x67850c], T_y=[idx+0x678990]; tile conv 44 B over ds:0x92ae14; row-walk 0x34 over 0x933282 (count ds:0x985af0) | `evidence/m307_folded_body.txt:4-17` (parsed inc/cap/jl + idx/tables/chain), A1-A7 | V |
| TABLES (file-backed .rdata 0x27850c/0x278990): 21 (dx,dy) = even-parity Cheb3-box minus 4 (+-3,+-3) corners; D4-closed; order center->8-ring->(2,2)-corners->8 far (1,3)/(3,1); NOT Moore 3x3/5x5 | `evidence/m307_folded_body.txt:19-31` (full 21-pair dump), A8-A11 | V |
| TRIAD @0x4f3e00: FUN_005a2ae0(rec_idx=[ebp-0x14], bit_idx=[ebp-0x4]); callee uses only [ebp+0x8]/[ebp+0xc], scales arg1 *304 into 0x95da10 slots, bounds-checks the RECORD's WORD coords; [ebp-0x14] producers never a coordinate; [ebp-0x4]=BYTE[ds:0x8f0d60+4] single store @0x4f3604 | `evidence/m307_folded_body.txt:32-44` (incl. push sites :33-34), A12-A15 | V (static); game meaning INFERRED |
| FUN_00507410 = div-8 decomposition, out1 = n/8 ROUNDED TOWARD ZERO ((n+(n>>31&7))>>3; n=-1 -> 0), out2 = 1<<(n&7); dump-wide triad shape at exactly 3/11 FUN_0051dcb0 sites (0x4f3e08/0x508b48/0x543bc6) | `evidence/m307_folded_body.txt:46-47,78`, A16/A20 | V |
| _rand x3 @0x4f36df/0x4f3750/0x4f379f = GATE mod [8380*idx+0x94d690]+7 + GATE mod 3 + VALUE rand%39 (esi, range (1,0x22]) | `evidence/m307_folded_body.txt:50-55`, A17-A19 | V |
| ACCEPTANCE `python3 scripts/m307_folded_body.py` -> **20/20 OK**, exit 0; rerun diff 0 | `evidence/m307_folded_body.txt:87` (post-Greptile 20/20) | V |
| UNKNOWN: branch-A/B seed semantics ([ebp-0x1c]/[ebp-0x18] write sites 0x4f3771/0x4f3863 vs 0x4f3a48/54); what the 52-B row-walk records are; live execution | `evidence/m307_folded_body.txt:64-77` (asserts list all sites) | lead |

## B21 (s267, BUILD 12/12) - the m289 run as ONE composed state object: written, reloaded, RESUMED (sim/composedrun.py)
| claim | evidence | conf |
|---|---|---|
| COMPOSED RUN EXECUTES: 30 B3 presses + the 9-op founder/destroyer ledger applied BETWEEN presses; year_before == save_year+turn 30/30; the engine's 331-state emission supplies all 31 distinct recorded (cur,tf,year) samples IN ORDER (the recorder's after(t) IS before(t+1): self-chain 29/29 on year, n_bases AND (cur,tf)) | `evidence/b21_composedrun.txt:54-55` | V |
| THE CURVE IS STRICTLY COARSER THAN THE OP LOG: sum\|delta\| = 7 ops suffice to match the recorded n_bases curve, the log carries 9 -> exactly one turn hides a net-zero (+1,-1) pair; the DP counts K=11 feasible placements of the 9 ops into the 30 intervals; the curve-only schedule (B10's method) matches the curve 30/30 yet hits only 7/9 recorded (kind,pre-cnt) rows vs the log schedule's 9/9 | `evidence/b21_composedrun.txt:52-53,74` | V |
| LEDGER: op chain a closed walk 9/9 (each FOUND/DESTROY row's cnt == the model count before it), curve 30/30, endpoint 23, peak 24, the 5 grown slots == the surviving recorded foundings; the FIFO-destroy rival keeps a destroyed tile | `evidence/b21_composedrun.txt:17,59,75` | V |
| WRITE + RELOAD + RESUME: image grows exactly 1520 B = 5x304, header diff 2 bytes (bases dword @72, year word @84) both inside modeled spans, tail 10,800 B byte-identical, re-parses (year 2180, 23 records, record-for-record equal), and reload+1 press == 31-presses-then-write BYTE-FOR-BYTE (img->img2 diff = the 1 changed year byte @84); THE RESUME ENGINE IS BUILT FROM THE SAVED cur_player/tf-bit/year READ OUT OF THE IMAGE, and a writer that leaves cur_player in an AI slot is REFUSED a press (R7) | `evidence/b21_composedrun.txt:63-69,78` | V |
| ACCEPTANCE `python3 -m sim.selftest --b21 programs/saves/m54b_clean.SAV` -> **PASS B21: 12/12**, exit 0, rerun stdout-vs-evidence diff 0; `python3 -m sim.composedrun --out <f>` exit 0; two runs -> identical table text + identical written-image sha256 | `evidence/b21_composedrun.txt:93` | V |
| UNMODELED (declared): WHICH turn each op really fired (11 placements; the log has no turn stamp - earliest-feasible is a tie-break); the destroy slot (last, as B13); any economy/research/unit effect of a founding; the recorder's mid-cycle sampling law | - | lead |

## M308 (s268, STATIC, zero box; s269 review) — FULL rows VERBATIM at `docs/named-archive-m339-rows.md:8` (§rotation-1 marker at `:7`, s320-chain2 headroom rotation, sha1 `07cec1770614`; re-asserted by `scripts/m339_named_rotate.py --verify`); this stub governs. `0x4ddcf1`'s UNATTRIBUTED edge is CLOSED by `## M339`: nonzero `jge` = callee 0x5f1394's result cell `[obj+0xa40]`.

## M309 (s271, STATIC, zero box; mutation-tested) - FUN_0056d350 is the GOAL-list insert-or-max of the same 8380-B block record; its -1 6th argument is the entry's +0C OWNER dword, and -1 = unbound

| claim | evidence | conf |
|---|---|---|
| FUN_0056d350(rec,kind,prio,A,B,owner) indexes **0x94ee28 + 8380*rec** (chain -> (8380,0); a 2nd `imul r,r,0x20bc` lives outside it at 0x470d50) over **75 x 0x10** entries (2 back-edges, both `cmp r,0x4b`, both `add r,0x10`); fields **+0 short KIND / +2 short PRIO / +4 d / +8 d / +0C d**, derived from the store displacements + the param slot each source register def-walks to | `evidence/m309_goal_sink.txt:9-56` (S2 chain/S3 stores/S4 probe/S5 bounds) | V |
| It is the **GOAL** list because the binary says so: the `(A^B)&1` parity guard + `ds:0x985ae8` bit 0x1000 push **0x6914fc = "Bad GOAL"** (PE .data), while FUN_0056d480 pushes **0x691508 = "Bad SITE"**; the guard CANNOT skip the insert (both je -> 0x56d386, no ret between) | `evidence/m309_goal_sink.txt:95-121` (S8 guard/S9 strings) | V (game meaning of a GOAL: OPEN) |
| Same law as the SITE list: hit -> **+2 = max(old,prio)** and stores NOTHING else; miss -> evict by score (**1000** empty / **prio+100** / **20-prio**), strict `jle` (first index wins), no-candidate -> `jl 0x56d476` over a **store-free** epilogue past exactly the 5 insert stores | `evidence/m309_goal_sink.txt:57-94` (S6 found path/S7 eviction) | V |
| **owner (+0C)**: 1 writer (0x56d470) + 1 reader (0x559b3e) among all **65** operands naming the 100-entry block; reader signed, `jl 0x559b74` guards negatives, scaled **x304** (9x->19x-><<4) -> `test BYTE [edx+0x95da40],0x20`, gated on that entry's **+0 == 9** -> **-1 selects nothing (unbound owner)** | `evidence/m309_goal_sink.txt:196-244` (S12 census/S13 reader) | V (what the 304-B table at 0x95da40 is: OPEN) |
| arg6 census: **40** sites push 0xffffffff, **5** def-walk to **ds:0x68cbb0** (.data, 340 refs, exactly 6 stores, all in 0x4e3000-0x4f6000), **5 DECLARED unattributed**; the mirror (0x56d590) and the rebuild broadcast (0x56d6f8) both pass -1 | `evidence/m309_goal_sink.txt:128-195,245-262` (S11 callers/S14 global) | V (identity of ds:0x68cbb0: OPEN) |
| GOAL **+0 short has exactly 2 writers**: 0x56d45f (insert) and **0x470d5c = `mov WORD PTR [...+0x94ee28],0xffff` in FUN_00470b90** - the -1 free-slot sentinel writer M308 U2 asked for (SITE window still has none) | `evidence/m309_goal_sink.txt:209-211` (2 writers + 15 separate `imul r,r,0x20bc` in FUN_00470b90) | V |
| Gates are load-bearing: `scripts/m309_mutate.py` = **9/9** mutations (arg-reversal, census range, read/write polarity, param-seed loss, forward-jcc-as-loop, chain seed, blind-to-`ds:` stores, wrong window, empty dump) each reddening its named check | `evidence/m309_mutate.txt:23` | V |

## M310 (s272, STATIC, zero box; mutation-tested 14/14) — `FUN_00470b90` = the view object's DEBUG-GATED GOAL duplicate-invalidator + one-char-token logger; it owns the GOAL kind<->token map. FULL-LENGTH TABLE VERBATIM at `docs/named-archive-b30-rows.md:5` (sha1 `ca3caf3785c9d6e9`); this stub governs, one line per claim

| claim | evidence | conf |
|---|---|---|
| entry gate is the FIELD bit `and ecx,0x2000` on `[eax+0x1dd70]` (stowed this-pointer), landing on the single epilogue (`1` ret in 1020 B @0x470f89, `ret 0x8`) -> inert without the bit = diagnostics, not rules | `evidence/m310_goal_invalidator.txt` S2/S1 | V |
| loop nest blocks 1..7, filter `(ds:0x985ae8 & 0x80) \|\| block == ds:0x91b5b4`, scan bound `0x4b` = the 75-entry GOAL list (15 `imul r,r,0x20bc` 1:1 with 15 `shl r,0x4`; entry offsets touched {+0,+2,+4,+8} only) | `:S3,S4` | V |
| hit predicate `p1 == entry+4` && `p2 == entry+8` && `movsx kind >= 0` && `movsx prio != 0`; prio > 0 goes straight to the log tail with NO store | `:S4` | V |
| invalidation law: negative prio scans j != i for the same (p1,p2) AND `kind[j] == kind[i]` (folds re-seeded, encoding is the arbiter); the `0xffff` store is the only WORD store to +0 and writes entry i (0x470d5c); +2 has no store | `:S6` | V |
| post-store re-read (`movsx`+`test`/`jge 0x470d86`) skips negative kinds before the log tail | `:S6` | V |
| log tail call order: `FUN_00403a40` -> `FUN_00407520` -> `FUN_00423c20(block)`+`FUN_00405220` -> `BYTE ds:0x997121 = 0` -> token appends x8 -> `FUN_004237f0(abs prio)` -> 2 vtable calls -> `FUN_004081b0(ds:0x997120, buf)`; 9 targets == index.csv | `:S9,S11` | V (buffer's consumer OPEN) |
| kind->token map read from the PE BYTES (objdump misassembles both): dword table @0x470f8c = 8 handlers, 42-byte index @0x470fac behind `cmp [ebp-30],0x29 / ja`; tokens 0->'a',2->'d',3->'s',6->'n',8->'c',9->'f',41->'^'; kinds 1,4,5,7,10..40 + default share 0x470eb7 (pushes nothing) - the C's case list AGREES with the bytes | - (the source row carried NO cite) | INFERRED |
| args are a (p1,p2) COORDINATE pair: 5 call sites, each forwarding 2 closed stack slots; **CORRECTED by M312: all 4 forwarder sites push arg4=0 into the 0x471050 tail guard, so the site-1 path never executes -- see ## M312** | `:S5` | V (coordinate system INFERRED) |
| gates load-bearing: `scripts/m310_mutate.py` = 14/14, every mutant reddening its named check, the harness requiring the unmutated instrument to exit 0 and rejecting tracebacks | `evidence/m310_mutate.txt:17,18` | V |
| OPEN: GOAL semantics and the token alphabet; WHY a negative priority is the invalidation trigger; what `this+0x1ddb4/1ddb8` hold; what consumes `ds:0x997120`; save-carry of the GOAL list | - | lead |

## B30 (s321 BUILD, zero box) — the COMPLETION leg EXECUTABLE: a paid queue item becomes a facility the base HAS (`sim/composedfacility.py`; spine §B30; M310 rotated VERBATIM to `docs/named-archive-b30-rows.md:5`, sha1 `ca3caf3785c9d6e9`). ACCEPT `python3 -u -m sim.selftest --b30` -> **`PASS B30: 6/6 gates`** rows `234ab3d83a88dbea` print `29f408c79329a5a8` img `3a503c638ba45330` (`evidence/b30_facility_completion.txt:35-36`), 2 runs + relay identical; harness `python3 -u scripts/b30_mutate.py` -> **`PASS HARNESS B30: 10/10`** digest `76a481b5d8a7d8b0`, every gate G1-G6 reddened, NO-OP `[]`, ST 4/4, baseline tree green, no crash accepted (`evidence/b30_mutate.txt:12`).

| claim | evidence | conf |
|---|---|---|
| the container's own queue drives the run: 18 base records, own player 3, 2 eligible (`1<=head<=31` AND inside the parsed charge window; heads 32..38 ineligible `[]`), target base 0 'University Base' item 2 = 'Children's Creche', rule delta 1 | `evidence/b30_facility_completion.txt:2`, `:22` | V MU6 |
| the SETTER is the reader's inverse over the whole 32-id window (32/32 round-trip, 0 stray bits, id 39 REFUSED); the swapped-orientation rival lands on only 4/32 ids | `:23` | V MU1/MU2 |
| the write is ONE byte: diff `[140]`, delta 4 = `1<<(item&7)`, inside `+0x8c..+0x8f` | `:24` | V MU1 |
| writer round-trip: identity build byte-identical, file diff = 1 offset, reload owns `[1,2,8]`, shape/tail equal, 17/17 other records byte-identical, wrong-base rival misses THROUGH THE RELOAD | `:25-26` | V MU3/MU5 |
| the bill moves by the DERIVED table under M46's disabled rule (0 -> 1, delta 1 == rule 1, 0 per-id mismatches), priced off the RELOADED record; the 'table value' rival differs at exactly `[8]`; G6 runs the instrument twice, so determinism is a gate | `:27` | V MU4/ME3/ME4 |
| the completion ROUTINE that stamps the bit is ASSUMED (reader-inverse) - no setter in this rung's evidence; **census pick opened** | spine §B30 | INFERRED |
| OPEN: every other real-completion effect (queue-pop order beyond B11, storage/mineral reset, messages); ids 39..71's shared-field question | - | lead |

## M338 (s319-chain2, STATIC 8/8, review #357 hardened) — the LAST two `#DIFF` readers: `0x57c606` is the literal loop counter 0..5; `0x44a1c8` indexes with a hall-of-fame record byte (+0x20) that is the faction's EFFECTIVE DIFFICULTY — `evidence/m338_diff_readers.txt:1`

| claim | line | kind |
|---|---|---|
| table census: `.text` refs to 0x94d2ac = 2 base loads + 7 scaled readers {0x44a1c8,0x484cc9,0x485426,0x48678f,0x486f40,0x57c606,0x599405}, 0 stores; declared==measured both ways | `:1-10` | V MU2,MU11,MU12,ALG1 |
| `0x57c606`: `xor esi,esi` (0x57c604) immediately precedes; the body's only esi write (broad write-classifier) is `inc` 0x57c6ca; `cmp esi,6`/`jl 0x57c606` => 0..5, and the LOADER is read (0x57ac74 mov esi / 0x57ac85 add 4 / 0x57ac88 cmp 0x94d2c4) = the same 6 | `:11-16` | V MU1 |
| `0x44a1c8`: exact 6-instruction window `eax=[ebp-0x1c]`, `xor edx,edx`, scratch clear, `ecx=0x997b28`, `dl=BYTE[eax+0x20]`, `[edx*4+0x94d2ac]`; 0 insns between the byte load and the index; 0 eax clobbers (write-classifier) | `:17-24` | V MU3,MU15 |
| `[ebp-0x1c]` = record of the 35x0x8c buffer 0x983a10: 3 stores only, the 0x4497b7 store's SOURCE is eax, no eax clobber in (0x4497ad,0x4497b7), no bracket-crossing jump; `(8-1)*(1+4)*4 = 0x8c` | `:25-33` | V MU4,MU5,MU13 |
| buffer = `hallfame.jhh`: the fopen WINDOW is `push 0x689f3c; push 0x689f40; call 0x64c980` with PE strings `rb`/`hallfame.jhh`, the read window pushes size 0x1324/buffer/call 0x64cc00, zero-init is the exact 8-insn sequence 35x0x8c to 0x984d34, sibling 0x44adc0 nests 5 per 0x2bc | `:34-41` | V MU6,MU7 |
| field +0x20: the module is MEASURED as the 7 functions that address 0x983a10 (ghidra extents); their union has exactly 2 stores — 0x44b15b from `BYTE[0x94d438+8380*faction]` (fold decoded = 0x20bc, cell = 0x94d430+8) and 0x44b612 a struct copy (scope: a computed-pointer store outside them is not excluded) | `:42-47` | V MU8,MU9 |
| 0x94d438 = the faction's EFFECTIVE DIFFICULTY: the exact 6-insn branch `mov al,ds:0x985b10; test dl,al; mov eax,ds:0x985aec; jne 0x59eed6; mov eax,3; mov [esi+0x94d438],eax`, plus save-load 0x57ef57 (same 8380 fold) | `:48-50` | V MU10,MU14 |
| rivals dead: index is NOT `ds:0x985aec` (0 refs in the chain); 0x983a10 is NOT the faction array (decoded 0x8c vs 0x20bc); 0x57c606's index is NOT stored | `:51-58` | V MU7 |
| ACCEPT `m338_diff_readers.py` -> `PASS M338: 8/8` `1ae1563d47d0039e` x2 (sha256 288a0edc); harness 16/16 `56455db0eadbedd7` (`evidence/m338_mutate.txt:18`), ST 3/3; review #357's 10 findings all fixed IN the gates | `:59-67` | V |
| OPEN: the +0x20 index is UNCLAMPED (a HoF byte >=6 reads past `0x94d2c4`); FUN_0058e7f0 admitting a pref >=6 is now ANSWERED by M340 (ADMITTED, 7/7); 0x44a1c8's window is the HoF screen INFERRED | - | lead |

## M340 (s320-chain1, pick (x6) residual = M338's #1 lead, STATIC 7/7, review #358 hardened) — FUN_0058e7f0 ADMITS a `Difficulty` pref >= 6: no bound anywhere in the read -> parse -> store chain, so index 6 reaches `0x94d2c4`, one dword past the six-row ladder — `evidence/m340_pref_admission.txt:79-90`

| claim | evidence | conf |
|---|---|---|
| 18 `call edi` sites, each with a 6-push window holding exactly one `push 0x100` (argc-6); exactly ONE key 0x692718 = PE `"Difficulty"` (0x58e8a1) whose lpDefault push IS 0x997120, the itoa(0) buffer seeded at 0x58e865; its store `ds:0x92bde8` @0x58e8c6 is the ONLY store to that cell in the function | `:3-8` | V MU1,MU10,MU11 |
| 0x58e8a9..0x58e8c6 is 10 straight-line insns (0 jcc/jmp/ret) with the two stores `ds:0x996be8,eax` (cursor) and `ds:0x92bde8,eax` | `:6-18` | V MU2,MU7 |
| the stored eax IS 0x6287e2's return: 0x58e8b9 calls 0x5ea484 -> 0x5eaa53 -> {0x5ea985, 0x6287e2}; both wrappers are branch-free, write no eax after their call and end pop ebp/ret; 0 eax writes between the call and the store | `:19-21` | V MU2,MU3,MU9 |
| the parse chain (atoi 0x64c360/0x64c460, tokeniser 0x5ea985, radix 0x6287e2/0x628720/0x62876b) compares CHARACTER CLASSES only: constants {0x0,0x1,0x2b,0x2c,0x2d,0x30,0x31,0x36}; intersection with {2,3,4,5,6} EMPTY | `:22-42` | V MU4,ALG1 |
| POSITIVE CONTROL, same function: `Language`'s consumer 0x628130 puts the argument in [ebp-0x4], `cmp [ebp-0x4],0x4`, `ja 0x6281a8`, then indexes `[edx*4+0x6281ac]` — bound 4 there, NONE on the Difficulty path | `:44-58` | V MU5 |
| endpoints MEASURED from the ladder loader 0x57ac74/0x57ac88 (base 0x94d2ac, end 0x94d2c4) and 6 rows from 0x57c6cb `cmp esi,0x6`; k=5 -> 0x94d2c0 last legal, k=6 -> 0x94d2c4 | `:61-65` | V MU8 |
| the three pref-fed readers 0x48678f / 0x44a1c8 / 0x599405 load TABLE at scale 4 from a memory-loaded index whose def-use gap (0/0/2 insns) holds no branch, call, compare or rewrite | `:67-76` | V MU6 |
| ACCEPT `python3 -u scripts/m340_pref_admission.py` -> `PASS M340: 7/7 gates`, rows `1cc44d0146a8b419`, census `a7bb50fde374ddca`, window `1ff9a31080ec2e22`, 2 runs byte-identical; `scripts/m340_mutate.py` -> `PASS HARNESS M340: 12/12`, 7/7 gates covered, NO-OP `[]`, `a2a1726721114b4d` | `evidence/m340_mutate.txt:16` | V |
| OPEN: what the runtime dword AT 0x94d2c4 holds (a box read); whether any other writer of the 0x92bde8/0x985aec pair (0x57c7b0 writes both in one breath, source untraced) supplies a bounded value | - | lead |

## M339 (s320-chain2, pick (x6) "callee 0x5f1394", STATIC 7/7, review #359 hardened) — 0x5f1394 = the modal SCREEN RUNNER; its return is the screen OBJECT's `+0xa40` result cell, and the difficulty dialog writes that return into `ds:0x985aec` + all 8 faction blocks — `evidence/m339_modal_runner.txt:1`

| claim | line | kind |
|---|---|---|
| FUN_005f1394 = 11,207 B span / 2,235 insns (gap histogram 2220x0 + 14x3 = the objdump byte-column wraps, no overlap); `ret 0x8`, args read = only `[ebp+0x8]`/`[ebp+0xc]`; SEH `0x66f786`, `sub esp,0x38c`, first call `[vtbl+0x170]`@0x5f13c6 whose 0 -> `or eax,-1`; vtable lane {15c,160,164,16c,170}; window create 0x5e3ed9's error returned verbatim | `:1`, `:42-43` | V MU1,MU2,MU9 |
| 7 exits, all jumping to the ONE SEH-restore label (no jump skips it): -1 x2, 0 x1, passthrough x2, `ds:0x698d0c` x1, `[obj+0xa40]` x1; the two passthroughs are TRACED to their feeder calls `[vtbl+0x15c]` and `0x5e3ed9`; +0xa40 read ONCE / written 0x, +0xa44 never read | `:43-44` | V MU3,MU7,ALG_A1 |
| 94 direct thiscall sites, exact receiver census: 76 `lea ecx,[ebp-…]` (screen object = a caller frame local), 14 pointer slots, 3 register, 1 global `0x9210a8`; none without a receiver | `:45` | V MU4,MU10 |
| FUN_004ddaa0 seeds `ds:0x985aec` into obj+0xa44 (0x4ddb3e/4d, the store ADJACENT to the call, receiver = the same lea 0x4ddb47), `call 0x5f1394`, `test eax,eax`/`jge 0x4ddcf1`; there `mov ds:0x985aec,eax` (no eax write in between) then `mov [ecx],eax` + `add ecx,0x20bc` + back-edge `jl 0x4ddcfb` from 0x94d438 to 0x95da18 = 8 iterations => the return IS the new effective difficulty of 8 factions | `:46` | V MU5,MU6,MU8,MU11,MU12 |
| rivals dead: "the runner is the chooser" — 0 refs to 0x94d2ac/0x985aec in 2,235 insns vs 3 in FUN_004ddaa0's own extent; "return is a dialog ID" — its only IMMEDIATE returns are -1 and 0 | `:47` | V MU7 |
| ACCEPT `python3 -u scripts/m339_modal_runner.py` -> `PASS M339: 7/7` `d76a5e83770b77bb` x2, `text_sha256=eb9f463e…` (`evidence/m339_modal_runner.txt:49-50`); harness `m339_mutate.py` 13/13 `927a1c66c322709e`, `--selftest` 3/3 | `evidence/m339_mutate.txt:17` | V |
| OPEN: the writer of `[screen+0xa40]` (outside the runner and outside FUN_004ddaa0); call site 0x57dd45 pushes ONE dword against `ret 0x8` (frame restore tolerates it); the MFC `DoModal` identity is INFERRED from shape only | - | lead |
