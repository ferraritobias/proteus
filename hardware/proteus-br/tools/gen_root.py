#!/usr/bin/env python3
"""Generates the Proteus-BR root sheet (proteus-br.kicad_sch).

Wiring style: every sheet pin and connector pin gets a global label at its
exact contact point; same-name labels join the nets. Power nets use power
symbols / labels with the canonical names (GND, +5V, +3V3 ...).
"""
import os
import sys
import uuid as uuidlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kicad_sexp import parse, dump, children, child, propval, set_propval
from schedit import Schematic, P
from build_br import (PROJECT, ROOT_UUID, SHEET_UUIDS, SRC, DST, load,
                      FIELDS_BY_VALUE)

OUT = os.path.join(DST, 'proteus-br.kicad_sch')


def U():
    return str(uuidlib.uuid4())


# ---------------------------------------------------------------- helpers
class Root:
    def __init__(self):
        self.body = []
        self.libs = {}

    def add_lib(self, name, node):
        if name not in self.libs:
            self.libs[name] = node

    def lib_from(self, sch, lib_id):
        self.add_lib(lib_id, sch._lib[lib_id])

    def glabel(self, text, pt, rot, shape='passive'):
        just = 'right' if rot == 180 else 'left'
        self.body.append(parse(
            '(global_label "%s" (shape %s) (at %s %s %s) (effects '
            '(font (size 1.27 1.27)) (justify %s)) (uuid %s))'
            % (text, shape, P(pt[0]), P(pt[1]), rot, just, U())))

    def nc(self, pt):
        self.body.append(parse('(no_connect (at %s %s) (uuid %s))'
                               % (P(pt[0]), P(pt[1]), U())))

    def text(self, s, pt, size=1.5):
        self.body.append(parse(
            '(text "%s" (at %s %s 0) (effects (font (size %s %s)) '
            '(justify left bottom)) (uuid %s))'
            % (s, P(pt[0]), P(pt[1]), size, size, U())))


SHAPE_FOR = {}      # (file, label) -> shape, filled from child sheets


def child_hier_labels(path):
    s = Schematic(path)
    out = {}
    for n in s.labels('hierarchical_label'):
        sh = child(n, 'shape')
        out[n[1]] = str(sh[1]) if sh else 'passive'
    return out


