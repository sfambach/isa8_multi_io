# Netlist of the isa8_multi_io card. One entry per part:
#   ref: (symbol, value, sheet, {pin number: net})   net None = not connected
# Net names use KiCad overbar notation ~{...} for active-low signals.
# The floppy section follows the Monster FDC (Sergey Kiselev, CERN-OHL-S-2.0).
NC = None
POWER = {'+5V', 'GND', '+12V', '-12V'}


def n(s):
    return '~{%s}' % s


IOR, IOW, MEMR, MEMW = n('IOR'), n('IOW'), n('MEMR'), n('MEMW')
D = ['D%d' % i for i in range(8)]
A = ['A%d' % i for i in range(20)]
# Bus-like nets are drawn as labels at every pin (as in the Monster FDC schematic); all others are wired.
BUS_NETS = set(D + A + [IOR, IOW, MEMR, MEMW, 'AEN', 'RESET', n('RESET')])

SHEETS = [
    ('bus', 'Bus and decoder', 'ISA edge, data bus buffer, three GALs, DIP switches'),
    ('ide', 'IDE', 'XT-IDE compatible register map, 40-pin and 44-pin connector, power for 44-pin'),
    ('fdc', 'Floppy and ROM', 'Floppy controller after Monster FDC, option ROM 28C256'),
    ('io', 'Serial and parallel', '16C550 serial port, bidirectional parallel port'),
]

PARTS = {}


def part(ref, sym, value, sheet, conn):
    assert ref not in PARTS, ref
    PARTS[ref] = (sym, value, sheet, conn)


# ---------------------------------------------------------------- bus
isa = {}
isa['A1'] = NC
for i in range(8):
    isa['A%d' % (9 - i)] = 'SD%d' % i
isa['A10'] = NC
isa['A11'] = 'AEN'
for i in range(20):
    isa['A%d' % (31 - i)] = A[i]
isa.update({'B1': 'GND', 'B2': 'RESET', 'B3': '+5V', 'B4': NC, 'B5': NC, 'B6': 'DRQ2', 'B7': '-12V', 'B8': NC, 'B9': '+12V',
            'B10': 'GND', 'B11': MEMW, 'B12': MEMR, 'B13': IOW, 'B14': IOR, 'B15': n('DACK3'), 'B16': 'DRQ3', 'B17': NC,
            'B18': NC, 'B19': NC, 'B20': NC, 'B21': 'IRQ7', 'B22': 'IRQ6', 'B23': 'IRQ5', 'B24': 'IRQ4', 'B25': 'IRQ3',
            'B26': n('DACK2'), 'B27': 'TC', 'B28': NC, 'B29': '+5V', 'B30': NC, 'B31': 'GND'})
part('J1', 'ISA_8bit', 'ISA 8-bit', 'bus', isa)

c = {str(2 + i): 'SD%d' % i for i in range(8)}
c.update({str(18 - i): D[i] for i in range(8)})
c.update({'1': n('BUFDIR'), '19': n('BUFEN'), '20': '+5V', '10': 'GND'})
part('U1', '74HCT245', '74HCT245', 'bus', c)

ide_gal = ['IA0', 'A1', 'A2', 'IA3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'AEN', 'GND',
           IOR, IOW, 'IDE_IS', 'IDE_EN', n('IDE_CS0'), n('IDE_CS1'), n('DIOR'), n('DIOW'), n('HWR'), n('HRDOE'), n('IDESEL'), '+5V']
iob_gal = ['A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'AEN', 'FDC_EN', 'FDC_SEC', 'GND',
           'UART_EN', 'UART_S0', 'UART_S1', 'LPT_S0', 'LPT_S1', NC, NC, NC, n('FDCCS'), n('UARTCS'), n('LPTSEL'), '+5V']
bus_gal = ['A15', 'A16', 'A17', 'A18', 'A19', 'ROM_EN', 'ROM_S0', 'ROM_S1', n('IDESEL'), n('FDCCS'), n('UARTCS'), 'GND',
           n('LPTSEL'), n('FDC_DACK'), IOR, IOW, MEMR, MEMW, n('ROMCE'), n('BUFEN'), n('BUFDIR'), n('LPTSTB'), NC, '+5V']
part('U2', 'GAL22V10', 'ATF22V10C "IDE"', 'bus', {str(i + 1): v for i, v in enumerate(ide_gal)})
part('U3', 'GAL22V10', 'ATF22V10C "IOBASE"', 'bus', {str(i + 1): v for i, v in enumerate(iob_gal)})
part('U4', 'GAL22V10', 'ATF22V10C "BUSCTL"', 'bus', {str(i + 1): v for i, v in enumerate(bus_gal)})

