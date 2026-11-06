#!/usr/bin/env python3
"""M71: independent SHA256d second-block schedule and fixed-word audit."""
import hashlib
import random

MASK=0xffffffff
def rr(x,n):return ((x>>n)|(x<<(32-n)))&MASK
def small0(x):return rr(x,7)^rr(x,18)^(x>>3)
def small1(x):return rr(x,17)^rr(x,19)^(x>>10)
def schedule(first):
    assert len(first)==32
    block=first+b'\x80'+bytes(23)+bytes.fromhex('0000000000000100')
    assert len(block)==64
    w=[int.from_bytes(block[i:i+4],'big') for i in range(0,64,4)]
    for i in range(16,64):
        w.append((w[i-16]+small0(w[i-15])+w[i-7]+small1(w[i-2]))&MASK)
    return w
def main():
    rng=random.Random(71)
    n=10000
    for i in range(n):
        header=rng.randbytes(80)
        first=hashlib.sha256(header).digest()
        w=schedule(first)
        assert all(w[j]==int.from_bytes(first[j*4:j*4+4],'big') for j in range(8))
        assert w[8]==0x80000000 and all(w[j]==0 for j in range(9,15))
        assert w[15]==256
        assert w[16]==(w[0]+small0(w[1]))&MASK
        assert w[17]==(w[1]+small0(w[2])+small1(256))&MASK
        assert hashlib.sha256(first).digest()==hashlib.sha256(hashlib.sha256(header).digest()).digest()
        bit=rng.randrange(256)
        altered=bytearray(first);altered[bit//8]^=1<<(bit%8)
        other=schedule(bytes(altered))
        assert w[8:16]==other[8:16]
        assert w[:8]!=other[:8]
        assert w!=other
    print(f"PASS M71 independent_headers={n} fixed_second_block_words=8 variable_first_digest_words=8 schedule_expansion=PASS")
    print("BOUNDARY first-SHA digest is nonce-dependent; no prehash nonce filter established")
if __name__=="__main__":main()
