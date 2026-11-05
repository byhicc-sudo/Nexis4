#!/usr/bin/env python3
"""Offline-only Stratum V1 protocol parser and Bitcoin job construction tests.
No network connection and no share submission.
"""
import hashlib,json,struct,sys,traceback
def sha(x):return hashlib.sha256(hashlib.sha256(x).digest()).digest()
def header(version,prevhash,merkle,ntime,nbits,nonce):
 assert len(prevhash)==64 and len(merkle)==64
 return struct.pack("<I",int(version,16))+bytes.fromhex(prevhash)[::-1]+bytes.fromhex(merkle)[::-1]+struct.pack("<III",int(ntime,16),int(nbits,16),nonce)
def merkle_root(coinbase,branches):
 h=sha(coinbase)
 for branch in branches:
  assert len(branch)==64
  h=sha(h+bytes.fromhex(branch))
 return h
def meets_share(hashbytes,difficulty):
 # Bitcoin difficulty-1 target: 0x00000000FFFF0000... (256-bit)
 target=(0xffff << 208)//difficulty
 return int.from_bytes(hashbytes,"little")<=target
def framing(parts):
 buffer=b"";messages=[]
 for chunk in parts:
  buffer+=chunk
  while b"\n" in buffer:
   line,buffer=buffer.split(b"\n",1)
   if line.strip():messages.append(json.loads(line))
 return messages,buffer
def check():
 genesis=bytes.fromhex("01000000"+"00"*32+"3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a"+"29ab5f49"+"ffff001d"+"1dac2b7c")
 assert len(genesis)==80
 assert sha(genesis)[::-1].hex()=="000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
 built=header("00000001","00"*32,"4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b","495fab29","1d00ffff",0x7c2bac1d)
 assert built==genesis
 assert merkle_root(b"test",[])==sha(b"test")
 assert merkle_root(b"test",["11"*32])==sha(sha(b"test")+bytes.fromhex("11"*32))
 m={"id":1,"method":"mining.notify","params":["job","prev","coin1","coin2",[],"version","bits","time",True]}
 raw=json.dumps(m).encode()+b"\n"
 assert framing([raw[:7],raw[7:22],raw[22:]])==([m],b"")
 assert meets_share(sha(genesis),1)
 assert not meets_share(b"\xff"*32,1)
 assert meets_share(b"\x00"*32,1000000)
 print("STRATUM-OFFLINE 8/8 PASS: genesis, header, merkle x2, framing, difficulty x3")
if __name__=="__main__":
 try:check()
 except Exception as e:\n  traceback.print_exc()\n  print("STRATUM-OFFLINE FAIL",repr(e));sys.exit(1)
