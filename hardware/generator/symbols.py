# Symbol definitions for the isa8_multi_io schematic (library nickname "isa8").
# Every IC is a single-unit box with pins on the left and right, power pins included,
# so the generator can place power symbols and route wires without hidden pins.
G = 2.54
TYPES = {'I': 'input', 'O': 'output', 'B': 'bidirectional', 'T': 'tri_state', 'P': 'passive',
         'W': 'power_in', 'C': 'open_collector', 'N': 'no_connect'}


def seq(nums, names, t):
    return [(str(n), m, t) for n, m in zip(nums, names)]


def ic(ref, fp, width, left, right, desc=''):
    return dict(kind='box', ref=ref, fp=fp, width=width, L=left, R=right, desc=desc)


def gal():
    left = seq(range(1, 12), ['I1/CLK'] + ['I%d' % i for i in range(2, 12)], 'I') + [('13', 'I13', 'I'), None, ('24', 'VCC', 'W'), ('12', 'GND', 'W')]
    right = seq(range(14, 24), ['IO%d' % i for i in range(14, 24)], 'B')
    return ic('U', 'Package_DIP:DIP-24_W7.62mm_Socket', 15.24, left, right, 'ATF22V10C / GAL22V10')


def latch574(name='574'):
    left = [('1', '~{OE}', 'I'), ('11', 'CLK', 'I'), None] + seq(range(2, 10), ['D%d' % i for i in range(8)], 'I') + [None, ('20', 'VCC', 'W'), ('10', 'GND', 'W')]
    right = seq(range(19, 11, -1), ['Q%d' % i for i in range(8)], 'T')
    return ic('U', 'Package_DIP:DIP-20_W7.62mm_Socket', 12.7, left, right)


def latch574_mirrored():
    right = [('1', '~{OE}', 'I'), ('11', 'CLK', 'I'), None] + seq(range(2, 10), ['D%d' % i for i in range(8)], 'I') + [None, ('20', 'VCC', 'W'), ('10', 'GND', 'W')]
    left = [None, None, None] + seq(range(19, 11, -1), ['Q%d' % i for i in range(8)], 'T')
    return ic('U', 'Package_DIP:DIP-20_W7.62mm_Socket', 12.7, left, right)


def latch374():
    d = ['3', '4', '7', '8', '13', '14', '17', '18']
    q = ['2', '5', '6', '9', '12', '15', '16', '19']
    left = [('1', '~{OE}', 'I'), ('11', 'CLK', 'I'), None] + seq(d, ['D%d' % i for i in range(8)], 'I') + [None, ('20', 'VCC', 'W'), ('10', 'GND', 'W')]
    right = seq(q, ['Q%d' % i for i in range(8)], 'T')
    return ic('U', 'Package_DIP:DIP-20_W7.62mm_Socket', 12.7, left, right)


def buf244():
    a = ['2', '4', '6', '8', '11', '13', '15', '17']
    y = ['18', '16', '14', '12', '9', '7', '5', '3']
    left = [('1', '~{1OE}', 'I'), ('19', '~{2OE}', 'I'), None] + seq(a, ['1A1', '1A2', '1A3', '1A4', '2A1', '2A2', '2A3', '2A4'], 'I') + [None, ('20', 'VCC', 'W'), ('10', 'GND', 'W')]
    right = seq(y, ['1Y1', '1Y2', '1Y3', '1Y4', '2Y1', '2Y2', '2Y3', '2Y4'], 'T')
    return ic('U', 'Package_DIP:DIP-20_W7.62mm_Socket', 12.7, left, right)


def xcvr245():
    left = seq(range(9, 1, -1), ['A%d' % i for i in range(7, -1, -1)], 'B') + [None, ('1', 'DIR', 'I'), ('19', '~{OE}', 'I'), None, ('20', 'VCC', 'W'), ('10', 'GND', 'W')]
    right = seq(range(11, 19), ['B%d' % i for i in range(7, -1, -1)], 'B')
    return ic('U', 'Package_DIP:DIP-20_W7.62mm_Socket', 12.7, left, right)


def dec138():
    left = [('1', 'A', 'I'), ('2', 'B', 'I'), ('3', 'C', 'I'), None, ('6', 'E3', 'I'), ('4', '~{E1}', 'I'), ('5', '~{E2}', 'I'), None, ('16', 'VCC', 'W'), ('8', 'GND', 'W')]
    right = seq(['15', '14', '13', '12', '11', '10', '9', '7'], ['~{Y%d}' % i for i in range(8)], 'O')
    return ic('U', 'Package_DIP:DIP-16_W7.62mm_Socket', 12.7, left, right)


