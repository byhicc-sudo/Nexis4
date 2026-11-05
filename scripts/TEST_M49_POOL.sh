#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 -m py_compile tests/check_m48_stratum_strict.py tests/m49_pool_probe.py
python3 tests/m49_pool_probe.py "$@"
