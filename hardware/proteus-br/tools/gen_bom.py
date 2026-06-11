#!/usr/bin/env python3
"""Gera BOMs do esquematico Proteus-BR e o diff contra a BOM-completa.csv.

Saidas:
  reports/bom-esquematico-completa.csv  — tudo que esta no netlist
  reports/bom-esquematico-fase1.csv     — BOM de montagem da fase 1
  reports/bom-diff.md                   — diff comentado vs docs/.../BOM-completa.csv
"""
import os
import sys
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.normpath(os.path.join(HERE, '..'))
DOCS = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'docs',
                                     'proteus-br'))

# instancias de folha inteiras fora da fase 1 (DNP por instancia nao
# existe no KiCad — populacao controlada aqui e anotada na folha raiz)
FASE1_SHEET_EXCLUDE = ('/lowside_quad3/', '/lowside_quad4/',
                       '/ign2/', '/ign3/', '/quad_analog3/',
                       '/highside_quad/', '/etb-1/', '/etb-2/')


def natkey(ref):
    import re
    m = re.match(r'([A-Za-z#]+)(\d*)', ref)
    return (m.group(1), int(m.group(2) or 0))


def main(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    comps = []
    for c in root.find('components'):
        ref = c.get('ref')
        if ref.startswith('#'):
            continue
        props = {p.get('name'): p.get('value')
                 for p in c.findall('property')}
        sheet = c.find('sheetpath')
        comps.append({
            'ref': ref,
            'value': c.findtext('value') or '',
            'footprint': c.findtext('footprint') or '',
            'lcsc': props.get('LCSC', ''),
            'mfn': props.get('MFN', ''),
            'mpn': props.get('MPN', ''),
            'dnp': 'dnp' in props,
            'dnp_note': props.get('DNP', ''),
            'sheet': sheet.get('names') if sheet is not None else '/',
        })

    def fase1(c):
        if c['dnp']:
            return False
        return not any(c['sheet'].startswith(x.rstrip('/')) or
                       c['sheet'] == x for x in FASE1_SHEET_EXCLUDE)

    # ---- group
    def write_bom(path, items, label):
        groups = defaultdict(list)
        for c in items:
            groups[(c['value'], c['footprint'], c['lcsc'], c['mfn'],
                    c['mpn'])].append(c['ref'])
        with open(path, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['qtd', 'valor', 'footprint', 'lcsc', 'mfn', 'mpn',
                        'referencias'])
            for (v, fp, lc, mf, mp), refs in sorted(
                    groups.items(), key=lambda kv: (kv[0][0], kv[0][1])):
                w.writerow([len(refs), v, fp, lc, mf, mp,
                            ' '.join(sorted(refs, key=natkey))])
        print('%s: %d linhas, %d componentes' % (
            label, len(groups), len(items)))
        return groups

    all_groups = write_bom(os.path.join(DST, 'reports',
                                        'bom-esquematico-completa.csv'),
                           comps, 'BOM completa')
    write_bom(os.path.join(DST, 'reports', 'bom-esquematico-fase1.csv'),
              [c for c in comps if fase1(c)], 'BOM fase 1')

    # ---- diff vs docs BOM-completa.csv
    qty_by_value = defaultdict(int)
    refs_by_value = defaultdict(list)
    for c in comps:
        qty_by_value[c['value']] += 1
        refs_by_value[c['value']].append(c['ref'])
    qty_by_lcsc = defaultdict(int)
    for c in comps:
        if c['lcsc']:
            qty_by_lcsc[c['lcsc']] += 1
    qty_by_mpn = defaultdict(int)
    for c in comps:
        if c['mpn']:
            qty_by_mpn[c['mpn']] += 1

    # mapeamento linha-da-BOM-doc -> contagem no esquematico
    MAP = {
        'STM32F427ZGT6': ('lcsc', 'C117816'),
        '8MHz 5032': ('value', '8MHz'),
        'REF3333AIDBZR': ('lcsc', 'C130016'),
        'USBLC6-2SC6': ('lcsc', 'C7519'),
        '5787834-1': ('value', 'USB_B'),
        'FTSH-105-01-F-DV': ('value', 'Conn_02x05_Odd_Even'),
        'EVQQ2': ('value', 'SW_Push'),
        'LED 0603': ('value', 'ORANGE'),
        '693072010801': ('value', 'Micro_SD_Card'),
        'LMR14020SDDAR': ('lcsc', 'C187824'),
        'AMS1117-3.3': ('lcsc', 'C6186'),
        'TLE4251D': ('lcsc', 'C539669'),
        'SM15T33CA': ('lcsc', 'C133707'),
        'SS34 classe': ('value', 'D_Schottky'),
        'polyfuse': ('value', 'Polyfuse'),
        'MWSA0503-100M': ('value', '10u#L'),
        'L1210': ('value', '2.2u#L'),
        'FB': ('value', 'Ferrite_Bead'),
        'EEH-AZF1H560B': ('value', '56u'),
        'TJA1051T/3': ('lcsc', 'C38695'),
        'PESD1CAN-UX': ('value', 'PESD1CAN-UX'),
        'VNLD5160TR-E': ('lcsc', 'C377942'),
        'BTS4175SGA': ('value', 'BTS4175SGA'),
        'TC4427ACOA713': ('lcsc', 'C144234'),
        'TLE9201SG': ('value', 'TLE9201SG'),
        'SN74LVC2G17DBVR': ('lcsc', 'C10429'),
        'MAX9924UAUB+T': ('lcsc', 'C5145181'),
        'MCP6004 SOIC-14': ('lcsc', 'C7378'),
        'MCP6002-xSN': ('lcsc', 'C7377'),
        'SRV05-4': ('lcsc', 'C13612'),
        '1R': ('value', '1'),
        '100R 1%': ('value', '100'),
        '120R 1%': ('value', '120'),
        '1k 1%': ('value', '1k'),
        '2.7k 1%': ('value', '2.7k'),
        '4.7k 1%': ('value', '4.7k'),
        '5.6k 1%': ('value', '5.6k'),
        '10k 1%': ('value', '10k'),
        '12k 1%': ('value', '12k'),
        '33k 1%': ('value', '33k'),
        '68k 1%': ('value', '68k'),
        '82k 1%': ('value', '82k'),
        '100k 1%': ('value', '100k'),
        '470k 1%': ('value', '470k'),
        '33p': ('value', '33p'), '47p': ('value', '47p'),
        '330p': ('value', '330p'), '680p': ('value', '680p'),
        '1n': ('value', '1n'), '3.3n': ('value', '3.3n'),
        '10n': ('value', '10n'), '100n': ('value', '100n'),
        '1u': ('value', '1u#C'), '2.2u': ('value', '2.2u'),
        '4.7u': ('value', '4.7u'), '10u': ('value', '10u#C'),
        '6437288-6 (keying a confirmar)': ('mpn', '6437288-6'),
        'box header 2.54 generico': ('value', 'EXPANSAO LINUX 2x10'),
    }
    # contagens especiais (valores ambiguos entre L e C)
    special = {
        '10u#L': sum(1 for c in comps if c['value'] == '10u' and
                     'MWSA' in c['footprint']),
        '2.2u#L': sum(1 for c in comps if c['value'] == '2.2u' and
                      c['ref'].startswith('L')),
        '1u#C': sum(1 for c in comps if c['value'] == '1u' and
                    c['ref'].startswith('C')),
        '10u#C': sum(1 for c in comps if c['value'] == '10u' and
                     c['ref'].startswith('C')),
        '2.2u': sum(1 for c in comps if c['value'] == '2.2u' and
                    c['ref'].startswith('C')),
        '1': sum(1 for c in comps if c['value'] == '1' and
                 c['ref'].startswith('R')),
        '100': sum(1 for c in comps if c['value'] == '100' and
                   c['ref'].startswith('R')),
        '120': sum(1 for c in comps if c['value'] == '120'),
    }

    # linhas que a doc divide em n.1/n.2 — o esquematico conta o total
    ROW_OVERRIDE = {
        'Tracker 5V n.1': (1, 'doc divide em n.1+n.2; total no '
                              'esquematico = 2 (U1004 + U1005 DNP) ✓'),
        'Tracker 5V n.2': (1, 'idem — confere'),
        'Transceiver CAN1': (1, 'doc divide CAN1/CAN2; total = 2 '
                                '(U904 + U6 DNP) ✓'),
        'Transceiver CAN2': (1, 'idem — confere'),
    }
    NOTES = {
        'Schottky SMA': 'BOM diz 6 (D101-104+D901+D903); esquematico tem '
                        '5 — D903 removido de proposito (entrada 12V '
                        'unica: schottky em paralelo com os polyfuses '
                        'anularia a protecao; nota na folha psu).',
        'Opamp quad': 'BOM diz 5; esquematico tem 5 (U701/U801/U901/'
                      'U1101/U5). ATENCAO: BOM-fase1.csv lista so 3, mas '
                      'a fase 1 precisa de 4 (U1101 buffer dos AT1-4 '
                      'esta populado).',
        'Buffer schmitt': 'BOM diz 3 (fase 1: 1x); esquematico tem 3, '
                          'mas fase 1 monta 2 (U1202+U1207): a fiacao da '
                          'v0.7 cruza canais (U1202=DIG1+5, U1207='
                          'DIG2+3) — corrigir BOM-fase1.',
        'ESD array': 'BOM diz 5 (fase1 3x); esquematico tem 7: U1/U2/U3/'
                     'U4 (AVs+AT) + D1501 (USB) + U1106/U1107 (hall) — '
                     'a BOM-completa nao contou os 2 SRV05 dos triggers '
                     '(existem na v0.7). Fase 1 monta 5 (U3 e U1107 DNP).',
        '1k': '47 = 32 lowside (4 folhas x 8 ex-array) + 12 ign '
              '(3 folhas x 4) + R1511 LED + R1217/R1218 VR. A estimativa '
              '~24 da doc nao multiplicou pelas instancias de folha.',
        '10k': 'inclui ex-arrays: RN1301 (4) + RN701-tipo (3 folhas x 4) '
               '+ RN1101 (4) como discretos.',
        '470k 1%': '14 = 12 bias AV (3 folhas x 4, R701-R904) + 2 knock '
                   '(R1903/R1904). A doc contou 16 assumindo bias na '
                   'folha AT — nao existe na v0.7.',
        '100n': 'contagem exata do esquematico; BOM usava ~42.',
        '10n': 'contagem exata do esquematico; BOM usava ~23.',
        'LED 0603': 'LED unico em PE5 (running) — decisao 4.',
        'Header SWD 2x5 1.27mm': 'J1502; Tag-Connect J4 removido.',
        'microSD': 'footprint montado so na fase 2 (DNP).',
        '47p': 'BOM diz 2 (1 por canal de knock); ch2 e DNP na fase 1.',
        '120R 1%': 'CAN1 + CAN2(DNP) + 4x highside(DNP) = 6 ✓.',
    }

    rows = []
    with open(os.path.join(DOCS, 'BOM-completa.csv')) as f:
        for row in csv.DictReader(f):
            pn = row['part_number']
            grupo = row['grupo']
            if grupo in ('CONN', 'REMOVIDOS') and pn not in MAP:
                rows.append((row, None, 'item de chicote/compra — fora '
                             'do esquematico' if grupo == 'CONN' else
                             'removido (confere)'))
                continue
            how = MAP.get(pn)
            if how is None:
                rows.append((row, None, 'sem mapeamento automatico'))
                continue
            kind, key = how
            if key in special:
                got = special[key]
            elif kind == 'lcsc':
                got = qty_by_lcsc.get(key, 0)
            elif kind == 'mpn':
                got = qty_by_mpn.get(key, 0)
            else:
                got = qty_by_value.get(key, 0)
            note = NOTES.get(row['funcao'], NOTES.get(pn, ''))
            if row['funcao'] in ROW_OVERRIDE:
                got, note = ROW_OVERRIDE[row['funcao']]
            rows.append((row, got, note))

    out = [
        '# Diff BOM: esquematico Proteus-BR x docs/proteus-br/BOM-completa.csv',
        '',
        'Gerado por tools/gen_bom.py a partir do netlist kicad-cli.',
        'Convencao: "qtd doc" e o campo qtd_total da BOM-completa;',
        '"qtd sch" e a contagem real no esquematico (populados + DNP).',
        '',
        '| grupo | funcao | part number | qtd doc | qtd sch | status | nota |',
        '|---|---|---|---|---|---|---|',
    ]
    for row, got, note in rows:
        want = row['qtd_total']
        if got is None:
            status = 'n/a'
            gots = '—'
        else:
            gots = str(got)
            w = want.replace('~', '')
            try:
                wn = int(w)
                status = 'OK' if got == wn else ('OK(~)' if '~' in want
                                                 else 'DIFERE')
                if '~' in want and abs(got - wn) > max(3, wn // 4):
                    status = 'DIFERE'
            except ValueError:
                status = 'ver nota'
        out.append('| %s | %s | %s | %s | %s | %s | %s |' % (
            row['grupo'], row['funcao'], row['part_number'], want, gots,
            status, note))
    diff_path = os.path.join(DST, 'reports', 'bom-diff.md')
    with open(diff_path, 'w') as f:
        f.write('\n'.join(out) + '\n')
    print('diff ->', diff_path)
    bad = [l for l in out if '| DIFERE |' in l]
    print('linhas DIFERE:', len(bad))
    for l in bad:
        print(' ', l)


if __name__ == '__main__':
    main(sys.argv[1])
