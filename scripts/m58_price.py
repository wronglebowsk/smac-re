#!/usr/bin/env python3
"""M58: DERIVE the completion price the engine charges at 0x4efa52, from the tables.

The gate is `cmp [curbase+0x40], edi ; jge` at 0x4efa5e and `edi` is built at
0x4efa4b-0x4efa52 (disasm, scratch/m574/text.txt):

    0x4efa2c  mov ebx,[eax+0x50]      ; eax = DAT_0x8f0d60 = the current base record
    0x4efa31  mov cl,[eax+4]          ; the base's owner/faction byte (base_dump.py `fac`)
    0x4efa34  push -1 ; push 1 ; push ecx
    0x4efa3c  call 0x4e40a0           ; -> edi : the per-owner cost factor in TENTHS
    0x4efa41  mov edx,ds:0x68cbb0     ; the base index the visit is running
    0x4efa47  push 0 ; push edx ; push ebx
    0x4efa4d  call 0x5ac950           ; -> eax : the queued type's cost
    0x4efa52  imul edi,eax            ; price = factor_tenths * type_cost

Both callees are re-implemented here EXACTLY as the disasm/Ghidra bodies
(evidence/m53i_fn4e40a0.txt, ghidra_out/shard_015.c:23696) and every input is read
out of the live process (read-only /proc/<pid>/mem, no tracer): the mask, the two
scale globals, the per-owner switch field, the type record (+41 cost, +42 plan).

Nothing here is tuned to an observation: the script prints the derived number and
compares it with the tracer-measured edi (9, twice) as an ASSERTION, not an input.

    python3 scripts/m58_price.py [--owner 3] [--type 2] [--json]
"""
import argparse
import json
import os
import struct
import subprocess
import sys

TYPE_BASE, TYPE_STRIDE = 0x98AD88, 52          # references/open-leads.md (M53b)
OWNER_STRIDE = 0x20bc                          # 8380 B per owner record (Ghidra 0x20bc)
OWNER_COST_TENTHS = 0x94D6A0                   # the switch field 0x4e40a0 reads
MASK = 0x985B10                                # low byte: bit per owner -> factor 10
G_A290, G_A294, G_ADA8 = 0x92A290, 0x92A294, 0x92ADA8
G_A20434, G_85B30, G_85AEC = 0x920434, 0x985B30, 0x985AEC
G_68CBB8, G_68CBB0, G_8F0D60 = 0x68CBB8, 0x68CBB0, 0x8F0D60


def pid_of():
    env = os.environ.get("SMAC_PID")
    if env:
        return int(env)
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                         text=True).stdout.split()
    if not out:
        sys.exit("terran.exe not running")
    return int(out[0])


