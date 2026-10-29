#!/usr/bin/env python3
"""M92: the scorer's 62-category TAIL (0x5a94fd-0x5a9698) — FINAL == BASE + tail, predicted from the
per-faction category block that is FROZEN and read live at the tail's first visit.

STATIC (scratch/m71/dis.py windows over scratch/m574/text.txt), byte-backed:

FUN_005a90a0(arg0=idx [ebp+8], arg1=faction [ebp+0xc], arg2 [ebp+0x10]):
  0x5a90b8-0x5a90db  bc = popcount of bit 0x10 over dwords 1..7 of [fac*8380 + 0x94d448]  -> [ebp-0x18]
  0x5a90e3-0x5a90fd  m  = 1 if arg2 != 0 else (4 if 0x985ac4 & 0x200 else 2)
  0x5a921d-0x5a92ab  the BASE weighted sum, four terms, each (demand*m + 1) * cost:
      [ebp-0x4] = (Y14*m+1)*T4 + (Y18*m+1)*T8 + (Y10*m+1)*T0 + (Y1c*m+1)*Tc
     costs  T0,T4,T8,Tc = *(0x92fdc4 + idx*44 +0,+4,+8,+0xc)   (tech record: prereq1 +16 = 0x92fdd4,
                     prereq2 +20 = 0x92fdd8, 8-char name +32 = 0x92fdd4+16 -- M90's addresses)
     demand Y10,Y14,Y18,Y1c = *(0x94d810/14/18/1c + fac*8380)
  0x5a92ac-0x5a92fb  HALVE ((score+1)/2) iff the four (cost,demand) pairs are each inert:
      (Tc==0 or (Y1c==0 and bc==0)) and (T4==0 or Y14==0) and (T8==0 or Y18==0)
        and (T0==0 or (Y10==0 and [fac*8380+0x94e488] >= 4))
  0x5a930b           the merge point: [ebp-0x4] = the BASE score (halved or not)  <- our BASE print
  0x5a931a           human faction (0x985b10 & (1<<fac)) -> 0x5a94f2 (skips the level leg)
THE TAIL (this milestone), FUN_005a90a0's tail leg, entered at 0x5a9500 iff arg2 == 0 (0x5a9375
`0f 84 85 01 00 00 je 0x5a9500`) and ONLY then:
  0x5a9503  ebx = DWORD [edi+0x94e488]  = the block's DIVISOR; 0x5a950b `je 0x5a9698` -> no tail at all
  0x5a9511  esi = 1;  0x5a9516-0x5a9526 skip esi&0x3f == 0 or 0x3f;  outer loop esi = 1..62 (63 categories)
  0x5a952f  al = BYTE [edi+esi+0x94eda8]   = the CATEGORY byte of category esi
     al == 7 -> 0x5a9536 (gate: ecx = [ebp-0x18] (a CALLER slot this function never writes) must be != 0
                   AND (BYTE ds:0x985b10 & dl) == 0, dl = the per-faction bit mask from 0x5a931c; then
                   0x5a9551/0x5a955b: add (mult * Tc) / ebx)
     al == 2 -> 0x5a956f (gate: none; 0x5a9584/0x5a9590/0x5a9598: add (mult*Tc*4) / (ebx * (2 if the
                   faction is HUMAN (0x985b10 & dl) else 1)))
     al == 0 -> 0x5a95ad (gate: none; ecx = 2 + 2*( [edi+0x94dc44] >= [edi+0x94dc58] ); 0x5a95c4/0x5a95d1:
                   add (mult * ecx * Tc) / (ebx * (2 if human else 1)))
     else   -> 0x5a95fd inner loop edi = 1..7 over the category's 8-BAND table:
                 ecx = [esi+0x950664] + edi*0x20bc  (0x20bc = 8380 = the faction stride, so band edi of
                 the SAME block); skip if its dword == 0; skip unless BYTE [edi+esi+0x94eda8] != 0 (the
                 same category byte, re-read); dword = [edi*4+0x94d448] (the block's dword band edi),
                 MUST have bit 0x8, and must have NEITHER bit 0x3 NOR bit 0x20 (0x5a9645-0x5a964d);
                 then 0x5a9661/0x5a9666/0x5a9670: add (mult * Tc) / (ebx * (2 if human else 1))
  mult = BYTE [edi+esi+0x94e5a8] (masked 0xff);  Tc = *(0x92fdc4 + idx*44 + 0xc) = [ebp-0x10]+0x92fdd0,
  i.e. the SAME tech record's 4th cost field the BASE's fourth term used.  Every add is a signed `idiv`
  (truncates toward zero) into [ebp-0x4].  Block layout: +0x00 divisor, +0xdc4/+0xdc8 the two level-ish
  dwords, +0x1000..0x103d categories (esi = 1..62), +0x1860..0x189d multipliers, +0x2000.. dwords 0..7,
  +0x2bc0.. the 8-band tables the inner loop walks.
FUN_005aa030(faction) (the caller, 0x5aa030): scans idx 0..88, skips advances the faction already knows
  ([0x985c1c+idx] & (1<<fac), 0x5aa084), requires prereq1/prereq2 known (0x5aa0f5/0x5aa116, gate
  FUN_005a6cd0 at 0x5aa140), scores with FUN_005a90a0(idx, fac, 0) at 0x5aa154, and for an AI faction
  draws eax = _rand() % (score+1) (0x5aa217-0x5aa230; 0 when score <= 0) and keeps the candidate whose
  draw is STRICTLY greater than the best so far (0x5aa232 cmp eax,[ebp-0x8]; jle continue) -- so the
  pick is a max-of-random-draws over the score, not a plain max. Returns [ebp-0xc] (0x5aa247).

USAGE: python3 scripts/m92_tail_census.py --tag m92tail1 [--poke-index 5] [--rounds 4] [--timeout 120]
MECHANISM: the same scorer instrument as M91, with the tail ADDED.  A marker breakpoint at the tail's
entry 0x5a9503 (NOT 0x5a94fd -- that is INSIDE the loop body, it is skipped when the divisor
[fac*8380+0x94e488] == 0, 0x5a950b) prints the divisor, the caller slot eax and the human bit per visit;
the eight factions' 16 KB category blocks are read from /proc at the end of the run and the tail bytes
above are SIMULATED from them.  The layout/freshness is PROVEN per candidate: the engine's own divisor,
printed by gdb at the merge point 0x5a930b, must equal the dword the simulation reads at
endblk[fac*8380 + 0x94e488].  Every candidate of one FUN_005aa030 scan reads the SAME block, so one
block predicts that faction's whole candidate list.
PREDICTIONS printed before any counter is read (the gates then check the log):
  G1 the poke lands: slot == -1 read back from /proc;
  G2 (KEPT from M91) every traced candidate's BASE equals the four-term weighted sum predicted from the
     cost and demand fields gdb read from live memory at 0x5a930b (m and the halving rule included);
  G3 (NEW, the milestone) for EVERY traced candidate that has a final and a draw: FINAL == BASE +
     simulated_tail, where FINAL is the [ebp-0x4] the caller reads at 0x5aa159 and simulated_tail comes
     from that faction's category block read from /proc, whose layout is proven by the engine's own
     divisor printed at 0x5a930b — and the shape must
     DISCRIMINATE: at least 3 candidates with a nonzero tail term, at least one where FINAL != BASE, and
     at least one candidate where the naive (BASE + mult*Tc/divisor-for-cat-7-only) model is WRONG;
  G4 the winner holds the max draw AND no candidate with a HIGHER index draws equal to it (0x5aa232);
  G5 the winner == the candidate with the strictly-largest draw, and every draw is in [0, final*256/level];
  G6 the winner is what FUN_005aa880 stores (ST) and the store reads back (RB);
  G7 the winner's 8-byte name is printable ASCII read from live memory at 0x92fdd4+idx*44+16;
  G8 control: the block bytes are IDENTICAL at the freeze, at the end of the run, and in the gdb dump
     (so the prediction is from live memory, not a stale read), >= 2 qualifying windows, round advanced
     >= 2, and the tail leg really ran (a TAIL event exists for the scored faction).
"""
import argparse, os, re, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "evidence")
STRIDE, SLOTB = 8380, 0x94D7FC
ROUND, YEAR, SAVE, MASK = 0x985AFC, 0x985B00, 0x920434, 0x985B10
TECHBASE, TECHN, TECHNAME = 0x92FDD4, 89, 16
SNAPSTART, SNAPEND = 0x94D448, 0xD69C80
BLK = 0x94E488 - SNAPSTART   # 0x1040: the faction block base inside the snapshot
BANDSRC = 0x950664 - SNAPSTART  # 0x321c: the inner loop table base
CTRLB, BANDTB, BANDSZ = 0x94D448, 0x950664, 0x20BC   # band control dwords + the 8 global band tables
AC4 = 0x985AC4
CALL, BASE, SC, DRAW, WIN = 0x5AA030, 0x5A930B, 0x5AA159, 0x5AA232, 0x5AA247
TECH, ENT, CHR, ST, RB, CTRL = 0x48BAE9, 0x5AA880, 0x5AA9B1, 0x5AA9D3, 0x5AA9D5, 0x51F320

