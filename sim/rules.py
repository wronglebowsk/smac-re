"""sim.rules — alpha.txt's balance tables as a state model (R1 rung B1).

data/alpha.json is produced by scripts/parse_alpha.py from programs/alpha.txt: 45
`#SECTION`s of comma-separated records, each stored as {"fields": [...]} plus
"names" when the file's own trailing comments line up one-per-field. The exe loads
this file, so a reimplementation reads the tables rather than the binary.

This module loads and indexes; it does not interpret field semantics beyond what
the section name plus the record's own names give it. Field semantics are only
known where alpha.txt's comments say so (see ALPHA_RULES.md).
"""

import json


class RulesError(Exception):
    pass


class Rules:
    def __init__(self, path):
        with open(path, encoding="utf-8") as f:
            try:
                doc = json.load(f)
            except json.JSONDecodeError as e:
                raise RulesError(f"{path}: not JSON: {e}") from e
        if not isinstance(doc, dict):
            raise RulesError(f"{path}: expected an object of sections, got {type(doc).__name__}")
        self.path = path
        self.sections = doc
        self.counts = {k: len(v) for k, v in doc.items()}
        self.total_records = sum(self.counts.values())
        self.empty_sections = sorted(k for k, c in self.counts.items() if c == 0)

    def section(self, name):
        try:
            return self.sections[name]
        except KeyError:
            raise RulesError(f"{self.path}: no section #{name}") from None

    def record(self, name, i):
        recs = self.section(name)
        try:
            return recs[i]
        except IndexError:
            raise RulesError(f"{self.path}: #{name} has {len(recs)} records, asked for {i}") from None

    def fields(self, name, i):
        return list(self.record(name, i)["fields"])

    def field(self, name, i, col):
        f = self.fields(name, i)
        try:
            return f[col]
        except IndexError:
            raise RulesError(f"{self.path}: #{name}[{i}] has {len(f)} fields, asked for {col}") from None

    def named(self, name, i):
        """(field, comment-name) pairs for a record; names fall back to '?<col>'."""
        rec = self.record(name, i)
        f = rec["fields"]
        n = rec.get("names") or []
        return list(zip(f, n + ["?%d" % j for j in range(len(n), len(f))]))

    def find_by_first_field(self, name, want):
        """Row index of the first record whose field 0 equals `want`, else None."""
        want = str(want).strip().lower()
        for i, rec in enumerate(self.section(name)):
            if str(rec["fields"][0]).strip().lower() == want:
                return i
        return None


def load(path):
    return Rules(path)
