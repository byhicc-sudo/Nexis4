#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [[ -z "${BTC_WORKER:-}" ]]; then echo 'Set BTC_WORKER to your authorized Bitcoin address.worker'; exit 2; fi
mkdir -p results/m58_live
python3 -u scripts/m58_live_job_lz.py --user "$BTC_WORKER" "$@" | tee -a results/m58_live/session.log
