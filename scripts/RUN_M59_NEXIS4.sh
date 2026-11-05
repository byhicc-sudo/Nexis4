#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
: "${BTC_WORKER:=bc1quzdw7vhxegc68nd4j9vur4n3hcsjcxyrfdznhy.nexis4}"
mkdir -p results/m59_live
g++ -std=c++17 -O3 -DNDEBUG tests/m59_live_engine.cpp -o results/m59_live/nexis4_engine
python3 -u scripts/m59_live_quat.py --user "$BTC_WORKER" "$@" | tee -a results/m59_live/session.log
