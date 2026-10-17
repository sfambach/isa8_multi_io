# Pin and body geometry of the generated symbols (symbol coordinates, y up, mm).
import math
from symbols import SYMBOLS, TYPES, G


def half_width(sym):
    return math.ceil(sym['width'] / 2 / G - 1e-9) * G


def box(sym):
    hw = half_width(sym)
    rows = max(len(sym['L']), len(sym['R']))
    y0 = G * ((rows - 1) // 2)
    pins = {}
    for side, x, ang in (('L', -hw - G, 0), ('R', hw + G, 180)):
        for i, p in enumerate(sym[side]):
            if p:
                num, name, t = p
                pins[num] = dict(x=x, y=y0 - G * i, ang=ang, name=name, type=TYPES[t], length=G)
    body = (-hw, y0 - G * rows, hw, y0 + G)
    return pins, body


def passive(sym):
    k, hz = sym['kind'], sym['horizontal']
    plen = {'R': G, 'F': G, 'C': 4.318, 'CP': 4.318, 'LED': 3.81}[k]
    if k == 'LED':
        pins = {'2': dict(x=0, y=2 * G, ang=270), '1': dict(x=0, y=-2 * G, ang=90)}
    else:
        pins = {'1': dict(x=0, y=2 * G, ang=270), '2': dict(x=0, y=-2 * G, ang=90)}
    for num, p in pins.items():
        p.update(name=num, type='passive', length=plen)
    body = (-1.27, -G, 1.27, G)
    if hz:
        for p in pins.values():
            p['x'], p['y'], p['ang'] = -p['y'], p['x'], (p['ang'] + 90) % 360
        body = (-G, -1.27, G, 1.27)
    return pins, body


def geom(symname):
    sym = SYMBOLS[symname]
    return box(sym) if sym['kind'] == 'box' else passive(sym)
