#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
mkdir -p results/m55_cpp
g++ -std=c++17 -O3 -DNDEBUG -Wall -Wextra tests/m55_cpp_benchmark.cpp -o results/m55_cpp/benchmark
results/m55_cpp/benchmark "${1:-1000}" | tee results/m55_cpp/benchmark.txt
