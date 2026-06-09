# Etapa 0 — 4 cilindros, 2 redes CAN (montagem JLC + mão)

Conjunto de BOMs para a **primeira tiragem**: motor 4 cilindros completo, dual
ETB, duas redes CAN, com todo o SMD montado pela JLC PCBA e apenas conectores /
through-hole soldados à mão. Os bancos de canais que escalam com o número de
cilindros (ignição 5–12 e low-side 9–16) ficam **não populados (DNP)**, com
footprint e roteamento intactos para expansão futura só soldando o CI à mão.

Gerado a partir de `export/v0.7/proteus-bom-jlc.csv` e `proteus-bom-not-jlc.csv`.
O PCB **não foi alterado** — isto é apenas seleção de populagem.

## Arquivos

| Arquivo | Uso |
|---|---|
| `proteus-bom-jlc-stage0.csv` | BOM para a JLC PCBA (todo o SMD, incl. automotivos e pad térmico). |
| `proteus-bom-hand.csv` | Itens TH/mecânicos soldados à mão (AMPSEAL, USB, jack, eletrolítico). |
| `proteus-dnp-stage0.csv` | Lista do que NÃO popular nesta etapa (expansão). |

Use o `export/v0.7/proteus-top-pos.csv` como arquivo de posição (CPL). A JLC
ignora na montagem os designadores que não estiverem na BOM.

## O que é montado (Etapa 0)

- MCU STM32F427ZGT6, baro LPS25HB, USB/DFU, microSD, debug.
- Power: buck LMR14020, LDO, supplies de sensor TLS115 (U1004/U1005).
- **2× CAN**: TJA1051 U6 (CAN1) e U904 (CAN2), cada um com ESD PESD1CAN.
- **Ignição cil 1–4**: U1602, U1603 (MIC4427).
- **Low-side 1–8**: VNLD5160 U201/U202/U301/U302 (4 injetores + 4 auxiliares).
- **High-side 1–4**: BTS4175 U1102–U1105.
- **2× ETB**: TLE9201SG U10, U11.
- **2× VR**: MAX9924 U1203, U1204 + hall (74HC2G17).
- Analógico/temperatura completo + knock front-end.

## Atenção / validar antes de fechar pedido

- **LCSC a confirmar no carrinho JLC** (linhas com LCSC vazio): `VNLD5160`,
  `TLS115`, `MAX9924`. São Extended Parts; se sem estoque, usar JLC Global
  Sourcing ou consignar. `TLE9201SG` = C112633.
- **Terminação CAN on-board** (R33 = CAN1, R1004 = CAN2, 120 Ω): manter apenas
  se a ECU ficar na **ponta** de cada barramento. Se for ligada no meio da rede,
  remover essas duas linhas da BOM JLC.
- Para USB instalar **apenas uma** das opções (J1501/J1503/J1504).

## Expansão futura (sem nova PCBA)

Soldar à mão (SOIC-8, fácil) conforme a lista DNP:
- Ignição 5–8 → U1701, U1702; 9–12 → U1801, U1802 (+ R/RN/C do banco).
- Low-side 9–12 → U401, U402; 13–16 → U501, U502 (+ arrays).
