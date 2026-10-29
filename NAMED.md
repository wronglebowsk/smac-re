# NAMED — functions we can name from evidence

Running list. Append-only; one row per function, evidence in the notes column. Names are
labelled with confidence (`H` = high, `M` = medium) and the *reason* — never a vibe.

Read code with `scripts/fn.py <addr> [--max N]`; metadata with `scripts/fn.py <addr> --index`.

| addr | proposed name | conf | evidence |
|---|---|---|---|
| `0x5c9fc5` | `ui_layout_three_parts(rect, obj)` | M | 383 callers (near the dialog count). Takes a rect (`*p`, `p[1]`, `p[2]`, `p[3]`) and an object with three parts `obj[0..2]`; for each part computes `pos - *(part+0x18/0x1c)` (size fields), then calls `0x5dd09c(x, y, w, h, …)`; if `obj[8]` is set also calls `0x5c1187` with both old and new coords plus `*(part+0x18/0x1c)` and `obj[9]` — i.e. "move/draw each part inside the rect, plus a second draw pass when a flag is set". |
| `0x5dd09c` | `draw_rect_stateful(x, y, w, h, a, b)` | M | Saves `DAT_00698bec` / `DAT_00698bf0` (a two-word graphics state: most likely clip origin), calls `0x5dd0fc(x, y, w, h)`, then restores them — a with-temporary-state wrapper around the actual primitive. |
| `0x598340` | `file_open_and_dispatch(file)` — magic sniffing | H | 413 B. Reads a 9-char magic (`FUN_005705f0`) then `_strcmp` against `s_TERRAN_00692fd8` and `s_TERRANMAP_00692fe0`; on match demands a 4-byte version `>= 5` (`FUN_0064cc00(&v,4,1,f)`, `-(mode!=0) & 0x51 + 5`), clears per-map globals (`DAT_0091b5c4`, `DAT_00985af0/af4`, `DAT_0091b5b8/bc`), then calls the loader `FUN_00597a70(f, 0, is_map)`. |
| `0x597a70` | `load_map_or_scenario(file, mode, is_map)` | H | 621 B but **~80 KB of stack**: `auStack_13600[67040]`, `local_3020[11488]`, `local_340[772]`; reads **0x31C (796) bytes** into the header buffer, then a 4-byte field, then a **0xE5E0 (58 848)-byte** block via `FUN_0064cc00` / `FUN_0064c9a0` (mode picks the reader). |
| `0x596540` | `read_decode_block(dest, nbytes, count=1, file)` | H | 214 B. Signature read off the call site (`0x597bc3`): `push file; push 1; push 0xE5E0; push dest; call` — cdecl, so (dest, nbytes, count, file). Note the decompiler prints `param_2 * param_3` as `w*h`; that is **size × count, not width × height**. It allocates `nbytes` (rounded to even, `FUN_005be090`), reads that many bytes into a temp, then walks 2 bytes at a time writing to `dest`: b0 ^= counter_a (starts `0x80`, ++), b1 ^= counter_b (starts `0x80`, --), and **a zero byte is copied without XOR** (escape). Frees the temp, returns 1. `0x596470` is the sibling used when `DAT_00926a0c != 0`. |
| `0x596850` | `load_save_state(file, mode)` | M | 4,637 B. Reads 796 bytes into the **global** `DAT_00985ab8` (a header/flags block — it is tested all over the code as a bitmask: `& 0x400`, `& 0x800`, `& 0x8000`), then 4 bytes into `DAT_0091b5b4` (the verified "own player" global). Do **not** conflate with the map loader: `FUN_00597a70` reads the same 796-byte size into a *local* buffer that it never parses. |
| `0x64b9e0` | compiler helper (security cookie / `_ftol2` class) | H | 1,968 callers, 224 B, no strings. Topped the raw in-degree ranking; excluded from hub rankings by `scripts/coverage.py`. |
| `0x4d3770` | `unit_order_hold(unit_index, u16 mode)` — writes the order byte | **H** | Live hardware watchpoint on `unit+17` hit at `0x4d3888` (`mov %bl,0x933289(%ecx)`, `ecx = 3*52`, `ebx = 2`) when `h` was pressed on a selected unit; Ghidra body (`shard_012.c:3927`) matches instruction-for-instruction: guard `FUN_00528930(&idx,0,0xffffffff,0xffffffff,0)`, then `(&DAT_00933294)[i*0x1a] = param_2` (unit+28) and `(&DAT_00933289)[i*0x34] = 2` (unit+17), then `FUN_00584350(idx)`. Reached from the WNDPROC chain `0x5d0ee6 ← … ← 0x512644`. Callers pass 10 / 0 (`shard_013.c:4349/4417/7024`). |
| `0x5ab240` | `unit_remove_from_map(unit_index)` — unlink + sentinel | **H** | Watchpoint on a unit's x hit `Old 67 → New 65535` at `0x5ab2f8`, inside this function (`shard_015.c:22729`): unlinks via `+48`/`+50` (prev/next record indices), writes 0xffff to +0/+2/+48/+50, stashes old x→`DAT_00991798`, index→`DAT_009917a0`, old y→`DAT_009917a4`. Explains the "packed array" observation: in-place sentinel, then a compaction pass. |
| `0x584350` | `unit_broadcast(idx)` — event `0x2101` | M | 34-byte thunk `FUN_0052a720(0x11, idx, 0, 0, 0, 1, 0x2101)`; the instruction at the watchpoint hit *is* the `call 0x584350` right after the order byte is written, so every order announcement goes through it. |

