#!/usr/bin/env python3
"""M32 DC nominal level detection, with measured analog outputs."""
import json,pathlib,re,sys
s=pathlib.Path(sys.argv[1]).read_text(errors="replace")
def m(key):
    x=re.search(rf"(?im)^\s*{key}\s*=\s*([-+\d.eE]+)",s)
    if not x:sys.exit("FAIL: missing DC measurement "+key)
    return float(x.group(1))
v=[[m(f"{k}{i}") for k in "abc"] for i in range(4)]
expected=((0,0,0),(1,0,0),(1,1,0),(1,1,1))
for i,row in enumerate(v):
    decoded=tuple(int(x<1.65) for x in row)
    print(f"input {i} ({i*1.1:.1f} V) output {row} detected {decoded}")
    if decoded!=expected[i]:sys.exit(f"FAIL: DC decoding {i}")
report={"model":"NMOS LEVEL=1 3-threshold sensor","nominal_inputs_V":[0,1.1,2.2,3.3],"sensor_outputs_V":v,"logic_decisions":expected,"note":"DC only; no process corners, transistor-level output regeneration, or CPU speed"}
pathlib.Path("spice/m32_dc_metrics.json").write_text(json.dumps(report,indent=2)+"\n")
print("PASS: M32 nominal DC four-level sensing")
