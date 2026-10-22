#!/usr/bin/env python3
"""Parse programs/Script.txt (SMAC dialog-box script) into a structured pane map.
Emits script_parsed.json: [{id, xs, x, y, widgets:[{kind:'caption'|'button'|'itemlist'|'listbox'|'wave', text|items}]}]
Directives observed in the file header docs + samples:
  #NAME            -> begin a pane definition (uppercase id)
  #xs N            -> pane width/size hint
  #x N / #y N      -> position
  #caption TEXT    -> title text (continues on following lines until blank)
  #button TEXT     -> button
  #itemlist        -> list of literal option lines follows (until next directive)
  #listbox         -> listbox widget
  #wave            -> audio?
  #<lowercase>     -> ?
Lines: ';' comment, '^' newline marker, '^^' centered, '{bold}', '[italic]',
'$NAME123' string substitution, '<n:a:b>' gender/plurality substitution.
"""
import json, re, sys

SRC = 'programs/Script.txt'

def parse(path=SRC):
    lines = open(path, 'rb').read().decode('latin-1').split('\r\n')
    panes = []
    cur = None
    pending = None  # accumulating list for itemlist
    i = 0
    def flush_pending():
        nonlocal pending
        if pending is not None and cur is not None:
            cur['widgets'].append({'kind': pending['kind'], 'items': pending['items']})
        pending = None
    for raw in lines:
        line = raw.rstrip()
        s = line.strip()
        if s.startswith(';'):
            continue
        if s == '':
            flush_pending()
            continue
        if s.startswith('#'):
            m = re.match(r'#([A-Za-z_][A-Za-z0-9_]*)\s*(.*)', s)
            if not m:
                continue
            name, rest = m.group(1), m.group(2).strip()
            low = name.lower()
            if re.fullmatch(r'[A-Z][A-Z0-9_]*', name):
                # pane id (uppercase) OR directives like #END/#TECH0
                flush_pending()
                if name in ('END',):
                    cur = None
                    continue
                cur = {'id': name, 'props': {}, 'widgets': []}
                panes.append(cur)
            elif low in ('xs','x','y'):
                if cur is not None:
                    try: cur['props'][low] = int(rest)
                    except ValueError: cur['props'][low] = rest
            elif low == 'caption':
                flush_pending()
                if cur is not None:
                    cur['widgets'].append({'kind':'caption','text':rest})
            elif low == 'button':
                flush_pending()
                if cur is not None:
                    cur['widgets'].append({'kind':'button','text':rest})
            elif low in ('itemlist','listbox'):
                flush_pending()
                pending = {'kind': low, 'items': []}
            else:
                if cur is not None:
                    cur['widgets'].append({'kind':'directive','name':name,'arg':rest})
            continue
        # continuation / item text
        if pending is not None:
            pending['items'].append(s)
        elif cur is not None and cur['widgets'] and cur['widgets'][-1]['kind']=='caption':
            cur['widgets'][-1]['text'] += ' ' + s.lstrip('^')
        elif cur is not None:
            cur.setdefault('text_lines', []).append(s)
    flush_pending()
    return panes

if __name__ == '__main__':
    panes = parse()
    json.dump(panes, open('script_parsed.json','w'), indent=1)
    print(f'{len(panes)} panes parsed -> script_parsed.json')
    for p in panes[:12]:
        kinds = [w['kind'] for w in p['widgets']]
        cap = next((w.get('text') for w in p['widgets'] if w['kind']=='caption'), None)
        print(f"  {p['id']:16s} xs={p['props'].get('xs','?'):>4} widgets={kinds} caption={cap!r}")
