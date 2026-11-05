#!/usr/bin/env python3
"""M31 functional quaternary inversion validation; no PPA advantage claims."""
import json, pathlib, re, sys
s=pathlib.Path(sys.argv[1]).read_text(errors="replace")
def measure(key):
    m=re.search(rf"(?im)^\s*{key}\s*=\s*([-+\d.eE]+)",s)
    if not m: sys.exit(f"FAIL: missing {key}")
    return float(m.group(1))
expected=[3.3,2.2,1.1,0.0]
measured=[measure(f"q{i}") for i in range(4)]
for i,(got,want) in enumerate(zip(measured,expected)):
    print(f"symbol {i}: measured {got:.6f} V; expected {want:.6f} V")
    if abs(got-want)>0.05: sys.exit(f"FAIL: symbol {i}")
fall=measure("qfall_delay")
rise=measure("qrise_delay")
if not (0<fall<10e-9 and 0<rise<10e-9): sys.exit(f"FAIL: delay fall={fall}, rise={rise}")
report={"model":"behavioral 4-level inversion + 2k resistor + 20fF load","outputs_V":measured,"fall_delay_ns":fall*1e9,"rise_delay_ns":rise*1e9,"limitations":"behavioral voltage source; no transistor-level power or fair binary comparison"}
pathlib.Path("spice/m31_metrics.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
print("PASS: M31 quaternary inversion 4/4")
