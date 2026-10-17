# How the GALs work

The card needs a lot of small glue logic: "is this I/O address mine?", "which chip is meant?", "which way does the data bus buffer drive?". On classic cards this is done with comparators (74688) and decoders (74138). Here three ATF22V10C GALs do that job.

## What a GAL is

A GAL (Generic Array Logic) is a small programmable logic chip. Inside there is an AND array followed by OR gates: every output is a **sum of products** – one or more AND terms, ORed together.

```mermaid
flowchart LR
  IN[Inputs<br/>address lines,<br/>IOR/IOW, DIP switches] --> AND[AND array<br/>programmable]
  AND --> OR[OR per output]
  OR --> OUT[Outputs<br/>chip selects,<br/>buffer control]
```

The `.pld` files in [`../gal`](../gal) describe these terms as text. GALasm turns them into a `.jed` fuse map; the programmer (XGecu T48) burns it into the chip. The chip can be erased and reprogrammed, so a wrong equation costs a reprogram, not a new board.

## Reading an equation

```
/FDCCS = A9 * A8 * A7 * A6 * A5 * A4 * /A3 * /AEN * FDCEN * /FS
       + ...
```

- `*` = AND, `+` = OR, `/` = signal is low (inverted).
- `/FDCCS` on the left: the output pin goes **low** when the right side is true (the ISA chip selects are active low).
- This line reads: address bits 9–4 are all 1, A3 is 0, AEN is 0 (no DMA cycle), the floppy block is switched on and the FS switch selects the primary address. That is exactly the range **3F0h–3F7h**.

Every term can only AND the inputs together, and a 22V10 output has room for 8 to 16 terms, depending on the pin. That limit is why the logic is split into three chips.

## The three GALs

```mermaid
flowchart LR
  ISA[ISA bus<br/>A0-A19, AEN,<br/>IOR, IOW, MEMR, MEMW] --> IDE[GAL ide]
  ISA --> IOB[GAL iobase]
  ISA --> BC[GAL busctl]
  DIP[DIP switches] --> IDE
  DIP --> IOB
  DIP --> BC
  IDE -->|CS0, CS1, DIOR, DIOW,<br/>latch control| HDD[IDE connector<br/>+ 2x 74HCT574]
  IOB -->|chip selects| CHIPS[FDC, UART, LPT]
  IDE -->|IDESEL| BC
  IOB -->|FDCCS, UARTCS, LPTSEL| BC
  BC -->|ROMCE| ROM[28C256]
  BC -->|BUFEN, BUFDIR| BUF[74HCT245<br/>data bus buffer]
  BC -->|LPTSTB| LPT138[74HCT138<br/>LPT registers]
```

| GAL | Job | Outputs |
|---|---|---|
| `ide` | XT-IDE register map at 300h or 320h | IDE chip selects CS0/CS1, read/write strobes DIOR/DIOW, high-byte latch control HWR/HRDOE, IDESEL |
| `iobase` | Base addresses of the other I/O blocks | FDC 3F0h/370h, UART COM1–COM4, LPT 378h/278h/3BCh or off |
| `busctl` | Memory and bus control | ROM select (C8000h/D0000h/D8000h/E0000h), data bus buffer enable and direction, LPT strobe |

### `ide` – XT-IDE register map

An IDE drive has a 16-bit data register, but the 8-bit ISA bus only carries 8 bits. The XT-IDE trick: the low byte goes directly to the drive, the high byte goes through a latch at base+8.

- **Read:** the CPU reads base+0. The drive delivers 16 bits; the low byte goes to the CPU, the high byte is caught in a 74HCT574 (clocked by DIOR). Then the CPU reads base+8 and gets the high byte from that latch (HRDOE).
- **Write:** the CPU first writes the high byte to base+8 (HWR clocks it into the second 574), then the low byte to base+0. DIOW then puts both halves on the drive at once.
- base+E/F are the drive's CS1 registers (alternate status, device control).

The high-speed jumpers swap A0 and A3 in front of the GAL, so data and latch sit at base+0 and base+1. The 8088 can then read both bytes with a single word instruction. The equations stay the same.

### `iobase` – where the other blocks live

Only address decoding: the GAL compares A2–A9 with the DIP switch setting and pulls the chip select of the FDC, UART or parallel port low. IOR/IOW go to those chips directly. Every term contains `/AEN`, so DMA cycles never select anything.

### `busctl` – ROM and data bus

- **ROMCE** selects the 28C256 in a 32 KiB window chosen with RS0/RS1.
- **BUFEN** opens the 74HCT245 only when a cycle belongs to this card: an I/O access to one of its blocks, an FDC DMA cycle (DACK) or a ROM access. Otherwise the card stays off the ISA data bus, so it cannot collide with other cards.
- **BUFDIR** sets the direction: low during read cycles (card → ISA), high during writes.
- **LPTSTB** enables the 74HCT138, which splits the parallel port's four registers by A0, A1 and read/write.

## Check before burning

[`../tests/check_gal.py`](../tests/check_gal.py) reads the equations and steps through every relevant address. It checks that each block answers in exactly its range, that nothing answers during DMA (AEN), and that the buffer only drives on this card's own read cycles. How to build and burn: [gal-programming.md](gal-programming.md).

Status: the equations pass this check; the GALs have not been tested in hardware yet.
