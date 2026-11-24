# NAMED.md `## M250-M254`, `## M277`, `## M326`, `## M246` — ROTATED VERBATIM
(byte-exact, by `scripts/m362_named_rotate.py`)

<!-- ## M250-M254 sha1 a9fc5ea5dbca1673 len 591 -->
## M250-M254 (s200-s201; PASS 7/7 + 7/7 + 7/7 + 8/8 + 8/8) — the region generator, the per-faction per-region verdict byte, the coarse map's single consumer, the four verdict codes, and the contact bits — FULL rows VERBATIM at `docs/named-archive-b28-rows.md:41` (§rotation-2 marker at `:40`, s316-chain1 review-round headroom rotation #2, sha1 `c839a606651b` — the region is bounded by its own terminator line, its line number AND the full digest re-asserted by `scripts/b28_named_rotate2.py --verify`); this stub governs. M254's bit-naming row stays INFERRED (named); every other row is V.

<!-- ## M277 sha1 6aa8eebae1f0d955 len 513 -->
## M277 (s218, PASS 6/6) - the scaled read is the permanent block-0 view; M274 G2's spill landing is arithmetically dead — FULL rows VERBATIM at `docs/named-archive-m337-rows.md:8` (§rotation-1 marker at `:7`, s318-chain1 headroom rotation, sha1 `653c93cda817` — the region is bounded by its own terminator line, its line number AND the full digest re-asserted by `scripts/m337_named_rotate.py --verify`); this stub governs. Every row is V; the M278 refinement (the player-index-0 real row) is archived with them.

<!-- ## M326 sha1 b35a213c4a689285 len 550 -->
## M326 (s301-chain2, STATIC 10/10, review #332 hardened) — FULL rows VERBATIM at `docs/named-archive-m338-rows.md:7` (§rotation-1 marker at `:6`, s319-chain2 headroom rotation, sha1 `a882ee40851d` — the region is bounded by its own terminator line and its digest is re-asserted by `scripts/m338_named_rotate.py --verify`); this stub governs. block+224 = the per-faction DEFERRED HURRY-PRODUCTION PAYMENT (energy debt), settled at upkeep; hurry defer-vs-pay flag chain 920434&91c62c, readers = AVAILABLE (220-224), reset 59f0bf/c1, save carry [0]*8.

<!-- ## M246 sha1 5fc00420de391631 len 757 -->
## M246 (s197) — the save's last 4 B are a `timeGetTime()` save-CREATION stamp — FULL rows VERBATIM at `docs/named-archive-b28-rows.md:10` (§rotation-1 marker at `:8`, s316-chain1 headroom rotation, sha1 `fcd4989fdf15` — the region is bounded by its own terminator line, its line number AND full digest re-asserted by `scripts/b28_named_rotate.py --verify`); this stub governs.
- `FUN_00597ce0` writes the trailing dword from `timeGetTime()` (`local_8` line 15 → `FUN_0064c9a0(&local_8,4,1,iVar2)` line 44), the codec never reads it; Δ(dword) vs Δ(mtime) ≤ 2.5 s on 5/5 same-session pairs | shard_015.c | V
- creation-stamped, not file-write-stamped: `0x15c79939` on 3 files 486,979 s apart, `0x2db1b939` on 2 files 71,224 s apart | census G3, 17 saves | V

