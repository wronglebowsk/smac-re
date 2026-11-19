#!/usr/bin/env python3
# M327 in-place registry patches: three earlier NAMED.md rows assert a weaker or now
# FALSE reading of the word at unit+10. Retract/qualify them in place (a retraction
# that lives only in SESSION_NOTES leaves the registry asserting the older claim).
import sys

P = "/home/paul/reverse/smac/NAMED.md"

ROW_OLD = ("| `0x933278` | `unit_array` (119 × 52 B) | live read: no ASCII anywhere, "
           "x at +0, y at +2, owner faction at +14, flags at +10;")
ROW_NEW = ("| `0x933278` | `unit_array` (119 × 52 B) | live read: no ASCII anywhere, "
           "x at +0, y at +2, owner faction at +14, **+10 = the unit's TYPE INDEX into "
           "the 8x64 type array at `0x98ad88` (M327 — NOT flags: the live value 128 and "
           "the saves' {128,130,131,256,320-323} are faction-band DESIGN ids, 25/25 with "
           "band == owner; a record's +12 word is 0 in all 67 of m54b_clean.SAV)**;")

ACT_OLD = "`+10` bits 0x40&0x400 not both"
ACT_NEW = ("`+10` bits 0x40&0x400 not both **(M327: +10 is the TYPE INDEX, so bit 6 there "
           "is bit 6 of the index — set on 6 of m54b_clean's 67 records — and 0x400 is bit "
           "10 of the word at +12, which is 0 in all 67; the pair carries no type meaning)**")

B25_OLD = ("INFERRED that the .exe shares the rule - `sim/save.py:52` marks it OPEN; "
           "whether the game ever writes +0/+2 of such a record is UNNAMED")
B25_NEW = ("**RETRACTED by M327 (was INFERRED)**: the .exe does NOT share the rule — +10 is "
           "a signed TYPE INDEX (**659** chains `movsx [u+0x933282]` -> x0x34 -> `+0x98ad88`, "
           "pinned `0x4bdec4-0x4bded4`), and `unit_set_position` 0x5ab320 writes the tile of "
           "whatever index it is handed with **0 branches on the path to its +0/+2 stores** "
           "(`evidence/m327_typeband_census.txt:756`); the exemption is decoder-side "
           "tolerance, and its only evidence (out-of-grid +0/+2 on band records) is OUR OWN "
           "`0xc0de00NN` poke of m113map.SAV (`:741-755`)")

EDITS = [(ROW_OLD, ROW_NEW), (ACT_OLD, ACT_NEW), (B25_OLD, B25_NEW)]


def main():
    s = open(P).read()
    for old, new in EDITS:
        n = s.count(old)
        print("edit on %r... : count=%d" % (old[:44], n))
        assert n == 1, "expected exactly 1 occurrence, got %d" % n
        s = s.replace(old, new)
    assert "flags at +10;" not in s
    # the only surviving copy of the old phrase is the quote inside THIS milestone's
    # own retraction row (NAMED.md:1478), not the B25 row it retracts.
    assert s.count("INFERRED that the .exe shares the rule") == 1, s.count(
        "INFERRED that the .exe shares the rule")
    assert B25_NEW[:40] in s
    open(P, "w").write(s)
    b = len(s.encode())
    print("PASS 3 rows patched in place; NAMED.md %d B; headroom vs the 250000 FAIL line = %d"
          % (b, 250000 - b))
    return 0


if __name__ == "__main__":
    sys.exit(main())
