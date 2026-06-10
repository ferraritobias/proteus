# PROTEUS-BR — SPEC FREEZE (v1.1 — decisões do dono incorporadas)

**Status:** especificação congelada para início do KiCad (Prompt 3). Nenhum
arquivo KiCad foi gerado nesta etapa. As DECISÕES-PENDENTES da v1 foram
respondidas pelo dono do projeto e estão registradas na seção G.
**Base:** projeto rusEFI Proteus v0.7 deste repositório +
`docs/proteus-br/PINOUT-CONTRACT.md` (imutável) + pesquisa de disponibilidade
jun/2026 (fontes citadas).
**Legenda:** itens marcados **PREMISSA** não têm evidência primária ainda e
devem ser confirmados no Prompt 3; a seção G registra as decisões
tomadas pelo dono sobre os pontos que estavam pendentes na v1.

---

## A. Discrepâncias: projeto original × PINOUT-CONTRACT

Auditoria do KiCad v0.7 deste repo contra o contrato. Nada bloqueante; itens
3–5 são diferenças que a Proteus-BR resolve de propósito.

| # | Item | Original (evidência) | Contrato | Ação na BR |
|---|---|---|---|---|
| 1 | MCU | Símbolo `STM32F427ZGTx` desenhado com lib do F767 (`mcu.kicad_sch`, U1501); readme cita F429ZG; BOM v0.7 compra **STM32F427ZGT6** (LCSC C117816, `export/v0.7/proteus-bom-jlc.csv`) | exige F42x, LQFP-144, 1 MB | Manter STM32F427ZGT6 |
| 2 | Cristal HSE | **8 MHz** (Y1501, BOM C115962; caps 33p C1521/C1522) | valor livre (auto-detect, inteiro em MHz) | Manter 8 MHz — fecha o "NÃO RESOLVIDO #3" do contrato |
| 3 | `5V_SENSOR_PG` | Os PG dos dois TLS115 vão a **PC14 (pad 8) e PC15 (pad 9)** do LQFP-144 (nets `/mcu/5V_SENSOR_1_PG`, `/mcu/5V_SENSOR_2_PG` no `proteus.kicad_pcb`), com pullups 10k R1006/R1007 | listava PC14/PC15 como "livres"; PG = "não resolvido #1" | **Resolvido:** é rede só de hardware, invisível ao firmware. BR roteia PG→PC14/PC15 com pullup 10k em footprint **DNP** (custo zero, diagnóstico futuro) |
| 4 | RTC/bateria (novidade v0.7) | BT1 + D1503 schottky + R1513 no VBAT (`mcu.kicad_sch`) | F4: `EFI_RTC=FALSE`, LSE not fitted | **Remover** — peso morto no F4 |
| 5 | LEDs | 5 LEDs (D1502/D1504–D1507, 330Ω R1508–R1512) p/ PE3/PE4/PE5/PE6 + power | PE3–PE6 são BOOT, mas LED ausente não quebra firmware | **DECIDIDO (v1.1):** LED populado em **PE5 (running)** — heartbeat que pisca sempre que o firmware roda, diagnóstico sem ambiguidade. Footprints LED+R em PE3/PE4/PE6 ficam na placa como DNP (custo zero) |
| 6 | Buffer schmitt triggers | BOM diz "74HC2G17" mas o código C10429 é **SN74LVC2G17DBVR** e o símbolo é `SN74LVC2G17DB` (`triggers.kicad_sch` U1202/U1207/U1208) | n/a | Adotar SN74LVC2G17DBVR (SOT-23-6, C10429, US$0,03) |
| 7 | USB | 3 opções de conector (J1501/J1503 verticais, J1504 header) | PA11/PA12 BOOT | 1 conector apenas (decisão já tomada) |
| 8 | Divisores/pullups analógicos | AV: 5,6k/10k + 100n por canal; VBatt: 82k (R1503)/10k (R1504); AT: 2,7k | 1,56 / 9,2 / 2700 Ω — byte a byte | **Copiar 1:1** (intocáveis, seção D) |
| 9 | VBUS→PA9 | a confirmar no roteamento original | proibido ligar VBUS em PA9 | BR **não liga** (FIREWALL); checagem de DRC no Prompt 3 |
| 10 | Knock | MCP6002 (U7) + parte do MCP6004 (U5) + jack 3,5 mm J3 → PF4/PF5 | PF4/PF5 BOOT+SILÍCIO | Manter circuito; trocar jack 3,5 mm por pinos no C3 (12/13 e 24/25) |