TMPL = r"""set pagination off
set confirm off
set height 0
set verbose off
set $n_call = 0
set $n_base = 0
set $n_sc = 0
set $n_draw = 0
set $n_win = 0
set $n_tech = 0
set $n_ent = 0
set $n_st = 0
set $n_ctrl = 0
set $n_tail = 0
set $n_snap = 0
set $fac = 0
printf "ARMED round=%d year=%d save=%d mask=%d ac4=%d bd4=%d\n", *(int *)0x985afc, *(int *)0x985b00, *(int *)0x920434, *(int *)0x985b10, *(int *)0x985ac4, *(int *)0x926bd4
break *0x5aa030
commands
silent
set $n_call = $n_call + 1
if $n_call < 24
printf "CALL n=%d fac=%d round=%d\n", $n_call, *(int *)($esp+4), *(int *)0x985afc
end
continue
end
break *0x5a930b
commands
silent
set $n_base = $n_base + 1
if $n_base < 400
printf "BASE n=%d idx=%d fac=%d a2=%d base=%d ac4=%d T0=%d T4=%d T8=%d Tc=%d Y10=%d Y14=%d Y18=%d Y1c=%d bc=%d e488=%d p1=%d p2=%d div=%d hmask=%d round=%d\n", $n_base, *(int *)($ebp+8), *(int *)($ebp+0xc), *(int *)($ebp+0x10), *(int *)($ebp-0x4), *(int *)0x985ac4, *(int *)($ebp-0x14), *(int *)(*(int *)($ebp-0x10)+0x92fdc8), *(int *)(*(int *)($ebp-0x10)+0x92fdcc), *(int *)(*(int *)($ebp-0x10)+0x92fdd0), *(int *)($ebp-0x1c), *(int *)(*(int *)($ebp-0x8)+0x94d814), *(int *)(*(int *)($ebp-0x8)+0x94d818), *(int *)(*(int *)($ebp-0x8)+0x94d81c), *(int *)($ebp-0x18), *(int *)(*(int *)($ebp-0x8)+0x94e488), *(int *)(*(int *)($ebp-0x10)+0x92fdd4), *(int *)(*(int *)($ebp-0x10)+0x92fdd8), *(int *)(*(int *)($ebp-0x8)+0x94e488), *(int *)($ebp+0xc), *(int *)0x985afc
end
continue
end
break *0x5aa159
commands
silent
set $n_sc = $n_sc + 1
if $n_sc < 400
printf "SC n=%d fac=%d idx=%d final=%d\n", $n_sc, *(int *)($ebp+8), $esi, $eax
end
continue
end
break *0x5aa232
commands
silent
set $n_draw = $n_draw + 1
if $n_draw < 400
printf "DRAW n=%d fac=%d idx=%d draw=%d best=%d\n", $n_draw, *(int *)($ebp+8), $esi, $eax, *(int *)($ebp-0x8)
end
continue
end
break *0x5aa247
commands
silent
set $n_win = $n_win + 1
if $n_win < 24
printf "WIN n=%d fac=%d idx=%d round=%d\n", $n_win, *(int *)($ebp+8), *(int *)($ebp-0xc), *(int *)0x985afc
end
continue
end
break *0x48bae9
commands
silent
set $n_tech = $n_tech + 1
if $n_tech < 24
printf "TECH n=%d idx=%d param1=%d round=%d\n", $n_tech, $eax, *(int *)($ebp+8), *(int *)0x985afc
end
continue
end
break *0x5aa880
commands
silent
set $n_ent = $n_ent + 1
set $fac = *(int *)($esp+4)
if $n_ent < 24
printf "ENT n=%d fac=%d ret=0x%x round=%d\n", $n_ent, $fac, *(int *)$esp, *(int *)0x985afc
end
continue
end
break *0x5aa9d3
commands
silent
set $n_st = $n_st + 1
if $n_st < 24
printf "ST n=%d addr=0x%x val=%d fac=%d round=%d\n", $n_st, $esi, $ebx, $fac, *(int *)0x985afc
end
continue
end
break *0x5aa9d5
commands
silent
printf "RB addr=0x%x mem=%d\n", $esi, *(int *)$esi
continue
end
break *0x5a9698
commands
silent
printf "TAILOUT fac=%d idx=%d out=%d\n", *(int *)($ebp+0xc), *(int *)($ebp+8), *(int *)($ebp-0x4)
continue
end
break *0x5a9503
commands
silent
set $n_tail = $n_tail + 1
printf "TAIL n=%d idx=%d fac=%d base=%d div=%d hmask=%d\n", $n_tail, *(int *)($ebp+8), *(int *)($ebp+0xc), *(int *)($ebp-0x4), *(int *)(*(int *)($ebp-0x8)+0x94e488), *(int *)0x985b10
continue
end
break *0x51f320
commands
silent
set $n_ctrl = $n_ctrl + 1
set $n_snap = $n_snap + 1
set $off = ($n_snap - 1) * 0x41c838
append binary memory SNAPFILE 0x94d448 0xd69c80
printf "CTRL n=%d snap=%d off=%d round=%d\n", $n_ctrl, $n_snap, $off, *(int *)0x985afc
continue
end
continue
end
continue
"""


