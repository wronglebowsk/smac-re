"""terran.exe string/VA helpers: import exe_strings as S; S.STRS is a sorted
list of (va, string) for every NUL-terminated printable ASCII string >=4 chars.
Built by scanning the raw PE once; VA mapping uses the section table."""
import re, struct

PATH = '/home/n100/reverse/smac/terran.exe'
_exe = open(PATH, 'rb').read()
_pe = struct.unpack_from('<I', _exe, 0x3c)[0]
_nsec = struct.unpack_from('<H', _exe, _pe + 6)[0]
_opt = struct.unpack_from('<H', _exe, _pe + 20)[0]
BASE = struct.unpack_from('<I', _exe, _pe + 52)[0]
SECS = []
_soff = _pe + 24 + _opt
for _i in range(_nsec):
    _name = _exe[_soff + _i * 40:_soff + _i * 40 + 8].rstrip(b'\0').decode()
    _vs, _va, _rs, _rp = struct.unpack_from('<IIII', _exe, _soff + _i * 40 + 8)
    SECS.append((_name, BASE + _va, _vs, _rp, _rs))


def off2va(o):
    for _n, va, vs, rp, rs in SECS:
        if rp <= o < rp + rs:
            return va + (o - rp)
    return None


def va2off(va):
    for _n, va0, vs, rp, rs in SECS:
        if va0 <= va < va0 + vs:
            return rp + (va - va0)
    return None


STRS = []
for _m in re.finditer(rb'[\x20-\x7e]{4,}\x00', _exe):
    _va = off2va(_m.start())
    if _va is not None:
        STRS.append((_va, _exe[_m.start():_m.end() - 1].decode('latin1')))
STRS.sort()

# name -> [(va, name)] index for the UPPER_CASE token inventory
TOKEN_RE = re.compile(r'^[A-Z][A-Z0-9_]{3,}$')
TOKENS = [(va, s) for va, s in STRS if TOKEN_RE.match(s)]


def find(pattern):
    """strings whose text matches regex `pattern` (case-insensitive)."""
    p = re.compile(pattern, re.I)
    return [(va, s) for va, s in STRS if p.search(s)]


def xref_targets(pattern):
    """just the VAs of matching strings"""
    return [va for va, s in find(pattern)]
