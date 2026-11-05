#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 -m py_compile tests/create_electrum_wallet.py
python3 tests/create_electrum_wallet.py
