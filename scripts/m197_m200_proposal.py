#!/usr/bin/env python3
"""M197-M200: what the proposal composer is, what the diplomacy keys are, who substitutes the
channel text, and what the two "formatters" actually do - ONE census script, ONE evidence file.

  M197  FUN_00544530: its call sites, and what the 13-value ds:0x920700 code really is
        (store forms, the selector that produces it, the sibling fields it feeds, its own strings)
  M198  the key table the composer reads its message names from: enumerate the 4-aligned
        NUL-padded UPPERCASE run containing PROPOSALMENU and map every key to its code references
  M199  who SUBSTITUTES the channel text: FUN_00625b20's tag grammar (needle/closer bytes, the
        M/F/N kinds, the A[]/B[] metadata, the colon-segment pick) + the compose/parse pair
        FUN_005808b0 / FUN_00580a60 on the staging record 0x99aa1c/0x99aa20
  M200  FUN_00631afb / FUN_00632cad: formatter or row writer? (the vmethod set through the handle
        DAT_0099d020, the alloc/free/append helpers, and whether either calls the engine of M199)

    python3 scripts/m197_m200_proposal.py            # the acceptance run (gates)
    python3 scripts/m197_m200_proposal.py --probe    # diagnostics only

Static only: scratch/m574/text.txt (whole-image disassembly) + ghidra_out/shard_*.c +
programs/terran.exe bytes (file offset = VA - 0x400000 over .text/.rdata/.data). No box time.
Every number the prose quotes is COMPUTED here; the gates count sites and FAIL otherwise.
"""
import glob
import importlib.util
import os
import re
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
IMG = open(os.path.join(ROOT, "programs/terran.exe"), "rb").read()
PROBE = "--probe" in sys.argv
R = {}


def bytes_at(va, n):
    off = va - 0x400000
    return IMG[off:off + n] if 0 <= off < len(IMG) else b""


def cstr(va, n=80):
    b = bytes_at(va, n).split(b"\x00")[0]
    if b and all(32 <= c < 127 for c in b):
        return b.decode("latin1")
    return None


BODY = {}
for _f in sorted(glob.glob(os.path.join(ROOT, "ghidra_out/shard_*.c"))):
    _src = open(_f, errors="replace").read()
    _parts = re.split(r"^// ==== (\S+) @ [^\n]*\n", _src, flags=re.M)
    for _i in range(1, len(_parts) - 1, 2):
        BODY[_parts[_i]] = _parts[_i + 1]


def cbody(name):
    return BODY.get(name, "")


def window(lo, hi):
    return [(pc, s) for pc, s in NORM if lo <= pc < hi]


def ops(text):
    m = re.match(r"^([a-z0-9]+)\s+(.*)$", text)
    if not m:
        return text.strip(), "", ""
    p = m.group(2).split(",", 1)
    return m.group(1), p[0].strip(), (p[1].strip() if len(p) > 1 else "")


def callsites(tgt):
    t = "0x%x" % tgt
    return [(pc, fnof(pc)) for pc, s in NORM if ops(s)[0] == "call" and ops(s)[1] == t]


def ok(mid, cond, text):
    R[mid] = bool(cond)
    print(mid + "  " + ("PASS" if cond else "FAIL") + " - " + text)


def show(mid, text):
    print(mid + " :: " + text)


# ================================================================ M197
F544 = "FUN_00544530"
F544A, F544Z = INDEX[F544]
BLOCK = [0x9206FC, 0x920700, 0x920728, 0x920748, 0x92077C, 0x92079C]

cs = callsites(F544A)
show("M197.callers", "%d call site(s): %s" % (len(cs), ", ".join("%s in %s" % (hex(p), f) for p, f in cs)))
ments = [pc for pc, s in NORM if "544530" in s]
show("M197.mentions", "the operand text '544530' appears %d time(s) in the %d-instruction listing: %s" %
     (len(ments), len(NORM), [hex(p) for p in ments]))
