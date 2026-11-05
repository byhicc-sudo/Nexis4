#!/usr/bin/env python3
"""M47 transient characterization of the *unchanged* M46 MOS topology.
No behavioral arithmetic in the SPICE deck. ngspice LEVEL=1; ideal rails.
"""
import ast,json,pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"results"/"m47_transient";OUT.mkdir(parents=True,exist_ok=True)
src=ast.parse((ROOT/"tests"/"check_m46_transistor_logic.py").read_text())
# Load only reusable definitions; importing the M46 module would run 80 DC tests.
defs=[n for n in src.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ("Net","logic","circuit")]
ns={"__name__":"m47"}
exec(compile(ast.Module(body=defs,type_ignores=[]),"<m46-reusable>","exec"),ns)
circuit=ns["circuit"];logic=ns["logic"]
# Input changes at 10ns; verify pre-transition 8ns and post-transition 19ns.
# Deliberately include maximal swings, intermediate levels and carry changes.
transitions=[
 ((0,0,0),(3,3,1)),
 ((3,3,1),(0,0,0)),
 ((1,2,0),(2,1,1)),
 ((2,1,1),(1,2,0)),
 ((0,3,0),(3,0,1)),
 ((3,0,1),(0,3,0)),
]
patt=re.compile(r"(?m)^\s*(pre_out|post_out|pre_carry|post_carry|peak_supply|low_supply)\s*=\s*([-+\d.eE]+)",re.I)
results=[]
for op in ("XOR","AND","NOT","ADD"):
 template,cout=circuit(op)
 # Replace M46 DC control block with transient measurements.
 control=template.index(".control\n")
 template=template[:control]
 # The probe is already part of M46, and the topology stays identical.
 for index,(before,after) in enumerate(transitions):
  def pwl(x,y,unit):
   return f"PWL(0n {x*unit:.8f} 9.9n {x*unit:.8f} 10n {y*unit:.8f} 20n {y*unit:.8f})"
  deck=template.replace("VA ain 0 {VA}","VA ain 0 "+pwl(before[0],after[0],1.1)).replace("VB bin 0 {VB}","VB bin 0 "+pwl(before[1],after[1],1.1)).replace("VC ci 0 {VC}","VC ci 0 "+pwl(before[2],after[2],3.3))
  deck+="""\n.control
set noaskquit
tran 0.02n 20n
meas tran pre_out FIND v(out) AT=8n
meas tran post_out FIND v(out) AT=19n
meas tran pre_carry FIND v(cout_probe) AT=8n
meas tran post_carry FIND v(cout_probe) AT=19n
meas tran peak_supply MAX i(VDD) FROM=9.8n TO=19.9n
meas tran low_supply MIN i(VDD) FROM=9.8n TO=19.9n
quit
.endc
.end
"""
  path=OUT/f"{op.lower()}_{index:02d}.cir";path.write_text(deck)
  try:
   p=subprocess.run(["ngspice","-b",str(path)],capture_output=True,text=True,timeout=35,cwd=ROOT)
   data={k.lower():float(v) for k,v in patt.findall(p.stdout+"\n"+p.stderr)}
   eb,cb=logic(*before,op);ea,ca=logic(*after,op)
   # ngspice return code and actual measurements are both required.
   ok=(p.returncode==0 and all(k in data for k in ("pre_out","post_out","pre_carry","post_carry","peak_supply","low_supply"))
    and abs(data["pre_out"]-eb*1.1)<0.18 and abs(data["post_out"]-ea*1.1)<0.18
    and abs(data["pre_carry"]-cb*3.3)<0.3 and abs(data["post_carry"]-ca*3.3)<0.3)
   result={"op":op,"before":before,"after":after,"pass":ok,"measurements":data,
    "expected_before_v":eb*1.1,"expected_after_v":ea*1.1,"expected_carry_before_v":cb*3.3,"expected_carry_after_v":ca*3.3}
   if not ok:result["ngspice_tail"]=(p.stdout+"\n"+p.stderr)[-900:]
  except (OSError,subprocess.TimeoutExpired) as exc:
   result={"op":op,"before":before,"after":after,"pass":False,"error":str(exc)}
  results.append(result)
failed=[r for r in results if not r["pass"]]
report={"test":"M47 MOS transient functional endpoint and supply current probe","count":len(results),"passed":len(results)-len(failed),"failed":failed,"cases":results,
"limitations":["20ns transient, only 6 transitions per operation; not exhaustive","no settling-time bound measured","supply current extrema are not energy/hash","ideal rails and LEVEL=1 models","no glitch/noise-margin or PVT certification","not full SHA-256d physical implementation"]}
(OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
print(f"M47 transient endpoints {report['passed']}/{report['count']} PASS")
for r in failed[:5]:print("FAIL",r)
print("LIMIT: endpoints and supply current extrema only; NOT energy/hash, PVT, or glitch-free proof.")
sys.exit(bool(failed))
