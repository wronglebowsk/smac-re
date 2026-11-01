#!/usr/bin/env python3
"""M205-M208: the dialog RESULT field, the child-dialog slot, the diplomacy switch, the message buffer.

  M205  who writes the field the dialog pump RETURNS: [this+0x290] = byte 0xa40
  M206  what [this+0x285] = byte 0xa14 holds: the child pointer the +0xdc dispatch switches on
  M207  FUN_00546800 (34550 B): three jump tables, a dialog built on its own frame, 0 pump calls
  M208  ds:0x997528 is a global staging buffer: 103 address-passes, 1 byte-clear, 0 absolute reads

    python3 scripts/m205_m208_fields.py            # the acceptance run (14 gates)
    python3 scripts/m205_m208_fields.py --probe    # diagnostics only

Static only: scratch/m574/text.txt (whole-image disassembly) + programs/terran.exe bytes
(file offset = VA - 0x400000). No box time. Every number the prose quotes is COMPUTED here.
"""
import bisect
import collections
import importlib.util
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)
INS, fnof, IDX = FC.INS, FC.fnof, FC.IDX
INDEX = {n: (a, z) for a, n, z in IDX}
NORM = [(pc, " ".join(s.lower().split())) for pc, s in INS]
PCS = [pc for pc, _ in NORM]
assert PCS == sorted(PCS), "the listing is not address-ordered"
NORMD = dict(NORM)
POS = {pc: i for i, pc in enumerate(PCS)}
IMG = open(os.path.join(ROOT, "programs/terran.exe"), "rb").read()
PROBE = "--probe" in sys.argv
R = {}


def bytes_at(va, n):
    off = va - 0x400000
    return IMG[off:off + n] if 0 <= off < len(IMG) else b""


