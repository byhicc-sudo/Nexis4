#!/usr/bin/env python3
"""M37: nominal threshold sensor + CMOS inverter validation."""
import json,pathlib,re,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
folder=root/"results/m37"
folder.mkdir(parents=True,exist_ok=True)
log=folder/"m37.log"
with log.open("w") as fh:
    p=subprocess.run(["ngspice","-b",str(root/"spice/m37_mos_sensors.cir")],cwd=root,stdout=fh,stderr=subprocess.STDOUT)
if p.returncode:sys.exit(f"FAIL ngspice exit={p.returncode}; see {log}")
s=log.read_text(errors="replace")
expected=[(0,0,0),(1,0,0),(1,1,0),(1,1,1)]
records=[]
for i,truth in enumerate(expected):
    vals=[]
    for j in (1,2,3):
        m=re.search(rf"(?im)^\s*t{j}{i}\s*=\s*([-+\d.eE]+)",s)
        if not m:sys.exit(f"FAIL missing t{j}{i}; see {log}")
        vals.append(float(m.group(1)))
    if any(0.4<=v<=2.9 for v in vals):
        sys.exit(f"FAIL ambiguous CMOS logic voltage at level {i}: {vals}")
    actual=tuple(int(v>1.65) for v in vals)
    ok=actual==truth
    print(f"M37 input={i} ({i*1.1:.1f}V) sensed={actual} expected={truth} raw={[round(v,5) for v in vals]} {'PASS' if ok else 'FAIL'}")
    records.append({"input_V":i*1.1,"outputs_V":vals,"decisions":actual,"expected":truth,"passed":ok})
(folder/"metrics.json").write_text(json.dumps({"test":"M37 transistor threshold sensors with CMOS output inverters","transistors":9,"limitations":["artificial threshold models","no one-hot decoder","no transient timing","no PDK"],"results":records},indent=2)+"\n")
if not all(r["passed"] for r in records):sys.exit("FAIL M37")
print("PASS M37 nominal sensing 4/4")
