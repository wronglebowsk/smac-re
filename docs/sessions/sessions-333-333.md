# Session notes archive — sessions 333-333

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-331-332.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 333-chain3 (2026-11-24) — M362: the 0x4db1xx sibling = the FACTION RELATIONS page; its +0x15a0 group = 13 ids that ARE the bits

- **PICK** (M360's alternate): "a second dialog with its own radio/flag block" -> the
  relations page (builder FUN_004db480: title = the faction name at 0x927874+f*0x59c, left
  list = every OTHER faction; +0xa1c = faction, +0xa20 = target), flag widget inline at
  dialog+0x15a0.
- **ACCEPT** `python3 -u scripts/m362_sibling.py` -> **`PASS M362: 22/22 gates`**
  `18298ed8d31de144` (`evidence/m362_sibling.txt:100`), re-run identical;
  `m362_mutate.py` -> **23/23 killed, 22/22 gates named**. Review #390's 8 findings fixed:
  G2b counts in-record slots, G4c binds the label call, G6c forbids unresolved forms, R3
  parses the delta, rotation idempotent.
- **13 rows, ids = bits**: 8,10,4,2,1,1000,2000,20,2000000,400,40000 read
  `0x94d448[fac*0x82f+tgt]`; 80000008,80002000 read `0x94d468` — the prefix picks the
  record's SECOND dword (+0x20 = slot +8); the high-id set IS the 0x94d468 row set.
- **INDEX**: all 13 blocks run one identical 6-insn idiom (shl 6/add/lea/shl 4/sub/add)
  = fac*0x82f + tgt; 0x82f dwords = 0x20bc B; the dialog indexes 12 slots, all in-record.
- **BUILDER** adds the same 13 ids in the same ORDER, one label each from
  FUN_0061482f(0x997b28, [0x997b20+off], 0), 13 DISTINCT slots a0c..a18/d90..dac/df8.
- **HANDLERS/WRITERS**: 0x4dabb0 (plain,A) -> 0x5518f0 clear / 0x551a20 set; 0x4dac30
  (high,B) -> 0x5519c0 / 0x551c40; 0x4dacc0 -> 0x551cf0 one-way; 0x4dad40 -> 0x551d70
  one-way. 4 of 6 writers store BOTH (p1,p2)/(p2,p1); 0x5518f0 also clears B's 0xC00.
- **TRAPS**: stores are RMWs via a copied register — census by FORM, not store shape;
  backward def-use must not cross a branch (0x551d70 arm 2).
- **ROTATION**: `scripts/m362_named_rotate.py` moved M250-M254/M277/M326/M246 VERBATIM to
  `docs/named-archive-m362-rows.md` (sha1 4/4, 2nd run a no-op); NAMED 246,262 B.
- **OPEN**: the 13 labels (0x997b20 heap); bit NOUNS (chain-2 lane); 0x94d5dc.

## Session 333-chain1 (2026-11-24) — B34: a FACILITY completion stamps NOTHING (no writer on the leg; the recorded bytes falsify the stamp at 3 discriminating completions)

`python3 -u -m sim.facstamp` -> **`PASS B34: 10/10 gates  5296fdad6d26caa3`** (`evidence/b34_facstamp.txt:99`,
re-run identical); harness 13/13, NO-OP `[]` (`evidence/b34_mutate.txt:16`). Answer to B33's gap: nowhere.
- **21 stores, and M342's 20 is SHORT BY ONE** (`:14,:88`): all 194 bitmap references are classified
  (11 direct + 183 address loads: 9 `lea`, 174 `mov`-imm, 10 feeding a store) -> API 2 / GRANT 11 /
  SET 1 / COPY 7. The miss is the screen's byte COPY at `4f0d60` (`mov [esi+eax*1],dl`); M342's lea-window was too
  short to reach it. COPY is the only LOSS-capable family.
- **Leg is writer-free, measured**: pop `FUN_004ef5d0` 88 insns, 0 bitmap refs, 0 API calls; the base screen
  (its only caller) 0 API calls, its only bitmap store the unit-only OR. API hosts ∩ pop hosts = ∅ (`:87-88`).
- **6 facility completions in the recorded run** (`:54-59`), not B31's 1: Korolev r0, Virgin Soil s1/s9 (head 2),
  New Jerusalem s1/s9 + Training Camp s15 (head 1). PAY = `st+1 >= 9` — testing `st >= price` misses Korolev.
- **3 discriminate, 3 are vacuous (bit already set)**; all 3 discriminating falsify the stamp ON BYTES
  (`:70-76,:92`): model `[8]`→`[2,8]` (Korolev), `[27]`→`[2,27]` (Virgin Soil) vs the recording's no-bit-2.
- **The 5 gains are not completions** (`:61-67`): before-heads 321/-2/-8/-3/-6 (unit-encoded); Virgin Soil s11
  (gain 4 + LOSS 27, no pay) is the COPY signature.
- **B31 QUALIFIED**: its single negative is real but is 3 boundaries, and it did not flag the vacuous rows.
- **Pitfalls**: `lea`-form writers need register-follow (`mov BYTE PTR [eax],cl` has no bitmap constant — a
  constant-only grep finds 11 of 20); `4f49e1` is a `mov` here (M342 said `and`); head 0 = empty queue, not item 0.
- NAMED 247,680 → 245,677 B by rotating `## B22` verbatim (`scripts/b34_named_rotate.py`, sha1 `524f63de`).

## Session 333-chain2 (2026-11-24) — M361: the A/V radio flags — 4 rows' pending state, 4 reader functions, relabel terminal = GENERIC set-label 0x5fa1e8

- **ACCEPT** `python3 -u scripts/m361_radio_flags.py` -> **`PASS  M361: 38/38 gates`
  `b92f1a61c041ae87`** (`evidence/m361_radio_flags.txt:165`), rerun byte-identical;
  `scripts/m361_mutate.py` -> **30/30 RED, NO-OP none** (`evidence/m361_mutate.txt:66`).
  Review #391 (10 findings, 3 P1) reworked the instrument: function-extent windows from
  index.csv, the commit scan is GLOBAL, "both ways" is now measured, census covers every
  addressing form, read mnemonics are broadened, mutant gate names are exact.
- **GEOMETRY**: flags = `widget+0xa18`, widgets `0x12cbc + k*0xb4c` (table 0x493fe0:
  0x4b->0x493f9d 0x136d4/0x12cbc, 0x4c->0x493f1c 0x14220/0x13808, 0x4d->0x493edc
  0x14d6c/0x14354, 0x4e->0x493f5d 0x158b8/0x14ea0). Ctor 0x48fed0 zeroes all four (`:75-85`);
  the 3 children are vtable objects (`call [eax+0xf0]`), master row 0x12cbc is not.
- **RELABEL TERMINAL**: 0x493ec0 -> `FUN_0061482f(0x997b28,id)` -> 0x5fa1e8(widget,text),
  which frees `[ecx+0xa7c]`, allocs strlen+1, strcpy; **10 call sites/4 fns, 0 flag
  displacements** -> generic set-label, not flag-aware.
- **READERS** 17 sites/4 fns: 0x493ec0 (4), 0x493ff0 (4), 0x492940 (3), 0x492030 (1 load +
  2 cmp); WRITERS 38/8 fns; 3 loner 0x14220 sites are BYTE stores in other classes (`:86-92`).
- **COMMIT** 0x492940: 0x14d6c -> `[+0xa50] |= 0x4000`; 0x14220 -> `[+0xa4c] |= 0x400` (ebx
  by def-use); 0x158b8 -> `[+0xa4c] |= 0x800`. Master 0x136d4 is never committed — 0x492030
  recomputes it as OR of the children (store 0, then 1 per cmp!=0).
- **TOGGLE** 0x493ff0: master-off clears all four + `and ch,0xf3`/`and ah,0xbf` (load from and
  store back to 0x985ab8/0x985abc; 0x400|0x800 / 0x4000 = the commit bits). Propagation runs
  BOTH ways: child ON -> master, and the master toggle -> all three children. **SEED**
  0x4930e0 reads `[+0xa50]` bits, writes each child flag + its relabel cmd.
- **RETRACTED**: none — M360's 0x4e/0x4c/0x4d reading holds; cmd 0x4b is the master row.
- **OPEN**: each row's noun (label text is runtime; 0x997b20's table is not in the file);
  0x4b87f0/0x4b8820/0x4b8a60/0x4b8af0 = audio on/off (INFERRED).
- NAMED: `## M360` rotated VERBATIM (docs/named-archive-m360-rows.md, sha1 e504b483); 247,881 B.
