#!/usr/bin/env python3
"""M54 experimental transient on the same M53 16-stage MOS netlist.
No success assumed: convergence, settling and timeouts are reported explicitly.
"""
import json,pathlib,re,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"results/m54_transient";OUT.mkdir(parents=True,exist_ok=True)
BASE=ROOT/"results/m53_add32/vector_00.cir"
if not BASE.exists():
 print("BLOCKED: run scripts/TEST_M53_ADD32.sh first to generate M53 netlists")
 sys.exit(2)
base=BASE.read_text()
if "XADD15 " not in base or ".global vdd ref1 ref2" not in base:
 print("BLOCKED: M53 baseline is not the validated global-rail 16-stage circuit")
 sys.exit(2)
cases=[("zero_to_full_carry",0xffffffff,1),("zero_to_alternating",0x55555555,0xaaaaaaaa)]
results=[]
for label,a,b in cases:
 deck=base
 for i in range(16):
  for prefix,word in (("VA",a),("VB",b)):
   pattern=rf"(?m)^{prefix}{i} [ab]{i} 0 [-+\d.eE]+$"
   new=f"{prefix}{i} {'a' if prefix=='VA' else 'b'}{i} 0 PWL(0n 0 40n 0 40.1n {((word>>(2*i))&3)*1.1:.9g} 300n {((word>>(2*i))&3)*1.1:.9g})"
   deck,n=re.subn(pattern,lambda m:new,deck)
   if n!=1:raise RuntimeError(f"source not found {prefix}{i}")
 deck=deck[:deck.index(".control")]
 deck+="\n.control\nset noaskquit\ntran 0.2n 300n\n"
 for i in range(16):
  deck+=f"meas tran s{i}_pre FIND v(s{i}) AT=30n\n"
  deck+=f"meas tran s{i}_post FIND v(s{i}) AT=290n\n"
 deck+="meas tran carry_pre FIND v(c16) AT=30n\nmeas tran carry_post FIND v(c16) AT=290n\nquit\n.endc\n.end\n"
 path=OUT/(label+".cir");path.write_text(deck)
 start=time.monotonic()
 try:
  p=subprocess.run(["ngspice","-b",str(path)],capture_output=True,text=True,timeout=240,cwd=ROOT)
  output=p.stdout+"\n"+p.stderr
  values={k.lower():float(v) for k,v in re.findall(r"(?m)^\s*(s\d+_(?:pre|post)|carry_(?:pre|post))\s*=\s*([-+\d.eE]+)",output,re.I)}
  expected=(a+b)&0xffffffff
  bad=[{"stage":i,"pre":values.get(f"s{i}_pre"),"post":values.get(f"s{i}_post"),"expected_post":((expected>>(2*i))&3)*1.1}
   for i in range(16) if f"s{i}_pre" not in values or f"s{i}_post" not in values or abs(values[f"s{i}_pre"])>0.18 or abs(values[f"s{i}_post"]-((expected>>(2*i))&3)*1.1)>0.18]
  carry=values.get("carry_post")
  ok=p.returncode==0 and not bad and carry is not None and abs(carry-((a+b)>>32)*3.3)<0.3 and abs(values.get("carry_pre",999))<0.3
  result={"name":label,"pass":ok,"elapsed_seconds":round(time.monotonic()-start,2),"bad_stages":bad,"carry_post_v":carry,"carry_expected_v":((a+b)>>32)*3.3,"returncode":p.returncode,"measurements":values,"log_tail":output[-1200:] if not ok else ""}
 except subprocess.TimeoutExpired as e:
  result={"name":label,"pass":False,"status":"TIMEOUT","elapsed_seconds":round(time.monotonic()-start,2),"error":str(e)}
 results.append(result)
 print(f"M54 {label}: {'PASS' if result['pass'] else 'FAIL'} ({result['elapsed_seconds']}s)",flush=True)
(OUT/"report.json").write_text(json.dumps({"cases":results,"passed":sum(r["pass"] for r in results),"total":len(results),"limitations":["Only 2 transitions; no settling-time bound, glitches, PVT, power, or silicon speed qualification","LEVEL=1 MOS, ideal rails","No full SHA256d physical core"]},indent=2)+"\n")
sys.exit(0 if all(r["pass"] for r in results) else 1)
