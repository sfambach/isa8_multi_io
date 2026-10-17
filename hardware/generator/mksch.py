# Generates the hierarchical KiCad 7 schematic of isa8_multi_io from design.py and layout.py.
# Wires are routed on a 2.54 mm grid: wires of different nets may only cross at right angles,
# never touch, bend or end on each other, so the drawn connections equal the netlist
# (checked afterwards by verify.py against the KiCad netlist export).
import heapq, json, math, os, sys, uuid
from collections import defaultdict
from sexpr import parse, dump, Sym, find, first
from symbols import SYMBOLS, G
from geometry import geom, half_width
import design
from layout import LAYOUT, CAP_ROW

OUT = sys.argv[1]
PROJECT = 'isa8_multi_io'
NS = uuid.UUID('6f1c1b5e-7d43-4a2e-9a55-6b0e8e1c2a10')


def U(*key):
    return str(uuid.uuid5(NS, '/'.join(map(str, key))))


ROOT = U('root')
PAPER = {'A2': (594, 420), 'A3': (420, 297), 'A4': (297, 210)}
DIRV = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}


def S(name):
    return Sym(name)


def eff(hide=False, justify=None, size=1.27):
    e = [S('effects'), [S('font'), [S('size'), size, size]]]
    if justify:
        e.append([S('justify')] + [S(j) for j in justify.split()])
    if hide:
        e.append(S('hide'))
    return e


def stroke(w=0.254):
    return [S('stroke'), [S('width'), w], [S('type'), S('default')]]


def fill(t='none'):
    return [S('fill'), [S('type'), S(t)]]


def label_len(text):
    return len(text.replace('~{', '').replace('}', ''))


# ------------------------------------------------------------------ library symbols
def lib_symbol(symname):
    sym = SYMBOLS[symname]
    pins, (x1, y1, x2, y2) = geom(symname)
    name = 'isa8:' + symname
    body = [S('symbol'), symname + '_0_1']
    if sym['kind'] == 'box':
        body.append([S('rectangle'), [S('start'), x1, y2], [S('end'), x2, y1], stroke(), fill('background')])
    else:
        rot = (lambda x, y: (-y, x)) if sym['horizontal'] else (lambda x, y: (x, y))

        def poly(pts, w=0.254, f='none'):
            return [S('polyline'), [S('pts')] + [[S('xy'), *rot(x, y)] for x, y in pts], stroke(w), fill(f)]
        k = sym['kind']
        if k in ('R', 'F'):
            if k == 'R':
                body.append(poly([(-1.016, -G), (1.016, -G), (1.016, G), (-1.016, G), (-1.016, -G)]))
            else:
                body.append(poly([(-0.762, -G), (0.762, -G), (0.762, G), (-0.762, G), (-0.762, -G)]))
                body.append(poly([(0, -G), (0, G)], 0.1524))
        elif k in ('C', 'CP'):
            body.append(poly([(-2.032, 0.762), (2.032, 0.762)], 0.508))
            body.append(poly([(-2.032, -0.762), (2.032, -0.762)], 0.508, 'outline' if k == 'CP' else 'none'))
            if k == 'CP':
                body.append(poly([(-1.778, 2.286), (-0.762, 2.286)], 0.1524))
                body.append(poly([(-1.27, 2.794), (-1.27, 1.778)], 0.1524))
        elif k == 'LED':
            body.append(poly([(-1.27, 1.27), (1.27, 1.27), (0, -1.27), (-1.27, 1.27)], 0.254))
            body.append(poly([(-1.27, -1.27), (1.27, -1.27)], 0.254))
            body.append(poly([(1.778, 0.508), (3.048, -0.762)], 0.1524))
            body.append(poly([(1.778, -0.508), (3.048, -1.778)], 0.1524))
    pinlist = [S('symbol'), symname + '_1_1']
    for num, p in sorted(pins.items(), key=lambda kv: kv[0]):
        pinlist.append([S('pin'), S(p['type']), S('line'), [S('at'), p['x'], p['y'], p['ang']], [S('length'), p['length']],
                        [S('name'), p['name'], eff()], [S('number'), num, eff()]])
    hdr = [S('symbol'), name]
    if sym['kind'] == 'box':
        hdr.append([S('pin_names'), [S('offset'), 1.016]])
    else:
        hdr += [[S('pin_numbers'), S('hide')], [S('pin_names'), [S('offset'), 0], S('hide')]]
    hdr += [[S('in_bom'), S('yes')], [S('on_board'), S('yes')],
            [S('property'), 'Reference', sym['ref'], [S('at'), 0, 0, 0], eff()],
            [S('property'), 'Value', symname, [S('at'), 0, 0, 0], eff()],
            [S('property'), 'Footprint', sym['fp'], [S('at'), 0, 0, 0], eff(True)],
            [S('property'), 'Datasheet', '~', [S('at'), 0, 0, 0], eff(True)],
            body, pinlist]
    return hdr