# ---------------------------------------------------------------- sheets
# table entries: (sheetkey, file, title, (x, y), (w, h), left, right)
# pin entries: (hier_name, net_label) — net None means no_connect
def build_sheets_table():
    """SHEETS is too unwieldy as a literal; build it here."""
    mcu_left = (
        [('LS%d' % i, 'LS%d_IN' % i) for i in range(1, 17)] +
        [('HS%d' % i, 'HS%d_IN' % i) for i in range(1, 5)] +
        [('IGN%d' % i, 'IGN%d_IN' % i) for i in range(1, 13)] +
        [('ETB1_PWM', 'ETB1_PWM'), ('ETB1_DIR', 'ETB1_DIR'),
         ('ETB1_DIS', 'ETB1_DIS'), ('ETB2_PWM', 'ETB2_PWM'),
         ('ETB2_DIR', 'ETB2_DIR'), ('ETB2_DIS', 'ETB2_DIS'),
         ('AUX_SPI_CS', 'AUX_SPI_CS'), ('AUX_SPI_SCK', 'AUX_SPI_SCK'),
         ('AUX_SPI_MISO', 'AUX_SPI_MISO'),
         ('AUX_SPI_MOSI', 'AUX_SPI_MOSI'),
         ('UART_TX', 'UART_TX'), ('UART_RX', 'UART_RX'),
         ('EXP_GPIO0', 'EXP_GPIO0')])
    mcu_right = (
        [('AV%d' % i, 'AV%d_F' % i) for i in range(1, 12)] +
        [('AT%d' % i, 'AT%d_F' % i) for i in range(1, 5)] +
        [('12V_SENSE', '12V_RAW')] +
        [('DIGITAL%d' % i, 'HALL_OUT_%d' % i) for i in range(1, 7)] +
        [('VR_1', 'VR1_OUT'), ('VR_2', 'VR2_OUT'),
         ('KNOCK_1', 'KNOCK1_F'), ('KNOCK_2', 'KNOCK2_F'),
         ('CAN_RX', 'CAN1_RX'), ('CAN_TX', 'CAN1_TX'),
         ('CAN2_RX', 'CAN2_RX'), ('CAN2_TX', 'CAN2_TX'),
         ('5V_SENSOR_1_PG', '5V_SENSOR_1_PG'),
         ('5V_SENSOR_2_PG', '5V_SENSOR_2_PG')])
    psu_left = [('12V_RAW', '12V_RAW')]
    psu_right = [('12v_PROT', '12v_PROT'),
                 ('5V_SENSOR_1', '5V_SENSOR_1'),
                 ('5V_SENSOR_2', '5V_SENSOR_2'),
                 ('5V_SENSOR_1_PG', '5V_SENSOR_1_PG'),
                 ('5V_SENSOR_2_PG', '5V_SENSOR_2_PG'),
                 ('CANH', 'CAN1_H'), ('CANL', 'CAN1_L'),
                 ('CANH2', 'CAN2_H'), ('CANL2', 'CAN2_L'),
                 ('RXDCAN', 'CAN1_RX'), ('TXDCAN', 'CAN1_TX'),
                 ('RXDCAN2', 'CAN2_RX'), ('TXDCAN2', 'CAN2_TX')]
    tbl = []
    tbl.append(('mcu', 'mcu.kicad_sch', 'mcu', (15, 15), (60, 130),
                mcu_left, mcu_right))
    tbl.append(('psu', 'psu.kicad_sch', 'psu', (15, 165), (50, 45),
                psu_left, psu_right))
    tbl.append(('knock', 'knock.kicad_sch', 'knock', (15, 230), (50, 20),
                [('INPUT_1', 'KNOCK_1'), ('INPUT_2', 'KNOCK_2')],
                [('FILTERED_1', 'KNOCK1_F'), ('FILTERED_2', 'KNOCK2_F')]))
    trig_left = ([('HALL_IN_%d' % i, 'DIGITAL_%d' % i)
                  for i in range(1, 7)] +
                 [('VR1+', 'VR1+'), ('VR1-', 'VR1-'),
                  ('VR2+', 'VR2+'), ('VR2-', 'VR2-'),
                  ('5V_SENSOR_SUPPLY', '5V_SENSOR_1')])
    trig_right = ([('HALL_OUT_%d' % i, 'HALL_OUT_%d' % i)
                   for i in range(1, 7)] +
                  [('VR1_OUT', 'VR1_OUT'), ('VR2_OUT', 'VR2_OUT')])
    tbl.append(('triggers', 'triggers.kicad_sch', 'triggers',
                (15, 265), (50, 40), trig_left, trig_right))
    for k in range(1, 5):
        ls = ['LS%d' % (4 * (k - 1) + i) for i in (1, 2, 3, 4)]
        tbl.append(('lowside_quad%d' % k, 'lowside_quad.kicad_sch',
                    'lowside_quad%d' % k, (100, 15 + 23 * (k - 1)),
                    (40, 15),
                    [('IN%d' % i, '%s_IN' % ls[i - 1]) for i in (1, 2, 3, 4)],
                    [('OUT%d' % i, ls[i - 1]) for i in (1, 2, 3, 4)]))
    for k in range(1, 4):
        ig = ['IGN%d' % (4 * (k - 1) + i) for i in (1, 2, 3, 4)]
        tbl.append(('ign%d' % k, 'ign_quad.kicad_sch', 'ign%d' % k,
                    (100, 107 + 23 * (k - 1)), (40, 15),
                    [('IN%d' % i, '%s_IN' % ig[i - 1]) for i in (1, 2, 3, 4)],
                    [('OUT%d' % i, ig[i - 1]) for i in (1, 2, 3, 4)]))
    tbl.append(('highside_quad', 'highside_quad.kicad_sch',
                'highside_quad', (100, 176), (40, 18),
                [('IN%d' % i, 'HS%d_IN' % i) for i in (1, 2, 3, 4)] +
                [('12V', '12V_RAW')],
                [('OUT%d' % i, 'HS%d' % i) for i in (1, 2, 3, 4)]))
    for k in (1, 2):
        tbl.append(('etb%d' % k, 'etb.kicad_sch', 'etb-%d' % k,
                    (100, 202 + 23 * (k - 1)), (40, 16),
                    [('PWM', 'ETB%d_PWM' % k), ('DIR', 'ETB%d_DIR' % k),
                     ('DIS', 'ETB%d_DIS' % k), ('12V_SUPPLY', '12V_RAW')],
                    [('OUT+', 'ETB%d+' % k), ('OUT-', 'ETB%d-' % k)]))
    for k in range(1, 4):
        avs = ['AV%d' % (4 * (k - 1) + i) for i in (1, 2, 3, 4)]
        left = [('IN%d' % i, avs[i - 1]) for i in (1, 2, 3, 4)]
        right = [('OUT%d' % i, avs[i - 1] + '_F') for i in (1, 2, 3, 4)]
        if k == 3:                       # only AV9-11 exist
            left[3] = ('IN4', None)
            right[3] = ('OUT4', None)
        tbl.append(('quad_analog%d' % k, 'quad_analog.kicad_sch',
                    'quad_analog%d' % k, (100, 248 + 23 * (k - 1)),
                    (40, 16), left, right))
    tbl.append(('quad_analog_temp', 'quad_analog_temp.kicad_sch',
                'quad_analog_temp', (100, 317), (40, 18),
                [('IN%d' % i, 'AT%d' % i) for i in (1, 2, 3, 4)] +
                [('5V_PULLUP_SUPPLY', '5V_SENSOR_1')],
                [('OUT%d' % i, 'AT%d_F' % i) for i in (1, 2, 3, 4)]))
    return tbl


