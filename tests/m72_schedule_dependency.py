#!/usr/bin/env python3
"""M72: exact SHA256d second-pass schedule dependencies, no mining advantage claimed."""
import hashlib
import random
MASK=0xffffffff
def rr(x,n):return ((x>>n)|(x<<(32-n)))&MASK
def s0(x):return rr(x,7)^rr(x,18)^(x>>3)
def s1(x):return rr(x,17)^rr(x,19)^(x>>10)
def schedule(first):
    assert len(first)==32
    w=[int.from_bytes(first[i:i+4],"big") for i in range(0,32,4)]
    w += [0x80000000]+[0]*6+[256]
    for i in range(16,64):
        w.append((w[i-16]+s0(w[i-15])+w[i-7]+s1(w[i-2]))&MASK)
    return w
def main():
    rng=random.Random(72)
    n=10000
    changed=[0]*64
    for _ in range(n):
        first=hashlib.sha256(rng.randbytes(80)).digest()
        w=schedule(first)
        assert w[8]==0x80000000 and w[9:15]==[0]*6 and w[15]==256
        for i in range(16,64):
            assert w[i]==(w[i-16]+s0(w[i-15])+w[i-7]+s1(w[i-2]))&MASK
        assert w[16]==(w[0]+s0(w[1]))&MASK
        assert w[17]==(w[1]+s0(w[2])+s1(256))&MASK
        assert w[23]==(w[7]+s0(w[8])+w[16]+s1(w[21]))&MASK
        altered=bytearray(first)
        bit=rng.randrange(256)
        altered[bit//8]^=1<<(bit%8)
        other=schedule(bytes(altered))
        for i in range(64):
            changed[i]+=(w[i]!=other[i])
        assert w[8:16]==other[8:16]
    print("PASS M72 schedule_recurrence=10000 fixed_W8_W15=10000 W16_W17_W23=10000")
    print("CHANGED_WORD_COUNTS",",".join(f"W{i}:{changed[i]}" for i in range(64)))
    print("BOUNDARY: observed word sensitivity is not an exact bit constraint or prehash nonce filter")
if __name__=="__main__":main()
