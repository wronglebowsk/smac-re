#!/usr/bin/env python3
"""M329 headroom rotation #2: the pre-M89 naming pile.

`## Method that worked` (right after `## B10`) is 12,564 B of s32-s60 prose + a tail of
header-less table rows (the B10 `## Not yet named` candidates and the M24-M28 gdb/watchpoint
rows). Every claim in it has a live successor in the registry (`## M327` for unit+10, `## B25`
for the move coordinate space, `docs/named-archive-m32-m84e.md` for M32-M84e), so the block
moves VERBATIM to `docs/named-archive-method-b10-era.md` and NAMED keeps the 4 method steps
plus a one-line-per-row pointer.

Same discipline as `scripts/m329_named_rotate.py`: sha1 asserted before the move, the archive
re-read and asserted to contain the block as a byte substring, refuses to run twice.
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARCH = os.path.join(ROOT, "docs", "named-archive-method-b10-era.md")
SHA1 = "16cd10eb5fc0"
HEAD = "## Method that worked"
STUB = r"""## Method that worked (steps kept; the s32-s60 row pile rotated VERBATIM to `docs/named-archive-method-b10-era.md`)
Hygiene rotation #2 at s307 (M329 headroom, paired with `scripts/m329_named_rotate.py`'s M255-M258 move): 56 lines, 12,564 B, sha1 `16cd10eb5fc0`, byte-exactness asserted by `scripts/m329_named_rotate2.py`; git history is the trail.

1. `scripts/coverage.py` ranks by in-degree *after* removing compiler helpers.
2. `scripts/fn.py <addr> --max 40` - read the shape: parameter types, which globals it touches, what it calls, whether string literals appear (`grep -oE '"[^"]{4,40}"'` on the body; none => pure logic => look at field offsets instead).
3. Follow one callee to see what the primitive is (here `0x5dd09c` => graphics state wrapper => the caller is a drawing routine, not a data routine).
4. Write the row with the offsets that justify it, so a later session can falsify it fast.

The rotated tail is the B10 `## Not yet named` candidates plus the M24-M28 gdb/watchpoint rows, one line per row, gates/cites unchanged in the archive:
`0x582260 map_load_arrays` (2,724 -> `0x92a378`, 140,800 = W*H*22, 128) | `0x596850 save_load` (796 -> `DAT_00985ab8`, section table) | `0x597a70 load_save_blocks` (**corrected** from the `.MP` map loader) | `0x95da10 base_array` (37 x 304 B, count `0x985af4`, name +19, x +0, y +2) | `0x933278 unit_array` (119 x 52 B; +10 owner? no - **+10 is the TYPE INDEX per `## M327`**, owner +14) | `0x8f79e0 ui_singleton_base` (= what Ghidra prints as `in_ECX`; `+0x23bd4` = `0x91b5b4`) | `0x91b5bc selected_unit_index` | `0x91b5b8 orders_mode_flag` | `0x91b5c4 order_menu_pending` | `0x91b5f0`/`0x91b670 cursor_x_list`/`cursor_y_list` | `0x4d3f70 activate_at_tile` | `0x476580 map_widget_click`/`map_click_handler` | `0x4cffa0 issue_move`/`issue_attack_or_engage` | `0x4cdc70 exec_action_with_target`/`bombard_resolve` | `0x528930 submit_unit_action` | `0x512450 hotkey_dispatch_unit`/`order_menu_command` | `0x511960 hotkey_dispatch_cursor` | `0x512b40 key_handler` (+ the arrow-key block M27) | `0x920434 netgame_flag` | `0x92ae14`/`0x692184 tile_record_array` / map row-count | `0x934aa4`/`0x934ba8` unit records 119/124 | `0x5acc00 unit_can_act` (M327-corrected) | `0x5acab0 unit_idle_and_own` | `0x5acdb0 consume_all_movement` | `0x5ac650 unit_movement_total` | `0x529090 solo_order_dispatch` | `0x4d6fb0 issue_order` | `0x4cce50` named-order engine | `0x50cab0 refresh_selection_state` | `0x5010d0 tile_cursor_display` | `0x50ba00`/`0x50ba90 set_map_pane_mode` | the unit-record field map (`+17` order byte, `+18/+19` waypoint legs, `+20/+28` order tiles, `+40` MP used, `+41` last dir, `+42` watchdog) | movement cost 3 MP/tile, 6 MP/turn | `0x4e1f90`/`0x5255e0` arrow-move pre-gates. Load-bearing successors: `## M327` (+10), `## B25` (the container owns the coordinate space), `docs/named-archive-m32-m84e.md` (M32-M84e).

"""


def main():
    t = open(NAMED, encoding="utf-8").read()
    if os.path.exists(ARCH):
        sys.exit("refusing: %s already exists (the rotation has run)" % os.path.relpath(ARCH, ROOT))
    i = t.index(HEAD)
    j = re.search(r"(?m)^## ", t[i + len(HEAD):]).start() + i + len(HEAD)
    blk = t[i:j]
    b = blk.encode("utf-8")
    got = hashlib.sha1(b).hexdigest()[:12]
    assert got == SHA1, "block sha1 %s != %s" % (got, SHA1)
    hdr = ("# NAMED.md archive - the B10-era method + M24-M28 naming rows (rotated VERBATIM at s307)\n\n"
           "Source: the `NAMED.md` block starting `## Method that worked` up to the next `## ` heading\n"
           "(`## (ARCHIVE) M89-M221...`): %d lines, %d B, sha1 `%s` - asserted byte-exact by\n"
           "`scripts/m329_named_rotate2.py`. `NAMED.md` keeps the 4 method steps and a one-line-per-row\n"
           "pointer. Grep here for the s32-s60 wording of these ids; git history is the trail.\n\n" % (blk.count("\n"), len(b), got))
    with open(ARCH, "w", encoding="utf-8") as f:
        f.write(hdr + blk)
    check = open(ARCH, "rb").read()
    assert b in check, "archive does not contain the block verbatim"
    with open(NAMED, "w", encoding="utf-8") as f:
        f.write(t[:i] + STUB + t[j:])
    after = len(open(NAMED, "rb").read())
    print("rotated %d B -> stub %d B; NAMED.md %d -> %d B" % (len(b), len(STUB.encode()), len(t.encode()), after))
    print("archive %s %d B, verbatim check PASS (sha1 %s)" % (os.path.relpath(ARCH, ROOT), len(check), got))


if __name__ == "__main__":
    main()
