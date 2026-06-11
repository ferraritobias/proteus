#!/usr/bin/env python3
"""Valida o netlist gerado contra o PINOUT-CONTRACT.csv, pino a pino.

Uso: validate_contract.py <netlist.xml> <saida.txt>

Checagens:
 1. Cada pino do STM32F427 com funcao no contrato esta na net esperada.
 2. Pinos livres do contrato estao desconectados (ou na excecao documentada).
 3. Cada pino dos conectores C1-C4 e da expansao esta na net esperada
    (tabelas iguais as dos YAML docs/proteus-br/connectors/*.yaml).
 4. Continuidade conector->MCU por nome de net (LSx, AVx, ...).
"""
import sys
import os
import csv
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_root import C1_NETS, C2_NETS, C3_NETS, C4_NETS, EXP_NETS

CONTRACT = os.path.join(HERE, '..', '..', '..', 'docs', 'proteus-br',
                        'PINOUT-CONTRACT.csv')

# net esperada por pino do MCU (None = deve estar desconectado;
# 'substr:X' = nome da net deve conter X)
EXPECTED = {}
for i in range(1, 17):
    pin = ['PD7', 'PG9', 'PG10', 'PG11', 'PG12', 'PG13', 'PG14', 'PB4',
           'PB5', 'PB6', 'PB7', 'PB8', 'PB9', 'PE0', 'PE1', 'PE2'][i - 1]
    EXPECTED[pin] = 'LS%d_IN' % i
for i, pin in enumerate(['PD4', 'PD3', 'PC9', 'PC8', 'PC7', 'PG8', 'PG7',
                         'PG6', 'PG5', 'PG4', 'PG3', 'PG2'], start=1):
    EXPECTED[pin] = 'IGN%d_IN' % i
EXPECTED.update({'PA9': 'HS1_IN', 'PA8': 'HS2_IN', 'PD15': 'HS3_IN',
                 'PD14': 'HS4_IN',
                 'PD12': 'ETB1_PWM', 'PD10': 'ETB1_DIR',
                 'PD11': 'ETB1_DIS', 'PD13': 'ETB2_PWM',
                 'PD9': 'ETB2_DIR', 'PD8': 'ETB2_DIS'})
for i, pin in enumerate(['PC0', 'PC1', 'PC2', 'PC3', 'PA0', 'PA1', 'PA2',
                         'PA3', 'PA4', 'PA5', 'PA6'], start=1):
    EXPECTED[pin] = 'AV%d_F' % i
for i, pin in enumerate(['PC4', 'PC5', 'PB0', 'PB1'], start=1):
    EXPECTED[pin] = 'AT%d_F' % i
for i, pin in enumerate(['PC6', 'PE11', 'PE12', 'PE14', 'PE13', 'PE15'],
                        start=1):
    EXPECTED[pin] = 'HALL_OUT_%d' % i
EXPECTED.update({
    'PE7': 'VR1_OUT', 'PE8': 'VR2_OUT',
    'PF4': 'KNOCK1_F', 'PF5': 'KNOCK2_F',
    'PD0': 'CAN1_RX', 'PD1': 'CAN1_TX',
    'PB12': 'CAN2_RX', 'PB13': 'CAN2_TX',
    'PA11': 'substr:USB_D-', 'PA12': 'substr:USB_D+',
    'PA13': 'substr:SWDIO', 'PA14': 'substr:SWCLK',
    'PA7': 'substr:12V_DIVIDED',
    'PC10': 'substr:SD_SCK', 'PC11': 'substr:SD_MISO',
    'PC12': 'substr:SD_MOSI', 'PD2': 'substr:SD_CS',
    'PD5': 'UART_TX', 'PD6': 'UART_RX',
    'PF7': 'AUX_SPI_SCK', 'PF8': 'AUX_SPI_MISO', 'PF9': 'AUX_SPI_MOSI',
    'PG15': 'AUX_SPI_CS', 'PG0': 'EXP_GPIO0',
    'PE5': 'substr:LED3',
    'PC14': '5V_SENSOR_2_PG', 'PC15': '5V_SENSOR_1_PG',
    'PB2': 'GND',                       # BOOT1 strap
    'BOOT0': 'substr:BOOT0',
    'NRST': 'substr:nRESET',
    'PH0': 'substr:PH0', 'PH1': 'substr:PH1',
})
# desvios deliberados da BR (documentados no SPEC-FREEZE / decisoes):
#   PE3/PE4/PE6: LEDs removidos (decisao 4, LED unico em PE5)
#   PB10/PB11:  LPS25HB removido de vez (secao F do SPEC-FREEZE)
#   PF6:        era AUX_SPI_CS no original; CS foi para PG15 (decisao 9)
EXPECT_NC = ['PE3', 'PE4', 'PE6', 'PB10', 'PB11', 'PF6',
             'PA10', 'PA15', 'PB3', 'PB14', 'PB15', 'PC13',
             'PE9', 'PE10', 'PF0', 'PF1', 'PF2', 'PF3', 'PF10',
             'PF11', 'PF12', 'PF13', 'PF14', 'PF15', 'PG1']