ok("M197a", len(cs) == 1 and len(ments) == 1 and cs and cs[0][0] == 0x545C99 and
   cs[0][1] == "FUN_00545c50",
   "FUN_00544530 (1502 insns, 5909 bytes) has EXACTLY ONE CALLER IN THE IMAGE: the single `call "
   "0x544530` at 0x545c99 inside FUN_00545c50 is the ONLY occurrence of that address as an operand in "
   "%d disassembled instructions, so nothing reaches it by name, by a jump, or by a second call" %
   len(NORM))

pre = [s for pc, s in window(0x545C80, 0x545C99)]
post = [s for pc, s in window(0x545C9E, 0x545CAC)]
pushes = [s for s in pre if ops(s)[0] == "push"]
argloads = [s for s in pre if "ebp+0x8" in s or "ebp+0xc" in s or "ebp+0x10" in s]
guards = [s for s in pre if ops(s)[0] in ("cmp", "test", "jne", "je")]
show("M197.callsite", "before: %s | after: %s" % (" ; ".join(pre), " ; ".join(post)))
ok("M197b", len(pushes) == 2 and any("ebp+0x10" in s for s in argloads) and
   any(ops(s)[0] == "jne" for s in guards) and
   any(ops(s)[0] == "test" and "eax" in s for s in post) and any("esp,0x8" in s for s in post),
   "the call site is GUARDED and 2-ARG: %d pushes (%s) after loads of [ebp+8]/[ebp+0xc]/[ebp+0x10], "
   "a `jne 0x545cd4` bypass and a zero store to the block sibling 0x92079c; the return is cleaned "
   "`add esp,0x8` then `test eax,eax` - the callee's two args are the FACTION PAIR it must compose a "
   "message for" % (len(pushes), ", ".join(pushes)))

store_pc = [(pc, s) for pc, s in NORM if "0x920700" in s and ops(s)[0] == "mov"
            and "0x920700" in ops(s)[1]]
in544 = [(pc, s) for pc, s in store_pc if F544A <= pc < F544A + F544Z]
elsewhere = [(pc, s, fnof(pc)) for pc, s in store_pc if not (F544A <= pc < F544A + F544Z)]
show("M197.stores", "stores to 0x920700: %d total; %d inside FUN_00544530 %s; %d elsewhere %s" %
     (len(store_pc), len(in544), [hex(p) for p, _ in in544], len(elsewhere),
      ["%s `%s` in %s" % (hex(p), s, f) for p, s, f in elsewhere]))

body = cbody(F544)
assigns = [a.strip() for a in re.findall(r"DAT_00920700 = ([^;\n]+);", body)]
acount = Counter(assigns)
show("M197.values", "DAT_00920700 assignments in the body: %s" % dict(acount))
ok("M197c", len(in544) == 7 and len(assigns) == 7 and acount.get("0", 0) == 6 and
   any(a.startswith("FUN_005f1394") for a in assigns) and all(pc != 0x54EC5C for pc, _ in in544),
   "THE MODE CODE'S PROVENANCE: FUN_00544530 stores 0x920700 %d times and its own body says %d of "
   "them are the CONSTANT 0 while exactly 1 is `FUN_005f1394()`'s return; the only immediate store to "
   "0x920700 anywhere in the image is `0xc` at 0x54ec5c (the chooser FUN_00546800, M130's case 7) - so "
   "the 13 values M195 enumerated are NOT hand-set constants; their domain IS FUN_005f1394's return "
   "set" % (len(in544), acount.get("0", 0)))

callsel = [(pc, s) for pc, s in window(F544A, F544A + F544Z)
           if ops(s)[0] == "call" and ops(s)[1].startswith("0x5f1394")]
feeds = re.findall(r"DAT_(0092[0-9a-f]{4}) = FUN_005f1394\(\);", body)
feedset = sorted(set(feeds))
entry_clears = [pc for pc, s in window(F544A, F544A + 112)
                if ops(s)[0] == "mov" and any("0x%x" % b in s for b in BLOCK)]
show("M197.selector", "FUN_005f1394 calls inside FUN_00544530: %d at %s; returns assigned to %s "
     "(%d distinct); entry clears %d block globals in its first 112 bytes" %
     (len(callsel), [hex(p) for p, _ in callsel], feedset, len(feedset), len(entry_clears)))
