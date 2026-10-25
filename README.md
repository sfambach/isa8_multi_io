# isa8_multi_io

8-bit ISA multi I/O card for XT and AT class PCs: floppy controller, XT-IDE compatible IDE, serial port, bidirectional parallel port and an option ROM. Every block is optional – populate only what you need.

**Status: design phase.** Nothing has been built or tested yet.

## Features (planned)

- Floppy: 82077AA / PC8477BV-1, two drives, 360 KB to 2.88 MB, 3F0h or 370h
- IDE: XT-IDE compatible (XT-IDE Universal BIOS), 40-pin or 44-pin connector, high-speed mode
- Serial: 16C550, COM1–COM4, DE9
- Parallel: bidirectional, 378h / 278h / 3BCh, DB25
- Option ROM: 28C256 for XT-IDE Universal BIOS and Multi-Floppy BIOS
- Addresses by DIP switch, IRQ/DMA by jumper, through-hole parts, glue logic in three ATF22V10C GALs

Details: [docs/design.md](docs/design.md) · How the GAL glue logic works: [docs/gal-explained.md](docs/gal-explained.md)

## License

- Hardware: [CERN-OHL-S-2.0](LICENSE)
- GAL sources: CERN-OHL-S-2.0
- Documentation: CC BY-SA 4.0
- Firmware used: XT-IDE Universal BIOS (GPL-2), Multi-Floppy BIOS by Sergey Kiselev (GPL-3) – not included here

The floppy section is based on the [Monster FDC](https://github.com/skiselev/monster-fdc) by Sergey Kiselev (CERN-OHL-S-2.0).

## Authors

- **Stefan Fambach** (SteFam) – idea and concept, review and testing – https://www.fambach.net
- **Claude** (Anthropic AI) – implementation, via Claude Code

## AI disclosure

This project is built with AI assistance. Stefan Fambach had the idea, wrote the concept and reviews and tests every change; the implementation (schematics, PCB and logic design files, firmware and documentation) is written largely by Claude (Anthropic) via Claude Code.
