#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
mkdir -p results/m57_round3
g++ -std=c++17 -O3 -DNDEBUG -Wall -Wextra tests/m57_round3_exact.cpp -o results/m57_round3/test
results/m57_round3/test "${1:-2048}" | tee results/m57_round3/report.txt
