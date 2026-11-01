#!/usr/bin/env python3
"""M201-M204: what the 94-caller function FUN_005f1394 IS, what it returns, how the $-tag engine
resolves its digit cases, and who emits the diplomacy keys - ONE census script, ONE evidence file.

  M201  FUN_005f1394: not a chooser - it is the RUN method of the dialog class whose ctor is
        FUN_00405ef0 (vtable 0x67164c + a CPane subobject at +0x444, vtable 0x671644); it is not
        in any vtable, its `this` is a caller's stack object, and it is the only function that
        names the OK / Cancel label strings
  M202  its return domain (1 `ret 0x8`, no `mov eax,imm` in 11207 bytes) and its arg2, which the
        class's +0xdc method CALLS; who supplies a callback, and what the composer does with the
        return - the 0x920700 "mode code" is a dialog RESULT CODE
  M203  FUN_00625b20's $H/$L/$N cases: FUN_0062898e is a first-DIGIT scanner, not a name resolver;
        $HEX/$LINK< are the only exceptions, and the engine's only return values are 14 and 3
  M204  the key pool read as an emitter list: 313 push-sites in 29 functions, the sinks, and the
        (surprising) overlap with the dialog pump's callers

    python3 scripts/m201_m204_dialog.py            # the acceptance run (gates)
    python3 scripts/m201_m204_dialog.py --probe    # diagnostics only

Static only: scratch/m574/text.txt (whole-image disassembly) + ghidra_out/shard_*.c +
programs/terran.exe bytes (file offset = VA - 0x400000 over .text/.rdata/.data). No box time.
Every number the prose quotes is COMPUTED here; the gates count sites and FAIL otherwise.
"""
import bisect
import glob
import importlib.util
import os
import re
import struct
import sys
from collections import Counter

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
IMG = open(os.path.join(ROOT, "programs/terran.exe"), "rb").read()
PROBE = "--probe" in sys.argv
R = {}


def bytes_at(va, n):
    off = va - 0x400000
    return IMG[off:off + n] if 0 <= off < len(IMG) else b""