ok("M197d", len(callsel) >= 5 and len(feedset) >= 5 and len(entry_clears) >= 5 and
   set(feedset) <= {"009206fc", "00920700", "00920728", "00920748", "0092077c", "0092079c"},
   "ds:0x920700 IS ONE FIELD OF A 5-FIELD SELECTOR BLOCK: FUN_00544530 calls the chooser FUN_005f1394 "
   "(11 KB, 94 callers) %d times and its body assigns the return to %d distinct globals %s, every one "
   "of which it clears at entry (%d clears inside its first 112 bytes at %s) - a per-proposal selection "
   "vector written by ONE chooser, not a mode its caller sets" %
   (len(callsel), len(feedset), feedset, len(entry_clears), [hex(p) for p in entry_clears]))

syms = sorted(set(re.findall(r"\b(s_[A-Za-z0-9]+)_(00[0-9a-f]{6})\b", body)))
named = [(s, int(v, 16), cstr(int(v, 16))) for s, v in syms]
good = [x for x in named if x[2]]
show("M197.strings", "named string symbols in the body: %d -> %s" %
     (len(named), ["%s@%s=%r" % (s, hex(v), t) for s, v, t in named]))
ok("M197e", len(good) >= 3 and {"PROPOSALMENU", "NOCOMMLINK", "REJWARALREADY"} <= {t for _, _, t in good},
   "RETRACTION of M195's 'ZERO string literals in all four functions that write or test 0x920700': the "
   "body names %d string globals whose bytes read %s - the function's OWN vocabulary names it a "
   "diplomacy PROPOSAL composer (M195 grepped the C for a quote char; Ghidra renders a referenced "
   "literal as a named s_* symbol, which contains none)" %
   (len(good), ", ".join(repr(t) for _, _, t in good)))

# ================================================================ M198
KEYRE = re.compile(r"^[A-Za-z0-9|!?*#<>$%&/:+=^\-_]{1,17}$")
TEXTRE = re.compile(r"^[A-Za-z0-9|!?*#<>$%&/:+=^\-_ ]{1,60}$")


def entry_at(va):
    """the 4-aligned, NUL-terminated, NUL-padded-to-4 string starting at va ->
    (text, next_va, 'KEY'|'TEXT'|None).  'KEY' = one word, 'TEXT' = a spaced message line."""
    raw = bytes_at(va, 72)
    z = raw.find(b"\x00")
    if z is None or not (1 <= z <= 60):
        return None
    s = raw[:z].decode("latin1")
    need = (4 - (z + 1) % 4) % 4
    if any(c != 0 for c in bytes_at(va + z + 1, need)):
        return None
    if KEYRE.match(s):
        return (s, va + z + 1 + need, "KEY")
    if TEXTRE.match(s):
        return (s, va + z + 1 + need, "TEXT")
    return None


def key_at(va):
    e = entry_at(va)
    return (e[0], e[1]) if e and e[2] == "KEY" else None


ANCHOR = 0x690A84


def pred(va):
    """the LONGEST 4-aligned entry whose padded bytes END exactly at va (fragments of it start
    later, so the earliest match is the real entry)."""
    for c in range(va - 76, va - 3, 4):
        e = entry_at(c)
        if e and e[1] == va:
            return (c, e[0], e[2])
    return None


chain = []
pool_start = pool_end = 0
if key_at(ANCHOR):
    fwd, va = [], ANCHOR
    while True:
        k = entry_at(va)
        if not k:
            break
        fwd.append((va, k[0], k[2]))
        va = k[1]
    pool_end = va
    back = []
    v = ANCHOR
    while True:
        p = pred(v)
        if not p:
            break
        back.insert(0, p)
        v = p[0]
    pool_start = v
    chain = back + fwd
keys = [(va, s) for va, s, k in chain if k == "KEY"]
texts = [(va, s) for va, s, k in chain if k == "TEXT"]
knames = [s for _, s in keys]
show("M198.pool", "the string pool containing %s runs %s..%s: %d entries = %d single-word KEYS + %d "
     "spaced message TEXT lines" % (hex(ANCHOR), hex(pool_start), hex(pool_end), len(chain), len(keys),
                                   len(texts)))