def dw(va):
    b = bytes_at(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else 0


def window(lo, hi):
    return NORM[bisect.bisect_left(PCS, lo):bisect.bisect_left(PCS, hi)]


def ops(text):
    m = re.match(r"^([a-z0-9]+)\s+(.*)$", text)
    if not m:
        return text.strip(), "", ""
    p = m.group(2).split(",", 1)
    return m.group(1), p[0].strip(), (p[1].strip() if len(p) > 1 else "")


def callsites(tgt):
    t = "0x%x" % tgt
    return [(pc, fnof(pc)) for pc, s in NORM if ops(s)[0] == "call" and ops(s)[1] == t]


def at(pc):
    return NORMD.get(pc, "")


def ok(mid, cond, text):
    R[mid] = bool(cond)
    print(mid + "  " + ("PASS" if cond else "FAIL") + " - " + text)


def show(mid, text):
    print(mid + " :: " + text)


STORE_MN = ("mov", "or", "and", "xor", "add", "sub", "shl", "shr", "movzx", "movsx", "inc", "dec", "neg")


def stores_with(disp):
    """Every instruction whose DESTINATION memory operand carries this displacement."""
    out = []
    for pc, s in NORM:
        o, a, b = ops(s)
        if o in STORE_MN and disp in a and ("ptr " in a or a.startswith("[")):
            out.append((pc, s))
    return out


# ================================================================ shared objects
PUMP, CTOR = "FUN_005f1394", "FUN_00405ef0"
PA, PZ = INDEX[PUMP]
VT = 0x67164C
CALLS = callsites(INDEX[PUMP][0])
CALLFN = sorted({f for _, f in CALLS})
CTORCALL = sorted({f for _, f in callsites(INDEX[CTOR][0])})
VTMEM = {}
for _i in range(276):
    _t = dw(VT + 4 * _i)
    if _t >= 0x401000 and fnof(_t) != "?":
        VTMEM.setdefault(fnof(_t), []).append(4 * _i)
THIS = "[ebp-0x394]"          # the pump's spilled `this` (written once, at 0x5f13b2)
LOOP = "[ebp-0x30]"           # the pump's copy of the +0xdc return value

# ================================================================ M205  the result field [this+0x290]
this_stores = [(pc, s) for pc, s in window(PA, PA + PZ) if ops(s)[0] in STORE_MN and THIS in ops(s)[1]]
loop_stores = [(pc, s) for pc, s in window(PA, PA + PZ) if ops(s)[0] in STORE_MN and LOOP in ops(s)[1]]
show("M205.return", "the pump's exit block: %s -> %s ; `%s` at 0x5f3f3f loads `this` from %s (its only "
     "store in the body is 0x5f13b2 `%s`), then 0x5f3f45 `%s`. The other two legs are gated by `%s` at "
     "0x5f3f26: 0x5f3f33 `%s` and 0x5f3f38 `%s` (the dword at 0x698d0c is 0x%08x). %s is written %d time(s) "
     "in the body: %s" % (at(0x5F3F1A), at(0x5F3F1E), at(0x5F3F3F), THIS, at(0x5F13B2), at(0x5F3F45),
                          at(0x5F3F26), at(0x5F3F33), at(0x5F3F38), dw(0x698D0C), LOOP, len(loop_stores),
                          [(hex(p), s) for p, s in loop_stores]))
ok("M205a", at(0x5F3F45) == "mov eax,dword ptr [eax+0xa40]" and at(0x5F3F3F) == "mov eax,dword ptr " + THIS and
   len(this_stores) == 1 and this_stores[0] == (0x5F13B2, "mov dword ptr " + THIS + ",ecx") and
   at(0x5F3F1A) == "cmp dword ptr " + LOOP + ",0x0" and at(0x5F3F1E) == "je 0x5f3f3f" and
   len(loop_stores) == 3 and sorted(p for p, _ in loop_stores) == [0x5F13D8, 0x5F3DC4, 0x5F3DFC] and
   at(0x5F13D8) == "mov dword ptr " + LOOP + ",0x0" and dw(0x698D0C) == 0xFFFFFFFF,
   "THE PUMP RETURNS THE FIELD, NOT A BUTTON CODE: its only read of the result is 0x5f3f45 "
   "`mov eax,[eax+0xa40]` on the register that holds `this` ([ebp-0x394], stored exactly ONCE in 11,207 "
   "bytes, by 0x5f13b2 `%s`), and that leg is taken only when %s == 0 - %s holds the value the +0xdc "
   "dispatch returned (3 stores in 11,207 bytes: the 0x5f13d8 init to 0 and 0x5f3dc4/0x5f3dfc, which sit "
   "right after the two `call [edx+0xdc]`). When it "
   "is nonzero the pump returns -1 either way: 0x5f3f33 `or eax,0xffffffff` when [this+0x30a8] bit 0x40 is "
   "set, else 0x5f3f38 `mov eax,ds:0x698d0c`, and that dword is 0x%08x" %
   (at(0x5F13B2), LOOP, LOOP, dw(0x698D0C)))

sa40 = stores_with("+0xa40]")
byfn = collections.Counter(fnof(pc) for pc, _ in sa40)
vtfns = {f: offs for f, offs in VTMEM.items() if f in byfn}
show("M205.census", "displacement +0xa40: %d store-shaped sites in %d functions image-wide; %d of those "
     "functions are members of the dialog vtable 0x67164c: %s; per-function store counts %s" %
     (len(sa40), len(byfn), len(vtfns), {f: ["+0x%x" % o for o in offs] for f, offs in vtfns.items()},
      dict(byfn.most_common(8))))
ok("M205b", len(sa40) == 56 and len(byfn) == 30 and set(vtfns) == {"FUN_005f5759", "FUN_005f58fa"} and
   sorted(VTMEM["FUN_005f5759"]) == [0xA8, 0x228] and sorted(VTMEM["FUN_005f58fa"]) == [0x64, 0x1E4] and
   byfn["FUN_005f5759"] == 4 and byfn["FUN_005f58fa"] == 3 and not callsites(0x5F5759) and
   not callsites(0x5F58FA),
   "THE WRITERS ARE THE CLASS'S OWN VMETHODS, REACHED ONLY THROUGH THE VTABLE: of the %d stores to "
   "+0xa40 in %d functions, exactly TWO functions are dialog-class vmethods - FUN_005f5759 at slots +0xa8 "
   "and +0x228 (%d stores) and FUN_005f58fa at slots +0x64 and +0x1e4 (%d stores) - and EACH has ZERO "
   "direct `call` sites image-wide, so nothing names them: they run only when some other code dispatches "
   "that slot. The pump itself stores the field 0 times (it only reads it at 0x5f3f45)" %
   (len(sa40), len(byfn), byfn["FUN_005f5759"], byfn["FUN_005f58fa"]))

f5759a, f5759z = INDEX["FUN_005f5759"]
f58faa, f58faz = INDEX["FUN_005f58fa"]
w5759 = [(pc, s) for pc, s in window(f5759a, f5759a + f5759z) if "+0xa40]" in s and ops(s)[0] in STORE_MN]
w58fa = [(pc, s) for pc, s in window(f58faa, f58faa + f58faz) if "+0xa40]" in s and ops(s)[0] in STORE_MN]
imm_written = sorted({ops(s)[2] for _, s in w5759 + w58fa if ops(s)[2].startswith("0x")})
srcs = [(hex(p), at(p - 6), at(p - 11), s) for p, s in w5759 + w58fa if not ops(s)[2].startswith("0x")]
show("M205.values", "FUN_005f5759 stores %s ; FUN_005f58fa stores %s ; the only immediates written are %s ; "
     "register-sourced writes and their producers: %s" %
     ([(hex(p), s) for p, s in w5759], [(hex(p), s) for p, s in w58fa], imm_written, srcs))
ok("M205c", imm_written == ["0x0", "0xffffffff"] and
   [(p, s) for p, s in w5759] == [(0x5F5765, "mov dword ptr [eax+0xa40],0x0"),
                                  (0x5F57B4, "mov dword ptr [edx+0xa40],eax"),
                                  (0x5F57DA, "mov dword ptr [edx+0xa40],eax"),
                                  (0x5F581C, "mov dword ptr [edx+0xa40],0xffffffff")] and
   at(0x5F57B1) == "mov eax,dword ptr [ebp-0x8]" and at(0x5F57A4) == "mov ecx,dword ptr [eax+edx*1+0xec]" and
   at(0x5F57D2) == "call 0x5fdcf7" and at(0x5F59A6) == "call 0x5fdcf7" and
   at(0x5F57E6) == "cmp dword ptr [ebp-0x10],0xfffffffe" and
   at(0x5F57EC) == "cmp dword ptr [ebp-0x10],0xffffffff" and
   at(0x5F584A) == "mov dword ptr [edx+0x3100],eax",
   "THE VALUE WRITTEN IS A LIST ITEM, NOT A CLICK: the only immediates the two vmethods put in the field "
   "are 0x0 (at entry, both) and 0xffffffff; the register-sourced stores take eax from `[node + [node+8] + "
   "0xec]` (0x5f57a4 -> 0x5f57b1 -> 0x5f57b4) or from `call 0x5fdcf7` (0x5f57d2/0x5f59a6) - the dialog's "
   "item list at this+0x21d0/0x2228 - and FUN_005f5759 ALSO keeps the incoming code in a SECOND slot, "
   "[this+0x3100] (0x5f584a), testing it against the sentinels 0xfffffffe and 0xffffffff")

fwd = []
for nm in ("FUN_005ce4a9", "FUN_005ce4dc"):
    a, z = INDEX[nm]
    bd = window(a, a + z)
    fwd.append((nm, z, [(hex(p), s) for p, s in bd if "+0xa40]" in s and ops(s)[0] in STORE_MN],
                [s for _, s in bd if "+0x43c]" in s or "+0x440]" in s], callsites(a)))
e350a, e350z = INDEX["FUN_005ee350"]
ini = [(hex(p), s) for p, s in window(e350a, e350a + e350z) if "+0xa40]" in s and ops(s)[0] in STORE_MN]
show("M205.fwd", "forwarders %s ; the ctor-side initializer FUN_005ee350 (called by the dialog ctor with "
     "ecx=this at 0x405f14: `%s`) stores %s" %
     ([(n, z, st, guard, [(hex(p), f) for p, f in cs]) for n, z, st, guard, cs in fwd], at(0x405F14), ini))
ok("M205d", fwd[0][1] == 51 and fwd[0][2] == [("0x5ce4d0", "mov dword ptr [eax+0xa40],ecx")] and
   fwd[0][3] == ["cmp dword ptr [eax+0x43c],0x0", "mov edx,dword ptr [ecx+0x43c]"] and
   fwd[1][2] == [("0x5ce503", "mov dword ptr [eax+0xa40],ecx")] and
   fwd[1][3] == ["cmp dword ptr [eax+0x440],0x0", "mov edx,dword ptr [ecx+0x440]"] and
   all(len(f[4]) == 2 and sorted({g for _, g in f[4]}) == ["FUN_005ff462", "FUN_00603fec"] for f in fwd) and
   ini == [("0x5ee7a5", "mov dword ptr [ecx+0xa40],0x0")] and at(0x405F14) == "call 0x5ee350",
   "TWO 51-BYTE FORWARDERS AND THE BASE CTOR COMPLETE THE PICTURE: FUN_005ce4a9 writes `*(this[0x43c] + "
   "0xa40) = arg` and FUN_005ce4dc writes `*(this[0x440] + 0xa40) = arg` (each 51 bytes, `ret 0x4`, exactly "
   "%d call sites, both in FUN_005ff462 and FUN_00603fec) - a wrapper object pushes its result INTO the "
   "dialog it points at; and the field is initialised to 0 by the base ctor FUN_005ee350 at 0x5ee7a5, which "
   "the dialog ctor calls with ecx = this at 0x405f14" % len(fwd[0][4]))

# ================================================================ M206  the child slot [this+0x285]
body_pump = window(PA, PA + PZ)
r_a14, w_a14 = [], []
for _p, _s in body_pump:
    if "+0xa14]" not in _s:
        continue
    _o, _a, _b = ops(_s)
    (w_a14 if _o in STORE_MN and "+0xa14]" in _a else r_a14).append((hex(_p), _s))
show("M206.field", "[this+0x285] = byte +0xa14: the pump reads it %d times %s and writes it %d time(s) %s" %
     (len(r_a14), r_a14, len(w_a14), w_a14))
ok("M206a", len(w_a14) == 1 and w_a14 == [("0x5f1561", "mov dword ptr [edx+0xa14],0x0")] and
   len(r_a14) == 10 and at(0x5F3D7C) == "cmp dword ptr [edx+0xa14],0x0" and at(0x5F3D83) == "je 0x5f3dc9",
   "THE PUMP CLEARS THE CHILD SLOT ON ITS WAY OUT AND TESTS IT BEFORE EVERY INTERACTIVE DISPATCH: "
   "1 store in 11,207 bytes (0x5f1561, value 0) against %d reads, and the dispatch selector is 0x5f3d7c "
   "`cmp [edx+0xa14],0` / `je 0x5f3dc9`" % len(r_a14))

show("M206.dispatch", "the two +0xdc legs are argument-identical: child %s / self %s ; both push `%s`,`%s` "
     "and the normalised bit `[this+0x30a8] & 0x200000` (%s..%s), both store the return to %s" %
     (at(0x5F3DB6), at(0x5F3DEE), at(0x5F3D85), at(0x5F3D8A), at(0x5F3D97), at(0x5F3DA1), LOOP))
ok("M206b", at(0x5F3DBC) == "mov edx,dword ptr [eax]" and at(0x5F3DBE) == "call dword ptr [edx+0xdc]" and
   at(0x5F3DEE) == "mov edx,dword ptr [eax]" and at(0x5F3DF6) == "call dword ptr [edx+0xdc]" and
   at(0x5F3DC4) == "mov dword ptr " + LOOP + ",eax" and at(0x5F3DFC) == "mov dword ptr " + LOOP + ",eax" and
   at(0x5F3D91) == "mov edx,dword ptr [ecx+0x30a8]" and at(0x5F3D97) == "and edx,0x200000" and
   at(0x5F5883) == "call dword ptr [edx+0xe0]" and at(0x5F5893) == "call dword ptr [edx+0xe0]" and
   at(0x5F5866) == "cmp dword ptr [eax+0xa14],0x0" and dw(VT + 0xDC) == 0x5CE5BD and dw(VT + 0xE0) == 0x5CE6FF,
   "THE DISPATCH IS A DELEGATION, NOT A BRANCH ON STATE: with the child set the pump calls slot +0xdc of "
   "*[this+0x285] (0x5f3dbe), without it it calls slot +0xdc of *this (0x5f3df6) - the same 3 args "
   "(0, the pump's own arg2 callback, and the boolean of [this+0x30a8] bit 0x200000) either way, and the "
   "result goes to the same %s. FUN_005f5759 dispatches slot +0xe0 the same way (0x5f5883 through the "
   "child, 0x5f5890 through self), so the child is an object with THE SAME vtable SHAPE: +0xdc = "
   "FUN_005ce5bd, +0xe0 = FUN_005ce6ff" % LOOP)

lnk = collections.OrderedDict()
for nm in ("FUN_005ee350", "FUN_005eede6", "FUN_005f6b8c"):
    a, z = INDEX[nm]
    lnk[nm] = [(hex(p), s) for p, s in window(a, a + z)
               if re.search(r"\+0xa(14|18|1c|20|24|28|2c)\]", s) and ops(s)[0] in STORE_MN]
globs = ["0x997850", "0x997854", "0x698e78", "0x698e7c"]
show("M206.link", "the 7-dword link block 0xa14..0xa2c, stores per ctor-function %s ; FUN_005f6b8c seeds it "
     "from the globals %s and installs vtable 0x671d94 on the object it builds" %
     ({k: len(v) for k, v in lnk.items()}, globs))
ok("M206c", all(len(v) >= 5 for v in lnk.values()) and
   ("0x5f6bf7", "mov dword ptr [edx+0xa14],eax") in lnk["FUN_005f6b8c"] and
   at(0x5F6BF2) == "mov eax,ds:0x997850" and at(0x5F6BDC) == "mov dword ptr [eax],0x671d94" and
   at(0x5F6BE5) == "mov dword ptr [ecx+0x444],0x671d8c" and
   ("0x5eec81", "mov dword ptr [eax+0xa14],ecx") in lnk["FUN_005ee350"] and
   ("0x5ef7f8", "mov dword ptr [eax+0xa14],ecx") in lnk["FUN_005eede6"],
   "[this+0x285] IS ONE SLOT OF A 7-POINTER LINK BLOCK (0xa14,0xa18,0xa1c,0xa20,0xa24,0xa28,0xa2c) that "
   "three ctors splice in triples: FUN_005ee350 %d stores, FUN_005eede6 %d, FUN_005f6b8c %d. The dialog "
   "ctor's second subobject ctor seeds the slot from the GLOBAL ds:0x997850 (0x5f6bf2-0x5f6bf7) and installs "
   "vtable 0x671d94 on the object it is constructing (0x5f6bdc) plus 0x671d8c at +0x444 (0x5f6be5) - the "
   "child the pump dispatches to is a member of THAT class, not a second copy of the dialog" %
   (len(lnk["FUN_005ee350"]), len(lnk["FUN_005eede6"]), len(lnk["FUN_005f6b8c"])))

mla, mlz = INDEX["FUN_005ce5bd"]
ml = window(mla, mla + mlz)
mlshapes = [(hex(p), s) for p, s in ml if "0x99" in s or (ops(s)[0] == "call" and ops(s)[1].startswith("0x"))]
show("M206.modal", "FUN_005ce5bd (vtable +0xdc) globals + slot calls: %s" % mlshapes[:22])
ok("M206d", at(0x5CE5CD) == "cmp dword ptr ds:0x9939c8,0x4" and at(0x5CE5D4) == "jl 0x5ce5dd" and
   at(0x5CE5E5) == "mov dword ptr [eax*4+0x992db8],ecx" and
   at(0x5CE5F5) == "mov dword ptr [edx*4+0x992dc8],eax" and
   at(0x5CE60E) == "mov dword ptr ds:0x9939c4,edx" and at(0x5CE649) == "call dword ptr [edx+0x10]" and
   at(0x5CE6B3) == "call dword ptr [edx+0xe4]" and at(0x5CE6C3) == "call dword ptr [ebp+0xc]" and
   at(0x5CE6E0) == "call dword ptr [edx+0xe0]" and at(0x5CE6E6) == "mov dword ptr [ebp-0x4],0x1" and
   at(0x5CE6FC) == "ret 0xc" and len(callsites(0x5CE5BD)) == 1,
   "AND THE +0xdc TARGET IS A MODAL LOOP OVER A 4-DEEP DIALOG STACK: FUN_005ce5bd refuses to run when "
   "ds:0x9939c8 >= 4 (0x5ce5cd `cmp ds:0x9939c8,4` / `jl`), pushes itself to [depth*4+0x992db8] and its "
   "arg3 to [depth*4+0x992dc8], publishes itself as the current dialog in ds:0x9939c4, suspends the "
   "previous modal through slot +0x10, pumps events through slot +0xe4, calls the caller's callback "
   "(`call [ebp+0xc]`) and, when that callback returns 0, closes the current dialog through slot +0xe0 and "
   "returns 1 - which is exactly the value that makes the pump take its -1 leg. It has %d direct call site "
   "(FUN_004413b0 at 0x4413cf)" % len(callsites(0x5CE5BD)))

# ================================================================ M207  FUN_00546800's switches
F546 = "FUN_00546800"
fa, fz = INDEX[F546]
fbody = window(fa, fa + fz)
TABLES = [(0x54A266, 0x54EEF8, 6), (0x54ACD1, 0x54EF14, 0xA), (0x54EAFC, 0x54EF34, 7)]
tinfo = []
for jpc, tab, hi in TABLES:
    ents = []
    i = 0
    while 0x540000 <= dw(tab + 4 * i) < 0x550000:
        ents.append(dw(tab + 4 * i))
        i += 1
    tinfo.append((jpc, tab, hi, ents))
def cstr(va, n=220):
    b = bytes_at(va, n).split(b"\x00")[0]
    return b.decode("latin1") if b and all(32 <= c < 127 for c in b) else None


pool = (0x690160, 0x69107C)
keypush = [(pc, int(ops(s)[1], 16)) for pc, s in fbody
           if ops(s)[0] == "push" and re.fullmatch(r"0x6[0-9a-f]{5}", ops(s)[1])]
inpool = [(pc, v) for pc, v in keypush if pool[0] <= v <= pool[1]]
words = [(pc, v) for pc, v in inpool if cstr(v) is not None and " " not in cstr(v)]
lines = [(pc, v) for pc, v in inpool if cstr(v) is not None and " " in cstr(v)]
ntext = len({cstr(v) for _, v in words})
show("M207.keys", "%d single-word key sites -> %d distinct ADDRESSES -> %d distinct STRINGS (the same text "
     "is stored at more than one pool address); %d sites name a multi-word message line" %
     (len(words), len({v for _, v in words}), ntext, len(lines)))
show("M207.tables", "%s+%d: jump tables %s ; pushes of .rdata immediates %d, of which %d name a string in "
     "the pool 0x690160..0x69107c; of those, single-word KEYS %d sites / %d distinct and multi-word message "
     "lines %d sites" %
     (hex(fa), fz, [(hex(j), hex(t), "cmp %s" % hex(h), "%d entries" % len(e)) for j, t, h, e in tinfo],
      len(keypush), len(inpool), len(words), len({v for _, v in words}), len(lines)))
ok("M207a", [len(e) for _, _, _, e in tinfo] == [12, 5, 8] and
   all(all(fa <= t < fa + fz for t in e) for _, _, _, e in tinfo) and
   at(0x54A25B) == "cmp eax,0x6" and at(0x54A25E) == "ja 0x54a3cf" and
   at(0x54A266) == "jmp dword ptr [edx*4+0x54eef8]" and
   at(0x54ACC0) == "cmp ebx,0xa" and at(0x54ACCB) == "mov cl,byte ptr [ebx+0x54ef28]" and
   at(0x54EAF3) == "cmp eax,0x7" and at(0x54EAF6) == "ja 0x54ec82" and at(0x54EAEB) == "call 0x542ea0" and
   at(0x54EAD2) == "mov eax,ds:0x920434" and at(0x54EAE0) == "test ah,0x8",
   "THREE HAND-ROLLED SWITCHES, ALL TARGETS INSIDE THE ONE FUNCTION: %d/%d/%d-entry tables at %s indexed by "
   "arg2 (guard `cmp eax,0x6; ja`), by a BYTE PERMUTATION read from 0x54ef28 (guard `cmp ebx,0xa`) and by "
   "the value FUN_00542ea0 returns (guard `cmp eax,0x7; ja`), the last reached only when ds:0x920434 != 0 "
   "and ds:0x985ae8 bit 0x800 is clear" %
   tuple([len(e) for _, _, _, e in tinfo] + [[hex(t) for _, t, _, _ in tinfo]]))

bnd = sorted({t for _, _, _, e in tinfo for t in e})
reg = collections.Counter()
for pc, v in words:
    reg[bisect.bisect_right(bnd, pc) - 1] += 1
t3 = tinfo[2][3]
per3 = [(k, hex(t3[k]), reg[bisect.bisect_right(bnd, t3[k]) - 1]) for k in range(len(t3))]
callc = collections.Counter(fnof(int(ops(s)[1], 16)) for pc, s in fbody
                            if ops(s)[0] == "call" and ops(s)[1].startswith("0x"))
show("M207.regions", "sorted switch targets %s..%s (%d distinct); in-pool key pushes per region %s ; the "
     "8-entry table's target -> region key-count %s" % (hex(bnd[0]), hex(bnd[-1]), len(bnd),
     sorted(reg.items(), key=lambda kv: -kv[1])[:10], per3))
ok("M207b", len(words) == 111 and len({v for _, v in words}) == 109 and ntext == 97 and len(keypush) == 162 and
   at(0x546842) == "call 0x405ef0" and at(0x546827) == "lea ecx,[ebp-0x5534]" and
   not any(ops(s)[1] == "0x5f1394" for pc, s in fbody if ops(s)[0] == "call") and
   at(0x54687B) == "test dword ptr [eax+0x94d448],0x8000000" and
   [at(q) for q in (0x546854, 0x546857, 0x546868, 0x54686B, 0x54686E, 0x546873, 0x546875)] ==
   ["shl eax,0x6", "add eax,esi", "lea eax,[esi+eax*2]", "shl eax,0x4", "sub eax,esi", "add eax,edi",
    "shl eax,0x2"],
   "M204's NUMBER REPRODUCES ON A NEW INSTRUMENT and the function is a per-(faction,record) RESPONDER, not "
   "a dialog runner: %d of its %d .rdata pushes name a single-word key in the diplomacy pool, at %d "
   "distinct addresses but only %d distinct STRINGS (M204 said 111 sites / 97 keys: the sites and the text "
   "count both reproduce - the pool stores the same word at more than one address); it builds a DIALOG "
   "OBJECT on its own 0x5534-byte frame (`lea ecx,[ebp-0x5534]` -> `call 0x405ef0`) and calls the pump 0 "
   "times; its two args are the canonical faction-block fold (shl 6 / add / lea [s+e*2] / shl 4 / sub / "
   "add edi / shl 2) feeding `test [eax+0x94d448],0x8000000`" %
   (len(words), len(keypush), len({v for _, v in words}), ntext))

sinkc = {k: callc.get(k, 0) for k in ("FUN_00626a17", "FUN_0064b9e0", "FUN_00405220", "FUN_00626634")}
show("M207.sinks", "%s callee counts: %s ; total call sites in the body %d ; the 5 callers: %s" %
     (F546, sinkc, sum(callc.values()), sorted({f for _, f in callsites(fa)})))
ok("M207c", sinkc["FUN_00626a17"] == 75 and sinkc["FUN_0064b9e0"] == 18 and len(callsites(fa)) == 5 and
   {f for _, f in callsites(fa)} == {"FUN_00519a20", "FUN_0054f1d0", "FUN_005525d0", "FUN_005551e0"},
   "THE KEYS LEAVE THROUGH THE WRITER THUNK: inside %s the address-sink FUN_00626a17 is called %d times and "
   "the strlen FUN_0064b9e0 %d times; the function has exactly 5 call sites (%s) - one of them the gap-stub "
   "callee FUN_00519a20 that 17 dialog sites hand to the pump as their callback" %
   (F546, sinkc["FUN_00626a17"], sinkc["FUN_0064b9e0"], ", ".join(sorted({f for _, f in callsites(fa)}))))

# ================================================================ M208  ds:0x997528
sites997 = [(pc, s) for pc, s in NORM if "0x997528" in s]
pushes = [(pc, s) for pc, s in sites997 if ops(s)[0] == "push" and ops(s)[1] == "0x997528"]
absbyte = [(hex(p), s) for p, s in sites997 if ops(s)[0] in STORE_MN and "ds:0x997528" in ops(s)[1]]
absread = [(hex(p), s) for p, s in sites997
           if "ds:0x997528" in (ops(s)[1] + ops(s)[2]) and ops(s)[0] not in STORE_MN]
slotst = [(hex(p), s) for p, s in sites997 if (p, s) not in pushes and (p, s) not in
          [(pp, ss) for pp, ss in sites997 if ops(ss)[0] in STORE_MN and "ds:0x997528" in ops(ss)[1]]
          and "ds:0x997528" not in (ops(s)[1] + ops(s)[2])]
sink_of = collections.Counter()
for pc in [p for p, _ in pushes]:
    nxt = [s for _, s in NORM[POS[pc] + 1:POS[pc] + 8] if ops(s)[0] == "call" and ops(s)[1].startswith("0x")]
    sink_of[fnof(int(ops(nxt[0])[1], 16)) if nxt else "?"] += 1
show("M208.census", "ds:0x997528: %d references = %d `push 0x997528` + %d absolute store(s) %s + %d absolute "
     "read(s) %s ; the rest %s ; sink of each push %s" %
     (len(sites997), len(pushes), len(absbyte), absbyte, len(absread), absread, slotst, sink_of.most_common(9)))
ok("M208a", len(sites997) == 105 and len(pushes) == 103 and
   absbyte == [("0x5f58de", "mov byte ptr ds:0x997528,0x0")] and
   len([p for p, s in sites997 if "ds:0x997528" in (ops(s)[1] + ops(s)[2]) and ops(s)[0] not in STORE_MN]) == 0 and
   slotst == [("0x5f06fe", "mov dword ptr [ebp+0x8],0x997528")] and sink_of["FUN_005f0583"] == 79,
   "THE CHANNEL IS A GLOBAL STAGING BUFFER THAT NO CODE EVER READS IN PLACE: %d references = %d pushes of "
   "its ADDRESS + %d absolute byte store (the clear 0x5f58de) + 1 store of the address into a stack arg slot; "
   "ZERO instructions load its bytes, so every consumer receives the pointer - and %d of the %d pushes go to "
   "one function, FUN_005f0583" % (len(sites997), len(pushes), len(absbyte), sink_of["FUN_005f0583"],
                                   len(pushes)))

ta, tz = INDEX["FUN_00626a17"]
tbody = window(ta, ta + tz)
tpush = [s for _, s in tbody if ops(s)[0] == "push"]
tcalls = [s for _, s in tbody if ops(s)[0] == "call"]
sl, sz = INDEX["FUN_0064b9e0"]
sbody = " ".join(s for _, s in window(sl, sl + sz))
show("M208.writer", "FUN_00626a17 is %d bytes; pushes %s; calls %s ; FUN_0064b9e0 (%d bytes) carries %s" %
     (tz, tpush, tcalls, sz, [c for c in ("0x7efefeff", "0x81010100") if c in sbody]))
ok("M208b", tz == 38 and tcalls == ["call 0x626b19"] and "push 0x997528" in tpush and
   tpush.count("push 0xffffffff") == 1 and tpush.count("push 0x0") == 1 and
   at(0x626A38) == "add esp,0x1c" and "0x7efefeff" in sbody and "0x81010100" in sbody and
   at(0x64B9E0) == "mov ecx,dword ptr [esp+0x4]" and not any("0x997528" in s for _, s in window(sl, sl + sz)),
   "M204's 'SINKS' ARE ONE WRITER THUNK AND ONE STRLEN: FUN_00626a17 is a %d-byte thunk that pushes its 5 "
   "args plus 0x0, 0xffffffff and 0x997528 and makes THE ONLY call in its body to the writer FUN_00626b19 "
   "(7 args, `add esp,0x1c`) - so the 149-site 'sink' is the append path into the global buffer; and "
   "FUN_0064b9e0 is the SWAR strlen (0x7efefeff / 0x81010100, reads [esp+0x4], never touches 0x997528), so "
   "M204's 76-site 'sink' is a MEASUREMENT of the key text, not an emit" % tz)

dr, dz = INDEX["FUN_005f0583"]
dbody = window(dr, dr + dz)
dflags = [(hex(p), s) for p, s in dbody if re.search(r"\+0x2350\],0x", s)]
show("M208.drain", "FUN_005f0583 (%d bytes, %d call sites): null-default %s -> %s ; tag engine %s ; mode "
     "stores %s ; attach %s" % (dz, len(callsites(dr)), at(0x5F06F8), at(0x5F06FE), at(0x5F0779), dflags,
                                at(0x5F05BF)))
ok("M208c", at(0x5F06F8) == "cmp dword ptr [ebp+0x8],0x0" and at(0x5F06FE) == "mov dword ptr [ebp+0x8],0x997528"
   and at(0x5F0779) == "call 0x625b20" and len(dflags) == 7 and
   sorted(ops(s)[2] for _, s in dflags) == ["0x1", "0x1", "0x10", "0x2", "0x2", "0x4", "0x4"] and
   at(0x5F05B0) == "and eax,0x80" and at(0x5F05BF) == "call 0x5eede6",
   "THE DRAIN IS THE DIALOG'S ADD-LINE METHOD, AND IT DEFAULTS TO THIS BUFFER: FUN_005f0583 (%d bytes) tests "
   "its text argument for null at 0x5f06f8 and substitutes 0x997528 at 0x5f06fe, then runs it through the "
   "$-tag engine FUN_00625b20 at 0x5f0779; the dialog mode field [this+0x2350] is written %d times in this "
   "one function with the immediates %s - the entry ladder maps arg5 bits 1/2/4 (else 0x10) at "
   "0x5f05d4/0x5f05f0/0x5f060c/0x5f061e - and bit 0x80 gates the attach call to FUN_005eede6 at 0x5f05bf, "
   "the same routine that splices the +0xa14 link block M206 found" %
   (dz, len(dflags), sorted(ops(s)[2] for _, s in dflags)))

# ================================================================ summary
print()
NEED = ["M205a", "M205b", "M205c", "M205d", "M206a", "M206b", "M206c", "M206d",
        "M207a", "M207b", "M207c", "M208a", "M208b", "M208c"]
if PROBE:
    print("PROBE MODE - verdicts below are not acceptance")
bad = [k for k in NEED if not R.get(k)]
ms = ["M205", "M206", "M207", "M208"]
print("SUMMARY %s  (%d/%d gates)%s" %
      (" ".join("%s=%s" % (m, "PASS" if not [k for k in bad if k.startswith(m)] else "FAIL") for m in ms),
       len(NEED) - len(bad), len(NEED), "" if not bad else "  FAILED: " + ", ".join(bad)))
if bad and not PROBE:
    sys.exit(1)
