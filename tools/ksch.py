"""KiCad schematic s-expression editing helpers: lossless load/save, pin positions, wires, labels, symbols.

Used by the scripted schematic edits in this repo. Verify every scripted edit with kicad-cli ERC and a
netlist export (compare nets before/after), and restore *.kicad_prl afterwards (kicad-cli rewrites it)."""
import math, uuid as _uuid


class S(str):
    """A quoted string token."""


def tokenize(s):
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in '()':
            yield c; i += 1
        elif c.isspace():
            i += 1
        elif c == '"':
            j = i + 1; buf = []
            while s[j] != '"':
                if s[j] == '\\':
                    nx = s[j + 1]
                    buf.append({'n': '\n', 't': '\t'}.get(nx, nx)); j += 2
                else:
                    buf.append(s[j]); j += 1
            yield S(''.join(buf)); i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in '()':
                j += 1
            yield s[i:j]; i = j


def parse(s):
    stack = [[]]
    for t in tokenize(s):
        if t == '(' and not isinstance(t, S):
            stack.append([])
        elif t == ')' and not isinstance(t, S):
            x = stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t)
    return stack[0][0]


def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def dump(node, ind=0):
    if not isinstance(node, list):
        return q(node) if isinstance(node, S) else node
    simple = all(not isinstance(c, list) for c in node)
    if simple:
        return '(' + ' '.join(dump(c) for c in node) + ')'
    out = '(' + ' '.join(dump(c) for c in node if not isinstance(c, list))
    for c in node:
        if isinstance(c, list):
            out += '\n' + '\t' * (ind + 1) + dump(c, ind + 1)
    return out + '\n' + '\t' * ind + ')'


def load(fn):
    return parse(open(fn).read())


def save(t, fn):
    open(fn, 'w').write(dump(t) + '\n')


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def first(node, key):
    r = find(node, key); return r[0] if r else None


def prop(sym, name):
    for p in find(sym, 'property'):
        if p[1] == name:
            return p[2]


def set_prop(sym, name, value, hide=True):
    for p in find(sym, 'property'):
        if p[1] == name:
            p[2] = S(value); return
    at = first(sym, 'at')
    eff = ['effects', ['font', ['size', '1.27', '1.27']]]
    if hide:
        eff.append(['hide', 'yes'])
    sym.insert(index_after_props(sym), ['property', S(name), S(value), ['at', at[1], at[2], '0'], eff])


def index_after_props(sym):
    idx = [i for i, c in enumerate(sym) if isinstance(c, list) and c and c[0] == 'property']
    return idx[-1] + 1


def U():
    return S(str(_uuid.uuid4()))


def fmt(v):
    v = round(float(v), 4)
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s == '-0' else s


def R(v):
    return round(float(v), 2)


def symbols(t):
    return find(t, 'symbol')


def by_ref(t, ref):
    for s in symbols(t):
        if prop(s, 'Reference') == ref:
            return s
    raise KeyError(ref)


def lib_symbol(t, lib_id):
    for s in find(first(t, 'lib_symbols'), 'symbol'):
        if s[1] == lib_id:
            return s
    raise KeyError(lib_id)


def lib_pins(t, lib_id, unit=1):
    """{number: (x, y, name)} for unit 0 and `unit`, body style 1."""
    ls = lib_symbol(t, lib_id); out = {}
    for sub in find(ls, 'symbol'):
        parts = sub[1].rsplit('_', 2)
        u, style = int(parts[-2]), int(parts[-1])
        if u not in (0, unit) or style not in (0, 1):
            continue
        for p in find(sub, 'pin'):
            at = first(p, 'at'); ln = float(first(p, 'length')[1]); a = math.radians(float(at[3]) if len(at) > 3 else 0)
            out[str(first(p, 'number')[1])] = (float(at[1]), float(at[2]), str(first(p, 'name')[1]))
    return out


def pin_pos(t, sym, number):
    """Absolute schematic position of a pin's connection point."""
    lib_id = first(sym, 'lib_id')[1]
    unit = int(first(sym, 'unit')[1]) if first(sym, 'unit') else 1
    px, py, _ = lib_pins(t, lib_id, unit)[str(number)]
    at = first(sym, 'at'); X, Y = float(at[1]), float(at[2]); a = math.radians(float(at[3]) if len(at) > 3 else 0)
    m = first(sym, 'mirror')
    if m and m[1] == 'x':
        py = -py
    if m and m[1] == 'y':
        px = -px
    rx = px * math.cos(a) - py * math.sin(a)
    ry = px * math.sin(a) + py * math.cos(a)
    return (R(X + rx), R(Y - ry))


def wires(t):
    return find(t, 'wire')


def wire_pts(w):
    return [(R(x[1]), R(x[2])) for x in find(first(w, 'pts'), 'xy')]


def add_wire(t, a, b):
    t.append(['wire', ['pts', ['xy', fmt(a[0]), fmt(a[1])], ['xy', fmt(b[0]), fmt(b[1])]],
              ['stroke', ['width', '0'], ['type', 'default']], ['uuid', U()]])