---

## B. Alocação dos 104 pinos (4× TE Superseal 1.0, 26 vias)

**PREMISSA de numeração:** 26 vias em 2 fileiras de 13 (1–13 / 14–26),
adjacência física = n↔n+1 na fileira e n↔n+13 entre fileiras. O desenho TE
real do header 26 vias é em 4 fileiras (7/6/7/6) — a numeração definitiva e a
adjacência serão re-verificadas com o drawing TE no Prompt 3; a alocação
abaixo já mantém os pares críticos (VR, CAN, ETB, knock) em números
consecutivos, o que sobrevive a qualquer arranjo de fileiras.

**Limite de corrente:** terminais Superseal 1.0 aceitam fio até
0,75–0,85 mm² (≈18 AWG, terminal 3-1447221-3); projeto assume
**≤5 A contínuos por pino (PREMISSA conservadora)** — potência sempre em
pinos paralelados. Marketing TE/KLS cita "até 15 A" no sistema, não
confirmado por datasheet de contato — não usamos esse número.

**Ajuste sobre a proposta inicial (exposto para sua validação):**
ETB1±/ETB2± saíram do C4 para o **C2**. Motivo: são saídas de ponte H com até
~3 A contínuos / 6 A de pico chaveadas em PWM — colocá-las ao lado de VR/CAN
violaria a regra "nenhum sinal sensível adjacente a alta corrente". O C2 tem
folga (12 IGN lógicos + GNDs) e é zona de atuadores.
**Validado pelo dono (v1.1)**, junto com a diretriz: *a posição de cada pino
dentro do conector não é requisito* — o layout do Prompt 3 pode reordenar
pinos livremente para otimizar chicote e roteamento, desde que (a) os pares
VR/CAN/ETB/knock continuem adjacentes, (b) retornos de potência e de sinal
continuem separados, e (c) os YAML de `connectors/` sejam atualizados junto.

Detalhe pino a pino (net, AWG, observação) está nos quatro YAML em
`docs/proteus-br/connectors/` — resumo:

### C1 — POTÊNCIA/INJEÇÃO (keying 1, housing 3-1437290-7)

| Pinos | Função | AWG | Obs |
|---|---|---|---|
| 1–2 | 12V_RAW (paralelo) | 18 | alimenta PSU + highsides; fusível externo no chicote |
| 3, 14–16 | GND potência (paralelo) | 18 | retorno de carga, plano de potência |
| 4–11 | LS1–LS8 (Inj 1–8) | 18 | **Fase 1** |
| 17–24 | LS9–LS16 | 18–20 | footprint DNP; LS10/11/12 = defaults bomba/fan/relé principal |
| 12–13, 25–26 | HS1–HS4 | 18 | footprint DNP (BTS4175SGA) |

### C2 — IGNIÇÃO/ETB (keying 2, housing 3-1437290-8)

| Pinos | Função | AWG | Obs |
|---|---|---|---|
| 2–7, 15–20 | IGN1–IGN12 (lógico 5 V) | 20 | Fase 1: IGN1–4; resto DNP |
| 9–10 | ETB1+ / ETB1− (par adjacente) | 18 | TLE9201 #1, DNP |
| 22–23 | ETB2+ / ETB2− (par adjacente) | 18 | TLE9201 #2, DNP |
| 1, 8, 13, 14, 21, 26 | GND lógico/retorno bobina | 20 | |
| 11, 12, 24, 25 | RESERVA | — | cavidade selada (tampão 4-1437284-3) |

### C3 — SENSORES (keying 3, housing 26v key 3 — PN exato a fixar na compra)

