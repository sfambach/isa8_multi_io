# Compares the netlist exported by KiCad with design.py: every intended net must appear as exactly
# one KiCad net with exactly the same pins, and not-connected pins must stay alone.
import sys
from collections import defaultdict
from sexpr import parse, find, first
import design

t = parse(open(sys.argv[1]).read())[0]
got = {}
for net in find(first(t, 'nets'), 'net'):
    name = first(net, 'name')[1]
    nodes = frozenset((first(nd, 'ref')[1], first(nd, 'pin')[1]) for nd in find(net, 'node'))
    got[nodes] = name
want = defaultdict(set)
nc = set()
for ref, (sym, value, sheet, conn) in design.PARTS.items():
    for pin, net in conn.items():
        if net:
            want[net].add((ref, pin))
        else:
            nc.add((ref, pin))
errors = 0
pin_net = {}
for nodes, name in got.items():
    for nd in nodes:
        pin_net[nd] = name
for net, pins in want.items():
    if frozenset(pins) not in got:
        errors += 1
        names = defaultdict(list)
        for p in pins:
            names[pin_net.get(p)].append(p)
        print('MISMATCH', net, dict(names))
for p in nc:
    name = pin_net.get(p)
    if name and not name.startswith('unconnected-'):
        nodes = [n for n, v in got.items() if p in n][0]
        if len(nodes) > 1:
            errors += 1
            print('NC pin connected', p, name)
print('nets wanted', len(want), 'kicad nets', len(got), 'errors', errors)
sys.exit(1 if errors else 0)
