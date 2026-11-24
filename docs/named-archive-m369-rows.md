# NAMED.md `## M361`, `## M363` — ROTATED VERBATIM
(byte-exact, by `scripts/m369_named_rotate.py`)

<!-- ## M361 sha1 5b172d91184d78ec len 1466 -->
## M361 (s333-c2) — the A/V radio flags: widget+0xa18 of 4 rows (0x12cbc+k*0xb4c). Readers = relabel 0x493ec0, commit 0x492940, aggregate 0x492030, seed 0x4930e0; relabel ends in generic set-label 0x5fa1e8. ev `evidence/m361_radio_flags.txt:160`
| claim | ev | conf |
|---|---|---|
| 0x136d4/14220/14d6c/158b8 = widget+0xa18; ctor 0x48fed0 zeroes 4; 3 children are vtable objects, master is not | `:75-85` | V MU7-9,23 |
| 0x493ec0 table 0x493fe0: cmd 0x4b..4e -> those flags x {12cbc,13808,14354,14ea0} | `:58-74` | V MU3-6,26 |
| flag -> 1 of 2 ids [997b20+10e0..10fc] -> 0x61482f -> 0x5fa1e8 at widget+0xa7c; 0x5fa1e8 has no flag (10 sites/4 fns) | `:66-74,:120-126` | V MU5,19-21 |
| commit: 14d6c->a50\|4000, 14220->a4c\|400, 158b8->a4c\|800 (def-use); master never committed | `:93-101` | V MU11-13 |
| 0x492030: master := 0 then 1 per child!=0; 0x493ff0 master-off clears all + (ch,f3)/(ah,bf); child ON -> master | `:102-119` | V MU14-18 |
| 0x4930e0 seeds flags from +0xa50 bits w/ relabel cmd; 55 sites = 17 reads/4 fns + 38 writes; 3 loners BYTE | `:4-57,:86-92,:140-147` | V MU1,2,10,22,24,25,27 |
| INF: the rows are the A/V radio group's pending state (label text is runtime; image .data absent) | - | INF |
| QUALIFIED by M363: the four callees are MIXER methods, not preference toggles - start/stop of a 16-slot voice table + the pair's enable/disable; 0 pref-cell sites in their closure | `evidence/m363_audio_callees.txt:11-53` | V M363 MU1-MU16 |

<!-- ## M363 sha1 65d68e56dea864c5 len 1616 -->
## M363 (s334-chain1, STATIC 18/18, zero box) — the four A/V audio callees touch the MIXER ONLY: 0 pref-cell sites in the bodies or their 8-fn closure, 6 in the handler. ACCEPT `python3 -u scripts/m363_audio_callees.py` -> **`PASS M363: 18/18`** `66b923f06f4e8866` x2 (`evidence/m363_audio_callees.txt:132`); harness 20/20 NO-OP `[]` (`evidence/m363_mutate.txt:46`). `:N` = line of that evidence.
| claim | ev | conf |
|---|---|---|
| bodies 0 absolute data operands; closure = them + 0x4b9330/0x4b9370/0x4b9460/0x4b94a0, also 0 | `:11-39` | V MU1(G2) MU2(G4) MU16(G1) MU17(G3) |
| cells 0x985ab8 = 121 sites/61 fns, 0x985abc = 99/33, **0 inside the closure** (pinned) | `:41-53` | V MU3(G5) MU5(G6a) |
| HANDLER 0x493ff0 holds all 6 cell sites (3 loads/3 stores); master-off: load both, `and ch,0xf3`/`ah,0xbf`, store both | `:55-62` | V MU4(G6b) |
| 12 call sites: 6 handler (`this=0x8a7920`), 6 in 5 mixer fns; 0 import-form calls in the closure | `:64-98` | V MU6 MU7 MU8 MU12; rivals R by MU1 |
| 0x4b8a60 = slot START (flag+0x24<-1, vtable+0x8c), 0x4b8af0 = STOP (<-0, +0x14), index*0x18, bound 0xf | `:81-86` | V MU9 MU10(G9) MU18(G9c) |
| 0x4b87f0/0x4b8820 = ONE guarded call each into slot 0x60/0x64 of `[this+0x14]` | `:88-91` | V MU11(G10) |
| table 0x4941ec: 0x4b->0x494154, 0x4c->0x494068, 0x4d->0x49400e, 0x4e->0x4940c3; start/stop pair 4/4 with the row store 1/0; the 0x4e row is NOT wired to audio (0x446490 + 2 vtable slots) | `:100-116` | V MU13 MU14 MU15 MU19(G13b) MU21(G12) |
| INF: slots = per-voice play/stop, the pair = master enable/disable; each slot's radio noun stays runtime | - | INF |

