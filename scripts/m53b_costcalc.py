#!/usr/bin/env python3
"""M53b: re-implement FUN_00595820 (the unit-type cost calculator) in python and
check it against the live +41 byte of every populated type record.

Reads (all live, /proc/<pid>/mem, no tracer):
  type table    0x98ad88 stride 52 : +32 ability int, +36 chassis, +37 weapon,
                                    +38 armor, +39 reactor, +41 cost factor
  chassis table 0x92ae80 stride 0x90: +1 triad, +4 cost, +5 missile flag
  weapon table  0x92b950 stride 16  : +0 attack (s8), +2 mode, +3 cost
  armor table   0x92fd10 stride 16  : +0xa cost
  ability table 0x98aaf4 stride 28  : int[0] special rule (-7..-1), int[4] bit 0x400

Prints only a compact digest: match counts by group + the mismatch rows.
"""
import json, struct, subprocess, sys

TYPE_BASE, TYPE_STRIDE = 0x98AD88, 52
CH_BASE, CH_STRIDE = 0x92AE80, 0x90
WP_BASE, WP_STRIDE = 0x92B950, 16
AR_BASE, AR_STRIDE = 0x92FD10, 16
AB_BASE, AB_STRIDE, AB_N = 0x98AAF4, 28, 25


def s8(v):
    return v - 256 if v > 127 else v