def trunc_div(a, b):
    """C signed division, truncating toward zero (what imul-magic + sar does)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", type=int, default=None,
                    help="owner/faction byte (default: read from DAT_0x8f0d60's record)")
    ap.add_argument("--type", dest="utype", type=int, default=None,
                    help="queued unit type id (default: [curbase+0x50])")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    pid = pid_of()
    with open(f"/proc/{pid}/mem", "rb", 0) as f:
        def rd(addr, n):
            f.seek(addr)
            return f.read(n)
        def u32(addr):
            return struct.unpack("<I", rd(addr, 4))[0]
        def s32(addr):
            return struct.unpack("<i", rd(addr, 4))[0]

        mask = rd(MASK, 1)[0]
        g_a290, g_a294, g_ada8 = s32(G_A290), s32(G_A294), s32(G_ADA8)
        g_20434, g_85b30, g_85aec = s32(G_A20434), s32(G_85B30), s32(G_85AEC)
        g_68cbb0 = s32(G_68CBB0)
        curbase = u32(G_8F0D60)
        brec = rd(curbase, 304) if 0x95DA10 <= curbase < 0x95DA10 + 304 * 64 else b""
        b_name = brec[19:59].split(b"\0")[0].decode("latin-1", "replace") if brec else None
        b_owner = struct.unpack("<i", brec[4:8])[0] if brec else None
        b_storage = struct.unpack("<i", brec[0x40:0x44])[0] if brec else None
        b_head = struct.unpack("<i", brec[0x50:0x54])[0] if brec else None

        owner = a.owner if a.owner is not None else b_owner
        utype = a.utype if a.utype is not None else (b_head & 0xFFFFFFFF)

        trec = rd(TYPE_BASE + utype * TYPE_STRIDE, TYPE_STRIDE)
        t_name = trec[:34].split(b"\0")[0].decode("latin-1", "replace")
        t_cost = trec[41]                       # +0x29 cost  (m53b_types.py / M53f)
        t_plan = trec[42]                       # +0x2a plan byte
        t_flag48 = trec[0x30]                   # +0x30, bit 4 -> the <64 early return

        sw = struct.unpack("<i", rd(OWNER_COST_TENTHS + owner * OWNER_STRIDE, 4))[0]

    # ---- FUN_004e40a0(owner, 1, -1): the per-owner cost factor in tenths ----
    steps = []
    in_mask = bool(mask & (1 << (owner & 0x1F)))
    if in_mask:
        v = 10
        steps.append(f"mask[0x{MASK:x}]&0xff has bit {owner} -> v = 10")
    else:
        # the else branch: 0x4e40c7-0x4e410b.  Not exercised for an in-mask owner;
        # reported rather than guessed (FUN_00531090 is not re-implemented here).
        v = None
        steps.append(f"mask bit {owner} clear -> v = ([0x{G_68CBB8:x}+{g_85aec}*4] "
                     f"- FUN_00531090(0x{G_85B30:x},0)!=0) - alt; NOT modelled")
    if v is not None:
        scale = g_a294                                    # param_2 == 1 -> the +4 variant
        if scale != 10:
            v = trunc_div(scale * v, 10)
        steps.append(f"scale 0x{G_A294:x}={g_a294} -> v = {v}")
        if g_ada8 == 1:
            v = trunc_div(v * 9, 10)
            steps.append("0x92ada8 == 1 -> v = v*9/10")
        elif g_ada8 == 0:
            v = trunc_div(v * 8, 10)
            steps.append("0x92ada8 == 0 -> v = v*8/10")
        else:
            steps.append(f"0x92ada8 == {g_ada8} -> v unchanged")
        # param_2 == 1 -> the switch on the per-owner field at 0x94d6a0 + owner*0x20bc
        if sw == 0:
            pass
        elif sw == 1:
            v = trunc_div(v * 9 + 9, 10)
        elif sw == 2:
            v = trunc_div(v * 4 + 4, 5)
        elif sw == 3:
            v = trunc_div(v * 7 + 9, 10)
        elif sw == 4:
            v = trunc_div(v * 3 + 4, 5)
        elif -7 <= sw <= -3:
            v = trunc_div(v * 13 + 9, 10)
        elif sw == -2:
            v = trunc_div(v * 6 + 4, 5)
        elif sw == -1:
            v = trunc_div(v * 11 + 9, 10)
        else:
            v = trunc_div(v + 1, 2)
        steps.append(f"switch [0x{OWNER_COST_TENTHS:x}+{owner}*0x{OWNER_STRIDE:x}]"
                     f" == {sw} -> factor_tenths = {v}")
        factor_tenths = v
    else:
        factor_tenths = None

    # ---- FUN_005ac950(type, DAT_0x68cbb0, 0): the queued type's cost ----
    p2 = g_68cbb0
    cost = t_cost
    clamped = ""
    if t_plan == 8 and p2 > -1:
        if cost == 0:
            cost, clamped = 1, " (byte +41 == 0 -> clamped to 1)"
        elif cost > 999:
            cost, clamped = 999, " (>999 -> clamped to 999)"
    early = utype < 0x40 or bool(t_flag48 & 4)
    steps.append(f"FUN_005ac950(type {utype} {t_name!r}, 0x{G_68CBB0:x}={p2}, 0): "
                 f"plan(+42)={t_plan}, cost(+41)={t_cost}{clamped}, "
                 f"type<0x40 or (+48&4)={early} -> cost = {cost}")

    price = None if factor_tenths is None else factor_tenths * cost
    out = {
        "pid": pid, "curbase": hex(curbase), "curbase_name": b_name,
        "curbase_owner": b_owner, "curbase_storage": b_storage, "curbase_head": b_head,
        "owner": owner, "type": utype, "type_name": t_name,
        "mask_byte": mask, "in_mask": in_mask,
        "g_a290": g_a290, "g_a294": g_a294, "g_ada8": g_ada8,
        "g_20434": g_20434, "g_85b30": g_85b30, "g_85aec": g_85aec,
        "g_68cbb0": g_68cbb0,
        "switch_field": sw, "factor_tenths": factor_tenths,
        "type_cost": t_cost, "type_plan": t_plan, "type_flag48": t_flag48,
        "price": price, "steps": steps,
    }
    if a.json:
        print(json.dumps(out))
        return
    for s in steps:
        print("  " + s)
    print(f"DERIVED price = factor_tenths {factor_tenths} * type_cost {cost} = {price}"
          f"   (owner {owner}, type {utype} {t_name!r})")
    print(f"tracer-measured edi at 0x4efa52 was 9 (evidence/trace_m574b.jsonl, "
          f"evidence/trace_m574c.jsonl) -> "
          f"{'MATCH' if price == 9 else 'NO MATCH'}")


if __name__ == "__main__":
    main()
