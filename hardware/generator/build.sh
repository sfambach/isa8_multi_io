#!/bin/sh
# Regenerates the KiCad schematic, checks it against design.py and plots the PDF.
set -e
cd "$(dirname "$0")"
OUT=../kicad
python3 mksch.py $OUT
kicad-cli sch export netlist -o /tmp/isa8_multi_io.net $OUT/isa8_multi_io.kicad_sch >/dev/null
python3 verify.py /tmp/isa8_multi_io.net
kicad-cli sch export pdf -o $OUT/isa8_multi_io-schematic.pdf $OUT/isa8_multi_io.kicad_sch >/dev/null