| Pinos | Função | AWG | Obs |
|---|---|---|---|
| 1 | 5V_SENSOR_1 (tracker #1) | 20 | **Fase 1** |
| 14 | 5V_SENSOR_2 (tracker #2) | 20 | DNP |
| 2, 9, 15, 21 | GND sensores | 20 | retorno analógico, estrela no GND analógico |
| 3–8, 16–17 | AV1–AV8 | 22 | Fase 1 (AV7 DNP opcional) |
| 18–20 | AV9–AV11 | 22 | DNP |
| 10–11, 22–23 | AT1–AT4 | 22 | Fase 1; pullup 2,7k/5V |
| 12–13 | KNOCK1 sinal + retorno (par) | 22 blindado | **Fase 1**; PF4 (BOOT) |
| 24–25 | KNOCK2 sinal + retorno (par) | 22 blindado | DNP; PF5 (BOOT) |
| 26 | RESERVA | — | sugerida p/ futura AV extra em PF3 (ADC3_IN9) |

### C4 — TRIGGERS/COMUNICAÇÃO (keying 1 repetido — housing 3-1437290-7, DECIDIDO v1.1; posição afastada do C1 + housing de cor distinta)

| Pinos | Função | AWG | Obs |
|---|---|---|---|
| 1, 14 | 5V_SENSOR_1 | 20 | alimentação de sensores hall |
| 2, 7, 15, 18 | GND sensores | 20 | |
| 3–6, 16–17 | HALL1–HALL6 (Digital 1–6) | 22 | Fase 1: HALL1–2 |
| 8–9 + 10 | VR1+/VR1− (par) + blindagem | 22 par trançado | MAX9924 #1 DNP |
| 20–21 + 22 | VR2+/VR2− (par) + blindagem | 22 par trançado | MAX9924 #2 DNP |
| 11–12 | CAN1 H/L (par) | 22 par trançado | **Fase 1**; OpenBLT/reflash |
| 23–24 | CAN2 H/L (par) | 22 par trançado | DNP (transceiver #2) |
| 13, 19, 25, 26 | RESERVA | — | |

Conferência: 4×26 = 104 posições; todos os pinos do contrato chegam a
conector ou footprint; canais DNP mantêm roteamento MCU→footprint→conector
desde a v1 (regra do contrato, "Expansão em etapas").

---

## C. Substituições de componentes (preços/estoque verificados jun/2026)

### C.1 Lowside (original VNLD5160TR-E, 8× dual = 16 canais)

**Fato novo da pesquisa:** o VNLD5160TR-E **não está obsoleto** — ativo na ST
e **em estoque na LCSC (C377942, a partir de US$0,61)**
([LCSC](https://lcsc.com/product-detail/Driver-ICs_STMicroelectronics-VNLD5160TR-E_C377942.html),
[ST](https://www.st.com/en/automotive-analog-and-power/vnld5160-e.html)).
Specs: dual lowside OMNIFET III, 160 mΩ/canal, 3,5 A, **clamp indutivo
interno ~41 V**, entrada compatível com GPIO 3,3 V (projeto original prova),
SOIC-8 soldável à mão.

**DECIDIDO (dono, v1.1): manter VNLD5160TR-E.** As duas alternativas abaixo
ficam congeladas apenas como plano B de supply:

| | Opção A — protegido pin-similar | Opção B — MOSFET lógico + TVS |
|---|---|---|
| Peça | **Infineon BTF3050TE** (TO-252-5, 50 mΩ, 1 canal, clamp interno, protegido) — LCSC **C534724**, US$0,94, **apenas 45 un. em estoque** ([LCSC](https://lcsc.com/product-detail/PMIC-Power-Distribution-Switches_Infineon-Technologies-BTF3050TE_C534724.html)) | **IRLR2905TRPBF** (DPAK, 55 V, 42 A, logic-level) — LCSC **C3010**, US$0,27 ([LCSC](https://www.lcsc.com/product-detail/MOSFETs_Infineon-Technologies_C3010.html)) + TVS **SMBJ33CA** Littelfuse — LCSC **C83325**, US$0,06 ([LCSC](https://www.lcsc.com/product-detail/TVS_Littelfuse-SMBJ33CA_C83325.html)) |
| Canais/peça | 1 → 16 chips | 1 → 16 FET + 16 TVS (+ pulldown 10k, série 1k existentes) |
| Trade-off | Proteção completa (térmica, curto, clamp) e diagnóstico; mas 16 chips, mais caro/canal, exige pino VDD 3–5,5 V e estoque LCSC raso (Mouser como fonte) | Mais barato e robusto de supply (genérico multi-fabricante); **perde proteção de curto/térmica** — um curto no chicote queima o FET; clamp externo dimensionado abaixo |
| Soldabilidade | TO-252-5 fácil | DPAK + SMB fáceis |

**Cálculo de clamp da Opção B** (mostrado para constar na spec):

- Injetor saturado: L≈14 mH, I=1 A → E=½LI²=7 mJ. TVS clampa em
  V_cl≈45 V; energia no TVS por evento E·V_cl/(V_cl−V_bat)=7×45/31≈**10 mJ**,
  decaimento LI/(V_cl−V_bat)≈0,45 ms. A 8000 rpm sequencial (67 Hz):
  P_média≈0,68 W — **acima** do contínuo de um SMB (~0,55 W). ⇒ Se a Opção B
  for escolhida, usar **SMCJ33CA** (DO-214AB, 1500 W) nos canais de injetor,
  ou aceitar SMBJ sabendo que o caso 8000 rpm/1 A é teto teórico.
- Solenoide PWM 2–3 A (boost/VVT): L≈5 mH, 3 A → 22 mJ/evento; em PWM
  100–300 Hz TVS é inviável (vários W) ⇒ canais de solenoide PWM precisariam
  de **roda-livre para +12 V (SS54)** = decaimento lento, inaceitável para
  injetor mas correto para solenoide. Ou seja: a Opção B exige dois circuitos
  de saída diferentes conforme o uso do canal — mais uma razão para a
  recomendação de manter o VNLD5160, que resolve demagnetização internamente
  em qualquer perfil de carga.

### C.2 Tracker 5 V dos sensores (original TLS115D0E ×2)

**DECIDIDO (dono, v1.1): manter o TLS115D0EJ original.** Fonte:
Mouser/Digi-Key (TLS115D0EJXUMA1, DK 6559864 — não há na LCSC); produto
ativo na Infineon (família garantida até ≥2038). Fase 1 monta 1; o #2 fica
DNP.

*Ressalva registrada:* o PG-DSO-8 tem exposed pad — é a segunda exceção (além
do LMR14020 HSOP-8-EP, que a placa original já tinha) à regra "zero ar
quente". Mitigação de montagem manual: furo/via térmica de ~1,5 mm sob o pad
para soldar o EP por baixo com ferro. As alternativas pesquisadas ficam
documentadas como plano B de supply:

| | Opção A — tracker real (plano B de supply) | Opção B — LDO protegido (perde tracking) |
|---|---|---|
| Peça | **Infineon TLE4251D** — tracker 400 mA, PG-TO252-5 (DPAK, sem exposed pad escondido), reverso + curto p/ bateria + curto p/ GND + térmica. LCSC **C539669**, US$0,955, 860 un. ([LCSC](https://lcsc.com/product-detail/voltage-regulators-linear-low-drop-out-ldo-regulators_infineon-technologies-tle4251d_C539669.html)) | **TI TPS7B6950QDCYRQ1** — 5 V fixo 150 mA, SOT-223, 40 V, limite de corrente + térmica. LCSC **C108469**, US$0,17 ([LCSC](https://www.lcsc.com/product-detail/Low-Dropout-Regulators-LDO_TI_TPS7B6950QDCYRQ1_TPS7B6950QDCYRQ1_C108469.html)) |
| Referência de tracking | Segue o 5 V do buck (como o TLS115) — erro ratiométrico sensor↔ADC cancela | **Sem tracking**: rail do sensor e referência do ADC viram duas fontes independentes (±1–2% cada + deriva térmica) ⇒ ~2–4% de erro de ganho em MAP/TPS, calibrável a uma temperatura só |
| Ressalva | — | Curto sustentado da saída para +bateria (cenário que o tracker tolera por projeto) precisa ser verificado no abs-max do TPS7B69xx antes de cravar |

Fallback de baixa corrente: TLE4250-2G (50 mA, LCSC C976300) só serve se
cada rail ficar abaixo de 50 mA — não recomendado. **Importante para o
Prompt 3:** desenhar o footprint do tracker de forma a aceitar TLE4251D
(PG-TO252-5) como alternativa ao TLS115 não é viável (pinagens diferentes);
o footprint congelado é o PG-DSO-8 do TLS115.

### C.3 Mantidos — disponibilidade verificada

| Peça | Código | Preço | Situação |
|---|---|---|---|
| STM32F427ZGT6 | LCSC C117816 | ~US$4,35 | 285 un. — comprar cedo |
| TJA1051T/3 | LCSC C38695 | US$0,29 | 34k un. ✔ |
| MAX9924UAUB+T | LCSC C5145181 | US$1,44 | em estoque ✔ (footprint DNP na Fase 1) |
| MCP6004 (SOIC) | LCSC C7378 | US$0,23 | 139k ✔ |
| MCP6002 (SOIC) | LCSC C7377 | — | ✔ (BOM v0.7) |
| LMR14020SDDAR | LCSC C187824 | US$0,20 | 9,9k ✔ |
| AMS1117-3.3 | LCSC C6186 | US$0,09 | 349k ✔ |
| SRV05-4 | LCSC C13612 (Semtech) | US$0,17 | 5,7k ✔ |
| USBLC6-2SC6 | LCSC C7519 | US$0,07 | 85k ✔ |
| REF3333AIDBZR | LCSC C130016 | ~US$1 | 2,7k ✔ |
| SN74LVC2G17DBVR | LCSC C10429 | US$0,03 | ✔ |
| **MIC4427** | **não há na LCSC** | — | substituto pin-compatível **TC4427ACOA713** (Microchip, SOIC-8) LCSC **C144234** — ver DECISÃO-PENDENTE 6 |
| **BTS4175SGA** | LCSC C152451 **esgotado** | US$0,76 | Mouser tem; é DNP na Fase 1 → sem pressa |
| **SM15T33CA** | LCSC C133707 (estoque ambíguo) | ~US$0,24–0,94 | fallback Mouser/Newark |
| **TLE9201SG** | não há na LCSC | — | Mouser/DK têm (TLE9201SGAUMA1); gêmeo industrial IFX9201SG na LCSC C112633; DNP na Fase 1 |
| PESD1CAN | C152727 (BOM v0.7) | — | ✔ |

### C.4 Conectores (pesquisa TE Superseal 1.0, 26 vias)

| Item | Part number | Evidência |
|---|---|---|
| Housing plug 26 vias, key 1 | **3-1437290-7** | [TE](https://www.te.com/en/product-3-1437290-7.html), [Corsa Technic SS10-26S-1](https://www.corsa-technic.com/item.php?item_id=533) |
| Housing plug 26 vias, key 2 | **3-1437290-8** | [TE](https://www.te.com/en/product-3-1437290-8.html), [KSV "Key 2"](https://www.ksvlooms.com/products/26-way-housing-te-amp-3-1437290-8-superseal-1-0-series-key-2) |
| Housing key 3 | existe (usado em MoTeC M800) — PN exato a confirmar | [EMH "26 way key 3"](https://store.emhmotorsports.com/superseal-connector-26-way-key-3-motec/) |
| Housing do C4 | **3-1437290-7 (key 1 repetido — DECIDIDO v1.1)** | mitigação: C1 e C4 ficam nas extremidades opostas da borda e com identificação de cor |
| Header PCB 26 vias vertical | **6437288-6** | [TE](https://www.te.com/en/product-6437288-6.html) |
| Header PCB 26 vias reto/alternativas | 6473418-1 ([Newark](https://www.newark.com/te-connectivity/6473418-1/automotive-conn-str-hdr-26pos/dp/70AH9494)), 6473711-1 ([TE](https://www.te.com/en/product-6473711-1.html)); right-angle 9-6437287-9 (**PREMISSA**, confirmar keying de cada um) | |
| Terminal fêmea 0,75–0,85 mm² (18 AWG), ouro | **3-1447221-3** | busca TE/distribuidores |
| Terminais 0,35–0,5 mm² (24–20 AWG) | os dos kits 26 vias (PN a fixar na compra) | [Carrot Top kit 24-20 AWG](https://www.carrottoptuning.com/products/26-way-amp-3-1437290-7-superseal-1-0-series-connector-kit-24-20-awg) |
| Tampão de cavidade | **4-1437284-3** | busca TE/distribuidores |

---

## D. Consolidação de passivos (0603 mínimo; 0805 onde dissipa)

Regra: **F** = valor funcional, intocável (mexer = quebrar contrato ou
circuito sintonizado); **G** = genérico, convergível. Todos 0603 salvo nota.

### Resistores — 14 valores finais

| Valor | Classe | Onde | Nota |
|---|---|---|---|
| 1 Ω | F | R906 (rede do buck LMR14020) | |
| 100 Ω (0805) | F | série das saídas IGN (R1601…R1804) | dissipação/EMI |
| 120 Ω | F | terminação CAN ×2 (R33/R1004) e série dos BTS4175 | |
| 1 k | F/G | knock (R39/R41), série COUT MAX9924 (R1217/18), entradas dos lowsides (ex-arrays RN 1k → discretos 0603) | absorve os 330 Ω dos LEDs (LED único passa a 1 k) |
| 2,7 k | F | pullup AT ×4 (bias_resistor=2700 do firmware) + redes hall (R1201–1204, R1401–1408) | contrato |
| 4,7 k | F | rede de entrada MAX9924 (R1205–R1216) + pullups de status (R34–37) | filtro VR sintonizado |
| 5,6 k | F | topo do divisor AV ×16 | coeficiente 1,56 do firmware |
| 10 k | F/G | base dos divisores AV e do VBatt (F); pullups genéricos, FB, gate pulldown (G) | |
| 12 k | F | knock (R42/43) + FB do buck (R907) | 0,75 V×(1+68/12)=5,0 V |
| 33 k | F | filtro do knock (R38/40/46/47) | |
| 68 k | F | FB do buck (R908) | |
| 82 k | F | topo do divisor VBatt (R1503) | coeficiente 9,2 do firmware |
| 100 k | F/G | knock (R44/45, R1901/02) F; pulldowns/straps G | |
| 470 k | F | bias dos buffers MCP6004 das AVs (R701–R904) + knock (R1903/04) | |

Eliminados por convergência: 330 Ω (LEDs → 1 k), arrays R_Pack04 1 k e 10 k
(→ discretos 0603; menos linhas de compra, mais fáceis de retrabalhar à mão —
custo: +ϵ de área de placa).

### Capacitores — 13 valores finais

| Valor | Classe | Onde | Nota |
|---|---|---|---|
| 33 p | F | carga do cristal (C1521/22) | CL do cristal 8 MHz |
| 47 p | F | knock (C25/26) | |
| 330 p | F | knock (C23/24) + feed-forward do buck (C905) | |
| 680 p | F | knock (C21/22) | |
| 1 n | F | filtros de trigger/VR (C1204–C1408) | sintonia EXTI/MAX9924 |
| 3,3 n (0805) | F | entrada do knock (C1901/02) | |
| 10 n | G | bypass HF (CAN, drivers, ETB) | manter separado de 100n |
| 100 n | G | decoupling geral (~40×) | |
| 1 u | F | saída/entrada dos trackers (estabilidade LDO) | janela de ESR do regulador |
| 2,2 u | F | VCAP do STM32 (C1518/19) | exigência ST |
| 4,7 u | G | bulk local (AMS1117, MCU, REF) | |
| 10 u (1206) | F | saída do buck, bulk ETB | ripple |
| 56 u eletrolítico THT | F | bulk de entrada (C17/C1001) | Panasonic EEH-AZF1H560B (BOM v0.7) |

Indutores/ferrites: 10 µH MWSA0503 (buck, C408412), 2,2 µH 1210 (filtro de
entrada, C75646), ferrite 0805 (C1015) — todos mantidos da BOM v0.7.

**Resultado:** 14 valores de R + 13 de C (era ~17 R + 14 C com 0402/arrays);
zero 0402; único pacote fora de 0603/0805/1206 é o eletrolítico THT.

---

## E. Dimensão e zoneamento da placa

### Dimensão **DECIDIDA (dono, v1.1): 180 × 120 mm**, 4 conectores na borda longa única

Consequências de engenharia (registradas):

- Largura do header Superseal 26 vias ≈ 38–40 mm (**PREMISSA**; drawing TE
  no Prompt 3). 4×40 = 160 mm de headers em 180 mm de borda ⇒ ~5 mm entre
  conectores e ~2,5 mm até cada canto. **Não sobra espaço para furos de
  fixação nos dois cantos da borda dos conectores** — a furação dessa borda
  vai entre os conectores ou recua para dentro da placa.
- Se o drawing TE mostrar header >42 mm efetivos (com flange), a saída é
  manter 180×120 e girar o C1 para a borda curta (volta o L) — fica como
  contingência registrada, sem mudar o tamanho da placa.
- Conectores numa borda única = caixa com chicote saindo num plano só (mesmo
  conceito de enclosure da Proteus original).
- 180×120 = +94% de área sobre a original (135×82,5): folga para DPAK/SOIC
  espaçados para ferro de solda e para a área da placa-filha.

### Zoneamento (vista superior, conectores embaixo)

```
 ┌────────────────────────────────────────────────────────────┐
 │  USB  SWD  microSD  LED  BOOT0/RESET      ÁREA FILHA       │
 │  (borda de serviço, topo)                 LINUX 65×45      │
 │                                           + header 2×10    │
 │  PSU (buck+LDO+     MCU LQFP144     TRIGGERS (schmitt,     │
 │  trackers+TVS)      + REF3333       MAX9924) | CAN1/CAN2   │
 │                                                            │
 │  LOWSIDE 16ch +     ANALÓGICO (divisores,                  │
 │  HIGHSIDE 4ch       buffers, knock)                        │
 │  IGN 6×TC4427 + 2×TLE9201                                  │
 ├──────────┬──────────┬──────────┬──────────┬────────────────┤
 │ C1 POTÊN │ C2 IGN   │ C3 SENS  │ C4 TRIG  │                │
 └──────────┴──────────┴──────────┴──────────┴────────────────┘
```

- **Zona potência (SW, atrás do C1):** entrada 12V, polyfuses, SM15T33CA,
  buck; lowsides e highsides colados no C1; TLE9201 entre C1 e C2. Plano GND
  de potência costurado ao GND lógico num único ponto perto da PSU.
- **Zona MCU (centro):** LQFP-144 + decoupling + REF3333; VCAP curtos.
- **Zona analógica (centro-sul, atrás do C3):** divisores/buffers/knock
  entre o C3 e o MCU; GND analógico estrela.
- **Zona triggers/comm (SE, atrás do C4):** schmitt + MAX9924 +
  transceivers CAN.
- **Borda de serviço (norte):** USB, SWD 2×5 1,27 mm, microSD, LED único,
  botões BOOT0/RESET — acessíveis com a caixa aberta sem desmontar chicote.
- **Expansão (NE):** header 2×10 2,54 mm + área 65×45 mm com 4 furos M2.5
  para a placa-filha Linux (CM4: 55×40 mm, furos 58×33 — **PREMISSA** a
  validar quando a filha for definida).
- **Furação:** 6× M3 metalizados ao GND — 2 cantos do topo + 2 no meio das
  bordas curtas + 2 entre conectores na borda sul (posição exata no layout,
  respeitando o keepout dos headers).

### Conector de expansão (board-to-board, 2×10, 2,54 mm, shrouded)

| Pino | Sinal | Pino | Sinal |
|---|---|---|---|
| 1 | 12V_SW (= 12v_PROT) | 2 | 12V_SW |
| 3 | GND | 4 | GND |
| 5 | 5V | 6 | 5V |
| 7 | CAN2_H (nível de barramento) | 8 | CAN2_L |
| 9 | GND | 10 | UART_TX (PD5, 3,3 V) |
| 11 | UART_RX (PD6, 3,3 V) | 12 | GND |
| 13 | AUX_SPI SCK (PF7) | 14 | AUX_SPI MISO (PF8) |
| 15 | AUX_SPI MOSI (PF9) | 16 | AUX_SPI CS (PG15 — pino livre, escolha nossa) |
| 17 | 3V3 (referência/lógica leve) | 18 | GND |
| 19 | GND | 20 | RESERVA (PG0, livre) |

Notas: CAN2 entregue em nível de barramento (depois do TJA1051 #2 — a filha
usa controlador+transceiver próprios ou MCP2515+TJA1051); PF7/8/9 são os pinos
que o build F7 usa como SPI5 (reservados no contrato); PG15/PG0 são livres no
contrato. 12V_SW = mesmo rail protegido da ECU (pós polyfuse+TVS) —
**PREMISSA**, ver DECISÃO-PENDENTE 10. PN do header 2×10: genérico box header
IDC (fixar código na compra, Prompt 3).

---

## F. Fase 1 × completa (resumo de população)

| Bloco | Fase 1 | Footprint DNP (mesma placa) |
|---|---|---|
| PSU | buck 5V + AMS1117 + TVS + polyfuses + tracker #1 (TLE4251D) | tracker #2 |
| Lowside | LS1–8 (4× VNLD5160) | LS9–16 (4× VNLD5160) |
| Ignição | IGN1–4 (2× TC4427A) | IGN5–12 (4× TC4427A) |
| Highside | — | HS1–4 (4× BTS4175SGA) |
| ETB | — | 2× TLE9201SG |
| Analógico | AV1–8, AT1–4 | AV9–11 |
| Knock | canal 1 (PF4) | canal 2 (PF5) |
| Triggers | HALL1–2 (1× LVC2G17) | HALL3–6 (2× LVC2G17), 2× MAX9924 |
| Comms | CAN1, USB, SWD | CAN2, microSD |
| MCU | completo (bring-up FIREWALL) | — |
| Removidos de vez | — | LPS25HB (baro), 2º USB, 4 LEDs, BT1/RTC |

BOMs: `BOM-fase1.csv` e `BOM-completa.csv` nesta pasta.

---

## G. DECISÕES TOMADAS (registro — respostas do dono, v1.1)

1. **Lowside:** manter **VNLD5160TR-E** (LCSC C377942). BTF3050TE e
   IRLR2905+TVS ficam só como plano B documentado (seção C.1).
2. **Tracker 5V:** manter o **TLS115D0EJ original** (Mouser/DK; não há na
   LCSC). Ressalva de montagem do exposed pad registrada na seção C.2.
3. **Placa:** **180×120 mm, 4 conectores na borda longa única.**
   Contingência registrada na seção E caso o drawing TE do header exceda
   ~42 mm efetivos.
4. **LED único:** populado em **PE5 (running/heartbeat)** — pisca sempre que
   o firmware roda, diagnóstico sem ambiguidade ("o que funciona sem dúvida
   de erro"). Footprints DNP em PE3/PE4/PE6.
5. **Keying:** C1=key 1 (3-1437290-7), C2=key 2 (3-1437290-8), C3=key 3
   (PN a fixar na compra), **C4=key 1 repetido**, nas extremidades opostas
   da borda e com identificação de cor no housing.
6. **Driver de ignição:** **TC4427ACOA713** (LCSC C144234) — pin-compatível
   e funcionalmente equivalente ao MIC4427 (mesma família Microchip, dual
   1,5 A, 4,5–18 V). MIC4427YM via Mouser fica como alternativa direta.
7. **ETB no C2:** validado (melhor funcionalmente; compatibilidade com
   firmware não é afetada — pinos do MCU idênticos ao contrato).
8. **Posição dos pinos nos conectores:** sem relevância para o dono — o
   layout pode reordenar livremente para otimizar chicote/placa (regras de
   pares adjacentes e separação de retornos mantidas; YAMLs acompanham).
   Vale também para a corrente do ETB: o layout pode paralelar as reservas
   adjacentes (11/24 do C2) com as fases do ETB se o roteamento permitir.
9. **AUX_SPI CS = PG15** e reserva = PG0 — mantidos (pinos livres do
   contrato, sem objeção).
10. **12V_SW da expansão = 12v_PROT** (rail protegido da ECU) — mantido.

---

*Fontes web: links inline nas seções C.1–C.4. Evidências de repositório:
citadas por arquivo nas seções A, B e D. Contrato: `PINOUT-CONTRACT.md`
(cópia nesta pasta).*