def add_label(t, name, p, angle=0, kind='label', shape='bidirectional'):
    just = {0: 'left bottom', 180: 'right bottom', 90: 'left bottom', 270: 'right bottom'}[angle]
    node = [kind, S(name)]
    if kind != 'label':
        node.append(['shape', shape])
    node += [['at', fmt(p[0]), fmt(p[1]), str(angle)],
             ['effects', ['font', ['size', '1.27', '1.27']], ['justify'] + just.split()],
             ['uuid', U()]]
    t.append(node)


def add_nc(t, p):
    t.append(['no_connect', ['at', fmt(p[0]), fmt(p[1])], ['uuid', U()]])


def add_junction(t, p):
    t.append(['junction', ['at', fmt(p[0]), fmt(p[1])], ['diameter', '0'], ['color', '0', '0', '0', '0'], ['uuid', U()]])


def add_text(t, text, p):
    t.append(['text', S(text), ['exclude_from_sim', 'no'], ['at', fmt(p[0]), fmt(p[1]), '0'],
              ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left']], ['uuid', U()]])


def instances_block(project, path, ref):
    return ['instances', ['project', S(project), ['path', S(path), ['reference', S(ref)], ['unit', '1']]]]


def add_symbol(t, lib_id, ref, value, p, angle=0, footprint='', props=None, project='', path='', pins=('1', '2'),
               in_bom=True, extra_paths=()):
    """Place a symbol instance. extra_paths: [(path, ref)] for multi-instance sheets."""
    X, Y = p
    sym = ['symbol', ['lib_id', S(lib_id)], ['at', fmt(X), fmt(Y), str(angle)], ['unit', '1'],
           ['exclude_from_sim', 'no'], ['in_bom', 'yes' if in_bom else 'no'], ['on_board', 'yes'], ['dnp', 'no'],
           ['fields_autoplaced', 'yes'], ['uuid', U()]]
    hidden = ref.startswith('#')
    sym.append(['property', S('Reference'), S(ref), ['at', fmt(X + 2.54), fmt(Y - 1.27), '0'],
                ['effects', ['font', ['size', '1.27', '1.27']]] + ([['hide', 'yes']] if hidden else [['justify', 'left']])])
    sym.append(['property', S('Value'), S(value), ['at', fmt(X + 2.54), fmt(Y + 1.27), '0'],
                ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left']]])
    for name, val in [('Footprint', footprint), ('Datasheet', props.pop('Datasheet', '~') if props else '~'),
                      ('Description', props.pop('Description', '') if props else '')] + list((props or {}).items()):
        sym.append(['property', S(name), S(val), ['at', fmt(X), fmt(Y), '0'],
                    ['effects', ['font', ['size', '1.27', '1.27']], ['hide', 'yes']]])
    for n in pins:
        sym.append(['pin', S(n), ['uuid', U()]])
    inst = ['instances', ['project', S(project)]]
    for pth, r in [(path, ref)] + list(extra_paths):
        inst[1].append(['path', S(pth), ['reference', S(r)], ['unit', '1']])
    sym.append(inst)
    t.append(sym)
    return sym


def remove(t, node):
    for i, c in enumerate(t):
        if c is node:
            del t[i]; return
    raise ValueError('node not found')


def point_users(t, pt, pin_points):
    """Count connection items touching point pt (wire ends, wire mid-points, labels, pins, junctions)."""
    n = 0
    for w in wires(t):
        a, b = wire_pts(w)
        if pt in (a, b):
            n += 1
        elif on_segment(pt, a, b):
            n += 2
    for kind in ('label', 'global_label', 'hierarchical_label', 'junction', 'no_connect'):
        for l in find(t, kind):
            at = first(l, 'at')
            if (R(at[1]), R(at[2])) == pt:
                n += 1
    n += pin_points.get(pt, 0)
    return n


def on_segment(p, a, b):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    if (x1 == x2 == x) and min(y1, y2) < y < max(y1, y2):
        return True
    if (y1 == y2 == y) and min(x1, x2) < x < max(x1, x2):
        return True
    return False


def all_pin_points(t, sheet_pins=()):
    pts = {}
    for s in symbols(t):
        lib_id = first(s, 'lib_id')[1]
        unit = int(first(s, 'unit')[1]) if first(s, 'unit') else 1
        for num in lib_pins(t, lib_id, unit):
            p = pin_pos(t, s, num); pts[p] = pts.get(p, 0) + 1
    for sh in find(t, 'sheet'):
        for sp in find(sh, 'pin'):
            at = first(sp, 'at'); p = (R(at[1]), R(at[2])); pts[p] = pts.get(p, 0) + 1
    return pts


def prune_stubs(t):
    """Remove wires with a dangling end, labels on nothing, NC flags on nothing; repeat until stable."""
    removed = 0
    while True:
        pins = all_pin_points(t); changed = False
        for w in list(wires(t)):
            a, b = wire_pts(w)
            if point_users(t, a, pins) <= 1 or point_users(t, b, pins) <= 1:
                remove(t, w); removed += 1; changed = True
        for kind in ('label', 'hierarchical_label', 'global_label', 'no_connect', 'junction'):
            for l in list(find(t, kind)):
                at = first(l, 'at'); p = (R(at[1]), R(at[2]))
                if point_users(t, p, pins) <= 1:
                    remove(t, l); removed += 1; changed = True
        if not changed:
            return removed
