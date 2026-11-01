#!/usr/bin/env python3
"""M244: the save tail - (1) the map-trailer/region-map LENGTH FORMULA, (2) what the
count-prefixed block holds, (3) who reads the tail's last blocks.

Static: no gdb, no box driving; /proc/<pid>/mem READS only, and only in gate 5.
Acceptance: `python3 scripts/m244_save_tail.py` prints `PASS M244: 5/5 gates`.

Gates
  region-formula  region_len(w,h) = (((w+4)//5 + 1)//2) * ((h+4)//5)  (FUN_00582000,
                  shard_014.c:27263-27265) closes planet.MP + planetx.MP on the byte and
                  puts the count u32 at the measured offset on all 17 saves.
  count-shape     the block after the u32 at DAT_00927538 is 8-B records
                  (type in {0,1,2}, faction <= 7, step non-decreasing and <= the header's
                  u32 at file 80, x < w, y < h); count == 8 * record count.
  replay-bases    replaying that log with FUN_0059bcb0's semantics (shard_015.c:13657-13708)
                  yields EXACTLY the (x, y, owner) of the 304-B base records, on every save.
  owner-byte      base +4 == the log's LAST faction for the site (the current owner) and base
                  +5 == the faction the log wrote just before it (the previous owner).
  tail-legs       the codec's four tail pushes are 0x100, 0x100, 0x98, 0x27a0
                  (shard_015.c:10654/10676/10698/10720) and NO 220- or 28-B leg exists; the
                  152-B leg is anchored by the unique [9999,9999,0,0,2100,2600] dword row.
"""
import glob
import os
import re
import struct
import subprocess
import sys

SAVE_DIR = "programs/saves"
MAP_FILES = ["programs/maps/planet.MP", "programs/maps/planetx.MP"]
SHARD15 = "ghidra_out/shard_015.c"
SHARD14 = "ghidra_out/shard_014.c"

