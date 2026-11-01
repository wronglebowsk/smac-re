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

**ARCHIVED (s171):** the M32-M84e blocks (sessions 32-133) live in `docs/named-archive-m32-m84e.md`, byte-identical,
moved to keep this file under its 250,000 budget. Grep both files for a name.

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

## M102 (session 157, PR #109) — the rebuild model AT the store sites is exact: slot 10 = the four category row dwords + accumulator D10, evaluated per hit; the D-accrual is NOT per-round
- ACCEPTANCE `python3 scripts/m102_rebuild_at_hit.py --tag m102hit3 --boundaries 2` **PASS 14/14** (m54b_clean r55->57, 15 silent bps, NO pokes: 36 CAT + 9 DADD events, every stored value == old + src at the hit, chains 0 -> final, cp == fac 45/45, CLAMP 0 == predicted, ENT 0 + D10 unmoved, final == /proc {1:-2,2:0,3:2,6:-2}). m102hit1 10/14, m102hit2 12/14 on instrument only (printf escape + forward grouping, skill instrument-laws.md).
- PER REBUILD (FUN_005a15a0 block A slot 10): reset 0; 4x `+= row10(cat)` @0x5a16d9 (rows 0x92babc+cat*212+idx*44+40, indices [fac*8380+0x94d658]); `+= D10` @0x5a179e (D = [fac*8380+0x94d700]); clamp leg inert (no key-10 entry in [0x927a88+fac*1436] tables); category-skip leg inert (era globals ds:0x985b90/0x985b9c = -1; combos (3,1),(3,3),(2,1) + byte[0x95da14+304*era]==fac). Supersedes M101's lagging offline shape (#108 stays open, UNMERGED).
- D-accrual functions 0x59ec00/0x59ec90 ran 0x in 2 full rounds — the +10 drift is NOT per-round; the writer of [fac*8380+0x94d700] is NAMED at M103 (a rebuild-from-zero; the drift is a record-list append, not a D write). Evidence: evidence/m102hit3.gdblog.

## M103 (session 158, PR open, NOT ACCEPTED) — [fac*8380+0x94d700] "D" (11 dwords) is written ONLY by FUN_0059ec00: zero the 11 (rep stos 0x59ec24), then D[KEY] += VAL for every record entry with TYPE==3; NOT per round
- THE RECORD BLOCK at 0x927a9c + fac*1436: count +0x00, TYPE +0x04, KEY +0x24, VAL +0x44, stride 4 (parallel arrays) — the SAME block FUN_005a15a0's clamp loop reads (type 3 = add to D, 4/10 = the clamps). The ONLY 0x94d700 stores in .text: 0x59ec24 `rep stos` + 0x59ec68 `add [ecx*4+0x94d700],ebx` (ecx = fac*2095+key), twin inline in FUN_0059ec90 at 0x5a043e/0x5a0471.
- WHEN: 4 callers — 0x4dbf6f (FUN_004dbf40, s_RESETALLFAC cheat, UI msg 0x30077), 0x4e061b (FUN_004e03d0, msg 0x30075), 0x57ce48 (FUN_0057c550), 0x57eee0 (FUN_0057ecf0) = setup/new-fac paths. Live: 0 events at all four + the twin across 2-boundary windows while the consumer 0x5a179e consumed the poked sentinels; model == live D 8/8 on five loads; forcing FUN_0059ec00(3) at 0x520909 rebuilt fac3 to the model EXACTLY (RESET all-zero, ADD key=10 val=2, ADD key=8 val=-2).
- ACCEPTANCE `python3 scripts/m103_d_rebuild.py --tag m103d2 --boundaries 2` **FAIL 6/13** (5 runs, all failures instrument-side — s158 TRAPS). OPEN: who appends the type-3 entries. Evidence: evidence/m103d1-5.gdblog.

## M104
[0x927a9c + fac*1436] = the per-faction RECORD BLOCK: count dword, then three parallel stride-4 arrays TYPE +0x04, KEY +0x24, VAL +0x44, 8 slots each; TYPE==3 entries are FUN_0059ec00's D adds (M103). NO store in .text reaches any of the four fields by displacement (46 mentions, all scan-loop loads/cmps) — the writer must be found with a hardware watchpoint on the count. ACCEPTANCE m104w3 PASS 12/12 (scripts/m104_append_watch.py --boundaries 3, m54b_clean r57->60): 0 count-change events for facs 1/3/6 while the CONTROL watchpoint on [fac3*8380+0x94d7f8] logged 6 writes at 0x5aaef1 (FUN_005aadf0); counts read back [0,6,5,4,3,4,5,3] unchanged for all 8; 0 events at 0x59ec00 or its 4 callers; m54b_clean.SAV carries the live 100-byte count+TYPE+KEY+VAL image at 0x113b4 / 0x11eec / 0x12fc0 (facs 1/3/6, consecutive at stride 1436, fac0 base 0x10e18). VERDICT: nobody appends during rounds — the entries are load-time scenario data, so D and the multiplier's D leg are frozen after setup. OPEN: the setup writer (save loader vs the 1436-byte template copy at FUN_0057c550/FUN_0057ecf0); the TYPE 0 / TYPE 2 consumers.

## M105
[0x927a9c + fac*1436] is BUILT AT PROCESS START by **FUN_005791c0** (terran.exe, 3112 B, shard_014): an append loop whose count store reports at **0x579b12 = store+2**. At pid discovery the counts are all 0; gdb logs 15 count increments (fac1 1->6, fac3 1->4, fac6 1->5) that land EXACTLY on the m104 image [0,6,5,4,3,4,5,3], and the CDROM screen is then quiescent for 4 min. The save loader stores NOTHING to the counts in the load window (0 CNT events while the ROUND control fires at 0x64bfa3 = FUN_0064bf70) and 0 events hit the 8 M103 setup sites (0x57c550 0x57ecf0 0x59ec00 0x59ec90 0x57ce48 0x57eee0 0x4dbf6f 0x4e061b) — the template-copy hypothesis is DEAD. ACCEPTANCE m105s4 PASS 17/17 (`scripts/m105_setup_watch.py --relaunch`: arm before any screen, poke -77 while armed at the quiescent screen, load). OPEN: the -77 was gone at the end with 0 load-window events — the load restores the region by a path a hw watchpoint cannot see (post-arm thread DR / out-of-process page write / MAP_FIXED remap). CLOSES M103's "who appends the type-3 entries". Evidence: evidence/m105s1-4.gdblog.

