#!/usr/bin/env python3
"""M53b/M53f: re-implement FUN_00595820 (the unit-type cost calculator) in python and
check it against the live +41 byte of every populated type record.

Reads (all live, /proc/<pid>/mem, no tracer):
  type table    0x98ad88 stride 52 : +32 ability int, +36 chassis, +37 weapon,
                                    +38 armor, +39 reactor, +41 cost factor
  chassis table 0x92ae80 stride 0x90: +1 triad, +4 cost, +5 missile flag
  weapon table  0x92b950 stride 16  : +0 attack (s8), +2 mode, +3 cost
  armor table   0x92fd10 stride 16  : +0xa cost
  ability table 0x98aaf4 stride 28  : int0 (+0)  cost rule (-7..-1 or >= 0)
                                      int2 (+8)  flag word; bit 0x400 => +1 surcharge
                                      (both == alpha.txt #ABILITIES cols 1 and 4, verbatim;
                                      24 rows == the two loops' iteration bounds
                                      0x98ad94 / 0x98ad9c, disasm 0x595916 / 0x595998)

M53f (see evidence/m53f_findings.md): the ability-rule jump table 0x595ab4 is indexed
`rule + 7` (0x5958ac-0x5958b4) and its 7 bodies are, in table order,
    -7 0x595903 ccost+armor-2   -6 0x5958f8 ccost+wcost-2   -5 0x5958f3 armor+wcost-2
    -4 0x5958ea ccost-1         -3 0x5958e4 armor-1         -2 0x5958de wcost-1
    -1 0x5958bb min(max(wcost/armor_cost,0),2)   (idiv; negative quotient -> 0)
i.e. Ghidra's case labels WERE right; the real M53b gap was the land-chassis branch:
for triad not in {1,2} the second loop 0x59597b-0x5959a6 DOES feed the surcharge —
every set ability whose entry+8 (NOT +16) has bit 0x400 adds +1.  That is exactly the
Scout Rover / Scout Speeder off-by-1 (ability bit 1 = Deep Radar, flag word 0x43f).
`--legacy` reproduces the superseded M53b model (loop skipped, flag read at +16).

Prints only a compact digest: match counts by group + the mismatch rows.
"""
import json, struct, subprocess, sys

