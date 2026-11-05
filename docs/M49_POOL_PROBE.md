# M49 live Stratum probe (read-only)

Usage (example; replace host, port and worker with pool-provided values):

```bash
bash scripts/TEST_M49_POOL.sh --host POOL_HOST --port POOL_PORT --user YOUR_WORKER --seconds 30 --max-jobs 3
```

For a TLS-enabled Stratum endpoint, add `--tls` only when supported by
the selected pool port. Password defaults to `x`; `--password` is optional.

This program sends only `mining.subscribe` and `mining.authorize`.
There is **no** `mining.submit` implementation and **no** nonce search.
A received job is used to construct one sample header with extranonce2=0
and nonce=0, then independently hash it with Python hashlib.

The output `results/m49_pool/report.json` records connection state,
subscription/authorization, difficulty notifications and validated job
headers. It does not demonstrate mining performance or a four-voltage
SHA-256d implementation.

Safety: avoid including real credentials in shell history; use a
dedicated pool worker and a non-sensitive worker password if possible.
