#!/usr/bin/env python3
"""M69: exact backwards mapping of 50 display-leading-zero bits into SHA-256 round states.
No prehash pruning is claimed. Synthetic states are NOT mined headers.
"""
import random

MASK = 0xffffffff
IV5 = 0x9b05688c
IV6 = 0x1f83d9ab
IV7 = 0x5be0cd19

def gate50_from_round_states(e61, e62):
    # After 64 rounds: h64 = e61, g64 = e62.
    # SHA output word 7 = h64+IV7; word 6 = g64+IV6.
    return ((e61 + IV7) & MASK) == 0 and (((e62 + IV6) & MASK) & 0xffffc000) == 0

def gate50_from_digest(d):
    return 256 - int.from_bytes(d, "little").bit_length() >= 50

def digest_from_final_state(state):
    iv = (0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
          0x510e527f,IV5,IV6,IV7)
    return b"".join(((x+y)&MASK).to_bytes(4,"big") for x,y in zip(state,iv))

def check_state(state):
    d = digest_from_final_state(state)
    # h64=e61; g64=e62; last two state words are g64,h64.
    assert gate50_from_round_states(state[7],state[6]) == gate50_from_digest(d)

def main():
    rng=random.Random(69)
    for _ in range(100000):
        check_state(tuple(rng.getrandbits(32) for _ in range(8)))
    e61=(-IV7)&MASK
    positives=0
    for w6 in (0,1,0x3fff):
        e62=(w6-IV6)&MASK
        check_state((0,0,0,0,0,0,e62,e61))
        assert gate50_from_round_states(e61,e62)
        positives+=1
    for w6 in (0x4000,0x8000,0x10000,0x80000000):
        e62=(w6-IV6)&MASK
        check_state((0,0,0,0,0,0,e62,e61))
        assert not gate50_from_round_states(e61,e62)
    assert not gate50_from_round_states((e61+1)&MASK,(-IV6)&MASK)
    print("PASS M69 random_states=100000 synthetic_positive=3 synthetic_negative=5 exact_e61_e62_mapping=1")
    print("BOUNDARY: final-state identities verified; nonce/extranonce2/nTime prefilter NOT established")

if __name__=="__main__":
    main()
