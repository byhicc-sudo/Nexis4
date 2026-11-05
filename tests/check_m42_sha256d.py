#!/usr/bin/env python3
"""M42: independent full SHA-256d implementation, 80-byte Bitcoin header."""
import hashlib, json, pathlib, struct, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"results/m42"
OUT.mkdir(parents=True,exist_ok=True)
K=[
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
INIT=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]
MASK=0xffffffff
def rotr(x,n):return ((x>>n)|(x<<(32-n)))&MASK
def sha256(data):
    bitlen=len(data)*8
    padded=data+b"\x80"+b"\x00"*((55-len(data))%64)+struct.pack(">Q",bitlen)
    h=INIT[:]
    blocks=[]
    for off in range(0,len(padded),64):
        w=list(struct.unpack(">16I",padded[off:off+64]))
        for i in range(16,64):
            a=rotr(w[i-15],7)^rotr(w[i-15],18)^(w[i-15]>>3)
            b=rotr(w[i-2],17)^rotr(w[i-2],19)^(w[i-2]>>10)
            w.append((w[i-16]+a+w[i-7]+b)&MASK)
        a,b,c,d,e,f,g,hh=h
        for i in range(64):
            s1=rotr(e,6)^rotr(e,11)^rotr(e,25)
            ch=(e&f)^((~e)&g)
            t1=(hh+s1+ch+K[i]+w[i])&MASK
            s0=rotr(a,2)^rotr(a,13)^rotr(a,22)
            maj=(a&b)^(a&c)^(b&c)
            t2=(s0+maj)&MASK
            a,b,c,d,e,f,g,hh=(t1+t2)&MASK,a,b,c,(d+t1)&MASK,e,f,g
        h=[(x+y)&MASK for x,y in zip(h,(a,b,c,d,e,f,g,hh))]
        blocks.append({"message_block":off//64,"rounds":64,"schedule_words":64})
    return struct.pack(">8I",*h),blocks
# Bitcoin genesis block header in wire byte order.
HEADER=bytes.fromhex(
"01000000"+
"00"*32+
"3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a"+
"29ab5f49"+"ffff001d"+"1dac2b7c")
assert len(HEADER)==80
KNOWN="000000000019d6689c085ae165831e93"+"4ff763ae46a2a6c172b3f1b60a8ce26f"
def run(header):
    first,b1=sha256(header)
    second,b2=sha256(first)
    reference=hashlib.sha256(hashlib.sha256(header).digest()).digest()
    return first,second,reference,b1,b2
tests=[]
for name,header in [("genesis",HEADER),("genesis_nonce_plus_1",HEADER[:-4]+struct.pack("<I",int.from_bytes(HEADER[-4:],"little")+1))]:
    first,second,reference,b1,b2=run(header)
    ok=second==reference and first==hashlib.sha256(header).digest()
    if name=="genesis":ok=ok and second[::-1].hex()==KNOWN
    tests.append({"name":name,"header_hex":header.hex(),"first_sha256_hex":first.hex(),
      "sha256d_raw_hex":second.hex(),"bitcoin_display_hash":second[::-1].hex(),
      "reference_match":ok,"first_pass_blocks":b1,"second_pass_blocks":b2})
    print(f"M42 {name}: {'PASS' if ok else 'FAIL'} hash={second[::-1].hex()}")
(OUT/"metrics.json").write_text(json.dumps({"implementation":"Python 32-bit SHA256 compression, full padding and schedule","tests":tests,
"limits":["Software reference only; no NEXIS-4 hardware SHA circuit","No mining speed claim"]},indent=2)+"\n")
if not all(t["reference_match"] for t in tests):sys.exit("FAIL M42")
print("PASS M42 full SHA-256d verified against hashlib and Bitcoin genesis")
