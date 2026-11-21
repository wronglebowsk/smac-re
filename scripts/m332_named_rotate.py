#!/usr/bin/env python3
"""M332 headroom rotation (s311-chain1): move the settled M262-M266 rows VERBATIM
out of NAMED.md into docs/named-archive-m332-rows.md.

NAMED.md was 246,133 B of a 250,000 B FAIL cap (3,867 B headroom, under the 5 KB
rotation trigger).  Nothing in the block is load-bearing for a current pick: the
view-table band, the allocator and the class-0x675964 layout were settled at
s205-s206 and the only successor that touches them is `## M267-M268` (kept in
place, and its "roles corrected by M267" note stays in the archive rows too).

Byte-exactness is ASSERTED, not promised: the block's sha1 is computed before the
move, the archive is re-read from disk, and the extracted block must hash the same.
"""
import hashlib, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = os.path.join(ROOT, "NAMED.md")
ARC = os.path.join(ROOT, "docs", "named-archive-m332-rows.md")
START = "## M262-M264 (s205, PASS 11/11)"
END = "## B5 (s207, BUILD track, PASS 9/9)"

STUB = """## M262-M266 (s205-s206, PASS 11/11 + 12/12) — FULL rows VERBATIM at `docs/named-archive-m332-rows.md` (s311-chain1 headroom rotation, sha1 SHA1PLACEHOLDER, byte-exact asserted by `scripts/m332_named_rotate.py`); this stub governs. Pre-mutation-law registry (no MU ids: the harness era began at M308); the gate ids below are the ones the archive rows carry.

- M262 the view table, band `0x7cdecc..0x7cdee8`: 426 mentions, exactly 1 store names it (`0x5803e1`, entry 0 = the static object); all 39 `[reg*4+0x7cdecc]` mentions in 12 functions are reads/cmps, 0 indexed stores (G1). Entries 1..7 are written by FUN_00580260's loop at `0x580392` (cursor `esi 0x7cded0`, bound `cmp esi,0x7cdeec`/`jl`, step `add esi,4` = 7 iters; body `push 0x22480; call 0x64bc20` → `push 1; mov ecx,eax; call 0x469650` (515-B SEH ctor, NOT the view ctor `0x518820`) → `mov [esi],eax` at `0x5803bb`); `xor eax,eax` feeds it only on the alloc-failure path — which is why M260 read the loop as a zero-fill (G2). `0x22480` named exactly once image-wide (`0x580397`), `0x224b8` zero times, delta `0x38` (G3). 35 address-of-band sites, 4 escapes and all 4 hand out `&DAT_007cdecc` (`0x50ba50/0x50baee/0x50bd98/0x517553`); the 4 lea'd cursors (`0x50a68a, 0x50a79e, 0x512ea5, 0x512fd1`) are re-read only (G4). Entry 1 (`0x7cded0`): 32 reads in ≥12 functions; the load-side FUN_00597ee0 walks entries 2..7 from `0x597f6d` clearing `*(entry+0x1dd74)` + calling FUN_00479e90(entry) (G5).
- M263 the band on LOAD: the writer set re-derives to 8 functions / 10 indexed stores {FUN_004e14d0 `0x4e153b`; FUN_004ef6d0 `0x4f0def`; FUN_0053a820 `0x53a8d9`+`0x53a90c`; FUN_00582fc0 `0x582fec`; FUN_00583c70 `0x583e1d`; FUN_005a3470 `0x5a3b95`+`0x5a3d3f`; FUN_005a7970 `0x5a7afd`+`0x5a86aa`} plus FUN_0051c750's walk store `0x51ca52` (G6). Only FUN_00596850 (call `0x596fd0`) and FUN_00597a70 (`0x597cc0`) call map_load_arrays `0x582260`; their depth-9 forward closure + their 4 callers = 276 functions and it meets the writer set in ZERO, and no band writer sits in a vtable slot → **the LOAD trusts the file's band bytes** (G7). FUN_00582260 itself has no band-shaped store; FUN_00583c70 has ZERO references in the image (no call, no imm32, no slot) so `0x583e1d` can never execute; the other writers hang off gameplay passes: FUN_004e14d0 ← FUN_00516b80 ← FUN_005186b0, FUN_004ef6d0 ← FUN_004f5a70, FUN_0051c750 ← FUN_0051f320, FUN_005a7970 ← 24 callers (G8).
- M264 the allocator + the record cursor: FUN_005be090 (72 B / 24 insns) is operator-new → FUN_00649e00 (29 B) → FUN_00649e70(size, `ds:0x99d5f8` = the heap handle, 1, 0, 0); the NULL path reports through the GLOBAL fn ptr `ds:0x671320` with `0x698890` "FATAL ERROR" + `0x69889c` "Windows has run out of virtual memory; the game will exit. Recom…", then `push 4; call 0x649c80`; no vtable slot holds it; 119 direct sites in 74 functions (G9) — the footing's "13 `[reg+4]` sites" are store-after-alloc sites, not dispatch: 14 sites in 13 functions store the new pointer at `[obj+4]` within 8 insns (`0x479647, 0x479da5, 0x47a0d0, 0x58aefc, 0x58af0d, 0x5be208, 0x5be4d8, 0x5be5fc, 0x5becb5, 0x5cca3c, 0x5dc1ed, 0x5e351a, 0x5e361c, 0x62cd28`) (G10). `ds:0x9965b8` — 6 mentions = 3 read/modify/write pairs, one per function — is a LINEAR RECORD CURSOR: FUN_005dbb5f (33 insns, ~150 callers) stamps a blank record (10 dword zero stores + `mov byte ptr [ecx+0x8],0x9`) and `add ecx,0x2c`; FUN_005dbbe6 (63 insns) gates `[rec+0x28]==0` and `[rec+4]!=0`, `sub edx,ecx` with `ecx = [rec+0x10]*[rec+0x14]`, and frees `[rec+4]` via FUN_0064a7f0 (19 B, 221 callers); FUN_005dbdc0 (1303 B, ret `0x1c`) is the FILLER — allocates `[rec+0x10]*[rec+0x14]` bytes at `0x5dc1ed`, stores the pointer at `[rec+4]`, then advances the cursor by the same product (G11).
- M265 the 7 blocks are class-`0x675964` objects: ctor FUN_00469650 (515 B), exactly 7 `call` sites {`0x40a027, 0x468fc0, 0x48dc7a, 0x4cb5cf, 0x50aaae, 0x5803b2, 0x59befc`}; its `[ebp+0x8]` flag gates `mov [this+0],0x675964` (`0x469681`, the only mention image-wide) so the sites passing 0 keep their own descriptor (G1/G2). Layout: `[0]` = descriptor `0x675964`, whose `dword[+4] = 0x21a6c` IS the base-subobject offset — the law holds for all three descriptors found this way (`0x675964→0x21a6c`, `0x6763fc→0x22050`, `0x678458→0x23d94`), each matching the `add ecx,K`/`lea ecx,[reg+K]` feeding `call 0x5e3b80` (53 callers) in its installer (G5); `[4]` = a lazily-freed pointer; `+0xc..+0x1dd6c` = **201 contiguous 608-B elements** (0x64bda0 constructs 4 at `+0xc` and 196 at `+0x98c`, element ctor/dtor `0x62514b`/`0x62516c`, the same ctor runs in place at `+0x1db0c`) — the 201st ends 8 B before the `+0x1dd74` the load-side clears (G3); `+0x1de28/+0x1e3b0/+0x1e938` via `0x5bee2f`, `+0x1eec8/+0x1eef4/+0x1ef20` via `0x617060`, `+0x1ef54` = 4 × 2756-B elements (ctor `0x6251d0` installs vtable `0x679e08`); the subobject at `+0x21a6c` has its vptr pair overwritten to `0x6725ac` there and `0x6725a4` at `+0x21eb0` (delta `0x444`, both vtable bases) — a pair stored at 5 sites in 1 ctor + 4 destructors {ctor FUN_00469650; dtors FUN_00421950, FUN_00518980, FUN_0059bec0, FUN_0059c1e0} (G4; roles corrected by `## M267-M268`). SIZE: FUN_005e3b80's stores top out at `+0xa10` and `0x21a6c + 0xa14 = 0x22480` = the allocation exactly (G6). Dispatch goes through `[desc+4]`: FUN_004412a0 calls slots +4/+8 of `0x6725ac` (= FUN_005cdd0a / FUN_005cdf82), the same two it also calls directly on the static instance `0x8cc520`; FUN_00479e90 frees `[this+4]` via `0x4017d0` then `this += [desc+4]` → `0x5e3d74` (G7).
- M266 FUN_00583c70 is dead code, not a split body and not a duplicate: 0 occurrences in .text operands AND 0 as an LE dword anywhere in the file image (all 8 sections) (G8); predecessor FUN_00583c20 rets at `0x583c6b`, four `0x90` pad bytes, then a real `push ebp/mov ebp,esp` prologue (G9); it is 1 of 8 functions in `0x583000..0x584300` with `n_callers==0` and all 8 have 0 address-taken dwords (G10); its 159-insn mnemonic signature matches 0 other functions ≥40 insns (G12); it is a terrain-record helper of FUN_00583c20's family — callees {`0x582000, 0x5b09b0, 0x625af1, 0x64a7f0`}, globals `ds:0x92a378/0x92a37c`, the stride-`0x2c` sibling's (G11). M263's band store `0x583e1d` can never execute.

Evidence (the rows above are the gate conclusions of these two runs): `evidence/m262_m264_census.txt:24` (SUMMARY M262/M263/M264: 11/11 gates PASS), `evidence/m265_m266_census.txt:13` (SUMMARY M265/M266: 12/12 gates PASS).
"""


