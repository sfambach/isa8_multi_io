# Placement per sheet: ref -> (left, top) of the symbol body in mm. Parts with the same top have their
# first pins on the same row, which keeps straight connections (e.g. FDC to floppy connector) straight.
# ports: side of the sheet where routed nets shared with other sheets leave as global labels.
G = 2.54
LAYOUT = {
    'bus': dict(paper='A3', ports='R', port_x=370, parts={
        'J1': (20, 25.4), 'U1': (95, 25.4 + G), 'U2': (180, 25.4), 'U3': (180, 101.6), 'U4': (180, 177.8),
        'JP1': (110, 100), 'JP2': (110, 120), 'SW1': (250, 30.48), 'RN1': (305, 30.48), 'SW2': (250, 101.6), 'RN2': (305, 101.6),
    }),
    'ide': dict(paper='A3', ports='R', port_x=330, parts={
        'U6': (40, 25.4 + G), 'U7': (40, 101.6), 'J2': (150, 25.4), 'J3': (150, 101.6),
        'R1': (230, 50.8), 'D1': (230, 71.12), 'R2': (110, 180), 'F1': (200, 190.5), 'JP3': (240, 180), 'J4': (290, 180),
    }),
    'fdc': dict(paper='A3', ports='L', port_x=25, parts={
        'U8': (60, 25.4), 'J5': (135, 25.4), 'JP4': (170, 25.4), 'RN3': (110, 155), 'C1': (100, 95),
        'X1': (30, 140), 'JP5': (30, 170), 'JP6': (30, 190), 'JP7': (30, 210), 'R3': (60, 190),
        'U9': (150, 150), 'R4': (125, 215),
    }),
    'io': dict(paper='A2', ports='L', port_x=25, parts={
        'U10': (60, 30.48), 'X2': (120, 15.24), 'U11': (140, 30.48 + 5 * G), 'J6': (215, 30.48 + 5 * G),
        'U12': (140, 101.6), 'JP8': (215, 101.6),
        'U19': (60, 132.08), 'U17': (60, 177.8), 'U18': (150, 177.8), 'RN4': (230, 177.8), 'U5': (400, 177.8),
        'U13': (60, 238.76), 'J7': (310, 238.76 + 2 * G), 'U14': (230, 254), 'U16': (150, 320.04), 'U15': (230, 320.04),
        'JP9': (215, 140),
    }),
}
# Decoupling capacitors are placed automatically in a row at CAP_ROW (mm from top).
CAP_ROW = {'bus': 250, 'ide': 250, 'fdc': 250, 'io': 380}