# DIP switches: ON = 1 (switch to +5V, 10k pull-down). SW1 switch 6 is the ROM write enable.
sw1 = ['IDE_EN', 'IDE_IS', 'ROM_EN', 'ROM_S0', 'ROM_S1', None, 'FDC_EN', 'FDC_SEC']
c = {}
for i, net in enumerate(sw1, 1):
    c[str(i)] = '+5V' if net else MEMW
    c[str(17 - i)] = net or n('ROMWE')
part('SW1', 'SW_DIP_8', 'IDE/ROM/FDC', 'bus', c)
sw2 = ['UART_EN', 'UART_S0', 'UART_S1', 'LPT_S0', 'LPT_S1', NC, NC, NC]
c = {}
for i, net in enumerate(sw2, 1):
    c[str(i)] = '+5V' if net else NC
    c[str(17 - i)] = net
part('SW2', 'SW_DIP_8', 'UART/LPT', 'bus', c)
pd = [x for x in sw1 if x] + ['UART_EN']
part('RN1', 'RN_8', '10k', 'bus', dict({'1': 'GND'}, **{str(i + 2): v for i, v in enumerate(pd)}))
part('RN2', 'RN_4', '10k', 'bus', dict({'1': 'GND'}, **{str(i + 2): v for i, v in enumerate(['UART_S0', 'UART_S1', 'LPT_S0', 'LPT_S1'])}))

# High-speed mode: jumpers swap A0 and A3 for the IDE GAL and IDE DA0 (1-2 normal, 2-3 swapped)
part('JP1', 'JP_3', 'IDE A0 (1-2 std, 2-3 HS)', 'bus', {'1': 'A0', '2': 'IA0', '3': 'A3'})
part('JP2', 'JP_3', 'IDE A3 (1-2 std, 2-3 HS)', 'bus', {'1': 'A3', '2': 'IA3', '3': 'A0'})

# ---------------------------------------------------------------- IDE
c = {str(2 + i): D[i] for i in range(8)}
c.update({str(19 - i): 'DD%d' % (8 + i) for i in range(8)})
c.update({'1': n('DIOW'), '11': n('HWR'), '20': '+5V', '10': 'GND'})
part('U6', '74HCT574', '74HCT574 write latch', 'ide', c)
c = {str(2 + i): 'DD%d' % (8 + i) for i in range(8)}
c.update({str(19 - i): D[i] for i in range(8)})
c.update({'1': n('HRDOE'), '11': n('DIOR'), '20': '+5V', '10': 'GND'})
part('U7', '74HCT574_M', '74HCT574 read latch', 'ide', c)

ide = {1: n('RESET'), 2: 'GND', 19: 'GND', 20: NC, 21: NC, 22: 'GND', 23: n('DIOW'), 24: 'GND', 25: n('DIOR'), 26: 'GND',
       27: NC, 28: 'GND', 29: NC, 30: 'GND', 31: NC, 32: NC, 33: 'A1', 34: NC, 35: 'IA0', 36: 'A2', 37: n('IDE_CS0'),
       38: n('IDE_CS1'), 39: n('DASP'), 40: 'GND'}
for i in range(8):
    ide[17 - 2 * i] = D[i]
    ide[4 + 2 * i] = 'DD%d' % (8 + i)
part('J2', 'IDE_40', 'IDE 40-pin 2.54 mm', 'ide', {str(k): v for k, v in ide.items()})
ide44 = {**ide, 41: 'IDE44_5V', 42: 'IDE44_5V', 43: 'GND', 44: NC}
part('J3', 'IDE_44', 'IDE 44-pin 2.0 mm', 'ide', {str(k): v for k, v in ide44.items()})
part('J4', 'Berg_4', 'Floppy power (Berg)', 'ide', {'1': 'BERG_5V', '2': 'GND', '3': 'GND', '4': NC})
part('F1', 'Polyfuse_H', 'MF-R075 0.75 A', 'ide', {'1': '+5V', '2': 'IDE_ISA_5V'})
part('JP3', 'JP_3', '44-pin power (1-2 ISA, 2-3 Berg)', 'ide', {'1': 'IDE_ISA_5V', '2': 'IDE44_5V', '3': 'BERG_5V'})
part('R1', 'R', '470', 'ide', {'1': '+5V', '2': 'DASP_LED'})
part('D1', 'LED', 'IDE activity', 'ide', {'2': 'DASP_LED', '1': n('DASP')})
part('R2', 'R', '10k', 'ide', {'1': 'D7', '2': 'GND'})