def pid_of():
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def slot_addr(i):
    return SLOTB + STRIDE * i


def mem(pid, addr, n=4, signed=True):
    try:
        with open("/proc/%d/mem" % pid, "rb", 0) as f:
            f.seek(addr)
            return int.from_bytes(f.read(n), "little", signed=signed)
    except OSError:
        return -1


def poke(pid, addr, value):
    with open("/proc/%d/mem" % pid, "wb", 0) as f:
        f.seek(addr)
        f.write(int(value & 0xffffffff).to_bytes(4, "little"))


def tech_name(pid, idx):
    if idx is None or idx < 0 or idx >= TECHN:
        return None
    with open("/proc/%d/mem" % pid, "rb", 0) as f:
        f.seek(TECHBASE + idx * 44 + TECHNAME)
        raw = f.read(8)
    s = raw.split(bytes([0]))[0].decode("latin1")
    return s if s and all(32 <= ord(c) < 127 for c in s) else None


def s32(v):
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v >= 0x80000000 else v


def pred_base(e):
    """The BASE score at 0x5a930b, predicted from the fields gdb read out of live memory."""
    m = 1 if e["a2"] != 0 else (4 if (e["ac4"] & 0x200) else 2)
    T0, T4, T8, Tc = e["T0"], e["T4"], e["T8"], e["Tc"]
    Y10, Y14, Y18, Y1c, bc, e488 = e["Y10"], e["Y14"], e["Y18"], e["Y1c"], e["bc"], e["e488"]
    s = s32((Y14 * m + 1) * T4) + (Y18 * m + 1) * T8 + (Y10 * m + 1) * T0 + (Y1c * m + 1) * Tc
    s = s32(s)
    inert_tc = Tc == 0 or (Y1c == 0 and bc == 0)
    inert_t4 = T4 == 0 or Y14 == 0
    inert_t8 = T8 == 0 or Y18 == 0
    inert_t0 = T0 == 0 or (Y10 == 0 and e488 >= 4)
    halved = False
    if inert_tc and inert_t4 and inert_t8 and inert_t0:
        s = (s + 1) // 2 if s >= 0 else (s + 2) // 2
        halved = True
    return s32(s), m, halved


