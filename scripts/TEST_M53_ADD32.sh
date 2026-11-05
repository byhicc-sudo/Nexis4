#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
command -v ngspice >/dev/null || { echo "ngspice required"; exit 2; }
python3 -m py_compile tests/check_m53_add32_mos.py
python3 tests/check_m53_add32_mos.py
