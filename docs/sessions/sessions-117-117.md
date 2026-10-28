# Session notes archive — sessions 117-117

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 117 (2026-10-28) — M75: the production sweep's MATCH SEMANTICS. ACCEPTANCE PASS (tag `m75sweep1`): the sweep marks EVERY valid UNMARKED designed record — the three bytes do NOT gate designed marking.

**Instrument.** `scripts/m75_sweep_replay.py`: implements FUN_00572800's loop from the
instruction bytes, predicts tid 194's marked set from live memory, reloads `m54b_clean.SAV`
(`m54a_load.py --relaunch`), enqueues 194 (`m57_ui_enqueue`), arms 4 hw watchpoints
(193/194/192/128), pokes storage 200, drives boundaries (early-stop when 193&194 carry
bit 2), compares prediction vs the stores. One real invocation:

    reload rc=0; PREDICTED sweep(194) marked set: [192, 193]
    boundary 0: rc=0 38s flags 193=0x41 194=0x41 192=0x01
    boundary 1: rc=0 71s flags 193=0x145 194=0x45 192=0x105
    events: 0x4efe67 tid194 0x45 | 0x5729de tid192 0x105 | 0x5729de tid193 0x145
    census diff: 192:0x01->0x105, 193:0x41->0x145, 194:0x41->0x45
    gates g1..g5 all True; newly_bit2=[192,193,194]; marked-untouched=[64,128,129,130,131]
    ACCEPTANCE m75sweep1: PASS (predicted=[192, 193] observed_sweep=[192, 193] tracer=0)

**RETRACTION (M74's sweep semantics).** s116 said the sweep marks records "whose
+0x24/+0x25/+0x26 match the produced unit's". FALSE for designed candidates: 192
(triple 00/02/00, tier-FAILING vs 194's 00/02/01 — tier25 rank[02]=03 > 194's byte 02)
WAS stored at 0x5729d5; 193 (matching triple) was stored; the marked designed
64/128/129/130/131 got NO store; alpha 0-13 got NO store. The sweep's live effect is
"mark every valid unmarked designed record" (the gate that discriminates is bit-2/validity,
not the bytes). The byte triple + tier tables + category gate are only reachable on the
alpha-candidate path (validator `0x5a6cd0(tid, produced_flag_byte)` then the three tier
tests); zero alpha candidates were marked this scenario, so that path stays UNTESTED.

**Fields (measured live, fresh save).** +0x24 selects the 144-byte row at `0x92ae80+(v*0x90)`
(same row M73's markup `C` byte `0x92ae81[+0x24*0x90]` and the build-base `==1` land test
read); the sweep's category gate compares those rows. `0x92b950[+0x24]` and `0x92fd18[+0x25/+0x26]`
are 16-byte-row tier tables, rank = row[0] (0x92b950: 00->01 01->02 02->04 03->05 04->06 05->08;
0x92fd18: 00->01 01->02 02->03 03->04 04->05 05->06); a tier test passes when candidate rank
(row[0], signed, >0 required) <= produced byte. Validator `0x5a6cd0(tid, shift)` = tech-table
record `[tid*0x14 + 0x92fdd4]` dw0 >= 0 and bit `shift` of ownership byte `0x985c1c[tech]`
(shift = produced record's +0x30 low byte; shift 0x41 here).

**Consequence for M73/M74.** At the FIRST designed production the sweep marks all remaining
unmarked designed records, so markup (`(C*P+50)/100`) is charged at most once per designed
record (only those already marked at load skip it from their first visit). Live: after the
run 192/193/194 carry bit 2; 192 ALSO still carries the 0x100 sweep marker.

**Open.** (a) why the marker clear `0x4ef398` (FUN_004ef380) cleared 193's 0x100 but not
192's (census 192=0x105 after; the clear writes +0x31, OUTSIDE the watched low WORD, so the
gdblog cannot show it — watch the HIGH byte or census-diff for 0x100 residue); (b) the
alpha-candidate path (validator+tiers) never fired — to exercise it: produce a designed unit
while an alpha designed... i.e. find a scenario where `0x5a6cd0(tid, flagbyte)` is true for
some tid<0x40 (needs `0x985c1c[tech]` bit `flagbyte&0x1f`... bit index >7 semantics unclear);
(c) the outer-loop block the sweep covers (edi start/tick: stores landed on 192/193 although
the entry computes edi=194*52 — the 64-record window arithmetic is NOT yet reconciled with
the instruction bytes); (d) other FUN_00572800 callers (shard_002 param_3=1, shard_012:20852,
shard_014:17826). NEXT pick: M76 — the 0x100 sweep marker: who clears it and for which
records (watch the +0x31 byte, census before/after a designed production).
Evidence: `evidence/m75sweep1.gdblog`, `evidence/m75sweep1_seq.jsonl`, traces `m75sweep1_r0..r1`.
