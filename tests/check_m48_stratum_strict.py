#!/usr/bin/env python3
"""M48 strict offline Stratum V1 job pipeline; no sockets or share submission."""
import hashlib,json,struct,unittest
from fractions import Fraction
MAX32=(1<<32)-1
DIFF1=0xffff << 208
def sha256d(data):
 return hashlib.sha256(hashlib.sha256(data).digest()).digest()
def hx(value,size,name):
 if not isinstance(value,str) or len(value)!=size*2:
  raise ValueError(f"{name} must be {size} bytes of hex")
 try:return bytes.fromhex(value)
 except ValueError as exc:raise ValueError(f"{name} invalid hex") from exc
def target_from_difficulty(value):
 try:d=Fraction(str(value))
 except (ValueError,ZeroDivisionError) as exc:raise ValueError("invalid difficulty") from exc
 if d<=0:raise ValueError("difficulty must be positive")
 return min((1<<256)-1,DIFF1*d.denominator//d.numerator)
def compact_target(bits):
 bits=int(bits,16) if isinstance(bits,str) else bits
 if not isinstance(bits,int) or not 0<=bits<=MAX32:raise ValueError("invalid nbits")
 size=bits>>24;word=bits&0x007fffff
 if bits&0x00800000 or word==0:raise ValueError("negative or zero compact target")
 value=word>>(8*(3-size)) if size<=3 else word<<(8*(size-3))
 if value<=0 or value>=1<<256:raise ValueError("compact target overflow")
 return value
def make_header(version,prevhash,merkle,ntime,nbits,nonce):
 if not isinstance(nonce,int) or not 0<=nonce<=MAX32:raise ValueError("nonce out of range")
 return (hx(version,4,"version")[::-1]+hx(prevhash,32,"prevhash")[::-1]
  +merkle+hx(ntime,4,"ntime")[::-1]+hx(nbits,4,"nbits")[::-1]+struct.pack("<I",nonce))
def make_job(params,extranonce1,extranonce2,extranonce2_size,nonce):
 if not isinstance(params,list) or len(params)!=9:raise ValueError("notify requires nine params")
 jobid,prevhash,coinb1,coinb2,branches,version,nbits,ntime,clean=params
 if not isinstance(jobid,str) or not jobid:raise ValueError("invalid job id")
 if type(clean) is not bool:raise ValueError("clean_jobs must be boolean")
 if not isinstance(branches,list):raise ValueError("branches must be list")
 if not isinstance(extranonce2_size,int) or not 0<=extranonce2_size<=32:raise ValueError("invalid extranonce2 size")
 ex1=hx(extranonce1,len(extranonce1)//2,"extranonce1")
 ex2=hx(extranonce2,extranonce2_size,"extranonce2")
 cb=hx(coinb1,len(coinb1)//2,"coinb1")+ex1+ex2+hx(coinb2,len(coinb2)//2,"coinb2")
 root=sha256d(cb)
 for i,b in enumerate(branches):root=sha256d(root+hx(b,32,f"branch {i}"))
 header=make_header(version,prevhash,root,ntime,nbits,nonce)
 assert len(header)==80
 digest=sha256d(header)
 return {"job_id":jobid,"header":header.hex(),"digest":digest[::-1].hex(),
 "meets_network_target":int.from_bytes(digest,"little")<=compact_target(nbits),
 "merkle_internal":root.hex(),"clean_jobs":clean}
class Framer:
 def __init__(self,limit=1048576):self.buf=b"";self.limit=limit
 def feed(self,chunk):
  if not isinstance(chunk,bytes):raise TypeError("bytes required")
  self.buf+=chunk;messages=[]
  while b"\n" in self.buf:
   line,self.buf=self.buf.split(b"\n",1)
   if len(line)>self.limit:raise ValueError("oversized Stratum message")
   if line.strip():messages.append(json.loads(line))
  if len(self.buf)>self.limit:raise ValueError("oversized incomplete message")
  return messages
class Tests(unittest.TestCase):
 def setUp(self):
  self.genesis_merkle="4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"
  self.params=["job0","00"*32,"","",[],"00000001","1d00ffff","495fab29",True]
 def test_genesis_header(self):
  raw=make_header("00000001","00"*32,bytes.fromhex(self.genesis_merkle)[::-1],"495fab29","1d00ffff",0x7c2bac1d)
  self.assertEqual(sha256d(raw)[::-1].hex(),"000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f")
 def test_genesis_network_target(self):
  self.assertEqual(compact_target("1d00ffff"),DIFF1)
 def test_difficulty_one(self):self.assertEqual(target_from_difficulty(1),DIFF1)
 def test_difficulty_fraction(self):self.assertEqual(target_from_difficulty("0.5"),min((1<<256)-1,DIFF1*2))
 def test_difficulty_reject_zero(self):
  with self.assertRaises(ValueError):target_from_difficulty(0)
 def test_difficulty_reject_negative(self):
  with self.assertRaises(ValueError):target_from_difficulty(-1)
 def test_compact_negative(self):
  with self.assertRaises(ValueError):compact_target("1d80ffff")
 def test_compact_zero(self):
  with self.assertRaises(ValueError):compact_target("1d000000")
 def test_nonce_max(self):self.assertEqual(len(make_header("00000001","00"*32,b"\0"*32,"495fab29","1d00ffff",MAX32)),80)
 def test_nonce_overflow(self):
  with self.assertRaises(ValueError):make_header("00000001","00"*32,b"\0"*32,"495fab29","1d00ffff",MAX32+1)
 def test_nonce_negative(self):
  with self.assertRaises(ValueError):make_header("00000001","00"*32,b"\0"*32,"495fab29","1d00ffff",-1)
 def test_notify_shape(self):
  with self.assertRaises(ValueError):make_job(self.params[:-1],"aa","bb",1,0)
 def test_extranonce_size(self):
  with self.assertRaises(ValueError):make_job(self.params,"aa","bbcc",1,0)
 def test_merkle_branch(self):
  params=self.params.copy();params[4]=["11"*32]
  result=make_job(params,"aa","bb",1,0)
  cb=bytes.fromhex("aabb");expected=sha256d(sha256d(cb)+bytes.fromhex("11"*32))
  self.assertEqual(result["merkle_internal"],expected.hex())
 def test_job_digest(self):
  result=make_job(self.params,"aa","bb",1,0)
  self.assertEqual(result["digest"],sha256d(bytes.fromhex(result["header"]))[::-1].hex())
 def test_job_header_length(self):self.assertEqual(len(bytes.fromhex(make_job(self.params,"aa","bb",1,0)["header"])),80)
 def test_invalid_prevhash(self):
  params=self.params.copy();params[1]="x"
  with self.assertRaises(ValueError):make_job(params,"aa","bb",1,0)
 def test_invalid_branch(self):
  params=self.params.copy();params[4]=["ff"]
  with self.assertRaises(ValueError):make_job(params,"aa","bb",1,0)
 def test_clean_jobs_type(self):
  params=self.params.copy();params[8]=1
  with self.assertRaises(ValueError):make_job(params,"aa","bb",1,0)
 def test_framing_fragmented(self):
  f=Framer();m={"method":"mining.notify","params":self.params}
  raw=json.dumps(m).encode()+b"\n"
  self.assertEqual(f.feed(raw[:3]),[])
  self.assertEqual(f.feed(raw[3:]),[m])
 def test_framing_multiple(self):
  f=Framer();self.assertEqual(f.feed(b'{"id":1}\n{"id":2}\n'),[{"id":1},{"id":2}])
 def test_framing_invalid_json(self):
  with self.assertRaises(json.JSONDecodeError):Framer().feed(b"{broken}\n")
 def test_framing_oversized(self):
  with self.assertRaises(ValueError):Framer(limit=4).feed(b"abcdef")
 def test_target_high_hash_reject(self):self.assertFalse(int.from_bytes(b"\xff"*32,"little")<=target_from_difficulty(1))
 def test_target_zero_hash_accept(self):self.assertTrue(int.from_bytes(b"\0"*32,"little")<=target_from_difficulty(1000000))
if __name__=="__main__":
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
 result=unittest.TextTestRunner(verbosity=1).run(suite)
 print(f"M48 STRICT STRATUM {result.testsRun-len(result.failures)-len(result.errors)}/{result.testsRun} PASS")
 raise SystemExit(not result.wasSuccessful())
