# M69 — 50 LZ exact backward boundary (SHA256d, radix-4)

## Exact end-state condition

Bitcoin display hash reverses the 32 bytes of the SHA256d digest. Therefore 50 leading zero display bits require SHA256 output word 7 to be zero (32 bits), and the high 18 bits of SHA256 output word 6 to be zero.

After the second SHA's 64 rounds (0-based indices 0..63), the SHA-256 shift register satisfies:
- h64 = e61 (three-register delay)
- g64 = e62 (two-register delay)

After feed-forward, output word7 = (h64 + IV7) mod 2^32 and output word6 = (g64 + IV6) mod 2^32.

Thus the **necessary and sufficient** 50-LZ constraints are:
- e61 == (-IV7) mod 2^32 = 0xA41F32E7
- ((e62 + IV6) mod 2^32) & 0xFFFFC000 == 0

The second condition permits 2^14 values for e62, not one value. No constraints on e63 are needed for 50 LZ.

## Backward propagation boundary

The SHA round e update is e(t+1) = d(t) + T1(t) mod 2^32, where T1(t) = h(t) + Sigma1(e(t)) + Ch(e(t),f(t),g(t)) + K[t] + W[t] mod 2^32.

This can be inverted *conditionally*: T1(t) = e(t+1) - d(t) mod 2^32. But d(t), the remaining state registers, and message schedule words W[t] are generally unknown if only the target 50 output bits are given.

Consequently the two exact output gates do NOT yet imply any provable restriction on a nonce, extranonce2, or nTime bit before the first SHA. They are exact output verification gates, not an early candidate filter.

## Audit discipline

- Keep NEXIS4_BABM_EARLY=0 for full scoring.
- Compare Quat and Binary full SHA256d results and independently audit with hashlib.
- Test synthetic positive states separately from genuine 80-byte header preimages; do not report them as mined 50-LZ hits.
- Any proposed earlier gate must prove zero false negatives for *all* possible headers, not merely pass a sample.
