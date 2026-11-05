#!/usr/bin/env python3
"""M59: live Stratum + NEXIS4 QUAT C++ 90-LZ gate; hashlib only independent audit."""
import argparse,hashlib,json,socket,time,threading,queue,struct,subprocess,os,sys
def h2(b):return hashlib.sha256(hashlib.sha256(b).digest()).digest()
def swap_words(h):
 b=bytes.fromhex(h);return b''.join(b[i:i+4][::-1] for i in range(0,len(b),4))
def lz(d):return 256-int.from_bytes(d,'little').bit_length()
def main():
 p=argparse.ArgumentParser();p.add_argument('--host',default='stratum.ckpool.org');p.add_argument('--port',type=int,default=3333);p.add_argument('--user',required=True);p.add_argument('--password',default='x');p.add_argument('--status-seconds',type=float,default=10);p.add_argument('--batch',type=int,default=256);p.add_argument('--ex2-step',type=int,default=65536)
 a=p.parse_args()
 if not 1<=a.batch<=8192 or a.ex2_step<1:p.error('invalid batch/ex2-step')
 proc=subprocess.Popen(['results/m59_live/nexis4_engine'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
 if not proc.stdout.readline().startswith('M59_READY'):raise RuntimeError('engine startup failed')
 sock=socket.create_connection((a.host,a.port),timeout=15);sock.settimeout(None)
 q=queue.Queue();stop=threading.Event()
 def reader():
  try:
   for line in sock.makefile('rb'):
    try:q.put(json.loads(line))
    except json.JSONDecodeError:print('INVALID_JSON',flush=True)
  except Exception as e:q.put({'_error':str(e)})
  finally:stop.set()
 threading.Thread(target=reader,daemon=True).start()
 def send(m):sock.sendall((json.dumps(m)+'\n').encode())
 send({'id':1,'method':'mining.subscribe','params':['NEXIS4-DIAG/1.0']})
 print('AUTH_REQUEST worker',repr(a.user),'password_length',len(a.password),flush=True)
 send({'id':2,'method':'mining.authorize','params':[a.user,a.password]})
 ex1=None;exsize=0;authorized=False;job=None;nonce=0;ex2_count=0;total=0;best=-1;generation=0
 started=last=time.monotonic()
 print('M59_ACTIVE NEXIS4_QUAT 90LZ_GATE ON; full SHA256d; independent hashlib audit; NO_SUBMIT',flush=True)
 try:
  while not stop.is_set():
   try:
    while True:
     m=q.get_nowait()
     if '_error' in m:raise RuntimeError(m['_error'])
     if m.get('id')==1:
      if m.get('error'):raise RuntimeError(str(m['error']))
      ex1=bytes.fromhex(m['result'][1]);exsize=int(m['result'][2]);print('SUBSCRIBED ex2_size',exsize,flush=True)
     elif m.get('id')==2:
      authorized=m.get('result') is True;print('AUTH_RESPONSE',repr(m),'AUTHORIZED',authorized,flush=True)
      if not authorized:raise RuntimeError('authorization rejected by pool; rerun or use --host solo.ckpool.org')
     elif m.get('method')=='mining.notify':
      job=m['params'];generation+=1;nonce=0;ex2_count=0
      print('NEW_JOB',job[0],'generation',generation,'clean',job[8],flush=True)
     elif m.get('method')=='mining.set_difficulty':print('POOL_DIFFICULTY',m['params'][0],flush=True)
   except queue.Empty:pass
   if not authorized or ex1 is None or job is None:time.sleep(.1);continue
   jid,prev,c1,c2,branches,ver,nbits,ntime,clean=job[:9]
   ex2=ex2_count.to_bytes(exsize,'big')
   merkle=h2(bytes.fromhex(c1)+ex1+ex2+bytes.fromhex(c2))
   for b in branches:merkle=h2(merkle+bytes.fromhex(b))
   prefix=swap_words(ver)+swap_words(prev)+merkle+swap_words(ntime)+swap_words(nbits)
   if len(prefix)!=76:raise RuntimeError('invalid header')
   count=min(a.batch,a.ex2_step-(nonce%a.ex2_step),2**32-nonce)
   proc.stdin.write(f'{prefix.hex()} {nonce} {count}\n');proc.stdin.flush()
   result=None
   while True:
    line=proc.stdout.readline().strip();parts=line.split()
    if not parts:raise RuntimeError('engine stopped')
    if parts[0]=='ERROR':raise RuntimeError(line)
    if parts[0]=='HIT':
     score=int(parts[1]);n=int(parts[2]);d=bytes.fromhex(parts[3])
     if h2(prefix+struct.pack('<I',n))!=d or lz(d)!=score:raise RuntimeError('HIT audit mismatch')
     print('HIT LZ',score,'job',jid,'ex2',ex2.hex(),'nonce',f'{n:08x}','hash',d[::-1].hex(),flush=True)
    if parts[0]=='BATCH':result=parts;break
   count=int(result[1]);score=int(result[2]);n=int(result[3]);d=bytes.fromhex(result[4])
   if h2(prefix+struct.pack('<I',n))!=d or lz(d)!=score:raise RuntimeError('BATCH audit mismatch')
   total+=count
   if score>best:
    best=score;print('NEW_BEST LZ',best,'job',jid,'ex2',ex2.hex(),'nonce',f'{n:08x}','hash',d[::-1].hex(),flush=True)
   nonce+=count
   if nonce>=2**32 or nonce%a.ex2_step==0:
    nonce=0;ex2_count=(ex2_count+1)%(1<<(8*exsize))
   now=time.monotonic()
   if now-last>=a.status_seconds:
    print('STATUS seconds',round(now-started,1),'hashes',total,'avg_Hps',round(total/(now-started)),'best_LZ',best,'ex2',ex2.hex(),'job',jid,'gate90_pass',result[5],flush=True)
    last=now
 except KeyboardInterrupt:print('STOPPED_BY_USER',flush=True)
 finally:
  stop.set();sock.close()
  try:proc.stdin.write('QUIT\n');proc.stdin.flush();proc.wait(timeout=2)
  except Exception:proc.kill()
if __name__=='__main__':main()
