# BABM 90-LZ constraint boundary (M62)

## Bit convention
The C++ `Digest` is the 32-byte SHA256d digest in SHA big-endian byte order. Bitcoin's displayed block hash is the reversed digest; `lz60` counts leading zeros in that reversed representation.

## Exact constraints on final second SHA
Let `S64=(a64,b64,c64,d64,e64,f64,g64,h64)` be the working state after 64 rounds, before feedforward, and `IV[0..7]` the SHA-256 IV. The 90-LZ condition is **exactly**:

- `h64 + IV[7] == 0 (mod 2^32)` (32 bits)
- `g64 + IV[6] == 0 (mod 2^32)` (32 bits)
- `((f64 + IV[5]) & 0xC0FFFFFF) == 0` (26 bits)

Since SHA rounds shift `e` to `f`, `g`, `h`, these become:

- after round index 60: `e61 == 0xA41F32E7`
- after round index 61: `e62 == 0xE07C2655`
- after round index 62: `((e63 + IV[5]) & 0xC0FFFFFF) == 0`

These are 90 exact necessary-and-sufficient bits for the final hash, not 90 independent restrictions on nonce/extranonce2. All are checked **after** the first SHA and most of the second SHA.

## Backward relation, not a free pruning rule
At round `t`, with previous state `(a,b,c,d,e,f,g,h)`:

`T1 = h + Sigma1(e) + Ch(e,f,g) + K[t] + W[t]`
`e_next = d + T1`

Thus any target `e_next` requires
`W[t] = e_next - d - h - Sigma1(e) - Ch(e,f,g) - K[t] (mod 2^32)`.

But `d,h,e,f,g` at rounds 60..62 are functions of the **same** unknown nonce/extranonce2 and of prior rounds. Substituting this equation does not produce a nonce-only restriction unless those states can be computed independently of the candidate, or a rigorously proved candidate-independent necessary condition is derived. Simply evaluating this relation after 60 rounds is not early pruning.

## Job-dependent dependency chain
`extranonce2 -> coinbase -> coinbase SHA256d -> merkle branch hashes -> 80-byte header -> header SHA256 -> second SHA256 -> target90`.

`nonce` affects the final four header bytes; `nTime` affects the header; `extranonce2` changes the merkle root. A fixed-job SMT model is not valid for a new job without rebinding all of these inputs.

## Acceptance criteria for any future prehash filter
1. A predicate is evaluated **before** the SHA work it claims to save.
2. A mathematical proof establishes `target90(header) => predicate(header)` for every permitted header.
3. On independent vectors, full SHA256d and the proposed predicate agree on all known target90 hits; random low-LZ tests alone are insufficient to establish zero false negatives.
4. Log evaluated, rejected, admitted, and independently audited counts separately. No speedup or 90-LZ hit claim without measured evidence.

Current implementation: exact late gate + live reverse-round witness; **no proven prehash candidate filter**.