def ff174():
    d = ['3', '4', '6', '11', '13', '14']
    q = ['2', '5', '7', '10', '12', '15']
    left = [('9', 'CLK', 'I'), ('1', '~{MR}', 'I'), None] + seq(d, ['D%d' % i for i in range(6)], 'I') + [None, ('16', 'VCC', 'W'), ('8', 'GND', 'W')]
    right = seq(q, ['Q%d' % i for i in range(6)], 'O')
    return ic('U', 'Package_DIP:DIP-16_W7.62mm_Socket', 12.7, left, right)


def hex_inv(otype='O'):
    a = ['1', '3', '5', '9', '11', '13']
    y = ['2', '4', '6', '8', '10', '12']
    left = seq(a, ['%dA' % i for i in range(1, 7)], 'I') + [None, ('14', 'VCC', 'W'), ('7', 'GND', 'W')]
    right = seq(y, ['%dY' % i for i in range(1, 7)], otype)
    return ic('U', 'Package_DIP:DIP-14_W7.62mm_Socket', 12.7, left, right)


def buf125():
    left = [('1', '~{1OE}', 'I'), ('2', '1A', 'I'), ('4', '~{2OE}', 'I'), ('5', '2A', 'I'), ('10', '~{3OE}', 'I'), ('9', '3A', 'I'),
            ('13', '~{4OE}', 'I'), ('12', '4A', 'I'), None, ('14', 'VCC', 'W'), ('7', 'GND', 'W')]
    right = [None, ('3', '1Y', 'T'), None, ('6', '2Y', 'T'), None, ('8', '3Y', 'T'), None, ('11', '4Y', 'T')]
    return ic('U', 'Package_DIP:DIP-14_W7.62mm_Socket', 12.7, left, right)


def eeprom():
    left = seq(['10', '9', '8', '7', '6', '5', '4', '3', '25', '24', '21', '23', '2', '26', '1'], ['A%d' % i for i in range(15)], 'I') + \
        [None, ('20', '~{CE}', 'I'), ('22', '~{OE}', 'I'), ('27', '~{WE}', 'I'), None, ('28', 'VCC', 'W'), ('14', 'GND', 'W')]
    right = seq(['11', '12', '13', '15', '16', '17', '18', '19'], ['D%d' % i for i in range(8)], 'B')
    return ic('U', 'Package_DIP:DIP-28_W15.24mm_Socket', 15.24, left, right)


def fdc():
    # 82077AA / PC8477BV-1, pin names after the Monster FDC symbol (Sergey Kiselev, CERN-OHL-S-2.0)
    left = [('11', 'DB0', 'B'), ('13', 'DB1', 'B'), ('14', 'DB2', 'B'), ('15', 'DB3', 'B'), ('17', 'DB4', 'B'), ('19', 'DB5', 'B'),
            ('20', 'DB6', 'B'), ('22', 'DB7', 'B'), None, ('7', 'A0', 'I'), ('8', 'A1', 'I'), ('10', 'A2', 'I'), None,
            ('6', '~{CS}', 'I'), ('4', '~{RD}', 'I'), ('5', '~{WR}', 'I'), ('3', '~{DACK}', 'I'), ('25', 'TC', 'I'),
            ('32', 'RESET', 'I'), ('24', 'DRQ', 'T'), ('23', 'INT', 'T'), None, ('33', 'X1', 'I'), ('34', 'X2', 'O'),
            ('27', 'IDENT', 'I'), ('39', 'PLL0', 'I'), ('35', '~{INVERT}', 'I'), ('30', 'DRV2', 'I'), None,
            ('42', 'NC', 'N'), ('43', 'NC', 'N'), ('44', 'NC', 'N'), ('47', 'NC', 'N'), None,
            ('18', 'VCC', 'W'), ('40', 'VCC', 'W'), ('60', 'VCC', 'W'), ('68', 'VCC', 'W'), ('46', 'AVCC', 'W'),
            ('9', 'GND', 'W'), ('12', 'GND', 'W'), ('16', 'GND', 'W'), ('21', 'GND', 'W'), ('36', 'GND', 'W')]
    right = [('49', 'DENSEL', 'O'), None, ('28', 'DRATE0', 'O'), ('26', 'INDEX', 'I'), ('57', 'ME0', 'O'), ('62', 'DS1', 'O'),
             ('58', 'DS0', 'O'), ('61', 'ME1', 'O'), ('56', 'DIR', 'O'), ('55', 'STEP', 'O'), ('53', 'WRDATA', 'O'), ('52', 'WE', 'O'),
             ('2', 'TRK0', 'I'), ('1', 'WP', 'I'), ('41', 'RDDATA', 'I'), ('51', 'HDSEL', 'O'), ('31', 'DSKCHG', 'I'), None,
             ('63', 'ME2', 'O'), ('66', 'ME3', 'O'), ('64', 'DS2', 'O'), ('67', 'DS3', 'O'), ('29', 'DRATE1', 'O'), ('48', 'MFM', 'O'), None,
             ('38', 'HIFIL', 'P'), ('37', 'LOFIL', 'P'), None,
             ('45', 'AVSS', 'W'), ('50', 'GND', 'W'), ('54', 'GND', 'W'), ('59', 'GND', 'W'), ('65', 'GND', 'W')]
    return ic('U', 'Package_LCC:PLCC-68_THT-Socket', 20.32, left, right, '82077AA / PC8477BV-1')


