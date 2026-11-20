#!/usr/bin/env python3
"""s308 retraction verification (P1#4/P2#6 of the #339 review): the call-site retraction's
decisive facts were measured by shell greps, not by the census. This instrument re-derives
them from scratch/m574/text.txt (the same objdump window the census reads), PRINTS the counts,
then ASSERTS them. Direct-call and direct-jmp targets are DECODED FROM THE ENCODING BYTES
(e8/eb/e9 rel); the "who else could reach this frame" classes (FF /2 indirect calls, indirect
jumps, jump tables) are COUNTED AND PRINTED AS UNKNOWN so the retraction cannot silently
overclaim. Parsing is TAB-SPLIT on objdump's own field layout (the byte field is the second tab
column) — an earlier revision matched lines with a byte regex whose field silently captured the
wrong span and the run reported 0 for everything that needs bytes: a parser that prints zeros
must be sanity-checked against a known line BEFORE its numbers gate anything.
"""
import sys

DUMP = "scratch/m574/text.txt"
FN = 0x41A8F0
TAG = 0x6899EC


def main() -> int:
    e8 = []          # e8 rel32 calls decoding to FN
    e8_all = 0
    jmp_to = []      # eb/e9 rel jmps decoding to FN
    jmp_all = 0
    imm_bytes = []   # lines whose ENCODING bytes contain FN little-endian
    push_tag = []    # push imm32 == the GOVOPTIONS tag
    ind_call = 0     # printed indirect calls (FF /2 family) - targets NOT resolvable here
    ind_jmp = 0      # printed indirect jumps
    FN_lo, FN_hi = FN, FN + 1403
    frame_calls = []      # e8 targets decoded from INSIDE the frame (context, not asserted)
    frame_push_imms = {}  # imm32 of every `push imm32` (68) inside the frame -> count
    fails = []
    with open(DUMP, encoding="utf-8", errors="replace") as f:
        for line in f:
            p = line.split("\t")
            if len(p) < 3 or not p[0].startswith("  "):
                continue
            head = p[0].strip()
            if not head.endswith(":"):
                continue
            try:
                addr = int(head[:-1], 16)
                raw = bytes.fromhex(p[1].strip())
            except ValueError:
                continue
            if not raw:
                continue
            ops = "\t".join(p[2:]).strip()
            words = ops.split(None, 1)
            mn = words[0].lower() if words else ""
            arg = words[1] if len(words) > 1 else ""
            if raw[0] == 0xE8 and len(raw) >= 5:
                e8_all += 1
                if (addr + 5 + int.from_bytes(raw[1:5], "little")) & 0xFFFFFFFF == FN:
                    e8.append(addr)
            if mn.startswith("jmp"):
                jmp_all += 1
                if raw[0] == 0xE9 and len(raw) >= 5:
                    if (addr + 5 + int.from_bytes(raw[1:5], "little")) & 0xFFFFFFFF == FN:
                        jmp_to.append(addr)
                elif raw[0] == 0xEB and len(raw) >= 2:
                    off = int.from_bytes(raw[1:2], "little", signed=True)
                    if (addr + 2 + off) & 0xFFFFFFFF == FN:
                        jmp_to.append(addr)
                if raw[0] not in (0xE9, 0xEB):
                    ind_jmp += 1
            if FN.to_bytes(4, "little") in raw:
                imm_bytes.append(addr)
            if mn == "push" and TAG.to_bytes(4, "little") in raw:
                push_tag.append(addr)
            if FN_lo <= addr < FN_hi:
                if raw[0] == 0xE8 and len(raw) >= 5:
                    frame_calls.append((addr, (addr + 5 + int.from_bytes(raw[1:5], "little")) & 0xFFFFFFFF))
                if raw[0] == 0x68 and len(raw) >= 5:
                    imm = int.from_bytes(raw[1:5], "little")
                    if imm >= 0x400000:  # a .text/.rdata absolute (a string pointer would be one)
                        frame_push_imms[imm] = frame_push_imms.get(imm, 0) + 1
            if mn == "call" and not arg.startswith("0x"):
                ind_call += 1

    print("== M329 s308 retraction facts, re-derived from %s ==" % DUMP)
    print("sanity 0x41e3bd e8-decodes-to-frame=%s (the parser must find a known site)"
          % (0x41E3BD in e8))
    print("e8 rel32 call insns decoded=%d; targeting 0x%x: %d %s"
          % (e8_all, FN, len(e8), [hex(a) for a in e8]))
    print("jmp insns=%d; jmp-to-frame (eb/e9 decoded)=%d %s"
          % (jmp_all, len(jmp_to), [hex(a) for a in jmp_to]))
    print("lines whose encoding bytes carry 0x%x little-endian=%d %s"
          % (FN, len(imm_bytes), [hex(a) for a in imm_bytes]))
    print("push 0x%x (GOVOPTIONS tag) sites=%d %s"
          % (TAG, len(push_tag), [hex(a) for a in push_tag]))
    print("UNKNOWN (out of scope): indirect calls=%d indirect jumps=%d; jump tables unscanned"
          % (ind_call, ind_jmp))
    print("in-frame `push imm32>=0x400000` distinct immediates=%d %s"
          % (len(frame_push_imms), {hex(k): v for k, v in sorted(frame_push_imms.items())}))
    print("in-frame e8 callees=%d %s"
          % (len(frame_calls), sorted({hex(t) for _, t in frame_calls})))

    want = [0x41E3BD, 0x49B306, 0x4A9E0E, 0x5120D0]
    for name, got, exp in (("sanity-known-site", [0x41E3BD] if 0x41E3BD in e8 else [], [0x41E3BD]),
                           ("e8-sites", sorted(e8), want),
                           ("jmp-to-frame", jmp_to, []),
                           # the 4 sites encode their target as rel32, so ZERO lines may carry the
                           # absolute little-endian FN anywhere in .text - a stray would be an
                           # unaccounted absolute reference to the frame
                           ("FN-absolute-encodings", imm_bytes, []),
                           ("push-6899ec", push_tag, [0x41ABA5]),
                           # the naming row: GOVOPTIONS is the frame's ONLY string-literal push
                           ("frame-string-pushes", sorted(frame_push_imms), [TAG])):
        ok = got == exp
        print("ASSERT %-16s got=%s expected=%s -> %s" % (name, got, exp, "OK" if ok else "FAIL"))
        if not ok:
            fails.append(name)
    if fails:
        print("== M329 s308 verify: FAIL (%s) ==" % ",".join(fails))
        return 1
    print("== M329 s308 verify: PASS (4 e8-sites, 0 direct jmps, 0 absolute FN-encodings, "
          "1 tag push; %d indirect calls / %d indirect jumps printed as UNKNOWN) =="
          % (ind_call, ind_jmp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