## M106
The load-window restore of [0x927a9c + fac*1436] is **read() STRAIGHT INTO THE REGION**: a kernel copy_to_user, no ring-3 store, so a hardware watchpoint CANNOT see it (M105's open question closed). The .SAV fd has NO open() in either strace log — the driver opens the file and Wine hands the fd to terran over **SCM_RIGHTS**; name it by the **TAIL-AND-EOF LAW**: the fd-run that contains a read returning the file's tail (242,539 mod 4096 = 875 B) and ends with a 0-byte read = EOF. Inside that run: **read(0x5, 0x927c84, 0x2000) = 0x2000**, span 0x927c84..0x929c84, which covers the fac1/fac3/fac6 counts (0x928038, 0x928b70, 0x929c44) M105 armed watchpoints on; the block HEAD (488 B, fac0) and TAIL (2,808 B, fac7) arrive through the CRT's 0x1000 stdio buffer at 0x40a5628, i.e. ring-3 stores — that is why the armed set was unlucky. Same run also reads 0x94e104+0xf000, 0x40a75b0+0x15000, 0x986d51+0x2000, 0x98af49+0x6000. ACCEPTANCE m106r7 PASS 15/15 (`scripts/m106_load_restore.py --tag m106r7`): VMA list identical + 0 mmap/mremap/munmap covering the region; soft-dirty cleared at the baseline then SET on 4/4 region pages; 0 process_vm_writev and 0 pwrite to a /proc/pid/mem fd; all 8 -1000..-1007 count sentinels replaced by the save image; exactly one candidate survives = C1-kernel-write-via-read. OPEN: why each fread's DESTINATION is where it is (the save chunk table / the loader's seek sequence); the positioned pread64 0x17-byte probes that ride inside the run; the 0x1bc heap chunks that precede the region chunks.

## M107
The save chunk map is **HARD-CODED in FUN_00596850**: 30 fread legs (25 `push <size>` immediates + 5 counted), and the file carries **NO (address,size) table** — 0 of the 20 static destinations occur as u32 LE in any of 9 saves and 0 (dest,size) pairs are adjacent, so the map is code, not data. **Block A is version-gated** (`cmp ds:0x985dbc,3` @0x596a43; 0x985dbc = header 0x985ab8 + 0x304 = file offset 772): u32@772 = 0 on 9/9 saves and the r7 strace shows the **malloc'd 0xe5e0 leg** (86,016 B at heap 0x40a75b0) — the static 0x105e0 leg never runs. Live immediate legs total **137,464 B** → **105,075 B** residual for the counted legs (count-prefix 0x927538 → 0x930d7c; [0x985af0] → 52n at 0x933278 + 48p malloc; [0x985af4] → 304m at 0x95da10). Loudest read is a malloc'd 86,016 B at heap 0x40a75b0. **RETRACTED by M108**: the gate claim below is WRONG — live [0x985dbc] = 9, so the STATIC 0x105e0 leg is the live one and the 105,075/old-path numbers are withdrawn; the flat 38,035 residual is real. ACCEPTANCE m107c3 PASS 7/7 (`scripts/m107_chunkmap.py --tag m107c3`, offline, 9 saves). OPEN: who SETS [0x985af0]/[0x985af4] (no 4-byte read site targets them — a derivation, not the raw header).

## M108
[0x985af0] is the **UNIT count** (67) and [0x985af4] the **BASE count** (18) of the loaded save, landed by ONE basic block — **0x598470 / 0x598476, 6 B apart — inside FUN_00598340**; 5 stores exist to 0x985af0 (0x4e10d8 reset, 0x4e11cc zero, 0x598476 load, 0x5a109e, 0x5abc5d) and 6 to 0x985af4 (0x4e10de, 0x4e11d8, 0x4e515d, 0x598470, 0x59b842, 0x5a1098). Read-back: the 304-byte array at 0x95da10 holds exactly 18 records with printable names. **RETRACTION of M107's gate claim**: live [0x985dbc] = **9** (>= 3), so the **static 0x105e0 block-A leg runs**, not the malloc'd 0xe5e0 one — 0x985dbc is a runtime field, NOT file offset 772; M107's 105,075/old-path numbers are withdrawn. **The chunk map does NOT close**: 38,035 B residual vs 12,172 counted = **25,863 B unaccounted**, and the r7 load's largest read is a **malloc'd 86,016 B at heap 0x40a75b0** (= 42 x [0x92a38c] = 2,048). ACCEPTANCE m108c3 PASS 6/6 (`scripts/m108_count_sources.py --tag m108c3`).

## M109 (RUN, NOT ACCEPTED)
The counted legs MEASURED LIVE on m54b_clean (6 silent bps before the load, `scripts/m109_leg_sizes.py --tag m109l2`): count-prefix leg **176 B**, **52n = 3,484 = 52 × 67**, **304m = 5,472 = 304 × 18** — the model from [0x985af0]=67 units / [0x985af4]=18 bases is EXACT on both. **0x59738b (the 48p leg) never executes** for this save and **its malloc (0x596ab7) never fires either** — that whole 48·n path is gated off here — and **0x5979f8 is a 4-byte read, not a tail section**. The map does not close: 204,504 immediate + 9,136 counted = 213,640 vs 242,539 → **28,899 B unaccounted**, because the 30 legs are CONDITIONAL (gates at 0x596a43 `ds:0x985dbc,3`, 0x5974b7 `ds:0x985dbc,0`, 0x5974d3 `[0x985af4]`). LAW: at an fread call the stack holds [esp]=dest, [esp+4]=size, [esp+8]=count, [esp+0xc]=FILE* — read the size from `*(int*)($esp+4)`, never a clobbered register. **CENSUS (s169, `scripts/m109_leg_census.py --tag m109c4`): one clean load executes 23 read sites = Σ(size×count) 149,380 B of the 242,539-B file — the loader's own reads are only 61.6%; the other 93,159 B is issued by 105 call sites OUTSIDE [0x596850,0x597a6b] (the 86,016-B heap read is one). A chunk map from FUN_00596850 alone can never close.**

## M110 (RUN — 99.94% closed, nothing merged)
Six ranges, 182 static bps, one load (`m110a2`): **45 executed sites, Σ = 242,383 of 242,539 → 156 B short, coverage CONTIGUOUS 0..242,383.** The MAP is named and it sits mid-file: `0x5822a7` **2,724 B** header at offset **79,364**; `0x5822f2` grid **90,112 B = 64×64×22** at **82,088**; `0x582318` **91 B** trailer at **172,200** — m54b_clean is a **64×64** map, which is why the 80×80 dims signature was never in it. **The old 86,016-B heap read is the grid minus its first 4,096-B stdio block (90,112 − 86,016 = 4,096)** — that closes M107/M108's open item. The last **156 B** (242,383..242,538) are a 6-dword table `[3,0,0,-6,32,32] … [7,…]` plus three trailing dwords, read by a site outside the six ranges (CRT fscanf 0x62b6xx/0x62c3xx excluded on purpose). **The 0x59666d/0x5966c1 pair is a 9-iteration loop** (18 × 4 B): each iteration writes a 4-B count and a 4-B value into `a+0x1dd78` / `a+0x1dd74` of a DIFFERENT structure, and 7 of the 9 destinations step by a constant **0x224B8 = 140,472 B** (`0x3b7d7a8 → 0x3b9fc60 → … → 0x3c4b3f8`), with `0x915758` first and `0x8eb7c4` last out of line — i.e. per-entity records ~140 KB apart, not one section. **CROSS-LINK to M108**: `[0x92ae14]` — read there as an unexplained heap pointer `0x40a6660` — IS the grid pointer: `0x5822f2` reads 90,112 B **into `0x40a6660`**, and the 2,724-B map struct lands at `0x92a378` with the grid pointer at **+0xA9C (2,716)** of it, i.e. the last-8-bytes-but-one field of the header struct.

## M109 (s168, RUN, NOT ACCEPTED — no green acceptance, nothing merged)
- The save loader's 30 `call 0x64cc00` legs are ONE OF FOUR readers: 0x596470/0x596540 = CONVERTING (malloc size*count, read, copy), 0x64c9a0/0x64cc00 = DIRECT; the pair is chosen by [0x926a14], set at 0x5968a7 = ([0x985ae8] & 0x10000000). The count arg is ALWAYS 1 -> bytes == size.
- Leg gates are the loaded VERSION [0x985dbc] (live 9): 0x59689a >=4, 0x596a43 >=3, 0x597159 >=3, 0x597246 >=6, 0x5972cb >=0, 0x5974b7 >7, 0x597542 <3, 0x5975e6 = [0x985ae8]&0x10, 0x597650 >=1, 0x5976c8 >=2, 0x597733 >=7.
- 0x5971c8-0x597244 = LOOP: 8 x read 0x680 with stride 0xd00 while edi < 0x991588 (the version<3 sparse form of 0x6800@0x98ad88); M107's 204,504 double-counts 1,664.
- 0x5973bc-0x597495 = 48->52 record expansion (0x30-byte source -> 0x34-byte records at 0x93327a, [0x985af0] iterations), gated version<0 -> 0x59738b never runs.
- 0x596620(a,stream) = 4-B read into a+0x1dd78 (8 calls off the dword table at 0x7cdecc + 1 with 0x8cda4c) = 36 B.
- 105 reader call sites exist outside FUN_00596850 -> the 30-leg table is not the whole read set. OPEN: the closure arithmetic, and who reads the malloc'd 86,016 B. Harness scripts/m109_leg_gates.py.
## M111 (s171, RUN, NOT ACCEPTED — the tail's reader is unnamed and the census model is VOID)

Command: `python3 scripts/m109_leg_census.py --tag m111b3 --relaunch --ranges 0x400000-0x62afff`
(190 static call sites to the four readers = 221 total minus the 31 CRT-band ones).
Result: 90 sites executed, 0 gdb errors, counts 67/18 (the load ran), **sum(size*count) = 243,007 vs file
242,539 → over by 468 B**. An order-based `file_off` column that over-runs the file is not a partial map, it is
an INVALID model: the executed set includes three 160-B CRT reads (0x62ae0f/0x62aec8/0x62af05 into 0x7cda1c,
0xbe8c10, 0xbefd3c) and a 9-iteration per-entity loop of 6 x 4-B reads into heap (0x3b7d7a8 .. 0x3c4b420,
stride 0x224B8) — the M110 pair 0x59666d/0x5966c1. **M110's "contiguous 0..242,383" is RETRACTED as a closure
claim**; it measured an un-armed site set.
Two failed instruments: m111b1 detached after 3 events (no SIGUSR1 handle), m111b2 armed the 31 CRT sites and
starved (0x62b8f0/0x62b935 8,277 hits each in 12 min, ZERO loader hits, stream frozen = m109g3).
Read-back (523 MB of /proc mem, no gdb): the 156-B tail is NOT present verbatim; its 12-B row signature
`fa ff ff ff 20 00 00 00 20 00 00 00` appears exactly 6x at **0x34f0000** — records restored per record, no
bulk 156-B read. Next shape: filter every bp by the save FILE* (set $savefile at 0x596850, `[esp+0xc]`).
## M112 (STATIC PASS, s171 cont.) — the last 156 B is a fixed TRAILER, write-only by construction

Nine saves (m54b_clean 242,539 B + 8 autosaves 242,815..243,691 B) share their final **152 bytes exactly**; only
the last dword differs. Layout: 5 x `[id,0,0,-6,32,32]` (id 3..7), `[1,1,0x80000080,-14,32,32]`, `[800,387,X]`.
Immediate 156 (0x9c) appears 13x in the EXE, **never** in 0x58xxxx-0x59xxxx (the two `push 0x9c` are 0x4b3476 /
0x4b3e3d), so no loader code can size a 156-B read. Not restored: 0xbe27b0/0xbe27b4 (the loader's last read
dests, sites 0x597a19/0x5979f8) hold unrelated values; the exact 156 B is absent from 523 MB of memory; its 12-B
row signature is 6x at heap 0x34f0000 and in 0 of the 24 files in programs/.
Acceptance to close (unspent): an autosave (trailer at a different offset) under a FILE*-filtered census,
prediction sum = filesize - 156.
CORRECTION (s171): the loader pushes a 152-B immediate at 0x597716; its dest 0x92bf58 holds
[9999,9999,0,0,2100,2600], NOT the trailer — so the trailer's reader is still unnamed, but "no constant can size
it" is too strong (152 = 156 - 4). The trailer's offset varies per save (file sizes 242,539..243,691).

## M112 (attempt m112a1, s171) — FILE* filter armed (savefile=0x6a79a0), sum still over-runs; census cannot decide

`m109_leg_census.py --tag m112a1 --relaunch --ranges 0x400000-0x62afff --filter-file --save m112auto1.SAV`
(autosave copy 242,927 B, trailer at 242,771, counts 68/19): 83 legs, 0 gdb errors, **sum 243,071 vs 242,927 ->
OVER by 144** (no repeated (site,dest,size) group). Pre-registered predictions H1 242,771 / H2 242,383 / H3
242,927 — none matched. With m111b3 at +468 (unfiltered, m54b_clean) the conclusion is that the cumulative
`file_off` column is invalid in this harness, not that the trailer is read or unread. Read-back of the final
group's destination 0xbefd3c is a shared CRT stdio buffer (other files overwrite it), so it is not evidence.
NEXT INSTRUMENT: poke a unique pattern into the trailer of a save copy, load, scan /proc/<pid>/mem for it —
identification, not byte counting. New `--filter-file` flag added to the census (captures the FILE* at 0x596850,
logs only `[esp+0xc] == $savefile`, exits 5 when the filter never arms).
## M112 RESOLVED (s171, m112p1) — the 156-B trailer IS READ; the per-entity loop is its reader

`scripts/m112_trailer_poke.py --tag m112p1 --relaunch`: 10 dwords of 0xCAFEBABE planted in the five trailer
rows of a save copy (40 B changed, size unchanged, magic absent from the original) -> load rc=0, counts 67/18,
522.9 MB scanned, **41 hits**, structural ones at 0x3bc2110 / 0x3be45c8 / 0x3c06a80 / 0x3c28f38 / 0x3c4b3f0 =
the m111b3 "pollution" loop destinations minus 8. Reader = the 6-site per-entity loop (0x59666d, 0x5966c1,
0x596715, 0x596769, 0x5967bd, 0x59683b) restoring each `[id,0,0,-6,32,32]` row (id 3..7) to heap records
0x915758, 0x3b7d7a8, 0x3b9fc60, 0x3bc2118, 0x3be45d0, 0x3c06a88, 0x3c28f40, 0x3c4b3f8 (stride 0x224B8), 0x8eb7c4.
**M110's "contiguous 0..242,383 / 156 B unread / 99.94%" is RETRACTED**: the sum over-runs (+468, +144) because
the cumulative `file_off` column assumes file order while these bytes are touched twice (bulk + per row).
## M113 ACCEPTED (m113map1/2/3, s171) — .SAV offset->dest anchors by poke: 20/20, then 24/25 and 19/20

`scripts/m113_save_map.py` plants 0xC0DE000i at known file offsets in a save copy, loads it, and finds each marker in
memory. m113map1 (step 16384): **20/20 found**, counts 67/18 — three slope-1 runs (16,384..65,536 ->
0x951104..0x95d104; 98,304..163,840 -> 0x40aa5b0..0x40ba5b0; 196,608..212,992 -> 0x98bf49..0x98ff49), the 90,112-B
grid at 0x40a6660. m113map2 (2 KB bands): 24/25 — block A -> block B bracketed 66,048 (0x95d304) / 68,096
(0x927684); grid -> next section bracketed 171,192 (0x40bc268) / 173,240 (0x986209) with the 91-B map trailer
inside; 174,000..180,144 -> 0x986501..0x987d01. m113map3 (128 B): 19/20 — the 52-record array maps 1:1 from **file
222,783 -> 0x933278** to the byte, and the single "absent" marker MOVES between runs (223,048 -> 0x933351, 223,152 ->
0x9333E9) with present neighbours: a normalised field, not an unread region.
## M114 (s171, zero box time) — restore fidelity by diff: 10/12 sampled windows are byte-identical

Diff of the loaded game against the poked save at `dest = off + k` (1 KB windows, 12 anchors): block A k=0x94D104,
grid k=0x40925B0, post-map section k=0x95BD51, 196,608/212,992 k=0x95BF49, 52-records k=0x926635. Clean windows:
16,384 / 49,152 / 80,384 / 114,688 / 163,000 / 174,000 / 180,144 / 196,608 / 212,992 / 227,144.
**Rewriting is confined to**: the map header TAIL (file 81,408..82,100, 665 B contiguous) and the block A TAIL
(file 67,080..67,143, 238 B on a 16-B stride, 2 B per hit = a per-record u16 array). The 52-record array differs
in exactly 2 dwords: 222,831 `0x0003FFFF -> 0` (cleared) and the poked field at 223,152 top byte `0xC0 -> 0xD6`
(normalised). Block B's base is file **67,852** -> 0x927590 (the documented 67,840 is 12 B early).
CORRECTION (s171, M114): the "two rewritten tails" (block A 67,080..67,143 and map header 81,408..82,100) are
RETRACTED as a k-straddling artifact — those windows cross a region boundary and were diffed with one region's k.
With per-region k: block A (66,048..67,840, k=0x94D104) 0 diffs; block B (67,852..79,328, k=0x916C84) 0 diffs;
map header (79,364..82,088, k=0x916D6C) 2 bytes, both at the FIRST offset; grid (82,088..172,200, k=0x40925B0) 10
bytes starting at the FIRST offset. The .SAV is restored 1:1; the only divergences are those leading bytes plus the
52-record array's 2 dwords (222,831 cleared, 223,152 field normalised).

## M115 (s171) — the guard is now code: save_diff.py refuses boundary-crossing ranges; the census proves a clean box

`scripts/save_diff.py` (+ `test_save_diff.py` PASS 7/7): regions from the poke anchors, KNOWN section boundaries
67,852 / 82,088 / 172,200 / 172,291 / 222,783 (each derived from an anchor plus its documented dest base), refuses
a range that crosses one and names it — M114's two windows are refused by the tool. `m109_leg_census.py` now
SIGTERM/SIGKILLs gdb by pid after its verdict, reads `TracerPid` into the log header and exits **8** if the box is
not clean. `m113_save_map.py --verify` (default ±8 B `local_1to1`): every anchor is checked against the file
locally — live check 64,000/68,096/81,408(±64)/82,432(±64)/174,000 all 0 diffs.

## M116-M118 (s171) — the band-flag gate: BYTE test at 0x5aaf7f, reached 17x/turn, never taken, inert BY CONSTRUCTION

`test BYTE PTR [esi+0x94d430],0x40` exists once (0x5aaf7f, FUN_005aadf0+0x18f, take 0x5aaf88); one turn reaches it
**17x** (factions 1..7, faction 0 never) and never takes it. No dword OR sets 0x40; of **22** `or al,0x40` register
sites the only one reaching a flag store (0x4dc226 -> 0x4dc296) RELOADS the word and masks 0xfc3fffff, so the bit never
lands — that block TRANSLATES source bit 0x800000 -> derived bit 0x40 into ds:0x99aa38, and nothing moves it back. Bit
0x40 is clear for all 8 factions in **all 12 saves**, and block A restores 1:1 (M114). So the M89 second ask cannot
fire on this build/save version.
**STRIDE TRAP:** NAMED's `f*8380` is **DECIMAL 8,380 (0x20BC)**, not hex 0x8380 — M116's first live table divided by
0x8380, sampled factions 0,4,8.. and wrongly reported "0xFFFFFFFF for faction 1" (RETRACTED; true words
0,0,0x04000000,0,0,0,0x10000000,0).
## M119-M123 (s171, all PASS) — five fields settled statically: stride 0x30, bit 0x20 @0x531782, 0x98adee read-only, the 0x1c copy, 0x94d78c one dword

`scripts/field_census.py`. **M119** 0x984d38 stride = **0x30** at 52/52 indexed sites (45 `lea [v+v*2]+shl 4`, 7
`imul 0x30`), 0 standalone `shl 4` -> M67's -3/-6 conflict was the ×48 tail, not a second stride. **M120** bit 0x20 of
[ebx+0x98adb8] set iff faction dword `0x94d448+inner*4` has bit 0 (test 0x531778, je 0x531780, or 0x531782); index
`esi*2095+edi` = 8,380-B stride folded in. **M121** ds:0x98adee: 7 `movsx` readers, 0 writers any width, no
neighbour-dword access -> load-only save/scenario field. **M122** the 0x1c loop is a COPY 0x91cb80 -> 0x98aaf8
(24 × 28 B, exact), never touches 0x984d38. **M123** ds:0x94d78c: 72 refs (48 `[reg+disp]`, 24 `[reg*4+disp]`, 6
writes); all 24 array-form sites are 2095-scaled -> one field, two encodings, no second array.

## M124 (s171) — ds:0x926bd4 = the UPKEEP-SYNCH PHASE CODE {0 idle, 1/2 synching}

4 writes, 2 tests in the image. `=1` at 0x5210aa (loop entry, after 0x744f24/0x91c658/0x91c630 are zeroed), `=2` at
0x521297 after the print at 0x68ea94 ("Skipping upkeep synch"), back to 0 at 0x5213c7 after the second (0x68eacc) with
counter 0x91c630 incremented, `=setne al` at 0x57f8c5 (FUN_0057f740). Both readers are `cmp [0x926bd4],1`: 0x5aaa6f
(FUN_005aaa20, after the "Earning a Tech" print at 0x693884) and **0x5aafe4 in FUN_005aadf0**, where phase==1 OR
[fab+0x94d7fc]<0 skips the tail — the named reason the band-flag tail is skipped during upkeep synch.

## M125 (s171) — ds:0x920434 = the ID published by the window-reset entry (NOT a faction field)

15 writes / 619 reads. 12 of 15 writes sit inside a reset sequence (`mov ecx,0x91db70; call 0x4e25e0` clears the widget
object; preceded by [0x91f738]=0xff, [0x91f6e0]=esi, `rep stos`, `call 0x581280`); the value is the caller's id
(esi/ebx/edi) or a constant. **0 references use a faction-scaled (8380) base** and the readers compare it to ids
(0x546887). It is the subject id a reset publishes, not per-faction storage.

## M126 (s171) — 0x59f0c7 INVALIDATES the memoized advance threshold ([fab+0x94d800] = -1)

Inside FUN_0059ec90, right after `[ebx+0x94d650] += [eax+0x927a78]+ecx+ds:0x985afc` and `[ebx+0x94d654] = 0`. Callers:
0x5a0b39 (FUN_005a0aa0), 0x5a123e and 0x5a1277 (FUN_005a0fa0); the first zeroes the DIVISOR [edx*4+0x94e488] just
before the call. The memo (M98) therefore dies exactly when a faction's base count changes.

## M127 (s171) — the type-record PLAN byte 0x98adb2 (= 0x98ad88+type*52+42) has 369 readers; "zero sites" RETRACTED

149 of them are the folded `[reg*4+0x98adb2]` form (reg = tid*13 -> tid*52), 0 use a literal `+0x2a]`. Top readers:
FUN_00502cd0 (48), FUN_0055f650 (33), FUN_004f6030 (24), FUN_0055c920 (23), FUN_00585720 (17), FUN_00556690 (15, the
base-count recompute), FUN_00595b10 (14, unit_type_builder), FUN_0059ce10 (10). M67's plan-descending sort key is
therefore supported statically; the registry's "zero sites read plan byte +42" was a literal-grep artifact.

## M128 (s171) — the chooser pump's PRE/POST-seek pair, in code: 0x497707 (pre), 0x497717 (seek), 0x49771c (post)

`mov ecx,[eax+0xa774]` (0x497707) + push happen BEFORE `call 0x4026b0` at 0x497717; after it the object is re-derived
(`mov ecx,[ebp-0x10]; add ecx,0xa780` at 0x49771c/0x49771f) and `call 0x495480` + `and eax,0x20` (0x49772a) read the
post-seek flag word. Any print at 0x497704 shows the PREVIOUS node; 0x49771c is the first instruction that sees the new.

## M129 (s171) — FUN_00546800's three-condition guard CONSUMES 0x92044c bit 0x2

Proceeds iff `[0x94d448]` bit 0x8000000 AND `ds:0x920434 != ebx` AND `[esi*4+0x92044c]` bit 0x2, then zeroes that byte
at 0x5469d3. 0x92044c's bit 1 is a per-record "already consumed" marker for this path, not persistent state.

## M130-M132 (s171, all PASS) — chooser dispatch @0x54eafc (case 7 = 0x54ec58), 0x920434 is not a record field, 0x92077c = a mode code

**M130** `FUN_00546800` 0x54eaeb: `call 0x542ea0` -> `cmp eax,0x7` -> `ja` -> `jmp [eax*4+0x54ef34]`; table
`[0x54ed3f, 0x54eb03, 0x54eb03, 0x54eb29, 0x54ec34, 0x54ec40, 0x54ec4c, 0x54ec58]` (1&2 share 0x54eb03; 4/5/6 =
0x54ec34/40/4c). **CASE 7 = 0x54ec58** sets `ds:0x920700 = 0xc` and `ds:0x92077c = 1` — the only case writing a pair.
**M131** 0x92044c: 24 refs, 24 folded (`[reg*4+..]`, tid*13 -> tid*52); 0x920434: 634 refs, **0 folded** -> standalone
global, NOT the +0 field of that record. **M132** ds:0x92077c: 4 writes (1,1,ebx,eax), 9 tests vs 1/3/7, a copy vs 6 at
0x54eb1b; partner 0x920700 (8 writes) set in the same body -> a (state, mode) pair; meaning unnamed (no strings nearby).

## M133-M142 (s171, all PASS) — ten censuses: the dispatch key, the 1436-byte stride, and eight field shapes

`scripts/m133_m142_census.py`. **M133** FUN_00542ea0 (1456 B, 341 insns, 28 callees, only call site 0x54eaeb) is the
chooser's dispatch key. **M137** its index folds to **359 dwords = 1436 BYTES** (0x542ed9-0x542eed: lea [v+v*4] ->
lea [v*9] -> shl 3 -> sub v -> shl 2) loading `[eax+0x927590]`; 1436 == M104's 0x927a9c+fac*1436 stride, same record
family, base 0x50c lower. **M134** ds:0x920700 UI state code (31 refs/8 writes; tests 6, 8, 0xd; case 7 sets 0xc).
**M135** ds:0x94d7fc per-faction counter, -1 = unset (its `jl` at 0x5aafd8 is the other half of M124's skip).
**M136** ds:0x927a78 = input of FUN_0059ec90 only (2 refs, 0 writes). **M138** 0x94d650 accumulator (261/34) vs
0x94d654 companion (13/2, zeroed at 0x59f0c1). **M139** ds:0x91c630 upkeep-synch counter (27/34 refs in FUN_00521070,
`inc` at 0x5213c6). **M140** ds:0x985afc read-dominant (336 refs / 5 writes) = run state, unnamed. **M141**
FUN_00495480 (21 insns) cached-flag getter with a null guard (0 = no cache object, not "flag clear"). **M142**
FUN_004026b0 (`ret 4`, 201 B) = LIST SEEK: index >= [obj+0x10] rejected, nodes walked via [node+0xc]/[node+0x10],
cursor stored at [obj+0x14] — the mechanism behind M128.

## M143-M162 (s171) — faction-block field ATLAS: the 20 most-referenced `+0x94dXXX` displacements

Generated by `scripts/m143_m162_atlas.py` into **`docs/field-atlas-faction.md`** (regenerate, do not hand-edit). Rule:
count every `+0x94dXXX` displacement in the objdump (150 distinct), take the top 20 by references, record refs / writes
/ shape / constants / tested values / containing functions / NAMED presence.
Headline shapes: `0x94d448` 653 refs, 27 writes, 139 functions (faction flag word; bit 0x8000000 gates FUN_00546800,
M129) · `0x94d650` 261/34 (M138 accumulator) · **`0x94d434` 196 refs, 1 write** (near-constant: many readers, one setter)
· `0x94d430` 168/18 (band-flag word, M116-M118) · `0x94dc84` 89 · `0x94d80c` 78 · `0x94d468` 75 · `0x94d438` 72 ·
`0x94d78c` 72 (M123) · `0x94d81c` 62 · `0x94d554` 57 · `0x94d734` 57 · `0x94d758` 51/12 · `0x94d488` 49/22 ·
`0x94d7fc` 47 (M135) · `0x94d818` 46 · `0x94d754` 44 · `0x94d814` 42 · `0x94d4e8` 40 · `0x94d4a8` 38/26.
These are SHAPE entries; a `—` in `in NAMED?` means the field is genuinely unnamed.

## M163-M165 (s171, all PASS) — 0x94d434 is a RANK written once; 0x94d80c..0x94d81c is one 20-byte struct; 0x94d554+55c an 8-byte pair

`scripts/m163_m165_structs.py`. **M163** the ONLY writer of `[faction*8380+0x94d434]` is 0x59ac8a in FUN_0059aa00, an
init loop that ranks factions: scan 0x926a7c-0x926a98 for the max, store -1 in the winner's slot 0x926a78+n*4, write
the rank and `dec ebx` (196 readers, 1 write, tests vs 2/4/5/6). **M164** 0x94d80c/10/14/18/1c: 11 (fn,base) pairs
address all five off ONE base -> one 20-byte struct (FUN_0040b960, 004dc100, 004e78e0, 004f6030, 00522b70, 0055a940,
00574370 x2, 0059ec90 x2). **M165** 0x94d554+0x94d55c = 8-byte pair (5 pairs; FUN_00546800 with 3 bases); 0x94d488 is
separate (17 base-pairs, one shared function).

## M166-M168 (s171, all PASS) — the rank is an ordering test; the 20-byte struct = header + payload quad; 0x94d488 is a derived cache

`scripts/m166_m168_roles.py`. **M166** 0x94d434: 196 refs, 92 `cmp` vs 2/4/5/6/7, ranking input = the 7-dword table
**0x926a7c** (2 refs: 0x59ac55 in the init loop, 0x532150 in FUN_00531df0), top entry EXCLUDED by `-1` at 0x59ac72 into
0x926a78+n*4 -> an order among 7 candidates, one discarded; what is ranked = unnamed. **M167** the 20-byte struct at
0x94d80c: +0x00 = header (writers FUN_004dc100 x3 + FUN_0059ec90 x3; consts 0/1/-1; 7 tests), +0x04/+0x08/+0x0c/+0x10 =
payload quad written together by FUN_004dc100/00510230/00512b40/00516b80/0059ec90. **M168** 0x94d488: 22 writes over 9
functions vs 49 refs and 1 comparison = derived/cached (recomputed by many paths), not authoritative state.

## M169-M171 (s171, all PASS) — 0x926a7c is totalled; FUN_00531df0 is the aggregator; FUN_004dc100 is a BIT-DECODER

`scripts/m169_m171_aggregate.py`. **M169** 0x926a7c's second reader (0x532150, FUN_00531df0) is a per-faction loop at
stride 0x20bc stepping the table by 4, with `ds:0x9204ac++` (count) and `ds:0x9204c4 += [eax+0x926a7c]` (sum).
**M170** FUN_00531df0 (6459 B, 1905 insns, 17 call sites) = per-faction AGGREGATOR: `1<<f` mask (`shl edi,cl`), gate
`cmp [ebx+0x94d434],0x5` (the M163 rank as a `< 5` threshold), accumulators 0x9204ac / 0x9204c4 / 0x920720 / 0x9204c8.
**M171** FUN_004dc100 (647 B) = BIT-DECODER: one byte in AL -> `[+0x94d810/14/18/1c] = setne(al&1/2/4/8)` (four boolean
dwords), header `[+0x94d80c]` = tristate 1/-1/0 from al&0x10 / al&0x20, and al&0x40 -> `or [+0x94d430],0x800000`.

## M172-M174 (s172, all PASS) — FUN_004dc100 is a SAVE-SECTION WRITER; the count/sum consumers; the tristate as a signed modifier

`scripts/m172_m174_savewriter.py`. **M172** FUN_004dc100's 2 callers are arg-free dispatch legs (FUN_00512b40 0x51500f,
FUN_00516b80 0x517eb6). The byte is the shared scratch **ds:0x99aa38** (74 refs / 33 stores; 19 stores in the 0x41a9xx
UI-build block FUN_0041a8f0) — NOT a caller argument (M171's "one byte arrives in AL" is RETRACTED): the PACK leg
(0x4dc1a4-0x4dc279) rewrites 22 `or/and al,ah` bits from +0x94d80c..1c + [esi+0x94d430] bits 0x800000/0x400000/0x1000000/
0x2000000 + [esi+0x94f4b0] bit 0x20, stores the byte, writes it via the tagged writer 0x6267a5 (18 sites, 12 in the
0x4d9xxx-0x4e1xxx save band); the DECODE leg (0x4dc29c, after the write's `jl` gate) reloads the SAME global and rebuilds
the struct. Context opener 0x4d9fb0 has EXACTLY 4 callers: FUN_004dc100/0x4dc390/0x4e0260/0x5a2930.
**M173** 0x9204ac (count) consumers = 0x53346c (in FUN_00531df0: `count<2` -> `table[ebx] >= 3*(sum+table[ecx])` ->
`rank<6`), 0x53a9cc (FUN_0053a9c0: `count + ds:0x920720`), 0x54d30d (FUN_00546800: `count != 0`); 0x9204c4 (sum) has the
ONE consumer 0x533478. Each has 2 stores (zero + loop RMW). **M174** 0x94d80c: 7 tests in 4 fns (2 vs 0, 4 vs 1, 1 reg
`cmp [eax+0x94d80c],ecx` @0x5520cd) + 7 arithmetic uses (`sub` x6 across FUN_0053cb20/0x546800 x2/0x5551e0/0x55f650,
`add` x1) — a 1/0/-1 SIGNED MODIFIER in scoring; FUN_00531df0 reads it as |value| (0x53206f).

## M175-M177 (s173, all PASS) — FUN_00531df0's demand set, its (block, record, mode) convention, and the primed stamp

`scripts/m175_m177_aggcallers.py`. **M175** 17 call sites in 13 owners: FUN_00546800 x2, FUN_005551e0 x2, FUN_004a5eb0 x2,
FUN_00534fa0 x2 + singles FUN_004282d0, FUN_0043ff20 (wrapper, arg1=`ds:0x91b5b4` current faction), FUN_00533e70,
FUN_00534180, FUN_005344c0, FUN_00535700, FUN_00535c60, FUN_0055f650, FUN_0058fa40 (save path, near a 0x626634 call).
**M176** args = (faction BLOCK base at stride 0x20bc, record base, mode): prologue `mov esi,[ebp+8]`; 10/13 callers build
the base with the folded *8380 chain (shl 6 / lea [i+i*2] / shl 4 / sub i); arg3 reloaded at 5 sites — 0x532194
`test eax,eax; je` gates `mov eax,[edx+0x94d4a8]; mov ds:0x9204b0,eax` (mode!=0 EXPORTS the stamp); 12/17 push 0, 1 pushes 1.
**M177** [block+0x94d4a8] = per-faction LAST-RUN stamp vs the round counter ds:0x985afc: 3 sites prime it pre-call
(0x533eec/0x53420e/0x534522); 6 `sub reg,[blk+0x94d4a8]` age tests, one GATING a call (0x569401 `cmp edx,0x10; jl` skips);
38 refs = 26 stores + 5 loads + 1 lea + 6 subs.





## M178-M180 (s174, all PASS) — the GOVOPTIONS bit filter, the save band's staging slot, the two aggregate globals
**M178** FUN_0041a8f0 0x41a9xx = 19-bit pack/unpack of `[ds:0x8f0d60+0x38]` through ds:0x99aa38; unpack restores
the INVERSE permutation (19/19, all destinations that same field); `and ecx,0xf000000` (0x41abdc) keeps only bits
24-27 -> source bits 1,2,3,4,8,14,28,29,30 are DESTROYED; rebuilt dword published to `[fac*8380+0x94d600]` (0x41ad94).
**M179** ds:0x99aa38 = the tagged-record STAGING slot (third field of the 0x99aa1c/0x99aa20 pair, 637 stores each):
33 stores / 14 functions, 9 sit directly before `call 0x6267a5` (args = name, size, extra): 7 pass size 0x41,
the TECHRANDOM pair 0x1 (0x510289/0x5170ae); names read out of terran.exe
= ASSEMBLEGROUP 0x68c774, AIEDITOR 0x68c80c, AIEDITOR2 0x68c818, RULES 0x68c824 + 0x691e30, SCENRULES 0x68c82c,
SCENVICTORY 0x68c838, TECHRANDOM 0x68db28, GOVOPTIONS 0x6899ec, EDITVEH 0x68c87c (the exe NAME table, not file bytes).
FUN_00518c50 = set/clear scratch BIT (arg1 = index). Band = scratch bits 0..17 (FUN_0041a8f0: 18); the 6
leg-sequence writers read ascending; 0x4dc5f0 == 0x57c550 unpack leg-for-leg 18/18 (sources 0x985ac4 low +
0x985ae8:23/24); 0x4dc8d0 / 0x4dcc10 same positions from 0x985ac4 HIGH + 0x985ae8 / 0x985dc8; 0x4dc100 from the
M164 struct [esi+0x94d80c..0x94d81c] with 0x94d80c as a sign pair (scratch4 >0, scratch5 <0).
**M180** ds:0x920720 = the aggregator's bit-25-CLEAR COUNT (1 writer function: zero 0x53207e + inc 0x53210c; 11
reads in 4 consumers: 0x53a9c0 x4, 0x53bb90, 0x53cb20 (round>=50), 0x546800 x5 incl. 2 `cmp ,0x2` gates + a loop
bound). ds:0x9204b0 = the stamp EXPORT, bidirectional: writers 0x5321a4 (from [blk+0x94d4a8]) and 0x54d121
(re-prime with 0x985afc); readers 0x5406b4 (age = 0x985afc - stamp), 0x546d44 `jl`, 0x54bf5f `jle`.


## M182-M184 (s174d, all PASS) — the staging record's field map, the whole-value writers, FUN_00535c60's callers
**M182** ds:0x99aa1c = BASE of the record 0x6267a5 emits: 14 dwords in [0x99aa1c, 0x99aa5c]; the 13 packers
touch +0x0 (637 stores, the write-bytes arg), +0x4 (637), +0x1c (0x99aa38, 33 = the flag dword), +0x20 (0x99aa3c,
5) ONLY; +0xc..+0x18 belong to the emitter FUN_00626b46; +0x24 shared with the 0x626xxx siblings; +0x30..+0x40 are
0x627xxx serializer fields. 0x41 size pushed with GOVOPTIONS == the 0x41-byte span (INFERRED).
**M183** whole-value writers (1 store each, not leg packers): FUN_004dc390 = RESTORER (17 `test al/ah,imm`, 1 mask
op; mirror of FUN_004dc100's 24 pack ops); FUN_004d9ae0 = 12-iteration `shl edx,cl / test eax,edx / or|and esi,edx
/ inc ecx / cmp ecx,0xc` copy of bits 0..11 of FUN_0058e760's return; FUN_00512b40 = `setne` boolean + FUN_00518c50
called with indices 1/2/3 (no mask built); FUN_004dde00 = tests of [esi+0x93327c], pushes EDITVEH.
**M184** FUN_00535c60 = per-faction VISIT wrapper, 3 call sites in 2 owners (FUN_004266c0 x2: ds:0x91b5b4,
[ebp-0x14], eax; FUN_00545c50 x1: esi, 0, ebx, eax). Body: 0x531df0 -> 0x530e30 -> 0x535940 in that order, then the
2095-dword fold into [ebp-0x14], then `test [eax*4+0x94d448],0x40030`.


## M185-M187 (s174e, all PASS) — the visit's sub-passes, the assigned flag dword, the record's +0x20 selector
**M185** FUN_00530e30 writes only `ds:0x920740 = 0xf` + the staging pair `ds:0x99aa1c`/`ds:0x99aa20` (= record
+0x0/+0x4) but makes 10 calls incl. 0x626634 at 0x530fc0. FUN_00535940 = the aggregate scratch RESET: 47 stores, 13 to
-1 (0x9204c0/0x9206f4/0x9206e8/0x9206e4/0x920774/0x9204d8/0x9204cc/0x920750), 12 to 0 (0x9204b8/0x920710/0x920770/
0x9204e0/0x920490/0x9206ec), + 0x5a6cd0 x2.
**M186** `[fac*4+0x94d448]`: 27 plain-mov stores in 8 functions, ZERO memory-operand `or/and [..+disp],imm` -- **QUALIFIED by M190**: 23 of the 27 are the store half of a REGISTER-level bit RMW of the same field (a copied register or'd/and'ed then written back), so the field IS bit-set; only 4 are whole-value assignments and bit 0x10 arrives only through those. Stores in 8 functions (FUN_005551e0 x15, FUN_00552970 x5,
FUN_0052a720 x2 + 5 singles), ZERO or/and/add/sub **memory-operand** sites (M190: 23 of those 27 movs ARE
register-level bit RMWs, so the field IS bit-set/cleared); 653 refs, byte tests 0x1/0x10/0x20/0x7/0x2/0x8/0x3; the 0x40030
mask tested at exactly 2 sites (0x535ccb in FUN_00535c60, 0x4f2bba in FUN_004f26e0).
**M187** `ds:0x99aa3c` (record +0x20) = 3-VALUED SELECTOR: 5 stores (3 copy `[[ds:0x99aa40]+0x3100]` from FUN_00626b46/
0x626dfc/0x626f19, 2 from FUN_0048ee00/0x48ef80), 14 reads; FUN_004d9ae0 branches ==1 (0x4d9da0: unit record at
0x933289/8c/94, clears bits in [rec+0x93327c], calls 0x4d97c0) and ==2 (0x4d9dff, needs ds:0x985af0 > 0); FUN_00616b89
tests ==0.

## M188-M190 (s175, all PASS) — the aggregate count's use, the two save-path writers, 0x94d448 provenance
**M188** FUN_0053a9c0's `[ebp-4]` = `ds:0x9204ac + ds:0x920720` (+1 iff `ds:0x920720 != 0`) is LOCAL
bookkeeping: 43 mentions = 11 reads + 10 re-stores + 8 inc + 11 dec + 2 reg-arith; 0 `push`, 0 index forms;
11/11 reads consumed by arithmetic/cmp on the register, none reaches a call; 4 windows name rank `0x94d434`
or round `0x985afc` or `0x920720`.
**M189** FUN_004e0260 writes 3 non-spill places (staging pair `ds:0x99aa1c`/`ds:0x99aa20` +
`[block(fac)+0] = ds:0x999fa4` at 0x4e0336) + 1 spill; 4 emitter calls (0x626634 x2, 0x626581, 0x626ec4);
loop = 7 records at stride 0x59c (1436 B = 359 dwords) while ebx walks 0x20bc (8380 B) blocks from
0x94f70c. FUN_005a2930 = 0 stores, 5 tests, 5 callees (0x4d9fb0/0x4b6060/0x4b5f90/0x5844f0/0x5a1950), the
last reached only when `ds:0x920434` reads 0.
**M190** 27 stores at displacement 0x94d448 (8 functions), 0 immediate sources; **23 are the store half of a
register-level bit RMW of the same field**; sets union 0xe0c60, clears union 0x8513aee7. Of the 0x40030
mask: 0x20 set at 2 sites (0x55487f `or ecx,0x40020`, 0x554d42 `or esi,0xc0020`) and cleared at 4
(0x552cca/cd8/d6f/d7d `and edx,ecx`, ecx=0xffffffdf); 0x40000 set at 2, never cleared; **0x10 never set or
cleared at all** — it arrives only via the 4 whole-value assignments (0x52b9c7/0x52b9d0 load
`[ebp-0x50]`/`[ebp-0x4c]` in FUN_0052a720; 0x55540a/0x55580f store `lea`-built addresses).

## M191-M193 (s176, all PASS) — the channel publish primitive, the 0x94d448 bracket, the pass's output leg
**M191** FUN_00626634 = 10-slot CHANNEL PUBLISH (44 insns, 7 stores, 11 loads, 1 callee 0x64b9e0 =
append-until-NUL copy): bail `mov eax,3` unless arg2 != 0 and arg1 <= 9; writes [edx*4+0x999ff4] and
[eax*4+0x999fcc], zeroes then appends arg2 into the 256-byte text slot 0x99a01c + arg1*0x100; a negative
arg3/arg4 takes ds:0x99aa1c / ds:0x99aa20, and 0x99a01c + 10*256 == 0x99aa1c — the staging record IS
slot 10 of the same table. 1584 sites in 190 fns (immediates only 0..9; 88 register slots); table
writers 0x6265a2/0x626634/0x636b1e only, text slots read in 26 fns. The visit's site 0x530fc0 =
(slot 7, &[ebp-0x100] built by 0x5808b0, -1, -1).
**M192** FUN_0052a720's 0x94d448 stores (0x52b9c7/0x52b9d0) are the PUBLISH half of an 18-load /
18-store bracket over 9 block fields {0x94d448,468,488,4a8,4c8,4e8,558,55c,57c} (byte field captured by
movsx). [ebp-0x50]/[ebp-0x4c]: 1 writer (the field's own load 0x52aff5/0x52affe) + 1 reader (the insn
before each store); 0 of its 23 direct callees stores the field. Both sides compute the base as
8380*S + 4*C via `mov r,S; shl 6; add S; lea [S+r*2]; shl 4; sub S; add C; shl 2` — capture
(edi,ebx)/(ebx,edi), publish (edx,esi)/(esi,edx) reloaded from the single-write spills [ebp-0x2c]/
[ebp-0x30]: ADDRESS-EXACT. M190 QUALIFIED: bit 0x10 is PRESERVED here, not produced; its only remaining
carriers are 0x55540a (`lea eax,[eax*4+0x94d4a8]; or eax,0x20000`) and 0x55580f (`lea eax,[ecx*4+
0x94d448]; and ah,0xdf`) — both store ADDRESSES, where 0x10 is index arithmetic (i mod 8 in 2..5).
**M193** FUN_0053a9c0 = the aggregate pass's OUTPUT leg: 23 global stores to 8 globals {0x99aa1c 6,
0x99aa20 6, 0x997120 5, 0x9206e4 2, 0x920774 1, 0x9204b4 1, 0x920718 1, 0x7a75c8 1}; 0x9204ac (2 stores
in the image) and 0x920720 (1) are written ONLY by FUN_00531df0 and are READ-ONLY here; 0x9206e4/
0x920774 are 2 of the 15 the reset pass 0x535940 clears (8 writers / 10 readers each, top reader
0x546800). Its one call site 0x545cfa (FUN_00545c50) is gated `ds:0x920700 == 2` (0x920700: 8 stores in
0x544530 x7 + 0x546800 x1), the caller tests the return, and the tail zeroes 0x9204b4/0x920718, calls
0x533e70 and returns 1.

## M194-M196 (s177, all PASS) — channel-table consumers, the 0x920700 mode code, 0x94d448 is not a pointer

**M194** the 10 text slots are consumed by POINTER PASSING: window 0x99a01c..0x99aa1b = 113 sites/31 fns, 93 push the
base or a slot address (base 50, slot1 15, slot2 8, slot3 6, slot5 6, slot4 5, slot6 2) vs 20 direct memory ops; 16
callees receive it - 6 are the C string layer (0x64b9d0/0x64c460 thunks, _strlen, _strcmp, _strncpy, the 0x7efefeff
append-copy 0x64b9e0), 2 indirect via `call dword ptr ds:0x6713xx`; FUN_00631afb (1076 insns) / FUN_00632cad (288)
take slot addresses at 5/7 and 2/4 sites. Register indexers FUN_00625b20 (4 shl-reg,8 -> add-reg,0x99a01c pairs,
77 sites/23 fns) and FUN_005f0583 (1 pair, 99/66); FUN_006265a2 is FUN_00626634's sibling publish (86/39, 4 signature
insns shared). Slot 7 is WRITE-ONLY: 7 publishers (0x4d10dd 0x5022a6 0x509163 0x530fc0 0x53438d 0x552eb9 0x594e65),
0 pushes of 0x99a71c; live slots 0-4 hold 'disciplined'/'Provost'/'Zakharov'/'University'/'Mission Year 2150' - one
faction's sentence parts - and 5-9 are empty.
**M195** ds:0x920700 is a 13-value MODE CODE: 31 mentions = 8 stores/17 loads/6 tests/0 RMW; writers FUN_00544530 x7
+ FUN_00546800 x1 (0xc at 0x54ec5c); tested {1,2,4,5,6,7,8,9,a,b,c,d}, live 0; "ZERO string literals in all four
functions that write or test it" was **RETRACTED by M197** (the body names PROPOSALMENU / REJWARALREADY /
NOCOMMLINK); FUN_00544530 (1531 insns) also writes 0x997120 x28 and the staging pair
0x99aa1c/0x99aa20 x14 each.
**M196** `[reg*4+0x94d448]` is NOT a pointer: 365/466 scaled sites carry the 2095-fold (= 0x94d448+8380*S+4*C, the
block field at +0x344), all 297 tests are `test`+mask (0 cmp, widest 5 bits), 0/139 loads is dereferenced, and 0/66
live dwords (33 at +4i, 33 at +8380*fac) lie in the mapped range. RETRACTS M190's "carriers 0x55540a/0x55580f store
addresses" - they follow `or eax,0x20000`/`and ah,0xdf` on the flag word; the 0x5553d2 lea is the store-through alias
of the 0x5553df store.

## M197-M200 (s178, all PASS) — FUN_00544530 = the proposal composer, the diplomacy KEY pool, FUN_00625b20 = the tag engine, 0x631afb/0x632cad = row writers

**M197** FUN_00544530 (1502 insns) is the **DIPLOMACY PROPOSAL COMPOSER** for a faction pair: exactly 1 call
site in the image (0x545c99 in FUN_00545c50, guarded `[ebp+0x10]==0`, args [ebp+8]/[ebp+0xc], return tested).
ds:0x920700 is **ONE FIELD OF A 5-FIELD SELECTOR BLOCK** {0x9206fc, 0x920700, 0x920728, 0x920748, 0x92077c}:
the function calls FUN_005f1394 6x (0x544a91 544c2c 544f2b 0x5451e4 545686 5457f4), assigns the return to 5
distinct fields, clears all 5 within its first 112 bytes, and 6 of its 7 stores to 0x920700 are the constant 0
— the image's only immediate store there is 0xc at 0x54ec5c. Its body names 3 string globals whose bytes read
PROPOSALMENU / REJWARALREADY / NOCOMMLINK → **M195's "ZERO string literals" RETRACTED** (Ghidra renders a
referenced literal as a named `s_*` symbol, which carries no quote char).
**M198** those keys live in the string pool **0x690160..0x69107c**, 0xFFFFFFFF-terminated at BOTH ends: 329
entries = 311 single-word KEYS + 18 spaced message lines; **257 of the 311 keys have code references** and the
census prints key→function. The vocabulary is diplomacy message kinds: NEVERBASESWAP / PROPOSALMENU /
PROPOSEATTACK / ATTACKSTRING / REJWARALREADY / PROPOSECOMMLINK / NOCOMMLINK / PROPOSEBASE / COUNTER* /
COUNCILVOTE* / *TRUCE / *TREATY / PACT / DEMANDATTACK / INTRODUCEENEMY / BETRAYFRIEND / RANSOMDEMAND /
WEASELOUT / ASKFORLOAN / …
**M199** FUN_00625b20 (char*,char*) **IS THE SUBSTITUTION ENGINE**: _strstr for '$' (the byte at 0x69911c),
switch on the char after it over 5 cases ($, <, H, L, N), closer '>' at 0x699138, '$HEX' at 0x699130; kinds
M=0 / F=1 / N=2 / '#n' / n→B[n]@0x999ff4 + A[n]@0x999fcc; slot text `&DAT_0099a01c + n*0x100`; it then copies
the Nth ':'-separated segment. FUN_005808b0 COMPOSES `$<`+{M,F,N}+{1,2}+`:`+arg+`>` from the record dwords
+0x2fc/+0x300 (literal bytes 0x692144..0x692160); FUN_00580a60 PARSES that head back into 0x99aa1c (F→1,
N→2, else 0) and 0x99aa20 (2nd char '2') — inverse-consistent, so **the staging record IS a parsed tag head**.
FUN_00426680 returns the name text at record +0x34 (record = 0x927590 + fac*0x59c).
**M200** FUN_00631afb / FUN_00632cad are **ROW WRITERS** on the table handle DAT_0099d020 (vtable
+0x10/+0x18/+0x38/+0x58/+0x60; alloc FUN_005be090, free FUN_0064a7f0, append FUN_0064b9e0): 0 `0x25`
immediates, 0 printf-family calls, 0 references to FUN_00625b20 — they copy their text argument VERBATIM, so
**M194's "the formatters" is RETRACTED**; the 16-byte memcmp keys 0x67bd20/0x67bd30 are GUIDs (a class test),
not table names.

## M201-M204 (s180, all PASS) — FUN_005f1394 = the OK/CANCEL DIALOG RUNNER (class ctor FUN_00405ef0, vtable 0x67164c), its return is a result code, FUN_0062898e = first-digit scanner, the key pool = an emitter list

**M201** FUN_005f1394 is a **thiscall member of the game's dialog class**: ctor FUN_00405ef0 installs
vtable 0x67164c at this+0 (0x405f31) and 0x671644 at this+0x444 (the CPane subobject), 99 ctor sites in 90
functions, 53 of the 67 pump-caller functions construct it. The dword 0x5f1394 appears 0 times as data
image-wide - not a vmethod, not a jump target; 94 direct calls, one exit `ret 0x8` (0x5f3f58), 90/94 sites
load ECX from the caller's own stack frame. It is the ONLY reader of 0x698e40 'OK', 0x698e44 'OK',
0x698e48 'Cancel', 0x698e50 'OK'. Slots it dispatches through *this, all resolved in 0x67164c:
+0x4=0x406750, +0x8=0x4068a0, +0x30=0x406970, +0xdc=0x5ce5bd, +0x15c=0x406990, +0x160=0x404e70,
+0x164=0x407060, +0x16c=0x407280, +0x170=0x407660; the +0xdc dispatch is made twice, on *this and on
*[this+0x285]. **M202** its return domain is {0, -1, [this+0x290], a passed-through dispatch value}: 0
`mov eax,imm` in 11,207 bytes, 5 `xor eax,eax`, 2 `or eax,0xffffffff`, `mov eax,ds:0x698d0c` (that dword IS
0xffffffff, 1 reader image-wide) and the single `[reg+0xa40]` read at 0x5f3f45 (0 stores). Its arg2 is a
CALLBACK the modal handler invokes - vtable+0xdc FUN_005ce5bd (`ret 0xc`) does `cmp [ebp+0xc],0` (0x5ce6bd)
then `call dword ptr [ebp+0xc]` (0x5ce6c3); 17/94 sites pass 0x530d70 (16) or 0x530db0 (1), unnamed
islands in the 0x530d45-0x530df0 gap that gate on ds:0x920434 and ds:0x991588, guard with ds:0x920790 (its
only 4 stores) and call FUN_00519a20. **M197's "chooser" is RETRACTED**: ds:0x920700 (31 sites, 4 fns,
tested {4,6,8,9,d}) holds a dialog RESULT CODE, stored there by all 6 composer calls. **M203**
FUN_0062898e is a FIRST-DIGIT scanner (61 B, 0 callees, only '0'/'9' bounds), 5/5 sites inside
FUN_00625b20; $H compares 4 bytes with 0x699130 '$HEX' -> `__itoa([0x999fa4][n])`, else digit -> slot text
0x99a01c+n*0x100; $L's exception is 0x69913c '$LINK<'; $N gotos the default tail; the engine returns only
14 (x6, behind 8 `9 < local_1c` guards) and 3. **M204** the key pool is an EMITTER LIST: 313 `push <key
VA>` sites / 255 keys / 29 functions, all inside 0x5316b0..0x54f1d0, FUN_00546800 owning 111 sites / 97
keys; sinks FUN_00626a17 x149 (thunk to FUN_00626b19(&0x997528, key, -1, 0, ...)), FUN_0064b9e0 x76,
FUN_00405220 x33 (thunk to FUN_00404010(&0x997120, key)); 11 of the 29 referrers call the pump, 56 of the
67 pump callers name no key - the paths join only as 0x530d70 -> FUN_00519a20 -> FUN_00546800.

## M205-M208 (s181, all PASS) — the dialog RESULT field and who writes it, [this+0x285] = child-dialog link slot, FUN_00546800's three switches, ds:0x997528 = write-only staging buffer

**M205** the pump FUN_005f1394 returns `[this+0xa40]` (= Ghidra `this[0x290]`): 0x5f3f3f `mov eax,[ebp-0x394]` (the spilled entry ECX, its ONLY store in 11,207 B) -> 0x5f3f45 `mov eax,[eax+0xa40]`, taken only when `[ebp-0x30]==0`; the other two legs both yield -1 (`or eax,0xffffffff` behind `[this+0x30a8]&0x40`; `mov eax,ds:0x698d0c`, that dword = 0xffffffff). Writers: 56 store-shaped +0xa40 sites in 30 functions, of which exactly TWO are dialog vmethods — FUN_005f5759 (+0xa8,+0x228) and FUN_005f58fa (+0x64,+0x1e4), each with 0 direct call sites — and the value they store is a LIST ITEM (`[node+[node+8]+0xec]`, or the result of `call 0x5fdcf7`) or 0 / 0xffffffff. FUN_005f5759 also parks its arg in [this+0x3100]. Forwarders FUN_005ce4a9/FUN_005ce4dc (51 B, `ret 0x4`, 2 sites each) write it through [this+0x43c]/[this+0x440]; base ctor FUN_005ee350 zeroes it (0x5ee7a5). WHO dispatches +0xa8 is OPEN (29 `call [reg+0xa8]` sites in 17 fns, none in a pump- or ctor-caller).
**M206** [this+0x285] = byte +0xa14, one slot of a 7-pointer link block (0xa14..0xa2c) spliced in triples by FUN_005ee350 (9 stores) / FUN_005eede6 (9) / FUN_005f6b8c (6); FUN_005f6b8c seeds it from the GLOBAL ds:0x997850 and installs vtable 0x671d94 (+0x671d8c at +0x444) on the object it constructs. The pump: 10 loads, 1 store (0x5f1561 = 0), and 0x5f3d7c chooses `call [[this+0xa14]->+0xdc]` (0x5f3dbe) over `call [*this->+0xdc]` (0x5f3df6) with identical args (0, the arg2 callback, `[this+0x30a8]&0x200000`). +0xdc = FUN_005ce5bd: modal loop over a 4-deep dialog stack (guard `cmp ds:0x9939c8,4`; [d*4+0x992db8], [d*4+0x992dc8], current ds:0x9939c4 at 0x5ce60e), suspend previous via +0x10, activate +0x4, events +0xe4, `call [ebp+0xc]`, close +0xe0, `ret 0xc`.
**M207** FUN_00546800 (34,550 B, 5 call sites: FUN_00519a20/0x54f1d0/0x5525d0/0x5551e0 x2): three jump tables 12/5/8 entries at 0x54eef8 / 0x54ef14 / 0x54ef34 (guards `cmp eax,6; ja`, `cmp ebx,0xa` + the byte-permute table 0x54ef28, `cmp eax,7; ja` on `call 0x542ea0` behind ds:0x920434 != 0 and ds:0x985ae8 bit 0x800), all 19 targets inside the function; args = the 2095-fold -> `test [eax+0x94d448],0x8000000`; builds a dialog on its 0x5534-byte frame and calls the pump 0 times. 111 single-word key sites = 109 addresses = 97 TEXTS (M204's 97 counted texts); 29 sites in the prologue, 68 in the region from 0x54ad65, 7 across the 8 result-code regions.
**M208** ds:0x997528: 103 address-pushes + 1 byte clear (0x5f58de) + 1 arg-slot store, ZERO absolute loads; the drain is FUN_005f0583 (79/103; defaults its text arg to the buffer at 0x5f06fe, calls the tag engine 0x625b20, writes [this+0x2350] 7x with 1/2/4/0x10, attaches via FUN_005eede6). FUN_00626a17 = 38-B thunk, only call -> writer FUN_00626b19(buffer, key, -1, 0, ...); FUN_0064b9e0 = the SWAR strlen, so M204's "76-site sink" measures the key text rather than emitting it.

## M209-M212 (s182, all PASS) — who dispatches dialog slot +0xa8, the dialog stack arrays, the pump wrapper FUN_00542ea0, the -9999 sentinel

**M209** slot +0xa8 = 33 implementations / 188 vtables; 3 map it to FUN_005f5759 (0x67164c/0x6717cc/0x6728c0, 390/70/4 installs, 457 at `[ebp-disp]` — dialogs are stack locals). Its dispatchers: FUN_005f6aa3 (the family's own +0x4c vmethod, 5 vtables, 0 direct calls) — `FUN_005e7917(a,b,&v,&f)` picks the LAST list item (24-B stride, `[obj+8]-1` down) for which FUN_005e75a0 succeeds, publishes item[+0x14]/item[+0x10], and `(*(*this+0xa8))(v)` runs when the index != -1 and f == 0; and FUN_0043fee0 (+0xa8 of 0x6738e4, 0 direct calls) — `if (ds:0x9977f0) (*(*ds:0x9977f0+0xa8))(arg1)`, ds:0x9977f0 written only by the pump (0x5f3d70/0x5f3e02). FUN_004bb900 = +0xa8 of 8 vtables, forwards to [this+0x3c], returns 0x14 if null. FUN_0043a4e0 (+0x60 of 0x673498 -> FUN_004394e0) and the -0xa14 thunks (subobject vtables 0x6723f4/0x672bfc/0x673444 at `[reg+0xa14]`) dispatch OTHER classes' +0xa8.
**M210** the +0xdc runner's stack = two parallel 4-deep dword arrays: dialogs[] 0x992db8 (4 stores / 2 loads, 3 fns) and arg3[] 0x992dc8 (3 stores, 0 loads = write-only); current 0x9939c4 22/3, depth 0x9939c8 21/3, writers only FUN_005ce5bd + FUN_005ce6ff. Slot +0xe4 is a BOOLEAN predicate, not an event pump: dialog family = FUN_005f6056 `return ds:0x997770 == 0`, sibling family = FUN_004060d0 `return 1`; ds:0x997770 = 2 stores (pump 0x5f3e6e = 0, FUN_005f6073 0x5f6081 = 1) + 1 read; 2 dispatch sites total.
**M211** FUN_00542ea0 = the pump's WRAPPER (1456 B, 1 caller FUN_00546800): calls ctor FUN_00405ef0 (0x542ecb), the pump once (0x54322b), returns its eax; the 8-entry table at 0x54ef34 (guard `cmp eax,7; ja 0x54ec82`) is therefore keyed on the PUMP's result code: 0->FUN_005306b0, 1/2->FUN_00545c50, 3->FUN_00626a17 (key 0x690fc0, stub 0x530d70), 4/5/6->FUN_0053fce0/FUN_00541bb0/FUN_00542810, 7->sets ds:0x920700=0xc + ds:0x92077c=1 then FUN_00545c50.
**M212** -9999 (0xffffd8f1) = FUN_00496ad0's "unset" sentinel (init 0x4976ce `mov [ebp-0xb9c],0xffffd8f1`, read-back 0x4976f9 `mov eax,[ebp-0xb9c]`, 1 caller FUN_00417ee0 whose 2 tests read edi = `call 0x496ad0; mov edi,eax`); 14 sites / 10 fns; 0 of the pump's 94 call sites and 0 of the 56 [this+0xa40] stores touch it — disjoint from the pump's -1. Pump consumers: 49 mov / 22 test eax,eax / 4 cmp-imm / 6 cmp-reg.

## M213-M216 (s183, all PASS) — point-in-rect hotspots, the dialog +0x4c click dispatcher (list at this+0x3098), the 0xb4c row class + its label buffer, vtable 0x6738e4 and the ds:0x9977f0 readers

**M213 hotspot primitive** FUN_005e75a0 (69 B, 29 insns, 0 callees, 61 direct sites / 25 fns) returns 1 iff `box[0] <= x < box[2] && box[1] <= y < box[3]` — a 16-byte {l,t,r,b} rect, HALF-OPEN right/bottom (4 cmp at +0/+4/+8/+0xc, 4 `xor eax,eax` miss arms, exactly 1 `mov eax,1`, 0 stores, bare `ret` = cdecl 3 args). FUN_005e7917 (140 B, 53 insns, 44 sites / 43 fns, `ret 0x10`) = the LIST SCAN: `[obj+0]` = item array base, `[obj+8]` = count, 24-byte items (`imul ,0x18` x3), index runs count-1 DOWN to 0 and stops at the first hit -> returns the HIGHEST (last-drawn) matching index, or -1 (`or eax,0xffffffff`); on a hit publishes item[+0x14]->param_3 and item[+0x10]->param_4 behind null-guards. Item = {x0@0, y0@4, x1@8, y1@0xc, gate@0x14, payload@0x10}. FUN_00403a40(r,x,y,w,h) = {x,y,x+w,y+h}; FUN_00403a80(r,dx,dy) inflates BOTH corners (4 mov/add/mov read-modify-writes at +0/+4/+8/+0xc). FUN_00478080 (143 insns, 0 direct call sites image-wide) = the 4-ZONE variant: 1x FUN_00403a40 + 4x FUN_00403a80 on one 16-byte stack rect, 4 tests, 4 dispatches of `[reg+0xa8]` with the immediate 3/2/1/0 = the ZONE NUMBER.
**M214 the +0x4c click dispatcher** FUN_005f6aa3 (76 B, `ret 0x8`, 0 direct calls) is +0x4c of exactly 5 vtables — 0x67164c (390 installs), 0x6717cc (70), 0x6728c0 (4), 0x675cc4 (1), 0x6776c8 (1) = 466 installs. Body: spill this to [ebp-0xc]; `add ecx,0x3098` then `call 0x5e7917` — THE HOTSPOT LIST IS A MEMBER AT this+0x3098 (Ghidra renders both the list and the vtable as `*in_ECX`, so the C reads as if the list were the object); gate `cmp [ebp-0x4],0` = item[+0x14] == 0; the dispatched argument is [ebp-0x8] = item[+0x10]; `mov eax,[edx]` then `call [eax+0xa8]` = SELF-dispatch of the class's own +0xa8. Slot +0xa8 is therefore the CLICK-RESULT method and its argument is the hotspot payload — this explains M209's "the slot takes a RESULT VALUE". Lists are a reusable member: the 44 scan sites take them from 19 distinct this-relative displacements (34 sites, 0x8f4..0x402f0), 1 global object (0x8a9108) and 9 stack locals. `[reg+0x3098]` = 1 direct site (dialog ctor FUN_00421da0 at 0x421ea0: `lea ecx,[esi+0x3098]; call 0x5e7665` = the list CLEAR (FUN_005e7665 wraps FUN_005e760d, which frees [+0] and zeroes the 3-dword header; the ALLOCATOR is FUN_005e7678 — s184/M217)), +0x309c/+0x30a0 = 0. WHO DISPATCHES +0x4c stays OPEN: all 12 image-wide `call [reg+0x4c]` sites belong to other hierarchies (FUN_004b83d0 = 0x676fc0+0x4c; FUN_004ba2b0 = +0x4c of 15 vtables; FUN_005d9aba = 0x67275c/0x67919c+0x4c; FUN_005d9b97 = +0x58; FUN_005fa7f5 = +0x40 of 0x679640/0x679e08/0x679f98; 7 in non-vmethods, 2 of them 0x5b7cec/0x5b7dc4 outside any indexed function).
**M215 the 0xb4c ROW class (vtable 0x67194c)** ctor FUN_005faec0 (376 B, 82 insns, 60 direct sites / 15 fns) installs 0x67194c at [ecx+0] and the CPane subobject vtable 0x671944 at [ecx+0x444]; 20 stores; fields 0xa14/0xa18 = 0, 0xab8 = -1, and the 0..2 loop writes [ecx+eax*4+0xabc] = -1, [..+0xac8] = 0, [..+0xad4] = 0 plus 27 dwords copied from 9 stride-0xc triples at 0x9978ac..0x99790c into [ecx+edx*4+0xae0/0xaec/0xaf8/0xb04/0xb10/0xb1c/0xb28/0xb34/0xb40] — last element 0xb48, so a row ENDS at 0xb4c, which is also 0x15f8-0xaac, the gap between the two row subobjects FUN_005f6b8c constructs (`add ecx,0xaac` / `add ecx,0x15f8` before two `call 0x5faec0`; the 0x671d94 sibling class, 275 installs, embeds 2 rows). Size VERIFIED two independent ways. Each triple has 3 refs (the copy loop) and is written by ONE of 9 THREE-store setter functions FUN_0045a4d0/500/530/560/590/5c0/5f0/620/650 (0x30 apart, 42 B, 3 args, 1 call site each, all 9 called in one run by FUN_00459bb0 — s184/M219; the earlier "one-store functions" reading is RETRACTED: the bare `mov ds:imm,eax` a3 form is only the FIRST of the 3 stores, 9 of 27): runtime SETTER state, not load-time data — every row starts as a copy of whatever its setter last computed. FUN_005f9e85 (422 B, 128 insns, 90 sites / 23 fns, 0 vtable slots) = the LABELLED-CONTROL CREATOR: dispatch *this+0x15c; param_7==0 -> return 3; else if param_1 != 0: `_strlen`, FUN_005be090(len+1) alloc, store the pointer at [this+0xa7c], write the NUL, FUN_0064b9e0 copy; then FUN_005e3ed9(x=param_3, y=param_4, w=param_5, h=param_6, style 0x1000320 | -(param_8!=0)&0x8000, parent=param_7) — on success store param_2 (the id) at [this+0xa78], 3x CPane::SetBorders on the +0x444 subobject from the 12 immediates 0x698eac..0x698ed8, return 0; return 4 when the alloc fails. LABEL ARGUMENT census over the 90 sites: 44 x the global scratch TEXT buffer ds:0x997120, 15 NULL, 30 register/field, 1 .rdata literal ("Create Session (Translate)" @0x69a7bc). ds:0x997120: 4089 refs, 668 stores of any width, ZERO indexed (`[reg*4+0x997120]` = 0 — code only ever uses the base), 466 of them the base-clear `mov byte ptr ds:0x997120,0x0`; 1425 of the 3232 `push 0x997120` sites hand it to the emitter FUN_0064b9e0 and 174 to the indirect call through ds:0x671324 — a row label is text FORMATTED INTO THIS GLOBAL BUFFER, never a literal.
**M216 vtable 0x6738e4 and the modal handle** 0x6738e4 = 87 slots, 2 installs (0x43fa14 in FUN_0043f9f0 -> [eax], 0x43fc3e in FUN_0043fb60 -> [ecx]); its +0xa8 is FUN_0043fee0 (`if (ds:0x9977f0) (**(*ds:0x9977f0 + 0xa8))(arg1)`; 1 vtable slot image-wide, 0 direct calls). It IS a dialog-family class: 75/87 slots identical to 0x6717cc, 73 to 0x671d94, 66 to 0x67164c, 70 to the row 0x67194c, and every differing set contains 0x0 (own ctor), 0x4c (no click dispatcher — replaced by the handle forwarder) and 0xa8. ds:0x9977f0 = 9 refs, 2 stores (0x5f3d70 `mov DWORD PTR ds:0x9977f0,ecx` and 0x5f3e02 `mov ds:0x9977f0,eax`, both inside the pump FUN_005f1394), 7 loads in exactly 4 functions: the pump (1), FUN_0043fee0 (3), FUN_005d69fa (2), FUN_005f5a11 (1). FUN_005d69fa (0 slots, 3 direct callers 0x5d157a/0x5d15d9/0x5d1605) picks the CURRENT object: if ds:0x9939c4 != 0 then (ds:0x9977f0 if set, else 0x9939c4), else (ds:0x9939a8 if set, else ds:0x9939d0); publishes it to ds:0x9939ac; returns the object's [+0xa8] FIELD — a DELEGATE object pointer, not a vtable slot value — after FUN_005d8123 (167 sites / 97 fns) approves; its 3 callers dispatch +0x12c / +0x130 / +0x134 on that delegate. FUN_005f5a11 (299 B) has 0 direct calls and 0 vtable slots, yet its address appears 3x in the image, each as an immediate stored into an object FIELD at [reg+0x2210] / [reg+0x2224] / [reg+0x2234]: a CALLBACK installed in a field. Narrowed at s184/M220: all 3 stores are inside FUN_005f3f5b (slot +0x15c of 0x6717cc, called twice by FUN_00406990, the +0x15c of the 0x67164c family) and those three fields have ZERO loads image-wide (2/1/1 refs, no indirect call carries a displacement in 0x21c0..0x2260) — the fields are WRITE-ONLY, so the invocation route is OPEN. Its body treats the handle as an object: reads [handle+0x30a8] and [handle+0x2350], writes [handle+0xa40] (the pump's result field, via FUN_005fdcf7) and [handle+0x3100]=0, dispatches +0xe0 (the closer) on [handle+0xa14] (the child dialog) or on the handle itself, and +8 when [handle+0x30a8] & 0x4000.
## M217-M221 (s184, all PASS) — the hotspot CONTAINER (3-dword header, 24-B items, 8-member API), the list is a MEMBER, the row triples' 3-store setter, the +0x15c installer with WRITE-ONLY callback fields, the 0x671d94 panel (0x214c, +0xa8 = detach)

**M217 the hotspot container** the object FUN_005e7917 walks is {+0 item array, +4 capacity, +8 count} of 24-byte items. API (all 0x5e7300-0x5e7d00, no vtable slots): FUN_005e75e5 reset (3 zero stores at +0/+4/+8); FUN_005e760d free+reset (if [+0] then FUN_0064a7f0([+0]), [+0]=0, then reset); FUN_005e7665 = 9-insn wrapper over it, 130 sites (the clear every owner calls — NOT an allocator); FUN_005e764f reset + return self, 21 sites; FUN_005e7678 `ret 0x4` ALLOCATE n: clear, `imul eax,arg1,0x18`, FUN_005be090, [+0]=ptr, [+4]=n, [+8]=0, 21 sites; FUN_005e774d `ret 0x18` ADD: returns -1 when `count >= capacity` else idx=count, count++, and writes item+0=arg3(x), +4=arg4(y), +8=x+arg5(w), +0xc=y+arg6(h), +0x10=arg2 (PAYLOAD), +0x14=arg1 (GATE) — i.e. arg1/arg2 are exactly what M214's dispatcher tests (==0) and hands to +0xa8; FUN_005e78c7 `ret 0x4` REMOVE-BY-PAYLOAD (idx count-1..0 while item+0x10 != arg1, then FUN_005e77e7(list, idx)), 32 sites. FUN_005e7917 publishes item+0x14 to arg3 and item+0x10 to arg4. Image-wide FUN_005e774d is the ONLY writer of an item's +0x10/+0x14 (2 stores); the 11 readers are 0x5e76be/0x5e7861/0x5e78c7/0x5e7917/0x5e79a3/0x5e7a5f, all inside the family.

**M218 the list owners** the container is a MEMBER, not a stand-alone object: the 130 clear sites take it from 47 member displacements (21 distinct, 0x10 .. 0x402f0) and 81 stack locals (`lea ecx,[ebp-0xNNNN]` — dialogs are stack objects) plus 2 loaded values; the 21 alloc sites give 13 distinct capacities 0x1..0x100; the 32 add sites take the list from 26 member displacements (0xa2c, 0x4b0, 0xa50, 0x20f0, 0x214c, 0xcc4, 0x5994, 0x402e4, 0x402f0) and 6 loaded values (FUN_00403b00, FUN_0040f830, FUN_004105b0, FUN_00411840, FUN_00415d10, FUN_00607eca). Gate-operand census (last push before the site): immediates {0, 1..8, 0x45} — the 1..8 set is confined to FUN_00486c30 writing its own list at +0xcc4 — and 21 register-passed gates. The dialog's list at this+0x3098: cleared at 0x405fb3 (FUN_00405f60) and 0x421eaa (FUN_00421da0) (+2 SEH unwind stubs 0x661efb/0x66f76b), allocated 10 items at 0x5eff25 (FUN_005ef957), reset at 0x5ee5fe (FUN_005ee350), scanned at 0x5f6ac5 (FUN_005f6aa3), and ZERO add-sites with that displacement — so it is filled through a register-passed list pointer, and which wrapper fills it stays OPEN.

**M219 the row triples' setter** each of 0x9978ac..0x997914 is written by ONE of 9 functions FUN_0045a4d0/500/530/560/590/5c0/5f0/620/650 (0x30 apart): 42 B, 18 insns, 3 args ([ebp+8], [ebp+0xc], [ebp+0x10]) and 3 stores — the whole triple at once. 9 of the 27 stores are the bare `mov ds:imm,eax` (a3) form, the other 18 print as `mov dword ptr ds:imm,ecx/edx`, so a bracket-only store census reports 18 and misses 9. All 9 setters have exactly one call site and all 9 are in FUN_00459bb0 (1722 B, 450 insns, 1 callsite, 0 vtable slots) in one straight run, each followed by `add esp,0xc`; 3 calls pass pointers 0x774c38 + 0x2c*i (i = 0..8, each entry used exactly once) and 6 pass (0,0,0). Both the triples and that table are above FILEMAP_END 0x6ed000 (BSS at runtime): runtime setter state, not load-time data. RETRACTION of M215's "one-store setters". Consumer: FUN_005fb1a5 = slot +0x30 of the row vtable 0x67194c reads/tests the 0xae0..0xb48 groups on the 4-byte grid.

**M220 the +0x15c installer and its WRITE-ONLY callback fields** FUN_005f3f5b (6102 B, 1336 insns) is slot +0x15c of exactly one vtable, 0x6717cc (95 slots, 70 installs), and is a 10-case switch (`cmp [ebp-0xf4],0x9` + `jmp dword ptr [ecx*4+0x5f5731]`, all 10 targets inside the function). The image holds exactly 3 references to 0x5f5a11 and all 3 are its stores: [eax+0x2210], [edx+0x2224], [edx+0x2234]. Those three displacements have 2/1/1 refs image-wide (the extra +0x2210 ref is a clear-loop store in FUN_00406990), ZERO loads of any width, and no `call [reg+disp]` anywhere carries a displacement in 0x21c0..0x2260 — the fields are WRITE-ONLY, so FUN_005f5a11's invocation is NOT through them (OPEN). FUN_00406990 (1560 B, 399 insns) is +0x15c of 0x67164c/0x6728c0/0x675cc4/0x6776c8 (396 installs) and calls FUN_005f3f5b twice (0x406c24, 0x406f26), so the install runs for both dialog classes. NB `push 0x2210` (0x528000) and `cmp eax,0x2210` (0x52d1bf) are the netcode LOCK message id — a value collision, not an offset.

**M221 the 0x671d94 panel** 87 slots, 275 installs; 74/87 slots identical to 0x6717cc, 63/87 to 0x67164c, 71/87 to the row 0x67194c. It has NO click dispatcher: +0x4c = FUN_005f84ff (not FUN_005f6aa3) and +0xa8 = FUN_005f90d7 (not FUN_005f5759). Ctor FUN_005f6b8c (605 B, 136 insns, 16 sites): calls FUN_005e3b80, then `add ecx,0xaac`/`add ecx,0x15f8` before two `call 0x5faec0` (2 rows), installs 0x671d94 at [reg+0] and 0x671d8c (3 slots, 268 installs) at +0x444, and initialises the 0xa14..0xaa0 block across the three objects. SIZE 0x214c proven by two independent containers that embed panels at a uniform 0x214c stride (3 in FUN_00409e70 at +0x40884/0x429d0/0x44b1c, 4 in FUN_004947c0 at +0xa78c/0xc8d8/0xea24/0x10b70); row 2 ends at 0x15f8+0xb4c = 0x2144 and the ctor still writes +0x2144/+0x2148. The two +0xa8 implementations differ: FUN_005f90d7 (142 insns, 7 indirect calls) clears [this+0xa38] (1 store), unlinks through the 0xa20/0xa24/0xa2c link block (`cmp eax,[edx+0xa20]` / `cmp eax,[edx+0xa24]` + 2 stores to [eax+0xa2c]) and dispatches `call [edx+0xb8]` — a DETACH; FUN_005f5759 (98 insns, 3 indirect) writes the RESULT field [this+0xa40] 4 times and never touches 0xa38/0xa2c. The dialog ctor FUN_00405ef0 embeds exactly one panel, at this+0x3230 (site 0x405f29).

**M222 the ADD wrapper FUN_00403b00 and which containers get filled** FUN_005e774d's own body (ret 0x18) maps arg1 -> item+0x14, arg2 -> item+0x10, arg3 -> item+0, arg4 -> item+4, item+8 = arg3+arg5, item+0xc = arg4+arg6; the only failure path is count>=capacity returning -1, with 0 allocator calls (a full list DROPS the item). FUN_00403b00 (75 B, ret 0xc) is the image's only wrapper: it spills ecx to [ebp-0x4] (so the CONTAINER is its own `this`) and pushes (arg1, arg2, [rect+0], [rect+4], [rect+8]-[rect+0], [rect+0xc]-[rect+4]) — its 3rd argument is an {x,y,right,bottom} RECT converted to (x,y,w,h). 23 sites in 16 functions: 22 pass the container as the caller's own ecx plus one of 8 member displacements (0xa48 x1, 0xcc4 x5, 0xe40 x1, 0x15e0 x5, 0x28ac x4, 0x5994 x3, 0x12758 x2, 0x12764 x1) and 1 (FUN_00403ad0) forwards ecx bare. NEITHER the wrapper nor any direct add-site carries the dialog's +0x3098: that 10-item list is allocated, reset and scanned but NEVER appended in the image. Slot statistics at the 23 sites: the +0x14 slot (the one FUN_005f6aa3 tests for 0) is an immediate at only 4 sites (0, 0, 3, 0x64) and a register/loaded value at 19; the +0x10 slot (the value handed to +0xa8) is an immediate at 19 sites with values {0,1,2,3,4,0xa,0xb} — 0xa and 0xb are outside M218's {0,1..8,0x45} gate set, so the small integers belong to the PAYLOAD slot, not the gate slot. The 4 remaining register-passed adders run on the GLOBAL object at 0x6a9480: FUN_0041f310 is slot +0x30 of vtable 0x672448 and all 3 of its call sites pass `mov ecx,0x6a9480`, and 8 of the 15 sites of FUN_0040f830/004105b0/00411840/00415d10 pass the same immediate (the rest pass the caller's own this); FUN_004105b0's container is this+0x402f0 (`lea ebx,[edi+0x402f0]` is the last write to ebx before its add-site at 0x41066c).

**M223 FUN_005f5a11: a callback that is installed but unreachable** 0 direct call sites, 0 vtable slots, and the dword 0x5f5a11 occurs in the whole image only as the imm32 of the 3 stores that install it (data hits 0x5f48bc/0x5f4915/0x5f4a76 = the FUN_005f3f5b stores at 0x5f48b6/0x5f490f/0x5f4a70 plus 6). The 3 fields it was installed into have exactly 4 bracket references image-wide and ALL 4 are stores (the 3 installs + FUN_00406990's zero-loop store at 0x406c57): 0 reads, 0 lea-address-takes, 0 `call [reg+disp]` with any displacement in 0x21c0..0x2260. Five mechanisms ruled out. Its own body says what it is: it reads ds:0x9977f0 (the modal-object handle the pump publishes), returns if null, gates [h+0x2350] against 1 and -1, reads [h+0x21d0] (used as an index into [h+0x229c]) and [h+0x30a8], and dispatches [reg+8] and [reg+0xe0] — a method of the MODAL object class. The block is NOT dead: the dialog runner FUN_005f1394 calls FUN_0060c436 at 0x5f1e33 with ecx = obj+0x21d0 and arg1 = [obj+0x2350], and FUN_0060c436 passes its this+0xb14 to FUN_00607eca, which subtracts 0xa94 before `call 0x5e774d` (0x60820b) — so the hotspot CONTAINER lives at obj+0x2250, 0x1c above the last write-only field, in the same 0x21c0..0x2260 block.

**M224 FUN_00459bb0, the 0x774c38 grid and the pane's +0xb24 page pointer** FUN_00459bb0 (1722 B, 450 insns) has exactly ONE call site, 0x45a755, inside FUN_0045a740 (56 B, itself called once by FUN_00580260); neither sits in a vtable. Re-deriving M219's setter set from the stores instead of from names: the 27 globals 0x9978ac..0x997914 are written by exactly 9 functions of 42 B (3 refs each), each with exactly 1 call site, all inside FUN_00459bb0. M219's split is CONFIRMED: 3 of those 9 calls pass three pointers each and 6 pass (0,0,0). The pointers are the 0x2c-stride grid 0x774c38 + 0x2c*i (i=0..8) — 24 pushes drawn from exactly those 9 addresses (per-entry counts 2,2,2,3,3,3,3,3,3) spread over 15 calls, so 12 further calls in the same run (a FUN_0045a320..0x45a6e0 family) take the same grid. The grid's 99 dwords all read 0 and the block lies past the end of the file image (0x400000 + 0x2ec8c0 = 0x6ec8c0): runtime-filled BSS, not load-time data. The only other function referencing the region, FUN_0041f450 (8250 B, 1 caller FUN_005800a0), does not read the grid: it INSTALLS page bases — 39 references to 0x774xxx, and its 5 stores to a field all go to [obj+0xb24]: 0x774c0c x4 (= grid base - 0x2c, one entry below the first entry any setter receives) and 0x774a80 x1 (= grid base - 0x18c = 9 entries below). 9 other functions load [obj+0xb24], so the grid is reached through that field.

**M225 the panel's +0xa8 DETACH dispatches a FIELD callback at +0x2144** FUN_005f90d7 is slot +0xa8 of exactly one vtable (0x671d94). It dispatches 7 times: `call [reg+0xb8]` x2 on the two link neighbours it unlinks (2 relink stores `mov [eax+0xa2c],edx`, plus `mov [eax+0xa38],0x0` and `mov [eax+0xa3c],0xffffffff`), `call [reg+0x5c]` then `call [reg+0x1c]` on a third object, `call [reg+0xf0]` on itself, and `call [reg+0x2144]` x2. The largest vtable slot offset in the whole image is 0x178 (over 188 vtables), so +0x2144 CANNOT be a vmethod: it is a call through the panel object's own last field (the panel is 0x214c). That field has 54 references, 17 writer functions and 7 reader/caller functions — a stored per-object callback, installed by whoever builds the panel, not a class slot.

**M226 the row class's slot +0x30 FUN_005fb1a5 is a DRAW on the CPane** 4202 B / 1000 insns, slot +0x30 of the row vtable 0x67194c. 14 of its calls are preceded by `add ecx,0x444`, i.e. they run on the CPane subobject (law: resolve the RECEIVER, not just the callee); it makes exactly ONE indirect call, `call [edx+0x14]`. It reads the row's group data as INDEXED dword arrays (`[reg+reg*4+0xabc]`, `[reg+edx*4+0xac8]`) plus the 0x98/0xa7c/0xa88/0xa8c fields — the 9 groups are arrays inside the row, not 9 separate members — and emits through the text/label helpers FUN_005dd09c x5, FUN_005c153f x5, FUN_005ca7c3 x4 (also FUN_005c60b6, FUN_005e4343, FUN_005c36cd/0x5c410a/0x5c40d0, FUN_005c3ca9, FUN_005c00a8, FUN_005c47c2, FUN_005c524c, FUN_005d26df, FUN_005fa02b, FUN_0064bac0).



## M227-M230 (s187, all PASS) - the +0x3098 stack-mirror; the panel tail field holds a POINTER TO a caller's block; [obj+0xb24] is a collision; FUN_00455c70 is a trampoline
`scripts/m227_m230_mirrors.py`, `evidence/m227_m230_mirrors.txt`. **M227** 0x3098 = 18 refs (8 member / 10 `[ebp-0x3098]`): FUN_0058dfd0/FUN_0058e2b0 hold a stack DIALOG at ebp-0x62c8 (0x6717cc, ctor FUN_00405ef0) whose panel subobject is [ebp-0x3098] (0x671d94) and whose hotspot LIST is [ebp-0x3230]. The 8 member takes call 0x5e7665 (clear, x5 counting the jmp) / 0x5e764f / 0x5e7678 (alloc) / 0x5e7917 (scan), never 0x5e774d or 0x403b00 -> never appended. **M228** +0x2144 = 54 refs / 24 stores (10 zero, 3 sentinel 0xffffffff, 11 register, 0 text imm); provenance frame-slot 8, .rdata 0x689f88 load 1, 0x7543d8 table-slot lea 2; callers FUN_005f86ad = 0x671d94+0x48, FUN_005f882f = +0x60, FUN_005f90d7 = +0xa8 (6 calls / 6 guards). **M229** [obj+0xb24] = 25 refs / 12 stores in 6 fns / 12 loads in 5 fns (0042d2c0, 00488e80, 004893e0, 004894c0, 00612c4c) + 1 test vs 0xffffffff; 0 read 0x774xxx; 1 indexes 0x7543d8 at stride 44; FUN_0041f450 stores 0x774c0c x4 + 0x774a80 x1; grid 0x774c38 = BSS (offset 0x374c38 > file 0x2ed000). **M230** FUN_00455c70 = 33-insn 0-store trampoline to 0x5dbdc0 x1 + 0x5e3412 x2, injecting 0x109/0x107/0x106/0x792a30 with arg1 as `this`; 15 sites (11 distinct BSS buffers, 4 registers); FUN_0045a320..FUN_0045a4a0 = 9 pair publishers (0x99aa9c+4i, 0x99aac0+4i).

## M231-M234 (s188, all PASS) - the pair staging arrays, the writer-free 0x774c38 grid, the 0x7543d8 record table, the trampoline's two callees
`scripts/m231_m234_staging.py`, `evidence/m231_m234_staging.txt` (17/17 gates, static + live reads).

**M231 the 0x99aa9c/0x99aac0 pair staging arrays** 9 publishers FUN_0045a320+0x30*i (15 insns, 2 args, 2 stores, 0 callees, 0 dereferences) publish their ARG VALUES into 0x99aa9c+4i and 0x99aac0+4i (the two slots are 0x24 apart, not adjacent). The 18 dwords [0x99aa9c,0x99aaf4) have 18 writers and their ONLY readers are FUN_0062d630 (6 direct sites) and FUN_0062d78d (0 direct sites, 0 code refs - it is slot +0x15c of vtable 0x679f98, the same slot offset the dialog family uses for its installer, M220). FUN_0062d630 is the CONSTRUCT: it installs 0x679f98 at [this+0] and 0x679f90 at [this+0x444], then both copy the 18 staging dwords verbatim into [this+0xab8..0xafc] (stride 4). Live: 3/9 pairs non-zero (i=2,4,5) and every value is a 0x774c38 grid-entry address.

**M232 the 0x774c38 grid has ZERO writers** of 39 stores naming [0x774a00,0x774e00) ZERO carry a region address in the destination and 39 in the source (FUN_0041f450 installs page bases into [ebx+0xaf0..0xb30]) - the region is written only through pointers. Its 9 entries (stride 0x2c) are handed out 24 times over 9 calls: 6 calls take a TRIPLE (0,3,6)/(1,4,7)/(2,5,8) - 3 to the 0x9978ac setters FUN_0045a530/590/5c0, 3 to the 0x99779c trio FUN_0045a680/6b0/6e0 - and 3 calls take the PAIR (e,e+6) to publishers i=2,4,5. Live every entry = {+0=0, +4=mapped data pointer, +8=9, +0xc=+0x10=+0x18=N, +0x14=+0x1c=0x14, +0x20..+0x28=0}, N=3 x6 / 0x43 x3; every staging slot reads back exactly the pointers its call passed, so the row's group data are POINTERS to grid records.

**M233 the 0x7543d8 record table** 3 writer sites image-wide: 2 folded stores of 0xd7 into +0x18/+0x1c of entry idx (idx=[ebp-0x4], `imul 0x2c`, inside FUN_00459490's loop bound 0x59 = 89 iterations) and 1 count store to 0x7543d4 (FUN_00459bb0). 0x7543d8 itself is never a destination: 13 base-takes = 2 push-as-arg (0x64bda0/0x64bc40), 5 receiver adjustors `add reg,0x7543d8` before a call (0x5dbcc4, 0x403b50 x2, 0x440c90 x2), 6 lea. 2 sites in FUN_005aa310 store `lea reg,[reg*4+0x7543d8]` into the panel's tail field [edi+0x2144] (M228's provenance; stride 4 against the 0xd7 writer's stride 0x2c - the same collision M229 found for [obj+0xb24]). Live: count 11, entries 0..15 = {+0 = 0x15064c0-0x40*i (mapped: entries point BACKWARD at 64-byte blocks), +4=0, +8=9, +0x18=+0x1c=0xd7, rest 0}.

**M234 the trampoline's callees** FUN_00455c70 gives its OWN arg1 to all three callees as `this` and injects (arg1=&0x792a30, arg2=0x109) for FUN_005dbdc0 and (0x107,0x109)/(0x106,0x109) for the two FUN_005e3412 calls. FUN_005dbdc0 (ret 0x1c = 7 args, 408 insns, 59 direct sites, 0 indirect calls) gates arg1 non-null through 0x5ca8d2, requires [ebp+0x18] and [ebp+0x1c] non-zero, returns 3 on 3 paths, reads [arg1+0x80] as the extent it compares arg3+arg5 against, allocates via 0x5be090 - a record consumer, not a formatter. FUN_005e3412 (ret 0x8, 91 insns, 0 callees of any kind, 14 sites) returns 7 when [this+4]==0, clamps both args with `and reg,0xff`, walks the [this+4] data rewriting 5 byte-matches of low(arg1) to low(arg2), length = [this+0xc]*[this+0x14]>>2 truncating (2 of 11 buffers have N*M %% 4 == 1). The 11 buffers FUN_00459bb0 passes are distinct BSS records of the same 11-dword grid shape.

## M235-M237 (s189, all PASS) — the 0x679f98 class, the record stamper, the write-only callback triple

`scripts/m235_m237_records.py` + `evidence/m235_m237_records.txt` (12/12 gates).
**M235** vtable 0x679f98 = 88 slots, +0x15c = FUN_0062d78d, next dword 0xfffffffc. EXACTLY 2 installs,
both `[reg+0]`, by TWO constructors: FUN_0062d630 (the 18-dword staging copy-in, M231) and FUN_0062d764
(41 B). Its 88 slot functions reference 0 string literals: the class is named structurally — 72 slots
implementation-identical to 0x6717cc, 71 to 0x671d94, 70 identical in all three, 15 unique (+0x0, +0x8,
+0x30, +0x40..+0x68). 87/88 have member-scale dispatchers (1920 sites; +0xf0 x301, +0x8 x282, +0x4 x252);
+0x0 none; +0x15c 28 sites. Largest member-scale call disp +0xf3c; larger call-through disps are indexed
function-pointer TABLES in .data (max +0x6a75a8), not slots.
**M236** the 9 at record +8 (grid 0x774c38, table 0x7543d8, the 11 trampoline buffers) has ONE emitter in
the image: `mov byte ptr [ecx+0x8],0x9` @0x5dbbd1 inside FUN_005dbb5f — a 33-insn, 0-call STAMPER that
zeroes +4..+0x28 and publishes the record pointer to ds:0x9965b8 (3 stores / 3 loads with FUN_005dbbe6
and FUN_005dbdc0, M234). +4 is allocated by FUN_005be090 (13 of the image's 55 "[reg+4] = eax within 8
insns of a call" sites, in 13 functions). Live: 9 grid +4 pointers = 2 clusters (6 x 0x70, 3 x 0x568),
all mapped; table entries' +0 step -0x40 (count 11) — block-strided allocations, not per-record mallocs.
**M237** the callback fields 0x2210/0x2224/0x2234 are write-only: 3 stores, 0 loads/calls/lea/add, while
their own block [0x21c0,0x2260) carries 118 sites and 80 loads (+0x21d0 x62). All 3 installs sit in ONE
installer FUN_005f3f5b (6102 B), same pointer into all three fields. No bulk copy reaches them (108
`rep movs` image-wide, 4 in 2 window functions naming only +0x21c0..+0x21d0). ds:0x9977f0 (the handle the
callback gates on): 2 stores, both absolute, both in FUN_005f1394, 7 loads, live 0x0 — no modal object,
so the triple is unverifiable from the box until a dialog is open.
