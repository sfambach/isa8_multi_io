# Hardware

- [`kicad/`](kicad) – KiCad 7 schematic (root sheet + 4 sheets: bus/decoder, IDE, floppy/ROM, serial/parallel) and [PDF](kicad/isa8_multi_io-schematic.pdf).
- [`generator/`](generator) – the schematic is generated from [`design.py`](generator/design.py) (netlist) and [`layout.py`](generator/layout.py) (placement). Run `sh generator/build.sh` (needs KiCad 7 `kicad-cli`).

The generator routes wires on a 2.54 mm grid; wires of different nets only cross at right angles. Data/address bus and bus strobes (D0–D7, A0–A19, IOR, IOW, MEMR, MEMW, AEN, RESET) are drawn as labels at every pin, as in most ISA card schematics. `verify.py` exports the netlist with KiCad and checks that every net has exactly the intended pins.

Status: schematic only, no PCB yet. Not built or tested. Footprints for the ISA edge and the Berg power connector (`isa8_multi_io:` library) are still to be drawn.