# ---------------------------------------------------------------- floppy + ROM
c = {'11': 'D0', '13': 'D1', '14': 'D2', '15': 'D3', '17': 'D4', '19': 'D5', '20': 'D6', '22': 'D7',
     '7': 'A0', '8': 'A1', '10': 'A2', '6': n('FDCCS'), '4': IOR, '5': IOW, '3': n('FDC_DACK'), '25': 'TC', '32': 'RESET',
     '24': 'FDC_DRQ', '23': 'FDC_IRQ', '33': 'FDC_CLK', '34': NC, '27': '+5V', '39': '+5V', '35': 'GND', '30': 'GND',
     '42': NC, '43': NC, '44': NC, '47': NC, '18': '+5V', '40': '+5V', '60': '+5V', '68': '+5V', '46': '+5V',
     '9': 'GND', '12': 'GND', '16': 'GND', '21': 'GND', '36': 'GND',
     '57': 'FD_ME0', '61': 'FD_ME1', '63': NC, '66': NC, '58': 'FD_DS0', '62': 'FD_DS1', '64': NC, '67': NC,
     '56': 'FD_DIR', '55': 'FD_STEP', '53': 'FD_WDATA', '52': 'FD_WGATE', '51': 'FD_HDSEL', '49': 'FD_DENSEL',
     '28': 'FD_DRATE0', '29': NC, '26': 'FD_INDEX', '2': 'FD_TRK0', '1': 'FD_WP', '41': 'FD_RDATA', '31': 'FD_DSKCHG',
     '38': 'FDC_HIFIL', '37': 'FDC_LOFIL', '48': NC, '45': 'GND', '50': 'GND', '54': 'GND', '59': 'GND', '65': 'GND'}
part('U8', '82077AA', '82077AA / PC8477BV-1', 'fdc', c)
part('X1', 'OSC_DIP8', '24 MHz', 'fdc', {'1': NC, '8': '+5V', '4': 'GND', '5': 'FDC_CLK'})
part('C1', 'C', '4.7n', 'fdc', {'1': 'FDC_HIFIL', '2': 'FDC_LOFIL'})
part('RN3', 'RN_5', '1k', 'fdc', {'1': '+5V', '2': 'FD_INDEX', '3': 'FD_TRK0', '4': 'FD_WP', '5': 'FD_RDATA', '6': 'FD_DSKCHG'})
fdd = {1: 'GND', 3: 'FD_PIN3', 5: 'GND', 7: 'GND', 9: NC, 11: 'GND', 13: 'GND', 15: 'GND', 17: NC, 19: 'GND', 21: 'GND',
       23: 'GND', 25: 'GND', 27: NC, 29: 'GND', 31: 'GND', 33: NC,
       2: 'FD_DENSEL', 4: NC, 6: 'FD_DRATE0', 8: 'FD_INDEX', 10: 'FD_ME0', 12: 'FD_DS1', 14: 'FD_DS0', 16: 'FD_ME1',
       18: 'FD_DIR', 20: 'FD_STEP', 22: 'FD_WDATA', 24: 'FD_WGATE', 26: 'FD_TRK0', 28: 'FD_WP', 30: 'FD_RDATA',
       32: 'FD_HDSEL', 34: 'FD_DSKCHG'}
part('J5', 'FDD_34', 'Floppy 34-pin', 'fdc', {str(k): v for k, v in fdd.items()})
part('JP4', 'JP_2', '+5V on floppy pin 3', 'fdc', {'1': '+5V', '2': 'FD_PIN3'})
part('JP5', 'JP_3', 'FDC DRQ (1-2 DRQ2, 2-3 DRQ3)', 'fdc', {'1': 'DRQ2', '2': 'FDC_DRQ', '3': 'DRQ3'})
part('JP6', 'JP_3', 'FDC DACK (1-2 DACK2, 2-3 DACK3)', 'fdc', {'1': n('DACK2'), '2': n('FDC_DACK'), '3': n('DACK3')})
part('JP7', 'JP_2', 'FDC IRQ6', 'fdc', {'1': 'FDC_IRQ', '2': 'IRQ6'})
part('R3', 'R', '10k', 'fdc', {'1': '+5V', '2': n('FDC_DACK')})

rom = {'10': 'A0', '9': 'A1', '8': 'A2', '7': 'A3', '6': 'A4', '5': 'A5', '4': 'A6', '3': 'A7', '25': 'A8', '24': 'A9',
       '21': 'A10', '23': 'A11', '2': 'A12', '26': 'A13', '1': 'A14', '20': n('ROMCE'), '22': MEMR, '27': n('ROMWE'),
       '28': '+5V', '14': 'GND', '11': 'D0', '12': 'D1', '13': 'D2', '15': 'D3', '16': 'D4', '17': 'D5', '18': 'D6', '19': 'D7'}
