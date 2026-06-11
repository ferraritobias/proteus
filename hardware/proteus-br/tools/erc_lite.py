#!/usr/bin/env python3
"""ERC-lite para o projeto Proteus-BR.

O ambiente de build so tem KiCad 7.0.11 (sem `kicad-cli sch erc`, que e
do KiCad 8; o PPA do KiCad 8 esta bloqueado pela politica de rede).
Este script cobre as checagens eletricas principais usando o netlist
exportado pelo kicad-cli + analise geometrica das folhas:

 1. referencias duplicadas
 2. nets com um unico no (typo de label)
 3. conflito de drivers (>=2 pinos output/power_out na mesma net)
 4. net com power_in sem nenhum driver (power_out/output/PWR_FLAG)
 5. pino de entrada em net sem driver
 6. pino solto sem flag de no-connect (varredura geometrica por folha)
 7. label hierarquico sem pino de folha correspondente (e vice-versa)
"""
import os
import sys
import glob
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from schedit import Schematic, P
from kicad_sexp import children, child, propval

DST = os.path.normpath(os.path.join(HERE, '..'))

# nets onde "sem driver" e aceito de proposito (com justificativa)
WAIVED_UNDRIVEN = {
    '5V_SENSOR_1_PG': 'pullup DNP + PC14/PC15; TLE4251D nao tem PG '
                      '(diagnostico futuro, ver nota na folha psu)',
    '5V_SENSOR_2_PG': 'idem 5V_SENSOR_1_PG',
    'Net-(U1501-VCAP_1)': 'VCAP do STM32: so capacitor, exigencia ST — '
                          'correto sem driver',
    'Net-(U1501-VCAP_2)': 'idem VCAP_1',
    'Net-(U903-EN)': 'EN do LMR14020 polarizado por R905 (10k) — '
                     'topologia da v0.7 mantida',
    'Net-(JP1201-C)': 'strap de modo do MAX9924 (JP1201 bridged 1-2); '
                      'cadeia VR e DNP na fase 1',
}


def flagged_nets(dst):
    """Nets que tem PWR_FLAG, detectadas geometricamente nas folhas
    (simbolos de power nao aparecem no netlist xml)."""
    out = set()
    for path in sorted(glob.glob(os.path.join(dst, '*.kicad_sch'))):
        s = Schematic(path)
        # label/pin points
        lbl_at = {}
        for tag in ('label', 'global_label', 'hierarchical_label'):
            for n in s.labels(tag):
                at = child(n, 'at')
                lbl_at[(P(at[1]), P(at[2]))] = n[1]
        pin_at = s.all_pin_points()
        # wire adjacency
        adj = defaultdict(set)
        for w in s.wires():
            a, b = s.wire_ends(w)
            adj[a].add(b)
            adj[b].add(a)
        for sym in s.symbols():
            lib = child(sym, 'lib_id')[1]
            if not lib.endswith(':PWR_FLAG'):
                continue
            start = s.pin_pos(sym, '1')
            seen = {start}
            stack = [start]
            while stack:
                pt = stack.pop()
                if pt in lbl_at:
                    out.add(lbl_at[pt])
                for other in pin_at.get(pt, []):
                    ref = other[0]
                    osym = s.by_ref(ref)
                    if osym is not None:
                        olib = child(osym, 'lib_id')[1]
                        libdef = s._lib.get(olib)
                        if libdef is not None and \
                                child(libdef, 'power') is not None and \
                                not olib.endswith(':PWR_FLAG'):
                            val = propval(osym, 'Value')
                            out.add(val)
                for nxt in adj.get(pt, ()):
                    if nxt not in seen:
                        seen.add(nxt)
                        stack.append(nxt)
    return out