_power = {}


def power_lib(name):
    if not _power:
        t = parse(open('/usr/share/kicad/symbols/power.kicad_sym').read())[0]
        _power.update({x[1]: x for x in find(t, 'symbol')})
    s = [S('symbol'), 'power:' + name] + [x for x in _power[name][2:]]
    return s


# ------------------------------------------------------------------ sheet building
nets_sheets = defaultdict(set)
for ref, (sym, val, sh, conn) in design.PARTS.items():
    for pin, net in conn.items():
        if net:
            nets_sheets[net].add(sh)


class Sheet:
    def __init__(self, key, title, desc, page):
        self.key, self.title, self.desc, self.page = key, title, desc, page
        self.uuid = U('sheet', key)
        self.lay = LAYOUT[key]
        self.W, self.H = PAPER[self.lay['paper']]
        self.items, self.libs = [], {}
        self.blocked = set()
        self.occ = defaultdict(dict)       # cell -> {net: 'H'|'V'|'N'}
        self.escape = {}
        self.terms = defaultdict(list)     # net -> [(cell, outward dir)]
        self.npwr = 0
        self.fallback = []
        self.gx0, self.gy0 = 4, 4
        self.gx1, self.gy1 = int(self.W / G) - 4, int(self.H / G) - 4
        # title block (bottom right)
        for x in range(int((self.W - 125) / G), self.gx1 + 2):
            for y in range(int((self.H - 45) / G), self.gy1 + 2):
                self.blocked.add((x, y))

    def place_parts(self):
        parts = {r: p for r, p in design.PARTS.items() if p[2] == self.key}
        pos = dict(self.lay['parts'])
        caps = [r for r in parts if r not in pos]
        x = 40
        for r in sorted(caps, key=lambda r: int(r[1:])):
            pos[r] = (x, CAP_ROW[self.key])
            x += 15.24
        for ref, (symname, value, sh, conn) in parts.items():
            pins, (x1, y1, x2, y2) = geom(symname)
            left, top = pos[ref]
            ox = round((left - x1) / G) * G
            oy = round((top + y2) / G) * G
            self.place(ref, symname, value, ox, oy, conn, pins, (x1, y1, x2, y2))

    def place(self, ref, symname, value, ox, oy, conn, pins, body):
        sym = SYMBOLS[symname]
        lib_id = 'isa8:' + symname
        if lib_id not in self.libs:
            self.libs[lib_id] = lib_symbol(symname)
        x1, y1, x2, y2 = body
        sx1, sx2, sy1, sy2 = ox + x1, ox + x2, oy - y2, oy - y1
        c1, c2 = math.floor(sx1 / G + 1e-6), math.ceil(sx2 / G - 1e-6)
        r1, r2 = math.floor(sy1 / G + 1e-6), math.ceil(sy2 / G - 1e-6)
        for cx in range(c1, c2 + 1):
            for cy in range(r1, r2 + 1):
                self.blocked.add((cx, cy))
        if sym['kind'] == 'box':
            ref_at, val_at, just = (sx1, sy1 - 1.27), (sx1, sy2 + 1.778), 'left'
            tl = max(len(ref), len(value)) * 1.15
            for cx in range(c1, max(c2, math.ceil((sx1 + tl) / G)) + 1):
                self.blocked.add((cx, r1 - 1))
                self.blocked.add((cx, r2 + 1))
        elif sym['horizontal']:
            ref_at, val_at, just = (ox, oy - 2.54), (ox, oy + 2.54), None
            for cx in range(c1 - 1, c2 + 2):
                self.blocked.add((cx, r1 - 1))
                self.blocked.add((cx, r2 + 1))
        else:
            ref_at, val_at, just = (ox + 2.54, oy - 1.27), (ox + 2.54, oy + 1.27), 'left'
            tl = max(len(ref), len(value)) * 1.15
            for cx in range(c2 + 1, math.ceil((ox + 2.54 + tl) / G) + 1):
                for cy in range(r1, r2 + 1):
                    self.blocked.add((cx, cy))
        e = [S('symbol'), [S('lib_id'), lib_id], [S('at'), ox, oy, 0], [S('unit'), 1],
             [S('in_bom'), S('yes')], [S('on_board'), S('yes')], [S('dnp'), S('no')], [S('uuid'), U('sym', ref)],
             [S('property'), 'Reference', ref, [S('at'), ref_at[0], ref_at[1], 0], eff(justify=just)],
             [S('property'), 'Value', value, [S('at'), val_at[0], val_at[1], 0], eff(justify=just)],
             [S('property'), 'Footprint', sym['fp'], [S('at'), ox, oy, 0], eff(True)],
             [S('property'), 'Datasheet', '~', [S('at'), ox, oy, 0], eff(True)]]
        for num in sorted(pins):
            e.append([S('pin'), num, [S('uuid'), U('pin', ref, num)]])
        e.append([S('instances'), [S('project'), PROJECT, [S('path'), '/%s/%s' % (ROOT, self.uuid), [S('reference'), ref], [S('unit'), 1]]]])
        self.items.append(e)
        for num, p in pins.items():
            ax, ay = round(ox + p['x'], 2), round(oy - p['y'], 2)
            cell = (round(ax / G), round(ay / G))
            out = (p['ang'] + 180) % 360
            net = conn[num]
            self.blocked.discard(cell)
            if net is None:
                self.items.append([S('no_connect'), [S('at'), ax, ay], [S('uuid'), U('nc', ref, num)]])
                self.blocked.add(cell)
            elif net in design.POWER:
                self.power(net, ax, ay, out, (ref, num))
                dx, dy = DIRV[out]
                for k in range(0, 3):
                    self.blocked.add((cell[0] + dx * k, cell[1] + dy * k))
            else:
                self.terms[net].append((cell, out, (ref, num)))
                self.occ[cell][net] = 'N'
                dx, dy = DIRV[out]
                for k in (1, 2):
                    self.escape.setdefault((cell[0] + dx * k, cell[1] + dy * k), (net, 'H' if dy == 0 else 'V'))

    def power(self, net, x, y, away, key, flag=False):
        self.npwr += 1
        lib_id = 'power:' + net
        if lib_id not in self.libs:
            self.libs[lib_id] = power_lib(net)
        base = 270 if net == 'GND' else 90
        rot = (base - away) % 360
        a = math.radians(away)
        d = 5 if net != 'GND' else -4
        vx, vy = round(x + 5 * math.cos(a), 2), round(y - 5 * math.sin(a), 2)
        ref = '#PWR%s%03d' % (self.key.upper(), self.npwr)
        self.items.append([S('symbol'), [S('lib_id'), lib_id], [S('at'), x, y, rot], [S('unit'), 1],
                           [S('in_bom'), S('no')], [S('on_board'), S('yes')], [S('dnp'), S('no')], [S('uuid'), U('pwr', self.key, *key)],
                           [S('property'), 'Reference', ref, [S('at'), x, y, 0], eff(True)],
                           [S('property'), 'Value', net, [S('at'), vx, vy, 0], eff()],
                           [S('property'), 'Footprint', '', [S('at'), x, y, 0], eff(True)],
                           [S('property'), 'Datasheet', '', [S('at'), x, y, 0], eff(True)],
                           [S('pin'), '1', [S('uuid'), U('pwrpin', self.key, *key)]],
                           [S('instances'), [S('project'), PROJECT, [S('path'), '/%s/%s' % (ROOT, self.uuid), [S('reference'), ref], [S('unit'), 1]]]]])

    def flag(self, net, x, y):
        lib_id = 'power:PWR_FLAG'
        if lib_id not in self.libs:
            self.libs[lib_id] = power_lib('PWR_FLAG')
        self.npwr += 1
        ref = '#FLG%s%02d' % (self.key.upper(), self.npwr)
        self.items.append([S('symbol'), [S('lib_id'), lib_id], [S('at'), x, y, 0], [S('unit'), 1],
                           [S('in_bom'), S('no')], [S('on_board'), S('yes')], [S('dnp'), S('no')], [S('uuid'), U('flag', net)],
                           [S('property'), 'Reference', ref, [S('at'), x, y, 0], eff(True)],
                           [S('property'), 'Value', 'PWR_FLAG', [S('at'), x, y - 3.81, 0], eff()],
                           [S('property'), 'Footprint', '', [S('at'), x, y, 0], eff(True)],
                           [S('property'), 'Datasheet', '~', [S('at'), x, y, 0], eff(True)],
                           [S('pin'), '1', [S('uuid'), U('flagpin', net)]],
                           [S('instances'), [S('project'), PROJECT, [S('path'), '/%s/%s' % (ROOT, self.uuid), [S('reference'), ref], [S('unit'), 1]]]]])
        self.power(net, x, y, 270 if net == 'GND' else 90, ('flag', net))

    def glabel(self, net, cell, away, key):
        x, y = cell[0] * G, cell[1] * G
        ang = {0: 0, 180: 180, 90: 90, 270: 270}[away]
        just = 'left' if away in (0, 90) else 'right'
        self.items.append([S('global_label'), net, [S('shape'), S('passive')], [S('at'), x, y, ang], [S('fields_autoplaced')],
                           eff(justify=just), [S('uuid'), U('gl', self.key, net, *key)],
                           [S('property'), 'Intersheetrefs', '${INTERSHEET_REFS}', [S('at'), x, y, 0], eff(True, just)]])
        n = math.ceil((label_len(net) * 1.15 + 4) / G)
        dx, dy = DIRV[away]
        for k in range(1, n + 1):
            self.blocked.add((cell[0] + dx * k, cell[1] + dy * k))

    # -------------------------------------------------------------- routing
    def prepare_nets(self):
        self.route_nets = []
        ports = []
        for net, terms in self.terms.items():
            cross = len(nets_sheets[net]) > 1
            if net in design.BUS_NETS:
                for cell, out, key in terms:
                    self.glabel(net, cell, out, key)
                continue
            if len(terms) == 1:
                cell, out, key = terms[0]
                self.glabel(net, cell, out, key)
                continue
            if cross:
                ys = [t[0][1] for t in terms]
                ports.append((sum(ys) / len(ys), net))
            self.route_nets.append(net)
        side = self.lay['ports']
        px = round(self.lay['port_x'] / G)
        out = 0 if side == 'R' else 180
        used = set()
        for want, net in sorted(ports):
            y = round(want)
            while y in used or (px, y) in self.blocked:
                y += 1
            used.add(y)
            cell = (px, y)
            self.terms[net].append((cell, (out + 180) % 360, ('port',)))
            self.occ[cell][net] = 'N'
            self.glabel(net, cell, out, ('port',))
            dx, dy = DIRV[out]
            for k in range(1, 3):
                self.escape.setdefault((cell[0] - dx * k, cell[1]), (net, 'H'))
        for y in range(self.gy0, self.gy1 + 1):
            for k in range(1, 40):
                c = (px + (k if side == 'R' else -k), y)
                self.blocked.add(c)

    def legal(self, net, cell):
        o = self.occ.get(cell)
        if not o:
            return True
        return net in o and len(o) == 1

    def search(self, net, start, tree, termdir, margin):
        (sx, sy), sout = start
        xs = [c[0] for c in tree] + [sx]
        ys = [c[1] for c in tree] + [sy]
        bx1, bx2 = max(self.gx0, min(xs) - margin), min(self.gx1, max(xs) + margin)
        by1, by2 = max(self.gy0, min(ys) - margin), min(self.gy1, max(ys) + margin)
        tx1, tx2, ty1, ty2 = min(xs[:-1]), max(xs[:-1]), min(ys[:-1]), max(ys[:-1])

        def h(x, y):
            return max(tx1 - x, 0, x - tx2) + max(ty1 - y, 0, y - ty2)
        startstate = (sx, sy, sout)
        best = {startstate: 0}
        prev = {}
        pq = [(h(sx, sy), 0, startstate, True)]
        while pq:
            f, g, st, first_step = heapq.heappop(pq)
            if best.get(st, 1e18) < g:
                continue
            x, y, d = st
            here = self.occ.get((x, y), {})
            esc = self.escape.get((x, y))
            crossing_here = ((bool(here) and net not in here) or (esc is not None and esc[0] != net)) and not first_step
            for nd in ((d,) if (first_step or crossing_here) else (0, 90, 180, 270)):
                if not first_step and nd == (d + 180) % 360:
                    continue
                dx, dy = DIRV[nd]
                nx, ny = x + dx, y + dy
                if not (bx1 <= nx <= bx2 and by1 <= ny <= by2):
                    continue
                c = (nx, ny)
                if c in self.blocked:
                    continue
                o = self.occ.get(c, {})
                other = {k: v for k, v in o.items() if k != net}
                horiz = nd in (0, 180)
                if net in o:
                    if other:
                        continue
                    if c in termdir and nd != (termdir[c] + 180) % 360:
                        continue
                    if c in termdir and o[net] == 'N' and c not in tree:
                        continue
                    ng = g + 1 + (3 if nd != d and not first_step else 0)
                    prev[(nx, ny, nd)] = st
                    return self.backtrack(prev, (nx, ny, nd), startstate)
                esc = self.escape.get(c)
                if esc and esc[0] != net and esc[1] == ('H' if horiz else 'V'):
                    continue
                if other:
                    if 'N' in other.values():
                        continue
                    if (horiz and 'H' in other.values()) or (not horiz and 'V' in other.values()):
                        continue
                    if len(other) > 1:
                        continue
                cost = 1 + (5 if nd != d and not first_step else 0) + (3 if other else 0) + self.near(net, nx, ny, horiz) + (3 if c in self.escape and self.escape[c][0] != net else 0)
                ns = (nx, ny, nd)
                ng = g + cost
                if ng < best.get(ns, 1e18):
                    best[ns] = ng
                    prev[ns] = st
                    heapq.heappush(pq, (ng + h(nx, ny), ng, ns, False))
        return None

    def near(self, net, x, y, horiz):
        # keep parallel wires of different nets one grid apart where possible
        k = 0
        for dx, dy in (((0, 1), (0, -1)) if horiz else ((1, 0), (-1, 0))):
            o = self.occ.get((x + dx, y + dy))
            if o and any(n != net and v == ('H' if horiz else 'V') for n, v in o.items()):
                k += 1
        return k

    def backtrack(self, prev, end, start):
        path = [end]
        while path[-1] != start:
            path.append(prev[path[-1]])
        return [(s[0], s[1]) for s in reversed(path)]

    def route(self):
        self.wires = defaultdict(list)
        self.edges = defaultdict(set)
        order = sorted(self.route_nets, key=lambda n: self.hpwl(n))
        for net in order:
            terms = self.terms[net]
            termdir = {t[0]: t[1] for t in terms}
            tree = {terms[0][0]}
            todo = terms[1:]
            while todo:
                todo.sort(key=lambda t: min(abs(t[0][0] - c[0]) + abs(t[0][1] - c[1]) for c in tree))
                t = todo.pop(0)
                path = None
                for margin in (12, 40, 400):
                    path = self.search(net, (t[0], t[1]), tree, termdir, margin)
                    if path:
                        break
                if not path:
                    self.fallback.append((net, t))
                    continue
                self.commit(net, path, tree)
        return order

    def hpwl(self, net):
        xs = [t[0][0] for t in self.terms[net]]
        ys = [t[0][1] for t in self.terms[net]]
        return (max(xs) - min(xs)) + (max(ys) - min(ys))

    def commit(self, net, path, tree):
        for i, c in enumerate(path):
            if i in (0, len(path) - 1):
                kind = 'N'
            else:
                a, b = path[i - 1], path[i + 1]
                if a[1] == b[1]:
                    kind = 'H'
                elif a[0] == b[0]:
                    kind = 'V'
                else:
                    kind = 'N'
            if i == len(path) - 1 and self.occ[c].get(net) in ('H', 'V'):
                kind = 'N'
            if self.occ[c].get(net) == 'N':
                kind = 'N'
            self.occ[c][net] = kind
            tree.add(c)
            if i:
                self.edges[net].add(frozenset((path[i - 1], c)))
        # merge straight runs into wire segments
        seg = [path[0]]
        for i in range(1, len(path)):
            if len(seg) >= 2 and (seg[-2][0] == seg[-1][0] == path[i][0] or seg[-2][1] == seg[-1][1] == path[i][1]):
                seg[-1] = path[i]
            else:
                seg.append(path[i])
        for a, b in zip(seg, seg[1:]):
            self.wires[net].append((a, b))

    def emit_wires(self):
        # Wires are rebuilt from the edge graph and split at every node, so each connection
        # (including T junctions) is an endpoint-to-endpoint connection.
        for net in self.wires:
            adj = defaultdict(set)
            for e in self.edges[net]:
                a, b = tuple(e)
                adj[a].add(b)
                adj[b].add(a)
            terms = {t[0] for t in self.terms[net]}

            def node(c):
                if c in terms or len(adj[c]) != 2:
                    return True
                a, b = adj[c]
                return not (a[0] == b[0] or a[1] == b[1])
            seen = set()
            i = 0
            for start in sorted(adj):
                if not node(start):
                    continue
                for nb in sorted(adj[start]):
                    if frozenset((start, nb)) in seen:
                        continue
                    prev, cur = start, nb
                    seen.add(frozenset((prev, cur)))
                    while not node(cur):
                        nxt = [c for c in adj[cur] if c != prev][0]
                        prev, cur = cur, nxt
                        seen.add(frozenset((prev, cur)))
                    self.items.append([S('wire'), [S('pts'), [S('xy'), start[0] * G, start[1] * G], [S('xy'), cur[0] * G, cur[1] * G]],
                                       [S('stroke'), [S('width'), 0], [S('type'), S('default')]], [S('uuid'), U('w', self.key, net, i)]])
                    i += 1
            for c in adj:
                k = len(adj[c]) + (1 if c in terms else 0)
                if k >= 3:
                    self.items.append([S('junction'), [S('at'), c[0] * G, c[1] * G], [S('diameter'), 0], [S('color'), 0, 0, 0, 0],
                                       [S('uuid'), U('j', self.key, net, c)]])
        for net, t in self.fallback:
            cell, out, key = t
            self.items.append([S('label'), net, [S('at'), cell[0] * G, cell[1] * G, out], eff(justify='left' if out in (0, 90) else 'right'),
                               [S('uuid'), U('fl', self.key, net, *key)]])
            src = self.terms[net][0]
            self.items.append([S('label'), net, [S('at'), src[0][0] * G, src[0][1] * G, src[1]],
                               eff(justify='left' if src[1] in (0, 90) else 'right'), [S('uuid'), U('fl2', self.key, net, *key)]])

    def write(self, path, flags=()):
        x = 60
        for net in flags:
            self.flag(net, x, 25.4)
            x += 15.24
        tb = [S('title_block'), [S('title'), 'isa8_multi_io - ' + self.title], [S('date'), '2026-10-17'], [S('rev'), '0.1'],
              [S('company'), 'Stefan Fambach - fambach.net'],
              [S('comment'), 1, self.desc],
              [S('comment'), 2, 'Hardware license CERN-OHL-S-2.0. Floppy section based on Monster FDC by Sergey Kiselev (CERN-OHL-S-2.0).'],
              [S('comment'), 3, 'Generated by hardware/generator - not built or tested yet.']]
        sch = [S('kicad_sch'), [S('version'), 20230121], [S('generator'), S('eeschema')], [S('uuid'), self.uuid],
               [S('paper'), self.lay['paper']], tb, [S('lib_symbols')] + list(self.libs.values())] + self.items
        open(path, 'w').write(dump(sch) + '\n')