# Superseal 26 local connector symbol
SUPERSEAL26 = '''
(symbol "proteus-br:Superseal26" (pin_names (offset 1.016) hide)
  (in_bom yes) (on_board yes)
  (property "Reference" "J" (at 2.54 2.54 0)
    (effects (font (size 1.27 1.27))))
  (property "Value" "Superseal26" (at 2.54 -66.04 0)
    (effects (font (size 1.27 1.27))))
  (property "Footprint" "proteus-br:TE_Superseal10_26pos_6437288-6"
    (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "https://www.te.com/en/product-6437288-6.html"
    (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "ki_description"
    "TE AMP Superseal 1.0, 26 vias, header PCB vertical 6437288-6"
    (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol "Superseal26_0_1"
    (rectangle (start -6.35 1.27) (end 8.89 -64.77)
      (stroke (width 0.254) (type default)) (fill (type background)))
  )
  (symbol "Superseal26_1_1"
%s
  )
)
''' % '\n'.join(
    '    (pin passive line (at -10.16 %s 0) (length 3.81)\n'
    '      (name "P%d" (effects (font (size 1.27 1.27))))\n'
    '      (number "%d" (effects (font (size 1.27 1.27)))))'
    % (-(n - 1) * 2.54, n, n) for n in range(1, 27))


# connector pin -> net (None = reserved/no-connect)
C1_NETS = {1: '12V_RAW', 2: '12V_RAW', 3: 'GND',
           **{p: 'LS%d' % (p - 3) for p in range(4, 12)},
           12: 'HS1', 13: 'HS2', 14: 'GND', 15: 'GND', 16: 'GND',
           **{p: 'LS%d' % (p - 8) for p in range(17, 25)},
           25: 'HS3', 26: 'HS4'}
C2_NETS = {1: 'GND', **{p: 'IGN%d' % (p - 1) for p in range(2, 8)},
           8: 'GND', 9: 'ETB1+', 10: 'ETB1-', 11: None, 12: None,
           13: 'GND', 14: 'GND',
           **{p: 'IGN%d' % (p - 8) for p in range(15, 21)},
           21: 'GND', 22: 'ETB2+', 23: 'ETB2-', 24: None, 25: None,
           26: 'GND'}
C3_NETS = {1: '5V_SENSOR_1', 2: 'GND',
           3: 'AV1', 4: 'AV2', 5: 'AV3', 6: 'AV4', 7: 'AV5', 8: 'AV6',
           9: 'GND', 10: 'AT1', 11: 'AT2', 12: 'KNOCK_1', 13: 'GND',
           14: '5V_SENSOR_2', 15: 'GND', 16: 'AV7', 17: 'AV8',
           18: 'AV9', 19: 'AV10', 20: 'AV11', 21: 'GND',
           22: 'AT3', 23: 'AT4', 24: 'KNOCK_2', 25: 'GND', 26: None}