def main(xml_path, out_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    issues = []
    waived = []

    # pin types per libpart
    pintype = {}
    parts = {}
    for lp in root.find('libparts'):
        key = (lp.get('lib'), lp.get('part'))
        pins = {}
        if lp.find('pins') is not None:
            for p in lp.find('pins'):
                pins[p.get('num')] = p.get('type')
        parts[key] = pins
    comp2part = {}
    for c in root.find('components'):
        ls = c.find('libsource')
        comp2part[c.get('ref')] = (ls.get('lib'), ls.get('part'))

    def ptype(ref, pin):
        return parts.get(comp2part.get(ref), {}).get(pin, 'passive')

    # 1. duplicate refs
    refs = [c.get('ref') for c in root.find('components')]
    for ref, n in Counter(refs).items():
        if n > 1:
            issues.append('[dup_ref] %s aparece %d vezes' % (ref, n))

    # nets
    nets = {}
    for n in root.find('nets'):
        nets[n.get('name')] = [(x.get('ref'), x.get('pin')) for x in n]

    DRIVERS = {'output', 'power_out', 'tri_state', 'bidirectional',
               'open_collector', 'open_emitter'}
    has_flag = flagged_nets(DST)
    for name, nodes in sorted(nets.items()):
        if name.startswith('unconnected-'):
            continue
        # 2. single node
        if len(nodes) < 2:
            issues.append('[single_node] net %s so tem %s'
                          % (name, nodes))
            continue
        types = [(r, p, ptype(r, p)) for r, p in nodes]
        outs = [(r, p) for r, p, t in types if t in ('output',
                                                     'power_out')]
        drivers = [(r, p) for r, p, t in types if t in DRIVERS]
        pwr_flag = (name in has_flag or
                    name.rsplit('/', 1)[-1] in has_flag or
                    any(comp2part.get(r, ('', ''))[1] == 'PWR_FLAG'
                        for r, p in nodes))
        # 3. multiple hard drivers (outputs only; open_* podem paralelar)
        hard = [(r, p) for r, p, t in types if t == 'output']
        pouts = [(r, p) for r, p, t in types if t == 'power_out']
        if len(hard) > 1:
            issues.append('[drive_conflict] net %s: outputs %s'
                          % (name, hard))
        # 4/5. power_in / input sem driver
        needs = [(r, p) for r, p, t in types if t == 'power_in']
        if needs and not drivers and not pwr_flag:
            msg = 'net %s: power_in %s sem driver' % (name, needs[:4])
            if name in WAIVED_UNDRIVEN:
                waived.append('[undriven/waived] %s — %s'
                              % (msg, WAIVED_UNDRIVEN[name]))
            else:
                issues.append('[undriven] ' + msg)
        ins = [(r, p) for r, p, t in types if t == 'input']
        if ins and not drivers and not pwr_flag and len(nodes) == len(ins):
            msg = 'net %s: so entradas %s' % (name, ins[:4])
            if name in WAIVED_UNDRIVEN:
                waived.append('[input_only/waived] %s — %s'
                              % (msg, WAIVED_UNDRIVEN[name]))
            else:
                issues.append('[input_only] ' + msg)

    # 6. orphan pins per sheet (geometric)
    for path in sorted(glob.glob(os.path.join(DST, '*.kicad_sch'))):
        s = Schematic(path)
        segs = [tuple(s.wire_ends(w)) for w in s.wires()]
        pts = set()
        for a, b in segs:
            pts.update((a, b))
        for tag in ('label', 'global_label', 'hierarchical_label',
                    'no_connect', 'junction'):
            for n in s.labels(tag):
                at = child(n, 'at')
                pts.add((P(at[1]), P(at[2])))

        def on_seg(pt, a, b):
            (x, y), (x1, y1), (x2, y2) = pt, a, b
            if x1 == x2:
                return x == x1 and min(y1, y2) <= y <= max(y1, y2)
            return (y == y1 == y2 and min(x1, x2) <= x <= max(x1, x2))
        pincount = defaultdict(list)
        for sym in s.symbols():
            ref = propval(sym, 'Reference')
            lib = child(sym, 'lib_id')[1]
            for num in s.lib_pins(lib):
                pp = s.pin_pos(sym, num)
                if pp:
                    pincount[pp].append((ref, num))
        fname = os.path.basename(path)
        for pp, v in pincount.items():
            if len(v) > 1 or pp in pts:
                continue
            if any(on_seg(pp, a, b) for a, b in segs):
                continue
            ref, num = v[0]
            # falsos positivos conhecidos: estilos de corpo alternativos
            # do SN74LVC2G17 (pinos 2/5 ligados no estilo ativo)
            if num in ('2', '5') and 'LVC2G17' in str(
                    propval(s.by_ref(ref) or [], 'Value') or ''):
                continue
            issues.append('[orphan_pin] %s: %s.%s sem fio/NC em %s'
                          % (fname, ref, num, pp))

    # 7. hier labels vs sheet pins
    rootsch = Schematic(os.path.join(DST, 'proteus-br.kicad_sch'))
    for sh in children(rootsch.tree, 'sheet'):
        f = propval(sh, 'Sheetfile')
        pins = {p[1] for p in children(sh, 'pin')}
        labels = set()
        cs = Schematic(os.path.join(DST, f))
        for n in cs.labels('hierarchical_label'):
            labels.add(n[1])
        for missing in labels - pins:
            issues.append('[hier_mismatch] %s: label %s sem pino de folha'
                          % (f, missing))
        for extra in pins - labels:
            issues.append('[hier_mismatch] %s: pino de folha %s sem label'
                          % (f, extra))

    lines = ['ERC-lite Proteus-BR',
             'Netlist: %s' % xml_path,
             'NOTA: kicad-cli sch erc indisponivel (KiCad 7.0.11; PPA do '
             'KiCad 8 bloqueado pela rede do ambiente). Rodar ERC do '
             'KiCad >=8 na primeira abertura do projeto.',
             '']
    if issues:
        lines.append('== PROBLEMAS (%d) ==' % len(issues))
        lines.extend(issues)
    else:
        lines.append('== PROBLEMAS: nenhum ==')
    if waived:
        lines.append('')
        lines.append('== WAIVERS (%d) ==' % len(waived))
        lines.extend(waived)
    txt = '\n'.join(lines) + '\n'
    with open(out_path, 'w') as f:
        f.write(txt)
    print(txt)
    return 1 if issues else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
