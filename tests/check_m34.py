#!/usr/bin/env python3
"""M34: load-sweep of M33 MOS transmission-gate output stage.
Ideal decoder and voltage references remain ideal; no PDK or H/s claim.
"""
import json, pathlib, re, subprocess, sys
root=pathlib.Path(__file__).resolve().parents[1]
source=(root/"spice/m33_regenerator.cir").read_text()
results=root/"results"/"m34"
results.mkdir(parents=True,exist_ok=True)
records=[]
for load in (20,100,500):
    deck, count=re.subn(r"(?im)^CLOAD\s+out\s+0\s+20f\s*$",f"CLOAD out 0 {load}f",source)
    if count != 1:
        sys.exit("FAIL: CLOAD not found in M33 source")
    path=results/f"load_{load}f.cir"
    log=results/f"load_{load}f.log"
    path.write_text(deck)
    with log.open("w") as fh:
        proc=subprocess.run(["ngspice","-b",str(path)],stdout=fh,stderr=subprocess.STDOUT)
    if proc.returncode:
        sys.exit(f"FAIL: ngspice load {load}f exit={proc.returncode}; see {log}")
    output=log.read_text(errors="replace")
    voltages=[]
    for i in range(4):
        m=re.search(rf"(?im)^\s*out{i}\s*=\s*([-+\d.eE]+)",output)
        if not m:
            sys.exit(f"FAIL: missing out{i} at load={load}f; see {log}")
        voltages.append(float(m.group(1)))
    errors=[abs(a-b) for a,b in zip(voltages,(0,1.1,2.2,3.3))]
    ok=all(e<=0.05 for e in errors)
    records.append(dict(load_fF=load,outputs_V=voltages,max_error_V=max(errors),passed=ok))
    print(f"M34 load={load} fF outputs={[round(x,6) for x in voltages]} max_error={max(errors):.6f} V {'PASS' if ok else 'FAIL'}")
report={"test":"M34 MOS output stage load sweep","ideal_parts":["one-hot input decoder","0/1.1/2.2/3.3V reference rails"],"model":"MOS LEVEL=1","tolerance_V":0.05,"results":records,"limitation":"Steady samples only; no noise margin, timing or full transistor logic claim"}
(results/"metrics.json").write_text(json.dumps(report,indent=2)+"\n")
if not all(r["passed"] for r in records):sys.exit("FAIL M34")
print("PASS M34 load sweep 3/3")