def root(sheets):
    items = []
    for i, sh in enumerate(sheets):
        x, y = 30 + (i % 2) * 120, 50 + (i // 2) * 50
        items.append([S('sheet'), [S('at'), x, y], [S('size'), 90, 25], [S('fields_autoplaced')],
                      [S('stroke'), [S('width'), 0.1524], [S('type'), S('solid')]], [S('fill'), [S('color'), 0, 0, 0, 0.0]],
                      [S('uuid'), sh.uuid],
                      [S('property'), 'Sheetname', sh.title, [S('at'), x, y - 0.7, 0], eff(justify='left bottom')],
                      [S('property'), 'Sheetfile', sh.key + '.kicad_sch', [S('at'), x, y + 25.6, 0], eff(justify='left top')],
                      [S('instances'), [S('project'), PROJECT, [S('path'), '/' + ROOT, [S('page'), str(sh.page)]]]]])
    note = ('8-bit ISA multi I/O card: floppy (82077AA), XT-IDE compatible IDE, 16C550 serial, bidirectional parallel, 28C256 option ROM.\n'
            'Glue logic in three ATF22V10C GALs (sources in gal/). Every block can be left unpopulated and switched off by DIP switch.\n'
            'DIP switches: ON = 1. Jumpers select IRQ, DMA and power. Nets shared between sheets are global labels.')
    items.append([S('text'), note, [S('at'), 30, 165, 0], eff(justify='left'), [S('uuid'), U('note')]])
    tb = [S('title_block'), [S('title'), 'isa8_multi_io - 8-bit ISA multi I/O card'], [S('date'), '2026-10-17'], [S('rev'), '0.1'],
          [S('company'), 'Stefan Fambach - fambach.net'], [S('comment'), 1, 'Hardware license CERN-OHL-S-2.0'],
          [S('comment'), 2, 'Floppy section based on Monster FDC by Sergey Kiselev (CERN-OHL-S-2.0)'],
          [S('comment'), 3, 'Generated by hardware/generator - not built or tested yet.']]
    sch = [S('kicad_sch'), [S('version'), 20230121], [S('generator'), S('eeschema')], [S('uuid'), ROOT], [S('paper'), 'A4'], tb,
           [S('lib_symbols')]] + items + [[S('sheet_instances'), [S('path'), '/', [S('page'), '1']]]]
    open(os.path.join(OUT, PROJECT + '.kicad_sch'), 'w').write(dump(sch) + '\n')


def main():
    os.makedirs(OUT, exist_ok=True)
    sheets = []
    report = {}
    for i, (key, title, desc) in enumerate(design.SHEETS):
        sh = Sheet(key, title, desc, i + 2)
        sh.place_parts()
        sh.prepare_nets()
        sh.route()
        sh.emit_wires()
        sh.write(os.path.join(OUT, key + '.kicad_sch'), flags=('+5V', 'GND', '+12V', '-12V') if key == 'bus' else ())
        report[key] = dict(routed=len(sh.route_nets), fallback=[f[0] for f in sh.fallback])
        print(key, 'nets routed', len(sh.route_nets), 'fallback labels', len(sh.fallback), [f[0] for f in sh.fallback][:20])
        sheets.append(sh)
    root(sheets)
    # project library for KiCad users who open the files
    lib = [S('kicad_symbol_lib'), [S('version'), 20220914], [S('generator'), S('kicad_symbol_editor')]]
    for name in sorted(SYMBOLS):
        sym = lib_symbol(name)
        sym[1] = name
        lib.append(sym)
    open(os.path.join(OUT, 'isa8.kicad_sym'), 'w').write(dump(lib) + '\n')
    open(os.path.join(OUT, 'sym-lib-table'), 'w').write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "isa8")(type "KiCad")(uri "${KIPRJMOD}/isa8.kicad_sym")(options "")(descr "isa8_multi_io symbols"))\n)\n')


main()