part('U9', '28C256', '28C256 option ROM', 'fdc', rom)
part('R4', 'R', '10k', 'fdc', {'1': '+5V', '2': n('ROMWE')})

# ---------------------------------------------------------------- serial
c = {str(2 + i): D[i] for i in range(8)}
c.update({'31': 'A0', '30': 'A1', '29': 'A2', '14': '+5V', '15': '+5V', '16': n('UARTCS'), '28': 'GND', '24': IOR, '25': 'GND',
          '20': IOW, '21': 'GND', '39': 'RESET', '33': 'UART_INT', '1': NC, '12': NC, '23': NC, '34': NC, '44': '+5V', '22': 'GND',
          '18': 'UART_CLK', '19': NC, '17': 'UART_BAUD', '10': 'UART_BAUD', '13': 'SER_SOUT', '11': 'SER_SIN',
          '36': n('SER_RTS'), '37': n('SER_DTR'), '40': n('SER_CTS'), '41': n('SER_DSR'), '42': n('SER_DCD'), '43': n('SER_RI'),
          '38': NC, '35': n('UART_OUT2'), '32': NC, '27': NC, '26': NC})
part('U10', '16C550', '16C550', 'io', c)
part('X2', 'OSC_DIP8', '1.8432 MHz', 'io', {'1': NC, '8': '+5V', '4': 'GND', '5': 'UART_CLK'})
part('U11', 'SN75C185', 'SN75C185', 'io', {
    '16': n('SER_RTS'), '15': 'SER_SOUT', '13': n('SER_DTR'), '19': n('SER_DCD'), '18': n('SER_DSR'), '17': 'SER_SIN',
    '14': n('SER_CTS'), '12': n('SER_RI'), '20': '+5V', '1': '+12V', '10': '-12V', '11': 'GND',
    '5': 'RS_RTS', '6': 'RS_TXD', '8': 'RS_DTR', '2': 'RS_DCD', '3': 'RS_DSR', '4': 'RS_RXD', '7': 'RS_CTS', '9': 'RS_RI'})
part('J6', 'DE9_Male', 'Serial DE9 male', 'io', {'1': 'RS_DCD', '2': 'RS_RXD', '3': 'RS_TXD', '4': 'RS_DTR', '5': 'GND',
                                                 '6': 'RS_DSR', '7': 'RS_RTS', '8': 'RS_CTS', '9': 'RS_RI', '0': 'GND'})
part('U12', '74HCT125', '74HCT125', 'io', {'1': n('UART_OUT2'), '2': 'UART_INT', '3': 'SER_IRQ',
                                           '4': n('LPT_IRQEN'), '5': n('LPT_ACK'), '6': 'LPT_IRQ',
                                           '10': '+5V', '9': 'GND', '8': NC, '13': '+5V', '12': 'GND', '11': NC,
                                           '14': '+5V', '7': 'GND'})
part('JP8', 'JP_2x4', 'Serial IRQ 3/4/5/7', 'io', {'1': 'SER_IRQ', '3': 'SER_IRQ', '5': 'SER_IRQ', '7': 'SER_IRQ',
                                                   '2': 'IRQ3', '4': 'IRQ4', '6': 'IRQ5', '8': 'IRQ7'})

# ---------------------------------------------------------------- parallel
part('U19', '74HCT138', '74HCT138', 'io', {'1': 'A0', '2': 'A1', '3': IOR, '6': '+5V', '4': n('LPTSTB'), '5': 'GND',
                                           '16': '+5V', '8': 'GND', '15': n('LPT_RDAT'), '14': n('LPT_RSTA'), '13': n('LPT_RCTL'),
                                           '12': NC, '11': n('LPT_WDAT'), '10': NC, '9': n('LPT_WCTL'), '7': NC})
PD = ['PD%d' % i for i in range(8)]
d374 = ['3', '4', '7', '8', '13', '14', '17', '18']
q374 = ['2', '5', '6', '9', '12', '15', '16', '19']
c = {d374[i]: D[i] for i in range(8)}
c.update({q374[i]: PD[i] for i in range(8)})
c.update({'1': 'LPT_DIR', '11': n('LPT_WDAT'), '20': '+5V', '10': 'GND'})
part('U13', '74HCT374', '74HCT374 data latch', 'io', c)
A244 = ['2', '4', '6', '8', '11', '13', '15', '17']
Y244 = ['18', '16', '14', '12', '9', '7', '5', '3']


