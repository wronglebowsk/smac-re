# NAMED.md `## M360` - ROTATED VERBATIM (byte-exact) by scripts/m361_named_rotate.py
<!-- block: every byte below is the original NAMED.md block -->

sha1 e504b48385833699e3c03db21c1bee231fa2a6ff  rows 8

## M360 (s331-c3) — NOT a seventh page: 0x37/0x38/0x39 are A/V RADIO rows (+0x7aec: 8 built, 11 queried), 0x50 the seventh widget's 4th id; a miss resolves to bit<count>. ev `evidence/m360_orphans.txt:137`
| claim | ev | conf |
|---|---|---|
| 7 widgets +0x5974/649c/6fc4/7aec/8614/913c/9c64; rows 8/12/14/8/13/4/7 (=66); queries 8/12/14/11/14/4/7 (=70) | `:12,:43-44,:50` | V MU1,MU3,MU4,MU19 |
| +0x7aec queries 0x37/38/39 unbuilt; +0x8614 queries 0x30; +0x913c built 0x30 (queried vs 0x8614, never painted), queries 0x50 | `:45,:120` | V MU5-7,18 |
| miss = bit<count> (scan 0, `jge` at count, shift `<node+0x14>`): 8/13/4 | `:55-70` | V MU8-10,MU21 |
| 0x37/38/39 = RADIO handlers (cls 1/2/3) relabelling ctrl 0x4e/0x4c/0x4d from a4c:11/10, a50:14 | `:89-93` | V MU11-13,MU22 |
| absent-id writes exactly [(0x913c,0x50)]; A/V+0x8614 bits unwritten; 7th block tests STALE a48&0x1000 | `:102-103,:114-116` | V MU14-17,MU23 |
| INF: 3 unbuilt A/V ids = Script.txt's unconsumed A/V tail (3=3 count) | `:130-132` | INF |

