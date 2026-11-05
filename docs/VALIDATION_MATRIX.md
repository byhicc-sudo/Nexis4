# NEXIS-4 integrated validation matrix

Run: `bash scripts/TEST_ALL.sh --include-slow` (may take several minutes).

## Status rules
- PASS: the invoked test actually ran and returned zero.
- FAIL/TIMEOUT: test executed unsuccessfully.
- BLOCKED_DEPENDENCY: a required local executable is absent.
- NOT_IMPLEMENTED: test file is not present.
- NOT_RUN_SLOW: explicitly skipped unless `--include-slow` is used.
- No test is silently treated as passing.

## Architecture boundaries
M46 uses four-level analog inputs/outputs, MOSFET threshold sensing and
binary CMOS internal truth-table logic. This does **not** mean the full SHA-256d
RTL has been implemented in four-voltage transistors.

The offline Stratum checks exercise message framing, Bitcoin genesis header
byte ordering, merkle hashing and share-target comparison. They do **not**
establish an authenticated live pool connection or an accepted share.

## Outstanding qualification gates
1. Voltage sweeps, PVT corners, noise margin and process models.
2. Transition settle time, glitch monitoring, rail contention, load sweep.
3. Measured integrated current, reference rail power and energy per operation.
4. 32-bit quaternary MOS ALU and complete 192-round SHA-256d transistor network.
5. Cycle-level equivalence, randomized headers, real Bitcoin block vectors.
6. Pool subscribe/authorize/notify/difficulty/extranonce handling, reconnect,
   clean_jobs, duplicate/stale filtering, independent share verification.
7. Explicitly authorized live share submission and pool acceptance audit.
8. Performance, reliability, thermal and energy comparison to a baseline.

Reports: `results/integration/report.json`. Logs are stored alongside it.
