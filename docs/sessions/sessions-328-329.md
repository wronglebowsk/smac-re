# Session notes archive — sessions 328-329

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-326-327.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 328-chain2 (2026-11-24) — M351: the CHOOSER-side producer — a unit row IS the negated TYPE ORDINAL (milestone/m351)
- ANSWER (`python3 -u scripts/m351_type_producer.py`): the modal 0x496ad0 returns **+item when
  (flags & 0x20) != 0**, **-item when clear** (`and eax,0x20` @0x49772a, `je` @0x49772f,
  `neg eax` @0x49777c); item = row+4 (0x401940), flags = row payload+8 (0x495480); same law in
  9 insns at 0x494e61-0x494e8f.
- THE ROW LIST IS TWO SECTIONS. A: idx 0..0x7f, item = cand[idx] @0x9267e4 (k<0x40 -> k,
  k>=0x40 -> owner*0x40|(k&0x3f)), flags |0x20 -> +item. B: i = 1..0x47,
  item = **i**, flags = 0x4960f0(i)|0x10 -> -i; 0x4960f0 returns only {0,1,2,3}, so 0x20 is
  ALWAYS clear on a B row — every B row negates unconditionally.
- WHICH FIELD: i is the **TYPE ORDINAL** — the same counter indexes `0x984d38 + 0x30*i` (name)
  and `0x984d44 + 0x30*i` (cost, M349's array; G10 cross-checks both parses). The design-id
  space (cand 192+, owner 3) is section A and returns POSITIVE.
- CHOOSER ALREADY SPEAKS -i: affordability asked with -i (`neg ecx`/`call 0x4e4350` @0x495c2f),
  and the base queue slot ds:0x8f0d60+0x50+4*[sub+0xb68] is tested against -i
  (`neg edx`/`cmp edx,[ebp-0x30]` @0x495e5c) while A tests +item @0x495aef. 0x418b54-0x418b57
  writes the return to base+0x50 when pos==0; 0 negs in the 381-insn path → sign made upstream.
- **RETRACTION (narrows M349):** M68's "cell 6 = item 195 -> -3" is a STALE cell read —
  the trace's verdict says "the candidate array re-sorted between the read and the click". The
  cell is a ROW counter (sub+0xa818 -> sub+0xa774 @0x495b00) and rows are FILTERED (0x5a6e70,
  `jne` skip @0x495b69), so cell != item. -3/-6 stand as type ordinals; 195/196 does not.
- ACCEPT `PASS M351: 15/15` `504c7342fb16273b`, x2 identical (`evidence/m351_x2.txt:2-4`,
  sha1 `6f53b29d`); harness 20/20 NO-OP ['MU20'] (`evidence/m351_mutate.txt:27`).
- OPEN: section A = "designs" is INFERRED (trace names only); which B31 loss is a raze;
  whether a completion stamps.

## Session 328-chain3 (2026-11-24) — M352: the writeback — its target, the key matrix, and `ds:0x6926ec` RETRACTED

- **ACCEPT** `python3 -u scripts/m352_persist_writeback.py` -> **`PASS M352: 7/7 gates`**,
  tables digest `d553194a9f6ddce9`; x2 byte-identical (sha1 `c8bbfda4`,
  `evidence/m352_x2.txt:4`, `evidence/m352_persist_writeback.txt:140`); `m352_mutate.py` -> **13/13** killed, NO-OP green
  (`evidence/m352_mutate.txt`).
- **THE 8 `call edi`** (0x58f11b..0x58f3a8) are ONE target: edi loaded once @0x58f106 from
  `ds:0x6710fc` = KERNEL32!WritePrivateProfileStringA (import dir; slot in .rdata, not writable;
  the slot's own dword is a .rdata RVA naming the same function). 0 mem-indirect calls; 20 direct.
- **WRITE keys = 13**: Prefs Format, Difficulty, Map Type, Top Menu, Faction, Preferences,
  More Preferences, Custom World (8 direct) + Semaphore/Announce/Rules/Customize/Time Controls
  (5 via FUN_0058f030). 12 write blocks LOAD a block cell (11/11 scalars + the 7-dword array;
  window presence, not value provenance); `Prefs Format` is `__itoa(0xb)` — a hardcoded stamp, NOT a cell. **The persist
  writes no cell it never read.**
- **READ asymmetry (image-wide, total):** 5 `GetPrivateProfileStringA` refs in 5 fns (0x58e5a0,
  0x58e640, 0x58e6c0, 0x58e760, 0x58e7f0); 52 attributed sites -> 35 keys. 13/13 written keys are
  read (0 write-only). Read but written NOWHERE (33 write sites / 28 keys): **`Laptop`**
  (0x6926fc/0x692704; twins + 2 loader sites) and **`Language`** (0x69270c).
- **RETRACTION (M350 OPEN "who sets ds:0x6926ec")**: nobody — it is not a variable. No store names the
  VA (moffs/mem-dest forms) and nothing materialises it as data; 7 uses all `push 0x6926ec` in the lpKeyName
  slot (the 7 four-byte VA occurrences are all push imm32, so nothing even materialises
  the address as data); the VA holds the literal `Prefs Format` (0x6926e8 = the `"0"` default of the same call).
  M350's "first read takes its key pointer from ds:0x6926ec" restated: the read's KEY IS it.
- **PROTOCOL**: `Prefs Format`=11 written once, read at 7 sites; `cmp eax,0xb` gates the 6 inline
  loader reads and all of FUN_0058e5a0 (mismatch -> caller's default); FUN_0058e760 (23 callers)
  reads ints with NO gate.
- **OPEN**: what `Laptop` selects (its atoi feeds masks @0x58ea12/0x58eb2b); the twins'
  0x3a7168/0x327168 return; whether any completion path re-persists.

## Session 329-chain1 (2026-11-24) — M353: the `0x999fa4` numeric band — its ONE indexed filler and four `$` consumers (milestone/m353)

- RUN `python3 -u scripts/m353_numeric_band.py` -> **PASS M353: 11/11 gates** digest `367fdae1d78979e5` (`evidence/m353_numeric_band.txt:87`), two renders byte-identical, stdout == committed evidence; harness `scripts/m353_mutate.py` -> **HARNESS PASS 14/14** `fd143532b283b01b` (`evidence/m353_mutate.txt:14`).
- GEOMETRY (V): numeric `0x999fa4` / owner `0x999fcc` / payload `0x999ff4` are 0x28 apart (10 dwords each); text `0x99a01c` stride 0x100 x10 -> `0x99aa1c` (`:77`).
- REFS (V): 16 = 11 absolute + 5 `[reg*4+0x999fa4]`; stores exactly 3 — `0x626597` SCALED (FUN_00626581), `0x442642` abs (cheat clamp, FUN_00442320), `0x626fd7` abs (FUN_00626f19 stores `0x64c460(0x99a01c)`'s return) (`:75-76`).
- FILLER (V): `FUN_00626581`, 33 B: `cmp [ebp+8],9; jle` else `mov eax,3`; store `[eax*4+0x999fa4]`; `xor eax,eax`; ret. 260 call sites, 242 with a literal k in 0..6, NONE above 9 (`:38-39,:78-79`).
- RETRACTION (V): M325/M324's `g999fa4 W={442642,626fd7}` was an ABSOLUTE-address census — the scaled store was invisible to it. Both rows patched in place in `NAMED.md`.
- CONSUMERS (V): in FUN_00625b20 — `$NUMBER`@625c2c, `$NUM`@625cec, `$HEX`@625e4b, each `__itoa(v,buf,10)`; arg3 of `0x64f980` IS the radix (`cmp [ebp+0x10],0xa`, then forwards it), so **`$HEX` prints DECIMAL** (`:80-81`).
- The 4th read `0x626091` is the `$#k` PREDICATE: k = char-0x30, `cmp numeric[k],1`, `setne`; that path has NO k bound while `$k` does (`cmp k,0xa`) (`:82`). Arithmetic: k=10 -> owner[0], 20 -> payload[0], 30 -> text[0] (`:83,:70`).
- OPEN: what the `$#` flag gates; numeric[0] is DUAL-USE (cheat clamp `0x442642` vs ENERGY read `0x4e032c`/`0x4e0336`); `0x64c460`'s semantic.
- CAP: NAMED headroom was 4,204 B (<5 KB trigger) -> `## B25` rotated VERBATIM to `docs/named-archive-m353-rows.md`, sha1 `dd4991b77b2528c9d3bf011d226165c14277c19d`, verify 8/8 (`evidence/m353_named_rotate.txt:9`); review #378: 10 findings (4 P1/6 P2) all fixed - geometry DERIVED from the writer body, G5 histogram pinned, G6 per-address mapping, G7 arg3 position, store-form census, RETRACT preserved through the rotation.
- PITFALLS: (a) a rotation stub gate written as `... or True` is vacuous — replaced with a real set-intersection check; (b) a PE section walk must read ImageBase at `pe+24+28`, not at the section-table base.
