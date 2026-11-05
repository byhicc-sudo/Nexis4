#!/usr/bin/env python3
"""M43: full SHA-256d via 16 two-bit quaternary symbols per 32-bit word.
Logical architecture model, NOT transistor-level hardware.
"""
import hashlib,json,pathlib,random,struct,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tests"))
from check_m42_sha256d import K, INIT, HEADER, KNOWN, sha256 as reference_sha256
OUT=ROOT/"results/m43";OUT.mkdir(parents=True,exist_ok=True)
MASK=0xffffffff
def enc(x):
    assert 0<=x<=MASK
    return tuple((x>>(2*i))&3 for i in range(16))
def dec(q):
    assert len(q)==16 and all(isinstance(d,int) and 0<=d<4 for d in q)
    return sum(d<<(2*i) for i,d in enumerate(q))
def qxor(a,b):return tuple(x^y for x,y in zip(a,b))
def qand(a,b):return tuple(x&y for x,y in zip(a,b))
def qnot(a):return tuple(x^3 for x in a)
def qadd(a,b):
    carry=0; out=[]
    for x,y in zip(a,b):
        v=x+y+carry
        out.append(v&3)
        carry=v>>2
    return tuple(out)
def qrotr(a,n):
    n%=32
    bits=[(a[i//2]>>(i%2))&1 for i in range(32)]
    return tuple(bits[(2*i+n)%32] | (bits[(2*i+1+n)%32]<<1) for i in range(16))
def qshr(a,n):
    bits=[(a[i//2]>>(i%2))&1 for i in range(32)]
    return tuple((bits[2*i+n] if 2*i+n<32 else 0) |
        ((bits[2*i+1+n] if 2*i+1+n<32 else 0)<<1) for i in range(16))
def xor3(a,b,c):return qxor(qxor(a,b),c)
def add_many(*words):
    z=enc(0)
    for word in words:z=qadd(z,word)
    return z
def sha_q(data):
    pad=data+b"\x80"+b"\x00"*((55-len(data))%64)+struct.pack(">Q",len(data)*8)
    h=[enc(x) for x in INIT]
    for off in range(0,len(pad),64):
        w=[enc(x) for x in struct.unpack(">16I",pad[off:off+64])]
        for i in range(16,64):
            s0=xor3(qrotr(w[i-15],7),qrotr(w[i-15],18),qshr(w[i-15],3))
            s1=xor3(qrotr(w[i-2],17),qrotr(w[i-2],19),qshr(w[i-2],10))
            w.append(add_many(w[i-16],s0,w[i-7],s1))
        a,b,c,d,e,f,g,hh=h
        for i in range(64):
            big1=xor3(qrotr(e,6),qrotr(e,11),qrotr(e,25))
            ch=qxor(qand(e,f),qand(qnot(e),g))
            t1=add_many(hh,big1,ch,enc(K[i]),w[i])
            big0=xor3(qrotr(a,2),qrotr(a,13),qrotr(a,22))
            maj=xor3(qand(a,b),qand(a,c),qand(b,c))
            t2=add_many(big0,maj)
            a,b,c,d,e,f,g,hh=qadd(t1,t2),a,b,c,qadd(d,t1),e,f,g
        h=[qadd(x,y) for x,y in zip(h,(a,b,c,d,e,f,g,hh))]
    return struct.pack(">8I",*(dec(x) for x in h))
rng=random.Random(43)
ops=0
for _ in range(1000):
    a=rng.getrandbits(32);b=rng.getrandbits(32);n=rng.randrange(32)
    qa,qb=enc(a),enc(b)
    assert dec(qxor(qa,qb))==a^b
    assert dec(qand(qa,qb))==a&b
    assert dec(qnot(qa))==(a^MASK)
    assert dec(qadd(qa,qb))==(a+b)&MASK
    assert dec(qrotr(qa,n))==((a>>n)|(a<<(32-n)))&MASK if n else dec(qrotr(qa,n))==a
    assert dec(qshr(qa,n))==a>>n
    ops+=6
print(f"M43 primitives: PASS {ops} randomized checks")
cases=[("genesis",HEADER),("genesis_nonce_plus_1",HEADER[:-4]+struct.pack("<I",int.from_bytes(HEADER[-4:],"little")+1))]
cases += [(f"random_header_{i}",rng.randbytes(80)) for i in range(8)]
records=[]
for name,header in cases:
    first=sha_q(header)
    second=sha_q(first)
    expected=hashlib.sha256(hashlib.sha256(header).digest()).digest()
    match=first==hashlib.sha256(header).digest() and second==expected
    if name=="genesis":match=match and second[::-1].hex()==KNOWN
    print(f"M43 {name}: {'PASS' if match else 'FAIL'} hash={second[::-1].hex()}")
    records.append({"case":name,"match":match,"sha256d_display":second[::-1].hex()})
(OUT/"metrics.json").write_text(json.dumps({"architecture":"16 base-4 symbols per 32-bit word, 2 bits/symbol","random_primitive_checks":ops,"sha256d_cases":records,"limitations":["software quaternary logic emulation, not physical transistor SHA hardware","no timing, area, energy or H/s measurement"]},indent=2)+"\n")
if not all(r["match"] for r in records):sys.exit("FAIL M43")
print(f"PASS M43 full quaternary-symbol SHA-256d {len(records)}/{len(records)}")
