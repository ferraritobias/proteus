# Proteus-BR — projeto KiCad (esquemático v1)

ECU baseada na rusEFI Proteus v0.7 (raiz deste repositório), implementando
o `docs/proteus-br/SPEC-FREEZE.md`. Pinos do STM32 vêm exclusivamente de
`docs/proteus-br/PINOUT-CONTRACT.csv`; alocação dos conectores vem dos
YAML em `docs/proteus-br/connectors/`.

Formato: KiCad 7 (compatível com KiCad 8 — abrir e salvar migra).

## Estrutura

| arquivo | conteúdo |
|---|---|
| `proteus-br.kicad_sch` | raiz: C1–C4 (Superseal 26v), expansão Linux 2×10, polyfuses, roda-livre LS13-16, interligação |
| `mcu.kicad_sch` | STM32F427ZGT6 + bring-up (FIREWALL), LED único PE5, USB-B, SWD, microSD (DNP) |
| `psu.kicad_sch` | TVS + buck LMR14020 + AMS1117 + trackers TLE4251D + CAN1/CAN2 |
| `lowside_quad.kicad_sch` | 4× (VNLD5160TR-E; LS9-16 não populados na fase 1) |
| `ign_quad.kicad_sch` | 3× (TC4427A; IGN5-12 não populados na fase 1) |
| `highside_quad.kicad_sch` | 1× BTS4175SGA — inteira DNP na fase 1 |
| `quad_analog.kicad_sch` | 3× (AV1-11; quad 3 não populado) |
| `quad_analog_temp.kicad_sch` | 1× (AT1-4, pullup 2,7k) |
| `triggers.kicad_sch` | 6 hall (fase 1: 1-2) + 2 VR MAX9924 (DNP) |
| `knock.kicad_sch` | 2 canais (ch2 DNP), entrada só pelo C3 |
| `etb.kicad_sch` | 2× TLE9201SG — DNP |
| `lib/` | símbolos locais (TLE4251D, Superseal26) + footprints locais |
| `tools/` | geração/validação (ver `tools/run_all.sh`) |
| `reports/` | validação de contrato, ERC-lite, BOMs, diff de BOM |

## Regeneração e validação

```sh
tools/run_all.sh
```

Reconstrói as folhas a partir do projeto original (raiz do repo), gera a
raiz, exporta o netlist, valida contra o PINOUT-CONTRACT (240 checagens),
roda o ERC-lite, gera BOMs/diff e plota o PDF.

## Avisos importantes

- **TLE4251D — pinout PREMISSA**: 1=I, 2=EN, 3=GND, 4=ADJ, 5=Q, tab=GND.
  Conferir no datasheet Infineon antes do layout (acesso web bloqueado no
  ambiente em que este projeto foi gerado).
- **Footprint Superseal 26v é DRAFT**: geometria não verificada contra o
  customer drawing TE 6437288-6 (2×13, pitch 3,5 mm — PREMISSA). NÃO
  fabricar sem conferir.
- **ERC oficial pendente**: o ambiente só tinha KiCad 7.0.11 (`sch erc`
  é do KiCad 8). Rodar ERC na primeira abertura; `reports/erc-lite.txt`
  cobre as checagens principais (0 problemas, 4 waivers justificados).
- **DNP por instância**: KiCad não suporta DNP por instância de folha;
  população da fase 1 (LS9-16, IGN5-12, AV9-11) é controlada na BOM de
  montagem (`reports/bom-esquematico-fase1.csv`) e anotada na folha raiz.