C4_NETS = {1: '5V_SENSOR_1', 2: 'GND', 3: 'DIGITAL_1', 4: 'DIGITAL_2',
           5: 'DIGITAL_3', 6: 'DIGITAL_4', 7: 'GND',
           8: 'VR1+', 9: 'VR1-', 10: 'GND', 11: 'CAN1_H', 12: 'CAN1_L',
           13: None, 14: '5V_SENSOR_1', 15: 'GND', 16: 'DIGITAL_5',
           17: 'DIGITAL_6', 18: 'GND', 19: None, 20: 'VR2+', 21: 'VR2-',
           22: 'GND', 23: 'CAN2_H', 24: 'CAN2_L', 25: None, 26: None}
EXP_NETS = {1: '12v_PROT', 2: '12v_PROT', 3: 'GND', 4: 'GND',
            5: '+5V', 6: '+5V', 7: 'CAN2_H', 8: 'CAN2_L', 9: 'GND',
            10: 'UART_TX', 11: 'UART_RX', 12: 'GND',
            13: 'AUX_SPI_SCK', 14: 'AUX_SPI_MISO', 15: 'AUX_SPI_MOSI',
            16: 'AUX_SPI_CS', 17: '+3V3', 18: 'GND', 19: 'GND',
            20: 'EXP_GPIO0'}

CONNECTOR_META = [
    ('J101', 'C1 POTENCIA/INJECAO', (250, 15), C1_NETS,
     'housing 3-1437290-7 (key 1)'),
    ('J102', 'C2 IGNICAO/ETB', (250, 95), C2_NETS,
     'housing 3-1437290-8 (key 2)'),
    ('J103', 'C3 SENSORES', (250, 175), C3_NETS,
     'housing 26v key 3 (PN a confirmar)'),
    ('J104', 'C4 TRIGGERS/COMUNICACAO', (250, 255), C4_NETS,
     'housing 3-1437290-7 (key 1, igual C1 — decisao 5)'),
]


def clone_moved(src, ref, new_at, root, project_path):
    """Clone a symbol from another schematic, move to new_at."""
    donor = src.by_ref(ref)
    assert donor is not None, ref
    node = parse(dump(donor))
    at = child(node, 'at')
    dx, dy = P(new_at[0]) - float(at[1]), P(new_at[1]) - float(at[2])
    at[1] = type(at[1])(str(P(new_at[0])))
    at[2] = type(at[2])(str(P(new_at[1])))
    child(node, 'uuid')[1] = type(child(node, 'uuid')[1])(U())
    for pn in children(node, 'pin'):
        pu = child(pn, 'uuid')
        if pu:
            pu[1] = type(pu[1])(U())
    for p in children(node, 'property'):
        pat = child(p, 'at')
        if pat:
            pat[1] = type(pat[1])(str(P(float(pat[1]) + dx)))
            pat[2] = type(pat[2])(str(P(float(pat[2]) + dy)))
    inst = child(node, 'instances')
    if inst:
        node.remove(inst)
    node.append(parse('(instances (project "%s" (path "%s" '
                      '(reference "%s") (unit 1))))'
                      % (PROJECT, project_path, ref)))
    root.body.append(node)
    lib_id = child(node, 'lib_id')[1]
    root.lib_from(src, lib_id)
    return node