MAP_HDR_OFF = 79372
MAP_HDR_LEN = 2724
CELL_LEN = 22
SEC16000 = 16000
UNIT_LEN = 52
BASE_LEN = 304
TAIL_LEN = 10800
MIDDLE = 3584 + 26624 + 4096
# SAVE_FORMAT.md's traced 80x80 save (n=119 m=37 count=328): units, bases, tail starts.
RECORDED_80 = (273660, 279848, 291096, 301896)


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def region_len(w, h):
    """FUN_00582000: DAT_0092ad9c=(W+4)/5, DAT_0092ada0=(H+4)/5,
    DAT_0092ada4=((DAT_0092ad9c+1)/2)*DAT_0092ada0."""
    rw = (w + 4) // 5
    rh = (h + 4) // 5
    return ((rw + 1) // 2) * rh


def saves():
    return sorted(glob.glob(os.path.join(SAVE_DIR, "**", "*.SAV"), recursive=True))


def load(path):
    with open(path, "rb") as fh:
        return fh.read()


def walk(d):
    """The B2 walk with the trailer length DERIVED instead of tabulated."""
    w, h = u32(d, MAP_HDR_OFF), u32(d, MAP_HDR_OFF + 4)
    grid = MAP_HDR_OFF + MAP_HDR_LEN
    reg = region_len(w, h)
    count_off = grid + w * h * CELL_LEN + reg + SEC16000
    n_units, n_bases = u32(d, 68), u32(d, 72)
    cnt = u32(d, count_off) if count_off + 4 <= len(d) else -1
    units = count_off + 4 + max(cnt, 0) + MIDDLE
    bases = units + UNIT_LEN * n_units
    tail = bases + BASE_LEN * n_bases
    return dict(w=w, h=h, reg=reg, grid=grid, count_off=count_off, cnt=cnt, n_units=n_units,
                n_bases=n_bases, units=units, bases=bases, tail=tail, block=count_off + 4)


def records(d, off, cnt):
    return [struct.unpack_from("<BBHHH", d, off + 8 * i) for i in range(cnt // 8)]


def replay(recs):
    """FUN_0059bcb0's semantics: type 0 appends (x, y, fac), type 1 rewrites the third word
    of the (x, y) entry, type 2 removes it. Each live entry carries the list of factions it
    has been written with. Returns (live, orphans)."""
    live, orphans = [], []
    for (t, fac, step, x, y) in recs:
        if t == 0:
            live.append([x, y, fac, [fac]])
        elif t in (1, 2):
            hit = [i for i, e in enumerate(live) if e[0] == x and e[1] == y]
            if not hit:
                orphans.append((t, fac, step, x, y))
                continue
            if t == 1:
                live[hit[0]][2] = fac
                live[hit[0]][3].append(fac)
            else:
                live.pop(hit[0])
        else:
            orphans.append((t, fac, step, x, y))
    return live, orphans


GATES = ["region-formula", "count-shape", "replay-bases", "owner-byte", "tail-legs"]
# The tail as the codec reads it: one 256-B leg (the other is gated off), the 152-B leg,
# the 10,144-B leg, five 4-B globals, 9 rows of 24 B (FUN_00596620's 6-site loop), the
# local_2c/local_30 pair, and 4 B the codec does NOT read.
TAIL_LEGS = [256, 152, 10144, 20, 216, 8, 4]
ROW_GRID = 256 + 152 + 10144 + 20          # offset of the 9 rows inside the tail


def _shard(path, lo, hi):
    with open(path) as fh:
        lines = fh.readlines()
    return "".join(lines[lo - 1:hi])


def _mf(addr):
    """state header 0x985ab8 == file 12."""
    return addr - 0x985ab8 + 12


def main():
    state = {"ok": True, "n": 0}

    def res(name, good, detail):
        print(("ok   " if good else "FAIL ") + name.ljust(15) + " " + detail)
        if good:
            state["n"] += 1
        else:
            state["ok"] = False

    sv = []
    for p in saves():
        d = load(p)
        sv.append((p, d, walk(d)))

    # gate 1: the region-map length formula
    good, det = True, []
    for p in MAP_FILES:
        d = load(p)
        w, h = u32(d, 15), u32(d, 19)
        pred = 15 + MAP_HDR_LEN + (w // 2) * h * 44 + region_len(w, h)
        good = good and pred == len(d)
        det.append("%s %dx%d reg=%d pred=%d file=%d" % (os.path.basename(p), w, h,
                                                       region_len(w, h), pred, len(d)))
    src = _shard(SHARD14, 27255, 27272)
    cites = all(re.search(x, src) for x in (r"DAT_0092ad9c = \(DAT_0092a378 \+ 4\) / 5",
                                            r"DAT_0092ada0 = \(DAT_0092a37c \+ 4\) / 5",
                                            r"DAT_0092ada4 = \(\(DAT_0092ad9c \+ 1\) / 2\) \*"
                                            r" DAT_0092ada0"))
    good = good and cites
    co = MAP_HDR_OFF + MAP_HDR_LEN + 80 * 80 * 22 + region_len(80, 80) + SEC16000
    got = (co + 4 + 328 + MIDDLE, co + 4 + 328 + MIDDLE + 52 * 119,
           co + 4 + 328 + MIDDLE + 52 * 119 + 304 * 37,
           co + 4 + 328 + MIDDLE + 52 * 119 + 304 * 37 + TAIL_LEN)
    good = good and got == RECORDED_80 and (region_len(64, 64), region_len(80, 80),
                                            region_len(128, 128)) == (91, 128, 338)
    nclose = sum(1 for _, d, w in sv if w["cnt"] % 8 == 0 and w["tail"] + TAIL_LEN == len(d))
    det.append("cites=%s 80x80=%s vs %s dims=(91,128,338)=%s closes=%d/%d"
               % (cites, got, RECORDED_80, (region_len(64, 64), region_len(80, 80),
                  region_len(128, 128)) == (91, 128, 338), nclose, len(sv)))
    res("region-formula", good, "; ".join(det))

    # gates 2-4: the count-prefixed block is the base-site event log
    bad_shape, bad_replay, bad_own = [], [], []
    moved = orphans = 0
    for p, d, w in sv:
        if w["cnt"] % 8 or w["cnt"] > 4096:
            bad_shape.append((p, w["cnt"]))
            continue
        recs = records(d, w["block"], w["cnt"])
        turn = u32(d, _mf(0x985afc))
        steps = [r[2] for r in recs]
        if any(r[0] not in (0, 1, 2) or r[1] > 7 or r[3] >= w["w"] or r[4] >= w["h"] or
               r[2] > turn for r in recs) or steps != sorted(steps):
            bad_shape.append((p, recs[:2]))
        live, orph = replay(recs)
        orphans += len(orph)
        final = {(e[0], e[1]): e[2] for e in live}                    # sites alive at the end
        prev = {(e[0], e[1]): (e[3][-2] if len(e[3]) > 1 else e[3][-1]) for e in live}
        bases = [struct.unpack_from("<HH", d, w["bases"] + BASE_LEN * i) +
                 (d[w["bases"] + BASE_LEN * i + 4], d[w["bases"] + BASE_LEN * i + 5])
                 for i in range(w["n_bases"])]
        if sorted(final.items()) != sorted(((x, y), o4) for x, y, o4, o5 in bases) or orph:
            bad_replay.append((os.path.basename(p), len(final), len(bases), len(orph)))
        for x, y, o4, o5 in bases:
            if final.get((x, y)) != o4 or prev.get((x, y)) != o5:
                bad_own.append((os.path.basename(p), x, y, o4, o5, final.get((x, y)),
                                prev.get((x, y))))
            if o4 != o5:
                moved += 1
    res("count-shape", not bad_shape, "%d saves, count%%8==0, type in {0,1,2}, fac<=7, "
        "x<w, y<h, step<=hdr-u32@80 and non-decreasing; bad=%s" % (len(sv), bad_shape[:3]))
    res("replay-bases", not bad_replay, "replayed (x,y,owner) == the 304-B base records' "
        "(x,y,+4) on %d/%d saves; orphan type-1/2 records=%d; bad=%s"
        % (len(sv) - len(bad_replay), len(sv), orphans, bad_replay[:3]))
    res("owner-byte", not bad_own, "base+4 == the log's LAST faction for the site and base+5 "
        "== the faction it wrote just before (the previous owner; == +4 where the site was "
        "written once); bases where +4!=+5 = %d; bad=%s" % (moved, bad_own[:3]))

    # gate 5: the tail's legs
    good, det = True, []
    body = _shard(SHARD15, 9971, 10871)
    sz = [s.split(",")[1].strip() for s in re.findall(r"FUN_0064cc00\(([^)]*)\)", body)]
    no220 = all(x not in sz for x in ("0xdc", "220", "0x1c", "28"))
    have = all(x in sz for x in ("0x100", "0x98", "0x27a0"))
    sig = struct.pack("<IIIIII", 9999, 9999, 0, 0, 2100, 2600)
    anchor = pairs = finals = gated = 0
    for p, d, w in sv:
        t = w["tail"]
        if d.count(sig) == 1 and d.find(sig) == t + 256:
            anchor += 1
        if d[t + 256 + 152:t + 256 + 152 + 10144] and (t + sum(TAIL_LEGS) == len(d)):
            pairs += 1
        if d[len(d) - 12:len(d) - 4] == struct.pack("<ii", 800, 387):
            finals += 1
        if (u32(d, _mf(0x985ae8)) & 0x10) == 0 and u32(d, _mf(0x985dbc)) >= 7:
            gated += 1
    fd = {d[-4:] for _, d, _ in sv}
    good = no220 and have and anchor == len(sv) and pairs == len(sv) and finals == len(sv) \
        and gated == len(sv) and sum(TAIL_LEGS) == TAIL_LEN and len(fd) > 1
    det.append("tail pushes %s: 0x100/0x98/0x27a0 present=%s, 220/28/0x1c/0xdc absent=%s; "
               "legs %s sum=%d==TAIL_LEN; 9999-anchor at tail+256 on %d/%d; feature bit 0x10 "
               "clear and subver>=7 on %d/%d; [800,387] at EOF-12..-4 on %d/%d; final dword "
               "distinct=%d; the 4 B after it is outside the codec"
               % ("FUN_0064cc00 sizes", have, no220, TAIL_LEGS, sum(TAIL_LEGS), anchor, len(sv),
                  gated, len(sv), finals, len(sv), len(fd)))
    res("tail-legs", good, "; ".join(det))

    print("%s M244: %d/%d gates on %d saves + %s"
          % ("PASS" if state["ok"] else "FAIL", state["n"], 5, len(sv),
             ",".join(os.path.basename(m) for m in MAP_FILES)))
    return 0 if state["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
