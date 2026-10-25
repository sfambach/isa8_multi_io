# isa8_multi_io – Design

Status: schematic drawn ([PDF](../hardware/kicad/isa8_multi_io-schematic.pdf)), no PCB yet. Nothing here has been built or tested.

## Goals

- One 8-bit ISA card (also works in 16-bit slots): floppy, IDE, serial, parallel, option ROM.
- Every function block can be left unpopulated and switched off.
- Through-hole parts only (FDC and UART are PLCC in through-hole sockets).
- Affordable: about 40–60 EUR fully populated, 15–20 EUR for IDE + ROM only.

## Blocks

| Block | Parts | Settings |
|---|---|---|
| Bus buffer | 74HCT245, GAL `busctl` | – |
| IDE (XT-IDE compatible) | GAL `ide`, 2× 74HCT574 (high byte write/read latch) | DIP: enable, base 300h/320h; jumpers: high-speed mode (A0/A3 swap) |
| IDE connector | 40-pin 2.54 mm **or** 44-pin 2.0 mm (both footprints, wired in parallel) | jumper: 44-pin +5 V from ISA (via PTC 0.75 A) or from Berg power connector |
| Floppy | Intel 82077AA / NS PC8477BV-1 (PLCC-68), 24 MHz crystal – circuit after Monster FDC | DIP: enable, 3F0h/370h; jumpers: DMA 2/3, IRQ 6/off, +5 V on pin 3 (PS/2 drives) |
| Option ROM | 28C256 (32 KiB): XT-IDE Universal BIOS + Multi-Floppy BIOS | DIP: enable, base C8000h/D0000h/D8000h/E0000h, write enable |
| Serial | 16C550 (PLCC-44), SN75C185, 1.8432 MHz oscillator, DE9 | DIP: enable, COM1–COM4; jumper: IRQ 3/4/5/7 |
| Parallel | 74HCT374, 3× 74HCT244, 74HCT174, 7406, 74HCT138, DB25 – bidirectional (PS/2 mode) | DIP: off/378h/278h/3BCh; jumper: IRQ 7/5/off |
| Misc | 74HCT04, 74HCT125 (IRQ drivers gated by UART OUT2 and LPT IRQ enable) | – |

Rule: DIP switches select addresses and enable blocks, jumpers select IRQ, DMA and power.

## Address decoding (GALs, ATF22V10C)

Sources and JEDEC files in [`../gal`](../gal). Assembled with GALasm 2.1 ([daveho/GALasm](https://github.com/daveho/GALasm), CRLF JEDEC output). The equations are checked against the address map by [`../tests/check_gal.py`](../tests/check_gal.py); the GALs have not been tested in hardware yet. How they work: [gal-explained.md](gal-explained.md). How to assemble and program: [gal-programming.md](gal-programming.md).

| GAL | Inputs | Outputs |
|---|---|---|
| `ide.pld` | A0–A9, AEN, IOR, IOW, IS, IDEEN | CS0, CS1, DIOR, DIOW, HWR, HRDOE, IDESEL |
| `iobase.pld` | A2–A9, AEN, FDCEN, FS, UARTEN, US0/1, LS0/1 | FDCCS, UARTCS, LPTSEL |
| `busctl.pld` | A15–A19, ROMEN, RS0/1, IDESEL, FDCCS, UARTCS, LPTSEL, DACK, IOR, IOW, MEMR, MEMW | ROMCE, BUFEN, BUFDIR, LPTSTB |

The bus buffer only drives ISA D0–D7 in read cycles that belong to this card
(I/O read of a selected block, FDC DMA with DACK + IOR, or a memory read of the ROM).

## Key decisions

- No open-source card combined floppy and IDE on one 8-bit board, so this is a new design.
- Through-hole only, addresses by DIP switch, IRQ/DMA/power by jumper, affordable.
- No Super-I/O chip (SMD only) and no FPGA (maybe a later version); glue logic in three GALs instead of 74688/74138 decoders.
- Floppy section after Monster FDC; the IDE part is redrawn (XT-IDE is GPL-3 and cannot be mixed into a CERN-OHL-S design).
- No game port (usually on the sound card).
- 44-pin IDE power from ISA only for SSD/DOM/CF; real 2.5" disks need the Berg connector.

## Settings

DIP switches: ON = 1.

| Switch | Function | OFF | ON |
|---|---|---|---|
| SW1-1 | IDE | disabled | enabled |
| SW1-2 | IDE base | 300h | 320h |
| SW1-3 | ROM | disabled | enabled |
| SW1-4/5 | ROM base (S0/S1) | see below | |
| SW1-6 | ROM write | protected | allowed |
| SW1-7 | Floppy | disabled | enabled |
| SW1-8 | Floppy base | 3F0h | 370h |
| SW2-1 | Serial | disabled | enabled |
| SW2-2/3 | Serial base (S0/S1) | see below | |
| SW2-4/5 | Parallel base (S0/S1) | see below | |

| S1 S0 | ROM | Serial | Parallel |
|---|---|---|---|
| 0 0 | C8000h | 3F8h | off |
| 0 1 | D0000h | 2F8h | 378h |
| 1 0 | D8000h | 3E8h | 278h |
| 1 1 | E0000h | 2E8h | 3BCh |

| Jumper | Function | Setting |
|---|---|---|
| JP1 + JP2 | IDE high-speed (A0/A3 swap) | both 1-2 standard, both 2-3 high-speed |
| JP3 | 44-pin IDE power | 1-2 ISA (via PTC), 2-3 Berg |
| JP4 | +5 V on floppy pin 3 | fitted = on |
| JP5 + JP6 | Floppy DMA | both 1-2 DMA 2, both 2-3 DMA 3 |
| JP7 | Floppy IRQ 6 | fitted = on |
| JP8 | Serial IRQ | one jumper: IRQ 3/4/5/7 |
| JP9 | Parallel IRQ | 1-2 IRQ 7, 2-3 IRQ 5, open = off |

## Open points

- Check whether FDC CS must skip 3F6h/376h (IDE alternate status on AT machines).
- PCB: board outline, footprints for ISA edge and Berg connector, ISA bracket (DE9 + DB25, 3D-printed) with 2D dimension drawing.
- Optional module header for a second IDE channel (isa8_ssd_controller), not decided.
- Test the programmed GALs in a real XT and AT.

## Basis and references

- Floppy part: [Monster FDC](https://github.com/skiselev/monster-fdc) by Sergey Kiselev (CERN-OHL-S-2.0).
- IDE register map: [XT-IDE](https://github.com/glitchwrks/xt_ide) and [XT-IDE Universal BIOS](https://www.xtideuniversalbios.org/); the IDE circuit is redrawn, no XT-IDE design files are copied.
- Parallel port: IBM PC parallel adapter standard circuit.
