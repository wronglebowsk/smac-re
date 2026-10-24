# m53q — every writer of the per-visit table 0x8f0ccc..0x8f0d1c, inside FUN_004e63b0

Line numbers = line no. in `gunzip -c evidence/m53j_text.txt.gz` (fn body starts line 298136).

## Summary
Rule: for each of 25 spiral candidates around the base in `*(0x8f0d60)`, `FUN_004e63b0` writes a
reason code (0 = usable; 2 = off-map / not explored; 4 = tile flag+nibble; 8 = unit; 0x20 = foreign
territory; 0x10 = tile also claimed by a nearby base), then folds "code != 0" into bitmask
`DAT_008f0d30` (0x4e6925-0x4e694f). 21/21 entries have a decoded predicate chain (all 21 traverse the
same per-iteration path, differing only in the spiral offset); entries 21-24 exist as code but their
stores land **past** the 21-dword window and are read by nothing.
Correction: 0x4e6925-0x4e694f is **inside FUN_004e63b0**, not 4e78e0 — fn ends `ret` at 0x4e6959
(line 298619). Built once per call: pass A (steps), pass B (neighbour bases), mask last.

## 1. Store map

| steps | value | store VA (asm line) | predicate in asm terms | inputs read | status |
|---|---|---|---|---|---|
| 0-20 | **1** | 0x4e63e8 (298155) | head guard `cmp ecx,0x54` / `jl 0x4e63f7` (0x4e63e3-6): falls through only when byte-offset ≥ 84 | `[ebp-0x8]` | VERIFIED **unreachable for 0-20**; writes 0x8f0d20-0x8f0d2c (steps 21-24), outside the window the mask loop scans (0x4e6946) |
| 0-20 | **2** off-map | 0x4e6442 (298184) | `y+DY[i]`: `js` / `cmp ebx,[0x92a37c]` `jge`; `x+DX[i]` wrapped when `[0x92a394]&1==0`, then `test edi,edi jl` / `cmp edi,eax jl` | DX 0x67850c[i], DY 0x678990[i] (0x4e63f7/0x4e6425), base x/y, w=0x92a378, h=0x92a37c | VERIFIED |
| 0-20 | **2** unseen | 0x4e6518 (298261) | skip if `[0x94d430+0x20bc*f] & 0x200` (`test ah,0x2` 0x4e64e8); else `test BYTE [tile+4],1<<f` == 0 (0x4e650f) | tile rec `*(0x92ae14)+(40*y+x>>1)*0x2c`, byte+4 = per-faction seen bits | bits VERIFIED, "seen/explored" INFERRED |
| 0-20 | **0** | 0x4e6533 (298269) | fall-through of every step that survived bounds+seen (`jmp` targets 0x4e6451/0x4e6527) | - | VERIFIED |
| 0-20 | **4** | 0x4e6563 (298284) | `test BYTE [tile+8],1` != 0 **and** `v=BYTE[tile+2]&0xf` with `0 <= v < 8` (0x4e654e-0x4e655d) | tile+8 (mask dword), tile+2 low nibble | bits VERIFIED, "improvement/level" INFERRED |
| 0-20 | **or 8** | 0x4e659f (298305) | `u=FUN_005a5c00(FUN_005ab130(x,y))`; `u>=0` (0x4e657f) and `FUN_005a6330(u,9,3,-1,-1)!=0` (0x4e6590) | tile list head; unit rec 0x933286+52*u | call chain VERIFIED; "carries order 3" INFERRED (NAMED.md:156) |
| 0-20 | **or 8** | 0x4e6635 (298352) | stack walk (head chain +0x24 0x4e65ac, then +0x22 0x4e663c): `BYTE[u.fac]!=f` (0x4e65e1) and `BYTE[u+0x19]` bit f set (0x4e660c) and `[0x94d448+0x20bc*f+4*u.fac]&3 == 0` (0x4e6628) | unit recs; stance table 0x94d448 | tests VERIFIED, "hostile foreign unit" INFERRED |
| 0-20 | **or 0x20** | 0x4e6699 (298388) | `o=FUN_004e3b50(f,x,y,0,0)`; `o>=0 && o!=f` (0x4e6659-62) and `[0x94d448+0x20bc*f+4*o]&3==0` (0x4e6675) and (no unit or `BYTE[u.fac]==f`) | 0x94d448 stance, tile+7 owner (0x4e3b76) | VERIFIED; "foreign territory, no treaty" INFERRED |
| 0-20 | **or 0x10** | read 0x4e68d6, RMW write 0x4e68de (298573-5) | loop B: for base b (≠`[0x68cbb0]`, dist(B)≤5) and step i with `[b+0x78]` bit i **set** (0x4e6783) whose tile is passable and dist(tile)≤2 (0x4e6892), any s with `x+DX[s]==tx && y+DY[s]==ty` (0x4e68a5-0x4e68d4) | bases 0x95da10 stride 0x130, count 0x985af4; per-base mask b+0x78 | VERIFIED |

Only 0x4e63e8 can set value 1, and it never reaches 0-20; nothing reads 0x8f0d20-0x2c
(`zgrep 8f0d2[0-9a-c]` → only the 0x4e6946 bound).

## 2. Control shape
1. **Arguments: none.** `call 0x4e63b0` at 0x4e78e9 (line 300034) is preceded only by the 4e78e0 prologue
   pushes (`push ebx/esi/edi` 0x4e78e6-8); nothing is pushed/moved for the call, and the callee reads no
   `[ebp+8..]`. Implicit inputs: `*(0x8f0d60)` = current base record → `x=(short)+0` 0x4e63be,
   `y=(short)+2` 0x4e63c1, `f=BYTE+4` 0x4e63ca; `w=0x692184` (row stride, 40) 0x4e63d0; 0x92a378/0x92a37c
   (80/80), 0x92a394 bit0 (clear = x wraps).
