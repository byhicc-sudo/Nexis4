#!/usr/bin/env python3
"""M49 read-only Stratum V1 live job probe. No mining.submit code path."""
import argparse,datetime,json,pathlib,socket,ssl,sys,time
from check_m48_stratum_strict import Framer,make_job,target_from_difficulty
def main():
 p=argparse.ArgumentParser(description="Read-only Stratum V1 pool job probe")
 p.add_argument("--host",required=True);p.add_argument("--port",required=True,type=int)
 p.add_argument("--user",required=True,help="Pool worker username; not a password")
 p.add_argument("--password",default="x");p.add_argument("--tls",action="store_true")
 p.add_argument("--seconds",type=int,default=30);p.add_argument("--max-jobs",type=int,default=3)
 args=p.parse_args()
 if not 1<=args.port<=65535 or not 1<=args.seconds<=300 or not 1<=args.max_jobs<=20:
  p.error("invalid port, seconds or max-jobs")
 root=pathlib.Path(__file__).resolve().parents[1];out=root/"results"/"m49_pool"
 out.mkdir(parents=True,exist_ok=True)
 now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
 state={"start_utc":now(),"host":args.host,"port":args.port,"tls":args.tls,
  "authorized":False,"subscribed":False,"difficulty":None,"jobs":[],"events":[],"pending_jobs_received":0,
  "share_submission_enabled":False,"engine":"Python hashlib reference only; MOS/RTL not used"}
 def event(name,**kwargs):
  entry={"utc":now(),"event":name,**kwargs};state["events"].append(entry)
  print(json.dumps(entry,ensure_ascii=False),flush=True)
 def send(sock,obj):
  sock.sendall((json.dumps(obj,separators=(",",":"))+"\n").encode())
 def save():
  state["end_utc"]=now()
  (out/"report.json").write_text(json.dumps(state,indent=2,ensure_ascii=False)+"\n")
  print("REPORT results/m49_pool/report.json",flush=True)
 framer=Framer();ex1=None;ex2_size=None;pending=[];deadline=time.monotonic()+args.seconds
 def process_job(params,queued=False):
  try:
   result=make_job(params,ex1,"00"*ex2_size,ex2_size,0)
   result["difficulty"]=state["difficulty"]
   if state["difficulty"] is not None:
    target=target_from_difficulty(state["difficulty"])
    result["meets_share_target"]=int(result["digest"],16)<=target
    result["share_target_hex"]=f"{target:064x}"
   else:result["meets_share_target"]=None
   result["queued_before_ready"]=queued
   state["jobs"].append(result)
   event("job_validated",job_id=result["job_id"],digest=result["digest"],
    network_target_met=result["meets_network_target"],share_target_met=result["meets_share_target"],queued=queued)
  except (KeyError,IndexError,TypeError,ValueError) as e:event("invalid_job",error=str(e))
 def drain_pending():
  if state["subscribed"] and state["authorized"] and ex1 is not None:
   while pending and len(state["jobs"])<args.max_jobs:process_job(pending.pop(0),queued=True)

 try:
  with socket.create_connection((args.host,args.port),timeout=8) as raw:
   raw.settimeout(2)
   sock=ssl.create_default_context().wrap_socket(raw,server_hostname=args.host) if args.tls else raw
   with sock:
    event("connected")
    send(sock,{"id":1,"method":"mining.subscribe","params":["NEXIS4-M49/0.1"]})
    send(sock,{"id":2,"method":"mining.authorize","params":[args.user,args.password]})
    while time.monotonic()<deadline and len(state["jobs"])<args.max_jobs:
     try:chunk=sock.recv(65536)
     except socket.timeout:continue
     if not chunk:event("connection_closed");break
     for msg in framer.feed(chunk):
      if not isinstance(msg,dict):event("invalid_message");continue
      method=msg.get("method")
      if msg.get("id")==1:
       result=msg.get("result")
       if isinstance(result,list) and len(result)>=3 and isinstance(result[1],str) and isinstance(result[2],int) and 0<=result[2]<=32:
        ex1,ex2_size=result[1],result[2];state["subscribed"]=True
        event("subscribed",extranonce2_size=ex2_size);drain_pending()
       else:event("subscribe_error",error=msg.get("error"))
      elif msg.get("id")==2:
       state["authorized"]=msg.get("result") is True
       event("authorization_result",authorized=state["authorized"],error=msg.get("error"))
       if not state["authorized"]:raise RuntimeError("pool rejected authorization")
       drain_pending()
      elif method=="mining.set_difficulty":
       try:
        difficulty=msg["params"][0];target=target_from_difficulty(difficulty)
        state["difficulty"]=str(difficulty);event("difficulty",value=str(difficulty),target_hex=f"{target:064x}")
       except (KeyError,IndexError,TypeError,ValueError) as e:event("invalid_difficulty",error=str(e))
      elif method=="mining.set_extranonce":
       params=msg.get("params")
       if isinstance(params,list) and len(params)>=2 and isinstance(params[0],str) and isinstance(params[1],int) and 0<=params[1]<=32:
        ex1,ex2_size=params[:2];event("extranonce_changed",extranonce2_size=ex2_size)
       else:event("invalid_extranonce")
      elif method=="mining.notify":
       params=msg.get("params")
       if not isinstance(params,list):
        event("invalid_job",error="notify params must be list");continue
       if not state["subscribed"] or not state["authorized"] or ex1 is None:
        if len(pending)>=32:
         pending.pop(0);event("pending_overflow_drop_oldest")
        if len(params)==9 and params[8] is True:pending.clear()
        pending.append(params);state["pending_jobs_received"]+=1
        event("job_queued_before_ready",pending=len(pending))
       else:process_job(params)
      elif method is not None:event("other_method",method=str(method))
 except (OSError,ssl.SSLError,RuntimeError,ValueError) as e:
  event("error",detail=str(e));save();return 1
 save()
 return 0 if state["subscribed"] and state["authorized"] and state["jobs"] else 2
if __name__=="__main__":sys.exit(main())
