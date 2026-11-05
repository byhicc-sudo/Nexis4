#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
: "${BTC_WORKER:=bc1quzdw7vhxegc68nd4j9vur4n3hcsjcxyrfdznhy.nexis4}"
if [[ "$BTC_WORKER" == "BITCOIN_ADRESIN.worker1" || "$BTC_WORKER" == BITCOIN_ADRESIN* ]]; then
  echo "M59_FIX_PLACEHOLDER_WORKER: replacing placeholder BTC_WORKER with verified CKPool worker"
  BTC_WORKER='bc1quzdw7vhxegc68nd4j9vur4n3hcsjcxyrfdznhy.nexis4'
fi
trap 'echo "M60_STOP_REQUESTED"; exit 130' INT TERM
mkdir -p results/m59_live
g++ -std=c++17 -O3 -DNDEBUG tests/m59_live_engine.cpp -o results/m59_live/nexis4_engine
# Retry transient authorization errors, switch CKPool endpoint after a failed attempt.
# Preserve user-specified --host arguments; do not override them.
for attempt in 1 2 3; do
  if (( attempt == 1 )); then host=stratum.ckpool.org; else host=solo.ckpool.org; fi
  echo "M59_CONNECTION_ATTEMPT $attempt host=$host"
  set +e
  python3 -u scripts/m59_live_quat.py --user "$BTC_WORKER" --host "$host" "$@" 2>&1 | tee -a results/m59_live/session.log
  rc=${PIPESTATUS[0]}
  set -e
  if (( rc == 0 )); then
    exit 0
  fi
  if (( rc == 130 || rc == 143 )); then echo "M60_USER_STOP"; exit 0; fi
  if (( attempt < 3 )); then echo "M59_RETRY_IN_3_SECONDS"; sleep 3; fi
done
echo "M59_FAILED_AFTER_3_ATTEMPTS" >&2
exit 1