def uart():
    left = seq(range(2, 10), ['D%d' % i for i in range(8)], 'B') + [None, ('31', 'A0', 'I'), ('30', 'A1', 'I'), ('29', 'A2', 'I'), None,
        ('14', 'CS0', 'I'), ('15', 'CS1', 'I'), ('16', '~{CS2}', 'I'), ('28', '~{ADS}', 'I'), ('24', '~{RD}', 'I'), ('25', 'RD', 'I'),
        ('20', '~{WR}', 'I'), ('21', 'WR', 'I'), ('39', 'MR', 'I'), ('33', 'INTR', 'O'), None,
        ('1', 'NC', 'N'), ('12', 'NC', 'N'), ('23', 'NC', 'N'), ('34', 'NC', 'N'), None, ('44', 'VCC', 'W'), ('22', 'GND', 'W')]
    right = [('18', 'XIN', 'I'), ('19', 'XOUT', 'O'), ('17', '~{BAUDOUT}', 'O'), ('10', 'RCLK', 'I'), None,
             ('13', 'SOUT', 'O'), ('11', 'SIN', 'I'), ('36', '~{RTS}', 'O'), ('37', '~{DTR}', 'O'), ('40', '~{CTS}', 'I'),
             ('41', '~{DSR}', 'I'), ('42', '~{DCD}', 'I'), ('43', '~{RI}', 'I'), None,
             ('38', '~{OUT1}', 'O'), ('35', '~{OUT2}', 'O'), ('32', '~{RXRDY}', 'O'), ('27', '~{TXRDY}', 'O'), ('26', 'DDIS', 'O')]
    return ic('U', 'Package_LCC:PLCC-44_THT-Socket', 17.78, left, right, '16C550 PLCC-44')


def rs232():
    # SN75C185 (same pinout as GD75232 / SN75185)
    left = [('15', 'DA2', 'I'), ('17', 'RY3', 'O'), ('16', 'DA1', 'I'), ('13', 'DA3', 'I'), ('14', 'RY4', 'O'), ('18', 'RY2', 'O'),
            ('19', 'RY1', 'O'), ('12', 'RY5', 'O'), None, ('20', 'VCC', 'W'), ('1', 'VDD', 'W'), ('10', 'VSS', 'W'), ('11', 'GND', 'W')]
    right = [('2', 'RA1', 'I'), ('4', 'RA3', 'I'), ('6', 'DY2', 'O'), ('8', 'DY3', 'O'), None, ('3', 'RA2', 'I'), ('5', 'DY1', 'O'),
             ('7', 'RA4', 'I'), ('9', 'RA5', 'I')]
    return ic('U', 'Package_DIP:DIP-20_W7.62mm_Socket', 12.7, left, right)


def osc():
    left = [('1', 'EN', 'I'), None, ('8', 'VCC', 'W'), ('4', 'GND', 'W')]
    right = [('5', 'OUT', 'O')]
    return ic('X', 'Oscillator:Oscillator_DIP-8', 10.16, left, right)


def isa8():
    a = ['~{IOCHCK}'] + ['SD%d' % i for i in range(7, -1, -1)] + ['IOCHRDY', 'AEN'] + ['SA%d' % i for i in range(19, -1, -1)]
    b = ['GND', 'RESET', '+5V', 'IRQ2', '-5V', 'DRQ2', '-12V', '~{0WS}', '+12V', 'GND', '~{SMEMW}', '~{SMEMR}', '~{IOW}', '~{IOR}',
         '~{DACK3}', 'DRQ3', '~{DACK1}', 'DRQ1', '~{REFRESH}', 'CLK', 'IRQ7', 'IRQ6', 'IRQ5', 'IRQ4', 'IRQ3', '~{DACK2}', 'TC',
         'ALE', '+5V', 'OSC', 'GND']
    right = [('A%d' % (i + 1), n, 'P') for i, n in enumerate(a)] + [None] + [('B%d' % (i + 1), n, 'P') for i, n in enumerate(b)]
    return ic('J', 'isa8_multi_io:ISA_8bit_Edge', 20.32, [], right, 'ISA 8-bit card edge')