CONNECTORS = {'J101': C1_NETS, 'J102': C2_NETS, 'J103': C3_NETS,
              'J104': C4_NETS, 'J110': EXP_NETS}


def main(xml_path, out_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    # pin name <-> number for the MCU from libparts (resolved via U1501)
    mcu_part = None
    for c in root.find('components'):
        if c.get('ref') == 'U1501':
            mcu_part = c.find('libsource').get('part')
    name2num = {}
    for lp in root.find('libparts'):
        if lp.get('part') == mcu_part:
            for p in lp.find('pins'):
                name2num[p.get('name')] = p.get('num')
    assert name2num, 'libpart do MCU nao encontrado (%s)' % mcu_part
    # net per (ref, pin)
    netof = {}
    for n in root.find('nets'):
        for x in n:
            netof[(x.get('ref'), x.get('pin'))] = n.get('name')

    lines = []
    fails = 0

    def check(desc, ok, got=''):
        nonlocal fails
        mark = 'OK  ' if ok else 'FAIL'
        if not ok:
            fails += 1
        lines.append('%s %-28s %s' % (mark, desc, got))

    lines.append('== 1. MCU (U1501) x PINOUT-CONTRACT ==')
    for pin, want in sorted(EXPECTED.items()):
        num = name2num.get(pin)
        if num is None:
            # named pins like BOOT0/NRST/PH0 may differ in symbol
            cand = [k for k in name2num if pin in k]
            num = name2num[cand[0]] if cand else None
        if num is None:
            check('U1501 %s' % pin, False, 'pino nao achado no simbolo')
            continue
        got = netof.get(('U1501', num), '<desconectado>')
        if want.startswith('substr:'):
            ok = want[7:] in got
        else:
            ok = got.lstrip('/') == want or got == want
        check('U1501 %s (pad %s)' % (pin, num), ok,
              '%s (esperado %s)' % (got, want))
    for pin in EXPECT_NC:
        num = name2num.get(pin)
        got = netof.get(('U1501', num), '')
        ok = got == '' or got.startswith('unconnected-')
        check('U1501 %s livre/NC' % pin, ok, got or '<desconectado>')

    lines.append('')
    lines.append('== 2. Conectores x alocacao (YAML) ==')
    for ref, table in sorted(CONNECTORS.items()):
        for pinno, want in sorted(table.items()):
            got = netof.get((ref, str(pinno)), '<desconectado>')
            if want is None:
                ok = got == '<desconectado>' or got.startswith('unconnected')
                check('%s.%d reservado' % (ref, pinno), ok, got)
            else:
                ok = got.lstrip('/') == want
                check('%s.%d' % (ref, pinno), ok,
                      '%s (esperado %s)' % (got, want))

    lines.append('')
    lines.append('== Resultado ==')
    total = len([l for l in lines if l[:4] in ('OK  ', 'FAIL')])
    lines.append('%d checagens, %d divergencias' % (total, fails))
    txt = '\n'.join(lines) + '\n'
    with open(out_path, 'w') as f:
        f.write(txt)
    print(txt.splitlines()[-1], '->', out_path)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
