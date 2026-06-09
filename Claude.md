# Projeto ECU custom (base Proteus)

## Objetivo
Placa ECU própria baseada na rusEFI Proteus. Máximo de features,
custo de produção razoável, e MÁXIMO de componentes soldáveis à mão.
Independência total — sem depender de suporte da comunidade rusEFI.

## Decisões fixas
- Base de hardware: mck1117/proteus (KiCad 5.1.12), fork próprio.
- Canais reduzidos no início (custo/solda), mas EXPANSÍVEIS em etapas:
  preservar footprints, pinos do MCU e roteamento — nunca inutilizar canais.

## A definir (analisar e recomendar — nada pré-decidido)
- MCU: melhor opção (soldável à mão/sem BGA, RAM e flash, custo,
  disponibilidade genuína) e COM FOLGA de pinos/memória p/ expansão futura.
- Firmware: melhor abordagem (target/variante de build e estrutura da board
  config) que permita expandir só populando hardware + ajustando config.
- Quantos canais (low-side / ignição / injeção) popular em cada etapa.
- Encapsulamentos e passivos visando soldagem à mão.
- Estratégia de sourcing dos componentes (genuíno x custo).

## Repos
- ./rusefi    -> firmware (monorepo, mexer só na board config)
- ./proteus   -> hardware KiCad
