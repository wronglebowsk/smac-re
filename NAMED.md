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

## B30 (ROTATED) - see `docs/named-archive-b32-rows.md` — spine §B30; ACCEPT `python3 -u -m sim.selftest --b30` `PASS B30: 6/6` `234ab3d83a88dbea`, harness 10/10 `76a481b5d8a7d8b0` (`evidence/b30_facility_completion.txt:35-36`).

- CONTAINER-DRIVEN run (G1): 18 records, own player 3, 2 eligible, target 0 'University Base' item 2 — `evidence/b30_facility_completion.txt:2,22` — V MU6.
- SETTER == reader inverse over the 32-id window (32/32 round-trip, id 39 refused); swapped rival 4/32 — `:23` — V MU1/MU2.
- the write is ONE byte: diff `[140]`, delta 4, inside `+0x8c..+0x8f` — `:24` — V MU1.
- writer round-trip: identity build byte-identical, 1 offset, reload `[1,2,8]`, 17/17 others — `:25-26` — V MU3/MU5.
- the bill moves by the DERIVED table (delta 1, 0 mismatches); 'table value' rival differs at `[8]`; G6 runs it twice — `:27` — V MU4/ME3/ME4.
- the stamper was ASSUMED here - QUALIFIED by `## M342` (inline `or` @0x4f0ec0) and by `## B31`/`## B32`: the recorded run has no facility-positive case, and the UNIT twin stamps 4/4 where the facility twin stamps 0/2 — `evidence/m342_completion_setter.txt:190`, `evidence/b32_unitoracle.txt:25` — V (M342/B32).
- OPEN: other real-completion effects (pop order beyond B11, storage/mineral reset, messages); ids 39..71 — - — lead.

## B31 (s324 BUILD, zero box) — the game's own 10-boundary run is the COMPLETION ORACLE: 6 facility-bit gains / 2 losses, the rule "the queue head id is the bit that appeared" scores 0/6, and Korolev r0 replays to st 0 with NO stamp (`sim/facoracle.py`; spine §B31). ACCEPT `python3 -u -m sim.facoracle` -> **`PASS B31: 16/16 gates`**, rows `ce7688c0cb3b5f9d` oracle `7afda4dd49566fb4` score `9a4f2c466f3d18b7` img `fb0bc0caa186b766` (`evidence/b31_facoracle.txt:63`), 2 runs identical; harness `python3 -u scripts/b31_mutate.py` -> **`PASS HARNESS B31: 12/12`** digest `087e1d0228debbe9` (`evidence/b31_mutate.txt:14`). NAMED cap: B24 rotated VERBATIM to `docs/named-archive-b31-rows.md:5`, sha1 `6bb8d2c5c2114bbc6e333ff2665bda8c50cfa1d6`, `scripts/b31_named_rotate.py --verify` ok.

| claim | evidence | conf |
|---|---|---|
| the oracle is the RECORDED run read from bytes: 10 before + 10 after samples, 407 base-records, every bitmap decoded from its own `+0x8c..+0x8f`; counts and digest pinned, deltas compared only with the ADJACENT sample (0 skipped) | `evidence/b31_facoracle.txt:4`, `evidence/b31_facoracle.txt:60` | V MU1/MU9 (G7 red) |
| the recorded bitmaps are NOT monotonic — 6 gains, 2 losses at 6 changed samples; the decoded delta equals the RAW XOR popcount at every changed sample (independent paths), and every changed byte lies in `+0x8c..+0x8f` | `evidence/b31_facoracle.txt:15-16` | V MU7 (losses dropped) / MU11 (a gain dropped → G2 red) |
| "the queue head id is the bit that appeared" FAILS: 0/6 matches, 5 heads unit-encoded (negative or >31), the one in-window head (Virgin Soil, 2) did not stamp | `evidence/b31_facoracle.txt:26` | V MU2 (head offset → G3 red) |
| Korolev r0 IS the anchor (r==0, st 8, head 2, pending 1, price 9, add 1 pinned): spend `8+1-9=0` == the recorded after, head id 2 inside the facility window, and the recorded bitmap does NOT move — the stamp is NOT a function of the paid pop; the type gate is OPEN | `evidence/b31_facoracle.txt:34-36`, `evidence/b31_facoracle.txt:38` | V MU3/MU5/MU12 (price or stamp drift → G4a/G4e/G4f red) |
| pop-first (reading the head AFTER the pop) stamps the NEXT item: on the declared 2-deep fixture it writes 6, the measured order writes 2 — M344's spend→stamp→pop order is load-bearing | `evidence/b31_facoracle.txt:40` | V MU6 (G4d/G6c red) |
| the writer carries an ARBITRARY bitmap including a LOSS of 8 (the OR-only setter cannot express it): 2-byte diff, reload `[1,4]`, identity build byte-identical, the other 17 records untouched | `evidence/b31_facoracle.txt:46` | V MU8 (write shifted → G5 red) |
| QUALIFIES `## B30`: B30's setter was ASSUMED; this run measures no positive completion case and one recorded NEGATIVE at a facility-range head, so "a paid queue item becomes a facility" is UNVERIFIED against the game's own run | `evidence/b31_facoracle.txt:35-36` | V MU5 |
| CLOSED by `## M349` + `## B32`: the unit-id decode is head<0 = negated TYPE and a unit completion stamps its mapper bit (4/4); STILL OPEN: a FACILITY completion stamps nothing on this run (0/2) and which loss is a raze vs an identity change | `evidence/b32_unitoracle.txt:25` | V (B32 MU3) |

