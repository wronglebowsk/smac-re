# CURSOR s322-chain1 / M342
ID: M342 (ANALYSE static) - who SETS +0x8c.
ACCEPT `python3 -u scripts/m342_completion_setter.py` -> PASS M342: 6/6, digest
2b88df5da5aeafe1 (`evidence/m342_completion_setter.txt:190`), 2x identical; harness 7/7 [] (`evidence/m342_mutate.txt:10`).
ANSWER: FUN_004e44f0(item,base,set): out1=idx out2=mask, `or BYTE PTR [304*base+idx+0x95da9c],mask`
@0x4e4528 (AND @0x4e4546), 27 sites/8 fns; pop FUN_004ef5d0 never touches it.
MERGED? milestone/m342. NEXT: which API caller completes production.
NAMED 248,127->241,089 (M329 VERBATIM named-archive-m329-rows.md:5).