| `0x5ab320` | `unit_set_position(unit_index, x, y)` — **the move-exec primitive** | **H** | 251 B, 24 callers, the only writer of a unit's tile reached by breakpoints: body writes `(&DAT_00933278)[i*0x1a]=x`, `+2=y`, `+50=0xffff`, `+48=FUN_005ab130(x,y)` (the destination tile's list head) and, when the tile is empty, `FUN_00582c80(x,y,unit+10)` on the tile record at `DAT_0092ae14+(DAT_00692184*y+x/2)*0x2c`. Live: 739 hits in `evidence/m19c_writesites2.log` at the store `0x5ab355`, 274 of them with real coordinates. |
| `0x5a58e0` | `unit_move_stack(unit_index, x, y)` — move every unit stacked on this one's tile | **H** | 109 B, 9 callers. Walks the +48/+50 chain from the list tail and calls `FUN_005ab320` per record with the passed (x,y). Live: return site `0x5a593f` appears as frame #1 above 274 real-coordinate writes, always under `FUN_00585720` (return `0x5893a8`). |
| `0x5a5a80` | `unit_restack(unit_index)` — clear the tile to scratch (-3,-3), then move the stack back | **H** | 378 B, 2 callers (`FUN_004bf1e0` at `0x4c0e0a`, `FUN_0055f650`). Body: reads `+0/+2`, walks the chain, parks records whose faction byte is `\b` / `< 2` via `FUN_005ab240(i,-3,-3)`+setter, then walks the destination list and moves it to the saved (x,y). Live: 24 hits fired the moment a unit was activated (`v`, and the activate dialog's OK) — `x=-3` then `x=41` on records 117/119/122/124. |
| `0x5a5cd0` | `unit_park(unit_index, mode)` — push a unit off the map to scratch | M | 1,518 B, 18 callers; called as `FUN_005a5cd0(iVar5,2)` / `(param_1,1)` from `FUN_00502cd0`'s can't-move branch. Live: return site `0x5a629a` above 274 writes of `x = -2`. |
| `0x502c40` | `unit_step(unit_index, dir, parity, …)` — one tile in one of 8 directions | **H** | 139 B. Reads x-delta from `(&DAT_006784a0)[dir]` (parity≠0) or `(&DAT_0067850c)[dir]` (parity=0) and y-delta from `0x6784c4`/`0x678990`, wraps x by `DAT_0092a378`, then calls `FUN_00502cd0(unit, ?, x+dx, y+dy, …)`. Tables read out of `.rdata` (see `turn_driver.md` §M19–M23) and cross-checked against a live cursor step of Δ(+2,0) at odd x. Called from dispatcher `FUN_0052bce0` **case 0x4402**. |
| `0x502cd0` | `unit_move_to(unit_index, ?, dest_x, dest_y, …)` — the move executor | **H** | 18,238 B, 4 callers. Its body calls the mover wrapper `FUN_004c1260(param_1, x0, y0, ?, flag)` then `FUN_005a58e0(param_1, x1, y1)` and marks both tiles dirty via `FUN_004737e0`. Callers: `FUN_00502c40` (step), `FUN_0055c920` (AI scoring — passes candidate destinations read straight out of the unit array), `FUN_0055f650`. |
| `0x4bf1e0` | `unit_commit_move(unit_index, from_x, from_y, to_x, to_y)` — mover + effects + message | M | 8,212 B, 4 callers, reached only through the 5-line wrapper `FUN_004c1260` (which then formats & sends a message: `FUN_00408180` ×2 + `FUN_005e4a32`). Live: return `0x4c0e0a` above the re-stack writes on activation. |
| `0x585720` | `unit_action_resolve(unit, param, mode)` — per-unit action executor (AI + end of turn) | M | 22,283 B, 6,347 insns, 108 callees, 6 callers, called as `FUN_00585720(unit, x, 3)` / `(unit, x, 1)`; it is the frame above 548 of the 739 live x-writes (via `0x5893a8` and `0x588e0b`). Also reached from dispatcher case `0x4401`. |
| `0x5abb40` | `unit_array_compact()` — slides records down with `rep movsd` | **H** | The 6 watchpoint hits in `evidence/m19_watch.log` all stopped at `0x64bfa3` (`rep movsl %ds:(%esi),%es:(%edi)`, `esi`/`edi` inside `0x9332xx`) with return `0x5abc4b` in this function — that is the compaction pass that made session 21 see "108/119 units moved". |

## Not yet named (candidates, ranked by `COVERAGE.md`)
- `0x5f6de9` — 305 callers, 550 B, 118 insns, no string literals
- `0x483470` — 292 callers, 556 B, 141 insns, no string literals
- `0x584010` — 249 callers, 108 B. **Known from M8**: the solo netcode "send" path that never fired in solo turns.
- `0x5a6330` — 224 callers, 1,596 B, 442 insns (big; likely a container/allocator helper)

## Method that worked
1. `scripts/coverage.py` ranks by in-degree *after* removing compiler helpers.
2. `scripts/fn.py <addr> --max 40` — read the shape: parameter types, which globals it
   touches, what it calls, whether string literals appear (`grep -oE '"[^"]{4,40}"'` on the body;
   none ⇒ pure logic ⇒ look at field offsets instead).
3. Follow one callee to see what the primitive is (here `0x5dd09c` ⇒ graphics state wrapper ⇒
   the caller is a drawing routine, not a data routine).
4. Write the row with the offsets that justify it, so a later session can falsify it fast.

| `0x582260` | `map_load_arrays(file)` | **gdb read trace**: reads 2,724 (→`0x92a378`), 140,800 (=W*H*22), 128 from one FILE* (callers `0x5822ac`, `0x5822f7`, `0x58231d`). Sibling `0x5821e0` used when `DAT_00926a0c != 0`. |
| `0x596850` | `save_load(file)` | 4,637 B. Reads 796 → `DAT_00985ab8` (year at +0x54, version 86), then sections at callers `0x596a96` (67,040), `0x596edb` (11,488), `0x597032`…`0x597786` (10 more). |
| `0x597a70` | `load_save_blocks(file, mode, is_map)` | **corrected**: save/scenario block path (796+4+67,040+58,848+11,488+32), *not* the `.MP` map loader. |

| `0x596850` | `save_load(file)` — **section table now known** | caller-scoped gdb trace: 26 ordered reads with destinations; 12-prefix, 796 header (`DAT_00985ab8`), player u32 @808, 67,040 / 11,488 / 32, 16,000, u32-count-prefixed section, 3,584 / 26,624 / 4,096, n×52 B, m×304 B, 256 / 152 / 10,144, 7×u32. |

| `0x95da10` | `base_array` (37 × 304 B, count in `DAT_00985af4`) | live read: base name at +19 (`University Base`, `Gaia's Landing`, `The Hive`, …), x at +0, y at +2, all inside 0..79 for an 80×80 map, **faction at +5 (byte)** and a flag byte at +4 (the u16 at +4 reads `flag | faction<<8`, so 0x0306 = faction 3, flag 6 — M31 corrected the earlier "faction at +4"), +6 = population, +7 = growth countdown, +60 = per-base turn counter, +64 = mineral accumulator mirrored at +152 (equal in all 62 bases), +48/+50 = flag words. Full map: `turn_driver.md` §M31. `DAT_00985af4` is a **base count**, not a faction count. |
| `0x933278` | `unit_array` (119 × 52 B) | live read: no ASCII anywhere, x at +0, y at +2, owner faction at +14, flags at +10; four records share (20,50) = `University Base`'s tile (garrison). |
| `0x8f79e0` | **`ui_singleton_base`** — what Ghidra prints as `in_ECX` | H — live `$ecx` = 0x8f79e0 at `0x4d3f70` and `0x512450`; exact cross-check `+0x23bd4 = 0x91b5b4` = the known own-player global. Converts every `in_ECX + 0x23xxx` in `ghidra_out/` into a flat address. |
| `0x91b5bc` | `selected_unit_index` (+0x23bdc) | H — written by `FUN_004d3f70`, read by every case of `FUN_00512450`/`FUN_00476580`; live read = 119 = one of our stacked survivors. |
| `0x91b5b8` | `orders_mode_flag` (+0x23bd8) | M — non-zero exactly while a unit is selected; gates the "destination" branch of `FUN_004d3f70` and of `FUN_00476580`; live = 1. |
| `0x91b5c4` | `order_menu_pending` (+0x23be4) | M — set on select, cleared by `FUN_00476580` after it dispatches an order code; live = 1. |
| `0x91b5f0` / `0x91b670` | `cursor_x_list` / `cursor_y_list` (u32 arrays, index at `0x91b5e8`) | M — read live (all entries (41,11), index 13); they are the arguments of `FUN_00511960`'s cursor-mode hotkeys and of `FUN_004d3f70(x,y,1)`. |
| `0x4d3f70` | `activate_at_tile(x, y, flag)` | H — `s_Console_ACTIVATE` string; live `ACT x=41 y=11 flag=0` for a click on our units' tile; raises the SELECT UNIT TO ACTIVATE modal via `FUN_0048f8b0` when the tile holds a stack; sets `0x91b5bc` and calls `FUN_0050cab0(1)`. |
| `0x476580` | `map_widget_click(pixel_x, pixel_y, flag)` | M/H — live `MAPH p1=0x1de p2=0xd4` == the click's pixel coords; dispatches order code `case 4→FUN_00529a40, 8→FUN_004d08b0, 10→FUN_004cffa0 (MOVE), 0xb→FUN_004d9380` on `0x91b5bc`; other branch writes `unit+17 = 0x18`, `unit+20/+28 = dest_x/dest_y` then `FUN_00584350` (Ghidra `&DAT_0093328c[i*0x1a]` = +20 and `&DAT_00933294[i*0x1a]` = **+28**, u16 arrays, 0x1a×2 = the 52 B stride; §M25 corrected an earlier `+24`). |
| `0x4cffa0` | `issue_move(unit, dest_x, dest_y)` | M — solo (`DAT_00920434 == 0`) → `FUN_004cdc70(unit,0,x,y)`; else `FUN_00528930(&unit,4,x,y,0)` + packet `0x2413` + `FUN_00528c10(1)`; `s_UNITMOVED` guard. |
| `0x4cdc70` | `exec_action_with_target(unit, mode, x, y)` | M — the solo path `issue_move` takes; sets `unit+4 \|= 0x40`, validates the target tile, `s_ARTYBOMBFAILED` branch. |
| `0x528930` | `submit_unit_action(&unit, mode, x, y, flag)` → `FUN_00527f70(mode, unit.x, unit.y, flag, x, y)` | M — returns 1 + `s_ALREADYDONE` when the unit is spent; mode 4 = move order. |
| `0x512450` | `hotkey_dispatch_unit(code, ?, ?)` | M — ASCII-keyed switch acting on `0x91b5bc`: `'h'`→`FUN_004d3770(sel,0)` (proven HOLD), `'H'`→`(...,10)`, `'F'`→4, `'E'`→0xd, `'B'`→0xe, `'g'`→`FUN_004d6fb0(sel,0x18)`, `'a'`→`FUN_004d3f70(sel.x,sel.y,1)`. |
| `0x511960` | `hotkey_dispatch_cursor(?, code)` | M — same codes, acts on the cursor tile from `0x91b5f0/0x91b670`: `Space`→base at cursor, `'a'`→`FUN_004d3f70(cursor,1)`, `'b'`→`FUN_004e3700(cursor, own)`. |
| `0x512b40` | `key_handler` | M — routes a key to the unit- or cursor-dispatcher and remaps `b c d f g h i` → `0x28 0x22 0x25 0x27 0x24 0x26 0x21` (8-value directional cluster = the cursor keys). |
| `0x920434` | `netgame_flag` (0 = single player) | H — read live = 0; it is the gate inside `FUN_00528930` (`if (DAT_00920434 == 0) return 0;`) and the branch selector in `FUN_004cffa0` (solo → `FUN_004cdc70`). Explains M6b/M7/M8's zero-netcode-hits result at source level. |
| `0x92ae14` / `0x692184` | `tile_record_array` pointer / map row-count (40 = width/2) | M — read live: pointer `0x40a6660` (Wine heap), record = `(40*y + x/2)*0x2c`, 44 B each; `FUN_004cdc70` validates a move target through it. |
| `0x934aa4` | unit record 119 (M24) / `0x934ba8` = record 124 (M25) | field map confirmed: `+17` order byte, `+18/+19` waypoint cursor, `+20` order-x, `+28` order-y, `+24` unused (−1 in every loaded record). |
| `0x4cdc70` | `bombard_resolve(unit, mode, x, y)` | M26 — strings `ARTYBOMBFAILED/BOMBFAILED/BOMBSUCCEEDED/BOMBARDSUCCEEDED/Arty_Failed_The_Hard_Way/ATEFOREST/ATESTUFF/HAVEDESTROYED`; `_rand()` 50%/25% coin rolls; 19-class facility-destroy loop over tile `+8` mask (`FUN_00582ed0`/`FUN_00582fc0`, attack `FUN_0056d350(unit,0,5,ax,ay,-1)`); head `FUN_005acdb0(unit)` + `unit+4 |= 0x40`; tail `FUN_00585720(unit,-1,3)`. **Retracts the M24 "solo move branch" label.** |
| `0x4cffa0` | `issue_attack_or_engage(unit, x, y)` | M26 — gate `FUN_005acc00` (0 → `s_UNITMOVED`); empty dest → `FUN_004cdc70(unit,0,x,y)` (solo) / `FUN_00528930`+packet `0x2413` (netplay); non-friendly occupied dest → `FUN_00596360` direction → `FUN_00502c40(unit,dir,1,1,0)` step toward. Writes no `+17`. |
| `0x5acc00` | `unit_can_act(unit)` | M26 — on-map ∧ owner==`0x91b5b4` ∧ `+10` bits 0x40&0x400 not both ∧ `+4 & 0x4200 == 0` ∧ order∈{0,1,2,3} rejected-or-passes ∧ `FUN_005ac650(unit,0)` − `+40` > 0 |
| `0x5acab0` | `unit_idle_and_own(unit)` | M26 — on-map, own, not busy, `FUN_005accd0 == 0`; used by `FUN_0040c8d0`/`FUN_004d3f70`/`FUN_0050cab0` |
| `0x5acdb0` | `consume_all_movement(unit)` | M26 — `+40 = FUN_005ac650(unit,0)`; called at bombard head + executor tail; live: `mpused 0→3` after injected executor call |
| `0x5ac650` | `unit_movement_total(unit, mode)` | M — getter used as movement total by `0x5acc00`/`0x5acdb0` (semantics inferred from use) |
| `0x529090` | `solo_order_dispatch(unit, dir, mode)` | M26 — head `if (DAT_00920434 == 0) return FUN_00585720(unit, dir, 3)`; netplay mode 0 queues via `FUN_00528930` (can print `s_MOVEPENDING`); callers `0x4d3770` (HOLD), `0x512b40` (key router), `0x4d1e90`, `0x4ce4a0`, `0x4ce710`, dispatcher — **solo orders run synchronously** |
| `0x4d6fb0` | `issue_order(unit, code, flag)` | M26/M28 — `+17 = param_2`; `0x18` branch `+20/+28` = **the target BASE's tile** (`(&DAT_0095da10/12)[base*0x98]`, base index supplied by the caller; no-ops when the unit already stands there) + `+4 &= ~0x10000` — so this issuer is "move to base", not "move to tile"; `0x80` branch `+4 = +4 & ~0x03000000 | 0x200`, `+38 = 10`, `+22/+30` = base coords; else `+20 = (short)target`; then broadcast `FUN_00584350()` + `FUN_00528d90()`; cursor tile read from `(&DAT_0091b5f0)[DAT_0091b5e8]`/`0x91b670` |
| `0x4cce50` | **named-order engine `0x4cce50(unit, k, execute)`** — `execute=0`: `+17 = k + 4` store + ETA (the M26 view); `execute=1`: the terraform execute branch (consume-all → `+37` accumulate → threshold → apply). M37 supersedes the 2-arg label | M26 store sites + **M37 live** — readers `0x4bdce0`/`0x4bf1e0` pass `order − 4`; `0x4d1200` passes `(order−4, 1)` |
| `0x50cab0` | `refresh_selection_state(flag)` | M26 — reads `DAT_0091b5bc` via `in_ECX+0x23bdc`; `FUN_005acab0` gate; arms move UI `FUN_005a3470(unit,0)` when solo ∧ `+40 == 0`; clears `in_ECX+0x23be4` (`0x91b5c4`) |
| `0x5010d0` | `tile_cursor_display(x, y, mode)` | M26 — 3.7 KB, static C++ vectors, direction-ish local table; modes seen `0/1/2/9/0x11/0x12/0x20/0x40/0x80`; touches NO setter/step/order/selection globals ⇒ display/cursor helper, not a mover |
| unit record fields | `+18` leg count, `+19` current leg, `+40` movement used, `+41` last dir, `+42` no-progress watchdog | M26 — executor waypoint advance `+19++` then `+20/+28 = arr[+19 + idx*0x1a]`; watchdog `+42 > 0x1f` → `s_KEEPMOVING` + order cancel; `+41` written from dispatch `param_2` ∈ 0..7 (`+4 |= 0x10000`) |
| `0x512b40` (arrow block) | **player MOVE via arrow keys** | **M27** — after the modal/Escape shortcuts, `case 0x21..0x28 → dir 0..7`; if `DAT_0091b5b8 != 0` ∧ selected ≥ 0 ∧ `FUN_004e1f90()==0` ∧ `FUN_005255e0()==0` then `FUN_005acc00(selected)` gate → `FUN_00529090(selected, dir, 0)`; gate fail → advisor `s_UNITMOVED_0068df64`. With `param_2 & 0x10000` (Shift) it instead queues `+17 = 0x19`, `+20 = dir`, `+22 = unit x`, `+30 = unit y`. Live: 1 `Right` moved rec117 (41,11)→(43,11); `evidence/m27_solowrap2.log` has 3 `SOLOWRAP idx=… dir=1 mode=0` → `SETTILE (45,11)/(45,11)/(43,11)` | 
| movement cost | `3 MP per tile, total 6 per unit per turn` | M27 — `+40` went `0→3` after one step and `3→6` after two (rec117/118); gate `FUN_005acc00` = `FUN_005ac650(unit,0) − +40 > 0` so a fresh unit gets **two** single-tile steps, then `UNITMOVED` |
| `0x4e1f90` / `0x5255e0` | arrow-move pre-gates | M27 — both must return 0 before the move is allowed in the arrow block; `0x5255e0` failure prints `s_SIMULNO_0068df5c`. Semantics not yet read |
| `0x476580` | `map_click_handler(pixel_x, pixel_y, button)` | **M28** — entry `MAPH`; `this = [0x7cdecc] = 0x8f79e0`; writes `+17 = 0x18` with the click-resolved tile (`esi`/`edi` low 16 bits) **only when `[this+0x1ef4c] == &DAT_0091cae4`** (pane mode 9); on the normal HUD that pointer is **0**, so a click falls to the base/`DESTTRIAD` branch and issues no order. Store sites `0x476ac7/0x476bae/0x476c39`; early-return gates `0x47674d/0x476778/0x4767ab` all skipped live (`evidence/m28_gates2.log`) |
| `0x50ba00` / `0x50ba90` | `set_map_pane_mode(idx[, arg])` | **M28** — `[this+0x1ef4c] = &DAT_0091c958 + idx*0x2c`; corpus callers pass only 8 (`0x4d8c20`), 0xb (`0x4d9120`), 10 (`0x4d9690`); **no caller with 9** ⇒ the destination-pick mode is entered from an unattributed (indirect) site |
| `0x512450` | `order_menu_command(command_id, key, …)` | **M28** — 0x42..0x73 command dispatcher on the selected unit; `0x67 → FUN_004d6fb0(sel, 0x18, 0)` (move to base), `0x6a` (`j`) in the key router → `FUN_004d6fb0(sel, 0x18, 1)`, `0x6f → FUN_004d44d0(sel, 9)` (terraform family, prints `NEEDTERRAFORMERS`/`TERRASEA`) |

## M32 additions (session 32) — the order setters, all live-named via `evidence/m32_keys2.log`

| addr | proposed name | conf | evidence |
|---|---|---|---|
| `0x512450` | `order_command(char, tolower(char), menu_code)` | **M32 H** | three live-verified stages: `param_1` switch (0x42–0x72), `param_2` switch (0x20 2e 2f 5b 5d 5f 64 6b 6d 73), `param_3` menu-code chain (0x20044–0x30055). 21 keys pressed, every `DISP p1/p2/p3` matched the static model exactly (`h`→(0x68,0x68,0x48), `M`→(0x4d,0x6d,0x1004d), `_`→(0x5f,0x5f,0x100bd), `G`→(0x47,0x67,0x10047)). Full map: `ORDERS.md` |
| `0x64d300` | `key_normalize(char)` — **tolower** | M32 M | live: uppercase chars arrive as `param_2 = tolower(char)` for `M S K E B G` (`DISP p2` = 0x6d 0x73 0x6b 0x65 0x62 0x67); punctuation passes through (`_` 0x5f, `.` 0x2e) |
| `0x4d44d0` | `issue_terraform_order(unit, mode)` | **M32 H** | 7 KB; gate `DAT_0098adb2[type*52] == 9` (Former) else `NEEDTERRAFORMERS`; mode = alpha.txt **#TERRAIN** index (validator strings per mode: HASROAD/HASFARM/NOBOREHOLE/NOAQUIFER/SEATOOLOW/TOOFLAT…); payment debits `DAT_0094d650[player*0x82f]`; store `+17 = mode + 4` + broadcast. Live modes 0,2,3,5,7,8,9,0xc,0xd,0xe,0xf,0x10,0x11,0x12 all fired with the predicted arg |
| `0x4d3770` | `set_hold(unit, sub_mode)` | **M32 H** | cancel → tile gate → `+28 = sub_mode`, `+17 = 2`, broadcast, `FUN_0041b710` (base-screen refresh), class-12 special (auto-run on own transport); live `h` on rec56: order 0→**2**, `+28` 0 |
| `0x4d9470` | `clear_order_and_explore(unit)` | **M32 H** | cancel; `+17 = 0`; `+4 \|= 0x4000`; broadcast → dispatcher walks the unit toward unexplored: live `EXEC idx=56 dir=7 mode=3` → `SETTILE (43,9)`; run 1: unit 57 explored onto an alien artifact (42,12) → Ops-Director modal. Explains M27's "`/` cancels" observation — it also walks |
| `0x4d3510` | `set_sentry_or_board(unit, mode)` | M32 M | cancel; air-load chain scan (`AIRLOAD` pane, class-7 carrier); else `FUN_005ab420` → `+17 = 1` (Sentry), `+20 = −1`, `+28 = 0`; clears `0x91b5c4` — matches `#ORDERS` 1 "Sentry/Board Transport L" |
| `0x5ab420` | `write_sentry_order(unit)` | M32 H | 42 B: `+17 = 1`, `+20 = −1`, `+28 = 0` — the Sentry order writer (called by `0x4d3510`) |
| `0x4d94d0` | `set_convoy(unit)` | M32 M | `+17 = 3` + `+38` = requisition flag (`s_SUPPLYEXTRACT`); dispatched from `'o'` when unit class (`DAT_0098adb2[type*52]`) == 10 (sea) — matches `#ORDERS` 3 "Convoy O" |
| `0x4d8b20` | `join_base_garrison(unit)` | M32 M | cancel; resolve base at unit tile (`FUN_004e34f0`); if base faction (`DAT_0095da14[base*0x130]`) == unit owner: `+46 = base idx`, broadcast, `FUN_0041b600` old+new (roster re-count); live `G` → `JOINBASE idx=56` (no base → cancel-only path) |
| `0x4d8920` | `set_route_to_base(unit, 0x1b\|0x1c)` | M32 M | gates: Former class, land domain, ocean tile check (`NOTINOCEAN`), `DAT_006939a8` check for 0x1c; then `FUN_004d6fb0(unit, code, 0)` → `+17 = 0x1b` (road-to) / `0x1c` (tube-to), `+20 = base index`; menu codes 0x20052 'R' / 0x20054 'T'; pickers `#ROADTO`/`#TUBETO` (Script.txt 1131/1135) |
| `0x4d6100` | `bombard_or_improvement_scan(unit)` | M32 M | 2.7 KB, 8 advisor gates, iterates the 19 improvement types against the tile `+8` mask (`DAT_006938f0[i*8]`), solo tail `FUN_004cdc70` (M26 bombard resolver), netplay `FUN_00583f40`; live `d` → entry on rec56 (gates returned, no side effect) |
| `0x4d8a30` | `toggle_unit_designation(unit)` | M32 M | cancel; `+4 ^= 0x80`; broadcast; `FUN_00626634(0, type record, …)`; `s_DESIGNATED`/`s_UNDESIGNATED`; menu code 0x20044 'D' |
| `0x4d8c20` | `clear_waypoints_and_enter_mode8(unit)` | M32 M | `+18 = 0`; if pane mode (`in_ECX+0x23d10`) == 8 → `FUN_0050bb20` (exit), else set widget flag 0x400000 + `FUN_0050ba90(8, −1)` — one of the three pane-mode setters M28 enumerated |
| `0x4d9690` | `enter_area_former_mode10(unit)` | M32 M | gates SIMULNO/UNITMOVED/SEAARTY then `FUN_0050ba90(10, DAT_0092a284)` — the mode-10 setter (destination-pick for area terraforms); reached from `'f'` when `FUN_005ac030(type,1) != 0` |
| `0x4d1e90` | `run_current_order(unit)` | M32 M | 68 B: can-act ∧ SIMUL ok → `FUN_00529090(unit, −1, 0)` (solo synchronous executor, dir −1 = "execute the order I have"); else clears `0x91b5c4`; dispatched from Space |
| `0x4d1f20` | `toggle_unload(unit)` | M32 M | `+17 == 1` → `+17 = 0` + broadcast (unboard); else transport-chain checks + `s_UNLOADNO/UNLOADNEXT` |
| `0x4d1280` | `found_base(unit)` | M32 M-H | strings NEEDCOLONISTS/BASETOONEAR/NEWBASE/BASEFOUNDED/`Sending_BUILD_BASE_message`/`Manually_building_base`; dispatched from `'b'` (land domain, non-engineer branch) — matches colonist "build base" |
| `0x4d6b90` | `obliterate_base(unit)` | M32 M | strings OBLITNOBASE/OBLITNOTYOURS/OBLITNOTOBJECTIVE/OBLIT; `'b'` sea-domain branch |
| `0x4d20f0` | `choose_unit_upgrade(unit)` | M32 M | 5.1 KB + `s_WHICHUPGRADE`; menu code 0x20055 'U' |
| `0x4d3950` | `give_unit_to_faction(unit)` | M32 M | strings CANGIVE/CANTGIVE/CANTGIVEAIR; menu code 0x30055 'U' |
| `0x4d8ca0` | `special_ability_action(unit)` | M32 low | gated by ability bit `DAT_0098ada8[type*13] & 0x10` + energy `FUN_005f1394` + tile checks; `'i'`; semantics unresolved |
| `0x94d650` | `faction_energy_pool` (stride `*0x82f` dwords) | M32 M | read+written inside `FUN_004d44d0` payment path (`Want_to_terraform`/`TERRACOST`/`TERRAPAY`, cost `FUN_004cc7b0()`, refund on failure); first live address for the energy ledger |
| `0x98adb2` / `0x98adac` / `0x98ada8` | unit-**type** tables (stride 52): class / domain byte / ability mask (`*0xd` shorts) | M32 M | class 9 = Former (`NEEDTERRAFORMERS` gate), 10 = sea (convoy dispatch), 12 = transport (HOLD auto-run), 7 = carrier (`AIRLOAD` scan); domain byte indexes `DAT_0092ae81[dom*0x90]` (0 land / 2 sea checks everywhere); ability bit 0x10 gates `FUN_004d8ca0` |
| `0x6938e8` / `0x6938f0` | terraform capability/mask tables (**runtime-loaded**) | M32 M | `[mode*8 + land]` capability index + `[i*8]` improvement bitmasks inside `FUN_004d44d0`/`FUN_004d6100`; **all zeros in the file image** ⇒ filled from alpha.txt `#TERRAIN` at load — confirms alpha.txt drives the terraform rules |

## M33 additions (session 33, 2026-10-21) — order issue/execute plumbing + selection

| addr | proposed name | conf | evidence |
|---|---|---|---|
| `0x4d5bbf` | (site) terraform **order store**: `mov %cl,0x933289(,%edx,4)`, cl = mode+4 | **M33 H** | objdump of `FUN_004d44d0` tail; live TERRAF idx=53 mode=0 → record `+17` 0→4 (`evidence/m33_try5.log` + unit reads) |
| `0x4d5bc6` | (site) broadcast call `FUN_00584350` (0x2101) after the store | M33 H | same tail; arg = unit idx (`$esp+4`) |
| `0x4d55a8` | (site) TERRAPAY pane show (`push 0x68c44c` → `FUN_005f0583`) — the picker **blocks inside the setter** until answered | M33 H | objdump + Script.txt `#TERRAPAY` ("Cancel action. / Expend $NUM0 credits."); payment flow `Want_to_terraform`→`FUN_004cc7b0` cost→TERRAPAY; Farm/Road/Sensor observed to **defer payment** (no pane, energy unchanged) |
| `0x4d561a` | (site) faction-energy **debit** `mov %edx,(%eax)`, eax = `0x94d650 + player*0x82f*4` | M33 H | objdump; refund variants `0x4d5908`/`0x4d59f3` add back |
| `0x4d5b25` | (site) tile-address math: `imul DAT_00692184`, ×11 dwords → `0x92ae14 + (40*y + x>>1)*0x2c` | **M33 H** | objdump; `DAT_00692184` = 40 read live; map dims `0x92a378/0x92a37c` = 80/80; height = `tile[0]>>5` matches HUD `Elev:` (h=7 ↔ 1036 m, h=4 ↔ 1096 m) |
| `0x40c8d0` | `select_unit(idx, …)` — the game's own selection routine | M33 M | gates: owner (`+14 == 0x91b5b4`), `FUN_005acab0(idx)` can-act, `+9` frozen; writes `0x91b5bc` + `FUN_00584350(idx)` + `FUN_0050cab0(1)` (scroll); callers `FUN_00499e70`/`FUN_0049af50` click handlers ("Reports left/right_click garrison") + netplay select-message (`FUN_0040c8b0` thunk) |
| `0x91b5bc` / `0x91b5c4` | selected-unit / order-menu-pending globals — **game-owned, poked values get re-validated** | **M33 H (negative)** | poke 55 reverts within ~1 pump iteration when the unit fails revalidation (already-moved, certain orders); keypresses advance the cycle; hardware watchpoints silent under Wine ptrace — cycle writes not pinned to a site (write-site bps on all 15 `mov ,0x91b5bc` sites: 0 hits in 12 s idle) |
| `0x98adb2` | unit-type class = **low byte** of dword `type*52` | **M33 H** | live: type 1 → `0xff002909` → class 9 Former (matches `#UNITS` field 5); faction variants (type ≥ 64) preserve the class byte (194 → class 2); reader `scripts/m33_scan.py` |
| `0x512b40` (menu echo path) | transient advisor/picker panes swallow the next input event, echoed as menu code `0x20011` | M33 M | repeated `KEY p1=0 p2=0x20011` after every rejected terraform (`That square already has a road…` pane); panes auto-dismiss in 1–2 s — faster than one OCR poll, so they look like "no modal" |

## M34 additions (session 34) — execution-trigger plumbing (static H unless noted)

| addr | name / meaning | confidence | evidence |
|---|---|---|---|
| `0x4d1e90` | `execute_stored_order(selected)` — Space handler: `if (FUN_005acc00(u) && FUN_005255e0()==0) FUN_00529090(u,-1,0)` else clears singleton `+0x23be4` | **H (static)** | shard_012.c:3206; callers: `FUN_00512450` `case 0x20` (Space, shard_013.c:4451) and `FUN_00516b80` menu id `0x323`; live `SPACEH` never observed (panes swallowed the key every attempt) |
| `0x512450` `case 0x20` | Space key → `execute_stored_order(DAT_0091b5bc)` | **H (static)** | shard_013.c:4451-4453 `switch(param_2)` on the key code |
| `0x585720` dir sentinel | `param_2 < 0 → 0x8` = "run the unit's stored order" branch of the executor | **H (static)** | shard_015.c head (`if ((int)param_2 < 0) param_2 = 0x8;`); M27 logged dir 1 steps, dir -1 never yet caught live |
| `0x52a720` (via `0x584350`) | `broadcast_unit(idx)` enqueues: `FUN_0052a720(q, idx, 0,0,0, 1, 0x2101)` — order-set broadcasts are QUEUED, drained by `FUN_005262e0` → `FUN_0052bce0` | **H (static)** | shard_014.c:28982+ (14 identical call sites, queue ids 0xb..0x13); bps `ENQ/DRAIN/DISP` armed in `scripts/m34_chain.gdb`, never reached live (runs died earlier) |
| `0x50cab0` | `selection_refresh()` pump: revalidates `0x91b5bc` via `FUN_005acab0`, re-picks via `FUN_0050c550` when it fails; arms move UI via `FUN_005a3470` | M (static) | shard_013.c head; live: cycle inert while selection passes the gate (try4/v7 waits) |
| `0x5acab0` / `0x5accd0` | `unit_idle(u)` = on-map ∧ own ∧ not-busy ∧ convoy-gate 0 — **no order-byte test**; same gate in `FUN_0040c8d0` select | **H (static)** | decompiled bodies; live corollary: ordered units stay selectable in principle, but cycle arrival on an ordered unit never observed |
| `0x4d44d0` eligibility remap | Farm on `tile+8 & 0x20` ∧ terrain ≥ 4 → **mode remap 0→0xa**; mode 0xa requires unit ability `0x2000` else picker branch `FUN_005a7520` → HASFARM advisor abort **before store** | **H (static + live signature)** | shard_012.c:108-113 + 182-184; live `evidence/m34_try2_gdb.log`: 5× `TERRAF idx=46 mode=0` no STORE, `0x20011` echoes — predicted rejection signature |
| `0x6938e8` index | terraform capability table indexed `[mode*8 + land]`; values −1/−2 = impossible | M (static) | shard_012.c:126 (`[pcVar6 + mode*8] < -1` → NOTATALL/NOTONLAND/NOTATSEA); runtime-loaded (alpha.txt `#TERRAIN`) |
| live: end-of-turn order cancel | pending terraform order (byte 4) clears at the turn boundary with **no debit, no tile change** | **H (live)** | `evidence/m34v6_run1_watch.json` turns: 2261 order 4 → 2262 order 0, energy 40→40, tile+8 unchanged; cancel write-site unpinned |
| live: pokes under tracer | `/proc/pid/mem` **writes** never reach the game while a tracer is attached (readbacks lie) | **H (live, reconfirmed)** | `evidence/m34_try3_gdb.log`: poked sel=46, `TERRAF idx=50` on the cycle's unit; also v7 waits |

## M35 additions (session 35) — the pay picker caught; tile base corrected

| addr | name / meaning | confidence | evidence |
|---|---|---|---|
| `0x92ae14` | **tile array base = pointer**, not the array: `mov esi,[ds:0x92ae14]` / `mov ecx,[0x92ae14]`, live `0x40a5cd0`; tile record = `*(0x92ae14) + (40*y + x>>1)*0x2c` | **H (asm + live)** | objdump 0x4d5260, 0x4d5650, 0x4d5b32; live: (45,7) `+0=0x80` elev 4, `+8=0x00108002`, (41,5) `+0=0x60` elev 3, all six of player 3's units read as land. **CORRECTS M33/M34**, which indexed off `0x92ae14` itself (the pointer slot region) — that is the whole "tile content unstable across snapshots" story |
| tile record layout | 40 records/row × 0x2c for an 80-wide map ⇒ **2 tiles per record** (`x>>1`); height = `+0 >> 5`, mask dword at `+8`; second tile's block appears at `+0x16` (unused by the setter head) | M | `DAT_00692184` = 40, `0x92a378/7c` = 80/80 read live; parity semantics **open** |
| `0x5a7520` | `terraform_tech_unlocked(mode, domain, player)`: req tech id = `*(int*)(0x6938e8 + (mode*8+domain)*4)` (−1 none, <−1 impossible); tested as bit `(player & 0x1f)` of byte `0x985c1c + tech_id`; plus the 0xb<mode<0x13 own-base bypass on `DAT_00985b44` | **H (asm)** | shard_015.c:20587-20617; objdump 0x5a7520-0x5a7559; runtime table decoded live and matches alpha.txt (mode 6→18, 7→17, 0xb-f→60, **0x10/0x11→59**) — `scripts/m35_gate.py` |
| `0x985c1c` | **faction tech bits**: byte per tech id, bit = `player & 0x1f` (LSB = player 0) | **H (asm + live)** | FUN_005a7520 bit test; live: player 3 has techs {0,1,2,3,4,5,6,32,48}; byte 59 = `0x10` before, `0x18` after the M35 poke |
| `0x4d5474`-`0x4d5493` (case 0x10/0x11) | **the only route to the payment path**: xrefs to `LAB_004d5496` = 0x4d5277, 0x4d5313, 0x4d53d8, 0x4d53f4, 0x4d53f9, all inside the Raise/Lower case ⇒ TERRACOST/TERRAPAY exist **only** for raise/lower | **H (objdump xrefs)** | every `jmp/jcc 0x4d5496` in `FUN_004d44d0`; raise: level≥3 ∧ <6 pays, level 3 pays, level 2/6/7 advisor; lower: level≥4 pays, 3 = TOOLOW, 0 = SEATOOLOW |
| `0x4d54c3` | `call FUN_005a6330(unit, 9, mode+4, -1, -1)` = "unit (or its cargo chain) already carries this order byte" → nonzero **skips the whole payment path** | H | objdump 0x4d54b2-0x4d54cd; FUN_005a6330 case 9 compares `+17` to param_3 walking the `+50` chain |
| `0x4d54df` → `0x4cc7b0` | payment **cost** is dynamic, not the alpha `#TERRAIN` figure | **H (live)** | raise at (45,7) elev 4 logged `COST cost=9`; alpha says 12 (`evidence/m35v2_gdb.log`) |
| `0x4d558f` | affordability gate: `cmp [0x94d650+player*0x82f], cost; jl 0x4d55cb` — **broke ⇒ the picker is not shown at all**, straight to the answer reader | **H (asm)** | objdump 0x4d557d-0x4d55cb |
| `0x4d55b3` | `call FUN_005f0583` **TERRAPAY picker** (pane id string `0x68c44c`) — blocks inside the setter; `0x4d5572` is the TERRACOST caption pane. Pane ids print via the `PANE` bp (arg at `$esp+8` = id string) | **H (live)** | `PANE #1 id=TERRACOSTUP` … `PANE #2 id=TERRAPAY`, then `PAYTAKEN`; `evidence/m35v2_paypicker.json` |
| `0x4d5634` | **common post-payment continuation** (footprint pass), reached both after paying and when payment is skipped — the M35 bp label `SKIPPAY` here is misleading | **H (objdump + live)** | `jne 0x4d5634` / `je 0x4d5634` at 0x4d54cd/0x4d54ec; live it fires *after* `DEBIT` |
| `0x4d5822` / `0x4d5839` / `0x4d58a4` | footprint-pass per-tile appliers/validators `0x528930` / `0x555030` / `0x4c2be0`; failure branches at 0x4d58dc / 0x4d59c7 / 0x4d5b0d show panes and return via 0x4d5add | M | objdump 0x4d5763-0x4d5b20; `FUN_00528930` is **netplay-only** (`if DAT_00920434==0 return 0`; solo switch live = 0) so it is not the refuser |
| `0x5ab320` | `FUN_005ab320(unit, x, y)` = **unit reposition** (writes unit `+0/+2`, `+18=0`, sets `DAT_009917a0=0xffffffff`, calls 0x582ed0/0x582c80) | **H** | shard_015.c:22775-22805. **RETRACTS the "sole tile writer" label** in the standing facts |
| live: picker answered | answering "Expend 9 credits." ⇒ `PAYTAKEN` → `DEBIT 40→31` (synchronous) → `ENQ q=11 idx=3 type=0x2101` (energy broadcast **queued**) → `PANE id=TERRAFORM`; then **no STORE/BCAST**, order byte 0, tile unchanged, **no refund** | **H (live)** | `evidence/m35v2_gdb.log` / `m35v2_paypicker.json`; post energy 31 |
| live: cancelled picker | `PAYDECLINED` = the picker was answered "Cancel" (or Escaped); no debit, no store | **H (live)** | `evidence/m35v1_paypicker.json` (Escape aimed at the transient TERRACOST pane cancelled TERRAPAY) |
| live: cycle rules | HOLD (order 2) units are **not** cycle candidates; an empty cycle makes the game **auto-end the turn**; a map click selects a unit **and** sets orders-mode `0x91b5b8=1`; `Tab` re-opens the CUSTOMIZE YOUR FACTION modal mid-game | **H (live)** | year ran 2266→2270 unattended; sel 0→201/45/42 by click; `m35_state.png` |

## M36 additions (session 36, 2026-10-21) — store tail, footprint rules, tutor pane

| addr | name / behavior | confidence | evidence |
|---|---|---|---|
| `0x48ef40` | `show_tutor_pane(script_ptr, pane_id, -1, 0, 0)` — **blocking**: `0x57b570` suspend → `0x62680e` pane runner → `0x57b0f0` resume; the `'TERRAFORM'` tutor (tutor.txt:1102) opened at `0x4d58c6` **parks the setter above STORE until clicked away** (OK at (400,408)) | **H (live)** | pane open 2 sessions straight with order 0 + latch consumed; `PANERET` fires on OK click — `evidence/m36v1_gdb.log` |
| `0x4c2be0(bit)` | **once-per-game solo latch**: `DAT_00985ab8 & 0x20` gate; sets bit in `DAT_00985ad4`, returns 1 first time only; netplay always 0. At `0x4d58a4` with `0x800` = "show the TERRAFORM tutor once" | **H (asm + live)** | shard_011.c decompile; live bit 0x800 consumed 0→1, tutor pane exactly once |
| `0x4d5b71`/`0x91f718` | **issue lock**: `DAT_0091f718 != 0` logs `"I think I've already got my lock"` (0x68c4bc) and skips the lock call; else `0x528930(unit,0,-1,-1,0)` — in solo returns 0 (`DAT_00920434==0`) ⇒ **store gate is pass-through in solo**; netplay nonzero jumps past STORE to 0x4d5c1c | **H (asm + live)** | objdump 0x4d5b71-0x4d5bae; live `LOCKCHK lock=0 → LOCKRET eax=0 → STORE` |
| `0x4d5bbf` / `0x4d5bc6` | **STORE order byte** `[unit*52+0x933289] = mode+4` + **BCAST** `call 0x584350` → enqueue 0x2101 idx=unit — **fired live**: order +17 = 0x14, `ENQ q=17 idx=41` | **H (live)** | `evidence/m36v1_gdb.log`; unit record +17 = 20 read through /proc/pid/mem after detach |
| `0x4d5b16`–`0x4d5b6f` | terrain/facility store gate **skipped for modes 0xa, 0x10, 0x11**; others: `(record byte0 & ~0x1f) >= 0x40` ∧ `tile_mask(+8) & *(0x6938f4+[ebp-0x18]*4)` then scan table `0x6938f0..0x693b70` → `0x4d5e85` | H | objdump 0x4d5b16-0x4d5b6f |
| footprint ladder `0x678e08` | raise footprint count = `[-13,-14,-15,1,9,25,49,81][height+1]` (clamp 6) ⇒ elev 4 ⇒ 25 tiles; lower = `[9..289]` with the `3−(height−1)` fold at 0x4d571d-0x4d5759; offsets `0x67850c`(x)/`0x678990`(y), **x wraps**, off-map = skip | **H (file bytes + objdump)** | .rdata read; objdump 0x4d5634-0x4d5899 |
| `0x4e3b50(own, x, y, 0, 0)` | **tile border-owner query** → player id or −1; own/none skip; foreign + relation `&7` ≠ 0 → diplomacy path | **H (asm)** | objdump 0x4d57c6-0x4d5811 |
| `0x555030(a, b, mask)` | **diplomatic-breach confirm**: reads `[0x94d448 + (a*0x82f+b)*4]`; pact bit ⇒ `BREAKINGPACT` pane, **instant refuse (no dialog)**; treaty/truce ⇒ yes/no confirm, decline = refuse; else `BEGINVENDETTA` confirm. Returns true = the terraform is refused (→ refund block) | **H (asm + strings)** | shard_014.c: s_BREAKINGPACT 0x6911e8 / BREAKINGTREATY 0x691208 / BREAKINGTRUCE 0x691228 / BEGINVENDETTA 0x691248 |
| `0x4d58dc` / `0x4d59c7` | footprint-failure **refund blocks**: `energy = [0x94d650+own*0x82f*4] + [ebp-0x14]`, energy broadcast `0x5843b0`, return via 0x4d5add | H | objdump 0x4d58dc-0x4d5a0d |
| `0x5076d0(own, owner, -1)` | solo "break diplomacy now" executor called per accepted foreign footprint tile | M | objdump 0x4d587b-0x4d588a (solo branch of the netplay 0x2440 packet path) |
| `0x582ed0(x, y, mask, setclr)` | **tile mask set/clear**: `record(+8) |= / &= mask` (pointer base `*(0x92ae14)`, `x>>1`) — confirms M35 tile base | **H** | shard_014.c decompile |
| `0x585720(u, dir, mode)` | **executor, arg shape proven live**: arg1 = plain unit index, arg2 = direction (−1→0x8 = run stored order), arg3 = 3 during turn execution; fires for every executing unit of every faction (183 hits in one round) — **never for unit 41 with order 0x14** | **H (live probe)** | `evidence/m36_execprobe_gdb.log` (unconditional bp, round 2272→2273) |
| `0x5262e0` drain / `0x52bce0` disp | **never fire in solo** across 3 rounds incl. a full executor round — the enqueued 0x2101 events (energy idx=player, unit idx=41) have no solo consumer | **H (live, positive control = 183 executor hits)** | `m36b_gdb.log`, `m36_execprobe_gdb.log` |
| ENDOFTURN1 pane | `Script.txt:8037` "Mission Year $NUM0: No units need new orders. Press ENTER for next turn." — auto-end prompt; **Return** advances; NOT a Yes/No confirm (`is_confirm` must not fire) | **H (live)** | `m36b_gdb.log` PANE id; Return → round ran |
| REALLYQUIT pane | `Script.txt:426` "Do you really want to quit?" — opened by **Escape on a bare HUD**; rows "Oops, no, wait!" y≈260 / "Yes, that's an order mister!" y≈281; OK bar ≈307; NO+OK recovers | **H (live)** | opened by the svc loop's Escape; `evidence/m36_after_no.png` |

## M37 block (session 37, 2026-10-21) — terraform EXECUTION chain + multi-turn accumulator

| addr / token | what it is | confidence | how known |
|---|---|---|---|
| `0x51f730(player)` | **turn-start refresh**: per unit of that player `watchdog+42=0`, **`mpused+40=0`**, `flags4 &= ~0x200202`, byte+5 &= 0xef, Sentry/Hold `+28` countdown −− (order cleared at 0); then decrements `byte+16` (reserve pool) by `field45(type)*local_8`, floor `field45*2` unless on-base/player0 (0 on own base, `0x4e34f0(x,y)` ≥ 0) | **H (live)** | `REFRESH player=N` fired per player per round in every m37 log; body shard_013.c:10992-11655 |
| `0x5208f0` / callers `0x520c10` `0x521070` | per-player turn-start sequence (`0x5a1830 → 0x51f730 → 0x520540 → upkeep 0x51fe90/0x5551e0/0x556690/0x5a1ad0`), driven by the round sequencers which also step the solo engine `0x51e700` — **runs in solo**, contrary to an M37-early guess | **H (live)** | REFRESH events; shard_013.c:11647-11995 |
| `0x529e70(unit, flag)` | **attempt-unit-action**: solo (`DAT_00920434==0`) → `return 0x4d1200(unit)`; netplay → ACTION packet `0x2404` + `0x528a60` lock; order 0x14/0x15 ⇒ arg `0xc` | **H (asm + live)** | shard_013.c:17278; called by pump `0x50ef60` (shard_013.c:2777) |
| `0x4d1200(unit)` | **solo order dispatcher**: 4..0x17 → `0x4cce50(unit, order−4, 1)`; 0x18/0x19/0x1a → `0x4ce4a0`; 0x1b/0x1c → `0x4ce710`; post-run `order & 0x40 ⇒ order=0` | **H (asm + live)** | 116 B body; `ORDEREXEC unit=41 order=0x14` live |
| `0x4cce50(unit, k, execute)` | **named-order engine** — supersedes the M26 `set_named_order` row (that was the `execute=0` branch: store `+17=k+4` + ETA return). Execute branch: consume-all → accumulate → threshold → apply (see branch rows below) | **H (live)** | shard_012.c:740-935; m37 logs |
| `0x4cd2c8` | TERRAFEXEC entry (execute branch): `$ebp-0x8` = unit*52 byte offset, `$ebp+0xc` = k | **H (live)** | bp fired for 5 factions |
| `0x4cd319` | swamp-cancel: tile became passable land ⇒ `order=0`, return 0 | H | decompile + bp |
| `0x4cd32e` | CHECK: `edx = accum+work` vs threshold at `$ebp-0x2c` (= `2*iVar16`) | **H (live)** | prints match memory reads |
| `0x4cd33b` | NOTYET: order stays; tile dirty `0x4737e0(x,y,2)` + panel refresh `0x41b710` | **H (live)** | |
| `0x4cd35e` | COMPLETE: `+37=0`, chain same-k orders cleared, mask swap, apply | **H (live)** | `COMPLETE unit=2028 x=45 y=7 mode=16` |
| unit `+37` (`DAT_0093329d`) | **terraform work accumulator** (byte): `+= Σ chain work` per our turn; panel shows it for domain>1 units; zeroed on completion | **H (live)** | m37a/b/c2: 8→10→…→24 then 0 |
| terrain runtime table `0x6938f0 + k*32` | entry layout: `+0` = mask bits SET on completion, `+4` = mask bits CLEARED, **`+8` = base work** (== alpha `#TERRAIN` field 5: raise/lower 12, mine 8, sensor 4, mag 3, road 1 — filled from alpha.txt at load, zeros in the file), `+18` = required tech id (59 = EnvEcon for k=16/17). **Completion threshold = 2×`+8`** (mode adjustments aside) | **H (live mem + file + log cross-check)** | live table read; `data/alpha.json` #TERRAIN; thresholds in m37 logs; road COMPLETE ⇒ `MASKSET mask=0x4` = `table[5].+0` |
| work per turn | 2 per chained unit (4 if ability mask `0x98ada8[type*52] & 1`); ×2 for k∈{10,0xb} when faction owns base `0x985b5c`; ×3/2 when owns `0x985b44`; chain = `prev@+50`→head→`next@+48`, same-k only, members' `+37` fold into head | **H (formula read; +2/turn live)** | shard_012.c:790-845; observed +2/turn for Former type 1 |
| `0x5acdb0(unit)` | **consume-all MP**: `mpused := 0x5ac650(unit,0)` — fires at every terraform-exec turn; explains M36's "mpused 3 persists" (re-charged each turn after REFRESH) | **H (asm + live)** | 34 B body; mpused=3 every our-turn snapshot |
| `0x5ad400(x,y)` / `0x5ad460(x,y)` | **RAISE / LOWER tile setters** (k=0x10 / k=0x11 completion apply) → `0x5ad0a0(x,y,new,flag)` elevation writer | **H (live)** | `RAISE x=45 y=7 → SETELEV x=45 y=7 new=5` |
| `0x5b09b0()` | post-change map recalc (re-erosion/leveling): SETELEV storm on neighbours after RAISE | M | fired between RAISE and redraw |
| `0x51f320` | per-unit **aquatic passive work**: domain==2 units with mp left, on deep water, not near land: `+37 += 1` (sea-floor mining accrual?) | M | shard_013.c:10875 |
| `0x4dde00` | unit info panel — **writes spinner values back** to `+15`, `+16`, `+40`, `+37` on its confirm path (`0x64c460` reads); prints `+16`/`+40` numerics | M | shard_012.c:10320-10390 |
| `0x5acc00(unit)` | can-act gate, full shape: in-map ∧ own ∧ ¬(`+8` bits 0x40&0x400 together) ∧ ¬`0x5accd0` ∧ ¬(`flags4&0x4200==0 ∧ order∈{1,2,3}`) ∧ **`0x5ac650(unit,0) > mpused`** (or remaining > 999) | **H (asm)** | full body read; `0x5accd0` = Sentry-with-target-on-water-ish special case only |

## M38 block (session 38, 2026-10-21) — issue-cost formula + footprint/diplomacy + economy

| addr / token | what it is | confidence | how known |
|---|---|---|---|
| `0x4cc7b0(x, y, player)` | **terraform issue cost**: `term = (\|elev−3\|+2)²`; ×3 fungal (`mask&0x20` ∧ elev>3); if nearest own base found: `× clamp((\|dx\|+\|dy\|)/2, 1, 100) × 2` + foreign-owner distance/reputation scaling; `/2` if faction trait bit `0x2000`; **always `/2`**; clamp 1..30000. For player 3 the base-distance branch is inert (see faction-byte row) ⇒ observed `cost = term`: **9 @ elev 4, 16 @ elev 5** | **H (asm + 2 live points)** | shard_012 body read; `COST idx=39 cost=16` live; call site 0x4d54d3 pushes (x, y, own-player from `[esi+0x23bd4]`) |
| `0x4e3700(x, y, player)` | nearest-base scan: walks the `DAT_00985af4` bases from `0x95da10` (stride 0x130 = 304; short-indexed `(&DAT_0095da10/12)[idx*0x98]` = x/y), **matches byte base+4 == player**, wrapped Manhattan distance | **H (asm + live dump)** | body read; 69 live bases have faction bytes {1,2,4,5,6,7} — never 3 ⇒ returns −1 for us |
| base `+4` faction byte | stores a **FACTION ID, not the player index** — the player↔faction-ID mapping is unresolved; consequence: cost distance factor + any `0x4e3700(x,y,player)` branch is inert for players whose ID ≠ index | **H (observation)** / mapping open | live dump of all 69 bases; `byte+4 dist: {1:10, 2:23, 4:7, 5:5, 6:15, 7:9}`, me=3 |
| `0x64b870(v)` | `abs(v)`; map-wrap correction lives in callers (`DAT_0092a394&1` = wrap flag, `DAT_00692184` = 40 half-width, `DAT_0092a378` = 80 width) | H | body + callers 467× |
| `0x5a6330(unit, 9, mode+4, −1, −1)` | ORDERCHK gate inside the pay path: `eax ≠ 0` ("already has this order") → jump to `0x4d5634` skipping payment | H (live bp) / semantics M | `ORDERCHK idx=39 already_this_order=0` then picker opened |
| `0x927a98 + player*0x59c` | faction record word; **bit `0x2000` = terraform-cost halving trait** (ours: clear) | M (branch read) | live read 0x00000000 for player 3 |
| raise ladder rung 6 | `0x678e08[5+1] = 49` ⇒ **elev-5 footprint = 7×7** (x 42..48, y 3..11); 81 = idx 7 = the elev-6 step (9×9). NEXT_PROMPT's "81 @ elev 5" corrected | **H (live pass)** | issue ran with zero `PACTCHK/DIPLO/REFUND` hits — all 49 tiles own-or-unclaimed |
| footprint diplomacy sites | `0x4d5839` = foreign-tile → `call 0x555030(own, owner, 7)`; `0x4d58dc`/`0x4d59c7` = refund blocks; `0x4d5add` EPILOGUE = early return without STORE — all armed live, **all silent** (clean footprint) | H (armed) / branch still untested live | `m38a_issue_gdb.log` |
| pump immediate execution | after `STORE`, the pump runs the new order **in the same turn** (consume-all + work +2); issue turn == execution turn #1 | **H (live)** | work37 0→2→4 within the issue window (2282/2283) |
| `0x5b09b0` re-erosion direction | after RAISE at (45,7)→6, the 8 neighbours were **lifted 4→5** — leveling erodes toward the new plateau | **H (live)** | `SETELEV (45,5)/(44,6)/(46,6)/(43,7)/(47,7)/(44,8)… new=5` storm in `m38run2_gdb.log` |
| energy economy | flat between debits: 31@2270 → 31@2282 → (−16) → 15@2293 ⇒ income ≈ upkeep ≈ **+0/turn** | H (observed) / cause M | mem snapshots across sessions 35–38 |
| selection recipe (harness) | poke `+40=255` into every other own order-0 unit → `Escape` deselects → pump auto-selects the only actionable unit | **H (live)** | worked first try in `m38a`; `sel` landed on Former 39 |

## M39 block (session 39, 2026-10-21) — road = no-cost issue; live threshold ladder; key model corrected

| addr / token | what it is | confidence | how known |
|---|---|---|---|
| `r` → `0x4d44d0(unit,5)` | Road issue: **skips the entire cost block** — PAYPATH `0x4d5496`, ORDERCHK `0x4d54c8`, cost `0x4cc7b0`, TERRACOST/TERRAPAY, SKIPPAY `0x4d5634` all silent; straight `TECHCHK → AFTERLATCH → STORE 0x09 → BCAST`. No picker, no DEBIT | **H (live)** | `m39a_gdb.log` TERRAF→TECHCHK→AFTERLATCH→STORE with zero cost-block hits |
| `0x4d5634` (SKIPPAY) | exit from the pay path when ORDERCHK says "already has this order" — **not** the no-pay-mode path (no-pay modes jump over the block entirely) | H (live negative) | road never hit it |
| road threshold by elevation | `CHECK threshold=4` at elev-6 (45,7)/(39,49) vs `=2` at (46,42): case-5 adjustment raises base 1→2 by elev-class (int), then ×2 | **H (live, 3 pts)** | m39a log (ours + AI) |
| solar threshold by elevation | 8 at (46,50)/(58,52), **16** at (40,46) — case 3 `×elev-class/2` | **H (live)** | m39a AI units |
| mine threshold 8 / RemoveFungus threshold 12 | modes 4/10 on AI tiles (54,36),(43,57) / (58,50),(44,46) | H (live) | m39a log |
| AI terraform work `+3`/execution | 9+ AI units across modes 3/4/5/10 (ours `+2`); not ability bit0 (that ⇒ 4); cause open | H (observed) / cause M | m39a CHECK pairs |
| `Tab` | cycle / select-next key (sel −1→36, orders mode →1); empty cycle ⇒ ENDOFTURN1 pane | **H (live)** | manual probe + m39a run |
| `l` | **SENTRY order key** in orders mode with a unit selected (issued order 1; auto-ended the turn) — supersedes the "L cycles" note | **H (live, oops-proof)** | Former's order byte became 1 after `l` |
| `0x91b5c4` order-menu-pending | sticks at 1 across turns/selections; poke 0 before order keys | H (observed) | m39a events + manual test |
| cycle MP filter | units with `mpused ≥ max` are skipped by the cycle — poke `+40=0` first | **H (live)** | sel stayed −1 until poked |
| Sentry clear by poke | `+17: 1→0` works; unit then accepts a key-issued order | H (live) | m39a after manual poke |
| mode-5 completion apply | mask swap only: mem 0x108002→**0x108006** (road bit 0x4), no SETELEV/RAISE, elev untouched | **H (live)** | m39a post + log |

## M40 block (session 40, 2026-10-22) — MagTube remap live, TECHFAIL advisory dispatch, advisor substitution plumbing

| addr / token | what it is | confidence | how known |
|---|---|---|---|
| `0x4d44d0` mode rewrites (body lines ~104–118) | **before validation**: `5→6` when `tile.mask&4` ∧ `cap[6+tile-seafloor-flag] > -2`; `0→0xa` when `mask&0x20` ∧ elev ≥ 4; `0→1` when `mask&0x8000` ∧ `cap[1+flag] > -2`. The rewrite **writes back to the stack arg slot** (TECHCHK bp at `0x4d4837` reads `$ebp+0xc` and printed 0x6 after TERRAF entered with 0x5) | **H (live + body)** | `m40a_gdb.log` TECHCHK mode=0x6; shard_012.c |
| capability table `0x6938e8`, int index `mode*8 + flag` (`flag` = tile elev<3) | the **real tech-gate + advisory source**: value ≥ 0 = required tech id (MagTube land = **18**, live), −1/−2 = operation undefined for that tile class (drives NOTATALL/NOTONLAND/NOTATSEA). Terrain-table `+18` is garbage (527) for k∈{1,5,6} — correction to the standing "+18 = required tech" note (only k=16/17 carry 59) | **H (live reads)** | `0x6939a8` = (18, −2) live; terrain table k=1/5/6 `+18`=527; m35_gate |
| TECHFAIL advisory dispatch (branch entry `0x4d486e`) | gate `0x5a7520` returned 0 ⇒ advisory is **mode-specific**: 6 → `HASROAD` (str 0x68c300), 1 → `HASFARM` (0x68c308), else → `NOTUNTILTECH` (0x68c310) → `0x483470`. Bypass: `mode==0xa ∧ ability&0x2000` skips the fail branch | **H (live + body)** | `m40a` ADVISOR id=HASROAD right after TECHFAIL; Script.txt `#HASROAD` text matches the remap UX exactly |
| pre-gate silent exits | mode 6 without road bit / mode 1 without bit 0x8000 → clean return to `LAB_004d5ae8`, **no advisory** (MagTube key on a roadless tile does nothing) | H (body) | shard_012.c gotos at 0x4d4812/0x4d47b3 |
| `0x5a69f0(buf, tech_id, flag)` | **format tech name into buffer** from the tech record `0x92fdb4 + id*44` (name at +0; 18 short name "Magnets"); `flag≠0` appends cost/level ints (`+0x10`/`+0x14` of the record); id<0 / id==9999 use fallback strings from `DAT_00997b20` | H (body + live names) | shard_015; live record reads 17/18/59; composed pane |
| `0x626634(slot, text, v3, v4)` | **set advisor substitution slot**: text buffer `DAT_0099a01c + slot*0x100`, slot values `0x999ff4[slot]`/`0x999fcc[slot]` (v<0 ⇒ defaults `0x99aa1c`/`0x99aa20`); slot 0 = `$TECH0`; 1580 callers = the generic advisor-text substitution setter | **H (live)** | post-run: slot-0 buffer = "Monopole Magnets" after the HASROAD advisory |
| `0x997120` | advisor **scratch** buffer: TECHFAIL branch zeroes it, `0x5a69f0` writes the tech name, the pane printer reuses it — post-run holds the **composed pane text with $TECH0 substituted** | **H (live)** | readback: "…converted to Magtubes until we discover Monopole Magnets." |
| `0x92fdb4 + id*44` | **tech records** (runtime-filled): name at +0, cost/level ints at +0x10/+0x14; 18 = "Magnets" / full "Monopole Magnets", 17 = "MilAlg", 59 = "EnvEcon" | H (body + live) | live record reads |
| terrain table k=6 (MagTube) | maskSET **0x8**, maskCLEAR 0, work **3** (alpha #TERRAIN mag 3 ✓); k=1 SoilEnricher 0x80000 / clear 0x200000 / 8 | **H (live read)** | runtime table dump 2026-10-22 |
| NOTBASE / ALREADYBUILT checks | `mask&1 ∧ tile+2&0xf < 8` → NOTBASE; terrain `+0` maskSET ⊆ tile mask → ALREADYBUILT (`$MINE0` name from `0x6938e0[mode*8+flag]`) — static only so far; road-on-road never reaches ALREADYBUILT (remap + gate intercept) | M (body) | shard_012.c |
| `m39_issue.py` on a reject path | TECHFAIL ends in the 75 s STORE timeout → cleanup, game left clean, zero side effects — **expected terminal state** for rejected orders | **H (live)** | `m40a_issue.json` post: order 0, energy 15, tile 0x108006 |

## M41 block (session 41, 2026-10-22) — MagTube live end-to-end; threshold adjustment refined

| addr / token | what it is | confidence | how known |
|---|---|---|---|
| tech bit `0x985c1c+18` bit 3 | Monopole Magnets for player 3: poke `0x00→0x08` (TracerPid 0, verify, arm gdb after) flips the remapped-mode gate `TECHCHK mode=0x6 unlocked=0→1`; persists across turns and runner invocations | **H (live)** | `m41a_issue.json` pre/post; `m35_gate.py` unlocked=True |
| TECHCHK pass-through path | gate 1 ⇒ **no advisory, straight to AFTERLATCH → LOCKCHK → STORE** — the advisory machinery lives only in the fail branch | **H (live)** | `m41a_gdb.log`: TECHCHK unlocked=1 → AFTERLATCH mode=0x6 → STORE 0x0a, ADVISOR silent |
| STORE writes the **rewritten** mode | `+17 = 0x0a` (mode 6 + 4), not the keyed 0x09 — the setter's arg-slot rewrite feeds the store tail; first completion of a rewritten mode proven | **H (live)** | `m41a` STORE order=0xa; `m41b` ORDEREXEC unit=36 order=0xa ×4 |
| MagTube threshold @ elev 6 = **8** | 2×3 + 2 ⇒ case-5/6 elev bump is **+2 flat**, not ×2 (road 2→4 @ elev 6 fits the same +2; M40's "may double" retracted) | **H (live, 2 runs × 4 CHECKs agree)** | `m41a`/`m41b` CHECK lines threshold=8 |
| magtube tile bit `0x8` | completion mask swap: (45,7) `0x108006 → 0x10800e`, elev 6 untouched — mode 6 = mask swap only (table k=6 SET 0x8 / CLEAR 0 ✓) | **H (live mem)** | post-snapshots both runners + live re-read; MASKSET print capped (299/300 hits) |
| consume-all pool ≠ work | `mpused := 3` (full Former pool) after an exec that credits only +2 work | **H (live, reconfirmed)** | post order/`+37`/`+40` reads |
| AI terraform thresholds (obs) | base 2×`+8` holds: sensor 8, bunker 10, condenser 24, raise 24, RemoveFungus 12, solar 8/12, road 6@(54,52) — bumps >+2 at unmeasured elevations | O (live side-effects) | `m41a_gdb.log`/`m41b_gdb.log` AI CHECK lines |
| AI accum +3 (mostly) | 7 AI formers +3/exec; **idx 51 (RemoveFungus) +2** — not universal; faction-trait hypothesis open | O (live) | same logs (accum_old→accum_new deltas) |

## M42 block (session 41 continued, 2026-10-22) — NOTUNTILTECH live; substitution slots $TECH0/$TERRAFORMTYPE6 closed; tech record +0 = display-name pointer

| addr / token | what it is | confidence | how known |
|---|---|---|---|
| NOTUNTILTECH else branch | gate fail on a non-rewrite mode (`n` Condenser mode 0xc, tech 60) → `TECHFAIL → ADVISOR/PANE id=NOTUNTILTECH` — the generic advisory proven live; rejects cleanly (no STORE/debit/tile change) | **H (live)** | `m42n_gdb.log` chain + `m42n_issue.json` post |
| Script.txt `#NOTUNTILTECH` | `The "$TERRAFORMTYPE6" operation cannot be performed until we discover $TECH0.` — rendered live verbatim from `0x997120` | **H (live composed)** | post-run readback matches Script.txt text |
| `$TERRAFORMTYPE6` = substitution **slot 6** | not a mode index — slot 6 of the `0x99a01c` table holds the attempted operation's display name ("Construct Condenser" live); set via `0x6265a2` | **H (live)** | slot-6 readback post-run |
| `0x6265a2(slot<10, text, v3, v4)` | substitution-slot setter (sibling of `0x626634`): writes `0x999ff4/0x999fcc` values, formats text via `0x61482f` into `0x99a01c+slot*0x100`; guard `slot<10`; 86 callers | H (body) | shard_021 body |
| tech record `0x92fdb4+id*44` layout | **+0 = pointer to display-name string** (heap arena), **+4 = short token** — corrects M40 "name at +0". 18→"Monopole Magnets", 60→"Ecological Engineering", 59→"Environmental Economics"; cost/level ints +0x10/+0x14 | **H (live)** | pointer derefs 2026-10-22; arena strings |
| terraform op-name table `0x94d2f8` | 14 × (land name, sea name, menu key char) triplets — Farm/Kelp Farm/`f` … Mag Tube/`R`, Bunker/`K`, Sensor/`O`, Condenser/`N`, Echelon Mirror/`E`; sea variants Mining Platform/Tidal Harness; `$TERRAFORMTYPE` name source | **H (live deref)** | table read 2026-10-22 |
| tech 60 = "Ecological Engineering" | gates Condenser (mode 0xc) + presumably Echelon/Aquifer/Borehole family; players 1/2/4 have it (byte 0x16), player 3 does NOT | **H (live)** | `m35_gate` + tech byte + composed pane |

## M43 block (session 41 continued, 2026-10-22) — base owner byte = player index (identity); `0x4e3700` semantics corrected; tile owner nibble; we own zero bases

| addr / token | what it is | confidence | how known |
|---|---|---|---|
| base `+4`/`+5` (stride 304) | **owner player index** (the two bytes are always equal) — NOT a separate faction-ID namespace; M38's "faction ID ≠ player index" retracted. Per owner: {1:10, 2:24, 4:7, 5:6, 6:16, 7:9}, none for 0 or 3 | **H (live, 167/167 unit-on-base owner matches)** | scan 2026-10-22 |
| `0x4e3700(x,y,player)` | nearest-OWNED-base scan: compares **byte at base+4** with the player arg (Ghidra `psVar7` is `short*`: `+1` ⇒ base+4, `[-1]` ⇒ base+0=x, stride 0x98 shorts = 304 B); Chebyshev-ish dist w/ wrap; sets `DAT_008f0d34`; returns idx in `local_10` frame | **H (body, semantics corrected)** | shard_012 re-read + live byte dumps |
| us owning zero bases | all 5 player-3 units `home_base@+46 = 0xffff`, chain `+48 = 0xffff`; no base byte 3 ⇒ `0x4e3700(…,3)` never matches ⇒ cost base-distance branch inert (data, not code quirk) | **H (live)** | unit scan + base scan |
| tile `+2` low nibble | **tile owner = player index**, `0xf` = unowned; hist {0:199, 1:317, 2:468, 3:45, 4:345, 5:130, 6:261, 7:269, 15:1166}; player 3 owns 45 orphan-border tiles, player 0 (destroyed: no units/bases) 199 | **H (live histogram)** | 3200-record scan |
| base `+64` u32 | **per-base** mineral accumulator (differs across bases: 43/4/4/78), mirrored at `+152` in the 304 record; no third copy | **H (live)** | dumps bases 0–3 |
| player 0 | destroyed faction: no units, no bases, owns 199 tiles, still visited by the turn engine (`cur=0`) | **H (live) + M30** | scans + m30 trace |
| alpha `#FACTIONS` | 7 scenario factions GAIANS/HIVE/UNIV/MORGAN/SPARTANS/BELIEVE/PEACE (def idx 0..6); runtime faction records carry **no def-index byte** (no permutation offset 0..6 across live players, no name ptrs) — player↔faction-name mapping open (scenario/save section) | H (alpha) / open | data/alpha.json + record scan |

## M44 block (session 41 continued, 2026-10-22) — economy idle run: our income/upkeep are BOTH zero; AI rates measured; Council-pane OK bar found by colour; tile mask bit 0x2 = unit present; type-record base 0x98ad88

| addr / token | what it is | confidence | how known |
|---|---|---|---|
| our energy `0x94d650+3*0x82f*4` | **flat 15 across 12 idle rounds (2304→2315) = 0 net/turn**; HUD readout agrees (Commerce/Gross Income 0/turn, Total Costs 0/turn, NET INCOME 0/turn) ⇒ zero bases = no income AND upkeep is not charged to faction energy | **H (live, 12 snapshots + HUD OCR)** | `evidence/m44d_idle.json` + `m44d_run.log` |
| AI energy/mineral rates | per-round Δenergy {1:-1.4 2:-1.3 4:+10.9 5:-0.5 6:+5.3 7:-0.9}, Δminerals {1:+2.3 2:+8.3 4:-11.2 5:-1.9 6:+31.2 7:+1.1}; p4's ≈exact anti-correlation ⇒ unspent base minerals → energy at ≈1:1 | H (rates) / O (1:1 rule) | same JSON, first differences over 11 intervals |
| message-bar OK bar (bottom-centre pane) | blue bar y **488-507**, x **268-532**, rgb (103,91,181) — the ONLY way out of a Council/PROPOSAL/elected pane; label is unreadable to tesseract; HUD chrome has a decoy 1-px blue line at **y 526 in every frame** | **H (live, click-dismissed 3×)** | `find_ok_bar()` in `scripts/m44_idle.py` + `m44d_run.log` events |
| tile record `0x2c` | == the map file's two 22-B cells `(2n,y)`++`(2n+1,y)` byte-exact (live autosave); accessors (`0x582ed0`, `0x5831a0`, elev readers) are **parity-blind** (`40*y + x>>1`, +0 elev / +8 mask) ⇒ the pair shares elevation + the +8 mask | **H (byte-exact vs save + code)** | `cellcmp3.py`-style comparison + shard bodies |
| tile mask bit `0x2` | **a unit is standing on the record's tile pair** — 3193/3200 agreement, 0 false negatives, 7 stale positives | **H (live histogram)** | full-map scan vs unit array |
| record `+0x18` | second mask-shaped dword (odd half +2); tracks +8 but not written by the parity-blind setter; 2951/3200 records differ | H (exists, live) / open (semantics) | full-map diff scan |
| terraform mask vocabulary | farm 0x8000, soil enricher 0x80000, mine 0x10, solar 0x40, forest 0x200000, road 0x4, magtube 0x8, bunker 0x800, **airbase 0x40000 (k=8 clears bunker, work 10)**, **sensor array 0x80000000 (k=9, work 4)**, fungus 0x20 (k=10 clears/k=11 sets), condenser 0x400000, echelon mirror 0x8000000, k=14 0x1000000 (work 24), k=15 work 18, raise/lower 0/0 work 12 | **H (runtime table × live op-name strings)** | `0x6938f0+k*32` + `0x94d2f8` derefs |
| `0x94d2f8` | 14 × (land name, sea name, **key-char string**) stride 12 — corrects M42's "key char" (it is a string) and the k=8 "Sensor" guess (k=8 = **Construct Airbase**, k=9 = Sensor Array) | **H (live deref)** | strings "Build Mag Tube"/'R', "Construct Airbase"/'.', "Construct Sensor Array"/'O' … |
| type record base **0x98ad88** | stride 52: `+0` name[34], `+32` ability u32 (=0x98ada8), `+36` domain (=0x98adac), `+42` class (=0x98adb2). Standing ABSOLUTE addresses correct; "record base 0x98ada8 / name at +20" was wrong. type 0 Colony Pod(cls 8), 1 Formers(cls 9), 193 Scout Rover(cls 3), 194 Synthmetal Garrison(cls 2), 195 Laser Squad(cls 1); ≥196 types vs alpha 15 template rows | **H (live strings × alpha × `0x4d44d0` gate `class==9`)** | string scan + `#UNITS` rows 0-2 |
| autosave ring | the game rewrites all 8 slots: 30/20/10 every 10 y (2290/2300/2310) then 5,4,3,2,1 yearly (2311-2315); year u16@`0x54` matches | **H (live mtimes + header)** | `programs/saves/auto/` scan |
| our survivors | idx 30 Colony Pod (type 0) @ (45,11) + idx 31 Laser Squad (type 195) @ (43,11), both Hold; **Formers unit (type 1) dead** — no terraformer left | **H (live scan)** | unit scan + type-name deref |

## M45 block (session 42, 2026-10-22) — first base founded: `b` path live-traced; NEWBASE accepts Return; mask bit 0x1000 = base border (radius ≈3, pop-independent); Ghidra `FUN_` addresses are VERBATIM (7 of 15 bps were +0x400000 off and silently never fired)

| addr / token | what it is | confidence | how known |
|---|---|---|---|
| `0x4d1280(unit)` | the `b` / BUILD BASE handler. Gate order: class byte (`type+42`)==8 else NEEDCOLONISTS → NOTINTRIAD (`(elev<3) != (0x92ae81[domain*0x90]==1`) → FUNGUSDANGUS (mask 0x20 ∧ elev>3) → NOTONMONOLITH (0x2000) → NOTONROCKY (rec+5 & 0xc0 > 0x40 ∧ elev>3) → SIMULNO (`0x5255e0`, false in solo `0x920434==0`) → can-act `0x5acc00` → BASETOONEAR (8-neighbour mask bit 0x1 ∧ owner nibble<8) → border dispute `0x4e3b50` → limit `0x4e9b40` → name `0x4e3cf0` → NEWBASE pane `0x462d30(s_NEWBASE,0x17,buf,0)` → **`0x4cca50(unit,name)`** | **H (static body + live trace)** | `scripts/fn.py 0x4d1280` + `evidence/m45a_gdb.log` (`SETTER unit=30`, `PANE #1 id=NEWBASE`, `CREATERET base=73`) |
| call sites pinned by E8 scan (`.text` file offset = VA−0x400000) | CREATE call `0x4d1d9c`→return `0x4d1da1` ($eax = new base idx); ALLOC call `0x4ccbdd`→`0x4ccbe2`; BORDER call `0x4d14f6`→`0x4d14fb`; LIMIT call `0x4d1945`→`0x4d194a`; ADVISORY sites `0x4d12e6 …0x4d1e10` (12 of them, all `0x483470`) | **H (byte scan of the exe)** | `scratch` E8 scan; `objdump` CANNOT read this PE ("invalid bfd target") — use capstone or a raw E8 scan instead |
| can-act `0x5acc00(unit)` | refuses (→ UNITMOVED) iff `unit+4 & 0x4200 == 0` **AND order byte `+17` ∈ {1,2,3}**; owner check `unit+14 == 0x91b5b4`; MP check `0x5ac650(unit) − unit+40 > 0`. ⇒ **poke `+17 = 0` to make a Hold unit key-able** (M40's poke, now explained) | **H (static + live)** | body + m45a (both units were `+17`=2; poke made idx 30 selectable) |
| base-limit `0x4e9b40` → **12** | returned 12 for us pre-founding; the BUREAUCRACY pane fires only when `*local_2c != 0 && count % limit == 0` — i.e. at a nonzero multiple of the limit | H (return value live) / O (pane rule reading) | `M45 LIMITRET eax=12` |
| border owner `0x4e3b50(owner,x,y,0,0)` | **returned −1** for (45,11) at founding although the tile's owner nibble was already 3 ⇒ nibble layer ≠ border layer; −1 = unclaimed ⇒ the TERRPACT/THISLANDISMYLAND branch was skipped, no dispute pane | **H (live return)** | `M45 BORDERRET eax=-1` |
| **mask1(+8) bit 0x1000** | "tile is inside a base's claimed border": 1258 pairs flagged; assigned to nearest base → **12-31 pairs per base, Chebyshev max 3-9, mean ≈3.3, independent of pop** (pop 1 → 18.7, pop 11 → 13.5); mask1-only 1238 vs mask2-only 1; includes ocean pairs; OUR tile gained it at founding (0x108006 → 0x109005, farm bit 0x8000 cleared in the same write) | **H (statistical, 74/74 bases)** | `scratch/m45_border.py` + per-base footprint assignment |
| mask bit 0x1 = base on the pair | now **74/74** base tiles (was 73/73); it is the precondition `0x4e34f0(x,y)` checks before linear-scanning `0x95da10` (stride 0x130, compares +0 x / +2 y) | **H (live, re-verified post-founding)** | `scratch/m45_mask.py` |
| base record +56 | constant `0x00dfbe41` in all 74 records — M44's "copied from the unit's home base" reading is WRONG (it never varies) | **H (live census)** | base scan |
| base record +64 == +152 | holds 74/74 post-founding (M44's mirror claim survives). Ours oscillates 10→10→6→2→8→4→9→4→8→2 with no trend | H (mirror) / H (values) | base scan + idle JSONs |
| our base | idx 73 at founding → **idx 72** now (array compacts when any base dies; count stayed 74): (45,11) owner 3, **pop 5 → 4** (nutrient shortfall attrition, NOT eco-damage), name **"Climactic Research"** (game-generated default), facilities HQ + Recycling Tank + Recreation Commons + Energy Bank + Network Node | **H (live memory + screenshot `m45a_post.png`)** | `evidence/m45a_base.json` + base scan |
| NEWBASE name pane | `#NEWBASE` = `#x 10 #y 40 #xs 320`, caption "Enter a name for your new base." + `Name:`; **a plain Return accepts the generated name** (no typing, no click; FIRSTBASE's OK (400,171) never needed) | **H (live)** | m45a (`post-b: Return on dialog pane` → `CREATERET`) |
| **BASE screen after founding** | classify kind `base` (BASE_WORDS governor/nutrients/conquer/discover): top menu EXPLORE/DISCOVER/GOVERNOR/BUILD/CONQUER, RESOURCE/SUPPORT/PSYCH tabs, RENAMEd/OK row at y≈365 — outside `find_ok_bar`'s 430-520 band. `service_pane` had NO `base` branch → m45b spun 15 min on 1 round. **Fix: `kind=="base"` → one Escape** (M26) | **H (live; patch in `m44_idle.service_pane`)** | `evidence/m45b_idle.json` (1 round) + `m45a_post.png` |
| economy after founding (16 snapshots 2315→2329) | faction energy **15 ×5 rounds → 19 at 2320 → flat 19 ×9**; `m45f`'s own deltas block reports **energy3 = 0.0/round over its 9 intervals**, ≈+0.8/round across the whole window, vs the base screen's own ENERGY 003−000 = +003. Our units 1→6 (the base turns out Scout Patrols, each new unit carrying `unit+46` = home base idx 72). 2319→2320 is the one moving interval: minerals 8→4 AND energy 15→19 (≈1:1, M44's player-4 signature on our side) | **H (live)** | `evidence/m45c_idle.json` (6) + `m45f_idle.json` (10, ended on budget) |
| HUD Gross Income / Total Costs / NET INCOME | **NOT read this session** — every frame had a dialog/base screen up or the bottom-left panel showing unit info (`Scout Patrol [1-1-1] / Green / Climactic Research / Moves: 1 / No Orders`); `hud_econ` crop (262,425,132,72) OCR'd garbage | honest limit (open item) | `m45e_hud.png`, m45c `hud_econ_ocr` fields |
| **PITFALL: Ghidra `FUN_<addr>` is verbatim** | `FUN_005abb40` = **0x5abb40**, not 0x45abb40. m45a armed 7 shifted addresses (`0x45abb40 0x450bea0 0x441b780 0x450fc20 0x45355c0 0x4551a20 0x447f490`); gdb armed 15/15 anyway (memory is mapped, a wrong address never complains) and the 7 never fired | **H (cost 7 trace lines)** | corrected in `scripts/m45_base.gdb` header |
| unit display name vs type name | HUD bottom-left said **`Scout Patrol [1-1-1]`** for a unit whose runtime type record (195) says `Laser Squad` — the base is producing NEW units (nmine 1→3), so do not assume the surviving unit's type from M44's scan | H (live HUD) / O (which name the panel uses) | `m45e_hud.png` + unit scan |
| autosave↔runtime map layout | **M44's "record == two 22-byte cells at +2724 byte-exact" did NOT reproduce**: frozen pre-founding `Alpha Centauri Autosave 1.SAV` (year 2315, u16@0x54) vs live records → 3200/3200 differ; located stable ocean pairs fit no row-stride model (Δy39 same pair = 70048 B ≈ 1796/row ≠ 44·40 = 1760) | **open / re-derive** | `scratch/m45_findcells.py`, `scratch/m45_diff.py`; copies frozen in `scratch/auto2315/` |
| live state at handoff | pid 914079, year 2329, cur=3 our turn OPEN, TracerPid 0; 1 base (idx 72, pop 4), **6 units** (Laser Squad idx 22 @ (43,11) + 5 Scout Patrols type 2 @ (45,11) home 0x48), energy **19**, n_bases 75, no cls-8 colonist and no cls-9 Former left | **H (live)** | `scripts/m44_probe.py` + idle JSONs |


## M46 block (session 43, 2026-10-22) — economy decomposed: the upkeep pipeline named; HUD Gross/Costs/NET = `FUN_00445900` scratch globals; item upkeep table + disabled list decoded; the OPERATIONS DIRECTOR end-turn pane named and serviced

| addr / token | what it is | confidence | how known |
|---|---|---|---|
| **`0x521070`** | UPKEEP-PHASE DRIVER (stages named by its own progress strings UPKEEP4..7; called from turn resolution `0x5214a0`/`0x51e700`). Stage 0: per-unit transport-chain fix `0x5ab4e0` + base flags; stage 1: `0x5208f0(p)` per live player; stage 2: `0x584380`/`0x584410`; stage 3: research advance loop (byte `faction+2204` lab-team countdown → `0x5aaa20(p)` per lab team) then `0x5aa880` "Set Research"; stage 4: unit mining flags `0x4ef380`; stage 5: AI turns `0x56d0c0`; stage 6: `0x525640`×24 + autosave | **H (pseudocode + string evidence)** | `ghidra_out/shard_013.c:11918` |
| **`0x5208f0(p)`** | PLAYER-UPKEEP step. Sub-steps `0x5a1830`, `0x51f730`, `0x520540`, `0x51fe90`, `0x5551e0`, `0x556690`, `0x5a1ad0`; Corner-office check (`0x58f8b0`); **tail: `energy −= faction+4; faction+4 = 0; clamp ≥ 0`** ⇒ **faction+4 = within-round SPENDING LEDGER debited here**. Council-open trigger `0x5241c0` + COUNCILOPEN pane; `0x524340` post-upkeep | **H (static + live: +4 reads 0 at every start-of-turn, 7 players × 2 rounds)** | `shard_013.c:11640` + `evidence/m46e_econ.json` diffs |
| **`0x520540(p)`** | PLAYER-INCOME step: clears scratch; **gift payments** out of energy (relation matrix `+0xcc` pending × recipient pact flag); **calls `0x4f5a70(base)` for each of p's bases** (index as STACK arg: `push ebx; call 0x4f5a70` at 0x5206d2; ebx dec + sub edi,0x130 on slides 0x5206df-e0); AI-only stockpile conversion `energy += faction+0xe0/3 or ×2/3` gated `DAT_00985aec > 3` (ours = 2 ⇒ never); **faction-trait energy**: trait-record flag 0x4000 ⇒ +1/base or `trait%·energy/100`; turn-1 "Freebie Advance" × trait `+0xe8` count; SANCTIONSEND message | **H (pseudocode)** | `shard_013.c:11503` |
| **`0x4f5a70(base)`** | BASE-ROUND PROCESSOR: arg0 = base INDEX (stack; `mov ebx,[ebp+0x8]`); sets `DAT_008f0d60` = base record ptr (same global the whole base UI uses), **`edi := index` at 0x4f5aa9** (survives into the pipeline = the SPENDA spend operand, see M49a row), pipeline `0x4e8d60 → 0x4e78e0 → 0x4e92c0 → 0x4e93f0 → 0x4eaa10 → 0x4ef6d0 → 0x4f26e0 → 0x4ee410`, second pass with `DAT_008f0d64=1`, then **`energy += *(int *)(base + 0x7e)`** (per-base per-round energy income), trade shares → faction+0xe8, growth countdown `base+7` tick, `0x4f47f0` + `0x4ebef0(0)`; colony-disruption branch (rename pane) | **H (pseudocode + disasm 0x4f5a70 head + live: +0x7e = 0 for all 75 bases at start-of-turn = transient)** | `shard_012.c:24241` (the `+=`); `evidence/m49a_*` |
| **mineral spend/clamp model (M49a)** | per round `base+0x40 += base+0xd0` unclamped (IADD 0x4ef7f6); at EVERY completion (COMPLET 0x4efe41, unit or facility) SPENDA 0x4efed8 does `storage −= edi` where **edi = the base's SWEEP-ENTRY INDEX** (from 0x520540's `push ebx`, via 0x4f5a70 0x4f5aa9; the pop-growth path in 0x4ef6d0 never writes edi — verified 32-bit disasm + 3 runs: our edi=10 = index-at-entry while current idx drifts 71→69→60; AI edi values == their entry indices, e.g. 44 recurs). Then event-owner clamp (`(1<<owner)&mask`, gate 0x4eff02): `storage := max(0, min(d0, cap))` (stores 0x4eff20/23). **esi at COMPLET is path residue** (pop-growth path: result of 0x4e40a0/0x48ee00 = 8 for us; facility path: type-record scratch). M48d's "Scout Patrol cost 10" RETRACTED — 10 was our base index; pop-growth units effectively free; real per-unit/facility mineral cost OPEN (candidate 0x4f26e0) | **H (disasm + live ×3)** | `evidence/m48d2_watch.log:356-361`, `m49a_watch.log:249-259`, `m49c_watch.log:381-390` |
| **`0x4f47f0`** | FACILITY-UPKEEP CHARGE (per base, turn>1): per completed facility `energy −= 0x4f4760(item, owner)` **directly** (not via the ledger) and `faction+0xe0 += cost`; **insufficient funds ⇒ auto-SELL a facility** (bitmap bit cleared, refund = `0x4e40a0 × refund table 0x984d44[item·0xc]`, POWERSHORT warning) | **H (pseudocode; cost side verified live via the 2-vs-3 disabled-list match)** | `shard_012.c:23470..23500` |
| **`0x4f4760(item, p)`** | ITEM-UPKEEP COST: item 27 special (`min((faction−0x218 array + 1)/2, 0x572300(p))`); **0 if item on p's disabled list** (`0x927a7c + p·0x59c`: count +0x20, types +0x24 (8 ints), items +0x44, `type==2` ⇒ disabled); else table **`0x984d48 + item·0x30` int0** | **H (pseudocode + live decode)** | `shard_012.c` + live table/record reads |
| **item table `0x984d48`** | 39 rows × 0x30 B: **int0 = upkeep (0-6), int1 = required-tech id** (names read live from `0x92fdb4 + id·44`: 44=EthCalc 4=Psych 45=IndEcon 2=InfNet 59=EnvEcon 75=SentEco …). **Runtime item idx = alpha `#FACILITIES` line idx + 1** (runtime 13 = EnvEcon-gated = Tree Farm = alpha 12 ✓). Costs: HQ 0, RecTank 0, RecCommons 1, EnergyBank 1, NetworkNode 1, Fusion Lab 4, Quantum Lab 3, Nanoreplicator 4, Quantum Converter 6 … | **H (live table read + tech-name cross-match)** | m46 scratch probes; alpha.txt 591-628 |
| **`0x4f26e0`** | **MINERAL↔ENERGY CONVERSION / INCOME step** (runs right after the pipeline `0x4ef6d0` in `0x4f5a70`): early-return if event-owner ∧ `~(base+0x38)` bits 0x1a/0x1c set (**our base always takes this gate** — f30 bit 0x1c) or `base+0x40==0`; amount ebx = f(energy pool `0x94d650+p·0x82f·4`, queue `base+0x50`, item-table int1 (`\|q\|·0xF0+0x984d44+0x44`), gov/trait term `0x927a84+p·0x3c`+0x50 (100 ⇒ ×2), globals 0x985bb8/0x985aec), clamped `0..min(derived, pool−storage)`; **THIRD storage writer 0x4f2d7d: `base+0x40 += ((pool/esi)·45)/trait`** (CREDIT — live deltas 0…+12, storage GAINS for non-event owners; event owners get the store but skip the energy-side at 0x4f2d85); non-event owners also adjust the energy pool (0x4f2dc4-0x4f2e97). NOT a production cost — production mineral cost still open (only debit = M49a index quirk 0x4efee0; `0x4ee410` never touches base+0x40) | **H (disasm + live: 28 entry hits / 10 store hits, deltas +0/+1/+2/+3/+12)** | `evidence/m50a_watch.log:59-246` (F26E0/CONVST/RET26E0 lines 131-192) |
| **disabled list (ours)** | `type[2]=2, item[2]=8` ⇒ **Network Node upkeep zeroed for our faction** ⇒ Σ upkeep = 0+0+1+1+0 = **2** = live `744f28`/`744f2c[72]` ✓. Trait-record stride is **0x59c bytes** (`0x167` is Ghidra's int-index) | **H (live)** | m46 record read |
| **`0x421fe0(item, base, 0)`** | BASE-HAS-ITEM: byte bitmap at **base+0x8c**, byte `item>>3`, bit `1<<(item&7)` (mapper `0x507410`); our base: bytes 0xCA 0x01 = items {1,3,6,7,8} = all five facilities completed | **H (pseudocode + live bitmap decode)** | `shard_001.c` + live |
| **`0x445900(player, 0)`** | ECONOMY AGGREGATOR — recomputes the HUD scratch globals on every redraw: **`0x745734 = Σ base+0xfc`** (Gross Income row), **`0x744f28 = Σ 0x4f4760`** (Total Costs row), **`0x7457d4`** trade, **`0x7457dc = Σ(base+0xfc − upkeep) − gifts`** (NET INCOME row), `0x744f2c[base]` per-base upkeep, `0x745738[39]` item counts, `0x74572c = Σ base+0x104 × (0x423af0(faction+0x54)·10+100)` food, `0x745730` self-sufficiency % | **H (pseudocode + live: 2/2/0/0 ⇔ energy flat 19)** | `shard_003.c:465-519` |
| **`0x49fee0` / `0x45a920`** | FACTION DISPLAY pane (rows 0x39 energy `faction+0`, 0x17d=745734, 0x17e=744f28, 0x17f=7457d4, NET=7457dc, FACTENERGY row) / the economy readout painter ("Total Costs" string call at `shard_007.c:3975`) | **H (pseudocode)** | `shard_010.c:2691`, `shard_007.c:3764` |
| **`0x4eaa10`** | PRODUCTION SPLIT: `base+0xd4 = base+0xc4 − base+0xf4`; sliders `a=faction+0x104`, `b=faction+0x108` (recomputed by `0x51fe90`): `base+0x100=(a·prod+4)/10`, `base+0xfc=min(prod−0x100,((10−a−b)·prod+4)/10)`, `base+0x104=leftover`, `base+0x108=((9−a−b)·prod+4)/10` capped. Live ours: c4 3 d4 3 buckets 0/2/3/2 — the split's true inputs include facility multipliers upstream (O) | H (formulas) / O (inputs) | `shard_012` + live |
| **`0x4e2050`** | CORNER MARKET SELL (requires HQ = bitmap item 1; sells stockpile, `energy += proceeds`); triggered from `0x5208f0` only when `energy > 0x58f8b0(p)` where **`0x58f8b0 = max(Σ rival production, 1000)`** ⇒ surplus dump, never a bailout at our 19 energy | **H (pseudocode + live gate values)** | `shard_012.c:12413` + live `DAT_00985aec=2` etc |
| **`0x5aaa20` / `0x5aa880` / `0x5a77f0`** | RESEARCH ADVANCE ("Earning a Tech"/"Saving Earned Tech for Later", completes at threshold) / PICK-NEXT-TECH (writes **faction+0x1ac**; live: p2 completed a tech between 2330/2331: +0x1ac 30→77, +0x1a8 485→87) / RESEARCH MODIFIERS (treaty free-tech types 7/8/9 → counters faction+0xe0/0xe4/0xe8; facility counts) | **H (static + live tech flip)** | `shard_015` + m46e diffs |
| **faction record fields (map now)** | `+0` energy · `+4` spending ledger (debited+zeroed by `0x5208f0`) · `+0xdc`/`+0xf0` trait per-base counters · `+0xe0` upkeep-paid accumulator (AI stockpile source) · `+0xe8` trade received · `+0xec` composite · `+0x104`/`+0x108` production sliders · `+0x1a8` research points toward current tech · `+0x1ac` tech under research · `+0x1b8` unknown, multiples of 20 (research-budget-ish; moves for AI, open) · **+2204 BYTES** lab-team advance queue (the export's `int[2204]` is out of record) · **record size = 2095 ints = 8380 B = stride 0x20bc** (the "2111 ints" earlier reads spilled 16 ints into the next record — int[2095] = next player's energy, a free self-check) | **H (live diffs)** | m46e rounds 2330→2331, all players |
| **OPERATIONS DIRECTOR end-turn pane** | Script confirm: "Some of our units have not yet moved this turn. DO YOU REALLY WANT TO END THE TURN NOW?" rows `Cancel.` (default) / `Yes, end the turn.` + blue OK bar **y≈215-350 (drifts)** — outside `find_ok_bar`'s 430-520 band; Return = OK with Cancel ⇒ no-op; TURN COMPLETE visible behind it ⇒ button-visibility checks lie. **Servicing: Cancel-word centre (cx,cy) → click (cx,cy+24) → click (cx,cy+49)** (offsets identical on two frames with pane y 296 and 176). In `m44_idle.service_pane` (keywords `wanttoendtheturn`/`havenotyetmoved`) + `scripts/m46_econ.py` | **H (two live frames + 2 serviced runs)** | `evidence/m46d_confirm.png`, `m46d_yesok.png`, `m46e_econ.json` |
| **`hud_up(png)`** | reliable HUD test = orange-pixel count (r>180, 60≤g≤160, b<80) > 300 in box (600,395,800,425); TURN COMPLETE button bbox x 609-791 y 405-426, TURN_BTN (650,410) inside; base-screen FORCES SUPPORTED panel has zero orange there. Needed because busy-HUD OCR garbles ("turngomplete") and the hover-info panel makes `classify()` deny hud | **H (calibrated on 3 frames)** | `m46_econ.py` + pixel scans |
| panel-net vs Δenergy, round 2330→2331 | p1 30/+4/+40pts · p2 16/−5/(tech done) · **p3(US) 0/0/+4** · p4 29/+18/+36 · p5 7/+7/+7 · p6 10/−24/+11 · p7 25/+11/+37 — exact for us and p5; gaps = ledger debits (research/gifts/AI terraform), mechanism proven, per-action split open | **H (live)** | `evidence/m46e_econ.json` |
| the 2320 +4 credit | one-off mineral→energy-shaped credit (minerals 8→4, energy 15→19). NOT Corner Market (surplus-gated >1000), NOT the AI stockpile line (`DAT_00985aec > 3` gate, ours 2). Candidates: Energy Bank "Economy Bonus" (alpha effect column) / transient `base+0x7e` path. **Mechanism OPEN (M)** | O/M | m45c/m45f JSONs + this session's gates |
| `base+0x7e` | consumed per round as energy income by `0x4f5a70`; **the only reference in the entire export is the `+=` read — no writer found in any shard** (searched `+ 0x7e`, `+ 126`, casts, byte-index forms); reads 0 for all bases at start-of-turn ⇒ transient within upkeep; unaligned (spills into the 0x80 field: the "65536" values on 4 p2 bases are just that field's 1s) | **H (live + exhaustive grep) / writer OPEN** | m46 scratch scans |
| PITFALL: `pkill -f <pat>` self-match | killed my own shell 3× this session because `<pat>` appeared in the shell's own cmdline (`m46.d`, `m46.econ`, `m46[._]d` all bit). Kill by PID or use a pattern that cannot appear literally in your command | **H (cost 3 killed shells)** | this session |
| live state at handoff | pid 914079, year **2332**, cur 0 (AI turn), TracerPid 0; energy 19 unchanged; 1 base idx 72; m46e runner exited cleanly on budget (2 rounds); no runner/OCR job left running | **H (live)** | m46e JSON + probes |

## M47 block (session 44, 2026-10-22) — write provenance: the exact stores that move faction energy, and the `base+0x7e` correction

| name | address / evidence | status |
|---|---|---|
| **income store** | `0x4f5c8c` in `FUN_004f5a70`: `mov 0xfc(%ecx),%edx; add %edx,%eax; mov %eax,0x94d650(%esi)` — `ecx` = base record, `esi` = `player·0x20bc`. **Faction energy += base+0xfc** (the GROSS bucket). Live: 19→21, `evidence/m47e_watch.log` | **H** (live watch + disasm) |
| **facility-upkeep store** | `0x4f4952` in `FUN_004f47f0`: `mov 0x94d650(%edi),%ecx; sub %eax,%ecx; mov %ecx,0x94d650(%edi)` then `+0xe0 += cost` at `0x4f4962`. `esi` = runtime item id. Live: items 6,7 = 1 each (21→20→19) | **H** |
| **AI per-base direct debit** | `0x4f2dc2` in `FUN_004f26e0`: `add %eax,(%ecx)` with `ecx` = the energy address, `eax` negative. The production/rush step that reads `energy/10` and `energy/50`. **Bypasses the ledger.** Live: Morgan −7 twice in one round | **H** |
| **end-of-round energy recompute** | `0x506d2b` (`mov %edx,0x94d650(%eax)`, `eax` = `player·0x20bc`) inside Ghidra's `FUN_00502cd0` block (a huge lump — treat the containing name as unreliable, the address is solid). Live: p4 := 905 | **H** (address), name **O** |
| **mission-year store** | `0x51f554` in `FUN_0051f320` — the turn-advance routine; used as the watchpoint **positive control** (2334→2335) | **H** |
| **`base+0x7e` correction** | never written in two armed rounds (`0x96300c` watch, 0 hits); reads 0 always. Ghidra's `*(int *)(DAT_008f0d60 + 0x7e)` is typed **short \***, so the byte offset is `0x7e·2 = 0xfc`. **There is no transient income field** — the addend is `base+0xfc`, and M46's "no visible writer" was a decompiler artifact | **H** |
| **spending ledger `faction+4`** | 0 writes for us and 0 for Morgan across a full idle round ⇒ its writers are **action-time** (research / gifts / terraform), not upkeep. Still **open** | **M** |

## M51a block (session 50, 2026-10-22) — the `+0x3c` writer named: `FUN_004ee410`; the converter gate is a different code path

| what | evidence | conf |
| --- | --- | --- |
| **`base+0x3c` set to 40** | `0x4ee82f` inside `FUN_004ee410` (0x4ee410, 2076 B); live `old=500 new=40 pop=7` on "Climactic Research" (evidence/m51f_watch.log:230) | **H** |
| **`base+0x3c` stepped by `cc`** | `0x4ee8c7` = `mov DWORD PTR [edi+0x3c],esi`, Δ = −3 per round matching `base+0xcc`; 40→37→34→31 over three rounds (evidence/m51f_watch.log:238) | **H** |
| **our base diverts at the flag test** | hits `0x4f2705` then `0x4f271e` with `ecx=0x20` and never reaches PASTFLAG; 197 gate hits vs 194 past-flag hits, zero PASTFLAG with `ours=1` (evidence/m51f_watch.log:229) | **H** |
| **record identity is the NAME, not the index** | VISIT prints the name each pass; "Climactic Research" moved idx 71 → 70 between sessions (evidence/m51f_watch.log:209) | **H** |
| **who writes `base+0x40`** | not observed in M51a (no `W40_*` hit); M50b's 200→7 remains unexplained | **open** |
| **who writes `base+0x40` (CLOSED, corrects the row above)** | hw watchpoint on our base's `+0x40` fired only at `0x4efee0` (SPENDA, store `0x4efedd sub esi,edi`) and `0x4eff23` (CLAMP), twice in 2 rounds (evidence/m52a_watch.log:318, :326; same in m51f :219, :227). Clamp = `max(0, min(base+0xd0, cap 0x92a370=10))` (static 0x4efee6-0x4eff20) ⇒ M50b's 200→7 is that store with d0 = 7. `FUN_004ee410` has ZERO `+0x40` refs in 2076 B | **H** |
| **`0x4e40a0(p, arg2, idx)` = ECONOMIC FACTOR (0..10)** | event-owner gate `(1<<p)&DAT_00985b10` ⇒ base 10; rescale `DAT_0092a290` (10) / `DAT_0092ada8` (1 ⇒ ×0.9, 0 ⇒ ×0.8); `arg2 == 0` ⇒ score = `clamp(faction[p].int[17]@0x94d694+p·0x20bc + 2·(base+0x30 byte0 & 4) + …, −2, 5)` then `(base·(10−score)+9)/10`; `arg2 == 1` ⇒ government multiplier switch, index `faction[p].int[20]@0x94d6a0+p·0x20bc + 7`, table `0x4e4318` (12 dwords; ours = index 7 = `0x4e430f` ×1, cases 0-4 = ×1.3). M50a's "(1<<p)&mask event test" was only the first gate | **H** |
| **`0x5ac950(type, idx, out)` = PER-TYPE PRODUCTION WEIGHT** | `esi = arg1` indexes the unit/facility type record `0x98ad88 + type·52`; returns `byte[type+0x29]` (+41), clamped [1, 999] only when class byte `+0x2a` == 8 and idx ≥ 0; `type < 0x40` short-circuits to `mov eax,ebx` (0x5ac996 → 0x5aca9c → 0x5acaa9, evidence/m52b_fn5ac950_disasm.txt:25-26, :119, :123). Live +41: Colony Pod 3, Formers 2, Scout Patrol 1, Transport Foil 3 | **H** |
| **`base+0x50` = queued production ITEM ID** | live 2 = unit type 2 "Scout Patrol" (name from `0x98ad88+2·52`); QGATE `0x4ef88b` decodes `0xffffffda` = empty, ≥ 0 = id, < 0 = `|q|` with `[ebp-0x1c] = |q|−39` and 34/39 thresholds (evidence/m52b_watch.log:388). Replaces M48d's "transient scratch" | **H** |
| **SPENDA subtrahend = `0x4e40a0(owner,1,−1) × 0x5ac950(queue_id, idx, 0)`** (M49a index quirk FALSIFIED) | `0x4f5aa9 mov edi,edx` takes edx from `0x4f5a9c mov dl,[ecx+0x4]` ⇒ edi starts as the **owner byte** (222/222 visits, evidence/m52b_watch.log:386, :62, :94, :109, :139); the queue path overwrites it: `0x4efa4b mov edi,eax` (factor 10) then `0x4efa52 imul edi,eax` (×1) ⇒ 10 charged at `0x4efedb` (:391, :392). `0x4eaa10` preserves edi (`push edi` 0x4eaa41 / `pop edi` 0x4eb672). M48d's "Scout Patrol cost 10" restored in substance | **H** |

## M53b block (session 56, 2026-10-24) — `+41` is a COST FACTOR, not a weight; the price is `0x4e40a0 × +41`

| what | evidence | conf |
| --- | --- | --- |
| **type-record `+41` (`0x98adb1`) = COST FACTOR** | exactly ONE writer in the corpus: `shard_015.c:9358` `(&DAT_0098adb1)[type·0x34] = FUN_00595820(chassis, weapon, armor, ability, reactor)` inside `FUN_00595b10 @ 0x595b10` (`:9273`); grep of both Ghidra store renderings across 42 shards finds no other. `FUN_00595820` (`shard_015.c:9124`-`:9258`) sums chassis `+4` cost + weapon `+3` cost + armor `+0xa` cost with triad/reactor/ability adjustments; the three input tables are the alpha rules tables byte-for-byte (`programs/alpha.txt:344-345`, `:383`, `:419`). `scripts/m53b_costcalc.py` reproduces 180/188 populated rows live (`evidence/m53b_costcalc_digest.txt`, table dump `evidence/m53b_types.tsv`, write-up `evidence/m53b_findings.md`) | **H** |
| **price = `0x4e40a0(owner,1,−1) × +41`; 1 unit of `+41` = 10 minerals** | affordability `base+0x40 < iVar3·iVar4` `shard_012.c:20722`; debit `base+0x40 −= iVar3·iVar4` `shard_012.c:20866`; pane `shard_001.c:4705-4708`; printed price `__itoa(mult × +41)` `shard_014.c:19723-19725`. Live multiplier = 10 (`0x92a290`=10, `0x92a294`=10, `0x92ada8`=2, `0x985b10&0xff`=0x08, government field 0). M52b measured exactly 10 minerals debited for Scout Patrol with `+41 = 1` (`evidence/m52b_watch.log:391-392`) | **H** |
| **alpha `#UNITS` Cost wins over autocalc** (`0 = Autocalculate`, `programs/alpha.txt:554`) | the only 3 formula-mismatches with `ability == 0` are the 3 shipped rows with an explicit non-zero Cost — Mind Worms 5, Isle of the Deep 8, Locusts 10 (formula 11) — and live `+41` equals the alpha value in all three; Alien Artifact's explicit 10 also equals the formula | **H** |
| **`+43` (`0x98adb3`) = auto-calculated AI role byte** | ladder in `FUN_00595b10` `shard_015.c:9366`-`:9441`: noncombat packages get `weapon mode + 0x20` (`:9431`) → 39/40/41/42/43/44 = live values for Transport Foil/Colony Pod/Formers/Supply Crawler/Probe Team/Alien Artifact; combat gets 1…10 — reproduces Mind Worms 1, Isle 6 (sea branch), Locusts & Unity Chopper 9 (air + `ability&0x20`), Scout Patrol & Unity Rover 10 (`attack==1 && armor==1`, `:9419`). `+42` = the alpha Plan column, 14/14 shipped rows (ladder alone explains 10; the loader override is unlocated) | **H** |
| **CORRECTION to the M52b row above: `0x5ac950` is the type COST accessor, not a "production weight"** | it returns `+41` verbatim for `type < 0x40` (`shard_015.c:23707`), clamped [1,999] only for class 8 with a base index; the ×10 that M52b saw is `0x4e40a0`'s 100 % convention, so `+41 = 1` means 10 minerals, not "weight 1 × cost 10" | **H** |
| `0x496ad0` | `item_chooser_modal(chooser_sub, base, owner, scratch)` — the modal picker loop; the bar handler is `0x496950` = vtable+0xa8 (M53g) | **H** | 3,310 B (`evidence/m53d_fn496ad0_disasm.txt`). The dispatch byte at `[chooser_sub+0xa778]` = `pane+0xb194` = 0x6b4614 is written NOT here but by `0x496950`: 0x496993→1 (HELP), 0x4969a5→2, 0x4969b7→3, 0x4969da→**7**, 0x4969e9→**4** (DELETE), 0x496a09→**5** (INSERT), 0x496a18→6, 0x496a27/0x496a36→0, 0x496a52→**7**; gates/CANCEL stores live in `0x496950`; 0x496a91 is the shared epilogue return, not a refusal (M53g). Live: hw watchpoint on 0x6b4614 hit at 0x496a13 (mode 5), 0x4969f3 (4), 0x49699d (1), 0x496a40/0x496a31 (0) — `evidence/m53e3_watch.log:109`, `m53e4:98`, `m53e6:78`. |
| `0x496950` | `chooser_bar_button_handler(this = chooser_sub in ecx, param)` = **vtable+0xa8** | **H** | 330 B; only pointer 0x672340 = live vptr 0x672298+0xa8. Jump table 0x496a9a indexes `param+2` (`ja` → 0x496a91): 0=HELP(gate)→1 · 1→2 · 2=(gate)→7 · 3→3 · 4→4 · 5=INSERT(gate)→5 · 6→6 · **7→7 UNGATED** · −1=OK→0 · −2=CANCEL→0 + `mov [this+0xa774],-1` (0x496a43). Gate = `cmp [this+0xa774],-1; je 0x496a91` (0x496982/9c9/9f8); 0x496a91 = shared epilogue (mode stores reach it too). Fired live: param 7 ← click (365,343) → mode 7 → REPLACE D20_STORE +0x54 (`evidence/m53g_watch.log:104-112`); param −2 ← 692. One run per click (`evidence/m53g_findings.md`). |
| `0x4962a0` | `chooser_guard_setter(this in eax, cell_idx in ecx)` = **vtable+0x48** | **H** | reads `[eax+0xa774]` 0x4962b1, stores 0x4962ec, cmp 0x4962fa. Live on icon/cell clicks: guard := clicked cell index (`evidence/m53g_watch.log:70-71,101-103`). |
| `0x4963b0` | `chooser_guard_mutator` = **vtable+0x60** | M | 8 stores to `[x+0xa774]` (0x496432/542/62b/64e/6cb/6ee/708/777, incl. `=0`) with paired swaps of `+0xa818` — sort/scroll path; never fired live yet. |
| `0x4954e0` | `chooser_paint_enumerate(chooser_sub)` — item enumeration + paint | **H** | 2,915 B. Entry clears guard (0x495541) + `+0xa77c`; sets guard := enum index of the item matching the queue-slot item `[[curbase]+0x50+slot*4]` (0x495b00/0x495e6f via enum counter `+0xa818`; `evidence/m53g_fn4954e0_pseudo.txt:44-46,140,205`). Live `evidence/m53g_watch.log:68-69`. |
| **`[chooser_sub+0xa774]` (`0x6b4610` = pane+0xb190) = SELECTION CELL INDEX** (−1 = none) | census 43 refs / 13 stores, whole `.text` (`evidence/m53g_a774_all_refs.txt`); writers 0x495541/0x495b00/0x495e6f (paint), 0x4962ec (setter), 0x496432..0x496777 (mutator), 0x496a43 (CANCEL). Live: paint sets the slot item's index (5 = Scout Patrol); icon click → 6; bar-row click → 17 (phantom cell: 5-col grid, row 3 col 3 = x 381-421); CANCEL → −1. M53e's "5/17 ≠ selection 2" = cell indices (`evidence/m53g_findings.md`). | **H** | REPLACE's clickable rect is param 7 at x~340-380, LEFT of its drawn bar (364-421); the drawn body 381-421 is dead setter-territory — why is an open thread. |
| `0x417ee0` | `production_queue_edit_dispatch(this = pane, slot, insert_flag)` | **H** | 7,459 B thiscall (`mov ebx,ecx` @0x417f03). Snapshots base `+0x50..+0x74` to the stack (loop 0x41820a-0x418222), calls the chooser at 0x41860a, dispatches on `[pane+0xb194]` through table 0x419c04 (1/2/3 → 0x418cda re-open, 4/6 → 0x418703 remove-or-clamp, 5 → 0x4187a2 push 1 = INSERT, 7 → 0x4187ad push 0 = REPLACE, 0 → tail, writes nothing); on pick == −9999 rewrites all ten slots from the snapshot (0x418623-0x41863f). Live: `evidence/m53e2_watch.log:48-59`, `m53e6:77-92`. |
| `0x417d20` | `queue_slot_write(this = pane, item, insert_flag)` | **H** | 302 B. 0x417e04 `mov [eax+edx*4+0x50], ebx` (slot 1→+0x54 … 9→+0x74), 0x417dd8 insert-shift (mode 5; caught live `evidence/m53e6_watch.log:83-92`), 0x417dad delete-shift, cap-9 store 0x417df6, count+1 0x417e1d. |
| `0x6a9480` | `base_pane_ui_object` (data; chooser sub-object at `+0xa1c` = 0x6a9e9c) | **H** | Static BSS pane passed as `ecx` to `0x417ee0` (read live at `evidence/m53e2_watch.log:72`). Fields: `+0x3ff3c` base index, `+0x3ff5c` selected queue slot, `+0x3ff60` zeroed by a QUEUE-row click, `+0xb194` == the sub-object's `+0xa778` dispatch mode (0x6b4614), `+0xa774` (0x6b4610) the guard/result field — NOT the icon selection (live reads 5/17 while the chooser returned 2). |

## M53f block (session 58, 2026-10-24) — the alpha `#UNITS` loader located: Plan→`+42`, Cost→`+41`

| addr | proposed name | conf | evidence |
|---|---|---|---|
| `0x579f40` | `alpha_units_loader(row_cap 0x40)` | **H** | 293 B (`shard_014.c:21351`); opens `#UNITS` via `FUN_005ea431(PTR_s_ALPHA_00693b64, s_UNITS_00691c40)` (`:21369`); record cursor `esi = 0x98adba` (record+50), `add esi,0x34` (0x57a04e). Disp8 stores: 0x57a001 `mov WORD PTR [esi],ax` (+50 prereq), 0x57a02d `[esi-0x8],bl` (+42 Plan, guard ≥0), **0x57a037 `[esi-0x9],al` (+41 Cost, guard ≠0 = Autocalculate)**, 0x57a041 `[esi-0xa],al` (+40 Carry, guard ≠0), 0x57a04a `[esi-0x4],cl` (+46 Icon, writes −1 too); builder called first at 0x57a021. Live 14/14 on +42 and +46 vs `data/alpha.json`. `evidence/m53f_findings.md`, `m53f_disasm_fn579f40.txt`. |
| `0x595b10` | `unit_type_builder(chassis, weapon, armor, ability, reactor, …)` | **H** | 0x595c60-0x595cf2: writes `+36/+37/+38/+39/+32/+43`, calls the cost formula at 0x595ce2, stores its byte at **0x595ce7 → +41** — the image's only +41 store (30 refs / 1 store, `evidence/m53f_adb1_refs.txt`). `m53f_disasm_595c60.txt`. |
| `0x595820` | `cost_formula(chassis, weapon, armor, ability, reactor)` | **H** | disasm-true model reimplemented in `scripts/m53b_costcalc.py`; rule switch = jump table `0x595ab4` indexed `rule+7` (`evidence/m53f_jumptable.txt`), land-chassis loop 0x59597b-0x5959a6 reads `entry+8` bit 0x400. 181 formula + 4 override rows, 0 unexplained (`evidence/m53f_costcalc_digest.txt`). |
| `0x596850` | `load_save_state` (unit-type record restore) | **H** | 48-byte save records → 52-byte runtime records, loop 0x5973bc-0x597495; `0x597464 [eax+0x29],dl` (+41), `0x59746a [eax+0x2a],dl` (+42) (`evidence/m53f_disasm_597400.txt`). |
| `0x5ea466` / `0x5ea484` | `alpha_string_field(sec, col)` / `alpha_numeric_field(sec, col)` | **M** | the two accessors every alpha loader calls; the column index is the literal `#UNITS` column number (`shard_014.c:21374-21410`, `evidence/m53f_grep_alphatabs.txt`). |

| `0x596000` | `chooser_build_unit_list(faction)` | **H** | 345 B, shard_015.c:9459-9518. Writes all 128 entries of `DAT_009267e4` (`id = (slot & 0x3f) + (slot < 0x40 ? 0 : faction<<6)` ⇒ shared ids then **this faction's designed units**), computes a sort key per slot, then `FUN_005a29a0(0x80, &DAT_009267e4, keyarray)`. Called by the chooser paint at `0x495583`. Live (faction 3): first 14 ids 195,196,192,194,193,2,197,198,3,0,200,1,199,6 with Plan 0,0,1,2,3,3,6,7,7,8,8,9,9,11 — `evidence/m53h_enum_ids.txt`. |
| `0x5a29a0` | `sort_pairs_by_key(n, values, keys)` | **H** | 101 B. Bubble pass over `keys`, swapping `values[i]` in lockstep via `FUN_006288a6`, **only on strict `<`** ⇒ stable; returns when a pass makes no swap. The chooser's ordering mechanism (shard_015.c:9514). |
| `0x5a73f0` | `unit_buildable_at(type_id, faction, base_idx)` | **H** | 297 B. Requires record+0x30 bit 0; rejects if the record+0x2c faction mask has the bit; for designed ids: Plan == 8 with `DAT_00985ac4 & 0x400000`, **chassis-table `+1 == 1` with `FUN_004e4620(base.x, base.y) == 0` (the naval/sea gate)**, and ownership `id>>6 == faction`; for alpha ids the prereq word (record+50) against the tech table `0x92fdd4`/0xb. Live: exactly the five chassis-3 candidates (197,198,3,200,199) are missing from the chooser's list — `evidence/m53h_list_dump.txt`. |
| `0x5a6e70` | `secret_project_available(idx, faction, base_idx, slot)` | M | 1,396 B, the chooser's project filter (paint pseudo:147-149). Nonzero = offered; its **return value indexes the cost table `0x984d44`** (`(&DAT_00984d44)[ret*0xc]`), not the loop index. Internals open (M53i). |
| `0x4026b0` / `0x401940` / `0x495480` | `list_select_by_index(i)` / `list_item_number()` / `list_item_flags()` | **H** | The chooser's item-list accessors: `0x4026b0` walks the head chain (`+8` head, `+0xc` cursor, `+0x10` count) to index i and sets the cursor; `0x401940` returns `cursor_node+4`; `0x495480` returns `*(node+8)+8`. `FUN_00496ad0` uses the flags bit 0x20 to decide the sign of its return (shard_009.c:15032-15041). |
| `0x5f9e85` | `control_create(caption, param, x, y, w, h, owner, flag)` | **H** | 422 B. Stores the caption at `+0x29f·4`, calls `FUN_005e3ed9(x,y,w,h,…)` for the rect and **stores `param` at control+0xa78** (shard_019.c:2065) — the field the release handler forwards to the owner's vtable+0xa8. Builds the chooser's six bars (shard_009.c:14931-14993). |
| `0x5fab08` | `button_on_release(button)` — forward `+0xa78` to owner vtable+0xa8 | **H** | 383 B (shard_019.c:2500-2540): clears the two global capture slots, then `(**(code **)(*(int *)in_ECX[0x31] + 0xa8))(in_ECX[0x29e])` — i.e. calls `owner->vtable+0xa8(button+0xa78)`, gated by `+0x2aa` through `FUN_0062921c`; params −1/−2 also fire the global `DAT_0099397c` / `DAT_00993980` callbacks. |
| `0x496ad0` | `chooser_run_modal(sub, base, owner, slot)` → ±item or −9999 | **H** | 3,310 B. Creates the six bar buttons (params −2/7/5/4/−1/0, rects `((W−0x20) − 103·count)/2 + (count−1)·103`, W = `sub+0xa824` = 758, count = `sub+0xb6c`), pumps until a bar closes it, then resolves the selection cell index `sub+0xa774` through the item list: `(flags & 0x20) == 0 ⇒ −item` else `+item` (shard_009.c:15013-15041). Live cross-check: cell 12 = project 26 ⇒ −26 = M53g's observed return. |
| data `0x9267e4` / `0x9267e0` | `chooser_unit_candidates[128]` / count | **H** | Written only by `FUN_00596000`/`FUN_00596160` (shard_015.c:9488/9545) and read by the chooser paint (`local_30 = (&DAT_009267e4)[local_2c]`). |
| data `0x6b461c` | chooser item list (= pane 0x6a9480 + 0xb19c = chooser-sub +0xa780) | **H** | vtable 0x67333c, +8 head / +0xc cursor / +0x10 count; 16-byte nodes (vtable 0x67143c): +4 item, +8 detail (detail+8 = flags), +0x10 next, circular. Survives close; live dump `evidence/m53h_list_dump.txt`. |

## M53i block (session 61, 2026-10-23) — project table 0x984d38 = alpha #FACILITIES; availability gate + negative-q cost accessor

| **`0x5a6e70(project, faction, baseidx, n_scan)`** | PROJECT_AVAILABLE: gates on record+0x14 prereq tech (tech table 0x92fdd4 stride 0xb dw + ownership byte `0x985c1c[tech]` bit faction), claim table `0x985aa0[project] == −1` for project > 0x26, base+0x8c bitmap + queue scan for project < 0x23, terrain/facility probes 0x421fe0 / 0x46f8e0 / 0x4e4620 per project; scenario globals 0x985ac4/0x985aec/0x985bb8 | **H (pseudocode full read)** | `evidence/m53i_fn5a6e70.txt:16-287`; `evidence/m53i_findings.md` §3 |
| **`0x4ef6d0`** | PRODUCTION/QUEUE PROCESSOR (size 12298, runs in the 0x4f5a70 pipeline): consumes queue head; **negative-q project cost accessor** `0x4e40a0 × (&DAT_00984d44)[(−q)·0xc]` with completion test `<= base+0xcc + base+0x3c` (0x5ac950 does NOT handle negative ids); COMPLET 0x4efe41 = `cmp ebx,0x40; jl 0x4efed1` designed-unit gate | **H (pseudocode + objdump window)** | `evidence/m53i_fn4ef6d0.txt:596,768-769`; `evidence/m53i_disasm.txt` |
| **`0x4e4350(q, baseidx)`** | QUEUE-ITEM CLASS CODE for the mineral carry-over compare: chooser opened on head ⇒ displayed remaining = price − minerals iff codes equal (else half); body = HQ bit (base+0x8c facility 10) + `DAT_0092a368` mode + `q < −0x26` split ⇒ 0/1/2/3/−1/−0x27 | **M (pseudocode; == use in paint VERIFIED, code semantics INFERRED)** | `evidence/m53i_fn4e4350.txt`; `evidence/m53i_fn4954e0.txt:162-171` |
| **`0x507410(x, *pbyte, *pbit)`** | BIT SPLITTER (39 B, 203 callers): `*pbyte = x>>3; *pbit = 1<<(x&7)` — the mapper behind every base+0x8c facility-bitmap access (also 0x421fe0's) | **H** | `evidence/m53i_fn507410.txt:4-12` |
| **claim table `0x985aa0[72]`** | PROJECT → base index where last completed (−1 = unclaimed); the availability gate for project > 38; pane counter compares `== DAT_0068cbb0`; live 29/71 = −1, aa0[38]=3 | **M (gate use H via 0x5a6e70; semantics from readers)** | `evidence/m53i_findings.md` §5; `shard_001.c:5440`; `shard_012.c:14698` |

## M53j block (session 62, 2026-10-24) — claim-array geometry + the completion writer
(`evidence/m53j_findings.md`, `evidence/m53j_complet.md`, `evidence/m53j_cfg.txt`)

| addr | proposed name | conf | evidence |
|---|---|---|---|
| **claim array `0x985b3c[33]`** (CORRECTION to the `0x985aa0[72]` row above) | SECRET-PROJECT CLAIMS, index = `project_idx − 0x27` (projects 39..71 ONLY); value = owning base index, −1 = unclaimed | H | trio: gate `m53i_fn5a6e70.txt:58` flat `0x985aa0+idx*4` reached only for `0x26 < idx`; machine 0x4ef89f-0x4ef8ac `neg ecx; cmp ecx,0x27; lea edx,[ecx-0x27]`; discriminator `shard_001.c:5424-5444` (`0x411180`) walks 0x985aa0..**0x985bc0** branching ON ADDRESS at 0x985b3c (below = facility bitmap / `0x5a6de0`, at-or-above = claim). Slots 0x985aa0..0x985b38 are other globals (nb 0x985af4, year 0x985b00, mask 0x985b10, flags 0x985ac4). Live: 39→8, 41→2, 42→4, 45→3, else −1 |
| **writers of the claim array: exactly 3** | `0x4f0d83` (in `0x4ef6d0` completion path: `mov [eax*4+0x985b3c],edx`, edx = `DAT_0068cbb0` current base INDEX, guarded `test eax,eax; jl`) = pseudo `m53i_fn4ef6d0.txt:892` = shard_012.c:21475; `0x59d595` in `0x59ce10` (re-rolls `_rand() & 0x80000007` until `claim[u] == -1 && u != 4 && !(u == 5 && f == 2)` then stores the grant, `m53j_fn59ce10.txt:286-291`, sole caller `0x5a0fa0`); `0x41cd7d` in `0x41c8b0` (dtor-heavy handler, sole caller `0x41d480`, INFERRED debug/scripted) | H | disp32 + scaled-index store census over all of `.text` (`evidence/m53j_refs_985aa.txt`: 3093 refs / 8 stores in 0x985aa0..0x985bd0, 3 based inside the array); no pointer-based writer (address-takers all read) |
| **`0x4ef6d0` completion path, ordered** | race scan (idx ≥ 0x27; 0x4f0abb `jl` skips) over bases whose head slot equals ours (0x4f0b05-0x4f0b0d) → 0x4f0b4f `cmp [esi+0xcc]+[esi+0x3c], price; jge 0x4f0c28` → epilogue `ret` 0x4f0c27 (NO store); loop end → 0x4f0b78 `test [ebp-0x30]; jg 0x4f0ca1` (SOLE pay-block entry): 0x4f0ca1 `base+0x40 −= edi`(price) → clamp 0x4f0ca9-0x4f0ce9 → 0x4f0cf5 `base+0x98 := base+0x40` → 0x4f0d00-0x4f0d1a base+0x30 `\| 0x800000` then `& 0x7fffffff` → 0x4f0d35-0x4f0d71 bit-clear (`0x507410`; ONLY idx 1 = Headquarters, current faction) → 0x4f0d83 claim store → 0x4f0dc0-0x4f0e44 → announce 0x4f0f6f/0x4f0f78 (`0x6265a2` → DAT_00997120) + 0x4f0f96 (faction name 0x927894+f·0x24) → `0x48f100` (0x4f122a/0x4f1319) → **THE POP 0x4f0f46** → `ret` 0x4f26d9 | H (shapes) / INFERRED (arm meaning) | `evidence/m53j_cfg.txt` + spot-checked against `evidence/m53j_text.txt`; `[esi+…]` are base+4-shifted: `[esi+0xcc]`+`[esi+0x3c]` = base+0xd0 + base+0x40 |
| **`0x4ef5d0(base_idx)` = THE POP internals** | pending 0 → return 0; head ≥ 0 → `DAT_0094de84[faction*0x20bc+head] −= 1`; left-shift `base+0x50..` (`*p = p[1]` × pending, 0x4ef62c-0x4ef637); base+0x4c −= 1 (0x4ef64a); re-test new head via `0x5a6e70(−head,f,base,0)` / `0x5a73f0` until available; head < −0x26 → `0x446250(0x24)`; then `0x473760(x,y,2,2)` | H | `evidence/m53j_fn4ef5d0.txt`; zero queue-shift/pending stores inside `0x4ef6d0` (grep of `+0x4c`/`+0x54`/`+0x58` store shapes) |
| **`0x4f6030`** | AI PROJECT CHOOSER (size 30475): its `param_1` is 0-based-from-39 — converts `(byte *)((int)param_1 + 0x27)` before calling `0x5a6e70`, and re-reads the record at `((param_1+0x27)*0x30)` | H | header `shard_012.c:24338` (`// ==== 0x4f6030 … size 30475`), body shard_012.c:28613-28619 — third confirmation of the −0x27 geometry |

## M53k block (session 63, 2026-10-26) — the accumulation side (`evidence/m53k_findings.md`)

| addr | proposed name | conf | evidence |
|---|---|---|---|
| **`0x4e93f0`** | NET-INCOME RECOMPUTER — sole writer of base+0xd0: d0 = [eax+0xc0] − [eax+0xf0] − [eax+0xe0] (e0 zeroed at 0x4e9562 first); mirror +0x94; c0 += DAT_008f0c70; +0x48 >>= 3; eax = ds:0x8f0d60; called per base from 0x4ef6d0 loop (shard_012.c:20861/22171) | VERIFIED | m53k_fn4e93f0.txt:47-52; disasm 0x4e9544-0x4e957f |
| **`0x4ef7f6`** | MINERALS INCOME ADD — `minerals += base+0xd0`, gated d0<0 / head==−38 / +0x30&2 (0x4ef7db-0x4ef7f9) | VERIFIED live (WP `eip=0x4ef7f9 new=301`) | m53k_watch2.log WP21 |
| **`0x4ee8c7`** | PROGRESS ACCUM — `[base+0x3c] += [base+0xcc]` per turn in `0x4ee410` (display only; announce 0x4efd49 uses them) | VERIFIED live (WP 50→56) | m53k_watch2.log WP22; disasm 0x4ee8b4-0x4ee8c7 |
| **`0x4e47d0`** | BASE FOUNDER (not a turn writer): inits new record incl. +0x40, nb++ at 0x985af4, calls 4e93f0 | VERIFIED | m53k_fn4e47d0.txt |
| **`0x4e40a0` price semantics** | 10 for IN-mask factions; OUT-mask: (era table `&DAT_0068cbb8[DAT_00985aec]` − FUN_00531090 adj) − contact adj — CAN BE 0; then ×DAT_0092a290/94/10, ×9/10 if 0x92ada8==1 | VERIFIED + live case (U.N. price 0) | m53k_fn4e40a0.txt:14-19 |
| **completion arm (CORRECTION to M53j row)** | gate 0x4f0a3d `cmp minerals, edi; jl → return` = STOCK ≥ FULL price, no accumulation; race scan (0x4f0af0) runs ONLY for OUT-mask currents (gate 0x4f0ac6) and defers them if any IN-mask same-head base has d0+minerals ≥ price; pay 0x4f0ca6; **clamp B 0x4f0cc3-0x4f0ce9** := max(0,min(10,d0)) if post-pay > min(10,d0) AND in-mask; mirror +0x98 always | VERIFIED | m53k_findings.md §D; disasm windows 0x4f0a37-0x4f0cf5, 0x4f0af0-0x4f0b51 |

## M53l block (session 64, 2026-10-23) — production inputs pinned

| **`0x4e92c0`** | RATE CALCULATOR (per base, 12 pipeline callers): `bc(base+0xbc) += 0x8f0c6c`; `ec(+0xec) = pop×0x92a27c(=2) + 0x8f0c34`; **sole writer of base+0xcc = bc − ec at 0x4e937b**; HQ-bit bump `0x8f0c48 := faction+0x2880 +2` (0x4e92f5-32a); progress clamp (cc<0∧prog==0→−1); faction total `0x94dc2c[f·0x20bc] += max(cc,0)` cap 99 iff 0x8f0d64==1 | VERIFIED machine + live (Colony 28−22=6; ec 22 = 11×2) | `m53l_fn4e92c0.txt:19-31`; m53l_findings.md §1 |
| **`0x4e8d60`** | YIELD/UPKEEP SWEEP (pipeline stage 1 per 4f5a70 row): zeroes 0x8f0c2c/34/38/4c/6c/70/74/78/d38; pop table local_34[9]; loops units (<0x985af0=339) over type records 0x98ad88+type·0x34 + terrain `DAT_0092ae14 + ((x·0x692184+y)>>1)·0x2c`; feeds c6c (bc), c70 (c0), c34/c38/c4c (upkeep), c4c += 1/unit | VERIFIED pseudocode; c6c/c70 feeders CLOSED by M53m (see below) | `m53l_fn4e8d60.txt:26-211` |
| **c0 stores in `0x4e93f0`** | exactly 3 writers of base+0xc0: ×2 gated (0x985ba8≥0 ∧ same-faction ∧ head∈[−37,−34]) 0x4e943f; += 0x8f0c70 0x4e9459; ×(2+[#421fe0(19/20/21/22,cur_idx,0) true + same-faction flags 0x985bac/0x985bb0])/2 0x4e9525; idempotent when c70=0 — bc/c0/cc live stable 75/75/turn | VERIFIED machine + live | m53l_findings.md §2/§7; m53l_delta.txt |
| **mask `0x985b10/11`** | TWO bytes (b10 facs 0-7, b11 8-15). Writers: 5a0fa0 0x5a1091 b11:=0xff (global reset); 597ee0 0x59814f/15c presence loop; 59ec90 0x5a07a4/7d3; 4df630 0x4df82e/9a3 b10 := 1<<player or 0 (gated 6266e6; alt b11&0xfe); 4e0720 0x4e08ca/8d0 elimination clear both + base walk. Semantics INFERRED: standard-rules set = player + aliens; AI human factions OUT (era prices, no clamp B, race-scan targets) | writers VERIFIED; semantics INFERRED | `m53l_mask_refs.txt`; m53l_findings.md §5 |
| **era table `0x68cbb8`** | DIRECT dwords {13,12,11,10,8,7} = out-mask base price multiplier per era 0-5 (era 0x985aec live 2 → 11; ASCII after — NOT pointers; sole ref 0x4e40fe). 4e40a0 out-mask: table − nonzero-boolean(531090(0x985b30,0)) − flag, ×0x92a290/94÷10. DAT_00985aec zero direct stores (writer open) | VERIFIED live + machine | `m53l_globals.txt`; m53l_findings.md §6 |
| **owner byte@4 = faction** | base record +4 low byte IS the faction (machine 4e92c0/4e93f0 `f·0x20bc`; ground truth idx 70 ours=3, idx 8 UN=7; census {1:6,2:44,3:1,4:7,5:3,6:5,7:9}); byte@5 usually equal (idx 0 2/6 — open) | VERIFIED | `m53l_colony_dump.txt` |

## M53m block (session 65, 2026-10-23) — crawler sweep pinned

| **`0x4e8d60` filter** | SOLE feeders of c6c/c70/c34 = Supply Crawler: plan(type+42)==10 ("Supply Convoy"; ONLY plan-10 type = 5) ∧ order(unit+17)==3 ("Convoy") ∧ unit+14==base owner. Branch A (bidx unit+46==cur base ∧ yield-OK tile): `[unit+38*4+0x8f0c6c] +=` yield-fn result @0x4e8f35 (calls 0x4e8efa/0x4e8f0b/0x4e8f1c); Branch B (bidx≠cur ∧ ≥0 ∧ on base tile): +1 @0x4e8e82 then jmp 0x4e9274; good tile ∧ bidx==cur: c34[cat]+1 @0x4e9009 | VERIFIED machine + live (c6c[0] 0→1 @0x4e8f3c ×10; c70 0→1 @0x4e8e89 ×10; zeroing pair 0x4e8d79/0x4e8d80) | `m53m_findings.md`; `m53m_watch.log` |
| **`0x4e6960`/`0x4e6d40`/`0x4e7070`** | tile-yield fns = **NUTRIENT / MINERAL / ENERGY** (fields 0/1/2 of `0x4e75f0`; tile = 40*y+(x>>1), record = `*(0x92ae14)`+tile*0x2c, category = rec[0]&0xe0; per-category values = alpha `#RESOURCEINFO` VERBATIM live @0x926bd8: Ocean 1,0,0 / Base 2,1,1 / Bonus 2,2,2 / Forest 1,2,1 / Recycling 1,1,1 / ImpLand 1,0,0 / ImpSea 2,1,3 / Monolith 2,2,2 / Borehole 0,6,6) | H (machine + live: the model reproduces 36/76 bases exactly) | `m53m_dis4e6960.txt`; `m53o_recon_findings.md` §3 |
| **`0x4ddaa0`** | era chooser/setup dialog (C++ frame; callers 0x51518b/0x517e1e): cold `jge` 0x4ddb5a→0x4ddcf1 = SOLE direct store to era DAT_00985aec (eax = 0x5f1394 return ≥0) + propagates same dword to 8 slots `0x94d438+f·0x20bc` | VERIFIED machine | `m53m_findings.md` §era |
| **`0x4e78e0`** | **PRODUCTION-VECTOR REBUILDER** (pipeline stage 2, per base): seeds `base+0xbc/0xc0/0xc4/0xc8` from `[eax*4+0x94dc34]` (store 0x4e79a5; esi walks 0xbc..0xc8 per `mov esi,0xbc`/`cmp esi,0xc8`; eax = local(ebp-4) + 2095·ebx → ×4 = +0x20bc·ebx, faction-record stride) then per item adds `0x4e75f0(ebx, ?, 0, DAT_0068cbb0, byte[base+4])` into those four fields (loop 0x4e7be3-0x4e7c28, store 0x4e7c15, running total `[ebp-0x48]`, outer counter `DAT_008f0c68` set 0x4e7904 / dec 0x4e85d8). ⇒ **bc/c0 are REBUILT on every block execution, before 4e92c0/4e93f0 add the crawler terms** — the crawler nets +1 per base VISIT, not per execution. M53o: the vector is **NUTRIENT(+0xbc)/MINERAL(+0xc0)/ENERGY(+0xc4)/PSI(+0xc8, seed-only)**; exactly 7 add sites (0x4e7c15, 0x4e7ea3, 0x4e85bd, 0x4e8739, 0x4e883b, 0x4e8951, 0x4e8a32); seed live 0; the tail loop 0x4e8b6f-0x4e8d48 writes only +0x48; a read-only Python model reproduces 36/76 bases exactly | VERIFIED machine + live | `m53n_findings.md` §3; `m53n_watch.log:935-976`; `m53o_recon_findings.md` |
| **`DAT_0068cbb4`** | **ECONOMY FRESHNESS MARKER** (base index last computed; live 70 = our base while idle on OUR turn, so NOT −1 there — M53p): `4f5a70` stamps it = idx at entry (`fn4f5a70.txt`:21) and again before pass2 (:41); `4f5a70` pass3 AND both `4ef6d0` block sites are guarded `if (DAT_0068cbb4 != idx)` → those nested recomputes are structurally unreachable inside a visit (0 hits/round live; pass3 fired 1× when a nested UI chain moved it); `4f41f0`/`4ee410` stamp + run unconditionally under their own production gates | VERIFIED machine + live | `m53n_findings.md` §2 |
| **`0x4e75f0(item, ?, 0, base_idx, faction)`** | per-(item, field) production **contribution accessor** called from the `0x4e7be3-0x4e7c28` loop; is the per-field DISPATCHER: field0->`0x4e6960` nutrient, 1->`0x4e6d40` mineral, 2->`0x4e7070` energy, 3->0 and clears `DAT_008f0cc8`; an "item" is a scanned TILE (x,y args) | H (machine + live model) | `m53n_findings.md` §3; `m53o_recon_findings.md` §1 |
| **`0x4f6030`** | **UI-RECOMPUTE TRIGGER**: only caller `0x4e5ae0`; calls `0x4e3470` @0x4f6070 (cur-base ptr/index) then `0x4eb6b0(1)` @0x4f6077 and a non-zero arg FORCES the 5-call economy block => recomputes d0 (0x4e9557) and cc (0x4e937b), inside a base visit AFTER the income add 0x4ef7f6 | H (machine + live log re-parse) | `m53o_chain_findings.txt` |
| **round pipeline order (M53n)** | `0x4f5a70(base_idx)` runs **once per base per round** (76/76 live) from ONE call site (`0x5206d3` in `0x520540`); visit order grouped by owner byte@4 in faction-turn order, ascending base index within group, **our faction (3) LAST, immediately before year++**; 247 block executions/round = pass1 76 + pass2 76 + 4f41f0-B 34 + -A 4 + 4eb6b0 (UI) 55 + 4ee410-B 1 + pass3 1, and SWEEPIN == RATEIN == BCADD == 247 ⇒ **the bc-add 0x4e9331-0x4e934a is ungated** | VERIFIED live (full round 2380→2381) | `m53n_findings.md` §1; `m53n_schedule.tsv`; `m53n_watch.log` |

| `0x5ab130` | `unit_tile_list_walk(x, y)` — walks the `+50` prev/next chain, **exits only on a NEGATIVE link** | **H (machine)** | loop 0x5ab223-37 = `movsx eax,cx` / `lea edx,[eax+eax*2]` / `lea ecx,[eax+edx*4]` (= 13·i = the 52-B unit stride) / `mov cx,[ecx*4+0x9332aa]` (unit+50) / `test cx,cx` / `jge 0x5ab223`; reached 0x5ab333 ← `FUN_005a5a80` (`unit_restack`) ← `FUN_004bf1e0`. A self-linked record (`unit[i]+50 == i`, left by the sentinel+compaction removal in `0x5ab240`) makes it spin forever: observed 2026-10-24 on unit 113 with the game pegged ~60% CPU and `turn_flags` 0x10002 stuck; poking the link to 0xffff cleared the flag at once (`evidence/m53p_livelock_findings.md`). |
| `0x5a6330` | `unit_stack_relay(unit)` — walks the `+48` chain with the same negative-sentinel exit | M (machine) | loop 0x5a6945-55 = same 13·index math + `movsx esi,[eax*4+0x9332a8]` (unit+48) + `test esi,esi` / `jge 0x5a637b`; the SECOND spin site once `0x5ab130`'s chain was fixed (same unit 113, same 0xFFFF poke). Tile-list links are INDEX values (`0x5ab320` writes `+50=0xffff`, `+48=FUN_005ab130(x,y)`), so any stale/self link is fatal to both walks. |
| `0x8f0ccc` + `DAT_008f0d30` | **PER-VISIT REBUILD STATE**: 21-dword per-step table + the blocked-step mask the scan pool is built from | **H (machine + live)** | `FUN_004e63b0` (FIRST call of `FUN_004e78e0`, 0x4e78e9) writes entries with flag values 0/1/2/4/8 (0x4e63e8, 0x4e6442, 0x4e6518, 0x4e6533, 0x4e6563, 0x4e659f, 0x4e6635), then 0x4e6925-0x4e694f sets `DAT_008f0d30 = {bit i : table[i] != 0}` (live {0:0xc,8:0x8} → 0x101); entry filter 0x4e796a-72 clears those steps from `base+0x78` and 0x4e8b19 stores the scanned mask back ⇒ both are per-base volatile, valid after a round only for the base in `DAT_0068cbb0` (`evidence/m53p_mask_findings.md`). |
| **`0x4e63b0`** | **SCAN-POOL BUILDER** `build_scan_table()` — fills the 21-dword per-step table `0x8f0ccc` for ONE base (from `*(0x8f0d60)`), then builds `DAT_008f0d30` itself | **H (machine, M53Q2)** | zero args (call 0x4e78e9); 9 stores `[reg+0x8f0ccc]` with reg = 4*step: 0x4e6442/0x4e6518 `=2` (off-map / not visible), 0x4e6533 `=0` (scannable), 0x4e6563 `=4` (terrain), 0x4e659f + 0x4e6635 `or 8` (unit order), 0x4e6699 `or 0x20` (foreign presence), 0x4e68de RMW `or al,0x10` (another base's step); 0x4e63e8 `=1` is DEAD (guarded `cmp ecx,0x54 / jl`, index >= 21 only). Mask build 0x4e6925-0x4e694f (`cmp eax,0x8f0d20`) with `ret` at **0x4e6959** ⇒ the mask is built AFTER both passes. `evidence/m53q_verify.md`. |

## M56 block (session 92, 2026-10-25) — the production gate settled by a controlled poke

| item | finding | conf | evidence |
|---|---|---|---|
| **THE PRODUCTION GATE = mineral storage `base+0x40`** | the queue processor `0x4ef6d0` (pipeline stage 6 of `0x4f5a70`, shard_012.c:24182) creates the unit record with `FUN_005ab650` at shard_012.c:20890 — the call sits AFTER the debit `*(int*)(DAT_008f0d60+0x20) -= iVar3*iVar4` (`+0x20` aliases `base+0x40`) and after the in-mask clamp, and is followed by `DAT_008f0d60[1] + 0x4c = *(DAT_008f0d60 + 0x20)` (the `+0x20` alias of `base+0x4c` = the pending count). Gate order: pending>0 ∧ head is an item ∧ **storage ≥ price** (`0x4f0a3d cmp minerals, edi; jl → return`, M53k correction) → pay `0x4f0ca6` → clamp B → POP `0x4ef5d0` (pending −1, queue left-shift, `faction[head]−1` at `0x94dc84`) → unit created on the base tile. **Price = `0x4e40a0(owner,1,−1)` × type_cost `+41` = 10 × cost for in-mask owners** (M52b/M53l). The per-round chain: upkeep `0x5208f0(p)` → `0x520540(p)` (shard_013.c:11659) → the per-owner base loop (`*pbVar8 == param_1`, shard_013.c:11568) → `0x4f5a70(base)` → `0x4ef6d0` — **runs for every base every round in solo; there is no separate "production phase" gate** (the `faction+0x104 & 2` gate at `0x521070` guards only the AI upkeep step `0x574370`) | **H (machine + live controlled poke)** | `evidence/trace_m56_build_20261025_201353.jsonl`; `scripts/test_m56_predict.py` 8/8 |
| **`base+0x3c` progress / `base+0xcc` rate do NOT gate production** | controlled poke: base 17 Korolev Center (29,42), fac 3, net income `+0xd0` = 0, rate `+0xcc` = 1, progress `+0x3c` = 32, minerals poked 0→100, pending 0→1, head −38→2 (Scout Patrol, cost +41 = 1 → price 10). At the NEXT boundary (2223→2224): a Scout Patrol record appeared on the base tile (net +1 of (29,42,type2,fac3)), pending 1→0, queue left-shifted, minerals 100→0 (the −100 is the pay −10 then **clamp B `max(0,min(10,d0))` = 0** re-capping storage, M53k §D — not a 100-cost). An accumulation model (cost ≤ progress+rate) would have predicted NO arrival at progress 32 with income 0; the storage model predicted it exactly | **H (live, one variable changed: the queue+storage poke)** | same trace; `m53k_findings.md` §D line 87 ("clamp B … = 0 at any completion. Minerals stay 0") |
| **WHY NOTHING GETS BUILT (the M55 contradiction, resolved)** | natural state read before any poke: **pending = 0 with head −38 (`0xffffffda` = empty) on ALL 28 bases**, and every base's net income `+0xd0` = 0 (mineral pipeline empty) — the gate can never fire. Session 91's "zero production in ~7 boundaries" was a **false negative**: it counted only OUR-side net-new order-0 arrivals; the M56 runs observed enemy-side order-0 arrivals on enemy base tiles in EVERY boundary (e.g. (20,24) fac 2 type 1 at 2223, base 22 fac 6 at 2226, base 24 fac 7, base 14 fac 2 at 2228) — session 90's "produced units arrive order 0 on base tiles" was RIGHT. Enemy-side queue reads sit outside their AI turn (queues refill inside it), so enemy predictions are reported, not floored (M55 #5 confounding stands) | **H (live ×4 runs)** | `evidence/trace_m56_build_20261025_200917.jsonl`, `..._201137.jsonl`, `..._201353.jsonl` |
| **the support cliff** | a produced unit with no mineral income is DISBANDED by upkeep: Operations Director popup "The minerals output of Korolev Center is not sufficient to support Scout Patrol unit. The unit has been disbanded." (our units 7→3 across the rounds at 2221-2222 while the queue produced every round) | **H (popup read + census deltas)** | `evidence/m56/stuck_2220.png`; census 2220 (7 units incl. two produced order 0) → 2222 (6) → 2223+ (3) |
| **the actionable-unit freeze after production** | a produced unit arrives order 0; the auto-end gate does NOT fire while an actionable unit exists and the cursor parks on it — `cur_player` sits at 3, `turn_flags` 0, Return every 2 s for 150 s does nothing; ONE `h` on the cursor unit (→ HOLD) closed the turn at once (`turn_flags 0→2`, `cur_player 3→6`). The Operations Director popup's DEFAULT row is "Zoom to Base Control" — Return CYCLES its options instead of closing it (that froze run r1 twice); clicking OK (window coords ≈ (630,247)) dismisses it | **H (live)** | `evidence/m56/stuck_2222.png`, traces `..._200529.jsonl`, `..._200917.jsonl` (Escape on the map raised the quit prompt again — `evidence/m56/quit_prompt_2220.png`) |

## M57-4 block (session 96, 2026-10-26) — EVERY store to `base+0x40` in one visit, enumerated by breakpoint (the M56 price conflict, resolved in favour of M53b)

| item | finding | conf | evidence |
|---|---|---|---|
| **the visit unit is `FUN_004f5a70(base_index)`; its marker is `0x4f5a99`** | single caller `FUN_00520540` (0x4f5adc). `lea eax,[ebx+ebx*8]; lea eax,[ebx+eax*2]; shl eax,4` = index*304, `lea ecx,[eax+0x95da10]`, and at 0x4f5a99 `mov DWORD PTR ds:0x8f0d60,ecx` — so at that instruction `$ecx` IS the record address and it is the only per-visit marker that does not depend on which branch the visit takes. It then calls 0x4e8d60, 0x4e78e0, 0x4e92c0, 0x4e93f0, 0x4eaa10, **0x4ef6d0**, 0x4f26e0 | **H (disasm + live: 3 markers = 3 visits)** | `evidence/m574c.gdblog` VISIT#1-3 |
| **the store census for `+0x40` is COMPLETE at 23 sites** | `objdump -d -M intel --section=.text`: 65 stores to a `[reg+0x40]` operand in `.text`, in 45 functions; mapped through `ghidra_out/index.csv` and kept only where the function is call-graph reachable (depth 4) from 0x4f5a70 / 0x417ee0 / 0x4f6030 -> 23 sites, table baked in `scripts/m57_stores.py` (`--sites` prints it). The pointer-arithmetic shape was censused too: all 12 `lea reg,[reg2+0x40]` in the image are stack locals (`[esp+0x40]`) or have NO store through the resulting register | **H (whole-image census)** | `scripts/m57_stores.py` SITES table |
| **in a visit only TWO sites ever move our storage** | `0x4ef7f6` ADD (`edx = [eax+0x40] + [eax+0xd0]`, gated 0x4ef7db-0x4ef7f9) and `0x4efedd` PAY (`esi = [ecx+0x40] - edi`, ecx = `DAT_0x8f0d60`). Measured 2026-10-26, Korolev Center: 7->9, 9->0 (pending 1->0 in the same visit), 0->1, 1->2 — 4 stores, 3 boundaries, and replaying those stores from the run-start value reproduces EVERY value the 2 ms sampler saw (sums 0/-7/+1/+1 == observed nets). The clamp stores 0x4eff20 / 0x4f0ce9 (which store `max(0, min([0x92a370], d0))` only when storage > that limit) and 0x4f2d7d (`FUN_004f26e0`, a division-based distribution) never fired for our base | **H (live read-back at the sites)** | `evidence/trace_m574c.jsonl`, `evidence/m574c.gdblog` |
| **THE COMPLETION GATE IS `cmp [curbase+0x40], edi ; jge` AT `0x4efa5e`** | the head slot is read at 0x4efa2c (`ebx = [eax+0x50]`), the cost comes back from `call 0x4e40a0` (0x4efa3c, args pushed at 0x4efa34-0x4efa38: `-1`, `1`, the faction), `edi = eax` at 0x4efa4b, then `call 0x5ac950` (0x4efa4d) and **`imul edi, eax` at 0x4efa52** — i.e. exactly M53b's `price = 0x4e40a0 × +41`. `edi` is then BOTH the gate value and the amount the pay deducts | **H (disasm + edi measured 9 twice)** | `evidence/m574b.gdblog` (10->1), `evidence/m574c.gdblog` (9->0) |
| **the M56 model's `price 10` is the RETRACTED M48d number, and it is what breaks the M56 gate** | `m56_build.py --ui-queued 17 --boundaries 10 --timeout 300` (queue filled by the BUILD UI, `memory writes: 0`, start minerals 2): `FAIL production prediction accounting`, `0/0 POSITIVE predictions verified`, arrival at minerals 8 (8 + income 1 = 9 >= the measured 9) while the gate asserted "queue held — minerals 8 vs price 10". M48d already retracted "Scout Patrol cost 10" ("10 was our base index"); the M56 model kept the constant. The floors are fine — the constant is not | **H (live, floors intact)** | `evidence/trace_m56_build_20261026_133041.jsonl` |
| **`gdb -batch` cannot single-step inside a breakpoint commands list** | the first hit printed the step location then `[Inferior 1 (process ...) detached]` and the watch ended after one store. For a plain `mov [reg+0x40],src` the source operand IS the after value; the memory sampler is what proves it. Also: `set print frame-quiet` is not a command in this gdb and aborts the whole command file | **H (live)** | session 96 notes |
| **the base array reorders DURING a watch** | Korolev Center walked index 18 -> 17 (0x95ef70 -> 0x95ee40) inside one run; from then on the baked address held another faction's record (storage 19, head −27) while ours kept playing elsewhere. Verify the NAME at the address every sample and end the watch at the move | **H (live)** | `evidence/trace_m574b.jsonl` samples at t=35.5/35.7 |

## M60 block (session 99, 2026-10-26) — the create guard is a GLOBAL (`0x8f0d70`), the chooser is `0x4f6030`, and `DAT_008f0d60` is a `short *`

| item | finding | conf | evidence |
|---|---|---|---|
| **`0x8f0d70` = CREATE GUARD (process global)** | `4eff32: a1 70 0d 8f 00 mov eax,ds:0x8f0d70` / `4eff37: 85 c0` / `4eff39: 75 21 jne 0x4eff5c` — nonzero skips `call 0x5ab650` at 0x4eff4e. `grep -c 0x8f0d70` over the whole `.text` dump = 1 (this read); no instruction writes it. HW watchpoint: `guard_writes: 0`, `writers: {}`, 53 visits, value 0 at every visit. **POKE, one variable, University control:** guard 1 -> Korolev still pays (9 -> 0) and NO unit arrives (our units 10 -> 10); guard 0 -> pays and the unit arrives (10 -> 11). The old note "guarded by `[base+0x10] == 0`" is RETRACTED: base `+0x10` holds 0x4b000000 / 0x55000000 on our two bases | **H (disasm + watchpoint + poke/read-back)** | `scripts/m60_guard.py --stage watch`, `evidence/m60w_watch.gdblog`, session 99 notes |
| **`0x4f6030` = production CHOOSER (what a base builds next)** | 30,475 B, 4727 pseudocode lines (`shard_012.c:24338-29064`), one `return pbVar10`. Keeps the MINIMUM score against `local_124[0]` seeded `0xf423f` (999999), tie-broken by a secondary key; score = cost × ~25 halve/double heuristics incl. the affordability reshape through `0x4e4450` × `0x5ac950` × `0x4e40a0` (0x4fb271-0x4fb2c9). Candidate REJECTED unless `[base+0x38]` carries the bits its category needs — switch on `record[+0x32]`: 0->0x200, 1->0x1000, 2/3->0x1000 (0x400000 if `[base+0x38] & 0x1000` clear or `record[+0x2c] != 0`), 4->0x2000, 5->0x800, 6->0x400, 7/10->0x800000, 8->0x20000, 9->0x8000, 0xb->0x100000, +0x80000 for types >= 0x40 whose `record[+0x38] & 4` is clear; gate runs only for owners in `0x985b10`. Fallback 0x4fd6a0-0x4fd6e5 scans the 512 type records at `0x98ad80` stride `0x34` (end `0x9915b2`) for `0x5a73f0`-buildable, category 1/2/3, `record[+0x38] & 4`, lowest `record[+0x31]`. Live: Korolev `[base+0x38] = 0x00dfbe41` carries 0x1000, so Scout Patrol (cat 3) passes | **H (pseudocode + disasm + live plan dword)** | `shard_012.c:27401-27470`, `29027-29054`, `scripts/m60_guard.py --stage read` |
| **`DAT_008f0d60` is a `short *` to the base record being visited — DOUBLE every offset Ghidra prints through it** | written as `&DAT_0095da10 + idx*0x98` (shorts = `idx*0x130` bytes) in `0x4e3470`, `0x4e47d0`, twice in `0x4ef6d0`, twice in `0x4f5a70`; 929 references in `.text`, all loads of the value except the pointer stores. So pseudocode `+0x1c` = byte **+0x38** (proved: `4fb293 mov ecx,ds:0x8f0d60` / `4fb299 test DWORD PTR [ecx+0x38],0x80000000`), `+0x20` = `+0x40` storage, `DAT_008f0d60[0]/[1]` = the x/y words at `+0x0/+0x2`. This mis-typing is what produced the retracted `[base+0x10]` guard note | **H (disasm + Ghidra type)** | `scratch/m574/text.txt` at 0x4fb293, session 99 notes |
| **a boundary read can be EARLY: production lands while the player walk comes home, not at the flip** | after `smac_play --turns 1` printed 2189->2190, Korolev held the poked 9 minerals with `+0x3c` unmoved and `cur_player 7`, and a 100 s poll changed nothing; the pay + create landed later in the same round (minerals 0, our units 10 -> 11, `cur_player 3`). `m56_build` closes each window on `cur_player` coming home, so its windows are valid; the store tracer only looked causal because it waits | **H (live, polled)** | `evidence/m60c.gdblog`, `evidence/m60d.gdblog`, session 99 notes |

## M62 block (session 101, 2026-10-26) — OPEN CONFLICTS, tagged so a session can find them

These lines start with `CONFLICT:` on purpose: `scripts/session_brief.py` prints every one of
them, so an unresolved disagreement is visible at the start of a session instead of buried in
prose. Delete a line only when a measurement settles it, and move the answer into the table.

CONFLICT: year store — the M59/M60 notes and the skill say `0x51f554`; the instruction bytes are
`0x51f54f` (`a3 00 5b 98`, immediately after the round store `0x51f53c`), and `0x51f554` is the
`call 0x478530` AFTER the store. Bytes win: `evidence/m61a_watch.gdblog`.
CONFLICT: pay site — `0x4f0ca6` (the NAMED "completion path", branch still unread) vs `0x4efedd`
(measured live: `before 9 edi 9 after 0`, immediately before the create at `0x4eff4e`). For the
UI-queued shape `0x4efedd` is the pay; the other branch is unexamined, not refuted.

### MEASURED (M62): a queue slot is NOT reliably a type id

Every trace in `evidence/` re-read: **38 of 303** of our-base rows and **2804** rows overall carry
a slot value outside `0..23` (`-41`, `-3`, `-8`, `65`, `132`, `384`, `386`, ...). So no reader may
assume `[base+0x50+4k]` is a type id, and no check may demand it globally — a hard floor there
would fail on the AI bases in every run. The observed case that matters:
`evidence/trace_m56_build_20261026_165917.jsonl` r3 shows University `pending 1 -> 0` with the
slot array unchanged (`[2,2,0,0]` before and after), and r4 shows two bases' head slots reading
`384`/`386` while Korolev reads `2` — a garbage head still reached the bookkeeping comparison and
was reported as a "queue held" failure. Open: what writes 384/386 into `+0x50`, and whether the pop
shifts at all (M61's observation repeats here: pending decrements, slots do not move).

## M66 block (session 106, 2026-10-26) — the queue's shape, measured by watching the BUILD UI write it

Four live enqueues through the game's own INSERT (no queue poke in any of them; the only writes are
the M57 recipe's three enabling pokes), each read back after every click
(`scripts/m66_insert_slot.py`; traces `evidence/m66_insert_slot_run1_korolev.jsonl`,
`evidence/m66_insert_slot_university.jsonl`, `evidence/m66_insert_slot_third_fourth.jsonl`,
`evidence/m66_insert_slot_cost_order.jsonl`; the scorer is pinned by
`python3 scripts/test_m66_layouts.py` -> `PASS 10/10 m66-layout cases`).

| name | address / rule | conf | evidence |
|---|---|---|---|
| **the queue REGION is `base+0x54 ..`** — queued entry `k` (for `k = 1 .. pending`) lives at `base+0x50 + 4k`; `pending` (`base+0x4c`) is the count of the region | H (four enqueues, read back after each INSERT) | `evidence/m66_insert_slot_cost_order.jsonl:6-7`, `evidence/m66_insert_slot_third_fourth.jsonl:6-7` |
| **INSERT does not write a slot index, it INSERTS** — the item goes at the first region slot whose type-record byte is STRICTLY below the new item's, else after the region (`pending + 1`); everything from that slot rightward shifts one slot; equal-value entries stay ahead of the newcomer. **M66 named the byte COST `+41`; M67 refuted that live — it is the PLAN byte `+42`** (the cost/plan confound is M66's own note; the first item whose cost order and plan order disagreed landed on the plan side, twice) | H (live) | `evidence/m66_insert_slot_cost_order.jsonl:6-7`, `evidence/m66_insert_slot_third_fourth.jsonl:6`; corrected by `evidence/m67_sort_key.jsonl:6`, `evidence/m67_sort_key_accept.jsonl:6` |
| **`base+0x50` (the head slot) is not a queued entry and INSERT never writes it** — it read 2 in all four runs, before and after; the pop consumes it (`0x4ef5d0`, M63's branch) and something else refreshes it (OPEN) | H (read back 8x) | `evidence/m66_insert_slot_university.jsonl:1,6,7`, `evidence/m66_insert_slot_cost_order.jsonl:1,6,7,8` |
| **the per-faction QUEUED count is the byte array `0x94de84 + 0x20bc*owner + type_id`** — the UI enqueue adds 1 per item of that type (settled state, read after OK), the pop subtracts 1 (`0x4ef613`, M63's branch). The sibling `0x94dc84` (512 B lower, same stride) was NOT touched by any enqueue, at its own indexing; it is a different counter (what it counts is OPEN; it is incremented at `0x4d2a25`/`0x4d2fa7`). This closes the M62 CONFLICT line, which is now deleted | H (two runs, whole-row diffs before -> after OK) | `evidence/m66_insert_slot_cost_order.jsonl:10`, `evidence/m66_insert_slot_run1_korolev.jsonl:8` |
| mid-click the whole row reads one LOWER for every queued id and by OK it is back with the new id added — read the SETTLED state, not the click instant | H | `evidence/m66_insert_slot_cost_order.jsonl:6` vs `:10` |
| **the chooser's candidate array `DAT_009267e4` re-sorts between reads** (`0x596000` rebuilds all 128 entries per paint): the same box read `[192,194,193,2,0,1,195,...]` before the chooser opened and `[192,195,194,193,2,0,1]` with it open. The id the game stored always equalled the entry at the CLICKED cell read AT CLICK TIME (no +1 shift), so a cell -> id map is only valid for the frame it was read from | H | `evidence/m66_insert_slot_cost_order.jsonl:6` (`cand_at_click`, `cell_entry`), `evidence/m66_insert_slot_run1_korolev.jsonl:2` |
| enqueue dispatch `FUN_00417ee0` (size 7459, `shard_001.c:8941`): pending is incremented at `0x418b0a-0x418b0b` with a CAP of 9 (`0x418b05 cmp ecx,0x9 / jge`), the slot at index = the new pending is read at `0x418b32` (`mov eax,[eax+esi*4+0x50]`) and pushed with the buffer `0x689974` into `0x62732a`, and the head store `mov [edx+0x50],eax` at `0x418b57` is gated on `esi == 0` (`0x418b46 test esi,esi / jne 0x418c39`) — which cannot happen after the increment, and did not fire in any of the four enqueues. STATIC: read from `scratch/m574/text.txt`, never poked, and which branch INSERT actually takes is still unassigned | M | disasm window `0x418ad0-0x418b74` |

CONFLICT: type names — the live `+0` strings of the faction-3 designed records now read 192
`Impact Squad`, 193 `Synthmetal Garrison`, 194 `Impact Infantry`, 195 `Impact Battery`; the M33-era
row above says 193 `Scout Rover`, 194 `Synthmetal Garrison`, 195 `Laser Squad`. Read 2026-10-26 from
`0x98ad88 + type*52`; nobody has established which read was right or whether the names are
per-save, so do not quote either list as the name of an id.

## M67 block (session 107, 2026-10-26) — the queue's SORT KEY is the plan byte `+42`, not the cost byte

Three live two-item enqueues through the game's own INSERT, queue read back after every click
(`scripts/m66_insert_slot.py --rules sort_key --slots 12`): University Base pending 6->7->8
(`evidence/m67_sort_key.jsonl`), Korolev Center 2->3->4 (`evidence/m67_sort_key_korolev.jsonl`),
and the acceptance Korolev Center 4->5->6 (`evidence/m67_sort_key_accept.jsonl`, which prints
`PASS: exactly one sort-key rule explains both read-backs — plan_desc_after`).  EIGHT rules were
written down before the first run — cost `+41` or plan `+42`, each descending/ascending with ties
after/before — they share the insert machinery and differ only in the key, and the script computes
all eight predictions from the BASELINE before clicking and refuses a shape where they all agree.
`python3 scripts/test_m67_sort_keys.py` -> `PASS 15/15 m67 sort-key cases`.

| name | address / rule | conf | evidence |
|---|---|---|---|
| **INSERT sorts by the type-record PLAN byte `0x98ad88 + type*52 + 42` DESCENDING, ties after** — the item goes at the first region slot whose plan byte is STRICTLY below its own, else after the region (`pending + 1`); equal-plan entries stay ahead of the newcomer | **H (live, three runs; PASS on one real invocation)** | University: 193 (plan 2, cost 2) went to region slot 1 IN FRONT of two 194s (plan 1, cost 3) while `cost_desc_after` predicted 7 (`m67_sort_key.jsonl:6` + its `shape_gate` row); Korolev acceptance: 193 went to slot 2 in front of 194 (plan 1) while `cost_desc_after` predicted 5, and 192 (plan 0) went behind 195 (plan 0), ties staying ahead (`m67_sort_key_accept.jsonl:6-7`) |
| **CORRECTION to the M66 row above: the key is NOT the cost byte `+41`.** M66's four runs could not separate the two bytes — the ids they measured order the same way by cost and by plan, which M66 wrote down as a confound. The first items whose cost order and plan order DISAGREED landed on the plan side, in both bases | H (live) | the two rows above; M66's own confound note in `SESSION_NOTES.md` session 106 |
| **the INSERT shift is capped to the 10-slot queue array `base+0x50 .. base+0x74`** (head + 9 region slots — the same 9 the enqueue cap at `0x418b05` refuses to exceed): stale ids inside the array are pushed ALONG with the shift, the value in slot 9 is pushed out of the array, and the dword at `base+0x78` (queue slot 10 — 9225 on University Base, 545 on Korolev Center) does NOT move. With an 8-slot window and a zero tail the capped and uncapped forms are indistinguishable, which is why M66 never saw the difference | H (four writes, each read back) | `m67_sort_key_korolev.jsonl:6-7` (the stale id 2 at slot 3 moved to 4, then to 5; slot 10 read 545 in every row before and after), `m67_sort_key.jsonl:6-7` (slots 1..8 shifted while slot 10 held 9225 throughout) |
| **scope of the claim**: this separates COST from PLAN. It does NOT separate `+42` from type-record bytes that happen to rank ids 192/193/194/195/2 the same way — several name bytes (`+0,+1,+3,+4,+6,+15,+16,+17,+18`), `+37`, and `+43` read ASCENDING all predict the same two landing slots. It DOES refute `+7, +9..+14, +33, +38, +41 (cost), +45, +48, +50, +51`. Separating plan from name-order needs an insert whose plan order and name order differ (e.g. id 1 Formers, plan 9, name `F`, against 194 Impact Infantry, plan 1, name `I`) | H (computed over the live records of the five involved ids) | the `shape_gate` and `score` rows of `evidence/m67_sort_key_accept.jsonl`; the type-record byte dump quoted in `SESSION_NOTES.md` session 107 |


## M68 block (session 108, 2026-10-26) — INSERT APPENDS at click time on a fresh queue; the plan-byte key is NOT re-earned

Run: `python3 scripts/m68_key_run.py --base-name "University Base" --items 2,1,194,192,193
--trace evidence/m68_key_run.jsonl` after `SMAC_SAVE='m54b_clean.SAV' python3
scripts/m54a_load.py --relaunch`, `python3 scripts/smac_play.py --turns 1 ... --tag m68t2`
and `python3 scripts/accept_ready.py`: year 2151 round 51 `cur_player 3`, University Base idx 0,
minerals 0, `+0xd0` 0, pending 0, head slot 2, region empty. Exit 1 — **no key claim, nothing
merged.** The instrument, its key-level gate and its 35 pinned cases are in
`scripts/m68_key_run.py` / `scripts/test_m68_key_rules.py`.

| name | address / rule | conf | evidence |
|---|---|---|---|
| **INSERT APPENDED all five items in click order** — click order 2, 1, 194, 192, 193 (plan bytes 3, 9, 1, 0, 2) wrote region slots 1, 2, 3, 4, 5. `plan_desc_after` (M67's finding) predicted 1, 1, 3, 4, 3; the writes are predicted by **55 of the 212 candidate rules** — every byte that is constant over these ids, plus `+45` and `+50`, whose values are monotone in click order — so a no-sort engine cannot be told from a byte key. Integrity was True: every click verified `guard == cell`, the clicked cell entry equalled the intended id, the stored id equalled it, and pending rose by exactly 1 per click | **H (live, one real invocation; the acceptance FAILED)** | `evidence/m68_key_run.jsonl:10-14` (the five read-backs), `:18` (the `score` row: `observed_landing [1,2,3,4,5]`, 55 matched rules, `integrity true`), `:5` (the `key_gate` row: only `+42` predicted 1,1,3,4,3, so the shape was accepted before any click) |
| **CONFLICT with the M67 block above: the same driver and the same INSERT button produced SORTED positions there and APPENDS here.** The runs differ in base (Korolev Center, and a University Base built up over 60 rounds, vs the save's University Base at round 51), in minerals (3 and 1 vs 0), in the queue's starting contents (pending 2/4/6 vs 0) and in the chooser's candidate list (4-7 entries vs 67 with filler), so **which** variable flips the behaviour is NOT established — quote neither as "INSERT sorts" without naming the state it was measured in. Do not "resolve" this by preferring the newer run: M67's three read-backs are real and unexplained by anything the driver has since measured | H (both sides measured live; the difference is confounded) | M67: `evidence/m67_sort_key.jsonl:6-7`, `evidence/m67_sort_key_korolev.jsonl:6-7`, `evidence/m67_sort_key_accept.jsonl:6-7`; M68: `evidence/m68_key_run.jsonl:10-14` |
| **the engine itself refuses to enqueue a type the queue already holds** — one INSERT of 193 into a queue already holding 193 left pending at 5 and every queue slot unchanged (no write, no error). The driver-side rule "never enqueue an id the queue already holds" is a GAME rule, not a caution | H (live, read back) | `evidence/m68_cellprobe_193.jsonl:4` |
| **the driver's chooser cell -> pixel mapping (5 columns, `(128+127*(cell%5), 60+100*(cell//5))`) is unreliable past the first row**: three probes clicked cell 6 (255,160) or cell 4 (636,60) and the chooser guard field stayed on the PREVIOUS selection, so INSERT did nothing; in the first acceptance run the same cell-6 click DID register (guard 6, cell entry 195) and the queue received **-3 (0xfffffffd)** instead of 195 — a queue entry with no type record, after which the next INSERT appended a plan-9 item at the END of the region. 195 is therefore not usable in a shape until the click mapping or the -3 is understood | H (four measurements, each read back) | `evidence/m68_cellprobe_195b.jsonl:3-4`, `evidence/m68_cellprobe_195c.jsonl:3-4`, `evidence/m68_cellprobe_0.jsonl:3-4`, `evidence/m68_key_run_attempt1.txt:12-13` |
| **STATIC: the capped shift is visible in the instruction bytes** — `0x418ab3-0x418acb` walks `eax` from `+0x74` down by 4 while `eax > 0x54`, copying `[base+eax]` to `[base+eax+4]`: slot 9's value is overwritten first (pushed out of the array), slots 1..8 move up one, and `+0x78` is never touched — M67's read model, now seen in the code. The same block sits next to the pending cap (`0x418b05 cmp ecx,0x9 / jge`, `0x418b0a inc`) and to `0x418b5f cmp DWORD PTR [eax+0x50],0xffffffd9` — a queue sentinel of **-39**, not the -38 the driver notes have been quoting | M (read from `scratch/m574/text.txt`, never poked) | disasm window `0x418ab3-0x418b74` |
| **the 212-rule candidate set and the key-level gate** — 52 offsets x descending/ascending x ties after/before plus four whole-name lexicographic rules; a rule's KEY is the offset it reads (None = the name string). The gate refuses a shape unless no OTHER key predicts the landing sequence under test; the verdict pays only if exactly one KEY explains every write (two conventions of one key = the tie direction went untested). Pinned: `python3 scripts/test_m68_key_rules.py` -> `PASS 35/35 m68 key-identifier cases`, including the three M67 read-backs, which fit **11, 17 and 15 rules across 4-6 different keys** — the quantified proof that M67's two-item shapes could not identify a byte | H (pinned offline against the measured records and the M67 traces) | `evidence/m68_typebytes.jsonl:11` (the live-record co-ordering measurement: on Korolev Center's pending-6 queue, 3 of 208 byte rules predict the same two slots as `+42 desc after`), `evidence/m68_key_run.jsonl:2` (the records the candidate set was built from) |


## M69 block (session 109, 2026-10-27) — the enqueue writes at the QUEUE WIDGET'S CURSOR; M67's "sort key" is the widget's list order, not an enqueue comparison. ACCEPTANCE PASS on one real invocation.

Run: `python3 scripts/m69_cursor_run.py --cursor 2 --item 193 --trace evidence/m69_cursor3.jsonl`
-> **PASS** (exit 0): `INSERT of id 193 wrote queue[2]=193 with the widget cursor poked to 2
(pending 2->3); the plan byte 2 would have put it at 1`. Region before `[2, 192, 194]`, after
`[2, 192, 193, 194]`, read back from `/proc/<pid>/mem`.

| name | address / rule | conf | evidence |
|---|---|---|---|
| **the INSERT writes `queue[pos] = item` where `pos = *(int *)(0x6a9480 + 0x3ff5c)` — the queue widget's CURSOR ROW** — `pos` comes from the widget object (`ecx` at `0x417dbf`), NOT from any type-record byte; the enqueue shifts slots `pos..9` up by one (`0x417dd3-0x417deb`), stores at `0x417e04` (`mov [eax+edx*4+0x50],ebx`), then bumps pending (capped 9) if `pos > pending` | **H (live + static: the store instruction is the one the hardware watchpoint caught)** | `evidence/m69_enqueue.gdblog` (`ENQUEUE obj=0x6a9480 pos=1 pending=2` -> `STORE queue[1]=192`; `ENQUEUE obj=0x6a9480 pos=4 pending=3` -> `STORE queue[4]=193` **in one click flow**), `evidence/m69_cursor3.jsonl` (the poked-cursor PASS) |
| **The consequence: there is NO sort in the enqueue, and M67's plan-descending finding is the WIDGET's list order.** One continuous click flow wrote at the FRONT (pos=1) and at the END (pos=4) because the widget moved its own cursor between clicks (`cursor_after=4` after a write at 2). So M67's "the item goes at the first slot whose plan byte is below its own" measured *where the widget's cursor happened to be*, which the widget derives from its own (plan-ordered) list. It is a real property of the LIST, not of the INSERT path | **H (live: two different indices from one flow; static: no comparison between the chooser click and the store)** | the two `ENQUEUE` rows in `evidence/m69_enqueue.gdblog`; `evidence/m69_cursor3.jsonl` (`wrote_at 2` while `plan_sorted_index 1`); the M68 appends (`evidence/m68_key_run.jsonl:10-14`) |
| **the controlled poke settles it**: with the cursor read back as `2`, one INSERT of 193 into region `[192 (plan 0), 194 (plan 1)]` wrote at slot **2**; the plan rule predicts **1**. The shape was refused by the instrument when the cursor and the plan index agreed (`--cursor 1` -> `FAIL: non-discriminating shape`), so the PASS is not a coin flip | **H (one real invocation, read back)** | `evidence/m69_cursor3.jsonl` (rows `plan`, `cursor_poked`, `insert`, `verdict`); `python3 scripts/test_m69_cursor.py` -> `PASS 15/15 m69 cursor cases` |
| **CORRECTION to the M68 block: a NEGATIVE queue value is the TYPE's, not a bad click.** With the click verified (`guard == cell == entry`) and the cursor poked, item **196** (a type with no real record: cost 0, plan 0, empty name) stored **-6** in the queue; item **195** stored **-3** earlier on a click whose guard read 6. Two different negatives, so it is not one sentinel: a type id with no valid record is stored as a negative value, and an INSERT of such a type is unusable in a shape (`-3` at slot 4 then `plan 9` appended at the end) | **H (two measurements, both with verified clicks)** | `evidence/m69_cursor2.jsonl` (`cell_click` guard 7 == cell, `insert` stored -6), `evidence/m68_key_run_attempt1.txt:12-13` (195 -> -3 with guard 6) |
| the instrument: `scripts/m69_enqueue_gdb.py --arm|--stop|--parse` attaches gdb to `terran.exe` (TracerPid/ptrace_scope guards), sets breakpoints at `0x417dbf` (cursor read), `0x417e04` (the store), `0x417dd3-0x417deb` shift, the old `0x418a99` dispatch (which the INSERT never reaches) and hardware watchpoints on slots 1..3, and drains to `evidence/m69_enqueue.gdblog` | M (tool) | `evidence/m69_enqueue.gdblog` |
| **the `0x418a99` dispatch is a DIFFERENT handler** (`cmp eax,3` + jump table `0x419c20`; case 0 writes `base+0x40`, case 1 shifts slots and bumps pending): it never fired in four INSERTs, so it is not the BUILD-pane enqueue — the M67 notes' assumption that the `0x418bxx` block is the insert path is superseded by `0x417d95-0x417e1e` | H (breakpoint armed on both, only the `0x417xxx` one fired) | `evidence/m69_enqueue.gdblog` (no `case0`/`case1` rows at all) |

## M70 block (session 110, 2026-10-27) — WHO WRITES THE QUEUE WIDGET'S CURSOR. ACCEPTANCE PASS on one real invocation.

Run: `python3 scripts/m70_cursor_watch.py --arm --base-name "University Base"` ->
`python3 scripts/m66_insert_slot.py --base-name "University Base" --item-a 193 --item-b 192
--slots 12 --trace /tmp/m70_flow.jsonl` -> `--stop` -> `--acceptance` -> **PASS** (exit 0):
4 cursor writes, all attributed, values `[1, 2, 3, 0]` each equal to the static model's
prediction; region `[2,0,0,...] -> [2,193,192,...]`, pending 0 -> 2.

| name | address / rule | conf | evidence |
|---|---|---|---|
| **the queue-LIST row click sets the cursor**: `cursor = min(clicked_row, [[0x8f0d60]+0x4c] + 1)` — read at `0x40aa22` (`mov eax,[edi+0x3ff5c]`), stored at **`0x40aae5`** (`mov [edi+0x3ff5c],eax`) inside `FUN_0040a990`; the second store `0x40aaeb`'s target is `+0x3ff60` (a different field) | **H (live watchpoint hit at 0x40aaeb = the instruction after the store + the static clamp at 0x40aad8-0x40aae5)** | `evidence/m70_cursor.gdblog:38` (`CURSORWRITE pc=0x40aaeb now=1` right after `ROWCLICK clicked=3 cursor_before=0 pending=0`); `evidence/m70_cursor_events.jsonl` |
| **the enqueue parks the cursor at rows+1 after an INSERT**: `eax = [[0x8f0d60]+0x4c]; inc eax; mov [ecx+0x3ff5c],eax` = `0x417e2d` / `0x417e3a` / **`0x417e3b`**, reached only from the inserting branch (`param_2 == 0` at `0x417e26`) | **H (live x2 + the bytes)** | `evidence/m70_cursor.gdblog:44,50` (`ENQTAIL_SET cursor_new=2 pending=1` -> `CURSORWRITE pc=0x417e41 now=2`; `cursor_new=3` -> `now=3`) |
| **a handler zeroes the cursor after sending widget message `0x4d00`**: `push 0x4d00; call 0x584010` (`0x4194a4`) with `eax = 0xffffffd9 - edi`, `edx = 0xffffffd9 - ecx` (the -39 sentinel), then **`0x4194b3`** `mov [ebx+0x3ff5c],0x0`, `push 1; call 0x4eb6b0` | H (live watchpoint hit; the caller/message id is NOT yet named) | `evidence/m70_cursor.gdblog:51` (`CURSORWRITE pc=0x4194bd now=0` — the last write, which is why the cursor read back 0 with pending 2) |
| **the cursor is clamped/advanced against the WIDGET'S OWN row count `[[0x8f0d60]+0x4c]`, not the base record's pending** — `DAT_008f0d60` is a POINTER to the base record (`0x40ad6c`, `0x40b00a`, `0x417d44` load it and index `+0x4c` / `+0x50+4k`); Ghidra flattens the deref | H (bytes at four sites + the live trace: tails printed 2 and 3 while the base's pending was 1 and 2 at those instants) | `evidence/m70_cursor.gdblog:43,49` vs the `STORE ... pending=` field of the same lines |
| **a list row IS a queue slot**: the same handler indexes `[[0x8f0d60] + 4*row + 0x54]` at `0x40b041-0x40b04c` (`lea eax,[edx*4+0x50]; mov edx,[eax+ecx+4]; mov [eax+ecx],edx`) — there is no separate row array to sort | H (bytes) | `scratch/m574/text.txt` 0x40b03e-0x40b04c |
| **the enqueue's shift starts at `min(9, max(pending+1, cursor))` and the store uses the ORIGINAL cursor** (the clamp at `0x417ddb` feeds only the `cmp` at `0x417e17`/`0x417df3`); `pending++` only when `pending < 9` | H (reproduces all four measured M69 transitions, offline) | `python3 scripts/test_m70_cursor.py` -> `PASS 23/23`; `evidence/m69_enqueue.gdblog:37-58` |
| **no paint rewrites the queue region**: in the armed window (arm -> 2 INSERTs -> OK -> Escape -> detach) the only writes to slots 1..3 were the two enqueue stores at `pc=0x417e08` | H (live, 4 hw watchpoints on slots 1..3 + the cursor field) | `evidence/m70_cursor.gdblog` (2 `SLOTnWRITE` lines only) |
| the instrument: `scripts/m70_cursor_watch.py --arm|--stop|--acceptance` — hw watchpoint on `*0x6e93dc` (the cursor field) + slots 1..3, breakpoints at `0x40aa22/0x40b02c/0x40b081/0x417dbf/0x417e04/0x417e3b/0x417e6b/0x417e7b` (4 hw + 8 bp is the ceiling), `attribute_store()` maps gdb's after-store pc back to the storing instruction (window 16 bytes) | M (tool) | `evidence/m70_cursor.gdblog`, `evidence/m70_cursor_events.jsonl` |
| **CONFLICT (not resolved): the negative-id table stride disagrees between sites.** `0x40ada8-0x40adae` and `0x4164ef-0x4164f5` compute `0x984d38 + (-v)*48`; `0x41890a-0x418914` and `0x418943-0x41894d` compute `0x984d38 + (-v)*16`. -3 -> `0x984dc8` or `0x9852b8`; -6 -> `0x984e58` or `0x985348` | reported, not resolved | `scratch/m574/text.txt` at those addresses; `test_m70_cursor.py` (the 48 form pinned, the 16 form named) |
| **CONFLICT (open): M67's plan-descending LIST order has no code behind it yet.** Zero sites read the plan byte `+42`: the only 52-byte type-address computations in .text are `0x40ad92`, `0x4164dd`, `0x4188f9`, `0x418932`, and each just pushes the record pointer into `FUN_00626634` / `FUN_006265a2` (the row's string builders; the negative branch pushes from the `0x984d38` table instead) | reported, not resolved | `scripts/m70_scan_writers.py`, `scripts/m70_type_sites.py` output (4 sites of 60 lea-base hits) |

## M71 block (session 111, 2026-10-27) — WHAT THE COMPLETION'S POP DOES TO THE QUEUE REGION AND TO THE CURSOR. ACCEPTANCE PASS on one real invocation, reproduced.

Runs: `python3 scripts/m71_pop_watch.py --boundaries 2 --tag m71pop` -> **PASS**; the same
command with `--tag m71pop3` on a reloaded save -> **PASS** (identical structure).
`--tag m71pop2` (a designed head) **FAILed its window gate** — no completion in the window —
and is reported below, not papered over. `python3 scripts/test_m71_pop.py` -> **PASS 34/34**
(both committed logs pass the acceptance; every negative fixture fails).

| name | address / rule | conf | evidence |
|---|---|---|---|
| **a completion pops EXACTLY ONE item when the new head validates as available** — pending 2 -> 1, region `[2,193,192,0...] -> [193,192,192,0...]` read back from `/proc/pid/mem` after detaching; the DRAIN candidate (`pending -> 0`, region `[192,192,192,...]`) predicts a different region and is refuted for this shape | **H (4 hw watchpoints + 10 breakpoints + memory read-back, twice)** | `evidence/m71pop.gdblog`, `evidence/m71pop3.gdblog`, `evidence/m71pop_seq.jsonl`, `evidence/m71pop3_seq.jsonl`, `test_m71_pop.py` |
| **the pop's shift writes `queue[k] = queue[k+1]` for k = 0..pending-1 ONLY** (store `0x4ef62c`, gdb reports `pc=0x4ef62e`); `queue[pending]` keeps its STALE value — the duplicated 192 at slot 2 in the read-back is that stale slot, not a second write (exactly ONE `SLOT1WRITE` was logged while `POPCNT` printed `s0=193 s1=192 s2=192`) | **H (bytes + the watchpoint count)** | `scratch/m574/text.txt` 0x4ef622-0x4ef639; `evidence/m71pop.gdblog` (`SLOT1WRITE pc=0x4ef62e now=192`, `POPCNT newpend=1`) |
| **the drain loop stops at the validator, with the new head still IN the queue**: `POPRES head=193 r=1` then `POPEXIT` (the exit `0x4ef68b`). `0x5a73f0` returns 0 iff type-record `+0x30` bit 0 is clear (`test BYTE [id*52+0x98adb8],1` at `0x5a7402`) OR the owner-mask byte `+0x2c` lacks the faction bit (`0x5a7415-0x5a7426`); designed records read `+0x30` = 192:`0x0001` 193:`0x0041` 194:`0x0041`, `+0x2c` = 0 for all three | **H (bytes + live verdicts + live record bytes)** | `evidence/m71pop.gdblog` (`POPRES`/`POPEXIT`), record probe in session 111 notes |
| **the completion never touches the cursor field**: ZERO writes to `*0x6e93dc` across the whole armed window (arm -> 2 round boundaries -> detach), and the `0x4194b3` handler (M70's cursor-zeroer) did not fire. So the engine's completion neither moves the cursor nor reorders the region — it left-shifts it | **H (live, watchpoint armed the whole window, twice)** | `evidence/m71pop.gdblog`, `evidence/m71pop3.gdblog` (no `CURSORWRITE` line in either) |
| **the pay for a UI-queued BASE-TYPE head is `0x4efedd` with `edi` = the head's PRICE, not the sweep-entry index**: `PAYA base=0x95da10 storage=9 edi=9` (run 1) and `storage=10 edi=9` (run 3, after the round's `+1` add at `0x4ef7f6`) while the base's INDEX is 0. `PAYB 0x4f0ca1` never fired. The standing conflict's other site `0x4f0ca6` is still unexamined for this shape, not refuted | **H (live x2)** contradicts M49a's `edi` = index for this shape | `evidence/m71pop.gdblog`, `evidence/m71pop3.gdblog` (`PAYA`), NAMED M49a row |
| the queued-count dec is at the address the GAME itself computed: `lea ecx,[ecx+edx*4+0x94de84]` with `edx = 2095*owner` -> `0x9540ba` for owner 3, head 2; the byte read back at `POPAFT` (`0x4ef61c`) went 1 -> 0, and the after-snapshot `de84[2]` read 0 | **H (live read-back at the game's own address)** | `evidence/m71pop.gdblog` (`POPDEC`/`POPAFT`), `evidence/m71pop3.gdblog` |
| **OPEN, not explained: a DESIGNED head did not complete.** With head 193 (price 18) and minerals poked to 18 (read back), two boundaries gave ONE `VISIT` of the base (`min=18`) and NO `PAY`/`POP`/`CREATE`; at the end `+0x3c` = 5, `+0xcc` (rate) = 0, `+0x30` = `0x80007020`, `+0x98` = 18. Confounded (head id 2 vs 193, progress, rate) — no mechanism claimed. **SUPERSEDED by the M72 block (session 113): the visit wanted `edi` = 27, not `price_of`'s 18, so storage 18 bailed at `0x4efa63` — verified by the same state paying at 27** | reported, then resolved in M72 | `evidence/m71pop2.gdblog` (2 events), `evidence/m72gate4.gdblog`, `evidence/m72gate5.gdblog` |
| the instrument: `scripts/m71_pop_watch.py` — pokes minerals and READS BACK before attaching (pokes lie under a tracer), arms 4 hw watchpoints (`0x6e93dc` + slots 1..3) and 10 breakpoints (`0x4f5a93` visit, `0x4ef5e4/0x4ef61a/0x4ef61c/0x4ef642/0x4ef65d/0x4ef68b` pop, `0x4efed8`/`0x4f0ca1` both pays, `0x4eff4e` create), drives real boundaries itself, detaches, and scores 8 gates including `shift_predict` (K shifts are NOT "shift left by K": index k is written `pending-k` times) | M (tool) | `scripts/test_m71_pop.py` 34/34 |

## M72 block (session 113, 2026-10-27) — WHICH TEST SENDS THE VISIT HOME WITHOUT PAYING. ACCEPTANCE PASS on two real invocations that differ in ONE variable.

Runs: `python3 scripts/m72_gate_watch.py --base-name "University Base" --boundaries 2 --tag m72gate4`
-> **PASS** (storage 18, the visit turns around); the same state with `--poke-minerals 27
--boundaries 1 --tag m72gate5` -> **PASS** (storage 27, the visit pays and creates).
`python3 scripts/test_m72_gate.py` -> **PASS 21/21**. The armed base is head 193, pending 1
(`queue [193,192,192,...]`), produced by the engine itself: the pre-run poked minerals to 9 and
one `smac_play` boundary let the head-2 Scout complete and pop, leaving 193 on top
(`evidence/trace_m72prep_20261027_164023.jsonl`).

| name | address / rule | conf | evidence |
|---|---|---|---|
| **the turn-around for an unaffordable DESIGNED head is the unit path's own affordability test `0x4efa5e` (`cmp [base+0x40],edi`), whose bail is `0x4efa63`** -> the message pair `0x67164c/0x671644` -> the epilogue `0x4f0bfa`. Storage 18 with edi 27: `POSAFF` then `BAILAFF`, no pay, no create, head 193 -> 193 and pending 1 -> 1 read back | **H (live x4 across two windows: 2 VISIT/2 ENTRY/2 BAILAFF per 2 boundaries)** | `evidence/m72gate4.gdblog`, `evidence/m72gate4_seq.jsonl` |
| **`edi` there is 27 for head 193 while `m56_build.price_of` says 18** — so the M71 `m71pop2` FAIL (minerals poked to 18, no pay in two boundaries) is fully explained: the visit wanted 27. `edi` is the product of `FUN_004e40a0(owner,1,-1)` (`0x4efa3c`) and `FUN_005ac950(head, base, 0)` (`0x4efa4d`, `imul` at `0x4efa52`); the factor split is INFERRED, the product is MEASURED. M71's `edi=9` for base-type head 2 is the same product on the other side of `0x4ef88b`'s head test | **H (measured both sites, both runs); composition INFERRED** | `evidence/m72gate4.gdblog` (`POSAFF storage=18 edi=27`), `evidence/m71pop.gdblog` (`PAYA storage=9 edi=9`) |
| **the discriminator: one variable, opposite outcomes.** Same base, same head, same window shape — storage **18** -> `POSAFF` -> `BAILAFF` (nothing paid, queue untouched); storage **27** -> `POSAFF` -> `CMP40 ebx=193` -> `PAYA storage=27 edi=27` -> `CREATE id=193 arg3=3`, storage read back 0, head 192, pending 0 | **H (two real invocations, A/B on storage alone)** | `evidence/m72gate4.gdblog`, `evidence/m72gate5.gdblog`, `evidence/m72gate5_seq.jsonl` |
| **`0x4efe41` (`cmp ebx,0x40`) is only reached when the special test fails** — `type+0x2a == 8`, `base+0x6 == 1`, `[base+0x30] & ...` all must hold at `0x4efae8-0x4efb09`; for head 193 the first test fails, so both the base-type (`jl 0x4efed1`) and the designed (`>= 0x40`, fallthrough) branch converge on the SAME pay `0x4efed8` with the same `edi` | H (live `CMP40 ebx=193 edi=27` + bytes) | `evidence/m72gate5.gdblog`; `scratch/m574/text.txt` 0x4efae8-0x4efe41 |
| **the visitor runs more than once per round boundary, and the repeats are the SAME test** — 2 boundaries produced 2 (once 3) `VISIT`/`ENTRY`/`POSAFF`/`BAILAFF` rows with identical operands; so "two BAILAFF rows" is not a confound, while two DIFFERENT turn-around kinds would be (the instrument's gate 4 says exactly that) | H (live, 3 windows) | `evidence/m72gate4.gdblog`; `scripts/test_m72_gate.py` cases 10b/10c |
| the facility (negative-head) path has THREE distinct no-pay exits, all armed and NONE exercised by a positive head: `0x4f0a42` (storage < edi at `0x4f0a3d`), `0x4f0b86` (`[ebp-0x30] <= 0`, i.e. `-head` not positive), `0x4f0c28` (`[esi+0xcc]+[esi+0x3c] >= f()*table` for another base already holding the same head) | armed, **not exercised** — no claim | `evidence/m72gate4.gdblog`, `evidence/m72gate5.gdblog` (no `GATE`/`BAILMIN`/`BAILDESC`/`BAILCNT` row) |
| the instrument: `scripts/m72_gate_watch.py` — 12 silent conditional breakpoints (`0x4ef6d0` entry, `0x4ef88e` head, `0x4efa5e`/`0x4efa63` unit affordability, `0x4efe41`, `0x4efed8` pay, `0x4eff4e` create, `0x4f0a3d`/`0x4f0a42`/`0x4f0b4f`/`0x4f0b86`/`0x4f0c28` facility path, `0x4f5a93` visit), each conditioned on the base pointer, pokes+reads back storage before attaching, drives real boundaries, detaches, then scores 8 gates over the parsed stream | M (tool) | `scripts/m72_gate_watch.py`, `scripts/test_m72_gate.py` |

## M73 block (session 114, 2026-10-27) — WHAT THE GATE'S `edi` IS MADE OF: `A x (cost + markup)`, with a live flag that switches the markup off. ACCEPTANCE PASS on one real invocation.

| name | value / rule | confidence | evidence |
|---|---|---|---|
| `edi` at `0x4efa5e` | `A x B`, `A = 0x4e40a0(owner,1,-1)`, `B = 0x5ac950(head,[0x68cbb0],0)` | measured (M72, M73) | `m73split4` |
| `A` | 9 on this save = Python `cost_multiplier(owner 3)` | measured, every visit | `FACTORA` rows |
| `B`, designed head | `byte(+0x29) + trunc_div(C*P+50, 100)`; `C = 0x595ad0(type)`, `P` = option dword | measured | `PRICE_C`/`PRICE_M`/`FACTORB` |
| `B`, head 194 | `C 3`, `P 50` -> markup 2 -> `B 5` -> `edi 45` (`price_of` 27) | measured | `evidence/m73split4.gdblog` |
| markup OFF | `type < 0x40` OR `type[+0x30] & 4` at `0x5ac99c` -> bare cost (`0x5aca9c`) | measured | `FLAG` rows 0x41 vs 0x45 |
| the flag | live STATE; 193 read `0x41` at arm, `0x45` at its first visit; 8/256 records set after the run | measured | `FLAG` rows + live reads |
| writers | `0x4eec30`, `0x4d20f0` (`|= 4` on a unit transformation) — NOT yet tied to the flip | static only | `shard_012.c` |

CONFLICT: `price_of` (the skill's M58 model) is `A x type_cost(+41)`; for a designed head above
`0x3f` with `+0x30` bit 2 clear the gate charges `A x (cost + 50% markup)` instead. The two agree
for head 2 and for any head whose bit 2 is set, which is why M72 measured 27 and this run 18 for
the same id.

## M74 block (RESOLVED session 116, PR — see M74-RESOLVED block below; this block = the s115 state)

`type[+0x30] & 4` is written by ELEVEN absolute-address sites in four functions
(`0x4eed18` in FUN_004eec30 guarded by `0x3f < param_2`; `0x573fed/0x574107/0x574117` in
FUN_00573a90; whole-word `= 1/0x105/0x115` at `0x595f82/0x595f91/0x595f9c` in FUN_00595b10;
`0x59d273/0x59d375/0x59d432/0x59db65` in FUN_0059ce10). M73's `0x4d20f0` only READS the field.
MEASURED, tag `m74flag2` (`evidence/m74flag2.gdblog`): at `0x4efa5e` head 194 read `f30=0x41
edi=45`, then in the same window `f30=0x45 edi=27` — the markup ON->OFF flip with the flag read
at `tid*0x34 + 0x98adb8`. Census `193/194: 0x41 -> 0x05`; `65/195` also gained bit 2 (confounded);
`pending 0 -> 0`, storage `200 -> 200` — no completion, so `when` is unproven. ZERO of the 11
writer breakpoints fired: the leading candidate was the whole-word sweep store
`0x597487 mov WORD PTR [eax+0x30],dx` in FUN_00596850 (stride-52 copy of a source table into
`+0x23..+0x30`, called only from FUN_00597ce0/FUN_00597ee0). Instrument
`scripts/m74_flag_watch.py`, tests 37/37. RETRACTED s116: that store writes the `0x93327a`
table from a stride-48 file buffer, save/load codec only — not the live `0x98ad88` table.

## M74-RESOLVED block (session 116, ACCEPTANCE PASS tag `m74flag3`)

WHO sets `type[+0x30] & 4`, WHEN: at PRODUCTION, inside FUN_004ef6d0 between the gate
`0x4efa5e` and pay `0x4efed8`. `0x4efe60 mov WORD PTR [esi+0x98adb8],ax` (after `cmp ebx,0x40`
skips non-designed; `mov ax,[rec]; or al,4; mov [rec],ax`) sets bit 2 on the produced designed
record; `[ebp-0x20]=(~old)&4`; already-marked records jump straight to pay (`je 0x4efed8`).
First production also calls FUN_00572800(tid) at `0x4efe7e`: stride-0x34 sweep, entry guard
`tid>=0x40 && !(flag&4)`, ORs `0x104` (bit 2 + temp marker bit 8) onto valid unmarked records
passing validator `0x5a6cd0` whose `+0x24/+0x25/+0x26` match the produced unit's (rank tables
`DAT_0092b950`/`0x92fd18`); FUN_004ef380 `0x4ef398 and BYTE [ebx+0x98adb9],0xfe` clears the
marker. LIVE (`evidence/m74flag3.gdblog`, 4 hw watchpoints on flag words): 194 `0x41->0x45` pc
`0x4efe67` at its production (r52/53, after head 2 completed r51 and 194 popped); 193
`0x41->0x145->0x45` pcs `0x5729de`/`0x4ef39f`; 65/195 unchanged. Markup story: first production
charges M73's markup (bit clear at gate) then sets the bit; siblings pre-marked by the sweep skip
it from their first production. Setter evaded both grep shapes: read-modify-write through a
COPIED register (plain MOV with `0x98adb8` addend). Instrument `scripts/m74_flag_hw.py`.

## M75 block (session 117, ACCEPTANCE PASS tag `m75sweep1`) — WHAT THE PRODUCTION SWEEP MARKS: every valid UNMARKED designed record; the +0x24/25/26 triple does NOT gate designed marking.

| item | finding | grade | evidence |
|---|---|---|---|
| `FUN_00572800(tid,0)` sweep effect, LIVE | at first production of designed tid: stores `or WORD [rec+0x30],0x104` at `0x5729d5` on **192 AND 193** (both unmarked, valid, designed) and on NOTHING else; marked designed 64/128/129/130/131 skipped; alpha 0-13 skipped; produced 194 marked by production `0x4efe60` first, so the sweep skips it. 192's triple (00,02,00) FAILS the tier test vs 194's (00,02,01) (rank `0x92fd18[02][0]=03 > 194's byte 02`) yet 192 was stored -> s116's "byte-match" claim RETRACTED for designed candidates | **H (live watchpoints + census diff)** | `evidence/m75sweep1.gdblog` (`0x5729de` pcs = the 0x5729d5 ors), `m75sweep1_seq.jsonl`; `scripts/m75_sweep_replay.py` gates g1-g5 |
| tier tables | `0x92b950[+0x24]`, `0x92fd18[+0x25/+0x26]`: 16-BB rows, rank=row[0] signed >0 required, pass when produced byte >= rank; rows measured: 92b950 00->01 01->02 02->04 03->05 04->06 05->08; 92fd18 00->01 01->02 02->03 03->04 04->05 05->06. Only reachable for candidates < 0x40 after validator `0x5a6cd0` — UNTESTED live (zero alpha marks) | H (bytes) / OPEN (role) | s117 dump via `scratch/m75_fields.py` |
| `+0x24` = domain-row selector | picks the 144-B row at `0x92ae80+(v*0x90)` — same row as M73's markup C byte (`0x92ae81[+0x24*0x90]`) and the build-base land test (`==1`); sweep category gate compares these rows (designed-marked path only) | H | s117 dump + NAMED `0x4d1280` row |
| validator `0x5a6cd0(tid, shift)` | = `tid*0x14+0x92fdd4` dw0 >= 0 && bit `shift` of `0x985c1c[tech]`; in the sweep shift = produced record's +0x30 low byte (0x41 here); rejects all 14 alpha candidates this scenario | H (asm exact) | objdump `0x5a6cd0-0x5a6d36` |
| 0x100 marker residue | sweep ORs 0x104; `0x4ef398` cleared 193's bit 8 but 192 STILL reads 0x105 live after the run — clear scope unreconciled; the clear writes +0x31 (outside the watched low word) | OPEN | census diff `192:0x01->0x105` |

## M76 — WHO CLEARS THE 0x100 SWEEP MARKER, AND FOR WHICH RECORDS (RESOLVED, PR #77, acceptance `m76marker1`)

- The clear is `and BYTE PTR [ebx+0x98adb9],0xfe` at **0x4ef398**, the FIRST statement of
  FUN_004ef380(owner, tid): ebx = tid*52 (`0x4ef386-0x4ef392` = `[ebp+0xc]` *13 << 2), so it lands on
  the record PASSED IN; `[ebp+4]` is the caller's return address.
- Callers of 0x4ef380 (`grep 'call   0x4ef380'`): `0x4ef5ae` in FUN_004ef540(owner) (test `0x4ef597`,
  ret `0x4ef5b3`); `0x4f0626` in the production function FUN_004ef6d0 (test `0x4f060f`, ret
  `0x4f062b`); `0x521479` in FUN_00521070 (the upkeep pass — it clears INLINE first: `and bh,0xfe`
  `0x521452` + `mov WORD PTR [edi],bx` `0x52145e`); `0x5a8568` in FUN_005a7970. FUN_004ef540 itself
  is called only at `0x5a7d14`/`0x5a7f7b`, right after a FUN_00572800 sweep call.
- Both selectors walk the 128 slots `{0..63} U {owner*64..+63}` and call iff the flag WORD has
  bits 0, 2 and 8 (`flags & 0x105 == 0x105`).
- LIVE (`m54b_clean.SAV`, enqueue 194, storage 200, `scripts/m76_marker_clear.py`): the sweep marks
  192/193 at the FIRST production (`0x5729d5 or WORD [edi+0x98adb8],0x104`); the NEXT visit of the
  production function clears both (ret `0x4f062b`, owner 3); census 192:0x001->0x005, 193:0x041->0x045,
  194:0x041->0x045, word_mismatch=[] — the observed stores reproduce the flag words. Gates g1-g5 True.
- RETRACTED (M75): "192 keeps the 0x100 marker" was a snapshot artifact — the marker is transient and
  every carrier is cleared on the next pass. Marker setters outside the sweep: `0x4f05bd`, `0x5a7d00`,
  `0x5a7f67` (`or BYTE [...0x98adb9],1`) — 0 events here. `0x595f82/91/9c` printed tid 324/325 with
  `$esi/52`: esi there is not a type-record pointer.
- OPEN: which path reaches `0x4f05e2` without printing the setter at `0x4efe50`; what gates the pass
  (`DAT_00920434 == 0 || (bVar8 & DAT_00985b10) == 0`); the upkeep and tech passes never fired here.
Evidence: `evidence/m76marker1.gdblog`, `evidence/m76marker1_seq.jsonl`.

## M77 (session 119) — what reaches the production marker-clear pass, and its gate
- `0x4f05e2` (the 128-slot clear sweep in FUN_004ef6d0) is entered ONLY by fall-through from
  `0x4f05e0 xor esi,esi`; in-edges `je 0x4f05e0` `0x4f05d2` + fall-through `0x4f05de`
  (`test ds:0x985abc,0x100000`). Gate block `0x4f0591-0x4f05de`; `0x4f0599 je 0x4f0637` bails
  when `[ebp-0x20] == 0` (the pass is not reached at all).
- Gate operands: `DAT_00920434` (DWORD, `0x4f05a5`), `DAT_00985b10` low byte = a PER-PLAYER
  mask (`0x4f05af`), `[ebp-0x2c]` = `1 << BYTE [base+4]` (owner) built `0x4ef804-0x4ef815`,
  `DAT_00985abc & 0x100000` (`0x4f05d4`). Admit = `(0x920434==0 || !(mask & (1<<owner)))`;
  then sweep iff `!(mask & (1<<owner))` or `0x985abc & 0x100000`. ELSE
  (`0x920434!=0 && mask & (1<<owner)`) sets the marker `0x4f05bd or BYTE [rec+0x98adb9],1`
  and skips the sweep.
- LIVE (`scripts/m77_gate_trace.py`, tag `m77gate1`, PASS g1-g8): `0x920434=0`,
  `0x985b10=0x08` (owner 3 set; owners 1/2/5/6 clear), `0x985abc=0x003a7168` bit20=1.
  11 GATE visits, 10 bail on `[ebp-0x20]==0`; the one with `[ebp-0x20]=1` (owner 3,
  `[ebp-0x1c]=10088=194*52`) took ROUTEB→SWEEPIN, cleared 192 (0x105) and 193 (0x145), both
  end without 0x100. MARKSET 0 events while `0x920434==0` on every visit.
- `[ebp-0x20]` writers: `0x4efe6c` (`= 1` iff flag bit 2 was clear before the `or al,4` store =
  FIRST production of that record — the writer that admitted this sweep, printed `edx=1 tid=194`),
  `0x4ef8c0` (1, queue-head codes 34-37; 0 events here), `0x4ef8c9`/`0x4efed1` (0).
- RETRACTED (M76): "the clear pass fired on a visit that printed no production setter" — that
  instrument's PRODSET cond is `*(int *)0x8f0d60 == $b`, so it cannot print for another base.
Evidence: `evidence/m77gate1.gdblog`, `evidence/m77gate1_seq.jsonl`.

## M78 (session 120) — the 0x100 mark and its clear are in ONE production visit; the census that reads 0x105 is a mid-visit snapshot

- `python3 scripts/m78_mark_clear.py --tag m78order3 --boundaries 4 --no-reload` -> PASS (g1-g9).
  visit 36: PRODFLAG tid=194 pre=0x41 -> L20FLAG edx=1 -> SWEEPCALL owner=3 tid=194 mode=0
  ret=0x4efe83 -> MARK 192 (pre 0x001) + MARK 193 (pre 0x041) at `0x5729d5` -> GATE l20=1
  rec=10088 -> SWEEPIN `0x4f05e0` -> CLEAR 192 (pre 0x105) + CLEAR 193 (pre 0x145) at `0x4ef398`.
  Cross-visit mark->clear pairs = []; the only carrier census (boundary 1, 192=0x105 193=0x145)
  sits BETWEEN those stores, so it is a snapshot of a stopped engine, not a survivor. Census replay
  exact at all 4 boundaries (carriers [] / [192,193] / [] / []).
- Callers live: SWEEPCALL rets {0x4efe83 x1 tid 194; 0x574203 x4 = FUN_00573a90 on indices
  324/325/385/387, other owners, ZERO marks}; CLEAR rets {0x4f062b x2}. Zero events: 0x4ef5b3
  (FUN_004ef540), 0x52145e (upkeep inline clear), 0x5a7d00/0x5a7f67 (tech setters), MARKSET.
- Static call sites (`call`, instruction bytes): 0x572800 <- 0x4394be FUN_00438ad0, 0x4efe7e
  FUN_004ef6d0, 0x5741fe FUN_00573a90, 0x5a7d0e + 0x5a7f75 FUN_005a7970; 0x4ef380 <- 0x4ef5ae
  FUN_004ef540, 0x4f0626 production inline, 0x521479 FUN_00521070, 0x5a8568 FUN_005a7970.
- RETRACTED (M77 open (a)): "either another caller re-marks later, or the census races the pass" —
  nothing re-marks; THE CENSUS RACES THE PASS. Side fact: PRODFLAG/L20FLAG also fire at indices
  322/323, so the production loop walks past the 256-record array the census covers.
Evidence: `evidence/m78order3.gdblog`, `evidence/m78order3_seq.jsonl`.

## M79 block (s121, tag m79net5)

| addr | name / claim | evidence |
|---|---|---|
| `0x920434` | **NETGAME / MULTIPLAYER flag** (0 = single player) | H+LIVE: FUN_0057ecf0 sets 1 at entry, clears at its tail; 7 of 9 writers store right after `call 0x4e25e0`; FUN_00528930 returns 0 when it is 0; the production gate reads it at 0x4f05a5 and the poke to 1 (m79net5) moved the engine to the else branch 0x4f05ba-0x4f05c4 |
| `0x985b10` | **HUMAN-PLAYER MASK**, byte, keyed `1 << faction` (live 0x08 = player 3) | H, **current-player reading ruled out**: gate visits print cur_player (0x985dcc) 1/2/5/6 while the mask stays 0x08; sibling 0x985b11 = 0xff (all 8 slots); writers 0x4df82e/0x4e08ca/0x512bf6(imm 0x10)/0x525eed/0x57f051/0x57f2da; FUN_004df630 `= 1<<p`, `= 0x985b11 & 0xfe`; FUN_00525e10 clears `1 << *(rec+0x788)`; FUN_0057ecf0 builds it from the 412-byte array 0x91e494 (count 0x91e2d0, live 0) |
| `0x4f0591-0x4f0637` | production MARKER gate: admit iff `0x920434==0 \|\| !(0x985b10 & (1<<owner))`, ELSE `0x4f05bd or BYTE [tid*52+0x98adb9],1` and skip the clear pass | VERIFIED live m79net5: POKE pre 0 post 1, MARKSET tid 194, SWEEPIN/CLEAR 0, end census 192=0x105 193=0x145 194=0x145, replay exact 3/3 |

## M80 block (session 122, ACCEPTANCE PASS tag `m80band1`) — THE TYPE-RECORD ARRAY IS 8 FACTION BANDS OF 64; FUN_00573a90'S ARG 1 IS THE FACTION; INDICES >= 256 ARE LIVE DESIGN SLOTS

`0x98ad88` record array = **8 bands x 64 records x 52 B, band = faction**; a faction's designed
types fill `band_start..` contiguously (census `scripts/m80_band_census.py`: b0 0..13 Colony
Pod..Unity Foil, b1 64, b2 128..131, b3 192..194 ours, b4 256, b5 320..325, b6 384..386, b7
448..449; 387+ empty). FUN_00573a90: `esi = [ebp+8]` = **FACTION** (0x573aa3); counter `[ebp-0x18]`
0..0x80; index = `counter<0x40 ? counter : (counter&0x3f)+faction*64`; 0x574167-0x574176 rejects
unless `index/64 in {0, faction}`; record = `0x98ad88 + index*52` (0x57417e); 32 B copied INTO the
record at 0x5741e1 (`call 0x64c5e0`, len 0x20); 0x5741e9 clears record+0x1f; 0x5741f0
`and BYTE [rec+0x30],0xfd`; 0x5741fe `call FUN_00572800(faction, index, 0)` and that sweep's own
band base is `param_1*0xd00` = faction*64*52.
LIVE (`evidence/m80band1.gdblog`, 2 boundaries): SW573 fac=5 idx=324/325 (ebx=16848=324*52),
SWENTER owner=5 tid=324/325 mode=0, CLR4 pre=**0xc1** (bit 2 already clear → the `and ~4` is a
no-op on this path), MARKHIGH (0x5729d5, tid>=256) **0**; census 324/325 `0 -> 0xc1` and they now
read "Impact Squad"/"Impact Rover" — EMPTY at window start, created as the next two free slots
after 323. F573IN callers: ret 0x5749a7 x6, 0x574da9, 0x575424. **OPEN:** writer of `+0x30 = 0xc1`
(bits 0/6/7) — unattributed, no breakpoint between the 32 B copy and 0x5741f0; meaning of bits
6/7; the sweep's band-walk/mark guard `tid<0x40 || flags&4` never engages on a fresh record.

## M81 block (session 123, ACCEPTANCE FAIL tags `m81write1`/`m81write1b`, NOTHING MERGED)

`python3 scripts/m81_flag_writer.py --tag m81write1 --boundaries 2` then `--tag m81write1b --boundaries 3` (4 hw watchpoints on the flag WORDS 0x98ef88/0x98efbc/0x98eff0/0x98f024 = slots 324-327; silent bps 0x5741e1/0x5741f0/0x5741fe; storage poked 200 before each boundary; gates G1-G6). Result FAIL: FLAGW 0 events; run A armed 2 hw (slots 326/327 only) with all four slots EMPTY at baseline; run B armed 4 hw, baseline 324/325 = "Impact Squad"/"Impact Rover" flag 0xc1 (created between runs — a clean reload does NOT carry M80's live-created records), G1/G4 True, G2/G3/G5/G6 False.

ONE REAL EVENT (`evidence/m81write1b.gdblog`): `TAG0 idx=($ebx/52) esi=6 ebx=20020 f30=0x81` at 0x5741e1 — record 385 (20020/52, faction 6's band) reached the sweep's 32 B copy with its flag WORD ALREADY 0x81. The +0x30 bits are written BEFORE the sweep's create path (consistent with M80's CLR4 pre=0xc1); the writer is still UNNAMED. Census flags 324/325 0xc1 vs this live 0x81 on 385 — created-record flag values DISAGREE, do not assert one.

INSTRUMENT BUG (the blocker): a bp-command printf with `%.20s` fed `*(char *)(rec+0)` makes gdb error ("Cannot access memory at address 0x4c" — inferior pointer read as a host address), which ABORTS the batch script and detaches mid-window; later boundaries run uninstrumented while smac_play still exits 0. Next attempt: print idx/esi/ebx/f30 only (no name).

BOX FACT (why the brief's FIX cannot restore credit): base+0xd0 (`credit`) has only two writers in .text, 0x6310c6/0x631154 (`mov [obj+0xd0],param_1`, player-record init via `call [obj+0x90]`); income is never recomputed per round; University Base income 0 rate 0 vs 1-6 on all 17 other bases; accrual 0x4ef7f6 adds 0. Route: per-boundary storage poke 200.


## M81 (s124, `m81write4`) — WHO WRITES A CREATED RECORD'S `+0x30`, AND WHEN

`FUN_00573a90` writes it itself, in the visit BEFORE its own 32 B copy at 0x5741e1:
`0x5740f7 call 0x595b10` (the sweep forwards its six params) -> inside, `0x595f82
mov WORD PTR [esi+0x98adb8],0x1` RESETS the flags WORD to bit 0 (the same function also
holds `0x595f91 ...0x105` and `0x595f9c ...0x115`, so the 0x100 marker is an INIT-time
possibility); then the sweep ORs `0x574125 or BYTE PTR [ebx+0x98adb8],0x40` (bit 6, iff the
local `[ebp-0xc]` written at 0x573e9f from max(edi, movsx(al)) is != 0) and `0x57412c
or BYTE PTR [ebx+0x98adb8],0x80` (bit 7, unconditional on that path). Bit 2's ORs (0x574107
on `eax == -2`, 0x574117 on `DWORD [0x985aec] > 1`) did not run. LIVE (m81write4 PASS: 4 hw
watchpoints on the flag WORDS of slots 324-327, fresh m54b_clean reload (all four EMPTY at
baseline), 3 boundaries): FLAGW 324/325 pc 0x595f8b val 0x1 -> 0x57412c val 0x41 -> 0x574133
val 0xc1; SWCOPY idx 324/325 esi 5 f30 0xc1; read back 324 "Impact Squad" 0xc1, 325 "Impact
Rover" 0xc1, 326/327 empty. Store pcs are outside {0x5741e1,0x5741f0,0x5741fe,0x572800}.
WHAT BITS 6/7 MEAN IS OPEN. Callers of 0x595b10: 0x4392fe/0x5740f7/0x57a021.
Evidence: evidence/m81write4.gdblog, traces m81write4_r0..2.

## M82 block (session 125, 2026-10-28, ACCEPTANCE FAIL — static half only)

| what | finding | evidence |
|---|---|---|
| consumers of the flag WORD `0x98ad88+tid*52+0x30` | 168 sites enumerated; EVERY test uses 0x1/0x4/0x8/0x10 — **no test of bit 6 (0x40) or bit 7 (0x80)** in the absolute or the `[reg+0x30]` pointer form; the markup test is bit 2 only (`0x5ac99c`) and B comes only from `0x5ac950`, so the price gate's `edi` cannot depend on bits 6/7 | **H (bytes)** `grep -n 98adb8 scratch/m574/text.txt` |
| bit 7 (0x80) | writer `0x57412c` (sweep, M81); the ONLY other bit-7-specific instruction is the CLEARER `and BYTE PTR [eax*4+0x98adb8],0x7f` at **`0x577ca8`** (`call 0x43f470` follows, ecx 0x71df20) | **H (bytes)** `dis.py 577c60 577cc0` |
| bit 6 (0x40) is NOT markup-off | live, already in hand: gate row `f30=0x41` (bit 6 set, bit 2 clear) charged `edi 45` = markup ON | **H (live)** `evidence/m74flag2.gdblog` |
| census of all 8 bands (0..511) | nonempty 34; bit6 carriers [193,194,324,325,386,449], bit7 [324,325,386,449], bit2 [64,128-131,256,320-323,448,449]; stock faction designs read 5 (bit0+bit2), band-0 designs 1 | **H (live)** `evidence/m82census_s126.txt` |
| the census is a SNAPSHOT | 19 min later the same read gives 385=0x81, 386=0x1, new 387=0xc1, bit7 [324,325,385,387,449], 194=0x45 — faction records are re-inited and re-marked between rounds | **H (live)** `evidence/m82bit7c.gdblog` header |
| the live poke test (bit 7 alone at the gate) | NOT MEASURED — acceptance m82bit7a/b/c FAIL (wrong chooser head; zero gate rows; a concurrent veilbrowser window occluded the Wine window; session 126 ran in the same worktree) | **OPEN** `evidence/m82bit7b.gdblog`, `evidence/m82bit7c.gdblog` |

## M82 (s127, `m82bit7d`) — `+0x30` BIT 7 IS NOT A PRICE TEST (live proof; complements s125's static FAIL block)

LIVE (one invocation, gates G1-G7 True, PASS): record 194 at University Base's head, storage held 20
(below both prices) every boundary — W1 flag 0x41 -> gate `0x4efa5e` edi=45; controlled poke changed
ONLY bit 7 (0x41 -> 0xc1, read back from /proc/pid/mem) -> W2 **edi=45 unchanged**; control bit2 on
(0x45) -> **edi=27** (markup off, M73/M74), so the instrument can see a switch. VERDICT: bit 7 does
NOT gate the price. Census (fresh m54b_clean): bit7 carriers [386, 449] = records the sweep (re)inits
via 0x57412c; ours (192/193/194) never carry it. Static (all 168 flag-WORD sites): no `test` of bit 6
or bit 7; the only bit-7 clearer is 0x577ca8 `and BYTE [tid*4+0x98adb8],0x7f` inside FUN_00577280
(shard_014.c:19576), which also tests bit 0, bit 2 (`&4`), sets 0x200 when bit 3 set, clears bit 3;
bit 5 (0x20) is ORed at 0x531782, bit 6 has no clearer found. Evidence: evidence/m82bit7d.gdblog,
traces m82bit7d_r0..r2.

## M84 (s129, `m84canc1`) - THE +9999 RETURN OF 0x496ad0 IS ITS DIALOG-CANCEL SENTINEL (static); acceptance FAIL

- Return gate: 0x497683 `cmp [ecx+0xa774],-1` / 0x49768f `cmp [edx+0xa778],0` -> 0x4976ce
  `mov [ebp-0xb9c],0xffffd8f1` (= **-9999**, not +9999; ecx = [ebp-0x10] = the thiscall
  chooser_sub 0x6a9e9c, which 0x496af1 loads from the caller's ecx, and the -1 is stored through
  EAX at 0x496a43 — corrected live at s130); cancel==-1 with result != 0 -> 0 (0x497698); field != -1
  -> the pump return (call 0x401940 at 0x497704/0x497777, negated iff 0x495480 bit 0x20 clear).
- -1 is written ONLY at 0x496a43 (handler FUN_00496950 case 7 = CANCEL, together with result 0 at
  0x496a27) and 0x495541 (FUN_004954e0 setup). Handler cases 0/2/5 bail when already -1.
- Live (`scripts/m84_cancel_sentinel.py --tag m84canc1 --escape --no-ok`): SENT 1 edi=2, ARM 1
  (buf=0, gdb could not read 0xa774), GATE 1 buf=0x6a9e9c cancel=3 result=5, BRANCH 0, ENTRY 0;
  gates G1 True, G2-G7 False -> FAIL, merge nothing.
- Evidence: evidence/m84canc1.gdblog.

## M84b (s130, `m84canc2`) — THE CANCEL SENTINEL IS LIVE; THE 0x270f BLOCK IS A DIFFERENT (POSITIVE) SENTINEL

- Live (`python3 scripts/m84_cancel_sentinel.py --tag m84canc2 --escape --no-ok`, ONE invocation,
  6 silent bps 0x41860a/0x41860f/0x496a43/0x497683/0x418d7d/0x577280): CALL obj=0x6a9e9c cancel=3
  mode=0 slot=1 -> GATE cancel=3 mode=5 -> SENT edi=2 -> CALL obj=0x6a9e9c cancel=3 mode=5 slot=3
  -> ARM obj=0x6a9e9c pre=3 mode=0 (Escape) -> GATE cancel=0xffffffff mode=0 -> SENT edi=-9999
  (0xffffd8f1). G1/G2/G3/G8 True; BRANCH 0 ENTRY 0 -> G4-G7 False -> FAIL, merge nothing.
- Escape on the chooser reaches bar handler 0x496950 param -2, which stores -1 through EAX at
  0x496a43; the chooser_sub is the thiscall ecx the caller loads at 0x418604 `lea ecx,[ebx+0xa1c]`
  (pane 0x6a9480), NOT the pushed 24 KB buffer (live buf=0xbe3984, a stack address).
- On -9999 the caller 0x417ee0 restores the queue from its snapshot (0x418623-0x41863f ->
  base+0x50..+0x78; pending at +0x4c from [ebp-0x20]) and leaves via 0x4186d2 `jle 0x419967`
  (`push 1; mov [ebx+0x3ff5c],0; call 0x416080`).
- RETRACT (s129 wording): 0x41861b/0x4186d2 do not gate the 0x270f block — the ONLY branch to
  0x418d7d is 0x4187be `cmp edi,0x270f`/`je`, POSITIVE +9999, on the mode 5/7 paths
  (0x4187a2/0x4187ad) only when [ebp+0x8] != 0. So 0x577280 (sole bit-7 clearer 0x577ca8) runs on
  a +9999 chooser result, not on cancel. OPEN: what yields +9999.
- Evidence: evidence/m84canc2.gdblog, scratch/m84b_selftest.py.

## M84c — the chooser modal 0x496ad0 has THREE value sources; +9999 is a row KEY nothing inserts

`0x496ad0` (n_callers = 1, only 0x41860a) returns: **-9999** (0x4976ce, `[obj+0xa774]==-1` and `[obj+0xa778]==0`), **0** (0x497698, armed with mode != 0), or **+/- the +4 word of the seeked node** of the list at `obj+0xa780` (= 0x6b461c for the chooser_sub 0x6a9e9c): pump 0x497704 seeks with `call 0x4026b0` (index > `[c+0x10]`-1 -> 0; cursor = `[c+8]`; step `node = [cursor+0xc]`; index stored at `[c+0x14]`), then 0x497725 `call 0x495480; and eax,0x20` — bit SET -> 0x49773a `call 0x401940` (`[c+8]==0 -> 0`, else `[[c+0xc]+4]`), bit CLEAR -> 0x497777 same call then `neg eax`; 0x4977ab returns eax. The caller snapshots it (0x41860f `mov edi,eax`, 0x418616 -> `[ebp-0x10]`, 0x418794/0x4187a2 reload) and 0x4187be `cmp edi,0x270f` is the ONLY branch to the 0x270f block 0x418d7d -> 0x418d8a `call 0x577280`. The list's only writers are 4 functions calling 0x42ee20 (0x4954e0 x2 with key = its setup loop var, 0x42e4d0, 0x42ef40, 0x4b0a80) and **none passes 9999**. Live `python3 scripts/m84c_item_pump.py --tag m84cprobe1` (FAIL: G3 instrument, G5 the claim): PUMP idx=3 count=13 -> VAL 2, SENT 2, CHK edi=2, BRANCH 0, ENTRY 0; inserted words [0,1,2,3,6,16,17,18,32,34,38,39,41,42,161,192,193,194]. Evidence: evidence/m84cprobe1.gdblog.

## M84d (s132, acceptance m84dky1 FAIL, branch milestone/m84d, UNMERGED) — 0x4a99e0 IS A VIRTUAL METHOD AND ITS >9999 LEG NEVER RUNS IN PLAY

- OWNER: the dword 0x4a99e0 occurs ONCE in the image, at 0x67671c, inside the 197-slot pointer run
  0x676584-0x676894. Constructors 0x498ea6/0x498eac store vptr 0x67658c at [obj] and 0x676584 at
  [obj+0x444] (0x498f00 `sub ecx,0x444` = the secondary thunk), so it is primary vtable slot 100 /
  secondary slot 102. No `call [reg+0x190]` in .text -> dispatched by a computed index. A scan of
  every rw region of terran.exe found ZERO live objects with vptr 0x67658c/0x676584/0x67673c.
- >9999 LEG = per-FACTION context switch: `[this+0x1d6f0]=1`; outgoing slot (ds:0x888514-1)*0xb4c
  gets +0xb38 = -1 then notify `[[slot+0x80]+0xf0]`; incoming slot (key-9999-1) gets +0xb38 = 2
  then the same notify; then `call 0x4a72c0(this, ds:0x86ae40, key-9999, [this+0x1d6e0])`. Records
  are 2892 B (stride 0xb4c) at this+0x80. The <=9999 leg needs `[this+8]==4` and
  `[this+0x1d6dc]==ds:0x91b5b4` (=3 live) and switches on 0xcef..0xcf4.
- ds:0x888514 = FACTION INDEX (live 0): 0x4a0c17 compares it to BYTE[i*0x130] of the 19 base
  records at 0x95da14 (names verified live: University Base 3, Gaia's Landing 2, The Hive 2, Morgan
  Industries 4, Sparta Command 5, New Jerusalem 6, Korolev Center 3 — owner faction at +0);
  0x499f13 also indexes 0x94d7fc by it with stride 0x20bc. All 37 .text references to it are READS.
- LIVE: `scripts/m84d_faction_key.py --tag m84dky1 --boundaries 8` — 8 silent bps armed
  ("Breakpoint 1 at 0x4a99ec".."Breakpoint 8 at 0x4a759f", clean detach), driver m56_build rc=0
  83 s "boundaries 8/8" with 1 verified production arrival: 0 KEY, 0 LOW, 0 OUT, 0 IN, 0 AFTER,
  0/0 notify, 0 SETFLAG2, 0 CLEARFLAG -> G1..G8 False. merge nothing.
Evidence: evidence/m84dky1.gdblog.

## M84e (session 133) — the 0x4d00 widget message: POST -> queue 0x91db70 -> dispatcher 0x52bce0 -> handler 0x52ed7d

- STATUS **H (instruction bytes) / acceptance m84edisp1+2+3 FAIL, merge nothing**: sending 0x4d00 is
  a queue POST, not a call; its handler is reached through a code switch, not a `call`.
- POST: 0x584010 builds a 32-byte record on its OWN stack (+0 WORD code, +4 ds:0x91b5b4, +8 the
  0x671368 result, +0xc ds:0x91f694, +0x10..+0x1c args 2-5), then `push [ebp+0xc]; push 0x20;
  push &rec; mov ecx,0x91db70; call 0x52a260` under guard ds:0x920438 inc/dec. Pumps pop it with
  `call 0x6361ff` and hand it to 0x52bce0 (16 pump loops, 0x5262ff-0x526707).
- DISPATCH: 0x52bce0 `mov ebx,[ebp+0x8]` = record, `mov ax,[ebx]` = code, 53 arms; the ONLY 0x4d00
  arm is 0x52eb61 `cmp eax,0x4d00` / 0x52eb66 `jg` / 0x52eb6c `je 0x52ed7d`. ONLY .text sender:
  0x4194a4 (`push 0x4d00; call 0x584010`) inside the chooser function 0x417ee0.
- HANDLER 0x52ed7d: record = 0x984d38 + a2*48 + 1872 where a2 = 0xffffffd9 - edi (1872 = 39*48
  cancels the -39 sentinel) = 0x984d38 - tid*48 — a THIRD stride-48 site for the M67 conflict;
  record+0x14 (0/1/2) selects three sub-behaviours over 1436-byte records at 0x927590/0x927894.
- RETRACT M70 mechanism: 0x52ed7d-0x52f756 writes nothing at +0x3ff5c/0x6e93dc; 0x4194b3 is in the
  SENDER, right after `call 0x584010` returns.
- LIVE `scripts/m84e_msg_dispatch.py --tag m84edisp3 --base-index 0` (7 silent bps; --tag selftest
  discriminates): ZERO obj=0x6a9480 pre=15 -> ZEROAFTER post=0, so the cursor store lands and the
  cursor is PANE-relative (+0x3ff5c = 0x6aa9dc on the static pane 0x6a9480), NOT the fixed
  0x6e93dc; POST 0 DISP 0 ARM 0 HND 0 IDX 0 because the post is CONDITIONAL (0x419464/79/8e/92
  jump past 0x4194a9). merge nothing.
Evidence: evidence/m84edisp1.gdblog, evidence/m84edisp2.gdblog, evidence/m84edisp3.gdblog.

M84e (s134 static follow-up; acceptance m84edisp1/2/3 FAIL, PR #88, merge nothing): the 0x4d00 POST
at 0x4194a9 is gated at 0x4193b2-0x4193b9 (`mov eax,ds:0x920434`; `test`; `je 0x4194b1`), at
0x4193bf on FUN_00417ee0 arg1 == 0, and at 0x4193ca-0x4193d2 on base+0x50 (the queue HEAD) !=
[ebp-0x1c]; 0x4194b1 (`push 1; mov [ebx+0x3ff5c],0; call 0x4eb6b0`) is the COMMON exit of four
jumps, so the cursor zero runs WITHOUT any POST (that is s133's 15 -> 0 read-back). ds:0x920434 is
set to 1 by exactly ONE writer, FUN_0057ecf0 (0x57ecf0, strings INTRO/SCENARIO/TOPMENU/MULTIMENU/
openinga_pcx/fx_opening_menu_wav = the opening movie + scenario/top-menu loop), and to 0 by every
other store (0x50fe70, 0x50fff5, 0x510196, 0x515ad8, 0x516f30, 0x51f267, 0x52280c, ...); live 0 on
the hud. So the send->queue 0x91db70->pump 0x6361ff->switch 0x52bce0->arm 0x52eb61->handler 0x52ed7d
chain belongs to the OPENING MENU, not to a loaded game. Evidence: instruction bytes only
(scratch/m71/dis.py 419340-41940f; grep -n "ds:0x920434," scratch/m574/text.txt).

M84f (s135; m84fpath1 FAIL on my own G4, m84fleg4/5 invalid): the netgame-gated 0x4d00 block (case at 0x419355 inside FUN_00417ee0) RUNS on the UI insert path — measured CHOOSER 2 / CASE 1 / BUMP 7 / EXIT 1 / NETCALL 1 with ds:0x920434 = 0 and pend 5 -> 6 — and exits via 0x4193b9 `je 0x4194b1` (`push 1; mov [ebx+0x3ff5c],0; call 0x4eb6b0`): cursor zero, no POST. Block content: it first bumps `[0x94de84 + item + tid*8380]` once per queued slot, then tests the flag. INSTRUMENT LAW: gdb breakpoint lists must be PRINTF-ONLY — any memory write there aborts the batch ("not an lvalue") and detaches at the first hit; poke ds:0x920434 from python via /proc/pid/mem instead (632 writes OK while gdb is attached). Blocker: m54b_clean.SAV = 2150 r50 with an EMPTY chooser candidate array, so the flag-1 arm is still unmeasured.

M85 (s136-s137; m85cens5 PASS, CLOSED): 0x52145e sits in FUN_00521070 (MP 7-stage driver, ONE call site 0x522376) — solo silence BY DESIGN (STAGE 0 in a measured boundary). 0x5a7d00 (+912)/0x5a7f67 (+1527) sit in FUN_005a7970 — LIVE at the boundary (entered once, eax=0, return 0x569948 inside FUN_0055f650, not the human-loop 0x507e57) but neither tail ran: UNTAKEN BRANCHES, not dead code. Round increment 0x51f320 fires once/boundary. Box at s135 swallowed Enter AND measured bar clicks (cause not isolated; fresh load repairs); m44_idle is no gdb-era driver (TracerPid assert; degenerate rounds=1 snapshot) — census drives with m55_boundary. ds:0x920434 carries two names — "save_later" (m55) vs "NETGAME" (M84e).
BOX-LEVEL (s137 RETRACTION): "no input focus" was a misdiagnosis — `getactivewindow` always errors on :99 (no WM); `windowfocus 10485761` works and keys land (Escape flips panes). The real s135-state blocker was the GAME swallowing turn-end input (Enter + measured bar click inert at 2150 r50); a fresh save load repairs it. Retract the "windowfocus does not set it" claim.


M86 (s138; m86cens1 FAIL, m86cens2 FAIL, UNMERGED milestone/m86): THE BOUNDARY TAKES THE TABLE-MISS LEG; THE TWO BIT-SET TAILS ARE GATED OUT UPSTREAM. FUN_005a7970(arg0=band, arg1=kind, arg2): [ebp-0x10] = 1<<arg0 (0x5a7a55-0x5a7a69); exits 0x5a7e00 `je 0x5a8f7d` (round==0) and 0x5a7e0d `jne 0x5a8f7d` (ds:0x926bcc!=0); a 3-entry table at 0x93325c/68/74 (stride 0xc, live shorts 10/25/26) is walked and 0x5a7e73 `0f 85 26 01 00 00 jne 0x5a7f9f` skips the 64-record band loop unless arg1 == that short. cens1 measured a0=5 a1=8 a2=0 ret=0x5aaad0, ALT 3, LOOP 0, GATE1/2 = OR1/2 = ELSE1/2 = 0, round 50->52. cens2 (clean boundary 52->53, driver rc=0) measured ZERO helper hits -> RETRACT s137 "entered once/boundary". Both tails 0x5a7d00/0x5a7f67 are `or BYTE PTR [eax*4+0x98adb9],0x1` = type record +0x31 bit 0 (bit 8 of the +0x30 flag word), gated by 0x573a90 != self (0x5a7f48 `je 0x5a7f83`), ds:0x920434 != 0 (LIVE 0) AND (1<<arg0) & ds:0x985b10 != 0 (LIVE 0x20 & 0x08 = 0); else 0x572800 + 0x4ef540. Evidence: evidence/m86cens1.gdblog, evidence/m86cens2.gdblog.


M87 (s138; m87trig1 FAIL on my own typo 0x5aaccb!=0x5aaacb, m87trig2 PASS 8/8 gates, milestone/m87): THE CALLER OF FUN_005aaa20 IS FUN_005aadf0 AND IT RUNS ON THE FIRST BOUNDARY AFTER A FRESH LOAD. Attribution by return site: ret=0x5aaf4b -> site 0x5aaf46 `e8 d5 fa ff ff call 0x5aaa20` -> FUN_005aadf0 (528 B), whose ONLY call site is 0x4f35cb inside FUN_004f34b0 (298 B, 1 caller). aaa20(faction=5) took the LIVE leg (ds:0x920434=0 -> 0x5aaa6d `je 0x5aaaa0`), read its PER-FACTION SLOT [faction*191*4+0x94d7fc] = 8 (KIND 0 -> FUN_005aa880 never ran), stored -1 at 0x5aaac1 and called FUN_005a7970(5, 8, 0) at 0x5aaacb — the a1=8 that M86 read as the table-miss leg (WALK 3, LOOP 0, ALT 3, table shorts 10/25/26). Round 50->52 read back from /proc. CONFOUNDED: AAA-hit windows also had driver rc=1 + a 2-round jump. Evidence: evidence/m87trig2.gdblog, evidence/m87trig1.gdblog.


M88 (s139; m88slot1-3 FAIL on my instruments, m88slot4 6/7, m88slot5 6/7, m88slot6 PASS 7/7, milestone/m88): THE SLOT [0x94d7fc + idx*8380] IS WRITTEN THROUGH A POINTER BY FUN_005aa880. Hardware watchpoint on 0x957ba8 (record 5), one poke of -1, four boundaries: n=1 val=-1 from FUN_005aaa20's own consumption (0x5aaac1), n=2 val=36 from **0x5aa9d3 `89 1e mov DWORD PTR [esi],ebx` in FUN_005aa880** (esi built at 0x5aa9c5 `lea esi,[eax*4+0x94d7fc]`); read-back final=36 == the last attributed store; control watchpoint on ds:0x985afc fired 4x (writer 0x51f53c in FUN_0051f320), proving the DR mechanism works. A mnemonic grep for `0x94d7fc` finds only direct stores (0x51038c FUN_005102f0, 0x59cfce FUN_0059ce10, the -1 stores 0x59cffe/0x59f23c/0x5a7db2/0x5aaac1) and MISSES the pointer forms (0x5aa9c5, 0x52ae09 in the 64-caller accessor FUN_0052a720). Slots after a fresh load: [-1,3,8,22,49,8,5,48]; the values 45/13/36 allocated in three consecutive windows -> the slot is a work-item allocation, not a constant. Observed invariant: every aaa20 CALL event has kind == the slot value it read (8/8 across slot2+slot6). Evidence: evidence/m88slot6.gdblog (and m88slot1-5).


## M89 — the work-item slot: WHO asks, WHEN, and WHERE the value comes from

- **Who:** `FUN_005aadf0`, call site **0x5aafee** `e8 8d f8 ff ff call 0x5aa880` (return site 0x5aaff3) — 3/3 observed allocations. The other three sites were armed and produced ZERO: 0x52132f (FUN_00521070 stage 3, the MP driver — 0 solo visits per M85), 0x5aaaab and 0x5aab58 (FUN_005aaa20's own legs, unreachable while the slot is >= 0).
- **When:** only when the slot reads negative — 0x5aafda `8b 86 fc d7 94 00 mov eax,[esi+0x94d7fc]` / `85 c0` / `7d 18 jge 0x5aaffc` — and only when 0x5aafe4 `83 3d d4 6b 92 00 01 cmp DWORD PTR ds:0x926bd4,1` / `74 0f je 0x5aaffc` passes. It is the same invocation whose call to FUN_005aaa20 at 0x5aaf46 consumed the slot (aaa20 stores -1 at 0x5aaac1, then calls the helper at 0x5aaacb). The caller stores the returned value a second time: 0x5aaff6 `89 86 fc d7 94 00 mov [esi+0x94d7fc],eax`.
- **Where the value comes from:** FUN_005aa880's live leg (0x5aa883 `a1 34 04 92 00 mov eax,ds:0x920434` / 0x5aa892 `je 0x5aa9a5`) pushes 0/-1/0/edi and calls **FUN_005ab000(faction, 0, -1, 0)** at 0x5aa9ac; 0x5aa9b3 `mov ebx,eax`; 0x5aa9c5 `lea esi,[eax*4+0x94d7fc]`; 0x5aa9d3 `mov [esi],ebx`. Live proof: `CHR n=1 eax=36 args=(5,0,-1,0) fac=5` -> `ST n=1 addr=0x957ba8 val=36 chr=36 ret=0x5aaff3` -> `RB mem=36` -> /proc slots[5]=36.
- **What it is NOT:** a global type-record id. `scratch/m89/recname.py 262651 36 44 13 32 5 48 45` — 36/44/32/48/45 are empty records at 0x98ad88+id*52 (name '', cost 0); 13 Unity Foil, 5 Supply Crawler, 3 Transport Foil, 8 Mind Worms, 10 Locusts of Chiron are real ANY-faction units (owner mask 0xff00). Domain: every observed value < 50, and 0x5aaf10 `cmp ecx,0x59` (=89) shows the space reaches at least 89; FUN_005ab000 has a 0xc5c-byte local (0x5ab018) scanned via 0x489fd0 then 0x48b9a0.
- **Numbers:** `python3 scripts/m89_alloc_census.py --tag m89alloc1 --poke-index 5 --rounds 3 --timeout 100` = **PASS 8/8** (2 allocations, both val 36, both ret 0x5aaff3, poke 36->-1, round 68->71, ctrl 3, aaa 1, cons 1); `--tag m89alloc2 --poke-index 5 --rounds 3 --timeout 100` = **PASS 8/8** (1 allocation, val 36, round 71->74). Evidence: `evidence/m89alloc1.gdblog`, `evidence/m89alloc2.gdblog`.


## M90 — the slot value is a TECH INDEX; the chooser is FUN_005aa030(faction)

- **Domain:** `0x92fdd4 + i*44`, `i < 0x59` (89 entries), 8-char name at +16, prereq ints at +0 and +4. Names read from live memory: 5 Ecology, 10 Alloys, 13 Surface, 22 AGrav, 25 SingMec, 26 ConSing, 32 DigSent, 36 Integ, 44 IndEcon, 45 IndAuto, 48 Gene, 88 TranT. Corroboration: Alloys' prereqs are 30 (Solids) + 7 (Chaos) = SMAC's Alloy Theory <- Solid State Physics + Chaos Theory.
- **Chain:** FUN_005aa880 -> FUN_005ab000 (thin wrapper: 0x5ab047 `call 0x48b9a0`, 0x5ab04c `mov esi,eax`, 0x5ab0bf `mov eax,esi`) -> FUN_0048b9a0's non-human leg returns **FUN_005aa030()'s eax verbatim** (call site 0x48bae4 `e8 47 e5 11 00`, landing 0x48bae9) -> FUN_005aa030 gates with FUN_005a6cd0, scores with FUN_005a90a0, tie-breaks with `_rand`, returns the winning index.
- **Live:** `python3 scripts/m90_tech_choice.py --tag m90tech2 --poke-index 5 --rounds 3 --timeout 100` = **PASS 8/8** — (fac5 36 'Integ'), (fac7 32 'DigSent') at round 77; (fac2 32 'DigSent'), (fac6 13 'Surface') at round 79; every store ret 0x5aaff3, every chooser param1 == the faction, every value read back from /proc; round 77->80, a030 calls 4, CONS 3.
- **First attempt:** `--tag m90tech1` = FAIL on G6 only, from my own events-slice bug (sliced by the ST index inside `st`, not inside `events`); its data already agreed (idx_from_5aa030=22 == eax=22). Evidence: `evidence/m90tech1.gdblog`, `evidence/m90tech2.gdblog`.

## M91 — FUN_005a90a0's BASE = SUM over four (cost,demand) pairs of (demand*m+1)*cost; the research pick is max-of-random-DRAWS, not max score (m91score5 PASS 7/7, MERGED)

`python3 scripts/m91_scorer_census.py --tag m91score1 --poke-index 5 --rounds 3 --timeout 120` -> **FAIL 6/7**
(G1 poke 36->-1; **G2 12/12 predicted BASE == engine [ebp-0x4] at 0x5a930b**; G3 FALSE; G4-G7 TRUE;
round 80->83; fac5 win 36 'Integ', fac4 win 43 'EthCalc').
Costs T0,T4,T8,Tc = *(0x92fdc4+idx*44+0,+4,+8,+0xc) (prereq1 +16 = 0x92fdd4, name +32); demand
Y10/Y14/Y18/Y1c = *(fac*8380+0x94d810/14/18/1c); m = 1 if arg2 != 0 else 4/2 by 0x985ac4 bit 0x200 (SET);
halved at 0x5a92fd iff all four pairs inert (bc = bit-0x10 popcount of 0x94d448 dwords 1..7,
[fac*8380+0x94e488] >= 4). Tail 0x5a94fd-0x5a95f8 adds byte[fac*8380+0x94e5a8+esi]*Tc over divisors keyed
by byte[+0x94eda8+esi] in {7,2,0} (fac5 idx36 15->112, fac4 idx60 19->38, unchanged where Tc==0).
FUN_005aa030: score = score*256/level (0x5aa1e4, level = max FUN_005a6d40(p,1)); DRAW = _rand() % (score+1)
(0x5aa217); keeps the STRICTLY greater draw (0x5aa232). Counter-example: fac4 winner idx43 final 16 vs
candidate idx60 final 38, draws 1838 vs 2. ACCEPTANCE CLOSED by `--tag m91score5 --rounds 4` on a fresh
load: **PASS 7/7** — 4 AI windows (fac5 8 'E=Mc2', fac5 22 'AGrav' final 31 vs max_final 56, fac4 60
'PlaEcon', fac6 13 'Surface' final 36 vs 63 — max-score falsified twice more), 27 candidates 0 base
mismatches, 4/4 ST/RB pairs, round 50->55. G3/G5 were instrument defects, fixed by bytes (0x5aa235 jle)
and event order (0x5aa9d5 after 0x5aa9d3), not by floors. Evidence evidence/m91score1-5.gdblog.

## M92 — the scorer's tail 0x5a9503-0x5a9698 (NOT YET MERGED; acceptance m92tail2-7 all FAIL, model decoded)

THE TAIL, verified against the engine's own finals (evidence/m92tail5.gdblog CAND line fac7,
scratch/m92/verify7.py over evidence/m92tail7.gdblog + scratch/m92tail7_snaps.bin):
- divisor `[fac*8380+0x94e488]` (0x5a9503; 0 -> the tail adds nothing; the value MOVES between rounds);
- category byte `[fac*8380+0x94eda8+esi]`, multiplier `[fac*8380+0x94e5a8+esi]`, esi = 1..62
  (0x5a9518 skips 63); the two arrays hold EQUAL nonzero bytes at the same esi = 0,4,24,36,40,44,48,52;
- Tc multiplier source = the tech record's +0xc cost (`imul eax,[edx+0x92fdd0]` = 0x92fdc4+idx*44+0xc);
- cat 7 adds `mult*Tc / div` (NOT doubled) only when bc != 0 AND the faction is not human;
  bc = [ebp-0x18] is FUN_005a90a0's OWN prologue popcount of bit 0x10 over the 8 control dwords
  [0x94d448+4*i] (0x5a90ae/0x5a90d6) — NOT a caller slot;
- cat 2 adds `mult*Tc*4 / (div*(1+human))`; cat 0 uses factor 4 if `[blk+0x94dc44] >= [blk+0x94dc58]`
  else 2, over `(div*(1+human))`;
- any other category: inner edi=1..7 (skipped whole when arg2 == the faction, 0x5a960e) over the GLOBAL
  band tables `0x950664 + edi*0x20bc` (stride 844) whose OWN byte at +esi must be nonzero (a SECOND
  multiplier), gated on the control dword `[0x94d448 + (fac+edi)*4]` needing bit 0x8 and not
  (bits 0-1 with bit 5 clear); adds `mult*Tc / (div*(1+human))`.
fac7's observed finals reproduce EXACTLY as base + idiv(16*Tc, 1) (cats[40] = 16, div 1); the previous
model (caller-slot gate, band tables inside the block at +0x2bc0) was off by >3 orders of magnitude.
UNNAMED still: who writes 0x94e488 / 0x94e5a8 / 0x94eda8 / the 0x950664 band tables. The band gate's
control dwords move between rounds, so the per-round snapshot must cover 0x94d448..0x966000.

### M92 block (branch milestone/m92, NOT merged — acceptance FAIL 5/8)
- `FUN_005a90a0` TAIL, 0x5a9500-0x5a9698, runs **only when arg2 == 0** (0x5a9375 `je 0x5a9500`) and only for a
  NON-human faction (0x5a931a sends a human to 0x5a94f2). Entry = **0x5a9503**; 0x5a94fd is inside the body.
- `ebx = [fac*8380 + 0x94e488]` = DIVISOR; 0x5a950b `je 0x5a9698` -> whole tail adds 0.
- Category byte `[fac*8380 + esi + 0x94eda8]` = **blk+0x920+esi**; multiplier `[fac*8380 + esi + 0x94e5a8]`
  = **blk+0x120+esi**; loop esi = 1..62. cat 7 -> `mult*Tc/div` gated on `[ebp-0x18] != 0` and non-human,
  and on gate failure it FALLS THROUGH to the band leg; cat 2 -> `mult*Tc*4/(div*(1+human))`; cat 0 ->
  `mult*c*Tc/(div*(1+human))` with **c = 2 if [0x94dc44] >= [0x94dc58] else 4** (those two live at
  blk-0x844 / blk-0x830, i.e. +0x7fc/+0x810 from 0x94d448); band leg -> `mult*Tc/(div*(1+human))` per
  accepted edi 1..7, gated on `[esi+0x950664+edi*0x8380] != 0` and the control dword
  `[0x94d448+fac*8380+4*edi]` having 0x8 and not (0x3 without 0x20).
- `TAILOUT` at **0x5a9698** = the tail's output; the SCORE at 0x5aa159 is a **post-tail leg** on top
  (0x5a9698 -> 0x5aa022), +1/+29 observed. Gating the tail on `final` conflates two legs.
- The DIVISOR and the arrays are **FROZEN WITHIN A ROUND** (s146: 0/39 and 0/19 per-TAIL-hit dumps
  differ from the candidate's own round snapshot; divisor cross-check 39/39 proven, bad=0). They move
  **BETWEEN rounds** (fac2 mult(esi1) 4->5 at r56, dc58 1->2 at r57, 2->4 at r58) — a census must stamp
  each candidate with the round live at ITS score (s145's "moves inside a round" RETRACTED: it was the
  window/snapshot pairing defect).
- M92 ACCEPTED (s146, `m92tail18` PASS 8/8, fresh load r51->55): TAILOUT == BASE + the simulated tail
  on **39/39 candidates, 0 mismatches, 2 qualifying windows**; naive one-factor splits 19.

## M93 block (sessions 148+147, 2026-10-29) — the POST-tail leg 0x5a9698-0x5aa022 (ACCEPTED: m93post3 PASS 9/9)

| fact | evidence |
|---|---|
| the POST leg is SKIPPED (final = tailout) when `[0x985c1c+idx] & (1<<fac)`; else `call 0x5312d0` (returned 0 for all 82 traced candidates) and only then the ds:0x985a9c leg may ×4 | 0x5a96d0-0x5a973f instruction bytes; evidence/m93post1/2.gdblog P531 res=0 82/82 |
| `0x5a9020(a,X,d)` = a == X or a is a prereq-ANCESTOR of X within d levels (0x5a9063 recurses on [X*44+0x92fdd4]/+4 with d-1; a<0 or X<0 -> 0) | objdump 0x5a9020-0x5a9090 |
| the cascade stages + their sets: A(47,0x9305e8/ec)x3 B(61,0x930850/854)x2 C(64,0x9308d4/8d8,d2)x2 D(35,0x9303d8/3dc,d1)x2 E(59,0x9307f8/7fc)x2 FIM(demand81c+1)x2 G(0x98582c)x2 if [0x927a8c+fac*1436]>0 else 0x93325c/0x933268 (x2,x2,+1@0x5a99cc,x2@0x5a9a21 if ac4 bit 0x200 clear) q=[0x94dc28]/clamp([0x94e488],1,0x270f) added if q>demand81c and idx in closure(0x984fec/984fbc/98531c/98534c) **x2@0x5a9c17 (0x9851cc) and x3/2@0x5a9c68 (0x9851fc) if [0x927a80+fac*1436]>0** era table 0x92b954 x21 (flag -4; ==id x3/x4, ==pr1/pr2 x2/x3) x3@0x5a9df3 (89-tech scan) x2/x4@0x5a9eb5 (0x98adee) | disassembly windows 0x5a9747-0x5aa022; scratch/m93post2.gdb |
| the band scan 0x5a9f83-0x5aa022 (x3/x6 @0x5aa004, x2+4 @0x5aa01b) contributed NOTHING in this state: PQ3/PR2/PS2p4 = 0 events in 82 candidates; PFIN ebx is the scan's retry flag (0/1) or idx, never a tech id | evidence/m93post1.gdblog, m93post2.gdblog counters |
| ACCEPTANCE m93post2 FAIL 8/9: G1-G8 green (tail exact 40/40, div 40/40, 2 windows), G9 ladder 13 predicted / 4 mismatch; RETRACTED "final = TAILOUT*5" | scratch/m93post2.out lines 27-31 |
| ACCEPTED (s147): m93post3 PASS 9/9, ONE invocation, fresh m54b_clean r50->55 — G9 13/13 candidates, 0 mismatch, splits 11 vs final==tailout and 13 vs tailout*5; G1-G8 green; fac2 win=8 E=Mc2 186=31x3x2, fac5 win=13 Surface 56=28x2 | scratch/m93post3.out; evidence/m93post3.gdblog |
| the 4 post2 mismatches were ALL TIMING: 0x92adbc, the era table and designed prereq fields move between the 0x51f320 boundary snap and the ladder — the census now dumps 0x927a00-0x933300 + 0x984f00-0x98b000 AT each TAIL hit and re-reads demand there (d814t/d818t/d81ct); LAW: freeze inputs at the consumer's read timing | m93post2 vs m93post3 verdicts; scratch/m93post3_tailx1/2.bin |
| K1/K2 gate correction: 0x5a9bb7 reads [0x927a80 + arg2] UNSCALED and arg2 = 0 at every tail call (BASE a2=0) — plain global [0x927a80], live 0, so K1/K2 never fire (PT1/PT2/PSX = 0 events in m93post3); the band region DID run 5x (PBH) and contributed x1 | disasm 0x5a9bb7-0x5a9bc2; evidence/m93post3.gdblog PBH/PT1 counts |

**M94 (s149, `m94table3` PASS 7/7):** the tail DIVISOR `[fac*8380+0x94e488]` is RECOMPUTED 0..N every round by **FUN_00556690** (per-faction upkeep stage; 6th call of FUN_005208f0's per-player sequence at 0x52094f, arg=fac; also called by FUN_0059ce10 @0x59dd43): reset trio 0x94e484/488/48c <- 0 at 0x5566cf (watchpoint pc 0x5566d5), rebuild `inc edx; mov [eax+0x94e488],edx` at 0x556a87 (pc 0x556a8d). **Divisor == the faction's base count** (r54: divisors [0,2,4,1,3,3,4,1] == bases/fac {1:2,2:4,3:1,4:3,5:3,6:4,7:1}); count 0 -> block skips -> the pick's fac0 dword 0x94e488 caught 0 stores in 2 boundaries (m94table1). Timing proof: printed cur_player (0x985dcc) == fac at every event. Same stage writes the multiplier `[+0x94e5a8+edi]` (0x556721/0x556b5a) and category `[+0x94eda8+edi]` (0x55851d/0x558551) arrays; 0x950664 = fac1's multiplier array. 10 static 0x94e488 store sites in 7 functions (FUN_004e47d0 0x4e4861, FUN_004e4e10 0x4e4f79, 0x4f3b16/26 unmapped, 0x5088ad/ba, 0x5566cf/0x556a87, 0x59efab, 0x5a0b2e) — only the FUN_00556690 pair observed firing between rounds. Evidence evidence/m94table1-3.gdblog.

## M95 block (session 150, ACCEPTANCE PASS tag `m95pay4`) — pay-site conflict CLOSED

| **the pay + activation of a UI-queued completion: branch A** | q0>=0 dispatches to A: gate 0x4efa5e (cmp [base+0x40],edi; edi=price) -> pay 0x4efedd (`mov esi,[ecx+0x40]; sub esi,edi; mov [ecx+0x40],esi`; watch pc 0x4efee0 new=191) -> clamp 0x4eff20 (min(cap 0x92a370,credit d0)/0, human; watch 0x4eff23 new=0) -> mirror +0x98 -> create 0x4eff4e (0x5ab650) -> POP 0x4f037b -> 0x4ef5d0 (pending store 0x4ef648, 1->0). Credit +0xd0 feeds ONLY the income add 0x4ef7f6 + the clamp — the pay is from STORAGE +0x40 | **VERIFIED (live)** | `evidence/m95pay4.gdblog` (GATEA/PAYA/POSTA/CREATE/POP retn 0x4f0380 + 2 hw watchpoints), `m95pay3.gdblog` |
| **branch B (0x4f0ca6) is the negative-queue/claim path, never the UI shape** | q0<0: tc=-q0; B iff tc>=39 && claim[tc-39](0x985b3c)==-1 (gate 0x4f0a3d), or tc>34 (0x4ef94a), or 0x507410 mask fails (0x4ef985); race scan defers when a competing human base's credit+storage >= its price (0x4f0b4f jge 0x4f0c28, no store); 0x4f0b80 jg 0x4f0ca1 SOLE pay entry — B pays the SAME field (`sub esi,edi; mov [edx+0x40],esi` 0x4f0ca6), claim store 0x4f0d83, POP 0x4f0f46; NO back-edge B->A (cfg.py). Live: 0 events at GATEB/PAYB/DEFERB/BRET/CLAIMED/DISP, no 0x4f0ca9 store | **VERIFIED (bytes) + live 0-event** | `scratch/m95/cfg.py`, `evidence/m95pay3-4.gdblog` |
| **stale tail keeps producing** | after pending 1->0, q0 (non-sentinel) re-enters A: gate-fail visit = no side effect (GATEAF); storage>=price -> PAYA + CREATE phantom + POP with no pending store (r59) | **H (live x2)** | `evidence/m95pay3.gdblog` |
| trap | the f-string bp-condition builder emitted `if *$ecx==` (deref) -> 10 register-cond bps silently 0-fired while the watchpoints carried the truth (m95pay1/2); a no-event is evidence only when the CONDITION is checked against the emitted script and a store pc is known. gdb printf `%x` prints BARE hex — parse accordingly. Fac upkeep runs in the faction's own segment ~1 cycle after turn-end: a 1-boundary window can close mid-cycle (cur_player 2, 0 events — m95pay2) | s150 | `scripts/m95_pay_sites.py` |

## M96 block (session 151, ACCEPTANCE PASS tag `m96human2`) — the tech chooser's human leg

| **bVar14 = ((ds:0x985ac4 & 0x200)!=0 && param_3<=0) — what lets a HUMAN-masked faction take FUN_005aa030 at all** | shard_009.c:9343-9347; live ebc 0x1a0e (bit 200 set), A030 fac=3 observed with ret=0x48bae9 | **VERIFIED (bytes + live)** | `evidence/m96human2.gdblog` A030 n=2, `scratch/m96human2.out` |
| **the score is scaled x256 and divided by the candidate's PREREQ-CHAIN DEPTH, for EVERY faction (not human-only)** | gate 0x5aa164 `test ah,0x2` on ds:0x985ac4; 0x5aa1e7 `shl eax,8`; 0x5aa1eb `idiv edi`, edi = max(FUN_005a6d40(prereq1,1), FUN_005a6d40(prereq2,1)) where FUN_005a6d40(a,b) returns b if a<0||a>=89 else max of the two prereqs at b+1. Live 13/13 divisors == the Python depth from the /proc prereq table, 13/13 quotients == (score<<8)/div; DIV events fire for fac2 (n=1-6) as well as fac3 | **VERIFIED (live 13/13 + 13/13)** | `evidence/m96human2.gdblog` DIV/QUO, `scripts/m96_human_leg.py` |
| **the human mask (1<<fac & byte ds:0x985b10) does ONLY two things** | (a) 0x5aa17e gates the forced pick: [fac*8380+0x94d810] / [+0x94d818] != 0 -> the candidate == WORD ds:0x98adee (live 6) returns at 0x5aa251 with NO draw; live flags fac1 (1,0) fac2 (0,1) fac4 (0,1) fac6 (1,0) fac7 (1,0), human fac3 (0,0) -> 0 events, INERT on this box. (b) 0x5aa204 picks the draw source | **VERIFIED (bytes + live leg 13/13, 0 forced events)** | `evidence/m96human2.gdblog` M17E/M204/SIB10/SIB18/S98/EARLY |
| **the human tie-break draw = a SEPARATE LCG at ds:0x999fa0; non-human = rand() % (score+1)** | FUN_00625af1(0,score+1) = thiscall FUN_00625a0f(&0x999fa0,0,hi): swap if lo>hi, state = state*0x19660d+0x3c6ef35f (mod 2^32), val = ((state&0xffff)*(hi-lo)) mod 2^32 >> 16 + lo; non-human 0x5aa228/0x5aa22e `_rand() % (score+1)`, 0 when score<=0. Live: 7/7 human draws predicted EXACTLY from the state read at 0x5aa20d; the stream advanced exactly 7 steps across the call (911923404 -> 296222889 == the RETV state) | **VERIFIED (live 7/7 exact)** | `evidence/m96human2.gdblog` HDRAW/DRAW/RETV, `scratch/m96/chain.py` + `chain.out` |
| **THE RANKING KEY IS THE DRAW, NOT THE SCORE (score-weighted lottery)** | 0x5aa232 `cmp eax,[ebp-0x8]` (best starts 0xfffffc19 = -999), strictly-greater wins, ties keep the earlier; 0x5aa247 loads [ebp-0xc]. Live: fac3 idx 72 IndRob scaled 2133 drew 5 and LOST to idx 13 Surface scaled 1408 draw 835; RETV idx 13 == the TECH landing == the /proc slot read-back (fac2 also 13). Winners predicted 2/2 | **VERIFIED (live 2/2 + read-back)** | `evidence/m96human2.gdblog` DRAW n=7-13/RETV/TECH, `scratch/m96human2.out` |
| OPEN | [f*8380+0x94d430] bit 0x40 = 0 for all 8 factions at r66 (dwords 0,2,c,3,9,4,8,1) -> the M89 second-ask never ran; [f*8380+0x94d800] live -1,81,128,86,166,128,77,64 (>=89, NOT tech indices); WORD ds:0x98adee = 6 — record 1's +0x32 or a standalone global, unread | INFERRED/OPEN | `scratch/m96human2.out` |
| trap | a bp at a `mov eax,[ebp-0xc]` RETURN site reads the OLD eax (m96human1 printed idx=0) — break at the NEXT instruction; 0x5aa21a `lea edi,[eax+1]` makes edi the MODULUS on the rand path, so a bp at 0x5aa232 printing $edi gets score+1, not the faction — read [ebp+8] | s151 | `scripts/m96_human_leg.py` |

## M97 block (session 152, ACCEPTANCE PASS tag `m97credit3`) — base+0xd0 (credit) is RECOMPUTED EVERY ROUND by FUN_004e93f0; the "written only at record init" trap is RETRACTED

| fact | evidence | status | source |
|---|---|---|---|
| **FUN_004e93f0 writes base+0xd0 twice per call** | 0x4e9557 `mov [eax+0xd0],edx` = [eax+0xc0]-[eax+0xf0]; 0x4e9562 `[eax+0xe0]=0`; 0x4e957f `mov [eax+0xd0],ebx` = credit-[eax+0xe0]; mirror 0x4e9590 `mov [eax+0x94],edx`; eax = ds:0x8f0d60 = the current base-record pointer. 12 store executions in 2 boundaries (r54/55/56), 12/12 stored values == c0-f0(-e0) read live AT the store; read-back credit == last store, +0x94 == credit | **VERIFIED (live 12/12 + read-back)** | `evidence/m97credit3.gdblog`, `scripts/m97_credit_watch.py` |
| **only SIX stores to `[reg+0xd0]` exist in all of .text** (734,503 instructions scanned): the two above + 0x5ba9e8 (ebx-zeroing sweep +0xa0..+0xe8, base creation), 0x6310c6/0x631154 (record init), 0x6315e2 (`=0`). The income add 0x4ef7f6 and the clamp 0x4eff20 write **[+0x40] STORAGE**, never +0xd0 (they only read credit) | static scan; the +0xd0 hardware watchpoint saw ONLY the two static store pcs in three runs (G8) | VERIFIED (scan + live) | `scratch/m574/text.txt`, `evidence/m97credit1.gdblog` |
| **WHEN: every round, in the current player's own segment** (cp=3 printed on every event). Callers: FUN_004f5a70 (the per-base turn stage — call 0x4f5ad2 after 0x4ef6d0/0x4f26e0/0x4ee410, and call 0x4f5b46 after 0x4e8d60/0x4e78e0/0x4e92c0; FUN_004f5a70 itself called at 0x5206d3) and the recalc helper FUN_004eb6b0 (call 0x4eb6db; runs whenever arg1 != 0, many UI callers 0x40b232..) | return address `*(int*)($ebp+4)` printed at every store, named by containment | **VERIFIED** | `scratch/m97credit3_seq.jsonl` |
| **inputs**: GROSS [+0xc0] is rebuilt from 0 every call by FUN_004e78e0 (reset 0x4e79a8, +1 per facility 0x4e7c19, +1 0x4e85c1); UPKEEP [+0xf0] = DAT_008f0c38 + DAT_008f0c4c (store 0x4e9544) — the WHOLE-FACTION upkeep total, so one facility anywhere raises every base's upkeep: r51 f0 3->4 credit 0->-1, r52 c0 3->4 credit -1->0 (the M95 -1->0 observation, reproduced) | hw watchpoint events on +0xc0/+0xf0 (30 events) | **VERIFIED (live)** | `evidence/m97credit1.gdblog`, `m97credit3.gdblog` |
| trap | a gdb HARDWARE watchpoint only reports a VALUE CHANGE (it re-evaluates the expression and continues silently) — an unchanged recompute logs NOTHING (m97credit2: 15 GROSS stores, 0 CREDIT events); count stores with silent bps AT the store instruction. `[New LWP]` banners arrive AFTER the attach printf and must be whitelisted (m97credit1) | s152 | `scripts/m97_credit_watch.py` |
M98 (s153; m98budget1 aborted, m98budget2 9/11, m98budget3 10/11 on instrument bugs, m98budget4 PASS 11/11, milestone/m98): `[faction*8380+0x94d800]` IS THE FACTION'S ADVANCE THRESHOLD — a memo of `FUN_005aab70(faction)`, compared against the accumulator `[faction*8380+0x94d7f8]` by `FUN_005aadf0` (per-base upkeep tail, 0x4f5c2e FUN_004f34b0 <- FUN_004f5a70 <- 0x5206d3). Grant iff threshold <= acc: print "Researched Advance", FUN_005aaa20(fac) consumes the work-item slot, FUN_0047f590 applies it, then acc = 0 (0x5aaf5c), field = -1 (0x5aaf67), field = FUN_005aab70(fac) (0x5aaf79, call at 0x5aaf71). .text holds FIVE references to 0x94d800 in total: reads 0x593483 (FUN_0058fa40, `aab70()/2 <= acc`) + 0x5aab8f (aab70's own cache read), writes 0x59f0c7 (FUN_0059ec90, `= -1`) and the pair above. aab70 returns the memo unchanged when >= 0 (63 entry events, 42 with cached >= 0, no movement outside the grant path). Model reproduces 13/13 live stores from hit-time inputs (r60->62, facs 1-7: 151,176,176,203,135,241,271,151,176,168,194,128,151) and 7/7 live fields offline at r60. Formula + traps in skill code-atlas.md. Evidence: evidence/m98budget4.gdblog, scripts/m98_advance_budget.py.

## M99 (session 154, PR #106) — the producer of FUN_005aadf0's param_2: ONE caller, FUN_004f34b0
- ACCEPTANCE `python3 scripts/m99_param2.py --tag m99p3 --boundaries 2` **PASS 13/13** (m54b_clean r66->68, 41 calls, 4 hw watchpoints on [fac*8380+0x94d7f8] facs 2,3,5,6, fac3 [0x94d808] poked 0/boundary). Evidence `evidence/m99p3.gdblog`, `scratch/m99p3_seq.jsonl`.
- `.text` has exactly ONE `call 0x5aadf0` (0x4f35cb, inside **FUN_004f34b0**, the per-base upkeep tail called at 0x4f5c2e from FUN_004f5a70); 41/41 callee return pcs == 0x4f35d0.
- **param_2 = (clamp([fac*8380+0x94d6a4],-5,5)+10) x [base_record+0x104] x 10, +100 when the %100 carry overflows, / 100 (C trunc)**. The remainder accumulates in [fac*8380+0x94d808]; the pre-scale total goes to [fac*8380+0x94dc30] (store 0x4f3560). Halve leg 0x4f3513 (policy word [0x95da9c+fac*0x130+idx] & mask, FUN_00507410(0x17)); zero legs 0x4f3546 (round < mult*-5) / 0x4f3556 (round<5 && [0x94d438]<2). Model 41/41, carry 41/41, acc law 40/40, read-back 4/4.
- **NO doubling live** (ebx == param_2 40/40; FUN_005312d0 returns 0) — M98's "AI legs double param_2" RETRACTED. [fac*8380+0x94d6a4] and [base+0x104] are RECOMPUTED every round (pokes undone; FUN_004eaa10 @0x4f5ad7 rebuilds +0x104). Second live acc writer: **0x56e024 FUN_0056df40 `inc [ebx+0x94d7f8]`**.

## M100 — [fac*8380+0x94d6a4] "research multiplier" = SLOT 10 (the last) of the 11-dword per-faction block `&DAT_0094d67c + fac*0x20bc`, rebuilt from ZERO every round by FUN_005a15a0
- WRITER FUN_005a15a0(p1 = &DAT_0094d658+fac*0x20bc, p2 = the block, p3 = fac, 0, p5): reset `rep stos` 0x5a15b3 (reported 0x5a15b5); category accumulate `mov [edi],eax` 0x5a16d9 (rep 0x5a16db); source accumulate `add [eax],edi` 0x5a179e (rep 0x5a17a0), only when p5 == 0. Inputs: 4 record indices at [fac*8380+0x94d658]; 11-dword rows at &DAT_0092babc + cat*0xd4 + rec*0x2c; the 11-dword array at [fac*8380+0x94d700]; legs over &DAT_00927ac0 (type 4 clamp 0..999, type 10 halve if <0); +1 slot 5 iff DAT_00985b70's base is this fac, +2 slot 2 iff DAT_00985b98's is.
- CALLER FUN_005a1830(fac): shifts 4 dwords at 0x94d668, calls 15a0 on blocks A 0x94d67c (mult = slot 10), B 0x94d6a8, C 0x94d6d4 (p5 = 1). `call 0x5a1830` at 0x4dbf8e and 0x520904 inside FUN_005208f0 (per-player turn sequence).
- LIVE (m100mult2, m54b_clean r52->54): 12 stores / 3 pcs, all inside FUN_005a15a0; 6/6 reset->set shapes; 16 CALL events = facs 1-7 x 2 rounds, cp == fac 16/16; all 7 pokes (live+10) undone and mults restored {0,-2,0,2,0,0,-2,0}.
- The five LOADS of 0x94d6a4: 0x445abf, 0x4aac96 (clamp(-5,5)*10+100 build-time scale), 0x4f352e/0x4f3566 (FUN_004f34b0), 0x56dffa (FUN_0056df40 `mult*-5 <= round`).

## M102 (session 157, PR #TBD) — the rebuild model AT the store sites is exact: slot 10 = the four category row dwords + accumulator D10, evaluated per hit; the D-accrual is NOT per-round
- ACCEPTANCE `python3 scripts/m102_rebuild_at_hit.py --tag m102hit3 --boundaries 2` **PASS 14/14** (m54b_clean r55->57, 15 silent bps, NO pokes: 36 CAT + 9 DADD events, every stored value == old + src at the hit, chains 0 -> final, cp == fac 45/45, CLAMP 0 == predicted, ENT 0 + D10 unmoved, final == /proc {1:-2,2:0,3:2,6:-2}). m102hit1 10/14, m102hit2 12/14 on instrument only (printf escape + forward grouping, skill instrument-laws.md).
- PER REBUILD (FUN_005a15a0 block A slot 10): reset 0; 4x `+= row10(cat)` @0x5a16d9 (rows 0x92babc+cat*212+idx*44+40, indices [fac*8380+0x94d658]); `+= D10` @0x5a179e (D = [fac*8380+0x94d700]); clamp leg inert (no key-10 entry in [0x927a88+fac*1436] tables); category-skip leg inert (era globals ds:0x985b90/0x985b9c = -1; combos (3,1),(3,3),(2,1) + byte[0x95da14+304*era]==fac). Supersedes M101's lagging offline shape (#108 stays open, UNMERGED).
- D-accrual functions 0x59ec00/0x59ec90 ran 0x in 2 full rounds — the +10 drift is NOT per-round; the writer of [fac*8380+0x94d700] (pointer form?) is OPEN. Evidence: evidence/m102hit3.gdblog.