## B22 (s273, BUILD 12/12, zero box; post-Greptile #286: one P1 arithmetic error retracted, the falsifier made load-bearing) - BOTH save record arrays grow in ONE writer call, and the CREATE leg demonstrably reads its ARGUMENTS out of the reloaded image (sim/composedgrowth.py)
| claim | evidence | conf |
|---|---|---|
| ONE WRITE GROWS BOTH ARRAYS: image +1572 B = 5x304 (bases) + 52 (one unit) over the untouched save, vs B21's bases-only +1520 B. The writer's layout is MEASURED band by band, `[unit originals 3484][the ONE new unit 52][base originals 5472][the grown bases 1520][tail 10800]`, every band byte-equal to its own source (the rung's first draft claimed one uniform lift - FALSE) | `evidence/b22_composedgrowth.txt:8` | V |
| THE SHAPE LOCATOR CANNOT SEE A FOUNDED BASE: on every grown container `sim/save`'s scan CONFIRMS ONLY the 18 NAMED bases of the header count's 23, because M282's founders write an EMPTY name span and `_base_ok` demands `[ -~]{3,30}\x00` at +19 - a grown base is locatable by COUNT, never by SHAPE. It costs the locator nothing, because `units_off` is DERIVED back from `bases_off` | `evidence/b22_composedgrowth.txt:6,9` | V |
| COUNT AND SHAPE AGREE EXACTLY on all three containers (`bases_pred == bases_off`, `closes` True on orig/B21/B22; the base array moves +52 B, the unit anchor does not). RETRACTED here: this run first claimed a 52-B DISAGREEMENT, which was its own arithmetic (a 68-unit count applied to a 67-unit image) and not the file's geometry - Greptile P1 on #286 | `evidence/b22_composedgrowth.txt:9` | V |
| INBOUND HALF OF THE ROUND-TRIP (the rung's point), through ONE shared producer `record_from_image`: the B12 CREATE leg's tile AND faction come out of the RELOADED image's 304-B base record (base[22] at (27,29) fac 1); FALSIFIER - corrupting tile AND faction IN THE IMAGE (1447,1448, fac 5A) makes the created unit CARRY those bytes | `evidence/b22_composedgrowth.txt:7,13` | V |
| THE FALSIFIER IS LOAD-BEARING, proved in-process every run: rebinding the shared leg to read the MODEL instead of the image makes G9's record collapse back onto G3's (the model's own 27,29 fac 1) while the real leg on the SAME corrupted image carries the bad bytes; G3 is DECLARED blind to that mutation (model tuple == container tuple in this fixture) | `evidence/b22_composedgrowth.txt:15` | V |
| HEADER DIFF IS EXACTLY 3 BYTES (0x44 units dword -> 68, 0x48 bases dword -> 23, 0x54 year word -> 2180), all inside modeled spans. 4 was the DECORATED guess ("one per modeled field") - cur/tf already hold their recorded values in this save | `evidence/b22_composedgrowth.txt:11` | V |
| RE-PARSE CLOSES THE CHAIN: n_units 67->68, n_bases 23, the 67 original unit records byte-identical, the new record AT THE ARRAY END, `units_off` unmoved / `bases_off` +52 B / tail +1572 B, parsed x/y/type/owner == the base tile read from the first reload | `evidence/b22_composedgrowth.txt:12` | V |
| RIVALS FAIL THE SAME FIT: growing ONLY the unit array re-derives n_bases 18 and loses the 5 grown records (242591 B != 244111); the idle order-2 record is NOT the produced record; a perturbed unit stride mis-places the tail (244245 B != 244111) | `evidence/b22_composedgrowth.txt:14` | V |
| ACCEPTANCE `python3 -m sim.selftest --b22 programs/saves/m54b_clean.SAV` -> **PASS B22: 12/12**, exit 0; `python3 -u -m sim.composedgrowth` prints the SAME 12 labels (`--b22` only relays the module's claims); two runs byte-identical (report digest, written image sha256 f7d90eb77ca7abac) | `evidence/b22_composedgrowth.txt:15-20` | V |
| UNMODELED (declared): WHICH base really ran the completion (the m289 trace tracks only year/cur/tf/ledger; the base is CHOSEN as the last surviving founding - a fixture); the created record's unmodeled bytes (zero + named fields, as B12); the founding's economy/research/units and the queue's per-turn progress | - | lead |
## B23 (s280, BUILD 11/11, zero box) - the production queue's PER-TURN progress round-trips through the writer at every recorded boundary, and a corruption that lands ONLY in the container changes the fold's LATER verdicts (sim/composedturn.py)

| Claim | Evidence | V |
|---|---|---|
| Seed (the trace's r0-before Korolev record as a GROWN 19th base) + all 18 originals round-trip the writer; queue spans equal | `evidence/b23_composedturn.txt:1` | V |
| Every boundary's visit inputs are READ FROM THE IMAGE (st/pen/slots == recorded round_before spans, 10 boundaries) and every result WRITTEN BACK | `evidence/b23_composedturn.txt:2` | V |
| Verdicts pay r0 only (p,b x9); storage+mirror parity vs recorded afters 10/10+10/10; slot parity 100/100 dwords with the stale [2,2,2,2] tail kept | lines 3-5 | V |
| M58 pop visibility: container shows popped pending at the NEXT before-sample; 9/9 after-parities elsewhere | line 6 | V |
| r0 arrival = LAST unit record, byte-equal to B22's image-fed producer (n_units 67->68); image grew exactly 304+52 B; the writer REFUSES 9- and 11-slot queue lists (an 11th would write +0x78 past the queue - Greptile P2 on #297) | lines 7-8 | V |
| CREATION SOURCE is the container: tile+owner poisoned in the SEED BYTES at r0 land in the created record (1447,1448,0x5a); a frozen-args variant (args pinned to seed-open values) FAILS the same fit (Greptile P2 on #297) | line 11 | V |
| 5 rivals fail the same fit (noadd, price10, nopop, zerotail, nomirror) - each reddens its own law's gate | line 9 | V |
| FALSIFIER: st:=20 poisoned in IMAGE BYTES at r1 only -> container fold pays at r1 AND r2 (poison persisted through the written image), model-fed fold blind -> container consumption is load-bearing | line 10 | V |
| Two runs -> identical FULL table (labels+verdicts+DETAILS, Greptile P2 on #297) + image sha256 e685d297e3d246eb; acceptance `python3 -m sim.selftest --b23 programs/saves/m54b_clean.SAV` PASS 12/12 | line 12 | V |
| savewriter gained identity/raw/queue override keys (backward-compat; B8-B12/B21-B22 calls unaffected - their relays green) | `sim/savewriter.py` | V |

UNMODELED (declared): visit-time d0 (+0xd0) and price = recorded data as inputs
(M57/M58/M72 law); recorder pop-visibility law used as recorded; +0x30/+0xd0
container spans not claimed (f30&2 never set in any sample).
QUALIFIED BY B24 (s287): `fold()` in this module is now PARAMETERIZED - new hooks `overrides_fn / d0s / price / seed_rec / slot_i / prior_units / start_img / passthrough`, every default reproducing rung B23 exactly. Verified, not asserted: B24's G1 replays B23's own acceptance in-process 12/12 and `evidence/b23_composedturn.txt` regenerated byte-identical at this head.
## B24 (s287, BUILD 9/9, zero box; mutation-tested 9/9 + 1 declared NO-OP) - the composed LIVE run: the QUEUE/visit leg operates on a record the FOUNDER leg wrote into the container in the SAME run, addressed BY LEDGER POSITION, and destroys run in the image (`sim/composedlive.py`). FULL ROWS VERBATIM at `docs/named-archive-b31-rows.md:5` (moved by `scripts/b31_named_rotate.py`, sha1 `6bb8d2c5c2114bbc6e333ff2665bda8c50cfa1d6`); this stub governs, one line per claim, same cites.

| claim | evidence | conf |
|---|---|---|
| THE QUEUE LEG CAN VISIT A BASE THE FOUNDER LEG WROTE IN THE SAME RUN: m289's 7 FOUND + 2 DESTROY applied to the base array IN THE IMAGE; the visited record is founded at t22, its 8 visits run t22-t29, 3 completions, image `n_units` 67->70 | `evidence/b24_selftest.txt` G2/G3/G6; `evidence/m289_gdb_raw.log:327,471,568,590,929,1001,1194,1251,1651` | V (composition) / OPEN (that the GAME founds the (27,29) record - the seed span is a declared fixture) |
| ADDRESSING LAW: the fold reaches that record by LEDGER POSITION 22 (`[22]*8`), never by tile - tile-addressing is IMPOSSIBLE once the container's tile bytes for that slot are rewritten, and `mode=locate` cannot be settled on the uncorrupted leg | `evidence/b24_selftest.txt` G8 | V |
| FALSIFIER bites: tile/owner corrupted IN THE IMAGE from visit 6 -> the THIRD arrival carries (1447,1448)/owner 0x5a while the image's first two unit records stay clean; the model-fed fold is blind | `evidence/b24_selftest.txt` G7 | V |
| 2nd falsifier shape: storage poisoned at ONE read moves the verdict table `b,b,p,b,p,b,p,b` -> `b,b,p,b,p,p,b,b` and completions [24,26,28] -> [24,26,27] | `evidence/b24_selftest.txt` G7 | V |
| PRE-COUNT FIDELITY: ops apply by their logged pre-count 9/9; image `n_bases` == ledger at 0/30 mismatched turns | `evidence/b24_selftest.txt` G2 | V |
| DESTROYS/COMPACTION run in the image: ops at idx [3,8] remove slots 20 (t19) and 23 (t29), NEVER the visited 22; array -304 B each; a skipped-destroy ledger would leave 304/608 B | `evidence/b24_selftest.txt` G4 | V |
| RETRACTED (authored draft, spine corrected at 981570f): the turn-29 compaction does NOT move the slot the fold addresses - the slot is stable at 22 for all 8 visits; compaction removes the array's LAST slot | `evidence/b24_selftest.txt` G4 | V |
| `frontinsert` and `locate` RETIRED as rivals - each measured PASS on this driver, so neither can fail (trap 24); G8 asserts the retirement (`clean arrivals` pinned) | `evidence/b24_selftest.txt` G8 | V |
| ACCEPTANCE `python3 -u -m sim.selftest --b24` -> `PASS B24: 9/9 gates`; `python3 -u -m sim.composedlive` -> clean image sha256 fddf0062740c9cfc; harness `python3 -u scripts/b24_mutate.py` -> MU1 {G3,G7}, MU2 {G3,G7}, MU3 {G7}, MU4 {G4,G5,G6,G7}, MU5 {G7}, MU6b {G8}, MU7 {G5,G6,G7,G8}, MU10 {G9} all = declared, MU8 = declared message-matched crash | `evidence/b24_selftest.txt`; `evidence/b24_mutate.txt` | V |
| MU2's FIRST anchor reddened NOTHING (the driver's per-turn write re-composes from the container's bytes); replaced by the write-side anchor `ent["raw"] = bytearray(target_raw)` | `scripts/b24_mutate.py` comment | V |
| OPEN: the queue content ON the founded base (the log records fac/x/y/cnt only - the seed span is a declared fixture); real income/price during t22-t29 (`D0_DECL`/`PRICE_DECL` are fixtures) | - | lead |

## M311 (s274, STATIC, zero box; mutation-tested 15/15) - `ds:0x68cbb0` is the CURRENT-RECORD INDEX of the 304-B entity array; `ds:0x8f0d60` is its derived record POINTER, written in lockstep — FULL-LENGTH ROWS VERBATIM at `docs/named-archive-m311-rows.md` (moved by `scripts/m327_named_rotate.py`, sha1 `0b12d45d08a4`); this stub governs, one line per claim, same cites

| claim | evidence | conf |
|---|---|---|
| THE INDEX: exactly 6 stores (`0x4e3476`, `0x4e4dd0`, `0x4efe8e`, `0x4f21e0`, `0x4f5a7c`, `0x4f5c36`), all `mov ds:..,reg`; cache split 6 writes / 16 tests / 318 reads = **340** refs (= `name_global.py`'s count); the field IS compared (`0x40CED9`) → no read-only-cursor claim | `evidence/m311_recidx.txt:11,33,39,60` | V |
| THE POINTER: exactly 6 stores, 1:1 pairing — each 6-25 B after exactly one index store, none unpaired either side, same 4 functions | `evidence/m311_recidx.txt:14-20,50,56` | V |
| STRIDE LAW in the encoding: `lea d,[n+n*8]`; `lea e,[n+d*2]`; `shl 0x4` = **304n** then `+0x95da10`; exact triplet pinned at all 5 folding sites (n=1:304, n=2:608) | `evidence/m311_recidx.txt:23-29,57` | V |
| 5 of 6 selection sites RECOMPUTE the address; `0x4f5c36` is the exception, storing a SAVED pointer from `[ebp-0x8]` (`0x4f5c33`) | `evidence/m311_recidx.txt:58,34-49` | V |
| THE TWO DEFERRED PICKS ARE ONE OBJECT: "304-B table at `0x95da40` bit 0x20" = `0x95da10 + 48`, field +48 of the same record (`0x4f5aab`); `0x95da10` in 310 insns, `0x95da40` in 96 | `evidence/m311_recidx.txt:30,59` | V |
| THE SETTER `FUN_004e3470`: arg→index, fold, fold→pointer — 34 B / 11 insns / **57 callers**, all read from `ghidra_out/index.csv` by the printing gate | `evidence/m311_recidx.txt:61` | V |
| NOT AN INVARIANT, MEASURED: `ds:0x68cbb4` stored **22**×, only **3** in an index window → pairing claimed for the pointer, REFUSED for it (CLOSED by M315: the refresh memo of `call 0x4e8d60`+`call 0x4e78e0`) | `evidence/m311_recidx.txt:62`, `evidence/m315_bb4_census.txt` | V |
| ACCEPTANCE `python3 -u scripts/m311_recidx.py` → **PASS 8/8**, 2 runs byte-identical, digest `625cd5877271cd85`; `scripts/m311_mutate.py` → **15/15** (MU1 fold width, MU2 transcribed store, MU3 census under-count, MU4 mis-transcribed triplet, MU5 wrong base, MU6 rewritten insn, MU7 wrong pointer addr, MU8 refused pairing, MU9 decoration constant, MU10 blind write-detect, MU11 caller count) | `evidence/m311_recidx.txt:64-65` | V |
| MATCHER CLAUSES, MEASURED (A8): only the window's RIGHT reach changes results (`0x4e4dd0`'s fold sits 78 B past the store: -24/+32→0, -24/+90→1); the `*8` operand-equality clause and 24 B proximity cap are **DECLARED INERT** — two earlier prose claims that they were load-bearing RETRACTED in the gate text | `evidence/m311_recidx.txt:53-58` | V |
| UNPROVEN, DECLARED: the index VALUE reaching the fold's 2nd step is not established (no write tracking; a register-name rule would be FALSE at the setter) → claim stops at the arithmetic shape | `evidence/m311_recidx.txt:58` | V |
| UNMODELED: which entity the index addresses in play; record +48's semantics; `0x68cbb4`'s 19 extra writers; who fills `[ebp-0x8]` behind `0x4f5c36` | - | lead |
## M312 (s276, STATIC, zero box; mutation-tested 23/23) - ROTATED VERBATIM to `docs/named-archive-m354-rows.md` (sha1 `5e8df0971a3d`) - the selection check (FUN_00470b90, M310) has TWO firing trunks; the forwarder's invalidator tail is UNREACHABLE from every caller; the pair is the cursor-tile neighbourhood

| claim (one line each; full rows in the archive) | evidence | conf |
|---|---|---|
| THE RETRACTION | `evidence/m312_goal_callers.txt:11,12,16` + `evidence/m312_mutate.txt:7,8,13` | V |
| TRUNK A (cursor) | `evidence/m312_goal_callers.txt:13,14,17,18,19,22,23` + `evidence/m312_mutate.txt:9,10,11,12,13,14,15,16,17` | V |
| VIEW-INSTANCE FAN-OUT | `evidence/m312_goal_callers.txt:24` + `evidence/m312_mutate.txt:18,19` | V |
| THE CENSUS LIMIT (Greptile P2 on #292) | `evidence/m312_goal_callers.txt:25` + `evidence/m312_mutate.txt:20,21` | V |
| TRUNK B | `evidence/m312_goal_callers.txt:26,27` + `evidence/m312_mutate.txt:22,23,24,25` | V |
| OPEN (pick) | - | lead |
## M313 (s278, STATIC, zero box; mutation-tested 23/23) - ROTATED VERBATIM to `docs/named-archive-m313-rows.md` (sha1 `b674876b9a74`) - pick (i') CLOSED: the events are TWO command pumps + one mouse handler, all wired to ONE interaction band; pumpA's door is a data pointer at 0x6724a8 inside a multi-table .text-pointer run

| claim (one line each; full rows in the archive) | evidence | conf |
|---|---|---|
| BAND LAW: both trunks converge on [0x50bb20,0x5175b4) - 20/28 + 9 owners, 8 off-band hub owners pinned, 53 sites by address list | `evidence/m313_event_map.txt:1-6` + `evidence/m313_mutate.txt:2,3,5` | V |
| THE PUMPS: FUN_00512b40 -> 8 in-band + 4 off-band; FUN_00516b80 -> 5 + 5 and (M314) also FUN_004d3f70 @0x517858; 7 + 6 hub sites by address | `evidence/m313_event_map.txt:7,8,9,10,12` + `evidence/m313_mutate.txt:6-9,11` | V |
| PUMPA = command dispatcher (byte map 0x5165ec + 8-slot jump 0x5165cc; VK map 0x516638 + 4-slot 0x516628); PUMPB = order-key `lea ebx-0x51 / cmp 0xc` + 13-slot table 0x5181d0 | `evidence/m313_event_map.txt:15-19` + `evidence/m313_mutate.txt:16-21` | V encoding / INFERRED meaning |
| PUMPA'S DOOR: FUN_0041bda0 has zero refs; a stored u32 at 0x6724a8 lies in a 490-pointer multi-class run at 0x672290 (f2e2c9dfae9ba011) - the word 'slot' retired | `evidence/m313_event_map.txt:13,14` + `evidence/m313_mutate.txt:12-15` | V entries |
| MOUSE PATH: map_click_handler FUN_00476580 calls 4 in-band members + 004739a0 - a map click reaches the goal check with no pump | `evidence/m313_event_map.txt:11` + `evidence/m313_mutate.txt:10` | V |
| PUMPB ENTRY: FUN_005186b0 has 0 call/jmp refs and exactly ONE stored u32 (imm32 of `push 0x5186b0` at 0x51892d in FUN_00518820, from init FUN_00580260) | `evidence/m313_event_map.txt:20,21` + `evidence/m313_mutate.txt:22-24` | V census / INFERRED install |
| CLOSED by M314: the 'dialog-family' census and FUN_004d3f70's band calls (exactly 1 band member, FUN_0050cab0 x2); GOAL game-meaning still open (M310) | `evidence/m314_tour_family.txt` | V |
this stub governs: one line per claim. Acceptance `python3 -u scripts/m313_event_map.py` -> **21/21**, digest 5e14170de426d127, x2 identical; `scripts/m313_mutate.py` -> **23/23**.
## M314 (s282, STATIC, 27/27) — FUN_004c5d60 = the token-keyed tour/dialog dispatcher (pick (i'') CLOSED).

FULL BLOCK VERBATIM at `docs/named-archive-m350-rows.md:7` (sha1 `decdd34b21f8dadbb475a7648efdca8bcf00f4d6`); these stubs govern nothing the archive does not carry — one line per claim, labels cut mechanically, evidence and confidence copied:

| claim (first clause) | evidence | conf |
|---|---|---|
| DISPATCHER… | `evidence/m314_tour_family.txt:1,2` + `evidence/m314_mutate.txt:2,3,4` | V |
| WRAPPERS 0x4c2e90/f00/f70/fe0 (112 B each)… | `evidence/m314_tour_family.txt:3,4` + `evidence/m314_mutate.txt:5,6` | V (census) / INFERRED (clamp role) |
| RESULT HANDLERS 0x4c5c40/ca0/cf0… | `evidence/m314_tour_family.txt:5,6,7,8,9` + `evidence/m314_mutate.txt:7,8,9,10,11,12,13` | V (bytes) / INFERRED (pane roles) |
| REGISTRATION… | `evidence/m314_tour_family.txt:10,11` + `evidence/m314_mutate.txt:14,15,16,17,25,26` | V |
| TOUR DRIVERS 0x4c3050/0x4c32f0/0x4c3540/0x4c3760… | `evidence/m314_tour_family.txt` (A2 family window) | INFERRED (semantics) |
| PUMP CORRECTION… | `evidence/m314_tour_family.txt:12,13,14,15,16,17` + `evidence/m314_mutate.txt:18,19,20,21,22,23,24,27,28` | V |

ACCEPT `scripts/m314_tour_family.py` 18/18 `cf54a7ca907344c6` x2; `scripts/m314_mutate.py` 27/27 (merged #299).
## M321 (s297, hardened at review #324) - pick (vi) CLOSED: the 2 unnamed memo owners are base STATUS-ICON emitters; the arrival test gates base_array field 56 bit 6

| claim | evidence | conf / mutant |
|---|---|---|
| FUN_004ee410 = base FOOD/POPULATION status emitter (7 `0x48f100` calls, sites pinned vs labels) vs FUN_004f41f0 = TALENT/PSYCH-REQUEST emitter; disjoint | `m321_memo_owners.txt:24-31` | V; MU13,MU19 |
| 4 memo sites per M319, fed by `mov R,ds:0x68cbb0`, whole refresh PAIR in pinned order 10-11 B after the store (claim <=25); **1** (not 2) is the a3 form; image-wide census: 8 index-fed memo stores in 6 fns, these owners hold 4 (agrees M319) | `:18-22` | V; MU1,MU2,MU7,MU8,MU14,MU15,MU21 |
| ONE arrival predicate at 3 sites: per-write base identity `ds:0x8f0d60`, `je` pinned (targets + call on fall-through), +0x78/7c/80 zeroing PROVED (xor esi,esi @0x416f01); callee re-gates @0x4f43a0 `cl,0x40`, chain pinned | `:33-36`, `:81` | V; MU3,MU9,MU10,MU16,MU17,MU18,MU22 |
| field = base_array +56 (fold = 304*idx+0x95da10; 52-chain rival dies on the printed histogram 646 vs 565); bit 6's only OR-setter = 0x41ac34 (FUN_0041a8f0's `ds:0x99aa38` round trip) — **M329 REFINES (s307)**: that round trip is the Governor-options pane packing a 19-bit policy record; it publishes ONLY `[rec+0x38] & 0x1f000000` (4 bits, `0x41abdc`), bit-disjoint from both faction-create defaults `0xdfbe41`/`0xc0dfbe41` (the two writes at `0x59ed6c`/`0x59ed7a`, `evidence/m329_scratchtree.txt:96-97`; **the s307 patch of this row wrote the second one as `0xdfbe01` — wrong constant, corrected at s308**), so the "personality" reading stands for the bits the pane never writes — and the pane also TESTS bit 6 (`0x41ade4`) as the arrival flag | `:2-3`, `:73`; `evidence/m329_scratchtree.txt:87-101` | V; MU5,MU6,MU11,MU20,MU4 NO-OP |
| OPEN: game nouns; 47 whole-dword field stores untraced to sources | - | lead |

22/22 mutants `evidence/m321_mutate.txt:24`; digest `f304cf871a971a3d` `m321_memo_owners.txt:84`.

## M328 (s304-chain2, STATIC 14/14, review #336 hardened) - 91c64c=turn-start ENERGY snapshot; 920434='multi' session flag; HURRY story closed

| claim | evidence | conf |
|---|---|---|
| A: 4 hits 2W/2R dw abs, 0 exact/lane/lea seeds; 52065d (520540) := ENERGY[8380*arg]; debt-pay(520605) < snapshot < interest(520743) pinned (linear order); HURRY mirror 41a551/41a563 | G1/G2 `evidence/m328_hurry_globals.txt:2,35,39` | V MU1-4,MU10,MU21,MU24,MU28,MU33 |
| A reader=INFRASTRUCTURE warn: E<100 pinned (cmp 0x64/jge); formula DERIVED 11E-10A (forward eval); no sub in post-snapshot window (clobber-aware) + 0 stores between upkeep calls; deadness INFERRED (deeper callees OPEN) | G3/G4 `evidence/m328_hurry_globals.txt:36-38,44-45` | V MU5-8,MU30,MU31,MU35 |
| B: 634 hits 15W/133T/486R 237 owners 0 seeds; {0x14,1x1} all mov; sole 1=57ed04 FIRST STORE of 57ecf0 (prologue pinned); 512b40 pair 0 via sole-def xor@512b63 (provenance pinned) | G5/G6 `evidence/m328_hurry_globals.txt:7,34,40-41` | V MU9,MU11-13,MU22,MU25,MU27,MU29,MU36 |
| B entry=menu case4@580070/auto-start 5229b7; no DIRECT B writer in SP 57c550/load fns (helper reachability OPEN); every lifecycle B-write measures 0 incl RESET 5a09ad; strings pinned | G7/G8 `evidence/m328_hurry_globals.txt:42,46-47,69` | V MU14-16,MU34,MU37 |
| B uncarried: blob [91f750,+ce0) ends B-4; 17 reg-dest freads resolved (runtime/stack/imm-above-B, none cover); opener 'multi' && B==0 fallthrough pinned -> opts 0x10c0; B!=0 -> diplo-send 584010 (546800:40); HURRY gate re-pin | G9/G10 `evidence/m328_hurry_globals.txt:43,48-67,68,70` | V MU17-20,MU23,MU32,MU38 |
| ACCEPT 14/14 digest 030a6fc12e4a7cd7 x2 (`evidence/m328_hurry_globals.txt:85-86`,`_rerun.txt:85-86`); harness 38 mutants (37 scored + 1 NO-OP) digest 36259eee0736d9c1 (`evidence/m328_mutate.txt:41-43`); ST 5/5 (`evidence/m328_mutate_selftest.txt:7`) | as cited | V |
| OPEN: B noun INFERRED 'multi' (menu label script-driven; MULTIMENU 692018 no push); SP-path noun INFERRED (DIFFICULTY/USERULES strings); ~~92bdf8 mode global~~ ANSWERED M332 (the win-INI pref cell "Top Menu"; read/write/pseudocode views agree); ~~+300 upkeep refund~~ ANSWERED M330 (spend accumulator, k=1/2 law V); ~~facprofile+4ec interest~~ ANSWERED M331 (rate%/100 on ENERGY, +508 bit14 gate) | - | lead |

## M332 (s311-chain1, pick (x2), STATIC 9/9) — `ds:0x985aec` is the RUNTIME MIRROR of the game's own `Difficulty` preference; its master `ds:0x92bde8` is the win-INI key `Difficulty`, read by FUN_0058e7f0 and written back by FUN_0058f0d0 (REFINES `## M308`). FULL-LENGTH TABLE VERBATIM at `docs/named-archive-m340-rows.md:5` (sha1 `3ef265e11aca`); this stub governs, one line per claim

| claim | evidence | conf |
|---|---|---|
| 68 refs to 0x985aec = 4 store / 40 load / 24 cmp / 0 RMW; cmp arms exactly {1,2,3,4} immediate AND exactly {ebx}, the ebx cmp unique at 0x4f9b5a; a byte-level LE scan of the .text cache finds the SAME 68 and 0 address materialisations. SCOPE (s312/#346 P1): a store through a runtime-computed register pointer is invisible to both scans | `evidence/m332_difficulty_census.txt:101` + G9.1 `:80-81` | V MU1-3,17,21 |
| store set exact {0x4ddcf1, 0x57c5af, 0x57c7b5, 0x57f006}, every one `a3 ec 5a 98 00` (moffs) | `evidence/m332_difficulty_census.txt:102` | V MU1-3 |
| 0x4ddcf1 has no fall-in; `jge 0x4ddcf1` at 0x4ddb5a takes callee 0x5f1394's eax (G9.2), 0 eax writes before the jge, 0 jump tables anywhere => M308's "0x4ddcf1 UNATTRIBUTED" CLOSED; 0x5f1394's own semantics OPEN | `:103` + G9.2 `:82-83` | V MU1-3,8,16,18 |
| clean-copy map among {0x92bde8, 0x985aec, 0x8f0c11, 0x8f0090} = 5 directions over 6 pairs, each pinned to site AND window (G9.4: 0 redefinitions, 0 writes between); no 0x985aec->0x92bde8 copy => direction is master -> runtime | `:104` + G9.4 `:87-93` | V MU2-7,14,19 |
| the pref table: 11 key-exclusive 6-arg profile reads in FUN_0058e7f0, an INJECTIVE name->field map, `Difficulty`@0x58e8a1 -> 0x92bde8@0x58e8c6, paired with the writeback load@0x58f11d; API identity measured (G9.5): 18 read / 8 write calls through `edi` == Ghidra's counts; 6/6 three-way names agree (s312 P2 correction) | `:105-107` + `:51-53`, `:68`, G9.5 `:94-97` | V MU4-15 |
| siblings the same map names: 0x92bdf4 = `Map Type`, 0x92bdf8 = `Top Menu`, 0x92bdec = `Faction` (what `## M328` called "92bdf8 mode global") | `:106-107` | V MU9,13 |
| RIVAL KILLED: 0x92bde8 is BOTH the end of the 4x0xd4 record array at 0x92ba98 (G9.6 reads the loops) AND a scalar pref cell (2 stores, 6 loads) - "sentinel only" fails on 0 stores | `:108` + G9.6 `:98-100` | V MU4,6,10,12,20 |
| ACCEPT `PASS M332: 9/9` digest(table) `d2691dc5abb39240` (`evidence/m332_difficulty_census.txt:110-111`); harness 20 scored + 1 NO-OP, digest `a9a944201849d026` (`evidence/m332_mutate.txt:25`) | both files | V |
| OPEN: the difficulty INDEX->label order is now ALPHA `#DIFF` file order (M335: 4=Thinker, 5=Transcend); the 0x8f0090 consumer is a player-record difficulty byte (M336); a pref >=6 is ADMITTED verbatim (M340, 7/7). Still open: 0x5f1394's semantics (chain 2), the other writers of the 0x92bde8..0x92bf14 block | - | lead |

## M331 (s310-chain2, STATIC 14/14, review #345 hardened) - block+2fc/+308 = upkeep INCOME siblings

| claim | evidence | conf |
|---|---|---|
| census 23→10(3W/7R)/7→4(2W/2R) STRIDE; feeders 4eacd9/4f5cb0; excl facprof+2fc×3, 997b20 heap, loader, OUT×6 | `evidence/m331_ledger_census.txt:36-37,54,87` | V MU1,2,5,6,10,18,19,21-23,30,33,34,36,43 |
| +2fc: phase-1 clamp(base_rec+0xd4,0,99999); owner spill-chain measured; interest +4ec %/100 bit14, facprofile id byte-tied | `evidence/m331_ledger_census.txt:59,65` | V MU3,4,9,11,26,34-36,40,44 |
| +308: per owned base Σ 8f0d40[k−1], k≠owner, +c0-gated; caller loop-index law; E+=base_rec+fc | `evidence/m331_ledger_census.txt:62` | V MU6,7,8,27,38,39 |
| +310:=+2fc; +30c:=+308−300+2fc: liveness+no-mid-branch V, save 8/8 corroborates; caps MIN(E/2,100net)≥50 / MIN(net,+1058) | `evidence/m331_ledger_census.txt:68,70,72` | V MU12-16,24,25,29,32,37,41,42 |
| readers 522b70/531df0/45a920/40e720-heap; carry; turnfn 0blk; reset 59ec90; scanners ALL-mnemonic+implicit-write aware | `evidence/m331_ledger_census.txt:74,76` | V MU17-20,28,32,41-43 |
| ACCEPT 14/14 digest 442270fd57be2b62 x2 (`evidence/m331_ledger_census.txt:90-91`, `evidence/m331_ledger_census_rerun.txt:90-91`); 43/43+1 digest 29061c567f9132fb (`evidence/m331_mutate.txt:48-50`); ST 5/5 (`evidence/m331_mutate_selftest.txt:6`) | cite | V |
| OPEN: income nouns; 4e9880; 8f0d40 law; +c0/+304; cap action; 920754 | - | lead |

## M330 (s307-chain2, STATIC 13/13) - block+300 = UPKEEP SPEND ACCUMULATOR

| claim | evidence | conf |
|---|---|---|
| 25->11 FIELD (4W/7R STRIDE)+2 arg-fed; 14 excl | G1/G12 `evidence/m330_block300_census.txt:2,31,64` | V MU12-14,17-19,28-30 |
| W={4f4962,52056d 0,52078f resid,59f26a reset}; refund 520714-78f: 985aec>3,x!=0: r=trunc(kx/3) k=1(==4)/2(>=5); E+=r,x-=r; magic 55555556; mask VACUOUS | G2/G4-6 `:43,45-51` | V MU1-8,25,26,32 |
| feeder 4f47f0 ROUND>1: v=[984d48+48*slot] (bits 95da9c); CONDITIONAL halving (owner-match +bit5 parity /2 else FULL); E-=v,+300+=v | G10 `:58-59` | V MU9,10,22-24 |
| entry zeroes +2fc/300/308/3f8; +310:=+2fc; +30c:=+308-300+2fc; carry (M324) vals=[0,1,1,0,1,0,1,1] | G7-9/11 `:52-57,61` | V MU8,11,15,16,21,27 |
| ACCEPT 13/13 digest 470d844054b1b101 x2 (`:67-68`,`_rerun.txt:67-68`); 31/31+1 digest cf85092dea6baa93 (`evidence/m330_mutate.txt:36-38`); ST 5/5 (`evidence/m330_mutate_selftest.txt:6`) | cite | V |
| OPEN: slot; ~~985aec~~ ANSWERED M332 (runtime mirror of the INI pref "Difficulty", master 0x92bde8); ~~+2fc/+308~~ ANSWERED M331 (income siblings); profile+300 | - | lead |

## M326 (s301-chain2, STATIC 10/10, review #332 hardened) — FULL rows VERBATIM at `docs/named-archive-m338-rows.md:7` (§rotation-1 marker at `:6`, s319-chain2 headroom rotation, sha1 `a882ee40851d` — the region is bounded by its own terminator line and its digest is re-asserted by `scripts/m338_named_rotate.py --verify`); this stub governs. block+224 = the per-faction DEFERRED HURRY-PRODUCTION PAYMENT (energy debt), settled at upkeep; hurry defer-vs-pay flag chain 920434&91c62c, readers = AVAILABLE (220-224), reset 59f0bf/c1, save carry [0]*8.

## M325 (s299-chain2) - block+220=faction ENERGY; turnfn writes none; MIN feed (M324 MAX retracted)

| claim | evidence | conf |
|---|---|---|
| 234 disp hits (54W/180R; 0 ABS/+220/sub) +30seeds->20regW/7regR; 74sites/34owners; 45P/29U | G1-G3 `evidence/m325_block220_census.txt:289-291` | V MU2-4/14-17/20/22/29/30; M326 subreg-fix: 29 labels BLKCONST->STRIDE, pins/totals unchanged (`evidence/m326_block224_census.txt:32`, `evidence/m326_m325_seedcheck.txt:4`) |
| 51f320: 16 st/0 str/0 blk; ROUND@51f53c YEAR@51f54f | G4 `:292` | V MU1/20/21 |
| ENERGY: EDITORENERGY@68c938: field<-g999fa4@4e0336; caps 9999999/999999999/99999, -1000@5085c0, reset0@59eef3 | G3/G5 `:291,293` | V MU5-8/23/26/27 |
| MIN derived (jle-skip@44262b); g999fa4=cheat-chain value (parse INFERRED); EDITORYEAR 4e0350 round=max(1,·-2100); **g999fa4 is element 0 of a 10-dword band whose only INDEXED writer is 0x626597 (M353: `evidence/m353_numeric_band.txt:76`)** | G6 `:294`; M353 G2 `evidence/m353_numeric_band.txt:76` | V MU9-13/18/22/25/28; M353 MU2/MU10 |
| save blkA@32c [10,28,112,69,229,60,102,37] <2100; R1-3 DEAD | G7/G8 `:295-296` | V MU18/19/20/25 |
| ACCEPT 8/8 digest a623181d7fb68263 x2 (`:297`); 30/30 (1 NO-OP) digest 97c193e12593c95e (`evidence/m325_mutate.txt:34`); ST 4/4 | cite | V |
| OPEN: ~~+224~~ ANSWERED M326; ~~+300~~ ANSWERED M330; MIN consumers; 920774; 519b00; 673b60; T9 | - | lead |

## M324 (s296-chain2, STATIC 8/8) - ROUND RAW-carry; re-derive DEAD

| claim | evidence | conf |
|---|---|---|
| hdr RW 59688a/596883->985ab8 sz31c; ROUND=blob+44 YEAR+48; sole imm carrier (heap decl) | G1/G2 `evidence/m324_save_carry.txt:82-83,63` | V MU1/MU2/MU3/MU24 |
| blk+220 8/8: 596a91->94d430 sz105e0=8*20bc; fac1436 596ed6->927590 sz2ce0 | G1/G3 `:82,84` | V MU4/MU4b/MU5 |
| pfx12; @50=50 @54=2150 @44=67 @48=18 @310=9; sha=M302 | G5 `:86` | V MU8/MU9 |
| g999fa4 W={442642,626fd7}; fold [this+a24]*20bc+[94d650] ~~MAX~~ **MIN** (jle skips store; direction RETRACTED by M325 G6); uncarried; 0call/0AT; =cheat-parsed number (M325); **W set SUPERSEDED by M353** (+ scaled 0x626597, `evidence/m353_numeric_band.txt:76,84`) | G4 `:85,70-78`; M325 `:294`; M353 G2/R1 `evidence/m353_numeric_band.txt:76,84` | V MU6/MU14/MU16/MU21; M325 MU9-13; M353 MU2/MU10 |
| direct closure 440, 0 writers; 4e0350 callers {514ecf,517e3a} out; mode0; entry-first; M272 inv9 | G6/G7 `:87-88,79` | V MU7/MU20/MU22 |
| R1/R2 DEAD; esi0@5a0fd3 | G8 `:89` | V MU7/MU8/MU17/MU19 |
| ACCEPT 8/8 digest 700b4133f62bd714 x2 (`:100`,`_rerun.txt:100`); 28/28+1 5c3fa2bceb490009 (`m324_mutate.txt:29-30`) | cite | V |
| OPEN: ~~block+220 noun~~ ANSWERED M325 (ENERGY); ~~g999fa4 noun~~ cheat number M325 (64c360 thunk body open); feed arrival (.rdata 0x673b60 entry, M325); byte-swap/heap | - | lead |

## M323 (s295-chain2, STATIC, 13/13, 31/31+1) - ds:0x985afc=ROUND counter; year=round+2100

| claim | evidence | conf |
|---|---|---|
| 336 refs W5/T59/R272/A0; dw333/w1 (mov ax @59c18a)/b2; gaps 4f3a91/51da30 | G1/G6/G9 `evidence/m323_round_census.txt:523,528,531` | V MU1/MU18/MU19/MU23/MU31 |
| writers: 5a0fa0=0; 51f320=+1; 4e0350=max(1,g999fa4-g92bf68)+flow; 59ce10=rand{30,60,80} gated 985ac4.7 | G2/G3/G10 `:524-525,532,340-348` | V MU2/MU3/MU13/MU18/MU20/MU27/MU28/MU30 |
| year sole writer 51f54f=5b2c00(round+1)=arg+g92bf68(2100); chain pinned | G10/R1 `:532-533` | V MU10/MU13/MU17/MU30 |
| M320 ==0@59f1a0; M305 &3==bl(1)@51f711 def-set pinned; M317 >75@55840d; M177 age<16 | G5/G8 `:527,530,438,502` | V MU5/MU14/MU15/MU16/MU21/MU22/MU25/MU29 |
| live round=50/year=2150; rivals dead | G7/R1-R3 `:529,533-535` | V MU7/MU24; R1 MU10/MU17, R2 MU13/MU18/MU23, R3 MU12/MU13/MU23 |
| ACCEPT 13/13 digest 136841406b5bee5b x2 (`evidence/m323_round_census.txt:536`); harness 31/31+1 a25f4b5f2af8bb8a (`evidence/m323_mutate.txt:32`) | as cited | V |
| OPEN: rand-start noun; ~~g999fa4~~ cheat-parsed number (M325; writers M324); ~~save-carry~~ ANSWERED M324 (raw header blob); 4e0350 = EDITORYEAR cheat path (M325); resolver linear-static | - | lead |

## M320 (s294-chain2, STATIC, 12/12, 26/26+1) - siblings: 128-region ladder, 512 arrays, reset/rebuild

| claim | evidence | conf |
|---|---|---|
| LADDER 9x128 +1078..+1878: reset 59efeb-59f01d, init 51dcb8-51dd03  | G4/G5 `evidence/m320_sibling_census.txt:409-410` | V MU3/MU4/MU12/MU14/MU16 |
| 512: byte 854/a54, word c54; cmp 0x200, 8380*blk+2*i, gated 985afc==0 | G6 `:411` | V MU5/MU20/MU24 |
| COUNTERS +1478/+1678/+1778 @51df3d+; +1578 faction-count, blks 1..7 | G7 `:412` | V MU6/MU17/MU19/MU24 |
| RESET FUN_0059ec90: 114 W/RW, 92 offs; callers x3; magic 0xdfbe41 +1d0 | G8 `:413` | V MU7/MU15/MU18 |
| TAIL +2038..20bc: 31 dw, 0x84%16=4; rival DEAD | R1 `:416` | V MU10 |
| FLAGWORD +0; CROSS GOAL 65/SITE 17; BLIND 61/3293 | G10/G3/G9 `:415,408,414` | V MU2/MU8/MU9/MU22 |
| ACCEPT 12/12 digest 12e247bdbc0f77ef (`evidence/m320_sibling_census.txt:418`); mutate 26/26 digest 0d18a3d23b3e94b4 (`evidence/m320_mutate.txt:27`) | as cited | V |
| OPEN: game nouns; 985afc; dfbe41; tail; save-carry | - | lead |

## M319 (s293, STATIC, zero box; 7/7 + 14/14 scored + 1 NO-OP + selftest 4/4) - pick (v) CLOSED: the 8 unguarded memo sites are NOT guarded by their callers

| claim | evidence | conf |
|---|---|---|
| MEMO READS FEW + PRIVATE (operand-substring census, mnemonic shape pinned): exactly 6 read/test instrs image-wide (0x4e5155, 0x4eb6bf, 0x4efe83, 0x4f21e9, 0x4f5c41, 0x5ab74d; {mov:5,cmp:1}) in 5 funcs; readers(5) subset writers(15) - no read-only consumer could hold a hoist | `evidence/m319_guard_hoist.txt:67-68` G2/G5 | V (MU3,MU4,MU10,MU11) |
| NOT HOISTED: 8 sites -> 4 nameable owners, 8 distinct direct callers; only 1 caller reads the memo (FUN_004f5a70) and it OWNS a guarded site (0x4f5c4a, pinned), so its read is its OWN guard; non-owner memo-readers 0 | :69 G3 | V (MU2,MU3,MU5,MU10-MU13) |
| NOT DEAD, NO MEMO-GATED ARRIVAL: min 1 call/owner; 9 arrivals, 0/9 under a memo test; the FULL histogram {other-test:8, fallthrough-only:1} is pinned; the flag-setter walk spans EVERY flag-writing class (not cmp/test only); 0x4f3f7f has no range (M315 A10), callers not nameable | :70-71 G4/G6 | V (MU2,MU3,MU5,MU6,MU10-MU12,MU14) |
| CLASSIFIER NOT BLIND, KINDS PINNED PER ADDRESS: memo-direct exactly at 0x4eb6c7, memo-copy at 0x4efeaa/0x4f2201/0x4f5c4a, no memo edge at any of the 7 nameable unguarded stores | :72 G7 | V (MU1-MU3,MU5,MU7,MU9,MU11,MU13,MU15) |
| PAIR LAW IS ORDERED: pair-fed only when `call 0x4e8d60` PRECEDES `call 0x4e78e0` in the 17 B reach (presence alone would accept a reversed pair) | :15 G1 | V (MU1,MU2,MU7) |
| THUNK-FOLLOWING MEASURED INERT HERE: turning it off moves NO printed number (a harness NO-OP, not a bite - the census does not depend on it) | MU8 `evidence/m319_mutate.txt:9` | V (harness measurement) |
| ACCEPT 7/7 digest fb4e802dac1995a2 (hashes T1 partition+guard kinds, T2 refs+mnemonics, T3 callers, T4 per-call arrival, T5 edge labels); 3 accepted runs byte-identical, sha256 5ea00d859bf4503f (`evidence/m319_guard_hoist.txt:73`, `evidence/m319_guard_hoist_rerun2.txt:73`, `evidence/m319_guard_hoist_rerun3.txt:73`; re-derive by re-running the acceptance 3x and `diff`ing each stdout against the committed file); sweep 14/14 scored + 1/1 NO-OP (`evidence/m319_mutate.txt:17`); selftest 4/4 (`evidence/m319_mutate_selftest.txt:5`) | as cited | V |
| REVIEW ROUND #317 + the squash title: the title's 459f47e3178f439d / 12-12+1 are the PRE-REVIEW harness; the ACCEPT row is what held at merge head (same defect as M314's "20/20"). Governance note - adds no byte claim | - | lead |
| OPEN (one lane CLOSED by M321): what gates the 8 - `BYTE PTR [eax+0x38],0x40` x3 is now NAMED (base_array field 56 bit 6, gating the FUN_004f41f0 talent-request leg: `NAMED ## M321`, `evidence/m321_memo_owners.txt:30-34`); still unnamed: al,0x10; eax,0x1; ecx,eax. Also open: 0x4f3f7f callers; never live. Caveat: `guarded()` accepts via-copy on copy-liveness AT THE JCC (over-approximation) - the 4/8 split stands on agreement with M315 + the pinned kinds | - | lead |

## M318 (s289, STATIC, zero box; 12/12+1 NO-OP) - pick (iv) ANSWERED: the selection-REFRESH PAIR = FUN_004e8d60 (selected-base UNIT-SUPPORT CENSUS) then FUN_004e78e0 (selected-base PANE REFRESH); both void(void), driven by the CURRENT selection

| claim | evidence | conf |
|---|---|---|
| PAIR: 12 back-to-back sites (gap 5) in 7 owners = M315's 12 memo sites; each follows a ds:0x68cbb4 store within 17 B of the SECOND call (worst = 17); the REFRESH tuple holds TARGETS | G2/G3 (`evidence/m318_refresh_pair.txt:6-35`) | V |
| A = UNIT-SUPPORT CENSUS: unit walk (count ds:0x985af0, stride 0x34), faction + home-base filter (unit+0x2e == ds:0x68cbb0); yield triad 4e6960/4e6d40/4e7070 switched on unit+0x26; over-capacity bit 0x10 (limit 94d684 clamp 0..7); foreign-tile bits 0x400000/0x200000 (4e3b50 owner, keyed 94d690 ==-3/<-3); 6-store bank 8f0c2c..8f0cc8 | C1/C2 (`:37-53,55-75`) | V (structure) / INFERRED (nouns) |
| B = PANE REFRESH: first call 4e63b0 scan-pool rebuild @4e78e9; rows from faction array 94dc34 into pane+0xbc..; dispatcher 4e75f0 x7; region bits 507410 x5 (first 0x1d); base flags +0x95da9c x5 halve unimproved rows; 15 selection reads; 8f0c68 countdown | C1/C3 (`:37-53,77-86`) | V (structure) / INFERRED (display) |
| KIND LAW SHARED: dispatcher 4e75f0 switch (cmp 3) = same triad + case-3 ds:0x8f0cc8=0, identical to A's inline switch | C4 (`:88-91`) | V |
| ACCEPT: `m318_refresh_pair.py` twice-equal, PRINTED digest 2e81643277e3a23b (`:100`, green `:102`); `m318_mutate.py` 17/17+1 NO-OP 39e6ce9f2334fe87 (`evidence/m318_mutate.txt:21`) | as cited | V |
| REVIEW #311 (3 P2 accepted): condition pins added (home-base cmp/je, 94d684 clamp chain, dispatcher ja + jump-table BYTES from the PE); G3 reach measured store->SECOND call (worst 17, was implicitly 22); digest now computed+printed by the instrument (was an external file hash). MU14-MU18 gate the fixes | `evidence/m318_mutate.txt:15-20` | V |
| OPEN: kinds' game words (resource triad candidate); unit+0x26; the 52-B array 98ada8 indexed by unit+0xa; pane+3 clamp byte | - | lead |

## M317 (s288, STATIC, zero box; 22/22+1 NO-OP post-review) - pick (iii') ANSWERED: FUN_00556690(faction) = per-faction AI STRATEGY PASS: decides goals-at-bases/units, region-state flips, inline unit orders, goal cancels

| claim | evidence | conf |
|---|---|---|
| CONTEXT: 1 arg=faction; callers 0x52094f (upkeep FUN_005208f0: 005551e0->ENGINE->005a1ad0, 985ae8 bits 1/8 gate, edi=param unclobbered) + 0x59dd43 (walker jl 59e2a6->59ce92) | C5 (`evidence/m317_engine_decides.txt:198-201`) | V |
| ISSUE: 7 AddGoal, owner=-1 x7, block=faction (6/7 direct [ebp+8]); d2@556820(p2)+556aed(p4), s3@556831(p2), a0@55698e(p local) at base x/y (+0/+2); n6@556e79 at UNIT x/y (933278/+2), prio=2+2*bit19[94d430+blk*8380]; ^41@556a4a+558adc(p2, base+2c/2e, cost gate 4cc7b0 first) | C4 (`:136-196`, n6 decode `:172-178`) | V |
| CANCEL: remover c8@559809 (p1,p2 from band+4/+8); knockout@559e8e arg=faction; 56d890@5597a5 (1 local arg) | C4 (`:179-196`) | V |
| SHAPE: 605 jcc (18 global-fed), 44 back-edges, 1 ret, 0 indirect; walks base 130 x5 / block 20bc x2 / goal 10 x1 / region bound 128 @558b1c; abs x20 | C1/C3/C6 (`:15-58,122-134,203-218`) | V |
| OUTPUTS: 358 stores = 239 stack + 2 direct (8f0d34 distance) + 104 global-disp (40 arrays: eda8 M250 FULL-insn pin, e5a8/e628, e7a8/a9 flags, unit+11=18/+14/+1c target/+2b=30/31/+4 bits 10/20/40000000, counter banks, pair 94d820/824, base flags 95da40) + 13 struct | C2 (`:60-120`) | V |
| ACCEPT: `m317_engine_decides.py` twice-equal digest 5263767ee3bf4bba (`:223`); `m317_mutate.py` 22/22+1 NO-OP digest a0729996723078a4 (`evidence/m317_mutate.txt:26`) | as cited | V |
| REVIEW #309 (5 P2 accepted): per-push arg trace + clobber-stop (old trace mis-decoded n6's p2/prio); M250 full-insn pin; C5 measured not constant-compare; per-pid harness copy + finally; path:line cites. MU17-MU23 gate the fixes | `evidence/m317_mutate.txt:17-25` | V |
| OPEN: kind game-words a/d/s/n/c (consumer side); 30/31 mission bytes; 692184 (map-width candidate, INFERRED from the y*W+x/2 tile fold @5567ce-5567e4); multi-base pick fold | - | lead |

## M316 (s286, STATIC, zero box) - pick (iii) OPEN-ANSWERED: `FUN_0056d350` = `AddGoal(block, kind, prio, p1, p2, owner)`; the GOAL list is a per-faction 75x16 B array at 0x94ee28+block*0x20bc — FULL-LENGTH ROWS VERBATIM at `docs/named-archive-m316-rows.md` (moved by `scripts/m327_named_rotate.py`, sha1 `d3dffc67fcb5`); this stub governs and keeps one line per claim

| claim (short) | evidence | conf / mutant |
|---|---|---|
| RECORD LAW: one 75-entry GOAL list per 0x20bc block, entry 16 B (+0 kind WORD signed, -1 = free/killed; +2 prio; +4 p1; +8 p2; +0C owner); absolute write-set 0x56d44b/55/5f/69/70 + M310's kill 0x470d5c; ALL four scan bounds `cmp ...,0x4b` (0x470c16, 0x470cc8, 0x56d3b9, 0x56d436) | A1 `:3`, A2 `:4`, A2b `:5`, A3 `:6`, A5 `:9` | V |
| INSERT LAW (50 sites, 12 owners, digest 8ace40ec97032541): scan for the (kind,p1,p2) triple; a hit goes to the MAX-PRIO tail (`mov WORD PTR [ecx],ax` 0x56d41c) — duplicates never add a record | A5/A5b `:10`, A11 `:1`, A6/A6b `:11,12` | V (A6b digest-pinned after PC10 exposed it) |
| EVICTION LAW: free or prio<new are candidates; score free=1000 (0x56d3e6), prio<1=100+prio (0x56d425), else 20-prio (0x56d3fb); MAX wins → NEGATIVE prio evicts before any ordinary goal; no victim → goal silently rejected (iVar2=-1) | A4/A4b `:7,8`, A2 `:4` | V (mechanism) / INFERRED (intent) |
| WRITE-SET: 6 absolute stores + 9 pointer-relative GOAL stores — max-update 0x56d41c; knockout helper FUN_0056d690 (0x56d6be/0x56d6c8, sole caller 0x559e8e); block-initializer FUN_0056d710 (fills all 75, sole caller 0x59ed4f); remover FUN_0056d780 (12 sites, triple scan 0x56d844/4e/58, kill 0x56d860 — read off the dump, not gated) | A1 `:3`, A11 `:1` | V |
| SITE TWIN ARRAY at 0x94f2d8, same 16 B shape: initializer second loop 0x56d75b-68, remover kills the twin (0x56d82e/33); 7 relative SITE stores file-wide | A11b `:2` | V (writes) / OPEN (what a SITE is) |
| READERS: FUN_0056d5d0 (15 callers), FUN_0056d780 (12); the engine FUN_00556690 holds 35 of the 65 band refs and is the only reader of +0C owner; called from 0x52094f + 0x59dd43 | A8 `:16`, A9 `:17` | V / ANSWERED by M317 |
| BAD-GOAL ASSERTION: `(p1^p2)&1` (0x56d35e/60) + debug bit 0x1000 of ds:0x985ae8 (`test ah,0x10` 0x56d369) → formatter on "Bad GOAL" (0x6914fc, PE); "Bad SITE" 12 B later | A7 `:14`, A7b `:15` | V (bytes) / INFERRED (why parity) |
| KIND CENSUS: immediate kinds {0,2,3,6,7,8,9,11,16,25,41}; all 7 tokened kinds ('a','d','s','n','c','f','^') have immediate producers; 2 sites compute kind at runtime; all 37 immediate prios in {1,2,4,5}, 13 reg-form | A6c `:13`, A10 `:18` | V (census) / INFERRED (nouns) |
| WHAT A GOAL IS: a per-faction AI claim record in a 75-deep list, one entry point enforcing uniqueness by (kind,p1,p2) and a fixed reclaim order; negative prio = evict-first tombstone, register-form only | all rows; M310 | V / INFERRED (game nouns) |
| ACCEPTANCE `python3 -u scripts/m316_addgoal.py` → **18/18**, digest **dcc6ce82fc98aec4** (`evidence/m316_addgoal.txt:19`); `scripts/m316_mutate.py` → **32/32 (19 expectation + 13 CODE via M316_PATCH), zero BAD** (`evidence/m316_mutate.txt:34`); honest retargets + PC10's decoration catch in the full rows | `evidence/m316_addgoal.txt`, `evidence/m316_mutate.txt` | V |
| OPEN: which game word each tokened kind is; save-carry of 0x94ee28..+0x4b0 per block; why 31 kinds have no immediate producer | - | lead |

## M315 (s284, STATIC, zero box; mutation-tested 29/29 post-review) - pick (ii) CLOSED: `ds:0x68cbb4` is the REFRESH MEMO of the record-selection chain - "the index the refresh pair has already run for" - not a second cursor, and M311's 19 unexplained writers all close. FULL-LENGTH ROWS VERBATIM at `docs/named-archive-m333-rows.md:56` (§rotation-2 marker at `:54`, s314 headroom rotation, sha1 `c70cc525ecbd` — the region is bounded by its own terminator line, its line number AND full digest re-asserted by `scripts/m333_named_rotate2.py --verify`); this stub governs.
- THE FIELD + PARTITION LAW: the 22 stores split 12 fed by the index or a caller slot (each followed by the refresh pair `call 0x4e8d60` + `call 0x4e78e0`) vs 10 `-1` sentinel clears with ZERO calls to either callee in the next 60 instructions (A2+A3, exact 12-element distance list); NO independent value ever enters — 8x `mov r,ds:0x68cbb0` + 4x caller slot, totals sum to exactly 22 (A2b+A9; proven CODE mutants PC1/PC2 rewrite those instructions).
- DEDUP GUARD PARTIAL, NOT UNIVERSAL: only 4 of the 12 memo sites carry a local guard (`0x4eb6c7`, `0x4efeaa`, `0x4f2201`, `0x4f5c4a`); the other 8 refresh unconditionally. ~~the 8 are guarded by their callers (pick (v))~~ **REFUTED by M319** — no hoisted guard exists; the single memo-reading caller is itself a memo-site owner (NAMED ## M319, `evidence/m319_guard_hoist.txt:69-71`). Still UNVERIFIED: that the 4 stack-slot stores carry an index; coherence across record deletion (A9 tail).
- M311's "19 writers unexplained" closes as 10 sentinel clears + 9 memo updates — its window was FORWARD `0..+32 B` (`m311_recidx.py:449`), not symmetric (A5); the image initialises BOTH `ds:0x68cbb0` and `ds:0x68cbb4` to `0xffffffff` (A7); `0x4e8d60`/`0x4e78e0` ANSWERED by M318 (NAMED ## M318).
- ACCEPTANCE `scripts/m315_bb4_census.py` -> 10/10, digest `3976ca97eedc1e19`, 2 runs byte-identical; `scripts/m315_bb4_mutate.py` -> 29/29 reddening EXACTLY their declared gate SETS (22 literal + 7 CODE mutants via `M315_PATCH`); coverage gap MEASURED: exactly 1 of 22 stores (`0x4f3f7f`) sits outside every `index.csv` function range — the only site where the def-walk falls back to a 36-instruction cap (A10; mutant MU19_unclaimed reddens exactly A10).

## B25 (ROTATED by s329) - MERGED s295 as #319 -> 1556ce9: the MOVE leg made PERSISTENT (sim/composedmove.py). FULL TABLE VERBATIM at `docs/named-archive-m353-rows.md` (sha1 `dd4991b77b2528c9d3bf011d226165c14277c19d`); this stub governs, one line per claim
| claim | evidence | conf / mutant |
|---|---|---|
| **THE LAW IS BYTE-LEVEL CARRY**: 4/4 rounds the container READ differs from the writer's last WRITE only by the falsifier's own bytes; 268/268 (round,unit) start tiles == a FRESH DECODE of the head bytes consumed; (+2,0) mod 64 and 2-accept/1-refuse hold from the RELOADED tile | `evidence/b25_selftest.txt:40-43` (table H), `:63` (G4) | V MU2/MU10/MU14/MU3/MU15 |
| an image-only poison of record 0 at round 1 shifts its trajectory 39 mod 64 into the FINAL container ([19,42] vs clean [44,42]), 0 of 67 others move; the model-fed movers are blind to the falsifier, not to writing (268 unit bytes each, image == their own clean run) | `:21-23` (table D), `:65` (G6) | V MU1/MU7 |
| the save's grid is 64x64 (`decode_save --sections`, 90,112 = 64*64*22) vs `planet.MP` 80x80: 37 records land out of the container, 27 return, `found_units` 67 -> 4, all six numbers PINNED in G5; B7 wrapped by the map file: 10 of 67 final tiles outside (4 of 67 at --turns 5) | `:52-53` (table I, mpwidth/wrapskip), `:38` (table F, B7), `:64` (G5) | V MU8/MU12/MU13 |
| **THE TILE TEST IS NOT THE DECODER**: raw `tile >= width` and `sim/save._unit_ok` differ in 8/44 probes - exactly the records the decoder exempts (25 of the 67 carry +10 in [128,130,131,256,320,321,322,323], so it coord-checks 42); with that rule both agree 44/44, and `found_units` is reproduced from `_unit_ok` 44/44 | `:56` (TOTAL), `:45-55` (table I), `:64` | V MU12/MU16 (archive: RETRACTED by M327) |
| footprint == move law: 67 unit bytes == 67 tiles written/round at record offset +0 (x only), + 1 modeled header byte/round (year 2151->2154); final image 68 B from the save, 0 B outside a modeled span | `:4-7` (table A), `:61` (G2), `:66` (G7) | V MU3/MU4/MU5 |
| rivals/controls: nowrite 0 unit bytes, lift 0 + year frozen 2150, budget3 1 accept/round; mpwidth and wrapskip COINCIDENT here (max_x 79 < 80, declared not separated); G8 requires the FULL table-E signature to differ from ALL 5 rival rows (the 3 `:clean` twins coincide by design) | `:26-36` (table E), `:67` (G8) | V MU4/MU5/MU6 |
| ACCEPT `python3 -u -m sim.selftest --b25` -> **PASS B25: 9/9**, anchor **901a286332960a10**, 2 runs byte-identical and identical to `python3 -u -m sim.composedmove`; **G9 PINS the anchor to a literal** (MU9 reddens G9 and nothing else); harness **13/13 + 3 declared NO-OP**; `--selftest` 5/5 | `:59`, `:69`, `b25_movepersist.txt:69` (its 69 lines are byte-identical to `b25_selftest.txt:1-69`), `b25_mutate.txt:20`, `b25_mutate_selftest.txt:11` | V MU1-MU16 |
| UNMODELED: MP/spent never crosses the container; y never moves (dy=0) so the y-bound law is unexercised; no blocking/ZOC/terrain refusal; which unit the game moves is not claimed; presses on all 67 records though 25 are not coord-checked | spine §B25 | lead |

## B26 (s299 BUILD + PR #328 review remediation; settled, ROTATED by s324-chain2) — the composed run crosses a SAVE/LOAD boundary: the container is LOADED, not just written, and the non-carry is counted, not declared away. ACCEPT `PASS 10/10` + harness 19/19 scored + 1 declared NO-OP + selftest 8/8 + entry identity 2/2, anchor `ae43e0ab9c8cfc3d`. FULL-LENGTH BLOCK VERBATIM at `docs/named-archive-b26-governing.md` (sha1 `543c1243f00c`); long-form reasoning at `docs/named-archive-b26-rows.md`; this stub governs

| claim | conf |
|---|---|
| the boundary is a fresh decode checked against an independent second parse: 69/69 unit tiles and 20/20 base records field-wise | V (archived row 1) |
| UNMODELED / OPEN (B26's own): the non-carry is measured on ONE mid-gesture configuration; in-progress turn state beyond the budget not modeled; whole-record growth INFERRED; `found_units` 69 -> 0 while `n_units_img` stays 70/71 (printed, NOT gated); smuggler owner 1 vs 2 UNKNOWN; zero box time | lead |
## M327 (s304 + s305 review round, pick (vii), STATIC, zero box; ACCEPT `python3 -u scripts/m327_typeband_census.py` → **PASS 11/11**, digest `91f58f3de03090c1` `evidence/m327_typeband_census.txt:769` (re-pinned at s305: T4's printed row changed when its tautological `covered` became a real cross-check), 2 runs byte-identical to the committed file; harness `python3 -u scripts/m327_mutate.py` → **24/24** (23 scored + declared NO-OP MU21), every gate reddened by ≥1 mutant, sets measured (`evidence/m327_mutate.txt:29`) — **a unit record's `+10` is its SIGNED TYPE INDEX into the save's own 512×52-B type array at `count_off+4+count_len+3584` (MIDDLE_SECTIONS' 26,624), ending 4,096 B before the unit array; `+10`//64 = faction band ⇒ the 25 coord-exempt records are units of faction-unique designs, not queue entries**

| claim | evidence | conf / mutant |
|---|---|---|
| `.text`: 659 chains `movsx [<base>+0x933282]` → ×0x34 → `+0x98ad88` (774 `+10` word refs, 116 funcs); pinned `0x4bdec4-0x4bded4` and `unit_set_position` `0x5ab3a2` → type rec **+0x24** | `:9`, `:669-671` | V; MU1-3, MU17 |
| 67 recs = 42 band-0 + 25 with `+10` ∈ {128,130,131,256,320,321,322,323}; **25/25 owner(+14) == `+10`//64**; 0/67 out-of-grid; replicates on `m112auto1.SAV` (68 recs, 25 band) | `:676`, `:739-740` | V; MU6-8, MU11, MU16, MU18 |
| **32/512 slots named = 14 band-0 + 18 faction designs**, per band == M80's live census minus 324/325 (its own creations); 67/67 recs name a slot ⇒ 10^-80.7; type byte **+0x2d==0xff exactly on the 14 band-0 slots**; `+0x30` bit 2 NOT a band marker | `:6-8`, `:762` | V / INFERRED (names); MU9, MU12, MU15, MU20, MU22 |
| the coord exemption is **ours, not the game's**: `0x5ab320` (90 insns, 9 jumps) has **0 branches on the entry path to the `+0`/`+2` stores** (0x5ab355/5c) | `:756` | V; MU4, MU5, MU19 |
| the only save where it bites is **our own poke** `m113map` = `m54b_clean` + 20 markers `0xc0de0001..14`, stride 128 from 222000; 13 windows in-array (one straddles rec16/17); out-of-grid recs **12 (3076,56832), 17 (192) both marker-struck**; all-record check ⇒ found_units 67→**49**; the 20 diff-derived windows == the 20 marker dwords an INDEPENDENT value scan of `m113map` finds (`:741`, s305) | `:741-755` | V; MU10, MU13, MU14 |
| rivals measured: R1 0-based page covers 0..34 too, so bounds do NOT discriminate — it dies on the decoded const -5; R2 a coherent 6-row page (step 6, 6 pages, 36 cells) reaches index 35 = the terminator; R3 a flat list needs coef_n == 1 but all three sites decode (5,-5); R4 base 0x983984 ends at 0x984ca8 != term | `:36-40` | V MU2,MU3,MU4,MU11 |
| **RETRACTED IN PLACE**: `sim/save.py:52` + `_unit_ok`'s docstring (comments only — `--b26` 10/10 `ae43e0ab9c8cfc3d`, `--b25` 9/9 `901a286332960a10` re-run after); `## B25`'s `.exe shares the rule`; the `0x933278` row's "flags at +10"; M26's `unit_can_act` bits (bit 6 = index bit 6, 6 recs; the word at **+12** is zero on **67/67** — G3 now asserts it — while the same census at +10 is nonzero on 64/67, `:757`) | `:757`, `:761` | V; MU4/MU19 (guarded-store rival), MU6/MU16/MU18 (band==owner), MU11 (out-of-band index), MU13 (shared-rule claim), MU23 (+12 census — G3+G10), MU24 (bit 10 of +10 poked — G3+G5+G6+G10) |
| OPEN: what `+0x2d` means; what the game validates on LOAD; `m112poke.SAV` is a byte-copy of `m54b_clean.SAV` (4 saves = 3 states) | - | lead |

## M329 (s307, pick (viii), STATIC, zero box; ACCEPT `python3 -u scripts/m329_scratchtree.py` -> 13/13, digest `757e40a7ed04abda`, 2 runs byte-identical; harness `scripts/m329_mutate.py` 26/26, base reddened `[]`) - `FUN_0041a8f0` = `ui_governor_options_pane(widget, page)`. FULL-LENGTH TABLE VERBATIM at `docs/named-archive-m329-rows.md:5` (sha1 `ccee72a56f16b4b4`); this stub governs, one line per claim

| # | claim (one line) | conf |
|---|---|---|
| 1 | `FUN_0041a8f0` (1,403 B) is a thiscall member of the widget singleton `0x6a9480` (`mov edi,ecx`) | V |
| 2 | exactly 4 direct `e8` call sites / 4 owners (`0x41e3bd`, `0x49b306`, `0x4a9e0e`, +1) | V |
| 3 | naming basis: the only `push imm32>=0x400000` in frame = `0x6899ec`='GOVOPTIONS' @`0x41aba5` -> save writer `0x6267a5` | V |
| 4 | 3 chains in the frame fold to stride 304 = the own-faction base array `304*idx+0x95da10` | V |
| 5 | `ds:0x99aa38` = the pack staging dword: 20 stores, 19 legs, 19 distinct record masks | V |
| 6 | write-back: of the 19 legs, 11 resolve to a direct `or mask @addr` on the record | V |
| 7 | `0x94d600`-field census: exactly 8 refs, 3 writers (2 textual forms of one site) | V |
| 8 | `[rec+0x38]` bit `0x40` = the ARRIVAL test @`0x41ade4`, after the publish, arg==0 phase only | V |
| 9 | 6 rivals refuted on the printed numbers (free function / cursor-driven / unit array / dword overwrite / ...) | V |
| 10 | mutant sets MEASURED (`M329_MUT_MEASURE=1`): 25 scored + 1 NO-OP, every gate covered | V |
| 11 | OPEN: what the 19 record bits MEAN (4 published, 15 stay); who fills the scratch `+0x00..+0x18` in other frames | OPEN |
| 12 | REVIEW meta: this rotation family (`m329_named_rotate*.py`) already moved two settled blocks out of NAMED.md | meta |
| 13 | REVIEW box time: ZERO - everything is `scratch/m574/text.txt` + `ghidra_out/index.csv` | meta |

Every `V` row above is the archived row's verdict verbatim: its mutant (MU1-MU25) and its `evidence/m329_*.txt:line` cites stay in `docs/named-archive-m329-rows.md` (same row order), so no V row here is unattested.
## B27 (s309 BUILD, zero box) — the ENERGY round EXECUTABLE and CARRIED: eight faction blocks in, the ledger written through the writer (block A's FIRST MODELED spans), out and back through the container. `sim/energy.py` = the law, `sim/composedenergy.py` = the run; spine §B27. Every row's numbers are transcribed from the lines it cites.

| claim | evidence | conf / mutant |
|---|---|---|
| the container carries the ledger: ENERGY `[10,28,112,69,229,60,102,37]`, `+300 [0,1,1,0,1,0,1,1]`, `+224` all 0, both file-offset tables (1580- / 1360-based) == the M325/M326/M330 censuses' OWN printed rows, PARSED from those evidence lines | `evidence/b27_selftest.txt:14-18`, gate `:70` | V; MU8 MU9 |
| the ledger law holds on the save's bytes **8/8 + 8/8** (`+310=+2fc`; `+30c=+308-+300++2fc`), predicted THROUGH `sim.energy.ledger`; the three rivals match 1/3/1 of 8 (all printed) | `:20-21`, gate `:71` | V; MU1 MU2 |
| refund = `trunc(k·spend/3)`, **residue kept**: M330 G4's 7 sample rows reproduced, sweep 40,002 cases 0 violations; k-table `[0,0,0,0,1,2,2,2,2,2]` derived from the switch tuples parsed from the census (skip<=3, k=1 at 4) == the module defaults; BOTH rivals measured (no-thresholding 1 difficulty, threshold-2 1) and the branch SHAPE is gated too (the switch reads the same `0x985aec` global; cmp 0x3/jle skip and cmp 0x4/jne to a DIFFERENT address, so the k=1 fall-through can exist) | `:23-25`, gates `:73` `:74` | V; MU5 MU16 (threshold, sweep width); MU3 MU4 redden G5 too |
| the ORDERING is a number: SNAPSHOT == the post-settle clamped pool on 3/3 discriminating fixtures (snapshot-first differs by the clamped amount); both legs MEASURED INERT here - settle moves 0/8 (`+224`=0), refund fires 0/8 (difficulty dword out of the container = 2 <= skip 3, noun INFERRED M308). Inertness MEASURED on the save's own eight blocks and proven not a stub: still 0/8 when driven at the k=1/k=2 difficulties (max +300 = 1, under the k=1 quantum) while `refund(3, k)` = 1 at both k (probe 2/2) | `:26-32` `:36`, gate `:75` | V; MU6 MU7 |
| B4 reuse, not fork: its 3 replay gates green IN-PROCESS; the post-found row (gross 2, upkeep 2, energy 19) reproduces through THIS pipeline while k=2 predicts 20 and full refund 21; the other six recorded factions move (507->627 etc.) = UNMODELED frontier. RETRACTED s309 (review F6): the flat 12-round idle 12/12 is only a **legs-zero consistency** print (with every input 0 a round cannot move energy - it cannot fail), so it gates nothing and is not a parity | `:33` `:35-38`, gate `:72` | V; MU3 MU4 (they redden G4 on the post-found parity); the six-faction frontier is DECLARED, never gated |
| **THE WRITER MODELS BLOCK A FOR THE FIRST TIME**: identity True; 40 spans (160 B) offered, 9 bytes differ, 0 outside modeled spans, carry violations `[0,0,0,0,0,0]` over 6 rounds, and bytes outside modeled spans measured **per round** `[0,0,0,0,0,0]` (not only on the final image, s309 review F10); `modeled_spans()` no-arg == the pre-B27 list (B8-B26 unloosened) | `:55-59`, gate `:76` | V; MU10 MU11 |
| falsifier: +77 on faction 4's ENERGY **in the written image only** reaches the final container for faction 4 alone (`[4]`); the ledger-keeping smuggler is blind, byte-equal to the clean run - counted as poisoned factions CARRIED: honest 1, smuggler 0 | `:60-61`, gate `:77` | V; MU12 MU13 |
| ACCEPT `python3 -u -m sim.selftest --b27` -> **PASS B27: 10/10 gates** (2 runs byte-identical), anchored on THREE literals inside G10: rows `b65e8129b67ba67d`, printed tables `3c134ea70638c12b`, unmutated container `626fec9a35deddba`; harness -> **HARNESS PASS 17/17** digest **181d99d9ac000044**, NO-OP reddens `[]`, `exact-set check: 17 mutant(s), 0 complaint(s), gates reddened 10/10` (each mutant's measured set must equal its frozen `DECLARED` entry, both directions; s309 review F1), `--selftest` 4/4 (ST4 rejects a wrong declaration); `--measure` prints the sets before they are frozen and asserts nothing | `:56` `:79`, `b27_mutate.txt:18-22`, `b27_mutate_selftest.txt:1-4` | V; MU1-MU17 |
| UNMODELED (printed, spine §B27): `+2fc/+308/+3f8` entry-zeroed but their mid-round writer is OPEN (M330) -> pass-through, the ledger law takes them as DECLARED inputs; the feeder's per-slot `v` — now PRICED from the B29 derived table, not alpha-assumed (B29); income-vs-feeder order unpinned (only settle < snapshot < refund pinned); 48 rows computed, 13 printed | spine §B27, `:54` | lead |

## M333 (s314, STATIC, zero box) — the 34 feeder slots `0x984d48+48*item`: the slot NOUN = a facility the base HAS, and bit5 of faction block+0 is a CARRIED HALF-UNIT exclusive to FUN_004f47f0 (closes M330 G10 "slot noun OPEN")
- ACCEPT `python3 -u scripts/m333_feeder_slot_census.py` -> **`PASS M333: 8/8 gates`**, digest `70376694feec5815` (post-#348-review; the pre-review run was `b1ca12715e833cc7`), 2 runs byte-identical (`evidence/m333_feeder_slot_census.txt:58-59`); harness `python3 -u scripts/m333_mutate.py` -> **`PASS HARNESS 18/18`** digest `dee04978a5b5dd09` (14 CODE mutants via `M333_PATCH` + 4 EXPECT mutants, every declared gate SET matched exactly; ME1's set GREW to include G7 when the harness found G7's `rowdiff` reads `ITEM_UPKEEP`, and ME3 `0x20BD` was replaced after it scored a true NO-OP — `//4` lands on 2095 either way), `--selftest` 6/6 (`evidence/m333_mutate.txt:20-21`, `evidence/m333_mutate_selftest.txt:8`)
- G1+G7 (mutants MU1/MU2/MU5/MU6/MU14/ME1): FUN_004f47f0's loop counter `esi` is the ITEM id — init 1 (prologue `0x4f4802`); the TOP test `cmp esi,0x22 / jg 0x4f4a34` SKIPS ids 35..38 (it is NOT the loop exit); the bottom `inc esi / cmp esi,0x27 / jl 0x4f480b` is the back-edge — the loop VISITS ids 1..38 and CHARGES 1..34 (G7 parses BOTH bounds from the cmp immediates; the `0x750` literal occurs 19x in .text but none is tied to this table); the `x48` fold (`lea r,[i+i*2]`+`shl r,4`) is SHAPE-pinned AND the shl dest is tied to the read's own base register (MU14), because the linear value-walker over-proves `48*1` through the back-edge (the defect this milestone exists to fix)
- G3 (MU8/MU12/ME1): a slot is charged only when its BIT is set in the current base's 304-B record at `base+0x8c` (`304*[ds:0x68cbb0]`) — and the tested bit is the mapper's bit-mask output for THIS item: the bitmap read's index register loads `[ebp-0x8]` and the `and al,cl`'s `cl` loads `[ebp-0xc]`, both mapper out-slots pushed with `esi` (FUN_00507410) — the slot is a facility the base HAS, not a queue position
- G4 (MU3/MU4/MU10/MU13/ME2): the halving is a CARRIED HALF-UNIT — bit5 of `block[owner]+0` (`0x94d430+8380*own`, `own=BYTE[[ds:0x8f0d60]+4]` read ONCE in the prologue, tied: `own_src` dest == `own_byte` base, `xor ebx,ebx` immediately before, fold leaf == that `ebx`) is extracted (`shr 5`+`and 1`), ADDED to the item cost, the sum's `sar 1` quotient is the charge, and the sum's PARITY is written back into the SAME bit5 (odd remainder survives the round); order read→add→test→set/clr→store→quotient monotonic; only the parity pair touches `ecx`
- G5+RIVAL-R2 (MU3/MU4/ME2/ME3): def-use census (path-insensitive, stops at calls/function bounds/address discontinuities; the 2 block+0 sites in UNCLAIMED gap regions are measured and printed) — FUN_004f47f0 is the ONLY function in .text that READS bit5 of a block+0 value AND the ONLY one that WRITES it (`or ecx,0x20` → store-back via the lea'd pointer); the 15 near-miss functions' `0x20` ops are on other values — FUN_004dc390 mirrors block+0 bits 30/29/20 into bits 4/5/6 of a DERIVED dword (rival "bit5 is a shared faction flag" dies here)
- G6 (MU7/MU11): `ds:0x985ba0` has NO writer in .text — ALL operand-text mentions measured (2 loads, 0 stores, no lea-absolute; a computed-address writer is beyond static .text reach — noun INFERRED); the halving fires only when that base's ZERO-EXTENDED owner byte (`xor edx,edx` then `mov dl,[ecx+0x95da14]`, no edx write between) == `ebx`, the current record's owner byte (`cmp`/`sete`/`je`), plus a sign test (`jl`) — 2 distinct skips to full price; `ebx`==the charged base's owner is INFERRED, not measured. **QUALIFIED by B28**: the dword IS carried — it lives in the save's state header at file offset 244 and reads `-1` in `m54b_clean.SAV`, so the halving is measured INERT on that container (`NAMED ## B28`, `evidence/b28_feeder_exec.txt:5`; mutants MU6/MU7 redden the two legs separately)
- G2 (MU9/ME1): FUN_004f4760(item, faction) is the SAME law standalone — 6 features 1:1 in both bodies, same 48-fold leaf `esi`, both fold the disabled-list record to 1436 B
- OPEN LEAD (printed, not gated): the same loop body carries a REMOVAL path — second mapper call `0x4f49b6`, bitmap bit-CLEAR `0x4f49e1`, 3 stores to `block+0x220` (`0x4f497f`/`0x4f4999`/`0x4f4a0b`), callees FUN_004e40a0/0x6265a2/0x48f100 — pick (x7)

## M334 (s316-chain2, STATIC, zero box) - FUN_004f47f0's upkeep-FAILURE branch = a DIFFICULTY-GATED AUTO-SELL of one facility; ENERGY is ASSIGNED the price, not refunded (closes pick (x7); CORRECTS `docs/named-archive-m32-m84e.md:268`). FULL-LENGTH ROWS VERBATIM at `docs/named-archive-b29-rows.md:5` (sha1 `579f90da7d8c`); this stub governs, one line per claim

- 3-way dispatch after `ENERGY -= cost`: A `cmp [block+0x8],1` -> clamp, B `cmp [base+0x50],neg(item)` -> clamp, C sell; the zero source is `xor eax,eax` @0x4f4960 (`evidence/m334_powershort_census.txt:4-10`) - V MU1-6,MU35,ME2.
- `block+0x8` = EFFECTIVE DIFFICULTY: create 0x59eed6 = `ds:0x985aec` / imm 3, save-load 0x57ef57 through `[ecx*4+0x94d438]` with ecx = 2095*eax => difficulty<2 never sells (`:11-18`) - V MU7-9,MU26,MU33,MU38,ME1,ME5.
- the sell clears the SAME bitmap bit the charge tests (derived 304*base + byte + 0x95da9c) (`:19-24`) - V MU10-13,MU22-24,MU27,MU28,MU39,ME3 + RIVAL2.
- `ENERGY := FUN_004e40a0(owner,1,-1) * row[item]+12` with 0 reads of block+0x220 => the archived "refund (+=)" is REFUTED (`:25-29`) - V MU14-17,MU29,MU30,MU36,MU37 + RIVAL1.
- announced `FUN_0048f100('POWERSHORT',0x10000,0xe,'genwarning_sm.pcx',0)` + `FUN_006265a2(1,row[item]+0,-1,-1)` (`:30-34`) - V MU18-20,MU25,MU31,ME6.
- no loop exit after a sale => several facilities can go in one round; 0 folded refs to block+0x220 (control: 10 image-wide) (`:35-39`) - V MU21,MU22,MU34,ME3,ME4.
- INFERRED/OPEN: `base_rec+0x50` = queue head; `row+12` runtime value (.bss) => numeric ENERGY outcome; FUN_004e40a0 = ECONOMIC FACTOR - lead (`:39`).
- ACCEPT `scripts/m334_powershort_census.py` 7/7 `5b5ece39af02baba`; harness 45/45 `a5a5091e533f7883`, selftest 6/6 (`evidence/m334_mutate.txt:47-49`).

## B28 (s316 BUILD, zero box) — the UPKEEP FEEDER made EXECUTABLE on the save's OWN base records; the CARRIED HALF-UNIT becomes a modeled block-A field (`sim/feeder.py` law, `sim/composedfeeder.py` run, spine §B28). ACCEPT `python3 -u -m sim.selftest --b28` -> **`PASS B28: 8/8 gates`** digest(rows) `705a4520c08c4062` / print `99c52201f073499d` / container `38bba29ab857654b`, 2 runs byte-identical (`evidence/b28_feeder_exec.txt:9`); harness `python3 -u scripts/b28_mutate.py` -> **`HARNESS PASS 18/18`** digest `3974d739da3af55f`, 8/8 gates covered, NO-OP `[]` (`evidence/b28_mutate.txt:20-23`). Post-#351-review: G4 asserts the pinned offset+value (244 / -1), G3 asserts the inert window against a control scan, G7 asserts the exact 7/8 and its miss, G6 measures the honest run's zero touch set.

ROTATED VERBATIM to `docs/named-archive-b28-feeder-rows.md` (sha1 `bd196a95e56c8016`); this stub governs: one line per claim; acceptance `python3 -u -m sim.selftest --b28` -> **`PASS B28: 8/8 gates`** digest `705a4520c08c4062`, harness `scripts/b28_mutate.py` -> **18/18** `3974d739da3af55f`.

| claim (one line each; full rows in the archive) | evidence | conf |
|---|---|---|
| `ds:0x985ba0` is CARRIED in the save's state header (file offset 244) and reads -1 in m54b_clean; the 4f48dc sign skip fires and the halving runs 0 times here | `evidence/b28_feeder_exec.txt:5` | V MU6 |
| the container's own `+300` octet is the executable feeder's full-price total 8/8; the no-list rival's exact 7/8 and its single miss `[own_player=3]` are asserted | `:8` | V MU5/MU9/MU10/ME3 |
| bounds are the PARSED immediates 1 / 0x22 / 0x27: VISITS 1..38, CHARGES 1..34, upkeep dword at row+0x10 | `:3` | V MU4/ME2 |
| charged only when the bit is set in the base's own `+0x8c` bitmap (18/18); ids 32..38 inert here (0/18 in `+0x90..+0x93`, 14/18 control windows nonzero) | `:4` | V MU5/MU9/ME6; bitmap WIDTH past `+0x8f` OPEN |
| charge = `trunc((cost+carry)/2)` (cdq/sub/sar, not a shift), parity written back into bit5; full-price leaves the carry | `:6` | V MU1/MU2/MU3/MU8 |
| FIXTURE-ONLY persistence: no carry written by the save's own run; honest run touches `[]` and rewrites bit5 unchanged | `:7` | V MU3/MU7/MU8/MU11/MU12/ME4/ME5 (fixture-only) |
| the NOUN of `ds:0x985ba0`; `ebx` == the charged base's owner | M333 G6 (no .text writer) | INFERRED |
## M335 (s317-chain2, pick (x6), STATIC 7/7) — the difficulty LADDER: `ds:0x985aec` indexes alpha.txt's six `#DIFF` names at `0x94d2ac` in file order; 4 = Thinker, 5 = Transcend

| claim | evidence | conf |
|---|---|---|
| alpha.txt has ONE `#DIFF` section, 6 rows in file order Citizen/Specialist/Talent/Librarian/Thinker/Transcend | `evidence/m335_difficulty_ladder.txt:2` | V MU4,5 |
| loader `push "DIFF"`@0x57ac56 -> `call 0x5ea431` -> fill `0x94d2ac`, `add esi,4`, `cmp 0x94d2c4`/`jl` = 6 iterations == 6 file rows (the count is the immediate, never read from the file) | `:3` | V MU1,2,3 |
| census with token-boundary matching over all addressing forms (7 scaled): exactly 11 sites on `0x94d2ac..0x94d2c4`, 0 literal-address STORES; scope: a register-indirect store elsewhere is NOT excluded | `:4` | V MU1,6,13,20 |
| ORDER: in 0x4ddaf8..0x4ddb60 the 11 fragments occur in the order base-load, `[esi]`, resolve, `push edi`, append, `add esi,4`, `inc edi`, `cmp 0x94d2c4`, `jl 0x4ddaff`; `edi` starts at 0 and the seed `ds:0x985aec`->`[ebp-0x494c]` precedes `call 0x5f1394` | `:5` | V MU10,11,14,15 |
| INDEX: `0x599405` `mov ecx,ds:0x985aec; mov edx,[ecx*4+0x94d2ac]`; both other readers are COUNTING loops 0..5 over the table (`cmp [slot],6` + `add eax,1`->same slot + `jmp` back) at `0x484cb3`,`0x485410` | `:6` | V MU7,12,19 |
| DOMAIN (geometry READ from the bytes, not from the script): base 0x94d2ac, bound 0x94d2c4 and clamp hi=6 with `hi*4 == end-base`, so the INCLUSIVE hi is the array LENGTH = one past the last row; of 169 `call 0x423af0` sites exactly 1 (`0x486f38`) is fed by an `0x8f0c11` load; cmp immediates on `0x985aec` = {1,2,3,4}+ebx (M332 reproduced); refund 3/jle + 4/jne => k=1 at 4, k=2 at >=5 = TRANSCEND (M330 refined) | `:7` | V MU8,9,16,17 |
| RIVAL killed: "0x94d2ac is not the difficulty names" — section string + row count + iteration count agree | `:8` | V MU3,4,5,13 |
| ACCEPT `7/7` digest `fb58bdc3307d6258` x2 (`:9-10`,`_rerun.txt`); harness `20/20` `6e0e05a8ffb388d8` incl. an ALGORITHM mutant (`--selftest` 3/3, `evidence/m335_mutate_selftest.txt:4`) | `evidence/m335_mutate.txt:22-23` | V |
| OPEN: a non-UI writer putting 6+ into `0x8f0c11`/`0x985aec` (the inclusive clamp would index `0x94d2c4`, outside the table); FUN_0060c555's API; index provenance of 0x44a1c8 / 0x48678f / 0x57c606 | - | lead |

## M337 (s318-chain1, x8, STATIC 8/8) — item table row order = alpha `#FACILITIES` FILE order (rec i = alpha row i-1)

| fact | evidence | status |
|---|---|---|
| `0x984d48` = `0x984d38`+`0x10`: fold `esi*3<<4` + `[eax+0x984d48]` reads rec idx's upkeep | G6 `:86` MU5,6 | V |
| loader 0x57a7ef..0x57a899 opens FACILITIES (0x691ccc, 0x5ea431) | G1 `:81` MU4 | V |
| the same loop writes recs 1..71 (`esi=0x984d74`=rec1+0xc, +0x30, end `0x985ac4`=rec72+0xc), rec 0 untouched; 1 line-read + 1 record step per iter => k-th line -> rec k | G2/G4 `:82,:84` MU1,3 | V |
| rec i == alpha row i-1: 6-vs-11 branch at rec 39 == alpha's first 11-token row (idx 38, alpha.txt:629) | G4 `:84` MU2 | V |
| one token per comma (`0x5ea985`); stores `+00,+0c,+10,+14,+18,+04,+18,+1c,+2c,+24,+28,+20` — supersedes M53i's +0x20/+0x28 (swapped) | G5 `:85` MU7,8 | V |
| "39" = consumers' bound (`cmp esi,0x27` @0x4f4a35), array ends rec 72; projects are this loop's (`jl` 0x57a866 skips 5 trailing stores) | G2/G7 `:82,:87` MU11,12 | V |
| OPEN: a non-UI writer putting 6+ into `0x8f0c11`/`0x985aec` (the inclusive clamp would index `0x94d2c4`, outside the table); FUN_0060c555's API; index provenance of 0x44a1c8 / 0x57c606 (0x48678f ANSWERED by ## M336) | - | lead |

## M336 (s318-chain2, STATIC 7/7) — `0x8f0090` = the DIFFICULTY byte of RECORD 1 (stride 0x176, frame `0x8eff18`); one UNCLAMPED `#DIFF` reader 0x486788; index 6 -> `0x94d2c4` — `evidence/m336_cell090_consumer.txt:1`

| claim | line | kind |
|---|---|---|
| ADDRESS census (3 forms; residue): loads at +2 = {0x486788} only, 6 stores, residue EMPTY, no address materialisation | `:1-14` | V MU1,MU4,MU9,MU14 |
| TARGET=FRAME+0x176+2; end `0x8f0ac8`; rec-1 ptr `0x8f008e` @0x525c42 | `:16-23` | V MU2,MU5 |
| chain: k=[ebp-0x8] (0x4865dc/5f5/77c) -> +1 -> imul 0x176 -> `[ecx+0x8eff1a]` -> `[edx*4+0x94d2ac]`, 0 gap | `:25-39` | V MU3,MU13 |
| walk stride `add eax,0x176` (0x4e24ab), 8 iters, iter 1 = TARGET; field+2 store sources = each register's own load (0x8f0c11 x3, lit 0) | `:41-56` | V MU8,MU11 |
| base/end READ 0x57ac74/0x57ac88 = 6 rows; only clamp 0x486f30 `FUN_00423af0(diff,0,6)` INCLUSIVE => 6 -> `0x94d2c4` | `:58-90` | V MU6,MU7,MU10,MU12 |
| OPEN: FUN_0058e7f0 >=6? — ANSWERED by `## M340`: ADMITTED verbatim (7/7); record indices assumed 0..7 | - | lead |

## B29 (s319 BUILD, zero box) — ITEM TABLE DERIVED from alpha through M337's LOADER LAW (`sim/itemtable.py`): `ALPHA_SHIFT=1` becomes a measured consequence (rec i = alpha row i-1); B4's four `table-later` DIFFERS rows are M46's alpha-INDEX numbering. ACCEPT `python3 -u -m sim.selftest --b29` -> `PASS B29: 9/9` rows `e4b1c98e68ff8685` print `377094bc16aa8f27` table `fa829fcd87cf43d5` (`evidence/b29_item_table.txt:85-86`), 2 runs + direct entry identical; harness `HARNESS PASS 9/9` `ae1f8e0292a59ed3`, NO-OP `[]` (`evidence/b29_mutate.txt:10`), ST 4/4.
- window == census: 72 recs, branch 39, widths 42/2/27 (`:77`) — V MU2.
- derived == sim table 38/38 name+upkeep; shift-0 differs 22 by value / 38 by name (`:78`) — V MU1/MU3.
- five pinned 5/5, raw 3 / disabled 2 == 0x744f28; at-index rival 0/5 by name (its value-only 3/5 is printed as NON-discriminating) (`:79`) — V ME4.
- four DIFFERS: at the alpha index 4/4 M46 values, at index+1 0/4 (`:80`) — V ME2.
- recs 39..71 built, 0 reachable (bounds 1..34); bound 39 == branch (`:81`) — V MU2/ME3; B28 re-run fed the derived table reproduces `705a4520c08c4062` / `99c52201f073499d` / `38bba29ab857654b`, honest touch `[]` (`:82`) — V MU1/MU3 (G7).
- OPEN: why M46 numbered by alpha line; rec 39..71 trailing columns; the 11-token re-sync INFERRED.

## M338 (s319-chain2, STATIC 8/8, review #357 hardened; ROTATED by s321-chain2) — the LAST two `#DIFF` readers: `0x57c606` is the literal loop counter 0..5; `0x44a1c8` indexes with a hall-of-fame record byte (+0x20) that is the faction's EFFECTIVE DIFFICULTY. FULL-LENGTH TABLE VERBATIM at `docs/named-archive-m341-rows.md:5` (sha1 `b82cddad74c8`); this stub governs, one line per claim

| claim | line | kind |
|---|---|---|
| table census: `.text` refs to 0x94d2ac = 2 base loads + 7 scaled readers {0x44a1c8,0x484cc9,0x485426,0x48678f,0x486f40,0x57c606,0x599405}, 0 stores | `:1` | V MU2,MU11,MU12,ALG1 |
| `0x57c606`: `xor esi,esi` precedes; only esi write is `inc` 0x57c6ca; `cmp esi,6`/`jl` = 0..5, same 6 as the loader end 0x94d2c4 | `:2` | V MU1 |
| `0x44a1c8`: 6-insn window, `dl=BYTE[eax+0x20]`, 0 insns between byte load and `[edx*4+0x94d2ac]`, 0 eax clobbers | `:3` | V MU3,MU15 |
| `[ebp-0x1c]` = a 0x983a10 record: 3 stores, the 0x4497b7 source is `lea eax,[edx*4+0x983a10]` with `(8-1)*(1+4)*4 = 0x8c` | `:4` | V MU4,MU5,MU13 |
| buffer = `hallfame.jhh`: fopen 0x64c980 window, read size 0x1324, zero-init 35x0x8c to 0x984d34 | `:5` | V MU6,MU7 |
| field +0x20: 7-function module, exactly 2 stores (0x44b15b from faction block +8, 0x44b612 struct copy) | `:6` | V MU8,MU9 |
| 0x94d438 = the faction's EFFECTIVE DIFFICULTY (creation 0x59eec3 branch, save-load 0x57ef57) | `:7` | V MU10,MU14 |
| rivals dead: index is not 0x985aec; 0x983a10 is not the faction array (0x8c vs 0x20bc); 0x57c606's index is not stored | `:8` | V MU7 |
| ACCEPT `PASS M338: 8/8` `1ae1563d47d0039e` x2, harness 16/16 `56455db0eadbedd7` | `:9` | V |
| OPEN: the +0x20 index is UNCLAMPED; a pref >=6 is ADMITTED (M340); 0x44a1c8's window is the HoF screen (INFERRED). **CLOSED by `## M341`:** the window's page arithmetic | - | lead |
## M340 (s320-chain1, pick (x6) residual = M338's #1 lead, STATIC 7/7, review #358 hardened) — FUN_0058e7f0 ADMITS a `Difficulty` pref >= 6: no bound anywhere in the read -> parse -> store chain, so index 6 reaches `0x94d2c4`, one dword past the six-row ladder. FULL TABLE VERBATIM at `docs/named-archive-m340-rows.md` (`dceab1fc162b3b519d1abce76800c81bb5bb4bd4`); every `:<line>` below is `evidence/m340_pref_admission.txt:<line>`; this stub governs, one line per claim  ACCEPT `scripts/m340_pref_admission.py` -> `PASS M340: 7/7`, rows `1cc44d0146a8b419`; harness `12/12`, NO-OP `[]`, `a2a1726721114b4d`.

| claim (one line) | evidence | conf |
|---|---|---|
| 18 `call edi` sites, each with a 6-push window holding one `push 0x100` (argc-6); exactly ONE key `0x692718` = PE `"Difficulty"` (`0x58e8a1`), lpDefault push IS the itoa(0) buffer `0x997120`; its store `ds:0x92bde8` @`0x58e8c6` is the only store to that cell | `:3-8` | V MU1,MU10,MU11 |
| `0x58e8a9..0x58e8c6` is 10 straight-line insns (0 jcc/jmp/ret), two stores (`ds:0x996be8` cursor, `ds:0x92bde8`) | `:6-18` | V MU2,MU7 |
| the stored eax IS `0x6287e2`'s return: both wrappers branch-free, no eax write after their call | `:19-21` | V MU2,MU3,MU9 |
| the parse chain compares CHARACTER CLASSES only; constants ∩ {2,3,4,5,6} EMPTY | `:22-42` | V MU4,ALG1 |
| POSITIVE CONTROL, same function: `Language`'s consumer has `cmp [ebp-0x4],0x4; ja` — no such bound on the Difficulty path | `:44-58` | V MU5 |
| ladder endpoints MEASURED (`0x94d2ac..0x94d2c4`), 6 rows from `cmp esi,0x6`; k=5 -> `0x94d2c0`, k=6 -> `0x94d2c4` | `:61-65` | V MU8 |
| the three pref-fed readers (`0x48678f`/`0x44a1c8`/`0x599405`) index TABLE at scale 4 from a memory-loaded index, def-use gap 0/0/2 insns with no branch | `:67-76` | V MU6 |
| OPEN: what `0x94d2c4` holds at runtime (box read); whether `0x57c7b0`'s paired write supplies a bounded value | - | lead |
## M342 (s322-chain1, ANALYSE, static, zero box; ACCEPT `python3 -u scripts/m342_completion_setter.py` -> **`PASS M342: 7/7 gates`**, table digest `2b88df5da5aeafe1` (PINNED, G7), 2 runs identical (`evidence/m342_completion_setter.txt:200,:218`); harness `scripts/m342_mutate.py` -> **9/9**, NO-OP `[]`, baseline green (`evidence/m342_mutate.txt:2,:12`)) — pick (x9) ANSWERED: the `base+0x8c` bit is SET by `or` through the mapper's mask at **11 addresses**, the API `FUN_004e44f0` first; the queue-pop is a NON-writer. (M329 rotated VERBATIM to `docs/named-archive-m329-rows.md:5`, sha1 `ccee72a56f16b4b4`.)

| claim | evidence | conf |
|---|---|---|
| the record array base is DERIVED as `0x95da10` from the owner site `0x440dbc` (`imul r,r,0x130` then a BYTE read of `0x95da14` = field +4), so `0x95da9c` = record+0x8c and is byte-identical to the charge routine's own read at `0x4f4837` (rival `+0x88` fails) | `evidence/m342_completion_setter.txt:4-8` | V MU1 |
| the field has exactly 2 writer idioms: **11 direct constant-form stores** in exactly 2 Ghidra functions (`FUN_0041cf20` 1 whole-byte copy, `FUN_004e47d0` 7 `or` + 3 copies) and **9 pointer-form `lea` sites, 9/9 resolved to a store through that register** (2 copy / 4 `or` / 3 `and`) | `:9-72`,`:86`,`:204` | V MU2/MU8 |
| SET = 11 `or` addresses (`4e4528 4e4b5a 4e4b87 4e4bec 4e4c16 4e4c3d 4e4c83 4e4d81 4f0ec0 4f3ebc 4f3f4c`); CLEAR = 3 `and` (`4e4546 4f38bb 4f49e1`, the last inside the charge routine `FUN_004f47f0`) | `:210-216` | V MU2/MU8 |
| the API `FUN_004e44f0` (92 B) is the first SET address: `or BYTE PTR [eax],cl` @`0x4e4528` after the 304-fold (`0x4e4512-0x4e451e`), index = mapper out1 slot `[ebp+0x8]`, mask = out2 slot `[ebp-0x4]`; its AND twin @`0x4e4546` clears | `:99-113`,`:205` | V MU3 |
| 27 call sites in 8 functions: 16 push set=1, **8 set=0, 3 variable** — M344 re-derived this with a 16-insn push window; the shipped 16/7/4 read `0x40dd3c` as '?' because its `push 0x0` sits 7 instructions back | `:129-158`,`:206`; `evidence/m344_completion_caller.txt:36-38` | V MU4 (M344 MU1/MU2) |
| the queue-pop `FUN_004ef5d0` (244 B, 3 direct callers all inside `FUN_004ef6d0`) has 0 references to `0x95da9c` and 0 API calls: the pop does not stamp | `:160-177`,`:207` | V MU5 |
| inline grant `FUN_004e47d0`: 7 ORs + 3 copies, 7/7 OR masks loaded from a stack slot the mapper filled | `:180-191`,`:208` | V MU6 |
| the printed digest is PINNED by G7 - the ACCEPT anchor cannot drift silently | `:200`,`:209` | V MU7 |
| OPEN: which of the 27 API call sites is the production-completion call; 3 pointer writers (`0x4f38b0`, `0x4f3eb1`, `0x4f3f3e`) sit in regions the Ghidra index does NOT name (semantics unidentified); projects 39..71 unmeasured | - | lead |

## M339 (s320-chain2, STATIC 7/7, review #359 hardened) — 0x5f1394 = the modal SCREEN RUNNER; its return is the screen OBJECT's `+0xa40` result cell, and the difficulty dialog writes that return into `ds:0x985aec` + all 8 faction blocks. FULL TABLE VERBATIM at `docs/named-archive-m339-rows.md` (`9a93e8acca0a99ac0779babaa63a94ae5afca934`); this stub governs, one line per claim; every `:<line>` below is `evidence/m339_modal_runner.txt:<line>`

| claim (one line) | evidence | conf |
|---|---|---|
| FUN_005f1394 = 11,207 B / 2,235 insns, `ret 0x8`, SEH 0x66f786, `sub esp,0x38c`; vtable lane {15c,160,164,16c,170} | `:1`, `:42-43` | V MU1,MU2,MU9 |
| 7 exits all through the ONE SEH-restore label; `[obj+0xa40]` read ONCE, written 0x; +0xa44 never read | `:43-44` | V MU3,MU7,ALG_A1 |
| 94 direct thiscall sites: 76 `lea ecx,[ebp-…]`, 14 pointer slots, 3 register, 1 global 0x9210a8; none receiverless | `:45` | V MU4,MU10 |
| FUN_004ddaa0: seed 0x985aec -> obj+0xa44, `call 0x5f1394`, `test eax`/`jge`, store-back + 8-iteration faction loop (0x20bc) | `:46` | V MU5,MU6,MU8,MU11,MU12 |
| rivals dead: runner is not the chooser (0 refs in 2,235 insns); return is not a dialog ID (only -1/0 immediates) | `:47` | V MU7 |
| ACCEPT `scripts/m339_modal_runner.py` -> `PASS M339: 7/7` `d76a5e83770b77bb` x2; harness 13/13; `--selftest` 3/3 | `evidence/m339_mutate.txt:17` | V |
| OPEN at s320: writer of `[screen+0xa40]` — CLOSED by M343 (3 dialog-family methods) | - | lead |
## M341 (s321-chain2, STATIC 10/10; ACCEPT `python3 -u scripts/m341_hof_window.py` -> `PASS M341: 11/11`, `digest=1cfdea39295dadce`, 2 runs identical; harness `scripts/m341_mutate.py` 19/19 `e1c003e81552f53f`) - the HoF record window is `5*n - 5 + s`: THREE .text sites decode to the same law, so the 35 records at 0x983a10 are 7 blocks x 5 rows and page index 8 lands on the terminator. FULL-LENGTH TABLE VERBATIM at `docs/named-archive-m343-rows.md:5` (sha1 `bcf9ba24a3eb4efb`); this stub governs, one line per claim

| # | claim (one line) | conf |
|---|---|---|
| 1 | SITE A 0x449793/96 = `5*[obj+0x59f4] + [obj+0xa918] - 5`, 0 other ebx defs | V MU1,MU2,MU8,MU9,ALG1 |
| 2 | SITE B 0x44af9b/9e = `5*[obj+0xa4c] + slot - 5`; `[obj+0xa4c]` <- `ds:0x91b5b4` at 0x44aed9 | V MU3,MU11,MU13,MU14,MU15 |
| 3 | SITE C 0x44b5a7..b9 insert-shift: dst = src + 0x8c, k in {0..3} | V MU10,MU16,MU17 |
| 4 | extent: base 0x983a10 / stride 0x8c / 35 records = 7x5 / index 35 = terminator 0x984d34 | V MU4,MU5,MU6,MU7 |
| 5 | NO CLAMP: the only direct 0x59f4 ref in 781,379 insns is the load 0x44970f | V MU8 |
| 6 | the 6-probe loop tests COLUMNS of ONE record (reload 0x449982), 6 != rows | V MU12,MU18 |
| 7 | OPEN: +0x59f4's writer (lead: a control at obj+0x5970); page 1..7 = faction block is INFERRED | lead |
## M343 (s323-chain2, STATIC 9/9, review #365 hardened) — the M339 OPEN `[obj+0xa40]` writer: THREE dialog-family methods publish the SELECTED item there; the runner only reads it

ROTATED VERBATIM to `docs/named-archive-m343-a40-rows.md` (sha1 `a7f9573ef60c5314`); this stub governs: one line per claim; acceptance `scripts/m343_a40_writer.py` -> **`PASS M343: 9/9`** `bcdace84a0352b4a` x2; harness 12/12 `[]`.

| claim (one line each; full rows in the archive) | evidence | conf |
|---|---|---|
| census: 97 refs name 0xa40 = 25 indexed (12 fns) + 72 field, all dword (47 stores / 25 reads); 0 `lea ..+0xa40`, 0 `,0xa40` immediate | `evidence/m343_a40_writer.txt:5-22` | V MU1 |
| writers: FUN_005f5759 x4, FUN_005f58fa x3, FUN_005f5a11 x2 (ds:0x9977f0); runner FUN_005f1394 = 1 read, 0 stores; ctor FUN_00405ef0 0 refs | `:66-77`,`:24-26` | V MU4,MU5,MU2 |
| receiver fingerprint = {[+0x21d0] container, [+0x2350] state}: exactly 4 fns; the '>=3 of {21d0,2350,30a8,3100}' rival admits 2 more | `:28-64` | V MU3,MU9 |
| identity chain 0x5f13b2 -> 0x5f3f45 `[ebp-0x394]+0xa40`; 5a11 reloads ds:0x9977f0 and both stores reach it (10 links, adjacency asserted) | `:79-88` | V MU7,MU10 |
| value law: each writer publishes {0, `[this+0x2228]->[+8]->+0xec`, `FUN_005fdcf7(+0x21d0)`}; the -1 @0x5f581c needs arg==-2 and `[+0x30a8]&0x40` | `:89-99` | V MU6,MU8,MU11 |
| ACCEPT `scripts/m343_a40_writer.py` -> `PASS M343: 9/9` `bcdace84a0352b4a` x2; harness 12/12 `[]` | `:118`, `evidence/m343_mutate.txt:25` | V MU0 |
| OPEN: dispatcher of the +0x64 slot (19 `call [reg+0x64]`, 0 direct); the container past +0xec; consumers of `[this+0x3100]` | - | lead |
## M344 (s323-chain1, ANALYSE, static; ACCEPT `scripts/m344_completion_caller.py` -> **`PASS M344: 8/8 gates`**, digest `034bf0e1a1606d2c`, 2 runs identical (`evidence/m344_completion_caller.txt:148`); harness `scripts/m344_mutate.py` -> **10/10**, NO-OP `[]` (`evidence/m344_mutate.txt:14`)) — NO API caller completes production: the stamp is the base screen's inline `or` @`0x4f0ec0`.

ROTATED VERBATIM to `docs/named-archive-m344-rows.md` (sha1 `e7b59fa35e2635c8`); this stub governs: one line per claim; acceptance `scripts/m344_completion_caller.py` -> **`PASS M344: 8/8 gates`** `034bf0e1a1606d2c` x2; harness 10/10 `[]`.

| claim (one line each; full rows in the archive) | evidence | conf |
|---|---|---|
| all 27 item args resolve (imm 18 / callret 3 / clamped 2 / loopctr 2 / param 2); split 16 set=1 / 8 set=0 / 3 variable; 0x40dd3c is the only divergent row | `:4-38` | V MU1,MU2,MU3 |
| 0/27 items' resolved class is QUEUE; 0/8 caller fns calls the pop | `:34`,`:40-49`,`:141` | V MU4 |
| the 4 register-item set=1 sites: 0x41c6f8, 0x41d8fc, 0x508c85/0x508cee | `:127-131` | V MU5 |
| stamp = `or BYTE PTR [eax],cl` @0x4f0ec0 in FUN_004ef6d0; 0x86 precedes the pop @0x4f0f46 | `:51-70`,`:143` | V MU6,MU8 |
| the block spends `[edx+0x40]` by edi then reads `[edi*48+0x984d38]`, edi unwritten between | `:112-124` | V MU7 |
| the build-finished posts go to the text bank whose consumer M348 found (Script.txt `#PRODUCEXQ/G`); FUN_00636b1e is the Create Session dialog | `evidence/m348_slot_template.txt:63-69` | V MU12 (M348) |
| the 8 caller ROLES; `edx` at 0x4f0ca1 = the base record; +0x40 = accumulated minerals; edi = the completed item | `:40-50` | INFERRED |
| ACCEPT `scripts/m344_completion_caller.py` 8/8 `034bf0e1a1606d2c` x2; harness 10/10 `[]` | `:148`, `evidence/m344_mutate.txt:14` | V MU0 |
## M345 (s324-chain2, 12/12) — the dialog family `+0x64` commit slot has no .text dispatcher

ROTATED VERBATIM to `docs/named-archive-m345-rows.md` (sha1 `907d07053aedb079`); this stub governs: one line per claim; acceptance `m345_slot64_dispatch` -> **`PASS M345: 12/12`** `833faf38e189ad40` x2; harness 11/11 `[]`.

| claim (one line each; full rows in the archive) | evidence | conf |
|---|---|---|
| slot `0x5f58fa` = 5 data dwords, all a family vt+0x64; 0 `.text` operands | `evidence/m345_slot64_dispatch.txt:3-10` | V MU1,MU3,MU2 |
| ctor 0x405ef0: 0x67164c at +0, CPane 0x671644 at +0x444 -> its `+0x6c` IS the primary `+0x64` | `:16,:93` | V MU1,MU4 |
| trio `+0x60`/`+0x64`/`+0x68` = 5f59bf ret8 / 5f58fa ret4 / 5f59e8 | `:12-15` | V MU5 |
| universe = 19 `[r+0x64]` + 18 `[r+0x6c]` calls, 0 jmp, 0 in the dialog module | `:18-57,:86-89` | V MU6,MU10 |
| arity {0:3,1:5,5:8,6:3}: 5 fit ret 4 = 3 MEMBER + 2 self, none a dialog | `:59-65,:100` | V MU8,MU9 |
| module's 4 `[r+0x64]` are movs; 5f49ad/b9 swaps `[this+0x2240]+0x64` | `:67-77,:102` | V MU7,MU10 |
| ACCEPT `m345_slot64_dispatch` -> `PASS M345: 12/12` `833faf38e189ad40` x2; harness 11/11 `[]` | `:104`, `evidence/m345_mutate.txt:17` | V MU0 |
| OPEN: MEMBER-receiver classes (+0xf624/+0xd9ec/+0x3870/+0x270c) untyped | - | lead |
## M346 (s325, ANALYSE, static; M348 qualified the 'alert' framing: the bank is the general text-variable bank; ACCEPT `scripts/m346_alert_raiser.py` -> **`PASS M346: 18/18`** `ab4f0ca8123245bb` x2 (`evidence/m346_alert_raiser.txt:110`); harness 22/22 `[]` (`evidence/m346_mutate.txt:25`)) — the build-finished ALERT = 2 posts into a 10-slot `$`-token table; `0x985b10` is NOT its channel.

| claim | evidence | conf |
|---|---|---|
| 0x4f0f46 = `call 0x4ef5d0` (the queue pop) and between it and 0x4f0f9b the block posts exactly 2: 0x6265a2 kind 1 @0x4f0f78, 0x626634 kind 2 @0x4f0f96 (14 in FUN_004ef6d0); payloads `[edi*48+0x984d38]` / `0x927894+1436*idx` | `:5-17`,`:27-37` | V MU1,2,3,4,5 |
| table: payload 0x999ff4+4k, owner 0x999fcc+4k, text 0x99a01c+0x100k, `cmp k,0x9` + `jle` body = TEN slots | `:41-46` | V MU6,7,8,9 |
| expander FUN_00625b20: 4 reads 0x999fa4 + 4 `shl REG,8; add REG,0x99a01c` (same register); tokens 0x69911c `$`/`$NUMBER`/`$NUM`/`$HEX`/`$LINK<` | `:59-62` | V MU10,11,12,13,14 |
| RETRACTED by M348 (G12, MU12): FUN_00636b1e is the multiplayer CREATE SESSION dialog - it draws `Session Name:`/`Maximum Players:`/`Session Password (Optional):` (0x6998b0/c0/d4) and re-loops while strlen(slot1) > 0x10 (session-name bound), so the slot 0/1/2 first-byte clears @0x63730e,15,1c are that dialog's field init, NOT a drain | `evidence/m348_slot_template.txt:76-79` | V MU12 |
| RETRACTION: 0x985b10 = player mask (M96,M308), not the channel: 0 refs in the 5 alert fns and the post window, 0 stores in FUN_004ef6d0 | `:81-83` | V MU18,19 |
| no pop/consume: the only first-byte writers of the 10 text slots are the 2 publishers + the three field-init clears inside the Create Session dialog (0x63730e/15/1c) - M348 re-read | `:86-88` | V MU20 |
| OPEN (narrowed): the `inc/add` counter 0x999f90 family is NOT measured; the template consuming slots 1/2 was ANSWERED by M348 - a Script.txt record, not .rdata (`## M348`); the bank is a general 10-slot text-variable bank (63 refs / 30 fns), not an alert-private queue | - | INFERRED |


## M348 (s326, ANALYSE, static; ACCEPT `scripts/m348_slot_template.py` -> **`PASS M348: 12/12`** `a3d46c017673526a` x2 (`evidence/m348_slot_template.txt:87`); harness 13/13 `[]` (`evidence/m348_mutate.txt:14`)) - slots 1/2 are consumed by a Script.txt record (`#PRODUCEXQ/G`), NOT an .rdata string; M346's `drainer` RETRACTED.

| claim | evidence | conf |
|---|---|---|
| the 10-slot bank (payload 0x999ff4, owner 0x999fcc, text 0x99a01c stride 0x100, numeric 0x999fa4, k<=9) is GENERAL: 63 sites in 30 fns, 7 sites build `k<<8+0x99a01c` (4 expander, 2 setters, 1 modal @0x5f12ee) | `:4-7`,`:58-61` | V MU1,MU11 |
| setter A FUN_006265a2(index, LABEL-ID) resolves via table 0x997b28 (`call 0x61482f`) then strcats; setter B FUN_00626634 copies a LITERAL; both clear the slot byte, return 3 above k=9 | `:10-19` | V MU2,MU3 |
| completion block: slot 1 = `[0x984d38+edi*48]` (item label id) @0x4f0f78; slot 2 = `0x927894+ebx*1436` (base name) @0x4f0f96 | `:21-27` | V MU4,MU5,MU6 |
| key = `PRODUCEX`(0x68cfc4)+`Q`/`G` into 0x997120 (fallback `PRODUCE` 0x68cfe8) -> FUN_0048f100 @0x4f122a, which sets slot 0 = `[0x8f0d60]+0x13` @0x48f20f | `:29-44` | V MU7,MU8 |
| consumer = Script.txt: `#PRODUCEXQ/XG` read slot 1 (`$ITEM1`, XQ also `$NUM1`), no slot-2; `#PRODUCE2/3` read `$<M1:$FACTIONADJ2>`; .rdata has 0 `$<` (only `$LINK<`) | `:46-55` | V MU9,MU10 |
| RETRACTION: FUN_00636b1e = multiplayer Create Session dialog (labels 0x6998b0/c0/d4, strlen(slot1)<=0x10, jmp 0x63724e); M346's 'drainer' withdrawn | `:63-69` | V MU12 |


# M350 (STUB — rows VERBATIM: `docs/named-archive-m352-rows.md`; `:N` = a line of `evidence/m350_pref_cowriters.txt:1-162`)
| claim | ev | conf |
|---|---|---|
| FUN_0058e7f0 = the block's only profile-backed INITIALISER | `:3-16,162` | V MU1,2,14,15 |
| EXTENT | `:54-69,157` | V MU3-5 |
| 57 co-refs / 32 scalar co-stores in 14 scalar fns (10 store + 4 read-only) | `:70-95` | V MU8,11,12,13 |
| LAW | `:96-133,160` | V MU6,7,9,15 |
| publisher 0x58f3d0 | `:144-155` | V MU10 |
| ANSWERED (M352): `ds:0x6926ec` = literal "Prefs Format"; 8 `call edi` = WritePrivateProfileStringA | `evidence/m352_persist_writeback.txt:124-131` | V M352 MU10,MU2 |
## M347 (s324-chain2, STATIC 12/12) — M341's OPEN `+0x59f4` WRITER: the `+0x5970` child selector; the page bound IS 7

| claim | evidence | conf |
|---|---|---|
| 0x59f4 = sub 0x5970+0x84; ctor 0x44ba40 -> 0x6290b0; vtable 0x674c5c+0x30 = 0x4495e0 loads it @44970f | `evidence/m347_page_writer.txt:2-4` | V MU1,MU2 |
| ctor 0x6290b0 never writes +0x84 (0 stores); init 0x629169 writes -2 | `:5` | V MU3 |
| 4 stores only: -2 @629187, -1 @6292ca/@62936e, id @629363; 0 lea-alias | `:6-11` | V MU4,MU5 |
| call SET = 4 (init/register/select x2), receivers lea[reg+0x5970] x3 + abs 0x74df70 (=0x748600+0x5970) | `:12-18` | V MU6,MU16 |
| ids {1..7}: 7 children (mov/add/cmp pinned), counter inc'd and reloaded AFTER the store @4493e1/4493f8; Init 0x5f9e85 -> +0xa78; selector compares +0xa78 | `:19-24` | V MU7-MU10,MU17 |
| writers: 7-block scan -> block+1 (pushed 0x44ae6b); player = ds:0x91b5b4 pushed 0x44b725 = SITE B cell [screen+0xa4c] (1..7, M312) | `:25-28` | V MU11,MU12,MU18 |
| no guard; -1 store = the NOT-FOUND branch (je @629331 -> 0x62936b); -1/-2 index BEFORE 0x983a10 (0x983498../0x9831dc..) | `:29-33` | V MU13,MU19 |
| rivals DEAD: ctor-zero, census (1 plain + 12 [r+r*4+] outside 0x44xxxx), 0-based ids, cap-32, receiver-blind 2/35 | `:34-41` | V MU3,MU14,MU10,MU7,MU15 |
| ACCEPT `scripts/m347_page_writer.py` `PASS M347: 12/12` `3fadfd6e6d26e64c` x2; harness 20/20, coverage 12/12 | `:55-57` | V MU0 |

## M349 (s326-chain2, 13/13) — M68/M69 `NEG_TYPE`: a negative queue head is the NEGATED UNIT TYPE
| claim | evidence | conf |
|---|---|---|
| `FUN_004ef6d0` slot 0: `cmp 0xffffffda` (-38) -> 0x4ef9b3, `jge 0x4efa2c` facility, `neg ecx` @0x4ef89f -> item = -head = unit type; 19 insns | `evidence/m349_unit_id.txt:4-23` | V MU13 |
| G4 pins all 30 TABLE-2 rows (bands 39/34/38, 2nd index type-39, sentinel -38, split 0x40) | `:31-62` | V MU2,MU3,MU7,MU17 |
| facility leg `cmp ebx,0x40` / `jl` -> id<64 stamps; id>=64 sets bit 2 @0x98adb8, stamps only if clear | `:24-30` | V MU16,MU6 |
| unit cost `imul [0x984d44+48*type]` (= 0x984d38+0xc, stride 0x30; 72-record identity = M337) | `:75` | V MU4 / INF |
| mapper DERIVED from its 17 insns (masks 7/7, `sar 3`, `shl cl`): byte id/8 truncating, mask 1<<(id&7); 203 calls exact | `:77`,`:98` | V MU19,MU20,MU11,MU12 |
| both sites: base 0x95da9c, 304 stride; unit leg ANDs @0x4ef97a, facility leg ORs @0x4f0ec0 | `:83-86` | V MU14,MU15,MU5 |
| recorded B31 heads ARE 321,-2,-8,2,-3,-6 (4 unit + 1 facility + 1 >=64); `>31` NOT unit-encoded | `:64-71` | V MU9,MU21 |
| rivals DEAD: -(design-192) -> -4 vs trace -6 (`evidence/m68_key_run_attempt1.txt:12`, `evidence/m69_cursor2.jsonl:8`), "-39 sentinel", logical shift | `:92-97` | V MU8,MU18,MU22 |
| ACCEPT `scripts/m349_unit_id.py` `PASS M349: 13/13` `fa2d81797551dae5` x2; harness 22/22, 13/13 | `:101-102`, `evidence/m349_mutate.txt:30` | V MU0 |
## B32 (s327 BUILD; ACCEPT `python3 -u -m sim.unitoracle` -> **`PASS B32: 10/10`** `e6875c63c8c2f911` x2 (`evidence/b32_unitoracle.txt:53-54`); harness **13/13** `155781675e5086a1` (`evidence/b32_mutate.txt:16`)) — the UNIT leg on the recorded trace: 4/4 unit heads stamp the mapper bit, 0/2 facility-range do, the post-pop head 0/6. NAMED cap: B30 rotated VERBATIM to `docs/named-archive-b32-rows.md:5`, sha1 `7a11114cc0b2ee78ef113acdb95260b5228cffa0`, `--verify` 7/7 (`evidence/b32_named_rotate.txt:9`). `:N` = a line of the ACCEPT evidence.

| claim | evidence | conf |
|---|---|---|
| heads `[321,-2,-8,2,-3,-6]` = 4 UNIT / 1 FAC / 1 BIG; local decode == M349's 30-row `UNIVERSE` row-for-row | `:43` | V MU11 |
| before-sample head PER LEG: 4/4 unit heads gain exactly the mapper bit (`-2`->2, `-8`->8, `-3`->3, `-6`->6); 0/2 facility; B31's bulk rule 0/6 | `:25`, `:44` | V MU3,MU7 |
| the AFTER-sample head scores 0/6 -> the stamp reads the head BEFORE the pop (M344's order) | `:28`, `:45` | V MU5 |
| before OR mask == the recorded after window at 4/4 unit boundaries; only the mapper byte moves | `:35-39`, `:47` | V MU6,MU13 |
| facility side: 321 -> byte 40 (off the 8-byte map, 1 refusal); facility 2 at Virgin Soil predicts `04 00 00 08 00` vs recorded `10 00 00 00 00` | `:34`, `:37`, `:48` | V MU10 |
| 2 losses, both on the 2 non-unit rows; each unit row's gain set is exactly its bit | `:49` | V MU9 |
## M351 (s328-chain2, 15/15) — the CHOOSER producer: a unit row's item IS the negated TYPE ORDINAL
| modal 0x496ad0: `and eax,0x20` @0x49772a, `neg eax` @0x49777c; item = row+4 (0x401940), flags = row+8 (0x495480) | `evidence/m351_type_producer.txt:95,100-101` | V MU1,MU2,MU10,MU11 |
| rows: A idx<0x80 item=cand[idx]@0x9267e4 \|0x20 -> +item; B i=1..0x47 item=i flags=0x4960f0(i)\|0x10 -> -i; 0x4960f0 in {0,1,2,3} so 0x20 never set | `:97-99,109` | V MU5,MU8,MU9,MU17,MU18 |
| i is the TYPE ORDINAL: 0x984d38+0x30*i name / 0x984d44 cost (= M349's) | `:97,104` | V MU4,MU5 |
| chooser uses -i: afford 0x495c2f, queue-slot cmp 0x495e5c @0x495566; A cmps +item @0x495aef | `:108` | V MU15,MU19 |
| 0x418b57 stores it to ds:0x8f0d60+0x50 on pos==0; 0 negs in 381 insns | `:102` | V MU12,MU13 |
| RETRACTED: M68's "195 -> -3" is a STALE cell read (m68 verdict line parses "re-sorted"); cell = row counter @0x495b00 | `:107` | V MU14 |
| ACCEPT 15/15 `504c7342fb16273b` x2; harness 20/20 | `:112-113` | V MU0 |

## M352 (s328-c3, static; ACCEPT `scripts/m352_persist_writeback.py` -> **`PASS M352: 7/7`** `d553194a`, x2 `c8bbfda4` (`evidence/m352_x2.txt:4`); harness 13/13; `:N` = a line of `evidence/m352_persist_writeback.txt:1-140`)
| claim | ev | conf |
|---|---|---|
| 8 `call edi` = 1 target: edi@0x58f106 from `ds:0x6710fc` = KERNEL32!WritePrivateProfileStringA (.rdata import slot; its own dword names it); 0 mem-indirect | `:18-25` | V MU1,MU2,MU13 |
| 13 write keys = 8 direct + 5 via FUN_0058f030; 12 blocks LOAD a block cell (11/11 scalars + Custom World array; window presence), `Prefs Format` = itoa(0xb) stamp | `:27-45` | V MU3-MU7 |
| read = 5 fns / 5 refs / 35 keys; 13/13 written keys read; `Laptop`+`Language` read, written NOWHERE (33 write sites) | `:47-122` | V MU8,MU9,MU12 |
| RETRACT M350: `ds:0x6926ec` = the .data literal "Prefs Format"; lpKeyName at 7 push sites; no store names the VA, 0 materialisations | `:124-131` | V MU10,MU11 |
| rivals R1 vtable / R2 write-only / R3 read==write / R4 mutable pointer all refuted | `:133-140` | V MU1,MU13 |
| OPEN: what `Laptop` selects (masks @0x58ea12/0x58eb2b); twins return 0x3a7168/0x327168 | `:97` | lead |

## M353 (s329-chain1, ANALYSE, STATIC 11/11 + harness 11/11, zero box) — the `0x999fa4` numeric band: ONE indexed filler + four `$`-token consumers

ACCEPT `python3 -u scripts/m353_numeric_band.py` -> **`PASS M353: 11/11 gates`** digest `367fdae1d78979e5`, two renders identical (`evidence/m353_numeric_band.txt:87`); harness `python3 -u scripts/m353_mutate.py` -> **`HARNESS PASS 14/14`** digest `fd143532b283b01b` (`evidence/m353_mutate.txt:17`). `:N` = a line of the ACCEPT evidence (`evidence/m353_numeric_band.txt:75-87`).

| claim | evidence | conf / mutant |
|---|---|---|
| band = 10 dwords `[0x999fa4,0x999fcc)`: own/pay/txt bases + stride DERIVED from the writer body (0x28 apart, `shl 8` -> 0x100, 10*0x100 -> 0x99aa1c) | `:77` | V MU3/MU14 |
| 16 refs = 11 absolute + 5 `[reg*4+0x999fa4]`; stores = 3, all `mov` (no xchg/movnti form) — SCALED `0x626597`, absolute `0x442642`, absolute `0x626fd7` | `:75,76` | V MU1/MU2 |
| FILLER = `FUN_00626581` (33 B): `k>9` returns 3, else `numeric[k]=v` and returns 0; 260 call sites, 242 literal k, histogram `0:131,1:75,2:23,3:7,4:3,5:2,6:1`, ZERO above 9 | `:38,39,78,79` | V MU4/MU5 |
| M325/M324's `W={442642,626fd7}` was an ABSOLUTE-address census: SUPERSEDED here (the scaled store `0x626597` was invisible to it) | `:76,84` | V MU2/MU10 |
| CONSUMERS pinned per ADDRESS: `$NUMBER`@625c2c, `$NUM`@625cec, `$HEX`@625e4b, each `itoa(v,buf,10)`; the 0xa is ARG3 (3 pushes before the call, forwarded by `0x64f980`) -> `$HEX` prints DECIMAL | `:80,81` | V MU6/MU7/MU12/MU13 |
| the 4th read is the `$#k` PREDICATE (`cmp numeric[k],1` -> `setne`), k = char-0x30 with NO bound — the `$k` path does bound (`cmp k,0xa`) | `:82` | V MU8 |
| `$#` at k>=10 leaves the band: k=10 = owner[0], 20 = payload[0], 30 = text[0] | `:83,70` | V MU9 |
| OPEN: what the `$#` flag gates; numeric[0] is DUAL-USE (the 0x442642 cheat clamp and the ENERGY read @0x4e032c) | - | lead |

## M354 (s329-chain2, STATIC 11/11) — SECTION A's identity: the positive chooser rows ARE the 0x98ad88 unit-type/design rows (M351's OPEN closed; the leg NOUNS of M349/M351 retracted). `:N` = a line of `evidence/m354_design_row.txt:1-91`
| claim | evidence | conf / mutant |
|---|---|---|
| A rows are the 0x98ad88 rows, stride 0x34: three imul sites take the item from [ebp-0x2c] (filled from `[..*4+0x9267e4]` @0x4956d6) and reach +0x00 name, +0x29 weight, +0x2a class | `:1-8,72-73` | V MU1,MU2,MU3,MU19 |
| A's flags fn 0x496050 over its PARSED extent 0x496050..0x4960c7 reads EXACTLY +0x2a and +0x30 (2 refs) and gates on item<0x40 / flags&4 (bit 2); B's 0x4960f0 over 0x4960f0..0x496150 has ALL 10 PTR operands on stack slots or its own 0x4961xx tables, 0 calls, returns {1,2,3}+xor | `:10-18,74-75` | V MU4-MU7,MU20 |
| sign follows the SECTION: A `or al,0x20` @0x495a8d, B `or al,0x10` @0x495dff, modal `and eax,0x20`/`neg` @0x49772a/7c | `:37-41,76` | V MU8-MU10 |
| builder 0x596000: `cmp 0x40`, `shl 6`, mask 0x8000003f (&0x3f==0x3f), store to 0x9267e4 — k<0x40 -> k, else owner*0x40\|(k&0x3f) (64 shared + 64 owner); item*0x34 via 13*i<<2 | `:19-36,77-78` | V MU11,MU12,MU21,MU26 |
| validator 0x5a73f0 reads {+0x24,+0x2a,+0x2c,+0x30,+0x32}; flags bit0 @0x5a7402, class @0x5a748b, owner mask 1<<owner (`shl ebx,cl`) | `:79` | V MU13,MU14 |
| field atlas (12 offsets consumed): +0 name, +0x20 abil, +0x24 domain, +0x25..+0x28 components, +0x29 weight, +0x2a class, +0x2c mask, +0x30 flags, +0x32 pre-req; the offset SET is gated (G8) and four SEMANTICS are gated (G10: name->std::string 0x64b9e0, weight x 0x4e40a0, class==8, +0x32 WORD -> tech table 0x92fdd4); the component NOUNS stay INFERRED | `:55-70,80,83-88` | V (set+4 semantics) MU3,MU14,MU22,MU24 / INFERRED (nouns) |
| **RETRACTION (narrows M349/M351):** the decoder legs are identified by their TABLES: `test ecx,ecx`/`jge 0x4efa2c`/`neg ecx` pinned, head<0 reads the 0x984d38/0x30 cost +0x0c (M337 `#FACILITIES`), head>=0 LOADS+STORES the 0x98ad88 row +0x30. M349's per-leg nouns (neg=UNIT, +2=FACILITY) and M351's "unit row" for section B are INVERTED; the arithmetic and the sign split stand | `:42-54,81` | V MU15,MU16,MU23 |
| ACCEPT `python3 -u scripts/m354_design_row.py` -> **`PASS M354: 11/11`** `dd5e689e8d9af320`, x2 identical (`evidence/m354_x2.txt:91`); `scripts/m354_mutate.py` **23/24 scored, NO-OP ['MU25']**, measured coverage ALL 11 gates {G1,G2,G3,G4,G5,G6,G6b,G7,G8,G9,G10} | `:91`, `evidence/m354_mutate.txt:30` | V MU0 |
| OPEN: the game noun of +0x25..+0x28; whether the +0x30 bit2 stamp is the prototype build (INFERRED); NAMED M312 rotated VERBATIM to `docs/named-archive-m354-rows.md` (sha1 `5e8df0971a3d9bae`, `scripts/m354_named_rotate.py --verify` PASS) | - | lead |