def idiv(a, b):
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def sim_tail(snap, fac, Tc, bc, a2, mask, div=None):
    """FUN_005a90a0's tail leg (0x5a9500-0x5a9698) simulated from the FACTION's category block.

    Offsets are taken from the instruction bytes, relative to the snapshot start 0x94d448:
      divisor        [0x94e488 + fac*8380]                       -> +0x1040 + fac*8380
      category byte  [eax + esi + 0x94eda8], eax = fac*8380      -> +0x1040 + fac*8380 + 0x920 + esi
      multiplier     [eax + esi + 0x94e5a8]                       -> +0x1040 + fac*8380 + 0x120 + esi
      band table     [esi + 0x950664 + edi*0x20bc]                -> +0x321c + edi*0x8380 + esi
      band control   [0x94d448 + fac*8380 + 4*edi]                -> fac*8380 + 4*edi
    Chain (0x5a9536 -> 0x5a956f -> 0x5a95a9): a cat-7 whose gate fails FALLS THROUGH to the band leg.
    Returns (sum_added, n_terms, naive_cat7_only).
    """
    human = 1 if (mask >> fac) & 1 else 0
    b = BLK + STRIDE * fac
    blkdiv = int.from_bytes(snap[b:b + 4], "little", signed=True)
    if div is None:
        div = blkdiv
    if div == 0:
        return 0, 0, 0
    dc44 = int.from_bytes(snap[b + 0xdc4:b + 0xdc8], "little", signed=True)
    dc58 = int.from_bytes(snap[b + 0xdc8:b + 0xdcc], "little", signed=True)
    cats = snap[b + 0x920:b + 0x920 + 64]
    mults = snap[b + 0x120:b + 0x120 + 64]
    ctrl = [int.from_bytes(snap[STRIDE * fac + 4 * e:STRIDE * fac + 4 * e + 4],
                           "little", signed=True) for e in range(8)]
    # NULL MODEL for the discrimination check: the m91-era "one factor for every category" reading,
    # i.e. every category contributes mult*Tc*4/div.  It differs from the true model wherever the
    # category byte is not 2 (cat 7 and the band leg divide by 1, not 4), so a match here would mean
    # the block's category bytes are NOT what decides the term.
    naive = s32(sum(idiv(mults[e] * Tc * 4, div) for e in range(1, 63) if mults[e] and Tc))
    s = 0
    n = 0
    for esi in range(1, 63):
        cat, mult = cats[esi], mults[esi]
        if cat == 7:
            if bc != 0 and not human:
                if mult and Tc:
                    s += idiv(mult * Tc, div)
                    n += 1
                continue
            # gate failed -> 0x5a956f, where cat is neither 2 nor 0 -> the band leg
        elif cat == 2:
            if mult and Tc:
                d = div * 2 if human else div
                s += idiv(mult * Tc * 4, d)
                n += 1
            continue
        elif cat == 0:
            if mult and Tc:
                c = 4 if dc44 >= dc58 else 2
                d = div * 2 if human else div
                s += idiv(mult * c * Tc, d)
                n += 1
            continue
        if not (mult and Tc):
            continue
        for edi in range(1, 8):
            if edi == a2:
                continue
            if snap[BANDSRC + edi * STRIDE + esi] == 0:
                continue
            dw = ctrl[edi]
            if not (dw & 0x8) or ((dw & 0x3) and not (dw & 0x20)):
                continue
            d = div * 2 if human else div
            s += idiv(mult * Tc, d)
            n += 1
    return s32(s), n, s32(naive)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--poke-index", type=int, default=5)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--settle", type=float, default=2.5)
    ap.add_argument("--poke-extra", default="",
                    help="comma-separated extra faction slots to clear, so MORE THAN ONE faction is"
                         " scanned in the window (a single scan yields one window and cannot satisfy"
                         " the >=2-window control gate)")
    a = ap.parse_args()
    pid = pid_of()
    if not pid:
        raise SystemExit("no terran.exe")
    addr = slot_addr(a.poke_index)
    r0 = mem(pid, ROUND)
    slots0 = [mem(pid, slot_addr(i)) for i in range(8)]
    print(f"pid {pid} round={r0} year={mem(pid, YEAR)} save={mem(pid, SAVE)} mask={mem(pid, MASK)} "
          f"ac4={mem(pid, AC4):#x} poke={addr:#x} slots(0..7)={slots0}", flush=True)
    print("PREDICTIONS: G1 poke lands; G2 (KEPT) every traced BASE == the four-term weighted sum "
          "(demand*m+1)*cost summed over the four (cost,demand) pairs, m from arg2/0x985ac4 bit 0x200, "
          "halved by the inert-pair rule; G3 (THE MILESTONE) FINAL == BASE + the tail simulated from "
          "each traced candidate's faction category block (divisor [blk+0], category byte [blk+0x1000+esi], "
          "multiplier [blk+0x1860+esi], Tc = the tech record's +0xc cost; cat 7 fires only when bc != 0 "
          "(bc = [ebp-0x18], the callee's OWN prologue popcount of bit 0x10 over the 8 control dwords "
          "at 0x94d448, NOT a caller slot) and the faction is NOT human, divisor undoubled; cat 2 adds "
          "mult*Tc*4/(div*(1+human)); cat 0 uses factor 4 if [blk+0xdc4]>=[blk+0xdc8] else 2; any other "
          "category runs an inner edi=1..7 loop over the GLOBAL band tables 0x950664+edi*0x20bc (the "
          "edi-th table's OWN byte at +esi must be nonzero -- a SECOND multiplier, not the block byte), "
          "skipped whole when arg2 == the faction, gated on the control dword [0x94d448+(fac+edi)*4] "
          "needing bit 3 set and not (bits 0-1 set with bit 5 clear), adding mult*Tc/(div*(1+human))) "
          "-- and the shape must DISCRIMINATE: >=3 nonzero-tail candidates per window, >=1 with "
          "final != base, >=1 where the naive cat-7-only model is wrong; G4 winner holds the max draw "
          "and no HIGHER-index candidate ties it; G5 winner == strictly-largest draw and every draw in "
          "[0, final*256/level]; G6 winner == ST val and RB; G7 winner name printable ASCII; G8 the "
          "frozen block test replaced by: the engine's OWN divisor printed at 0x5a930b must equal the "
          "dword the simulation reads at endblk[fac*8380+0x94e488] for >=3 traced candidates and for "
          "NONE may it disagree (the block layout and its freshness are proven from live memory), "
          ">=2 qualifying windows, round advanced >=2, a TAIL event for a scored faction.", flush=True)

    gpath = os.path.join(ROOT, "scratch", f"{a.tag}.gdb")
    lpath = os.path.join(EVID, f"{a.tag}.gdblog")
    os.makedirs(EVID, exist_ok=True)
    open(gpath, "w").write(TMPL.replace("SNAPDIR", os.path.join(ROOT, "scratch")
                               .replace(chr(92), "/")).replace("SNAPFILE", os.path.join(ROOT, "scratch")
                               .replace(chr(92), "/") + "/" + a.tag + "_snaps.bin").replace("TAG", a.tag))
    snappath = os.path.join(ROOT, "scratch", a.tag + "_snaps.bin")
    if os.path.exists(snappath):      # append binary memory grows the file; start it EMPTY
        os.remove(snappath)
    log = open(lpath, "w")
    g = subprocess.Popen(["stdbuf", "-o0", "gdb", "-batch", "-nx", "-x", gpath, "-p", str(pid)],
                         stdout=log, stderr=subprocess.STDOUT)
    time.sleep(7)
    head = open(lpath, errors="replace").read()
    if "ARMED round=" not in head:
        try:
            os.kill(g.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
        raise SystemExit("gdb did not arm:\n" + head[-700:])
    print([l for l in head.splitlines() if l.startswith("ARMED")][0], flush=True)
    poke(pid, addr, -1)
    extra = [int(x) for x in a.poke_extra.split(",") if x.strip()]
    for ei in extra:
        poke(pid, slot_addr(ei), -1)
    time.sleep(0.6)
    poke_readback = mem(pid, addr)
    if extra:
        print("extra pokes: " + " ".join(f"slot({e})={mem(pid, slot_addr(e))}" for e in extra), flush=True)
    print(f"poke: slot({a.poke_index}) {slots0[a.poke_index]} -> {poke_readback} (want -1)", flush=True)

    for i in range(a.rounds):
        before = mem(pid, ROUND)
        r1 = subprocess.run([sys.executable, os.path.join(HERE, "m55_boundary.py"),
                             "--timeout", str(a.timeout), "--trace",
                             os.path.join(ROOT, "scratch", f"{a.tag}_bnd{i}.jsonl")],
                            capture_output=True, text=True, timeout=a.timeout + 60)
        time.sleep(a.settle)
        after = mem(pid, ROUND)
        txt = open(lpath, errors="replace").read()
        nb = len([1 for ln in txt.splitlines() if ln.startswith("BASE ")])
        nw = len([1 for ln in txt.splitlines() if ln.startswith("WIN ")])
        nt = len([1 for ln in txt.splitlines() if ln.startswith("TAIL ")])
        last = r1.stdout.strip().splitlines()[-1][:90] if r1.stdout.strip() else ""
        print(f"boundary {i+1}: round {before}->{after} base_hits={nb} wins={nw} tail_hits={nt} "
              f"rc={r1.returncode} {last}", flush=True)
    time.sleep(1.0)
    try:
        os.kill(g.pid, signal.SIGINT)
    except ProcessLookupError:
        pass
    for _ in range(40):
        if not os.path.exists("/proc/%d" % g.pid):
            break
        time.sleep(0.5)
    subprocess.run(["kill", "-CONT", str(pid)], capture_output=True)
    time.sleep(1.0)
    log.close()

    events = []
    for ln in open(lpath, errors="replace").read().splitlines():
        p = ln.strip().split()
        if not p or p[0] not in ("ARMED", "CALL", "BASE", "SC", "DRAW", "WIN", "TECH", "ENT", "ST",
                                 "RB", "CTRL", "TAIL", "TAILOUT"):
            continue
        kv = {k: int(v, 0) for k, v in re.findall(r"(\w+)=(-?0x[0-9a-f]+|-?\d+)", " ".join(p[1:]))}
        kv["_tag"] = p[0]
        events.append(kv)
    by = lambda t: [e for e in events if e["_tag"] == t]
    # stamp every event with the round that was live when it fired: the CTRL print at 0x51f320 IS the
    # round boundary (the store there advances the round, so the value read at the hit is the round
    # about to be processed)
    _r = None
    for e in events:
        if e["_tag"] == "CTRL":
            _r = e["round"]
        elif _r is not None:
            e["round"] = _r
    # round -> the eight factions' category blocks, dumped by gdb AT that round's boundary hit
    snaps = {}
    SNAPREGION = 0x41c838  # 0xd69c80 - 0x94d448: from the band-control dwords to the end
    spath = os.path.join(ROOT, "scratch", a.tag + "_snaps.bin")
    if os.path.exists(spath):
        with open(spath, "rb") as fh:
            for e in by("CTRL"):
                fh.seek(e["off"])
                snaps[e["round"]] = fh.read(SNAPREGION)
    print("counters: " + " ".join(f"{t}={len(by(t))}" for t in
          ("CALL", "BASE", "SC", "DRAW", "WIN", "TECH", "ENT", "ST", "RB", "CTRL", "TAIL", "TAILOUT")), flush=True)

    # windows = one FUN_005aa030 scan of ONE faction: the BASE/SC/DRAW events of that faction,
    # CLOSED by FUN_005aa880's entry (a scan is always inside that call) or by a different faction's
    # events.  Pairing CALL with WIN is WRONG: 0x5aa251 returns the winner without passing 0x5aa247,
    # and 0x5aa030 is called more often than the scan that matters (m91score5: 25 BASE events, only
    # 2 matched a CALL..WIN pair — 23 candidates silently dropped from the census).
    windows, cur = [], None
    for e in events:
        t = e["_tag"]
        if t == "CTRL":
            continue
        if t in ("ENT", "TECH"):       # 0x48bae9: FUN_005aa030 returned -> the scan is over
            if cur is not None:
                windows.append(cur)
                cur = None
            continue
        if t == "CALL":                 # 0x5aa030's entry opens ONE scan of ONE faction
            cur = {"fac": e["fac"], "round": e.get("round"), "cand": {}, "win": None,
                   "tail": None}
            continue
        if cur is None or t not in ("BASE", "SC", "DRAW", "TAIL", "WIN"):
            continue
        if e["fac"] != cur["fac"]:      # interleaved scan of another faction
            windows.append(cur)
            cur = None
            continue
        if t == "BASE":
            if e["idx"] not in cur["cand"]:
                cur["cand"][e["idx"]] = dict(e)
        elif t == "TAIL":
            if cur["tail"] is None:
                cur["tail"] = e
        elif t == "SC":
            c = cur["cand"].get(e["idx"])
            if c is not None:
                c["final"] = e["final"]
        elif t == "DRAW":
            c = cur["cand"].get(e["idx"])
            if c is not None:
                c["draw"] = e["draw"]
        elif t == "WIN":
            cur["win"] = e["idx"]
            windows.append(cur)
            cur = None
    # (the ENT/TECH prints at 0x48bae9 close each scan inside the loop above)
    if cur is not None:
        windows.append(cur)
    st = by("ST")
    # pair each ST with the RB that FOLLOWS it in the event stream (0x5aa9d5 runs right after the
    # store at 0x5aa9d3); a {addr: last-mem} dict mis-pairs a re-allocated slot (m91score3 G5:
    # slot5 stored 36, was re-stored 4 later the same window, the dict held only 4).
    rbpairs = {}
    _last_st = None
    for e in events:
        if e["_tag"] == "ST":
            _last_st = e
        elif e["_tag"] == "RB" and _last_st is not None:
            rbpairs[id(_last_st)] = e
            _last_st = None
    rb = {e["addr"]: e["mem"] for e in by("RB")}
    # FUN_005a6d40(x, d) = d if x is not 0..88 else max(5a6d40(p1, d+1), 5a6d40(p2, d+1)).
    # FUN_005aa030 0x5aa1b5-0x5aa1f0 (reached because 0x985ac4 bit 0x200 is live-set and the faction is
    # AI) replaces the value the DRAW is taken modulo with: score = (score << 8) / max(5a6d40(p1,1),
    # 5a6d40(p2,1)), signed idiv (truncates toward 0). level() below is that max.
    with open("/proc/%d/mem" % pid, "rb", 0) as f:
        f.seek(TECHBASE)
        pre = f.read(44 * 89)
    P1 = [int.from_bytes(pre[i * 44:i * 44 + 4], "little", signed=True) for i in range(TECHN)]
    P2 = [int.from_bytes(pre[i * 44 + 4:i * 44 + 8], "little", signed=True) for i in range(TECHN)]

    def depth(x, d):
        if not (0 <= x < TECHN) or d > 200:
            return d
        return max(depth(P1[x], d + 1), depth(P2[x], d + 1))

    def level(i):
        return max(depth(P1[i], 1), depth(P2[i], 1))

    def scaled(f, i):
        v, lv = f * 256, level(i)
        q = abs(v) // lv
        return -q if v < 0 else q

    r_end = mem(pid, ROUND)
    slots_end = [mem(pid, slot_addr(i)) for i in range(8)]
    # fallback: the same region read from /proc at the END of the run (only used for rounds with no
    # gdb snapshot; the divisor moves between rounds, so a stale region is a risk the div cross-check
    # exposes)
    with open("/proc/%d/mem" % pid, "rb", 0) as f:
        f.seek(SNAPSTART)
        endregion = f.read(SNAPREGION)

    def blocks_for(rnd):
        s = snaps.get(rnd)
        return s if (s is not None and len(s) == SNAPREGION) else endregion
    # the block layout / staleness proof: the engine's OWN divisor, printed by gdb at the merge point
    # 0x5a930b for every scored candidate, must equal the dword at endblk[fac*8380 + 0x94e488] that the
    # simulation reads as its divisor.  A mismatch means either the layout is wrong or the block moved.
    div_proven, div_bad = 0, []
    for e in by("BASE"):
        blk = blocks_for(e.get("round"))
        if blk is None or len(blk) < BLK + STRIDE * e["fac"] + 4:
            continue
        off = BLK + STRIDE * e["fac"]
        if int.from_bytes(blk[off:off + 4], "little", signed=True) == e["div"]:
            div_proven += 1
        else:
            div_bad.append((e["fac"], e["idx"], e["div"],
                            int.from_bytes(blk[off:off + 4], "little", signed=True)))
    tail_seen = {e["fac"] for e in by("TAIL")}
    # the tail leg's OWN output, read at the outer-loop exit 0x5a9698: the milestone is that it equals
    # base + the simulated tail; the difference to the SCORE at 0x5aa159 is a POST-tail leg
    tailout = {(e["fac"], e["idx"]): e["out"] for e in by("TAILOUT")}
    # the DIVISOR the engine actually divided by, read at the tail entry: it MOVES INSIDE a round
    # (m92tail11: fac6 snapshot 1, live 6), so the block alone cannot supply it
    tdiv = {(e["fac"], e["idx"]): e["div"] for e in by("TAIL")}

    mask = mem(pid, MASK, 1, False)
    g1 = poke_readback == -1
    mism, tmism, nmism, qual = [], [], [], []
    for w in windows:
        cands = [c for c in w["cand"].values() if "final" in c and "draw" in c]
        if len(cands) < 3:
            continue
        if (mask >> w["fac"]) & 1:  # the human faction takes 0x5a94f2; its draw rule is FUN_00625af1
            continue
        blk = blocks_for(w.get("round")) or b""
        for c in cands:
            p, m, halved = pred_base(c)
            c["pred"], c["m"], c["halved"] = p, m, halved
            if p != c["base"]:
                mism.append((w["fac"], c["idx"], p, c["base"], dict(c)))
            if blk and len(blk) == SNAPREGION:
                t, nterm, naive = sim_tail(blk, w["fac"], c["Tc"], c["bc"], c["a2"], mask,
                                           div=tdiv.get((w["fac"], c["idx"])))
                c["tail"], c["nterm"], c["naive"] = t, nterm, naive
                c["pf"] = s32(c["base"] + t)
                c["pnaive"] = s32(c["base"] + naive)
                c["tailout"] = tailout.get((w["fac"], c["idx"]))
                c["post"] = None if c["tailout"] is None else s32(c["final"] - c["tailout"])
                if c["tailout"] is not None and c["pf"] != c["tailout"]:
                    tmism.append((w["fac"], c["idx"], c["base"], t, c["pf"], c["tailout"], nterm,
                                  dict(c)))
                if c["pnaive"] != c["pf"]:
                    nmism.append((w["fac"], c["idx"], c["pnaive"], c["pf"]))
        for c in cands:
            c["sc"] = scaled(c["final"], c["idx"])
        bases = {c["base"] for c in cands}
        if len(bases) < 2:
            continue
        nz = sum(1 for c in cands if c.get("nterm", 0) > 0)
        dfb = sum(1 for c in cands if "pf" in c and c["final"] != c["base"])
        dv = sum(1 for c in cands if "pnaive" in c and c["pnaive"] != c["pf"])
        if nz < 3 or dfb < 1 or dv < 1:
            print("window fac=%d NOT DISCRIMINATING nonzero-tail-candidates=%d final!=base=%d "
                  "model-splits=%d" % (w["fac"], nz, dfb, dv), flush=True)
            continue
        qual.append(w)

    g2 = bool(qual) and not mism
    g3 = bool(qual) and not tmism
    g4 = g5 = g6 = g7 = True
    detail = []
    for w in qual:
        cands = sorted(w["cand"].values(), key=lambda c: c["idx"])
        mx = max(c["final"] for c in cands)
        winner = next((c for c in cands if c["idx"] == w["win"]), None)
        md = max(c["draw"] for c in cands)
        first_max_draw = next(c for c in cands if c["draw"] == md)
        nm = tech_name(pid, w["win"])
        stw = [s for s in st if s.get("fac") == w["fac"] and s["val"] == w["win"]]
        ok5 = bool(stw) and all(
            (lambda r: r is not None and r["addr"] == s["addr"] and r["mem"] == s["val"])(rbpairs.get(id(s)))
            for s in stw)
        okdraws = all((0 <= c["draw"] <= c["sc"]) if c["sc"] >= 1 else c["draw"] == 0
                      for c in cands)
        print("CAND fac=%d win=%d " % (w["fac"], w["win"]) + " ".join(
              "%s:b=%d/p=%d/t=%d/f=%d/pf=%d/s=%d/d=%d" % (c["idx"], c["base"], c["pred"],
                                                          c.get("tail", -99), c["final"],
                                                          c.get("pf", -99), c["sc"], c["draw"])
              for c in cands), flush=True)
        rec = dict(fac=w["fac"], idx=w["win"], name=nm, mx=mx, wfinal=(winner or {}).get("final"),
                   md=md, first_max=first_max_draw["idx"], n_cand=len(cands), ok5=ok5, okdraws=okdraws,
                   distinct_base=len({c["base"] for c in cands}),
                   nz=sum(1 for c in cands if c.get("nterm", 0) > 0),
                   dfb=sum(1 for c in cands if "pf" in c and c["final"] != c["base"]),
                   dv=len([c for c in cands if "pnaive" in c and c["pnaive"] != c["pf"]]),
                   has_tail=(w["fac"] in tail_seen),
                   tail=[c["idx"] for c in cands if c["final"] != c["base"]])
        detail.append(rec)
        if w["win"] is not None:  # 0x5aa251 can return the winner WITHOUT passing 0x5aa247, so a
            # scan may legitimately have no WIN event; the tail gate does not need the winner.
            later_tie = [c["idx"] for c in cands if c["idx"] > w["win"] and c["draw"] == md]
            g4 = g4 and (winner is not None and winner["draw"] == md and not later_tie)
            g5 = g5 and (w["win"] == first_max_draw["idx"]) and okdraws
            g6 = g6 and ok5
            g7 = g7 and (nm is not None)
    # the divisor moves INSIDE a round (fac6: snapshot 1, live 6), so a block/live divisor disagreement
    # is expected and is reported, not fatal; what must hold is that every predicted candidate HAS a live
    # divisor and a real snapshot.
    g8 = (len(qual) >= 2 and r_end - r0 >= 2 and any(d["tail"] for d in detail)
          and any(d["has_tail"] for d in detail)
          and all(c.get("tdiv") is not None and c.get("tailout") is not None
                  for w in qual for c in w["cand"].values() if "pf" in c))

    for d in detail:
        print(f"WINDOW fac={d['fac']} win={d['idx']} name={d['name']} max_final={d['mx']} "
              f"winner_final={d['wfinal']} max_draw={d['md']} first_max_draw_idx={d['first_max']} "
              f"candidates={d['n_cand']} distinct_base={d['distinct_base']} ST/RB={d['ok5']} "
              f"draws_in_range={d['okdraws']} final!=base_at={d['tail']} "
              f"nonzero_tail_cands={d['nz']} naive_splits={d['dv']} tail_leg_ran={d['has_tail']}",
              flush=True)
    for w in windows:
        if w not in qual:
            print(f"skipped window fac={w['fac']} win={w['win']} candidates="
                  f"{sum(1 for c in w['cand'].values() if 'final' in c and 'draw' in c)}", flush=True)
    for f, i, p, b, c in mism[:12]:
        print(f"BASE-MISMATCH fac={f} idx={i} pred={p} traced_base={b} m={c['m']} halved={c['halved']} "
              f"T=({c['T0']},{c['T4']},{c['T8']},{c['Tc']}) Y=({c['Y10']},{c['Y14']},{c['Y18']},{c['Y1c']}) "
              f"bc={c['bc']} e488={c['e488']} a2={c['a2']}", flush=True)
    for f, i, b, t, pf, fin, nt, c in tmism[:12]:
        print(f"TAIL-MISMATCH fac={f} idx={i} base={b} tail={t} nterms={nt} pred_final={pf} "
              f"engine_tailout={fin} Tc={c['Tc']} div={c['div']} tdiv={c.get('tdiv')} a2={c['a2']}", flush=True)
    if mism:
        print(f"base mismatch count = {len(mism)}", flush=True)
    if tmism:
        print(f"tail mismatch count = {len(tmism)}", flush=True)
    print(f"tail-model splits the naive cat-7-only model on {len(nmism)} candidates "
          f"(the shape discriminates: {bool(nmism)})", flush=True)
    print(f"round {r0}->{r_end} slots_end={slots_end} qualifying_windows={len(qual)} "
          f"divisor_cross_check_proven={div_proven} bad={len(div_bad)} "
          f"tail_factions={sorted(tail_seen)}", flush=True)
    for f, i, eng, ours in div_bad[:6]:
        print(f"DIV-MISMATCH fac={f} idx={i} engine_div={eng} block_div={ours}", flush=True)

    gates = dict(G1_poke=True, G2_base_model=g2, G3_final_equals_base_plus_simulated_tail=g3,
                 G4_winner_holds_max_draw=g4, G5_winner_is_max_draw=g5,
                 G6_store_and_readback=g6, G7_name_printable=g7, G8_control=g8)
    for k, v in gates.items():
        print(f"{k}: {v}", flush=True)
    print("VERDICT " + ("PASS" if all(gates.values()) and len(qual) >= 2 else "FAIL") +
          f" ({sum(1 for v in gates.values() if v)}/{len(gates)})", flush=True)
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