def conn(n, side='L', names=None, fp='', extra=()):
    pins = [(str(i), names[i - 1] if names else str(i), 'P') for i in range(1, n + 1)] + list(extra)
    return ic('J', fp, 7.62, pins if side == 'L' else [], pins if side == 'R' else [])


def conn2(rows, fp, even_left=False):
    odd = [(str(2 * i + 1), str(2 * i + 1), 'P') for i in range(rows)]
    even = [(str(2 * i + 2), str(2 * i + 2), 'P') for i in range(rows)]
    return ic('J', fp, 7.62, even, odd) if even_left else ic('J', fp, 7.62, odd, even)


def dipsw(n):
    left = [(str(i), str(i), 'P') for i in range(1, n + 1)]
    right = [(str(2 * n + 1 - i), str(2 * n + 1 - i), 'P') for i in range(1, n + 1)]
    return ic('SW', 'Button_Switch_THT:SW_DIP_SPSTx%02d_Slide_9.78x%s_W7.62mm_P2.54mm' % (n, {8: '22.5mm', 4: '12.34mm'}[n]), 7.62, left, right)


def rnet(n):
    right = [('1', 'COM', 'P')]
    left = [(str(i), 'R%d' % (i - 1), 'P') for i in range(2, n + 2)]
    return ic('RN', 'Resistor_THT:R_Array_SIP%d' % (n + 1), 7.62, left, right)


def two(kind, ref, fp, horizontal=False):
    return dict(kind=kind, ref=ref, fp=fp, horizontal=horizontal)


R_FP = 'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal'
C_FP = 'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'
CP_FP = 'Capacitor_THT:CP_Radial_D5.0mm_P2.00mm'

SYMBOLS = {
    'GAL22V10': gal(),
    '74HCT574': latch574(),
    '74HCT574_M': latch574_mirrored(),
    '74HCT374': latch374(),
    '74HCT244': buf244(),
    '74HCT245': xcvr245(),
    '74HCT138': dec138(),
    '74HCT174': ff174(),
    '74HCT04': hex_inv('O'),
    '7406': hex_inv('C'),
    '74HCT125': buf125(),
    '28C256': eeprom(),
    '82077AA': fdc(),
    '16C550': uart(),
    'SN75C185': rs232(),
    'OSC_DIP8': osc(),
    'ISA_8bit': isa8(),
    'IDE_40': conn2(20, 'Connector_IDC:IDC-Header_2x20_P2.54mm_Vertical', True),
    'IDE_44': conn2(22, 'Connector_PinHeader_2.00mm:PinHeader_2x22_P2.00mm_Vertical', True),
    'FDD_34': conn2(17, 'Connector_IDC:IDC-Header_2x17_P2.54mm_Vertical', True),
    'DE9_Male': conn(9, 'L', fp='Connector_Dsub:DSUB-9_Male_Horizontal_P2.77x2.84mm_EdgePinOffset7.70mm_Housed_MountingHolesOffset9.12mm',
                     extra=[('0', 'SHIELD', 'P')]),
    'DB25_Female': conn(25, 'L', fp='Connector_Dsub:DSUB-25_Female_Horizontal_P2.77x2.84mm_EdgePinOffset7.70mm_Housed_MountingHolesOffset9.12mm',
                        extra=[('0', 'SHIELD', 'P')]),
    'Berg_4': conn(4, 'L', ['+5V', 'GND', 'GND', '+12V'], fp='isa8_multi_io:Berg_Floppy_Power_1x04_P2.50mm'),
    'JP_2': dict(conn(2, 'R', fp='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical'), ref='JP'),
    'JP_3': dict(conn(3, 'R', fp='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical'), ref='JP'),
    'JP_3L': dict(conn(3, 'L', fp='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical'), ref='JP'),
    'JP_2x4': dict(conn2(4, 'Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical'), ref='JP'),
    'SW_DIP_8': dipsw(8),
    'RN_4': rnet(4),
    'RN_5': rnet(5),
    'RN_8': rnet(8),
    'RN_9': rnet(9),
    'R': two('R', 'R', R_FP),
    'R_H': two('R', 'R', R_FP, True),
    'C': two('C', 'C', C_FP),
    'C_H': two('C', 'C', C_FP, True),
    'CP': two('CP', 'C', CP_FP),
    'LED': two('LED', 'D', 'LED_THT:LED_D3.0mm'),
    'Polyfuse_H': two('F', 'F', 'Fuse:Fuse_Bourns_MF-RHT070', True),
}
