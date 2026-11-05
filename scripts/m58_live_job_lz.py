#!/usr/bin/env python3
"""M58 read-only live Stratum V1 SHA256d LZ monitor. No share submissions."""
import argparse, hashlib, json, socket, time, threading, queue, struct, sys
def h2(b): return hashlib.sha256(hashlib.sha256(b).digest()).digest()
def swap_words(h): return b''.join(bytes.fromhex(h)[i:i+4][::-1] for i in range(0,len(h)//2,4))
def lz(d):
    return sum(8 if x==0 else 8-x.bit_length() for x in d[::-1][:0]) if False else (256-int.from_bytes(d,'little').bit_length())
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--host',default='solo.ckpool.org');p.add_argument('--port',type=int,default=3333)
    p.add_argument('--user',required=True,help='Your authorized BTC address.worker')
    p.add_argument('--password',default='x');p.add_argument('--threshold',type=int,default=45)
    p.add_argument('--status-seconds',type=float,default=10)
    a=p.parse_args()
    if not 0<=a.threshold<=255:p.error('threshold 0..255')
    s=socket.create_connection((a.host,a.port),timeout=15);s.settimeout(None)
    stream=s.makefile('rb');messages=queue.Queue();stop=threading.Event()
    def reader():
        try:
            for line in stream:
                try: messages.put(json.loads(line))
                except json.JSONDecodeError: print('INVALID_JSON',flush=True)
        except Exception as e:messages.put({'_error':str(e)})
        finally:stop.set()
    threading.Thread(target=reader,daemon=True).start()
    def send(obj):s.sendall((json.dumps(obj,separators=(',',':'))+'\n').encode())
    send({'id':1,'method':'mining.subscribe','params':['NEXIS4-M58/1.0']})
    send({'id':2,'method':'mining.authorize','params':[a.user,a.password]})
    ex1=None;exsize=None;authorized=False;job=None;nonce=0;ex2_counter=0
    total=0;best=-1;start=time.monotonic();last=start;generation=0
    print('READ_ONLY NO_SUBMIT; full hashlib SHA256d; threshold LZ >',a.threshold,flush=True)
    try:
        while not stop.is_set():
            try:
                while True:
                    msg=messages.get_nowait()
                    if '_error' in msg:raise RuntimeError(msg['_error'])
                    if msg.get('id')==1:
                        if msg.get('error'):raise RuntimeError('subscribe: '+str(msg['error']))
                        ex1=bytes.fromhex(msg['result'][1]);exsize=int(msg['result'][2])
                        if not 1<=exsize<=16:raise RuntimeError('invalid extranonce2 size')
                        print('SUBSCRIBED ex2_size=',exsize,flush=True)
                    elif msg.get('id')==2:
                        authorized=msg.get('result') is True
                        print('AUTHORIZED',authorized,'error',msg.get('error'),flush=True)
                        if not authorized:raise RuntimeError('authorization failed')
                    elif msg.get('method')=='mining.notify':
                        params=msg['params']
                        if len(params)<9:raise RuntimeError('invalid mining.notify')
                        job=params;generation+=1;nonce=0;ex2_counter=0
                        print('NEW_JOB',params[0],'generation',generation,'clean',params[8],flush=True)
                    elif msg.get('method')=='mining.set_difficulty':
                        print('POOL_DIFFICULTY',msg['params'][0],flush=True)
            except queue.Empty:pass
            if not authorized or ex1 is None or job is None:
                time.sleep(.1);continue
            jid,prev,coinb1,coinb2,branches,version,nbits,ntime,clean=job[:9]
            ex2=ex2_counter.to_bytes(exsize,'big')
            coinbase=bytes.fromhex(coinb1)+ex1+ex2+bytes.fromhex(coinb2)
            merkle=h2(coinbase)
            for branch in branches:merkle=h2(merkle+bytes.fromhex(branch))
            # Stratum V1 fields are wire/display hex with word reversal for header serialization.
            prefix=swap_words(version)+swap_words(prev)+merkle+swap_words(ntime)+swap_words(nbits)
            if len(prefix)!=76:raise RuntimeError('invalid 76-byte header prefix')
            for _ in range(8192):
                if stop.is_set() or not messages.empty():break
                header=prefix+struct.pack('<I',nonce)
                digest=h2(header)
                score=lz(digest)
                total+=1
                if score>best:
                    best=score
                    print('NEW_BEST LZ',score,'job',jid,'ex2',ex2.hex(),'nonce',f'{nonce:08x}','hash',digest[::-1].hex(),flush=True)
                if score>a.threshold:
                    print('HIT LZ',score,'job',jid,'ex2',ex2.hex(),'nonce',f'{nonce:08x}','hash',digest[::-1].hex(),flush=True)
                nonce+=1
                if nonce==2**32:
                    nonce=0;ex2_counter=(ex2_counter+1)%(1<<(8*exsize));break
            now=time.monotonic()
            if now-last>=a.status_seconds:
                print('STATUS seconds',round(now-start,1),'hashes',total,'avg_Hps',round(total/(now-start)),'best_LZ',best,'job',jid,flush=True)
                last=now
    except KeyboardInterrupt:print('STOPPED_BY_USER',flush=True)
    finally:
        stop.set();s.close()
if __name__=='__main__':main()