def main():
    pid = int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                             text=True).stdout.split()[0])
    blob = {}
    with open(f"/proc/{pid}/mem", "rb", 0) as f:
        f.seek(TYPE_BASE); blob["type"] = f.read(700 * TYPE_STRIDE)
        f.seek(CH_BASE); blob["ch"] = f.read(40 * CH_STRIDE)
        f.seek(WP_BASE); blob["wp"] = f.read(400 * WP_STRIDE)
        f.seek(AR_BASE); blob["ar"] = f.read(80 * AR_STRIDE)
        f.seek(AB_BASE); blob["ab"] = f.read(AB_N * AB_STRIDE)
    # variant 3 = the transcription that reproduces 180/188 rows: the land-triad
    # ability loop over the 0x400 flag does NOT feed the surcharge counter.
    variant = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    abil = [(struct.unpack_from("<i", blob["ab"], i * AB_STRIDE)[0],
             struct.unpack_from("<i", blob["ab"], i * AB_STRIDE + 16)[0]) for i in range(AB_N)]

    def cost(chassis, weapon, armor, ability, reactor):
        woff = weapon * WP_STRIDE
        wcost = blob["wp"][woff + 3]
        wmode = blob["wp"][woff + 2]
        watk = s8(blob["wp"][woff])
        acost = blob["ar"][armor * AR_STRIDE + 0xa]
        coff = chassis * CH_STRIDE
        triad = blob["ch"][coff + 1]
        ccost = blob["ch"][coff + 4]
        missile = blob["ch"][coff + 5]
        acc = acost           # bVar1 / uVar9 original copies
        acc_orig = acost
        wcost_orig = wcost
        sur = 0               # iVar7
        if ability:
            for b in range(AB_N):
                if not (ability >> b) & 1:
                    continue
                rule = abil[b][0]
                if sur and variant not in (1, 4) and not (variant == 2 and rule < 0):
                    sur += 1
                if rule >= 0:
                    sur += rule
                elif rule == -7:
                    sur += -2 + acc + ccost
                elif rule == -6:
                    sur += -2 + ccost + wcost
                elif rule == -5:
                    sur += -2 + acc + wcost
                elif rule == -4:
                    sur += -1 + ccost
                elif rule == -3:
                    sur += -1 + acc
                elif rule == -2:
                    sur += -1 + wcost
                elif rule == -1:
                    sur += 2 if acc == 0 else (min(wcost // acc, 2) if wcost // acc < 3 else 2)
        if triad == 1:
            acc = acc // 2
            ccost = ccost + reactor
        elif triad == 2:
            ccost = ccost + reactor * 2
            if acc > 1:
                ccost = ccost - 2 * acc
                acc = 2 * acc
                if ccost < 2:
                    ccost = 2
        else:
            if variant not in (3, 4):
                for b in range(AB_N):
                    if ((ability >> b) & 1) and (abil[b][1] & 0x400):
                        sur += 1
        if missile != 0 and watk > 98:
            return wcost_orig
        local_c = max(wcost, acc // 2 + 1)
        div = 2 << (reactor & 0x1f)
        v = (div // 2 + (ccost + acc) * local_c) // div
        if ccost == 1:
            v = v // 2 + 1
        if wcost_orig > 1 and acc_orig > 1:
            v += 1
        if triad == 0 and wcost_orig > 1 and acc_orig > 1 and ccost > 1:
            v += 1
        if triad == 1:
            if wmode != 11:
                v = (v + 1) // 2
        elif triad == 2:
            v = v // (2 if wmode > 2 else 4)
        floor = reactor * 2 - reactor // 2
        if v <= floor:
            v = floor
        if local_c == 1 and acc == 1 and ccost == 1 and reactor == 1:
            v = 1
        return ((sur + 4) * v + 2) >> 2

    # alpha #UNITS rows: name -> explicit Cost column (0 = autocalculate)
    d = json.load(open("data/alpha.json"))
    urows = d["UNITS"]["rows"] if isinstance(d["UNITS"], dict) else d["UNITS"]
    explicit = {}
    for r in urows:
        f = r["fields"]
        if len(f) > 5:
            explicit[f[0]] = int(f[5])

    rows = []
    skipped = []
    for i in range(700):
        r = blob["type"][i * TYPE_STRIDE:(i + 1) * TYPE_STRIDE]
        if len(r) < TYPE_STRIDE:
            break
        nm = r[:34].split(b"\0")[0]
        try:
            name = nm.decode("ascii")
        except UnicodeDecodeError:
            continue
        if len(name) < 3 or not name.isprintable():
            continue
        ability = struct.unpack_from("<i", r, 32)[0]
        chassis, weapon, armor, reactor = r[36], r[37], r[38], r[39]
        if (chassis * CH_STRIDE + 5 >= len(blob["ch"]) or weapon * WP_STRIDE + 3 >= len(blob["wp"])
                or armor * AR_STRIDE + 0xa >= len(blob["ar"]) or reactor > 12):
            skipped.append((i, name, chassis, weapon, armor, reactor))
            continue
        pred = cost(chassis, weapon, armor, ability, reactor)
        rows.append((i, name, chassis, weapon, armor, ability, reactor, pred, r[41], r[42], r[43]))

    ok = [r for r in rows if r[7] == r[8]]
    bad = [r for r in rows if r[7] != r[8]]
    print(f"rows={len(rows)} predicted==live +41: {len(ok)}  mismatched: {len(bad)}  skipped(bad indices)={len(skipped)}")
    for r in skipped[:6]:
        print(f"  SKIP id{r[0]} {r[1][:20]} ch{r[2]} wp{r[3]} ar{r[4]} rx{r[5]}")
    ex_bad = [r for r in bad if r[1] in explicit and explicit[r[1]] != 0]
    print(f"mismatches that ARE alpha rows with an explicit Cost: {len(ex_bad)}")
    for r in ex_bad:
        print(f"  alpha-explicit id{r[0]} {r[1]:<22} pred={r[7]} live={r[8]} alphaCost={explicit[r[1]]}")
    print("mismatch rows (all):")
    from collections import Counter
    hist = Counter(r[7] - r[8] for r in bad)
    print("  delta(pred-live) histogram:", dict(sorted(hist.items())))
    print("  mismatches with ability == 0:", sum(1 for r in bad if r[5] == 0))
    for r in bad:
        e = explicit.get(r[1], "-")
        print(f"  id{r[0]:3d} {r[1]:<24} ch{r[2]} wp{r[3]:3d} ar{r[4]:2d} ab{r[5]:#x} rx{r[6]} pred={r[7]:3d} live={r[8]:3d} alphaCost={e}")
    # alpha rows with explicit cost: does live == alphaCost?
    print("alpha #UNITS rows with explicit Cost != 0:")
    for i, name, ch, wp, ar, ab, rx, pred, live, c42, c43 in rows:
        if name in explicit and explicit[name] != 0:
            print(f"  {name:<22} alphaCost={explicit[name]:3d} live+41={live:3d} pred={pred:3d} +42={c42} +43={c43}")


if __name__ == "__main__":
    main()
