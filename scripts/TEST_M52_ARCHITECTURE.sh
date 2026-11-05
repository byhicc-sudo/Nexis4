#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 -m py_compile tests/check_m52_architecture.py
python3 tests/check_m52_architecture.py
