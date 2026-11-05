#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p results/full_sha_rtl
iverilog -g2012 -s tb_sha256d -o results/full_sha_rtl/full_sha.vvp rtl/nexis4_sha256d80.v tests/tb_sha256d80.v
vvp results/full_sha_rtl/full_sha.vvp | tee results/full_sha_rtl/run.log
