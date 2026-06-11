# Diff BOM: esquematico Proteus-BR x docs/proteus-br/BOM-completa.csv

Gerado por tools/gen_bom.py a partir do netlist kicad-cli.
Convencao: "qtd doc" e o campo qtd_total da BOM-completa;
"qtd sch" e a contagem real no esquematico (populados + DNP).

| grupo | funcao | part number | qtd doc | qtd sch | status | nota |
|---|---|---|---|---|---|---|
| MCU | Microcontrolador | STM32F427ZGT6 | 1 | 1 | OK |  |
| MCU | Cristal HSE 8 MHz | 8MHz 5032 | 1 | 1 | OK |  |
| MCU | Referencia 3V3 VREF+ | REF3333AIDBZR | 1 | 1 | OK |  |
| MCU | Protecao USB | USBLC6-2SC6 | 1 | 1 | OK |  |
| MCU | Conector USB-B | 5787834-1 | 1 | 1 | OK |  |
| MCU | Header SWD 2x5 1.27mm | FTSH-105-01-F-DV | 1 | 1 | OK | J1502; Tag-Connect J4 removido. |
| MCU | Botoes BOOT0/RESET | EVQQ2 | 2 | 2 | OK |  |
| MCU | LED status | LED 0603 | 1 | 1 | OK | LED unico em PE5 (running) — decisao 4. |
| MCU | microSD | 693072010801 | 1 | 1 | OK | footprint montado so na fase 2 (DNP). |
| PSU | Buck 5V | LMR14020SDDAR | 1 | 1 | OK |  |
| PSU | LDO 3V3 | AMS1117-3.3 | 1 | 1 | OK |  |
| PSU | Tracker 5V n.1 | TLE4251D | 1 | 1 | OK | doc divide em n.1+n.2; total no esquematico = 2 (U1004 + U1005 DNP) ✓ |
| PSU | Tracker 5V n.2 | TLE4251D | 1 | 1 | OK | idem — confere |
| PSU | TVS entrada | SM15T33CA | 1 | 1 | OK |  |
| PSU | Schottky SMA | SS34 classe | 6 | 5 | DIFERE | BOM diz 6 (D101-104+D901+D903); esquematico tem 5 — D903 removido de proposito (entrada 12V unica: schottky em paralelo com os polyfuses anularia a protecao; nota na folha psu). |
| PSU | Polyfuse 1206 | polyfuse | 2 | 2 | OK |  |
| PSU | Indutor 10uH buck | MWSA0503-100M | 1 | 1 | OK |  |
| PSU | Indutor 2.2uH filtro | L1210 | 1 | 1 | OK |  |
| PSU | Ferrite 0805 | FB | 1 | 1 | OK |  |
| PSU | Eletrolitico 56u/50V | EEH-AZF1H560B | 2 | 2 | OK |  |
| CAN | Transceiver CAN1 | TJA1051T/3 | 1 | 1 | OK | doc divide CAN1/CAN2; total = 2 (U904 + U6 DNP) ✓ |
| CAN | Transceiver CAN2 | TJA1051T/3 | 1 | 1 | OK | idem — confere |
| CAN | TVS CAN | PESD1CAN-UX | 2 | 2 | OK |  |
| LOWSIDE | Driver dual LS1-16 | VNLD5160TR-E | 8 | 8 | OK |  |
| HIGHSIDE | Switch HS1-4 | BTS4175SGA | 4 | 4 | OK |  |
| IGN | Driver IGN1-12 | TC4427ACOA713 | 6 | 6 | OK |  |
| ETB | Ponte H ETB1/ETB2 | TLE9201SG | 2 | 2 | OK |  |
| TRIGGER | Buffer schmitt | SN74LVC2G17DBVR | 3 | 3 | OK | BOM diz 3 (fase 1: 1x); esquematico tem 3, mas fase 1 monta 2 (U1202+U1207): a fiacao da v0.7 cruza canais (U1202=DIG1+5, U1207=DIG2+3) — corrigir BOM-fase1. |
| TRIGGER | Condicionador VR | MAX9924UAUB+T | 2 | 2 | OK |  |
| ANALOG | Opamp quad | MCP6004 SOIC-14 | 5 | 5 | OK | BOM diz 5; esquematico tem 5 (U701/U801/U901/U1101/U5). ATENCAO: BOM-fase1.csv lista so 3, mas a fase 1 precisa de 4 (U1101 buffer dos AT1-4 esta populado). |
| ANALOG | Opamp dual knock | MCP6002-xSN | 1 | 1 | OK |  |
| ANALOG | ESD array | SRV05-4 | 5 | 7 | DIFERE | BOM diz 5 (fase1 3x); esquematico tem 7: U1/U2/U3/U4 (AVs+AT) + D1501 (USB) + U1106/U1107 (hall) — a BOM-completa nao contou os 2 SRV05 dos triggers (existem na v0.7). Fase 1 monta 5 (U3 e U1107 DNP). |
| R | 1R buck | 1R | 1 | 1 | OK |  |
| R | 100R serie IGN | 100R 1% | 12 | 12 | OK |  |
| R | 120R CAN/highside | 120R 1% | 6 | 6 | OK | CAN1 + CAN2(DNP) + 4x highside(DNP) = 6 ✓. |
| R | 1k | 1k 1% | ~24 | 47 | DIFERE | 47 = 32 lowside (4 folhas x 8 ex-array) + 12 ign (3 folhas x 4) + R1511 LED + R1217/R1218 VR. A estimativa ~24 da doc nao multiplicou pelas instancias de folha. |
| R | 2.7k | 2.7k 1% | 16 | 16 | OK |  |
| R | 4.7k | 4.7k 1% | 14 | 14 | OK |  |
| R | 5.6k | 5.6k 1% | 16 | 16 | OK |  |
| R | 10k | 10k 1% | ~40 | 48 | OK(~) | inclui ex-arrays: RN1301 (4) + RN701-tipo (3 folhas x 4) + RN1101 (4) como discretos. |
| R | 12k | 12k 1% | 3 | 3 | OK |  |
| R | 33k | 33k 1% | 4 | 4 | OK |  |
| R | 68k | 68k 1% | 1 | 1 | OK |  |
| R | 82k | 82k 1% | 1 | 1 | OK |  |
| R | 100k | 100k 1% | ~8 | 5 | OK(~) |  |
| R | 470k | 470k 1% | 16 | 14 | DIFERE | 14 = 12 bias AV (3 folhas x 4, R701-R904) + 2 knock (R1903/R1904). A doc contou 16 assumindo bias na folha AT — nao existe na v0.7. |
| C | 33p C0G | 33p | 2 | 2 | OK |  |
| C | 47p C0G | 47p | 2 | 2 | OK | BOM diz 2 (1 por canal de knock); ch2 e DNP na fase 1. |
| C | 330p C0G | 330p | 3 | 3 | OK |  |
| C | 680p C0G | 680p | 2 | 2 | OK |  |
| C | 1n X7R | 1n | 14 | 14 | OK |  |
| C | 3.3n X7R | 3.3n | 2 | 2 | OK |  |
| C | 10n X7R | 10n | ~23 | 22 | OK(~) | contagem exata do esquematico; BOM usava ~23. |
| C | 100n X7R | 100n | ~42 | 41 | OK(~) | contagem exata do esquematico; BOM usava ~42. |
| C | 1u X7R | 1u | ~7 | 7 | OK |  |
| C | 2.2u X7R | 2.2u | 2 | 2 | OK |  |
| C | 4.7u X7R | 4.7u | ~8 | 7 | OK(~) |  |
| C | 10u X7R | 10u | ~6 | 4 | OK(~) |  |
| CONN | Header Superseal 26v | 6437288-6 (keying a confirmar) | 4 | 4 | OK |  |
| CONN | Housing key1 | 3-1437290-7 | 1 | — | n/a | item de chicote/compra — fora do esquematico |
| CONN | Housing key2 | 3-1437290-8 | 1 | — | n/a | item de chicote/compra — fora do esquematico |
| CONN | Housing key3 | a confirmar | 1 | — | n/a | item de chicote/compra — fora do esquematico |
| CONN | Housing C4 | ver decisao 5 | 1 | — | n/a | item de chicote/compra — fora do esquematico |
| CONN | Terminais 24-20AWG | kit Superseal 1.0 | ~150 | — | n/a | item de chicote/compra — fora do esquematico |
| CONN | Terminais 18AWG | 3-1447221-3 | ~40 | — | n/a | item de chicote/compra — fora do esquematico |
| CONN | Tampoes cavidade | 4-1437284-3 | ~60 | — | n/a | item de chicote/compra — fora do esquematico |
| CONN | Header expansao 2x10 | box header 2.54 generico | 1 | 1 | OK |  |
| REMOVIDOS | Barometro | LPS25HB | 0 | — | n/a | removido (confere) |
| REMOVIDOS | 2o USB | — | 0 | — | n/a | removido (confere) |
| REMOVIDOS | RTC/bateria | BT1+D1503+R1513 | 0 | — | n/a | removido (confere) |
| REMOVIDOS | LEDs extras | 4x LED 0603 | 0 | — | n/a | removido (confere) |