2. **Loop A** (0x4e63d9-0x4e66b2): `i=[ebp-0x8]`, init 0 (0x4e63d9), `+= 4` (0x4e66a9), tail
   `cmp eax,0x64` / `jl` (0x4e66ac-0x4e66b2) → i ∈ {0,4,..,96} = **25 iterations**; i is a **byte offset**
   into the table, so step = i/4 and the guard `i<0x54` splits 21 real steps from 4 out-of-radius ones.
3. **Loop B** (0x4e66b8-0x4e691f): base index `[ebp-0x1c]` 0→`[0x985af4]-1`, record ptr `[ebp-0xc]` =
   0x95da10 + 0x130*n; skip n==`[0x68cbb0]`; guard `mov ecx,5`-class dist ≤ 5. **Loop C** (0x4e6778-0x4e68fe):
   step `[ebp-0x10]` 0→0x14 (`cmp eax,0x15` 0x4e68f8) = 21 steps, filtered by `[b+0x78]` bit; inner
   step-match 0x4e68a5-0x4e68ea (ecx += 4, `cmp ecx,0x54`).
4. So the table is written **per step 0..20 for one base** (the base in 0x8f0d60), not per facility; loop B
   only or-s 0x10 into steps already written by loop A.
5. Spiral tables (dumped from .rdata, file off = 0x271000+VA-0x671000): DX@0x67850c =
   `0,1,2,1,0,-1,-2,-1,0,2,2,-2,-2,1,3,3,1,-1,-3,-3,-1,4,-4,0,0`;
   DY@0x678990 = `0,-1,0,1,2,1,0,-1,-2,-2,2,2,-2,-3,-1,1,3,3,1,-1,-3,0,0,4,-4`
   (steps 21-24 = (4,0),(-4,0),(0,4),(0,-4)). Consumers agree on 21: 0x4107be `cmp ecx,0x15`.

## 3. DAT_008f0c4c / DAT_008f0c68
- `0x8f0c68`: **written inside 4e78e0** at 0x4e7904 (line 300041) = `(int8)(*(0x8f0d60+6)) + 1`
  (`movsx ecx,BYTE [eax+6]` 0x4e78fc, `inc ecx` 0x4e7903); then decremented twice: 0x4e7c35-36 and
  0x4e7ec9-cd (`mov eax,ds:0x8f0c68` / `dec eax` / `mov ds:0x8f0c68,eax`). Not touched by 4e63b0.
- `0x8f0c4c`: **NOT FOUND in either function** — only reads (0x4e8225) inside 4e78e0's range. Its writers
  are outside: 0x4e8dbc (`mov ds:0x8f0c4c,esi`, in FUN_004e8d60), 0x4e90e0, 0x4f3063, 0x4f3110.

## 4. Pseudocode (25 slots; only 0..20 reach the mask)
```python
def build_table(base, fac) -> list:      # base = *(0x8f0d60); no args passed at 0x4e78e9
    W, H, FLAT = g(0x92a378), g(0x92a37c), g(0x92a394) & 1
    x, y, out = base.x, base.y, [0]*25
    for i in range(25):                                   # loop A, step = byte/4
        if i >= 21:
            out[i] = 1; continue                          # store is past the window (0x4e63e8)
        tx = x + DX[i] if FLAT else (x + DX[i]) % W       # INFERRED: bit0 set = no wrap
        ty = y + DY[i]
        if not (0 <= ty < H and 0 <= tx < W): out[i] = 2; continue
        if not (fac_rec(fac).bit9 or tile(tx,ty).seen[fac]): out[i] = 2; continue   # bit9 = INFERRED exemption
        if tile.mask8 & 1 and 0 <= (tile.b2 & 0xF) < 8: out[i] = 4   # INFERRED meaning
        u = first_unit(tx, ty)
        if u >= 0 and unit_has_order(u, 3): out[i] |= 8   # INFERRED: order 3 = works the tile
        for v in tile_stack(tx, ty):                       # 0x933286 + 52*v, +0x24 then +0x22
            if v.fac != fac and v.facbit[fac] and stance(fac, v.fac) & 3 == 0:
                out[i] |= 8                                # INFERRED: stance 0 = hostile
        o = tile_owner(fac, tx, ty)                        # 0x4e3b50, tile byte+7
        if o >= 0 and o != fac and stance(fac, o) & 3 == 0: out[i] |= 0x20
    for b in bases(0x95da10, 0x130, g(0x985af4)):          # loop B
        if b.idx == g(0x68cbb0) or dist(x, y, b.x, b.y) > 5: continue
        for i in range(21):                                # loop C
            if not (b.mask78 >> i) & 1: continue           # bit set = step available for b
            tx, ty = b.tile(i)
            if b.fac != fac and (tile(tx,ty)[0] & 0xE0) >= 0x60: continue
            if dist(x, y, tx, ty) > 2: continue            # INFERRED
            for s in range(21):
                if wrap(x+DX[s]) == tx and y+DY[s] == ty: out[s] |= 0x10
    return out
# dist(a,b) 0x4e6733-0x4e6759 VERIFIED instrs: mx=max(|dx|,|dy|), mn=min, mx-((( |dx|+|dy|)>>1 - mn +1)>>1)
# mask 0x4e6925-4e694f: mask = OR(1<<k for k in 0..20 if out[k] != 0); out[21..24] ignored
```