def main():
    if "--verify" in sys.argv:
        # #346 P2: the tool is a ONE-SHOT migration; after the archive exists a
        # replay is refused.  --verify is the replay-safe mode, and it states
        # exactly what is byte-exact here: the ARCHIVED BLOCK is (sha1 over the
        # bytes re-read from disk).  The hot-file stub is NOT byte-compared
        # against STUB below — the stub shipped at s311 was shortened by hand
        # afterwards to buy headroom, so STUB is the ORIGINAL long form and the
        # live stub is only required to name the archive and carry its sha1.
        if not os.path.exists(ARC):
            sys.stderr.write("VERIFY FAIL: archive missing\n")
            return 1
        back = open(ARC, "rb").read().decode("utf-8")
        # rotate2 (M267-M271) APPENDED to this same archive afterwards, so the
        # region rotate.py hashed is bounded by rotate2's first heading — without
        # that bound the sha1 is not reproducible, which is itself a defect this
        # mode exists to catch.
        body = back[back.index(START):]
        cut = body.find("\n§rotation-2 (M332 headroom)", 1)
        assert cut > 0, "rotation-2's section marker not found in the archive"
        got = body[:cut].rstrip("\n")
        sha = hashlib.sha1((got + "\n").encode()).hexdigest()
        named = open(NAMED, "rb").read().decode("utf-8")
        moved = not any(l.startswith(h) for l in named.split("\n")
                        for h in (START, "## M265-M266"))
        stub = ("## M262-M266" in named) and (sha[:12] in named) and (ARC.split("/")[-1] in named)
        print("VERIFY archive block sha1=%s  moved-out-of-NAMED=%s  stub-names-archive+sha1=%s"
              % (sha[:12], moved, stub))
        print("STUB constant is the ORIGINAL long form; the live stub was shortened "
              "by hand at s311 — byte-exactness law applies to the archive only.")
        return 0 if (moved and stub) else 1
    src = open(NAMED, "rb").read().decode("utf-8")
    lines = src.split("\n")
    i0 = [i for i, l in enumerate(lines) if l.startswith(START)]
    i1 = [i for i, l in enumerate(lines) if l.startswith(END)]
    assert len(i0) == 1 and len(i1) == 1, (len(i0), len(i1))
    i0, i1 = i0[0], i1[0]
    assert i1 > i0
    block = "\n".join(lines[i0:i1])
    sha = hashlib.sha1(block.encode()).hexdigest()
    stub = STUB.replace("SHA1PLACEHOLDER", sha[:12])

    if os.path.exists(ARC):
        sys.stderr.write("archive already exists — refusing to double-rotate\n")
        return 1
    hdr = ("# NAMED archive — M262-M266 rows, moved VERBATIM out of `NAMED.md` at "
           "s311-chain1 (M332 headroom rotation).\nsha1 of the moved block: %s "
           "(byte-exact, asserted by `scripts/m332_named_rotate.py`).\n\n" % sha)
    open(ARC, "w").write(hdr + block + "\n")

    # re-read from disk and prove byte-exactness of what is actually on disk
    back = open(ARC, "rb").read().decode("utf-8")
    got = back[back.index(START):].rstrip("\n")
    assert got == block.rstrip("\n"), "archive block is not byte-identical"
    assert hashlib.sha1((got + "\n").encode()).hexdigest() == sha

    new = "\n".join(lines[:i0] + stub.split("\n") + [""] + lines[i1:])
    assert stub.split("\n")[0] in new and START not in new.split(stub)[0]
    open(NAMED, "w").write(new)
    print("moved %d lines / %d B out of NAMED.md" % (i1 - i0, len(block.encode())))
    print("sha1(block)=%s" % sha)
    print("NAMED.md %d B -> %d B (headroom to the 250,000 FAIL cap: %d B)" %
          (len(src.encode()), len(new.encode()), 250000 - len(new.encode())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
