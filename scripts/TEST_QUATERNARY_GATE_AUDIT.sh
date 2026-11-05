#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p results/quaternary_gate_audit
iverilog -g2012 -s tb_nexis4_exhaustive -o results/quaternary_gate_audit/tb.vvp rtl/nexis4_alu.v tests/tb_nexis4_exhaustive.v
vvp results/quaternary_gate_audit/tb.vvp | tee results/quaternary_gate_audit/rtl.log
bash scripts/TEST_M38.sh > results/quaternary_gate_audit/mos_buffer.log 2>&1
echo "PASS M38 four-voltage MOS buffer regression (see results/quaternary_gate_audit/mos_buffer.log)"
echo "OPEN: no transistor-level XOR/AND/ADD; no PDK, noise margin, power or timing characterization."