def buf244(ref, value, inputs, oe):
    c = {A244[i]: inputs[i] for i in range(8)}
    c.update({Y244[i]: D[i] for i in range(8)})
    c.update({'1': oe, '19': oe, '20': '+5V', '10': 'GND'})
    part(ref, '74HCT244', value, 'io', c)


buf244('U14', '74HCT244 data read', PD, n('LPT_RDAT'))
buf244('U15', '74HCT244 status read', ['+5V', '+5V', '+5V', n('LPT_ERR'), 'LPT_SEL', 'LPT_PE', n('LPT_ACK'), n('LPT_BUSY')], n('LPT_RSTA'))
buf244('U16', '74HCT244 control read', ['LPT_STB', 'LPT_AFD', 'LPT_INI', 'LPT_SLI', 'LPT_IRQEN', 'LPT_DIR', '+5V', '+5V'], n('LPT_RCTL'))
part('U17', '74HCT174', '74HCT174 control', 'io', {'9': n('LPT_WCTL'), '1': n('RESET'), '3': 'D0', '4': 'D1', '6': 'D2', '11': 'D3',
                                                   '13': 'D4', '14': 'D5', '2': 'LPT_STB', '5': 'LPT_AFD', '7': 'LPT_INI',
                                                   '10': 'LPT_SLI', '12': 'LPT_IRQEN', '15': 'LPT_DIR', '16': '+5V', '8': 'GND'})
part('U18', '7406', '7406', 'io', {'1': 'LPT_STB', '2': n('LPT_STROBE'), '3': 'LPT_AFD', '4': n('LPT_AUTOFD'), '5': 'LPT_ININ',
                                   '6': n('LPT_INIT'), '9': 'LPT_SLI', '8': n('LPT_SELIN'), '11': 'GND', '10': NC, '13': 'GND',
                                   '12': NC, '14': '+5V', '7': 'GND'})
part('U5', '74HCT04', '74HCT04', 'io', {'1': 'RESET', '2': n('RESET'), '3': 'LPT_BUSY', '4': n('LPT_BUSY'), '5': 'LPT_INI',
                                        '6': 'LPT_ININ', '9': 'LPT_IRQEN', '8': n('LPT_IRQEN'), '11': 'GND', '10': NC,
                                        '13': 'GND', '12': NC, '14': '+5V', '7': 'GND'})
part('RN4', 'RN_9', '4k7', 'io', {'1': '+5V', '2': n('LPT_STROBE'), '3': n('LPT_AUTOFD'), '4': n('LPT_INIT'), '5': n('LPT_SELIN'),
                                  '6': n('LPT_ACK'), '7': 'LPT_BUSY', '8': 'LPT_PE', '9': 'LPT_SEL', '10': n('LPT_ERR')})
db = {1: n('LPT_STROBE'), 10: n('LPT_ACK'), 11: 'LPT_BUSY', 12: 'LPT_PE', 13: 'LPT_SEL', 14: n('LPT_AUTOFD'), 15: n('LPT_ERR'),
      16: n('LPT_INIT'), 17: n('LPT_SELIN'), 0: 'GND'}
for i in range(8):
    db[2 + i] = PD[i]
for i in range(18, 26):
    db[i] = 'GND'
part('J7', 'DB25_Female', 'Parallel DB25 female', 'io', {str(k): v for k, v in db.items()})
part('JP9', 'JP_3', 'LPT IRQ (1-2 IRQ7, 2-3 IRQ5)', 'io', {'1': 'IRQ7', '2': 'LPT_IRQ', '3': 'IRQ5'})

# ---------------------------------------------------------------- decoupling
DECOUPLE = {'bus': ['U1', 'U2', 'U3', 'U4'], 'ide': ['U6', 'U7'], 'fdc': ['U8', 'U8', 'U9'],
            'io': ['U10', 'U11', 'U12', 'U13', 'U14', 'U15', 'U16', 'U17', 'U18', 'U19', 'U5']}
k = 10
for sheet, refs in DECOUPLE.items():
    for r in refs:
        part('C%d' % k, 'C', '100n', sheet, {'1': '+5V', '2': 'GND'})
        k += 1
part('C%d' % k, 'CP', '10u', 'bus', {'1': '+5V', '2': 'GND'}); k += 1
part('C%d' % k, 'CP', '10u', 'bus', {'1': '+5V', '2': 'GND'}); k += 1
part('C%d' % k, 'C', '100n', 'io', {'1': '+12V', '2': 'GND'}); k += 1
part('C%d' % k, 'C', '100n', 'io', {'1': 'GND', '2': '-12V'}); k += 1
part('C%d' % k, 'CP', '10u', 'ide', {'1': 'IDE44_5V', '2': 'GND'}); k += 1
