#!/usr/bin/env python3
"""Builds the Proteus-BR schematic sheets from the original Proteus v0.7.

Reads pristine sheets from the repository root, applies the SPEC-FREEZE
changes, writes results into hardware/proteus-br/. Idempotent: always
regenerates from the originals.

Decisions implemented (approved 2026-06-10):
  1/2/6: VNLD5160TR-E kept, TLE4251D tracker, TC4427ACOA713 ignition driver
  4: single status LED on PE5 (running)
  7: ETB pairs on C2; 8: one connector pin per ETB phase
  9: AUX_SPI CS = PG15, expansion reserve = PG0
  10: expansion 12V_SW = 12v_PROT
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
DST = os.path.normpath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)

from kicad_sexp import (Sym, Num, parse, dump, children, child, prop,
                        propval, set_propval)
from schedit import Schematic, P

PROJECT = 'proteus-br'
ROOT_UUID = 'da96cc1d-20c0-47ba-9881-2a73783a20fb'
SHEET_UUIDS = {
    'ign1':             '00000000-0000-0000-0000-00005d975f3c',
    'lowside_quad1':    '00000000-0000-0000-0000-00005d98a146',
    'ign2':             '00000000-0000-0000-0000-00005d98f734',
    'ign3':             '00000000-0000-0000-0000-00005d991e7f',
    'mcu':              '00000000-0000-0000-0000-00005d99e6ee',
    'lowside_quad2':    '00000000-0000-0000-0000-00005d99f107',
    'lowside_quad3':    '00000000-0000-0000-0000-00005d99f37f',
    'lowside_quad4':    '00000000-0000-0000-0000-00005d99f54c',
    'quad_analog1':     '00000000-0000-0000-0000-00005d9a3845',
    'quad_analog2':     '00000000-0000-0000-0000-00005da6c1ea',
    'quad_analog3':     '00000000-0000-0000-0000-00005da6c714',
    'psu':              '00000000-0000-0000-0000-00005da72eff',
    'quad_analog_temp': '00000000-0000-0000-0000-00005dcc02d0',
    'highside_quad':    '00000000-0000-0000-0000-00005dd5b2e0',
    'triggers':         '00000000-0000-0000-0000-00005dd8090b',
    'knock':            '00000000-0000-0000-0000-00005e814213',
    'etb1':             '00000000-0000-0000-0000-000062471bcf',
    'etb2':             '00000000-0000-0000-0000-00006247ae9a',
}


def spath(sheet):
    return '/%s/%s' % (ROOT_UUID, SHEET_UUIDS[sheet])


def load(src_name):
    """Load original sheet, renaming the instances project."""
    path = os.path.join(SRC, src_name)
    with open(path) as f:
        text = f.read()
    text = text.replace('(project "proteus"', '(project "%s"' % PROJECT)
    s = Schematic.__new__(Schematic)
    s.path = path
    s.tree = parse(text)
    s._lib = {}
    libs = child(s.tree, 'lib_symbols')
    if libs:
        for sym in children(libs, 'symbol'):
            s._lib[sym[1]] = sym
    return s


def save(s, dst_name):
    out = os.path.join(DST, dst_name)
    with open(out, 'w') as f:
        f.write(dump(s.tree) + '\n')
    print('wrote', out)


def setval(s, ref, value):
    sym = s.by_ref(ref)
    assert sym is not None, ref
    set_propval(sym, 'Value', value)


def mark_dnp(s, refs, note='DNP fase 1'):
    for ref in refs:
        sym = s.by_ref(ref)
        assert sym is not None, 'DNP ref not found: %s' % ref
        s.set_dnp(sym, True)
        s.add_property(sym, 'DNP', note)


# --------------------------------------------------------------------------
def build_mcu():
    s = load('mcu.kicad_sch')
    u = s.by_ref('U1501')
    pin = lambda n: s.pin_pos(u, n)

    # --- removals -----------------------------------------------------
    # RTC battery (BT1 + OR diodes; R1513 is the BOOT0 pulldown -> kept)
    # power/extra LEDs, remote USB (J1504), UART header (J2), AUX SPI
    # header (J1505), Tag-Connect (J4), VBUS->5V diode (D1503),
    # LPS25HB baro (U9 + I2C pullups R39/R41 + local decoupling C20)
    s.delete_symbols(['BT1', 'D3', 'D4', 'C30', 'D1503',
                      'D1502', 'D1504', 'D1505', 'D1507',
                      'R1508', 'R1509', 'R1510', 'R1512',
                      'J1504', 'J1505', 'J2', 'J4',
                      'U9', 'R39', 'R41', 'C20'])

    # VBAT (pin 6) tied straight to 3V3 (no RTC on the F427 build)
    s.add_power('proteus-rescue:+3.3V-power', pin('6'), 0,
                PROJECT, spath('mcu'))

    # unused LED nets PE3/PE4/PE6 -> NC
    for pn, lbl in (('2', 'LED1'), ('3', 'LED2'), ('5', 'LED4')):
        s.remove_label_at(lbl, pin(pn))
        s.add_nc(pin(pn))

    # single status LED: D1506 on PE5 (running), 1k series per spec
    setval(s, 'D1506', 'ORANGE')
    setval(s, 'R1511', '1k')

    # AUX_SPI_CS moves from PF6 (pin 18) to PG15 (pin 132) per decision 9
    assert s.remove_wire(pin('18'), (81.28, 177.165))
    assert s.remove_label_at('AUX_SPI_CS', (81.28, 177.165))
    s.add_nc(pin('18'))
    assert s.remove_nc_at(pin('132'))
    s.add_wire(pin('132'), (81.28, 156.845))
    s.add_label('AUX_SPI_CS', (81.28, 156.845), 180,
                kind='hierarchical_label', shape='output')

    # expansion reserve PG0 (pin 56)
    assert s.remove_nc_at(pin('56'))
    s.add_wire(pin('56'), (88.9, 118.745))
    s.add_label('EXP_GPIO0', (88.9, 118.745), 180,
                kind='hierarchical_label', shape='bidirectional')

    # AUX SPI + UART now leave through the hierarchy (expansion connector)
    for name, shape in (('AUX_SPI_SCK', 'output'),
                        ('AUX_SPI_MISO', 'input'),
                        ('AUX_SPI_MOSI', 'output'),
                        ('UART_TX', 'output'), ('UART_RX', 'input')):
        n = s.convert_local_to_hier(name, shape)
        assert n == 1, (name, n)

    # baro bus gone: PB10/PB11 NC
    for pn, lbl in (('69', 'BARO_SCL'), ('70', 'BARO_SDA')):
        assert s.remove_wire(pin(pn), (177.165, P(pin(pn)[1])))
        assert s.remove_label_at(lbl, (177.165, P(pin(pn)[1])))
        s.add_nc(pin(pn))

    # single USB connector: USB_D+/- stay local (local labels already
    # exist at the same points); shield net becomes local as well
    s.remove_label_at('USB_D+', (173.99, 106.045),
                      tags=('hierarchical_label',))
    s.remove_label_at('USB_D-', (173.99, 103.505),
                      tags=('hierarchical_label',))
    s.convert_hier_to_local('USB_SHIELD')

    setval(s, 'U1501', 'STM32F427ZGT6')

    # fase 1 DNP inside mcu sheet
    mark_dnp(s, ['J1'])           # microSD

    removed = s.gc_power()
    print('mcu: gc_power removed', removed)
    save(s, 'mcu.kicad_sch')
    return s


# --------------------------------------------------------------------------
TLE4251D_LIB = '''
(symbol "proteus-br:TLE4251D" (in_bom yes) (on_board yes)
  (property "Reference" "U" (at 0 8.89 0) (effects (font (size 1.27 1.27))))
  (property "Value" "TLE4251D" (at 0 -15.24 0)
    (effects (font (size 1.27 1.27))))
  (property "Footprint" "Package_TO_SOT_SMD:TO-252-5_TabPin6" (at 0 0 0)
    (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "https://www.infineon.com/tle4251d" (at 0 0 0)
    (effects (font (size 1.27 1.27)) hide))
  (property "ki_description" "Voltage tracker 400mA, PG-TO252-5 (DPAK-5)"
    (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol "TLE4251D_0_1"
    (rectangle (start -7.62 6.35) (end 8.89 -8.89)
      (stroke (width 0.254) (type default)) (fill (type background)))
  )
  (symbol "TLE4251D_1_1"
    (pin power_in line (at -10.16 0 0) (length 2.54)
      (name "I" (effects (font (size 1.27 1.27))))
      (number "1" (effects (font (size 1.27 1.27)))))
    (pin input line (at -10.16 2.54 0) (length 2.54)
      (name "EN" (effects (font (size 1.27 1.27))))
      (number "2" (effects (font (size 1.27 1.27)))))
    (pin power_in line (at 0 -11.43 90) (length 2.54)
      (name "GND" (effects (font (size 1.27 1.27))))
      (number "3" (effects (font (size 1.27 1.27)))))
    (pin input line (at -10.16 -6.35 0) (length 2.54)
      (name "ADJ" (effects (font (size 1.27 1.27))))
      (number "4" (effects (font (size 1.27 1.27)))))
    (pin power_out line (at 11.43 2.54 180) (length 2.54)
      (name "Q" (effects (font (size 1.27 1.27))))
      (number "5" (effects (font (size 1.27 1.27)))))
    (pin passive line (at 2.54 -11.43 90) (length 2.54)
      (name "TAB" (effects (font (size 1.27 1.27))))
      (number "6" (effects (font (size 1.27 1.27)))))
  )
)
'''


def swap_tracker(s, ref):
    """Swap a TLS115 instance to the embedded TLE4251D symbol."""
    import uuid as uuidlib
    sym = s.by_ref(ref)
    lid = child(sym, 'lib_id')
    lid[1] = 'proteus-br:TLE4251D'
    set_propval(sym, 'Value', 'TLE4251D')
    set_propval(sym, 'Footprint', 'Package_TO_SOT_SMD:TO-252-5_TabPin6')
    for pnode in list(children(sym, 'pin')):
        sym.remove(pnode)
    inst = child(sym, 'instances')
    idx = sym.index(inst) if inst else len(sym)
    for n in ('1', '2', '3', '4', '5', '6'):
        sym.insert(idx, parse('(pin "%s" (uuid %s))' % (n, uuidlib.uuid4())))
        idx += 1


def build_psu():
    s = load('psu.kicad_sch')
    libs = child(s.tree, 'lib_symbols')
    tle = parse(TLE4251D_LIB)
    libs.append(tle)
    s._lib['proteus-br:TLE4251D'] = tle

    # tracker swap: TLS115D0E (PG-DSO-8) -> TLE4251D (PG-TO252-5).
    # Geometry mapping (same wire contact points):
    #   TLS115 pin7/8 (VI, 12V_PROT)  -> TLE4251D I (1) + EN (2, self-en)
    #   TLS115 pin5 (5V ref)          -> TLE4251D ADJ (4)
    #   TLS115 pin1 (out)             -> TLE4251D Q (5)
    #   TLS115 pin3/9 (GND)           -> TLE4251D GND (3) + TAB (6)
    #   TLS115 pin4 (PG)              -> removed (TLE4251D has no PG);
    #       the 5V_SENSOR_x_PG nets stay routed to PC14/PC15 with the
    #       10k pullups R1006/R1007 as DNP (diagnostics only).
    swap_tracker(s, 'U1004')
    swap_tracker(s, 'U1005')
    # PG stub wires off the old pin 4 of each tracker
    assert s.remove_wire((55.88, 84.455), (59.69, 84.455))
    assert s.remove_wire((59.69, 84.455), (59.69, 94.615))
    assert s.remove_wire((128.905, 84.455), (132.715, 84.455))
    assert s.remove_wire((132.715, 84.455), (132.715, 94.615))

    # single 12V input on the BR: 12v_PROT comes only from the root
    # polyfuses; the old D903 schottky (12V_RAW -> 12V_PROT OR-ing)
    # would bypass the polyfuses and is removed.
    s.delete_symbols(['D903'])

    # fase 1 DNP: tracker #2 + its caps, PG pullups, whole CAN2 channel
    mark_dnp(s, ['U1005', 'C1017', 'C1018'])
    mark_dnp(s, ['R1006', 'R1007'], note='DNP — diagnóstico futuro (PG)')
    mark_dnp(s, ['U6', 'D2', 'R33'], note='DNP fase 1 — CAN2 footprint')

    s.add_text('Proteus-BR: TLE4251D substitui TLS115D0E (LCSC C539669). '
               'PREMISSA a verificar no datasheet Infineon antes do layout: '
               'pinos 1=I 2=EN 3=GND 4=ADJ 5=Q tab=GND. EN amarrado em I '
               '(sempre ligado). ADJ segue o 5V do buck (tracking '
               'ratiometrico). Cout 1u X7R: janela de ESR do datasheet.',
               (20.32, 110.49), 1.5)
    s.add_text('TLE4251D nao tem saida PG: redes 5V_SENSOR_x_PG mantidas '
               'ate PC14/PC15 com pullups 10k DNP (R1006/R1007) para '
               'diagnostico futuro por resistor.', (20.32, 115.57), 1.5)
    s.add_text('Proteus-BR: D903 removido — entrada unica de 12V; '
               '12v_PROT vem somente dos polyfuses F101/F102 (folha raiz). '
               'Um schottky em paralelo anularia a protecao.',
               (20.32, 120.65), 1.5)

    removed = s.gc_power()
    print('psu: gc_power removed', removed)
    save(s, 'psu.kicad_sch')


def ensure_lib(s, lib_id, donor_path):
    """Copy a lib_symbols entry from another sheet file if missing."""
    if lib_id in s._lib:
        return
    d = load(donor_path) if isinstance(donor_path, str) else donor_path
    src = d._lib[lib_id]
    libs = child(s.tree, 'lib_symbols')
    node = parse(dump(src))
    libs.append(node)
    s._lib[lib_id] = node


def add_resistor(s, pt, rot, value, footprint, inst_refs, fields=None):
    """Place a Device:R with per-instance references.

    inst_refs: list of (sheetpath, ref).
    """
    import uuid as uuidlib
    x, y = P(pt[0]), P(pt[1])
    node = parse(
        '(symbol (lib_id "Device:R") (at %s %s %s) (unit 1) (in_bom yes) '
        '(on_board yes) (dnp no) (fields_autoplaced) (uuid %s) '
        '(property "Reference" "%s" (at %s %s 0) (effects (font '
        '(size 1.27 1.27)) (justify left))) '
        '(property "Value" "%s" (at %s %s 0) (effects (font '
        '(size 1.27 1.27)) (justify left))) '
        '(property "Footprint" "%s" (at %s %s 0) (effects (font '
        '(size 1.27 1.27)) hide)) '
        '(property "Datasheet" "~" (at %s %s 0) (effects (font '
        '(size 1.27 1.27)) hide)) '
        '(pin "1" (uuid %s)) (pin "2" (uuid %s)))'
        % (x, y, rot, uuidlib.uuid4(), inst_refs[0][1],
           x + 2.0, y - 1.8, value, x + 2.0, y + 0.2,
           footprint, x, y, x, y,
           uuidlib.uuid4(), uuidlib.uuid4()))
    for fname, fval in (fields or {}).items():
        Schematic.add_property(node, fname, fval)
    node.append(parse('(instances (project "%s" %s))' % (PROJECT, ' '.join(
        '(path "%s" (reference "%s") (unit 1))' % (p, r)
        for p, r in inst_refs))))
    s.tree.append(node)
    return node


R0603 = 'Resistor_SMD:R_0603_1608Metric'


def build_lowside():
    s = load('lowside_quad.kicad_sch')
    ensure_lib(s, 'Device:R', 'mcu.kicad_sch')
    paths = [spath('lowside_quad%d' % i) for i in (1, 2, 3, 4)]

    # arrays out (spec D: ex-arrays RN 1k -> discrete 0603)
    s.delete_symbols(['RN201', 'RN202'], prune=False)

    # series 1k per channel (horizontal, between x=73.025 and 83.185)
    for ch, yy in enumerate((68.58, 71.12, 73.66, 76.2), start=1):
        refs = [(paths[k], 'R%d1%d' % (k + 2, ch)) for k in range(4)]
        add_resistor(s, (78.105, yy), 90, '1k', R0603, refs)
        s.add_wire((73.025, yy), (74.295, yy))
        s.add_wire((81.915, yy), (83.185, yy))

    # pulldown 1k per channel (vertical, between y=78.74 and 88.9)
    for ch, xx in enumerate((62.865, 65.405, 67.945, 70.485), start=1):
        refs = [(paths[k], 'R%d2%d' % (k + 2, ch)) for k in range(4)]
        add_resistor(s, (xx, 83.82), 0, '1k', R0603, refs)
        s.add_wire((xx, 78.74), (xx, 80.01))
        s.add_wire((xx, 87.63), (xx, 88.9))

    s.add_text('Proteus-BR: arrays RN 1k convertidos em discretos 0603 '
               '(retrabalho manual mais facil). Serie 1k + pulldown 1k '
               'por canal, iguais ao original.', (59.055, 116.84), 1.5)
    save(s, 'lowside_quad.kicad_sch')


if __name__ == '__main__':
    build_mcu()
    build_psu()
    build_lowside()
