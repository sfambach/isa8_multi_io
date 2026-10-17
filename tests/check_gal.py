"""Evaluates the galasm equations in ../gal and checks the address map."""
import re
import sys
from pathlib import Path

GAL_DIR = Path(__file__).resolve().parent.parent / "gal"


def load(name):
    text = (GAL_DIR / name).read_text().split("DESCRIPTION")[0]
    equations = {}
    for lhs, rhs in re.findall(r"^/(\w+)\s*=\s*(.*?)(?=^\s*/\w+\s*=|\Z)", text, re.S | re.M):
        terms = [[t.strip() for t in term.split("*")] for term in rhs.replace("\n", " ").split("+")]
        equations[lhs] = terms
    return equations


def active(equations, name, signals):
    """True when the active-low output /name is asserted."""
    for term in equations[name]:
        if all((not signals[t[1:]]) if t.startswith("/") else signals[t] for t in term):
            return True
    return False


def bits(value, prefix, lo, hi):
    return {f"{prefix}{i}": bool(value >> i & 1) for i in range(lo, hi + 1)}


def fail(msg):
    print("FAIL:", msg)
    sys.exit(1)


ide, iobase, busctl = load("ide.pld"), load("iobase.pld"), load("busctl.pld")

# IDE: 16-byte window at 300h / 320h
for is_bit, base in ((0, 0x300), (1, 0x320)):
    for addr in range(0x400):
        s = bits(addr, "A", 0, 9) | {"AEN": False, "IOR": False, "IOW": True, "IS": bool(is_bit), "IDEEN": True}
        sel = active(ide, "IDESEL", s)
        if sel != (base <= addr < base + 16):
            fail(f"IDESEL {addr:03X} IS={is_bit}")
        off = addr - base
        if sel:
            if active(ide, "CS0", s) != (off < 8):
                fail(f"CS0 {addr:03X}")
            if active(ide, "CS1", s) != (off >= 14):
                fail(f"CS1 {addr:03X}")
            if active(ide, "DIOR", s) != (off < 8 or off >= 14):
                fail(f"DIOR {addr:03X}")
            if active(ide, "HRDOE", s) != (off == 8):
                fail(f"HRDOE {addr:03X}")
            if active(ide, "DIOW", s) or active(ide, "HWR", s):
                fail(f"write strobe on read {addr:03X}")
        s["IDEEN"] = False
        if active(ide, "IDESEL", s):
            fail("IDEEN=0 still selects")

# I/O base decoder
fdc = {0: 0x3F0, 1: 0x370}
uart = {(0, 0): 0x3F8, (0, 1): 0x2F8, (1, 0): 0x3E8, (1, 1): 0x2E8}
lpt = {(0, 1): 0x378, (1, 0): 0x278, (1, 1): 0x3BC}
for fs in (0, 1):
    for us, ubase in uart.items():
        for ls in ((0, 0), (0, 1), (1, 0), (1, 1)):
            for addr in range(0x400):
                s = bits(addr, "A", 2, 9) | {"AEN": False, "FDCEN": True, "FS": bool(fs), "UARTEN": True,
                                             "US1": bool(us[0]), "US0": bool(us[1]),
                                             "LS1": bool(ls[0]), "LS0": bool(ls[1])}
                if active(iobase, "FDCCS", s) != (fdc[fs] <= addr < fdc[fs] + 8):
                    fail(f"FDCCS {addr:03X}")
                if active(iobase, "UARTCS", s) != (ubase <= addr < ubase + 8):
                    fail(f"UARTCS {addr:03X}")
                lbase = lpt.get(ls)
                if active(iobase, "LPTSEL", s) != (lbase is not None and lbase <= addr < lbase + 4):
                    fail(f"LPTSEL {addr:03X} LS={ls}")
                s["AEN"] = True
                if any(active(iobase, o, s) for o in ("FDCCS", "UARTCS", "LPTSEL")):
                    fail("select during DMA (AEN=1)")

# ROM select
rom = {(0, 0): 0xC8000, (0, 1): 0xD0000, (1, 0): 0xD8000, (1, 1): 0xE0000}
idle = {"IDESEL": True, "FDCCS": True, "UARTCS": True, "LPTSEL": True, "DACK": True,
        "IOR": True, "IOW": True, "MEMR": True, "MEMW": True}
for rs, rbase in rom.items():
    for block in range(32):
        addr = block << 15
        s = bits(addr, "A", 15, 19) | idle | {"ROMEN": True, "RS1": bool(rs[0]), "RS0": bool(rs[1])}
        hit = active(busctl, "ROMCE", s)
        if hit != (addr == rbase):
            fail(f"ROMCE {addr:05X}")
        s["ROMCE"] = not hit
        s["MEMR"] = False
        if active(busctl, "BUFDIR", s) != hit or active(busctl, "BUFEN", s) != hit:
            fail(f"buffer on ROM read {addr:05X}")

# Buffer must stay off when nothing on the card is selected
s = bits(0, "A", 15, 19) | idle | {"ROMEN": True, "RS1": False, "RS0": False, "ROMCE": True, "IOR": False}
if active(busctl, "BUFEN", s) or active(busctl, "BUFDIR", s):
    fail("buffer drives bus without select")
s["DACK"] = False
if not (active(busctl, "BUFEN", s) and active(busctl, "BUFDIR", s)):
    fail("FDC DMA read does not drive bus")
s.update({"DACK": True, "LPTSEL": False, "IOR": True, "IOW": False})
if not active(busctl, "LPTSTB", s) or active(busctl, "BUFDIR", s):
    fail("LPT write")

print("OK: all GAL address map checks passed")