def main():
    root = Root()
    tbl = build_sheets_table()

    # ---- validate pin maps against child hierarchical labels
    for key, fname, title, at, size, left, right in tbl:
        labels = child_hier_labels(os.path.join(DST, fname))
        mapped = {n for n, _ in left} | {n for n, _ in right}
        missing = set(labels) - mapped
        extra = mapped - set(labels)
        assert not missing and not extra, (key, missing, extra)
        SHAPE_FOR[fname] = labels

    # ---- sheet instances + their pin labels
    page = 2
    for key, fname, title, (sx, sy), (w, h), left, right in tbl:
        labels = SHAPE_FOR[fname]
        pins = []
        for i, (name, net) in enumerate(left):
            y = P(sy + 2.54 * (i + 1))
            pins.append((name, labels[name], (sx, y), 180))
        for i, (name, net) in enumerate(right):
            y = P(sy + 2.54 * (i + 1))
            pins.append((name, labels[name], (P(sx + w), y), 0))
        pintxt = '\n'.join(
            '(pin "%s" %s (at %s %s %s) (effects (font (size 1.27 1.27)) '
            '(justify %s)) (uuid %s))'
            % (name, shape, pt[0], pt[1], rot,
               'left' if rot == 180 else 'right', U())
            for name, shape, pt, rot in pins)
        root.body.append(parse(
            '(sheet (at %s %s) (size %s %s) (fields_autoplaced) '
            '(stroke (width 0) (type solid)) (fill (color 0 0 0 0.0)) '
            '(uuid %s) '
            '(property "Sheetname" "%s" (at %s %s 0) (effects (font '
            '(size 1.27 1.27)) (justify left bottom))) '
            '(property "Sheetfile" "%s" (at %s %s 0) (effects (font '
            '(size 1.27 1.27)) (justify left top))) '
            '%s '
            '(instances (project "%s" (path "/%s" (page "%d")))))'
            % (sx, sy, w, h, SHEET_UUIDS[key], title, sx, P(sy - 0.7),
               fname, sx, P(sy + h + 0.7), pintxt, PROJECT, ROOT_UUID,
               page)))
        page += 1
        # attach global labels / NCs at pin points
        for i, (name, net) in enumerate(left):
            pt = (sx, P(sy + 2.54 * (i + 1)))
            if net is None:
                root.nc(pt)
            else:
                root.glabel(net, pt, 180, _glshape(labels[name]))
        for i, (name, net) in enumerate(right):
            pt = (P(sx + w), P(sy + 2.54 * (i + 1)))
            if net is None:
                root.nc(pt)
            else:
                root.glabel(net, pt, 0, _glshape(labels[name]))

    # ---- connectors
    root.add_lib('proteus-br:Superseal26', parse(SUPERSEAL26))
    for ref, value, (cx, cy), nets, housing in CONNECTOR_META:
        pins = '\n'.join('(pin "%d" (uuid %s))' % (n, U())
                         for n in range(1, 27))
        root.body.append(parse(
            '(symbol (lib_id "proteus-br:Superseal26") (at %s %s 0) '
            '(unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid %s) '
            '(property "Reference" "%s" (at %s %s 0) (effects (font '
            '(size 1.27 1.27)))) '
            '(property "Value" "%s" (at %s %s 0) (effects (font '
            '(size 1.27 1.27)))) '
            '(property "Footprint" '
            '"proteus-br:TE_Superseal10_26pos_6437288-6" (at %s %s 0) '
            '(effects (font (size 1.27 1.27)) hide)) '
            '(property "Datasheet" '
            '"https://www.te.com/en/product-6437288-6.html" (at %s %s 0) '
            '(effects (font (size 1.27 1.27)) hide)) '
            '(property "LCSC" "" (at %s %s 0) (effects (font '
            '(size 1.27 1.27)) hide)) '
            '(property "MFN" "TE Connectivity" (at %s %s 0) (effects '
            '(font (size 1.27 1.27)) hide)) '
            '(property "MPN" "6437288-6" (at %s %s 0) (effects (font '
            '(size 1.27 1.27)) hide)) '
            '(property "Mating" "%s" (at %s %s 0) (effects (font '
            '(size 1.27 1.27)) hide)) '
            '%s '
            '(instances (project "%s" (path "/%s" (reference "%s") '
            '(unit 1)))))'
            % (cx, cy, U(), ref, P(cx + 2.5), P(cy - 2.5),
               value, P(cx + 2.5), P(cy + 67),
               cx, cy, cx, cy, cx, cy, cx, cy, cx, cy,
               housing, cx, cy, pins, PROJECT, ROOT_UUID, ref)))
        for n in range(1, 27):
            pt = (P(cx - 10.16), P(cy + (n - 1) * 2.54))
            net = nets[n]
            if net is None:
                root.nc(pt)
            elif net == 'GND':
                root.glabel('GND', pt, 180)
            else:
                root.glabel(net, pt, 180)

    # ---- expansion header (official generic symbol Conn_02x10_Odd_Even)
    with open('/usr/share/kicad/symbols/Connector_Generic.kicad_sym') as f:
        libtree = parse(f.read())
    conn = None
    for sym in children(libtree, 'symbol'):
        if sym[1] == 'Conn_02x10_Odd_Even':
            conn = parse(dump(sym))
            break
    assert conn is not None
    conn[1] = 'Connector_Generic:Conn_02x10_Odd_Even'
    root.add_lib('Connector_Generic:Conn_02x10_Odd_Even', conn)
    ex, ey = 250, 340
    pins = '\n'.join('(pin "%d" (uuid %s))' % (n, U())
                     for n in range(1, 21))
    root.body.append(parse(
        '(symbol (lib_id "Connector_Generic:Conn_02x10_Odd_Even") '
        '(at %s %s 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) '
        '(uuid %s) '
        '(property "Reference" "J110" (at %s %s 0) (effects (font '
        '(size 1.27 1.27)))) '
        '(property "Value" "EXPANSAO LINUX 2x10" (at %s %s 0) (effects '
        '(font (size 1.27 1.27)))) '
        '(property "Footprint" '
        '"Connector_IDC:IDC-Header_2x10_P2.54mm_Vertical" (at %s %s 0) '
        '(effects (font (size 1.27 1.27)) hide)) '
        '(property "Datasheet" "~" (at %s %s 0) (effects (font '
        '(size 1.27 1.27)) hide)) '
        '(property "MFN" "generico" (at %s %s 0) (effects (font '
        '(size 1.27 1.27)) hide)) '
        '(property "MPN" "box header IDC 2x10 2.54mm" (at %s %s 0) '
        '(effects (font (size 1.27 1.27)) hide)) '
        '%s '
        '(instances (project "%s" (path "/%s" (reference "J110") '
        '(unit 1)))))'
        % (ex, ey, U(), P(ex + 2.5), P(ey - 5),
           ex, P(ey + 30), ex, ey, ex, ey, ex, ey, ex, ey,
           pins, PROJECT, ROOT_UUID)))
    # find the actual pin contact points via a temp Schematic-like lookup
    tmp = Schematic.__new__(Schematic)
    tmp.path = OUT
    tmp.tree = parse('(kicad_sch (lib_symbols %s) %s)' % (
        dump(conn), dump(root.body[-1])))
    tmp._lib = {'Connector_Generic:Conn_02x10_Odd_Even': conn}
    symnode = child(tmp.tree, 'symbol')
    for n in range(1, 21):
        pt = tmp.pin_pos(symnode, str(n))
        assert pt is not None, n
        rot = 180 if pt[0] < ex else 0
        net = EXP_NETS[n]
        root.glabel(net, pt, rot)

    # ---- 12V input parts cloned from the original root
    orig = load('proteus.kicad_sch')
    pwr_path = '/%s' % ROOT_UUID
    f1 = clone_moved(orig, 'F101', (190, 385), root, pwr_path)
    f2 = clone_moved(orig, 'F102', (200, 385), root, pwr_path)
    c17 = clone_moved(orig, 'C17', (215, 385), root, pwr_path)
    tmp2 = Schematic.__new__(Schematic)
    tmp2.tree = parse('(kicad_sch (lib_symbols %s) )'
                      % ' '.join(dump(v) for v in root.libs.values()))
    tmp2._lib = root.libs   # live ref: clones add libs as they come

    def pinpt(node, num):
        return Schematic.pin_pos(tmp2, node, num)

    for node, nets in ((f1, ('12V_RAW', '12v_PROT')),
                       (f2, ('12V_RAW', '12v_PROT')),
                       (c17, ('12V_RAW', 'GND'))):
        for num, net in zip(('1', '2'), nets):
            pt = pinpt(node, num)
            assert pt is not None
            root.glabel(net, pt, 0)
    # freewheel diodes for LS13-16 (solenoid channels) — DNP fase 1
    for i, ref in enumerate(('D101', 'D102', 'D103', 'D104')):
        node = clone_moved(orig, ref, (170 + 12 * i, 400), root, pwr_path)
        Schematic.set_dnp(node, True)
        Schematic.add_property(node, 'DNP', 'DNP fase 1 — LS13-16')
        # original anode net was 12V_MR; BR uses the raw fused rail
        k = pinpt(node, '1')
        a = pinpt(node, '2')
        ls = {'D103': 'LS13', 'D101': 'LS14', 'D104': 'LS15',
              'D102': 'LS16'}[ref]
        root.glabel(ls, k, 0)
        root.glabel('12V_RAW', a, 0)

    # ---- PWR_FLAGs (nets driven by passive parts need them for ERC)
    root.lib_from(orig, 'power:PWR_FLAG')
    for i, net in enumerate(('12V_RAW', '12v_PROT', 'GND',
                             '5V_SENSOR_1', '5V_SENSOR_2', '+5V')):
        x = P(170 + 18 * i)
        ref = '#FLG010%d' % i
        root.body.append(parse(
            '(symbol (lib_id "power:PWR_FLAG") (at %s 370 0) (unit 1) '
            '(in_bom yes) (on_board yes) (dnp no) (uuid %s) '
            '(property "Reference" "%s" (at %s 366 0) (effects (font '
            '(size 1.27 1.27)) hide)) '
            '(property "Value" "PWR_FLAG" (at %s 364 0) (effects (font '
            '(size 1.27 1.27)))) '
            '(property "Footprint" "" (at %s 370 0) (effects (font '
            '(size 1.27 1.27)) hide)) '
            '(property "Datasheet" "~" (at %s 370 0) (effects (font '
            '(size 1.27 1.27)) hide)) '
            '(pin "1" (uuid %s)) '
            '(instances (project "%s" (path "/%s" (reference "%s") '
            '(unit 1)))))'
            % (x, U(), ref, x, x, x, x, U(), PROJECT, ROOT_UUID, ref)))
        root.glabel(net, (x, 370), 0)

    # ---- notes
    root.text('PROTEUS-BR v1 — raiz. Conectores TE Superseal 1.0 26v '
              '(headers 6437288-6). Keying: C1=key1, C2=key2, C3=key3, '
              'C4=key1 repetido (decisao 5 — afastado do C1, housing de '
              'cor distinta).', (15, 395), 2.0)
    root.text('Limite assumido: 5 A continuos por pino (PREMISSA '
              'conservadora; terminal 18 AWG 3-1447221-3). Potencia '
              'sempre em pinos paralelados (12V_RAW e GND no C1).',
              (15, 400), 1.5)
    root.text('Populacao fase 1 por instancia (DNP gerenciado na BOM de '
              'montagem — KiCad nao tem DNP por instancia de folha): '
              'lowside_quad3/4 (LS9-16) NAO populadas; ign2/ign3 '
              '(IGN5-12) NAO populadas; quad_analog3 (AV9-11) NAO '
              'populada; highside_quad e etb-1/etb-2 inteiras NAO '
              'populadas.', (15, 405), 1.5)
    root.text('ETB: 1 pino por fase no C2 (decisao 8) — pico 6 A '
              'transitorio aceito; reservas 11/12/24/25 do C2 seladas '
              'com tampao 4-1437284-3.', (15, 410), 1.5)
    root.text('12V: C1.1-2 (12V_RAW, fusivel externo no chicote) -> '
              'TVS SM15T33CA (psu) + bulk C17; polyfuses F101||F102 -> '
              '12v_PROT (buck, trackers, expansao). Highside/ETB/roda-'
              'livre direto no 12V_RAW.', (15, 415), 1.5)

    # ---- assemble file
    libtxt = '\n'.join(dump(v, 1) for v in root.libs.values())
    bodytxt = '\n'.join(dump(n) for n in root.body)
    content = (
        '(kicad_sch (version 20230121) (generator eeschema)\n'
        '  (uuid %s)\n'
        '  (paper "A2")\n'
        '  (title_block\n'
        '    (title "Proteus-BR")\n'
        '    (date "2026-06-11")\n'
        '    (rev "v1")\n'
        '    (company "baseado em rusEFI Proteus v0.7")\n'
        '    (comment 1 "SPEC-FREEZE docs/proteus-br/SPEC-FREEZE.md")\n'
        '    (comment 2 "PINOUT-CONTRACT.csv = fonte unica dos pinos")\n'
        '  )\n'
        '  (lib_symbols\n%s\n  )\n'
        '%s\n'
        '  (sheet_instances (path "/" (page "1")))\n'
        ')\n' % (ROOT_UUID, libtxt, bodytxt))
    with open(OUT, 'w') as f:
        f.write(content)
    print('wrote', OUT)


def _glshape(hshape):
    # global label shapes: input/output/bidirectional/tri_state/passive
    return hshape if hshape in ('input', 'output', 'bidirectional',
                                'passive') else 'passive'


if __name__ == '__main__':
    main()