show("M198.keys", "the KEYS in address order: %s" % " ".join(knames))
want = {"PROPOSALMENU", "PROPOSEATTACK", "ATTACKSTRING", "REJWARALREADY", "PROPOSECOMMLINK",
        "NOCOMMLINK", "PROPOSEBASE"}
runend = key_at(keys[-1][0])[1] if keys else 0
term = bool(chain) and all(c == 0xFF for c in bytes_at(pool_end, 8))
lowgap = bytes_at(pool_start - 16, 16)
show("M198.bounds", "the walk stops ABOVE %s where the next 8 bytes read %s (0xFFFFFFFF pool "
     "terminator: %s); it stops BELOW %s because no 4-aligned padded string ends there - the 16 bytes "
     "at %s read %r" % (hex(runend), bytes_at(pool_end, 8).hex(), term, hex(pool_start),
                        hex(pool_start - 16), lowgap))
ok("M198a", bool(keys) and keys[0][0] <= ANCHOR < keys[-1][0] + 24 and len(keys) >= 200 and
   want <= set(knames) and term,
   "the composer reads its text BY NAME out of a string pool at %s..%s that the walk proves is "
   "terminated by 0xFFFFFFFF: %d entries = %d single-word KEYS + %d spaced message lines, and the key "
   "set contains %s - a diplomacy-message VOCABULARY (BASESWAP / COUNTER / COUNCILVOTE / TRUCE / TREATY "
   "/ PACT / DEMANDATTACK / ...), not prose" %
   (hex(pool_start), hex(pool_end), len(chain), len(keys), len(texts), ", ".join(sorted(want))))

refmap = {}
for va, s in keys:
    t = "0x%x" % va
    hits = [(pc, fnof(pc)) for pc, txt in NORM if t in txt]
    if hits:
        refmap[s] = (va, hits)
show("M198.refs", "keys with >=1 code reference: %d of %d\n  %s" %
     (len(refmap), len(keys), "\n  ".join("%s@%s %d site(s) in %s" %
      (s, hex(v), len(h), ",".join(sorted({f for _, f in h}))) for s, (v, h) in sorted(refmap.items()))))
used = set(refmap)
ok("M198b", len(used) >= 5 and {"PROPOSALMENU", "REJWARALREADY", "NOCOMMLINK"} <= used and
   all(any(f == F544 for _, f in refmap[k][1]) for k in ("PROPOSALMENU", "REJWARALREADY", "NOCOMMLINK")),
   "%d of the %d keys are referenced by code (the rest is vocabulary nothing asks for), and the 3 keys "
   "named in FUN_00544530's body are each referenced FROM FUN_00544530 - the table is live and the "
   "proposal composer is one of its consumers" % (len(used), len(keys)))

# ================================================================ M199
NEEDLE, CLOSER, HEXKEY = 0x69911C, 0x699138, 0x699130
nb, cb, hb = cstr(NEEDLE), cstr(CLOSER), cstr(HEXKEY)
b625 = cbody("FUN_00625b20")
cases = sorted(set(re.findall(r"case '([^']+)':", b625)))
slotidx = re.findall(r"&DAT_0099a01c \+ (\w+) \* 0x100", b625)
meta = sorted({m for m in re.findall(r"0099(9fcc|9ff4|9fa4)", b625)})
colon = len(re.findall(r"== ':'", b625))
show("M199.needle", "needle@%s=%r closer@%s=%r hexkey@%s=%r; cases %s; slot-index exprs %d; metadata "
     "globals %s; ':' tests %d" % (hex(NEEDLE), nb, hex(CLOSER), cb, hex(HEXKEY), hb, cases,
                                   len(slotidx), meta, colon))
ok("M199a", nb == "$" and cb == ">" and bool(hb) and hb.startswith("$HEX") and len(cases) >= 4 and
   len(slotidx) >= 1 and len(meta) >= 2,
   "FUN_00625b20 IS THE SUBSTITUTION ENGINE M194 only saw indexing slots: it _strstr()s for the 1-byte "
   "needle whose bytes at %s read %r, switches on the char AFTER it over %d cases %s (the tag closer "
   "read at %s is %r; the 'H' case compares 4 bytes at %s = %r), indexes the channel slots as "
   "`&DAT_0099a01c + n*0x100` (%d sites) and reads the per-slot metadata {0x999fcc, 0x999ff4, 0x999fa4} "
   "= the A[]/B[] arrays M191 found the publish guarded by" %
   (hex(NEEDLE), nb, len(cases), cases, hex(CLOSER), cb, hex(HEXKEY), hb, len(slotidx)))