TYPE_BASE, TYPE_STRIDE = 0x98AD88, 52
CH_BASE, CH_STRIDE = 0x92AE80, 0x90
WP_BASE, WP_STRIDE = 0x92B950, 16
AR_BASE, AR_STRIDE = 0x92FD10, 16
AB_BASE, AB_STRIDE, AB_N = 0x98AAF4, 28, 24   # 24 = alpha #ABILITIES rows


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
    legacy = "--legacy" in sys.argv[1:]
    FLAG_OFF = 16 if legacy else 8      # M53b read the flag word at the wrong offset
    # entry+0 = the cost rule column, entry+8 = the 11-bit flag word (bit 0x400 = the
    # flag string's first character).  Both verified against alpha.txt #ABILITIES.
    abil = [(struct.unpack_from("<i", blob["ab"], i * AB_STRIDE)[0],
             struct.unpack_from("<i", blob["ab"], i * AB_STRIDE + FLAG_OFF)[0])
            for i in range(AB_N)]

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
        acc = acost           # uVar9 / bVar1 original copies
        acc_orig = acost
        wcost_orig = wcost
        sur = 0               # ebx / iVar7
        if ability:
            for b in range(AB_N):                       # 0x59588c-0x595921
                if not (ability >> b) & 1:
                    continue
                if sur:                                 # 0x59589a-0x59589e
                    sur += 1
                rule = abil[b][0]                       # 0x5958a2 *(int *)cursor
                if rule >= 0:                           # 0x5958a6-0x5958a8
                    sur += rule
                elif rule == -7:                        # jtbl[0] 0x595903 (+0x595908)
                    sur += ccost + acost - 2
                elif rule == -6:                        # jtbl[1] 0x5958f8
                    sur += ccost + wcost - 2
                elif rule == -5:                        # jtbl[2] 0x5958f3 -> 0x595908
                    sur += acost + wcost - 2
                elif rule == -4:                        # jtbl[3] 0x5958ea
                    sur += ccost - 1
                elif rule == -3:                        # jtbl[4] 0x5958e4  (edi = armor cost)
                    sur += acost - 1
                elif rule == -2:                        # jtbl[5] 0x5958de  (edx = weapon cost)
                    sur += wcost - 1
                elif rule == -1:                        # jtbl[6] 0x5958bb  (idiv wcost/armor)
                    q = 0 if acost == 0 else wcost // acost
                    sur += q if 0 <= q <= 2 else 2
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
        elif not legacy:
            # 0x59597b-0x5959a6: land chassis only.  entry+8 bit 0x400 (the alpha
            # #ABILITIES flag string's FIRST character) => +1 on the surcharge.
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

    # alpha.txt: #UNITS Cost/Plan columns + the shipped-table row counts (used to
    # separate corrupt type records from real formula failures).
    d = json.load(open("data/alpha.json"))

    def sec(k):
        v = d[k]
        return v["rows"] if isinstance(v, dict) else v
    urows = sec("UNITS")
    nCH, nWP, nAR = len(sec("CHASSIS")), len(sec("WEAPONS")), len(sec("DEFENSES"))
    explicit, plan = {}, {}
    for r in urows:
        f = r["fields"]
        if len(f) > 8:
            explicit[f[0]] = int(f[5])          # col 5 Cost (0 = Autocalculate)
            plan[f[0]] = int(f[4])              # col 4 Plan

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
        formula = cost(chassis, weapon, armor, ability, reactor)
        # M53f: FUN_00579f40 writes the alpha Cost over the formula result at 0x57a037
        # (guard: Cost != 0) and the alpha Plan over +42 at 0x57a02d (guard: Plan >= 0).
        # The loader only touches rows 0..min(n_rows,0x40)-1, i.e. the shipped ids.
        ov = explicit.get(name, 0)
        applied = bool(ov) and i < 0x40
        # not a real unit record: a chassis/weapon/armor index beyond the shipped alpha
        # tables, or reactor 0 (the 185 real rows all have reactor 1 or 2; every
        # reactor-0 row in the table is one of these 7 garbage rows).
        junk = chassis >= nCH or weapon >= nWP or armor >= nAR or reactor == 0
        rows.append((i, name, chassis, weapon, armor, ability, reactor,
                     ov if applied else formula, r[41], r[42], r[43],
                     formula, applied, junk))

    ok = [r for r in rows if r[7] == r[8] and not r[12] and not r[13]]
    ovr = [r for r in rows if r[12]]
    ovr_ok = [r for r in ovr if r[7] == r[8]]
    junk = [r for r in rows if not r[12] and r[13]]
    bad = [r for r in rows if r[7] != r[8] and not r[12] and not r[13]]
    print(f"rows={len(rows)}  formula==live +41: {len(ok)}  alpha-Cost override rows: "
          f"{len(ovr_ok)}/{len(ovr)}  stale/out-of-range records: {len(junk)}  "
          f"UNEXPLAINED mismatches: {len(bad)}  skipped(bad indices)={len(skipped)}")
    for r in skipped[:6]:
        print(f"  SKIP id{r[0]} {r[1][:20]} ch{r[2]} wp{r[3]} ar{r[4]} rx{r[5]}")
    print("alpha #UNITS rows with explicit Cost != 0 (override store 0x57a037):")
    for i, name, ch, wp, ar, ab, rx, pred, live, c42, c43, formula, applied, j in ovr:
        print(f"  {name:<22} alphaCost={pred:3d} live+41={live:3d} formula={formula:3d} "
              f"+42={c42} alphaPlan={plan.get(name)} +43={c43}")
    shipped = [r for r in rows if r[1] in plan]
    print("shipped #UNITS rows: live +42 == alpha Plan (override store 0x57a02d):",
          sum(1 for r in shipped if r[9] == plan[r[1]]), "/", len(shipped))
    if junk:
        print("stale records (index beyond the shipped tables, or reactor 0):")
        for r in junk[:6]:
            print(f"  id{r[0]:3d} {r[1][:22]:<22} ch{r[2]} wp{r[3]} ar{r[4]} rx{r[6]} "
                  f"(shipped max ch{nCH} wp{nWP} ar{nAR}) formula={r[11]} live={r[8]}")
    if bad:
        from collections import Counter
        print("UNEXPLAINED mismatch rows:")
        print("  delta(pred-live) histogram:",
              dict(sorted(Counter(r[7] - r[8] for r in bad).items())))
        for r in bad:
            print(f"  id{r[0]:3d} {r[1]:<24} ch{r[2]} wp{r[3]:3d} ar{r[4]:2d} ab{r[5]:#x} "
                  f"rx{r[6]} pred={r[7]:3d} live={r[8]:3d}")


if __name__ == "__main__":
    main()
