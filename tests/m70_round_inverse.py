#!/usr/bin/env python3
"""M70: verify exact SHA256 round inversion, and demonstrate schedule dependence.
Synthetic internal states only; no nonce filter or mined header.
"""
import random
from m69_backward_state_test import gate50_from_round_states, MASK, IV6, IV7

def rr(x,n): return ((x>>n)|(x<<(32-n)))&MASK
def s0(x): return rr(x,2)^rr(x,13)^rr(x,22)
def s1(x): return rr(x,6)^rr(x,11)^rr(x,25)
def ch(x,y,z): return (x&y)^((~x)&z)
def maj(x,y,z): return (x&y)^(x&z)^(y&z)
def step(st,w,k):
    a,b,c,d,e,f,g,h=st
    t1=(h+s1(e)+ch(e,f,g)+k+w)&MASK
    t2=(s0(a)+maj(a,b,c))&MASK
    return ((t1+t2)&MASK,a,b,c,(d+t1)&MASK,e,f,g)
def undo(out,w,k):
    A,B,C,D,E,F,G,H=out
    a,b,c,d,e,f,g=B,C,D,F,G,H,0
    # h_old is unknown until we recover t1 via the a update.
    t2=(s0(a)+maj(a,b,c))&MASK
    t1=(A-t2)&MASK
    d=(E-t1)&MASK
    # old g is new h, old f is new g, old e is new f.
    e,f,g=F,G,H
    h=(t1-s1(e)-ch(e,f,g)-k-w)&MASK
    return (a,b,c,d,e,f,g,h)

def main():
    rng=random.Random(70)
    n=50000
    for i in range(n):
        st=tuple(rng.getrandbits(32) for _ in range(8))
        w=rng.getrandbits(32)
        k=rng.getrandbits(32)
        out=step(st,w,k)
        assert undo(out,w,k)==st, ("inverse",i)
        assert step(undo(out,w,k),w,k)==out, ("forward",i)
    # 50-LZ synthetic final states: construct valid final SHA word6/7
    # and reverse the last two rounds with chosen schedule words.
    count=0
    for x in (0,0x10000,0x20000):
        final=list(rng.getrandbits(32) for _ in range(8))
        final[6]=(x-IV6)&MASK
        final[7]=(-IV7)&MASK
        assert gate50_from_round_states(final[7],final[6])
        k63,w63,k62,w62=[rng.getrandbits(32) for _ in range(4)]
        state62=undo(undo(tuple(final),w63,k63),w62,k62)
        assert step(step(state62,w62,k62),w63,k63)==tuple(final)
        count+=1
    # Unknown schedule is not eliminated by inverse: for the same
    # round output, different w yields different preceding h.
    out=tuple(rng.getrandbits(32) for _ in range(8))
    k=rng.getrandbits(32)
    a=undo(out,0,k)
    b=undo(out,1,k)
    assert a[:7]==b[:7] and a[7]!=b[7]
    print(f"PASS M70 random_roundtrip={n} synthetic_target50_roundtrip={count} schedule_ambiguity=PASS")
    print("BOUNDARY no nonce/extranonce2/nTime restriction, no zero-false-negative prehash filter")

if __name__=="__main__":main()