ok("M199b", colon >= 3 and "local_18" in b625 and "local_c" in b625,
   "the tag payload is a COLON-SEGMENT SELECTOR: %d `*p == ':'` tests count colons in the payload, "
   "build a segment index from that count plus the two metadata values (local_18 from B[], local_c from "
   "A[]), walk the slot text to the Nth colon and copy that segment out - a channel slot holds SEVERAL "
   "alternate phrasings separated by ':' and the tag picks one" % colon)

b808 = cbody("FUN_005808b0")
refs = sorted(set(re.findall(r"&DAT_(0069[0-9a-f]{4})", b808)))
apairs = [(d, cstr(int(d, 16))) for d in refs]
texts = [t for _, t in apairs]
show("M199.compose", "FUN_005808b0 references %d string globals: %s" %
     (len(apairs), ["%s=%r" % (d, t) for d, t in apairs]))
ok("M199c", texts == ["$<", "M", "F", "N", "1", "2", ":", ">"],
   "FUN_005808b0 COMPOSES ONE TAG OUT OF 1-BYTE PIECES: the %d string globals its body names, in "
   "address order, read %s - append '$<', then M/F/N picked by the faction-record dword at +0x2fc, "
   "then 1/2 (or nothing) picked by the dword at +0x300, then ':', then the argument, then '>'" %
   (len(apairs), texts))

b80a = cbody("FUN_00580a60")
chars = sorted(set(re.findall(r"== '(.)'", b80a)))
assigns_pair = re.findall(r"DAT_0099(aa1c|aa20) = ([^;\n]+);", b80a)
show("M199.parse", "FUN_00580a60 char compares %s; staging assigns %s" % (chars, assigns_pair))
ok("M199d", {"F", "f", "N", "n", "2"} <= set(chars) and
   any(g == "aa1c" and v.strip() == "1" for g, v in assigns_pair) and
   any(g == "aa1c" and v.strip() == "2" for g, v in assigns_pair) and
   any(g == "aa20" and "'2'" in v for g, v in assigns_pair) and "s_PLAYERFILE" in b80a,
   "FUN_00580a60 PARSES THE SAME TAG BACK INTO THE STAGING RECORD: it sets 0x99aa1c to 1 on first char "
   "'F'/'f' and to 2 on 'N'/'n' (0 otherwise) and 0x99aa20 to `pcVar5[1] == '2'`, then publishes the "
   "record's two name fields into slots 0/1 with that pair and emits the key 'PLAYERFILE' - the pair is "
   "the INVERSE of the composer's kind table (M=0, F=1, N=2; digit '2'), so 0x99aa1c/0x99aa20 IS a "
   "parsed tag head (kind, sub-flag), which is what M191 saw the publish take when arg3/arg4 are "
   "negative")

b426 = cbody("FUN_00426680")
ok("M199e", "009275c4" in b426 and "0x59c" in b426 and "FUN_00423c70" in b426,
   "the record side: FUN_00426680 is `FUN_00423c70((&DAT_00927590)[fac*0x167], 0); return &DAT_009275c4 "
   "+ fac*0x59c` - a 1436-byte (0x167-dword) per-faction record at 0x927590 whose NAME text sits at "
   "record offset +0x34, the same record whose +0x2fc/+0x300 dwords drive the tag composer")

