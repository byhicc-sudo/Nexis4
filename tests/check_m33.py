#!/usr/bin/env python3
"""Validate nominal M33 regenerated voltages; not a fully physical decoder."""
import json,pathlib,re,sys
s=pathlib.Path(sys.argv[1]).read_text(errors="replace")
v=[]
for i in range(4):
    m=re.search(rf"(?im)^\s*out{i}\s*=\s*([-+\d.eE]+)",s)
    if not m: sys.exit(f"FAIL missing out{i} measurement")
    v.append(float(m.group(1)))
for i,(measured,expected) in enumerate(zip(v,[0,1.1,2.2,3.3])):
    print(f"level {i}: output={measured:.6f} V expected={expected:.6f} V")
    if abs(measured-expected)>0.05:sys.exit(f"FAIL M33 level {i}")
report={"architecture":"ideal one-hot decoder + 4 MOS CMOS transmission gates","outputs_V":v,"nominal_tolerance_V":0.05,"load_fF":20,"scope":"functional output regeneration only; no power or speed advantage measured"}
pathlib.Path("spice/m33_metrics.json").write_text(json.dumps(report,indent=2)+"\n")
print("PASS: M33 regenerated 4 nominal voltages")
