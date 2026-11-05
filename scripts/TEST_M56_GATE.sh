#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
mkdir -p results/m56_gate
g++ -std=c++17 -O3 -DNDEBUG -Wall -Wextra tests/m56_gate_benchmark.cpp -o results/m56_gate/benchmark
results/m56_gate/benchmark "${1:-10000}" | tee results/m56_gate/report.txt
