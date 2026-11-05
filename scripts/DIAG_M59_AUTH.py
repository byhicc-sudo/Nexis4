#!/usr/bin/env python3
"""Diagnose Stratum V1 authorization on two CKPool endpoints, no mining or submit."""
import json,socket,sys,time
worker=sys.argv[1] if len(sys.argv)>1 else 'bc1quzdw7vhxegc68nd4j9vur4n3hcsjcxyrfdznhy.nexis4'
for host in ('stratum.ckpool.org','solo.ckpool.org'):
 print('CONNECT',host,3333,flush=True)
 try:
  with socket.create_connection((host,3333),timeout=10) as sock:
   sock.settimeout(12)
   for msg in ({'id':1,'method':'mining.subscribe','params':['NEXIS4-DIAG/1.0']},
               {'id':2,'method':'mining.authorize','params':[worker,'x']}):
    sock.sendall((json.dumps(msg)+'\n').encode())
   stream=sock.makefile('rb')
   deadline=time.monotonic()+12
   found=False
   while time.monotonic()<deadline:
    m=json.loads(stream.readline())
    if m.get('id')==1:
     print('SUBSCRIBE',bool(m.get('result')),'error',m.get('error'),flush=True)
    elif m.get('id')==2:
     print('AUTHORIZE result',m.get('result'),'error',m.get('error'),flush=True)
     found=True;break
    elif m.get('method')=='mining.set_difficulty':
     print('DIFFICULTY',m.get('params'),flush=True)
   if not found:print('AUTHORIZE NO_RESPONSE',flush=True)
 except Exception as e:print('CONNECT_ERROR',type(e).__name__,str(e),flush=True)
print('DIAGNOSTIC_COMPLETE; no shares submitted',flush=True)
