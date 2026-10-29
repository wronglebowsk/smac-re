M92 | acceptance scripts/m92_tail_census.py NOT green (m92tail2-7 all FAIL) | merged NO | branch milestone/m92 @a6e221a+
The tail 0x5a9503-0x5a9698 is DECODED and validated on the engine's own finals (NAMED.md M92, SESSION_NOTES s144).
Left: the census dump/reader (literal dump end address, region-SIZE SNAPREGION, cover 0x94d448..0x966000 per round),
then who writes 0x94e488/0x94e5a8/0x94eda8 and the band tables 0x950664+edi*0x20bc.
Next: python3 scripts/m92_tail_census.py --tag m92tail8 --poke-index 5 --rounds 4 --timeout 100 (BACKGROUND)