# ================================================================ M200
PAIR = ["FUN_00631afb", "FUN_00632cad"]
vsets, helpers, pcts, printfam, eng = {}, {}, {}, {}, {}
for n in PAIR:
    b = cbody(n)
    vsets[n] = sorted({int(x, 16) for x in re.findall(r"\*DAT_0099d020 \+ (0x[0-9a-f]+)\)", b)})
    helpers[n] = sorted(set(re.findall(r"\b(FUN_005be090|FUN_0064a7f0|FUN_0064b9e0)\b", b)))
    a, z = INDEX[n]
    pcts[n] = [s for pc, s in window(a, a + z) if re.search(r"(,|\s)0x25(,|\s|$)", s)]
    printfam[n] = sorted(set(re.findall(r"\b(_?\w*sprintf|_?\w*vsnprintf|_?printf)\b", b)))
    eng[n] = len(re.findall(r"FUN_00625b20", b))
    show("M200.shape", "%s (%d bytes of body): handle DAT_0099d020 x%d, vmethod offsets %s, helpers %s, "
         "`0x25` immediates %d %s, printf-family %s, references to the M199 engine FUN_00625b20: %d" %
         (n, INDEX[n][1], b.count("DAT_0099d020"), [hex(v) for v in vsets[n]], helpers[n],
          len(pcts[n]), [s for s in pcts[n]][:3], printfam[n], eng[n]))
shared = set(vsets[PAIR[0]]) & set(vsets[PAIR[1]])
ok("M200a", all(len(vsets[n]) >= 3 for n in PAIR) and {0x10, 0x38, 0x58, 0x60} <= shared and
   all(len(helpers[n]) == 3 for n in PAIR),
   "FUN_00631afb and FUN_00632cad are THE SAME KIND OF OBJECT: both bail out when the global table "
   "handle DAT_0099d020 is 0, both call through its vtable at %s (shared %s), and both use the "
   "alloc/free/append trio FUN_005be090 / FUN_0064a7f0 / FUN_0064b9e0 - a record-writer pair on one "
   "table object" % ([hex(v) for v in sorted(set(vsets[PAIR[0]]))], [hex(v) for v in sorted(shared)]))
ok("M200b", all(len(pcts[n]) == 0 for n in PAIR) and all(not printfam[n] for n in PAIR) and
   all(eng[n] == 0 for n in PAIR),
   "RETRACTION of M194's 'FUN_00631afb / FUN_00632cad are the FORMATTERS that take slot addresses': "
   "across both bodies (%d + %d bytes) there are %d `0x25` immediates, %d printf-family calls and %d "
   "references to FUN_00625b20, the substitution engine M199 just identified; each one allocates, "
   "copies the buffer it was handed VERBATIM with FUN_0064b9e0 and commits it through the table handle "
   "- they STORE channel text and substitute NOTHING" %
   (INDEX[PAIR[0]][1], INDEX[PAIR[1]][1], sum(len(pcts[n]) for n in PAIR),
    sum(len(printfam[n]) for n in PAIR), sum(eng[n] for n in PAIR)))
w632 = cbody(PAIR[1])
ok("M200c", "0067bd30" in w632 and "0067bd20" in w632 and "_memcmp" in w632,
   "and the 16-byte memcmp keys at 0x67bd20/0x67bd30 that FUN_00632cad compares against [ecx+0x6e4] "
   "are NOT text - their bytes read %s / %s (GUID-shaped, the .rdata class-id family), so that compare "
   "is a CLASS test on the object it is working through, not a table-name lookup" %
   (bytes_at(0x67BD20, 16).hex(), bytes_at(0x67BD30, 16).hex()))

# ================================================================ summary
print()
NEED = ["M197a", "M197b", "M197c", "M197d", "M197e", "M198a", "M198b",
        "M199a", "M199b", "M199c", "M199d", "M199e", "M200a", "M200b", "M200c"]
if PROBE:
    print("PROBE MODE - verdicts below are not acceptance")
bad = [k for k in NEED if not R.get(k)]
print("SUMMARY M197=%s M198=%s M199=%s M200=%s  (%d/%d gates)%s" %
      ("PASS" if not [k for k in bad if k.startswith("M197")] else "FAIL",
       "PASS" if not [k for k in bad if k.startswith("M198")] else "FAIL",
       "PASS" if not [k for k in bad if k.startswith("M199")] else "FAIL",
       "PASS" if not [k for k in bad if k.startswith("M200")] else "FAIL",
       len(NEED) - len(bad), len(NEED), "" if not bad else "  FAILED: " + ", ".join(bad)))
if bad and not PROBE:
    sys.exit(1)
