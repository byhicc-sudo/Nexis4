#!/usr/bin/env python3
"""Independent deterministic regression for exact 50-leading-zero digest word gates."""
import hashlib
import random

IV6 = 0x1F83D9AB
IV7 = 0x5BE0CD19
MASK18 = 0xFFFFC000

def lz_display(d):
    return 256 - int.from_bytes(d, "little").bit_length()

def gate_from_final_words(g, h):
    # SHA-256 output bytes 24..27 = g+IV6, bytes 28..31 = h+IV7.
    word7 = (h + IV7) & 0xFFFFFFFF
    word6 = (g + IV6) & 0xFFFFFFFF
    return word7 == 0 and (word6 & MASK18) == 0

def test():
    rng = random.Random(20261105)
    for _ in range(10000):
        d = rng.randbytes(32)
        g = (int.from_bytes(d[24:28], "big") - IV6) & 0xFFFFFFFF
        h = (int.from_bytes(d[28:32], "big") - IV7) & 0xFFFFFFFF
        assert gate_from_final_words(g, h) == (lz_display(d) >= 50)
    for word6 in (0, 1, 0x3FFF):
        g = (word6 - IV6) & 0xFFFFFFFF
        h = (-IV7) & 0xFFFFFFFF
        assert gate_from_final_words(g, h)
    for word6 in (0x4000, 0x8000, 0x10000, 0x40000000, 0x80000000):
        assert not gate_from_final_words((word6-IV6)&0xFFFFFFFF, (-IV7)&0xFFFFFFFF)
    assert not gate_from_final_words((-IV6)&0xFFFFFFFF, (1-IV7)&0xFFFFFFFF)
    # Independent real SHA256d digest smoke test; no artificial 50-LZ claim.
    for i in range(1000):
        msg = i.to_bytes(4, "little")
        d = hashlib.sha256(hashlib.sha256(msg).digest()).digest()
        g = (int.from_bytes(d[24:28], "big") - IV6) & 0xFFFFFFFF
        h = (int.from_bytes(d[28:32], "big") - IV7) & 0xFFFFFFFF
        assert gate_from_final_words(g, h) == (lz_display(d) >= 50)
    print("PASS target50_mask random=10000 synthetic_positive=3 synthetic_negative=6 sha256d=1000")

if __name__ == "__main__":
    test()
