#!/bin/sh
# Pipeline completo de regeneracao/validacao do Proteus-BR.
set -e
cd "$(dirname "$0")"
python3 build_br.py
python3 gen_root.py
cd ..
kicad-cli sch export netlist --format kicadxml -o /tmp/proteus-br.xml proteus-br.kicad_sch
cd tools
python3 validate_contract.py /tmp/proteus-br.xml ../reports/contract-validation.txt
python3 erc_lite.py /tmp/proteus-br.xml ../reports/erc-lite.txt
python3 gen_bom.py /tmp/proteus-br.xml
cd ..
kicad-cli sch export pdf -o proteus-br-schematic.pdf proteus-br.kicad_sch
echo "== pipeline OK =="