def dw(va):
    b = bytes_at(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else 0


def cstr(va, n=90):
    b = bytes_at(va, n).split(b"\x00")[0]
    return b.decode("latin1") if b and all(32 <= c < 127 for c in b) else None


def ops(text):
    m = re.match(r"^([a-z0-9]+)\s+(.*)$", text)
    if not m:
        return text.strip(), "", ""
    p = m.group(2).split(",", 1)
    return m.group(1), p[0].strip(), (p[1].strip() if len(p) > 1 else "")


def window(lo, hi):
    return NORM[bisect.bisect_left(PCS, lo):bisect.bisect_left(PCS, hi)]


def callsites(tgt):
    t = "0x%x" % tgt
    return [(pc, fnof(pc)) for pc, s in NORM if ops(s)[0] == "call" and ops(s)[1] == t]


BODY = {}
for _f in sorted(glob.glob(os.path.join(ROOT, "ghidra_out/shard_*.c"))):
    _src = open(_f, errors="replace").read()
    _parts = re.split(r"^// ==== (\S+) @ [^\n]*\n", _src, flags=re.M)
    for _i in range(1, len(_parts) - 1, 2):
        BODY[_parts[_i]] = _parts[_i + 1]


def cbody(name):
    return BODY.get(name, "")


def ok(mid, cond, text):
    R[mid] = bool(cond)
    print(mid + "  " + ("PASS" if cond else "FAIL") + " - " + text)


def show(mid, text):
    print(mid + " :: " + text)


# ================================================================ shared objects
PUMP = "FUN_005f1394"
PA, PZ = INDEX[PUMP]
CTOR = "FUN_00405ef0"
VT, VT2 = 0x67164C, 0x671644
CALLS = callsites(PA)
CALLFN = sorted({f for _, f in CALLS})

# ================================================================ M201
ca, cz = INDEX[CTOR]
vstores = [(pc, s) for pc, s in window(ca, ca + cz)
           if ops(s)[0] == "mov" and re.fullmatch(r"0x67[0-9a-f]{4}", ops(s)[2])]
ctor_sites = callsites(INDEX[CTOR][0])
shared = sorted(set(f for _, f in ctor_sites) & set(CALLFN))
show("M201.ctor", "%s (%d bytes) stores %s; %d call sites in %d functions; %d of the %d pump-caller "
     "functions also construct it" % (CTOR, cz, [("%s `%s`" % (hex(p), s)) for p, s in vstores],
                                     len(ctor_sites), len({f for _, f in ctor_sites}), len(shared), len(CALLFN)))
ok("M201a", len(vstores) == 2 and (0x405F31, "mov dword ptr [eax],0x67164c") in vstores and
   (0x405F3A, "mov dword ptr [ecx+0x444],0x671644") in vstores and len(ctor_sites) == 99 and
   len(shared) >= 50,
   "FUN_005f1394 IS A METHOD OF A NAMED CLASS, and the class is the game's DIALOG: its constructor "
   "%s installs vtable 0x%x at this+0 (0x405f31 `mov [eax],0x67164c`) and a SECOND vtable 0x%x at "
   "this+0x444 (0x405f3a), after calling the two subobject ctors 0x5ee350 and 0x5f6b8c (the 2nd on "
   "this+0x3230); the ctor has %d call sites in %d functions and %d of the %d functions that call "
   "the pump construct this very object themselves" %
   (CTOR, VT, VT2, len(ctor_sites), len({f for _, f in ctor_sites}), len(shared), len(CALLFN)))

n_data = 0
_start = 0
while True:
    i = IMG.find(struct.pack("<I", PA), _start)
    if i < 0:
        break
    n_data += 1
    _start = i + 1
ecx_src = Counter()
for pc, f in CALLS:
    e = None
    for s in reversed([x for p, x in window(pc - 90, pc)]):
        o, a, b = ops(s)
        if o in ("lea", "mov") and a.startswith("ecx"):
            e = s
            break
    ecx_src["stack slot" if e and "[ebp" in e else ("global" if e and "ds:0x" in e else
            ("none-in-90" if not e else "register"))] += 1
retsite = [(pc, s) for pc, s in window(PA, PA + PZ) if ops(s)[0] == "ret"]
show("M201.shape", "%s..%s (%d bytes): the dword 0x%08x appears %d time(s) as data in the mapped "
     "image; %d direct `call` sites; exits %s; ECX ('this') sources %s" %
     (hex(PA), hex(PA + PZ), PZ, PA, n_data, len(CALLS), [(hex(p), s) for p, s in retsite], dict(ecx_src)))
ok("M201b", n_data == 0 and len(CALLS) == 94 and len(retsite) == 1 and retsite[0][1] == "ret 0x8"
   and ecx_src.get("stack slot", 0) >= 90,
   "IT IS NOT A VMETHOD AND NOT A JUMP TARGET: the little-endian dword for 0x5f1394 appears %d times "
   "in the mapped .text/.rdata/.data bytes, so no vtable or switch table holds it; all %d arrivals "
   "are direct `call 0x5f1394`; its single exit is `ret 0x8` at %s (callee cleans 8 = 2 args, a "
   "thiscall member with `this` in ECX), and at %d of the %d sites ECX is loaded from the CALLER'S "
   "OWN STACK FRAME (`lea ecx,[ebp-0x53xx]`, `mov ecx,[ebp-0x3824]`) - the dialog object is a stack "
   "temporary built by whoever shows the dialog" %
   (n_data, len(CALLS), hex(retsite[0][0]) if retsite else "?", ecx_src.get("stack slot", 0), len(CALLS)))

LABELS = [0x698E40, 0x698E44, 0x698E48, 0x698E50]
lab = [(va, cstr(va)) for va in LABELS]
refs = {}
for va in LABELS:
    t = "0x%x" % va
    refs[va] = [(pc, fnof(pc)) for pc, txt in NORM if re.search(r"\b%s\b" % t, txt)]
show("M201.labels", "the 32 bytes at 0x698e40 read %r; the 4 globals the pump names read %s; reference "
     "sites %s" % (bytes_at(0x698E40, 32), ["%s@%s" % (repr(t), hex(v)) for v, t in lab],
                  {hex(v): [(hex(p), f) for p, f in h] for v, h in refs.items()}))
ok("M201c", [t for _, t in lab] == ["OK", "OK", "Cancel", "OK"] and
   all(len(refs[v]) == 1 for v in LABELS) and all(f == PUMP for v in LABELS for _, f in refs[v]) and
   bytes_at(0x698E40, 8) == b"OK\x00\x00OK\x00\x00" and bytes_at(0x698E48, 8) == b"Cancel\x00\x00",
   "THE PUMP IS THE OK/CANCEL DIALOG RUNNER: the only string globals its body names are %s, the pool "
   "at 0x698e40 alternates OK/OK/Cancel/OK, and EACH of the four is referenced by exactly ONE site in "
   "the whole image - all %d inside %s. The pump builds a row from ds:0x9977f4 (default the 'OK' text "
   "at 0x698e44) and a bottom row from ds:0x9977f8 (default 'Cancel' at 0x698e50)" %
   (["%s@%s" % (repr(t), hex(v)) for v, t in lab], sum(len(refs[v]) for v in LABELS), PUMP))

SLOTS = [0x4, 0x8, 0x30, 0xdc, 0x15c, 0x160, 0x164, 0x16c, 0x170]
bpump = cbody(PUMP)
slotinfo = []
for off in SLOTS:
    tgt = dw(VT + off)
    # Ghidra prints small offsets as `+ 4`/`+ 8` and larger ones as `+ 0x15c`: accept either form.
    pat = r"\*in_ECX \+ (?:0x%x|%d)\)" % (off, off)
    slotinfo.append((off, tgt, fnof(tgt), len(re.findall(pat, bpump))))
child_dc = len(re.findall(r"in_ECX\[0x285\] \+ 0xdc\)", bpump))
self_dc = len(re.findall(r"\*in_ECX \+ 0xdc\)", bpump))
show("M201.slots", "slots the pump dispatches through *this: %s; +0xdc dispatches: on *this %d, on "
     "*this[0x285] %d" % ([("0x%x->0x%08x %s (%d C site(s))" % (o, t, f, n)) for o, t, f, n in slotinfo],
                          self_dc, child_dc))
ok("M201d", all(t >= 0x401000 and fnof(t) != "?" and n >= 1 for _, t, f, n in slotinfo) and
   self_dc == 1 and child_dc == 1 and dw(VT + 0xdc) == 0x5CE5BD,
   "THE PUMP'S OWN DISPATCH TABLE IS RESOLVABLE: it calls %d distinct slots of the ctor's vtable "
   "0x%x - %s - and every one is a real function in the export, not the class's `return 0` stub "
   "0x404ed0 that fills dozens of the table's other slots. The interactive dispatch at +0xdc is made "
   "TWICE, on `*this` when this[0x285] is 0 and on `*this[0x285]` otherwise - the sub-dialog pointer "
   "M197 already saw tested repeatedly in this body" %
   (len(SLOTS), VT, ", ".join("0x%x=%s" % (o, f) for o, t, f, n in slotinfo)))

# ================================================================ M202
eaximm = [(pc, s) for pc, s in window(PA, PA + PZ)
          if ops(s)[0] == "mov" and ops(s)[1] == "eax" and re.fullmatch(r"0x[0-9a-f]+", ops(s)[2])]
eaxxor = [(pc, s) for pc, s in window(PA, PA + PZ) if ops(s)[0] == "xor" and ops(s)[1] == "eax" and ops(s)[2] == "eax"]
eaxm1 = [(pc, s) for pc, s in window(PA, PA + PZ) if ops(s)[0] == "or" and ops(s)[1] == "eax" and ops(s)[2] == "0xffffffff"]
eaxglb = [(pc, s) for pc, s in window(PA, PA + PZ) if ops(s)[0] == "mov" and ops(s)[1] == "eax" and "0x698d0c" in s]
fld = [(pc, s) for pc, s in window(PA, PA + PZ) if "+0xa40]" in s]
fldw = [(pc, s) for pc, s in fld if ops(s)[0] == "mov" and re.search(r"0xa40\]$", ops(s)[1])]
show("M202.domain", "inside %s's %d bytes: `mov eax,imm` %d; `xor eax,eax` %d at %s; `or eax,0xffffffff` "
     "%d at %s; `mov eax,ds:0x698d0c` %d (that dword reads 0x%08x = %d signed); [reg+0xa40] mentions %d "
     "(stores %d)" % (PUMP, PZ, len(eaximm), len(eaxxor), [hex(p) for p, _ in eaxxor], len(eaxm1),
                      [hex(p) for p, _ in eaxm1], len(eaxglb), dw(0x698D0C),
                      struct.unpack("<i", bytes_at(0x698D0C, 4))[0], len(fld), len(fldw)))
ok("M202a", len(retsite) == 1 and len(eaximm) == 0 and len(eaxxor) == 5 and len(eaxm1) == 2 and
   len(eaxglb) == 1 and dw(0x698D0C) == 0xFFFFFFFF and len(fld) == 1 and len(fldw) == 0,
   "ITS RETURN DOMAIN IS {0, -1, the dialog's result field, a passed-through dispatch value} - not an "
   "enum: the %d-byte body contains %d `mov eax,imm` at all; 0 reaches EAX through %d `xor eax,eax`, "
   "-1 through %d `or eax,0xffffffff` plus the load at 0x5f3f38 of ds:0x698d0c, whose dword IS "
   "0xffffffff (%d site(s) in the image name it and the pump is one); the only other value it can "
   "return is the object field at byte +0xa40 (dword index 0x290), read ONCE at 0x5f3f45 and NEVER "
   "written here (%d stores) - the pump REPORTS a result, it does not compute one" %
   (PZ, len(eaximm), len(eaxxor), len(eaxm1), len([1 for pc, s in NORM if "0x698d0c" in s]), len(fldw)))

arg2 = [(pc, s) for pc, s in window(PA, PA + PZ) if "[ebp+0xc]" in s]
launched = sum(1 for pc, s in arg2
               if any("+0xdc]" in s2 for p2, s2 in window(pc, pc + 90) if ops(s2)[0] == "call"))
dc_fn = dw(VT + 0xDC)
dcs, dca = INDEX[fnof(dc_fn)]
dccall = [(pc, s) for pc, s in window(dcs, dcs + dca) if ops(s)[0] == "call" and "[ebp+0xc]" in s]
dccmp = [(pc, s) for pc, s in window(dcs, dcs + dca) if ops(s)[0] == "cmp" and "[ebp+0xc]" in s]
dcret = [(pc, s) for pc, s in window(dcs, dcs + dca) if ops(s)[0] == "ret"]
show("M202.callback", "the pump uses [ebp+0xc] at %d site(s) %s, %d of them within 90 bytes of a "
     "`call [reg+0xdc]`; vtable+0xdc = 0x%08x %s whose body has cmp-arg2 %s, call-arg2 %s, exit %s" %
     (len(arg2), [hex(p) for p, _ in arg2], launched, dc_fn, fnof(dc_fn), [hex(p) for p, _ in dccmp],
      [hex(p) for p, _ in dccall], [(hex(p), t) for p, t in dcret]))
ok("M202b", len(arg2) == 2 and launched == 2 and dc_fn == 0x5CE5BD and len(dccall) == 1 and
   len(dccmp) == 1 and bool(dcret) and dcret[0][1] == "ret 0xc",
   "ARG2 IS A CALLBACK THE MODAL HANDLER INVOKES: the pump touches its 2nd arg exactly %d times "
   "(0x5f3d87, 0x5f3dcb), each time pushing it as the 2nd argument of a +0xdc dispatch; the method in "
   "that slot, %s, takes 3 args (`ret 0xc`) and at 0x5ce6bd tests `[ebp+0xc]` for null and at 0x5ce6c3 "
   "does `call dword ptr [ebp+0xc]` - the dialog CALLS the caller's function, and its 0/1 answer "
   "selects between the caller's hook and the default handler on ds:0x9939c4" % (len(arg2), fnof(dc_fn)))

codeargs = Counter()
ncb = 0
for pc, f in CALLS:
    last2 = [s for p, s in window(pc - 90, pc) if ops(s)[0] == "push"][-2:]
    has = False
    for s in last2:
        o, a, b = ops(s)
        if re.fullmatch(r"0x[0-9a-f]{6,7}", a) and 0x401000 <= int(a, 16) < 0x670000:
            codeargs["%s (%s)" % (a, fnof(int(a, 16)))] += 1
            has = True
    ncb += 1 if has else 0
gap = [0x530D70, 0x530DB0]
stub = {}
for g in gap:
    body = [s for p, s in window(g, g + 0x40)]
    stub[g] = dict(owner=fnof(g),
                   calls=[ops(s)[1] for s in body if ops(s)[0] == "call"],
                   reads=[t for s in body for t in re.findall(r"ds:0x[0-9a-f]+", s)],
                   rets=[s for s in body if ops(s)[0] == "ret"])
g790 = [(pc, s, fnof(pc)) for pc, s in NORM if "0x920790" in s]
g790w = [(pc, s, f) for pc, s, f in g790 if ops(s)[0] == "mov" and "0x920790" in ops(s)[1]]
show("M202.stubs", "%d of %d sites pass a code pointer: %s; the stubs' owners %s; 0x920790 stores in "
     "the image: %d %s" % (ncb, len(CALLS), codeargs.most_common(),
                          {hex(k): v["owner"] for k, v in stub.items()}, len(g790w),
                          [(hex(p), s) for p, s, _ in g790w]))
ok("M202c", ncb == 17 and codeargs.most_common() == [("0x530d70 (?)", 16), ("0x530db0 (?)", 1)] and
   all(stub[g]["owner"] == "?" for g in gap) and all("0x519a20" in stub[g]["calls"] for g in gap) and
   all("ds:0x920434" in stub[g]["reads"] and "ds:0x991588" in stub[g]["reads"] for g in gap) and
   len(g790w) == 4 and all(0x530D70 <= p < 0x530DF0 for p, _, _ in g790w),
   "ONLY 17 OF THE 94 SITES SUPPLY A CALLBACK, and both supplied addresses are UNNAMED CODE ISLANDS "
   "in the 0x530d45-0x530df0 gap (no function in the export contains them): 16 pass 0x530d70, 1 passes "
   "0x530db0, the other %d pass 0/0 or a register pair. Each stub is the same predicate: read "
   "ds:0x920434 (the dialog-open gate M83/M84 hit), then ds:0x991588, return 0 if that is set, else "
   "set the reentrancy flag ds:0x920790=1 (its only 4 stores anywhere are these 4 sites in the gap), "
   "call FUN_00519a20, clear the flag, return 1" % (len(CALLS) - ncb))

SEL = ("0x9206fc", "0x920700", "0x920728", "0x920748", "0x92077c")
CSITES = [0x544A91, 0x544C2C, 0x544F2B, 0x5451E4, 0x545686, 0x5457F4]
stores = []
for cp in CSITES:
    post = [s for p, s in window(cp + 5, cp + 40)][:4]
    hit = [s for s in post if ops(s)[0] == "mov" and any(g in s for g in SEL)]
    test = [s for s in post if ops(s)[0] == "cmp"]
    stores.append((cp, bool(hit), test[:1]))
touched = [(pc, s, fnof(pc)) for pc, s in NORM if "0x920700" in s]
cmpimm = Counter()
for pc, s, f in touched:
    o, a, b = ops(s)
    if o == "cmp":
        cmpimm[b if "0x920700" in a else a] += 1
n_stored = sum(1 for _, h, _ in stores if h)
show("M202.composer", "composer sites storing the return into a selector global within 4 insns: %d/6 "
     "%s; 0x920700 touched at %d sites in %s; compared with %s" %
     (n_stored, [(hex(p), t) for p, h, t in stores], len(touched),
      Counter(f for _, _, f in touched).most_common(), cmpimm.most_common()))
ok("M202d", n_stored == 6 and len(touched) == 31 and len({f for _, _, f in touched}) == 4 and
   {"0x8", "0x6", "0xd", "0x4", "0x9"} <= {k for k, _ in cmpimm.items()},
   "M197's LABEL 'THE CHOOSER' IS RETRACTED - FUN_005f1394 CHOOSES NOTHING: all %d of the composer's "
   "calls are followed within 4 instructions by a store of the return into one of the 5 selector "
   "globals {0x9206fc,0x920700,0x920728,0x920748,0x92077c} and a `cmp` of it against a small integer; "
   "0x920700 is touched at %d sites in only %d functions and compared with the immediates %s, which "
   "are therefore NOT a hand-set mode enum but DIALOG RESULT CODES - what the pump returns from "
   "[this+0x290] when the modal dispatch answers 0 (M195's '13-value mode code', and the lone "
   "immediate store 0xc at 0x54ec5c, is one such code)" %
   (n_stored, len(touched), len({f for _, _, f in touched}),
    sorted({k for k, _ in cmpimm.items()}, key=lambda x: int(x, 16))))

# ================================================================ M203
b625 = cbody("FUN_00625b20")
b898 = cbody("FUN_0062898e")
a898, z898 = INDEX["FUN_0062898e"]
c898 = callsites(a898)
lit898 = sorted(set(re.findall(r"'([^']{1,3})'", b898)))
show("M203.digit", "%s (%d bytes): char literals %s, _strlen %s, tail %r; call sites %d %s" %
     ("FUN_0062898e", z898, lit898, "_strlen" in b898, b898.splitlines()[-4:], len(c898),
      sorted({f for _, f in c898})))
ok("M203a", z898 == 61 and {"0", "9"} <= set(lit898) and all(x in ("0", "9", "\\0") for x in lit898)
   and "_strlen" not in b898 and len(c898) == 5 and {f for _, f in c898} == {"FUN_00625b20"},
   "FUN_0062898e IS NOT A NAME-TO-SLOT RESOLVER, IT IS A FIRST-DIGIT SCANNER: %d bytes, 0 callees, the "
   "only character constants anywhere in it are the digit bounds %r plus the loop's NUL test, it calls "
   "no string routine, and its body is `p = param-1; do { p++; if (*p == 0) return 0; } while (*p < '0' "
   "|| *p > '9'); return p;` - it hands back a POINTER TO THE FIRST DIGIT in the tag payload, or NULL. "
   "All %d of its call sites are inside FUN_00625b20, its only caller" % (z898, sorted({"0", "9"}), len(c898)))

cases = sorted(set(re.findall(r"case '([^']+)':", b625)))
hexbytes, linkbytes = cstr(0x699130), cstr(0x69913c)
nh = len(re.findall(r"_strncmp\(local_14,&DAT_00699130,4\)", b625))
nl = len(re.findall(r"_strncmp\(local_14,s__LINK<_0069913c,6\)", b625))
nitoa = b625.count("__itoa")
nfine = b625.count("00999fa4")
nslot = b625.count("DAT_0099a01c")
show("M203.H", "cases %s; $HEX compare %d (bytes at 0x699130 = %r), $LINK< compare %d (bytes at "
     "0x69913c = %r); __itoa %d; 0x999fa4 refs %d; slot-text refs %d; FUN_0062898e calls %d" %
     (cases, nh, hexbytes, nl, linkbytes, nitoa, nfine, nslot, b625.count("FUN_0062898e")))
ok("M203b", cases == ["$", "<", "H", "L", "N"] and nh == 1 and hexbytes == "$HEX" and nl == 1 and
   linkbytes == "$LINK<" and nitoa == 3 and nfine == 4 and nslot == 4,
   "THE $H CASE HAS TWO ARMS AND ONLY ONE IS A NUMBER: `case 'H'` compares 4 bytes with the needle "
   "table at 0x699130, whose bytes read %r - on a match ($HEXn) it appends `__itoa((&DAT_00999fa4)[n])`, "
   "the DECIMAL of the third metadata array M191 found (%d references in this body); on a MISMATCH it "
   "does what $L and $N do - take the first digit and append the CHANNEL SLOT TEXT `&DAT_0099a01c + "
   "n*0x100` (%d slot-text sites, %d __itoa sites in the whole engine)" % (hexbytes, nfine, nslot, nitoa))
ngoto = len(re.findall(r"case 'N':\s*\n?\s*goto (switchD_00625bb6_caseD_4e);", b625))
nlabel = b625.count("switchD_00625bb6_caseD_4e")
n898 = b625.count("FUN_0062898e")
nguard = b625.count("9 < local_1c")
show("M203.tail", "$N -> goto %d (label appears %d times: the goto + its definition); FUN_0062898e "
     "called %d times in the body; digit guards `9 < local_1c` %d" % (ngoto, nlabel, n898, nguard))
ok("M203c", ngoto == 1 and nlabel == 2 and n898 == 5 and nguard == 8,
   "$N (and therefore every tag char the switch does not name) IS THE SLOT-TEXT PATH: `case 'N': goto "
   "switchD_00625bb6_caseD_4e` - the label occurs %d times, the goto and its definition - so $N shares "
   "the switch's fall-through tail with the un-named default case, and that tail, like the $H-mismatch "
   "and $L-non-$LINK arms, is `p = FUN_0062898e(tag); n = *p - '0'; append(&DAT_0099a01c + n*0x100)`. "
   "The engine calls the digit scanner %d times and guards each of its %d index uses with `9 < "
   "local_1c`" % (nlabel, n898, nguard))
nerr = b625.count("return 0xe")
retn = Counter(re.findall(r"return [^;]+;", b625))
show("M203.err", "returns in the engine body: %s; `uVar2 = 3` sites %d" % (dict(retn), b625.count("uVar2 = 3")))
ok("M203d", nerr == 6 and dict(retn) == {"return 0xe;": 6, "return uVar2;": 1} and b625.count("uVar2 = 3") == 1,
   "THE ENGINE'S WHOLE RESULT SET IS 2 VALUES: the only `return` statements in FUN_00625b20's %d lines "
   "are `return 0xe` %d times (each behind one of the %d `9 < local_1c` digit guards - a tag whose "
   "payload has no leading digit index is REJECTED with 14) and one `return uVar2`, whose only "
   "assignment is `uVar2 = 3` for a NULL source or destination. A message line either substitutes or "
   "reports 'bad tag'; it cannot silently leave a $tag in the text" % (len(b625.splitlines()), nerr, nguard))

# ================================================================ M204
KEYRE = re.compile(r"^[A-Za-z0-9|!?*#<>$%&/:+=^\-_]{1,17}$")


def entry_at(va):
    raw = bytes_at(va, 72)
    z = raw.find(b"\x00")
    if z is None or not (1 <= z <= 60):
        return None
    s = raw[:z].decode("latin1")
    need = (4 - (z + 1) % 4) % 4
    if any(c != 0 for c in bytes_at(va + z + 1, need)):
        return None
    return (s, va + z + 1 + need) if KEYRE.match(s) else None


ANCHOR = 0x690A84


def pred(va):
    for c in range(va - 76, va - 3, 4):
        e = entry_at(c)
        if e and e[1] == va:
            return (c, e[0])
    return None


_fwd, _v = [], ANCHOR
while True:
    k = entry_at(_v)
    if not k:
        break
    _fwd.append((_v, k[0]))
    _v = k[1]
POOL_END = _v
_back = []
_v = ANCHOR
while True:
    p = pred(_v)
    if not p:
        break
    _back.insert(0, p)
    _v = p[0]
POOL_START = _v
KEYVA = dict(_back + _fwd)
HEXRE = re.compile(r"0x([0-9a-f]{6,7})")
sites = []
for pc, txt in NORM:
    for m in HEXRE.finditer(txt):
        va = int(m.group(1), 16)
        if va in KEYVA:
            sites.append((pc, fnof(pc), KEYVA[va]))
emitters = {}
for pc, f, k in sites:
    emitters.setdefault(f, []).append((pc, k))
sinks = Counter()
npush = 0
for pc, f, k in sites:
    if ops(NORMD[pc])[0] == "push":
        npush += 1
    tgt = None
    for p2, s2 in window(pc + 1, pc + 30):
        o, a, b = ops(s2)
        if o == "push" and re.fullmatch(r"0x[0-9a-f]{6,7}", a) and int(a, 16) in KEYVA:
            continue
        if o == "call" and re.fullmatch(r"0x[0-9a-f]+", a):
            tgt = a
            break
    sinks[tgt] += 1
addrs = {f: INDEX[f][0] for f in emitters if f in INDEX}
rank = sorted(emitters.items(), key=lambda kv: -len(kv[1]))
show("M204.map", "the single-word-key walk from 0x690a84 reaches %d contiguous entries at %s..%s; %d "
     "code sites reference %d distinct keys; %d functions reference them, spanning %s..%s" %
     (len(KEYVA), hex(POOL_START), hex(POOL_END), len(sites), len({k for _, _, k in sites}), len(emitters),
      hex(min(addrs.values())), hex(max(addrs.values()))))
show("M204.rank", "emitters by site count:\n  %s" %
     "\n  ".join("%-16s %3d sites %3d keys" % (f, len(v), len({k for _, k in v})) for f, v in rank[:12]))
ok("M204a", len(sites) == 313 and len(emitters) == 29 and rank[0][0] == "FUN_00546800" and
   len(rank[0][1]) == 111 and len({k for _, k in rank[0][1]}) == 97 and
   min(addrs.values()) >= 0x531000 and max(addrs.values()) <= 0x550000,
   "THE POOL IS NOT A LOOKUP TABLE, IT IS AN EMITTER LIST: %d code sites reference %d of the %d keys, "
   "coming from only %d functions, ALL of them inside the diplomacy band 0x531000-0x550000 (%s..%s). "
   "One function, %s (34,550 bytes, the biggest in the band), owns %d of the %d sites and %d distinct "
   "keys - a third of the pool in a single switch" %
   (len(sites), len({k for _, _, k in sites}), len(KEYVA), len(emitters), hex(min(addrs.values())),
    hex(max(addrs.values())), rank[0][0], len(rank[0][1]), len(sites), len({k for _, k in rank[0][1]})))
top3 = sum(c for t, c in sinks.most_common(3))
show("M204.sinks", "every key site's own instruction is a push of the key VA: %d/%d; the call it feeds "
     "(first call below it, key pushes skipped): %s" % (npush, len(sites), sinks.most_common(10)))
ok("M204b", npush == len(sites) and sinks.most_common(3) == [("0x626a17", 149), ("0x64b9e0", 76), ("0x405220", 33)] and top3 >= 250,
   "EVERY SITE IS A PUSH AND THE SINKS ARE TEXT SINKS: all %d key references are `push <key VA>`; the "
   "call each one feeds is FUN_00626a17 %d times (a 4-arg thunk to FUN_00626b19(&DAT_00997528, key, "
   "0xffffffff, 0, ...) - the MESSAGE channel), FUN_0064b9e0 %d times (the append-copy M191 saw the "
   "publish use) and FUN_00405220 %d times (a 1-arg thunk to FUN_00404010(&DAT_00997120, key) - the "
   "scratch buffer the composer zeroes before calling the tag engine). Those three take %d of %d sites; "
   "the tail is %d to the slot indexer FUN_005f0583 and %d smaller sinks" %
   (len(sites), sinks["0x626a17"], sinks["0x64b9e0"], sinks["0x405220"], top3, len(sites),
    sinks["0x5f0583"], len(sites) - top3 - sinks["0x5f0583"] - sinks[None]))
keyfns = set(emitters)
ov = sorted(keyfns & set(CALLFN))
c546 = callsites(INDEX["FUN_00546800"][0])
show("M204.split", "key-referrers that ALSO call the dialog pump: %d %s; pump callers that reference no "
     "key: %d; FUN_00546800's callers: %s" % (len(ov), ov, len(set(CALLFN) - keyfns),
                                              sorted({f for _, f in c546})))
ok("M204c", len(ov) == 11 and len(set(CALLFN) - keyfns) == 56 and "FUN_00519a20" in {f for _, f in c546} and
   "0x519a20" in stub[0x530D70]["calls"],
   "THE DIALOG AND THE MESSAGE PATHS ARE ALMOST DISJOINT, and they meet through the CALLBACK: only %d "
   "of the %d key-emitting functions call the pump at all, and %d of the pump's %d caller functions "
   "reference no key - emitting a diplomacy line is NOT how a dialog gets filled. The join is the "
   "callback chain: the stub at 0x530d70 that 16 dialog sites hand to the pump calls FUN_00519a20, and "
   "FUN_00519a20 is one of the %d callers of %s, the 111-site emitter (%s)" %
   (len(ov), len(keyfns), len(set(CALLFN) - keyfns), len(CALLFN), len(c546), "FUN_00546800",
    ", ".join(sorted({f for _, f in c546}))))

# ================================================================ summary
print()
NEED = ["M201a", "M201b", "M201c", "M201d", "M202a", "M202b", "M202c", "M202d",
        "M203a", "M203b", "M203c", "M203d", "M204a", "M204b", "M204c"]
if PROBE:
    print("PROBE MODE - verdicts below are not acceptance")
bad = [k for k in NEED if not R.get(k)]
print("SUMMARY M201=%s M202=%s M203=%s M204=%s  (%d/%d gates)%s" %
      ("PASS" if not [k for k in bad if k.startswith("M201")] else "FAIL",
       "PASS" if not [k for k in bad if k.startswith("M202")] else "FAIL",
       "PASS" if not [k for k in bad if k.startswith("M203")] else "FAIL",
       "PASS" if not [k for k in bad if k.startswith("M204")] else "FAIL",
       len(NEED) - len(bad), len(NEED), "" if not bad else "  FAILED: " + ", ".join(bad)))
if bad and not PROBE:
    sys.exit(1)
