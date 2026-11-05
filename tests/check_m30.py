#!/usr/bin/env python3
"""Validate the M30 CMOS binary baseline and publish measured values."""
import json, pathlib, re, sys
s=pathlib.Path(sys.argv[1]).read_text(errors="replace")
def val(k):
    m=re.search(rf"(?im)^\s*{k}\s*=\s*([-+\d.eE]+)",s)
    if not m: sys.exit(f"FAIL missing {k}")
    return float(m.group(1))
fall=val("binary_fall_delay"); rise=val("binary_rise_delay")
high=val("binary_high"); low=val("binary_low")
power=-3.3*val("binary_avg_current")
if not (0<fall<10e-9 and 0<rise<10e-9 and high>3 and low<0.3 and 0<=power<0.02):
    sys.exit(f"FAIL CMOS baseline: fall={fall}, rise={rise}, high={high}, low={low}, power={power}")
r={"baseline":"binary CMOS inverter LEVEL=1","binary_fall_delay_ns":fall*1e9,"binary_rise_delay_ns":rise*1e9,"binary_average_power_mW":power*1e3,"binary_high_V":high,"binary_low_V":low,"load_fF":20,"supply_V":3.3,"limitations":"not comparable to complete 4-level logic; not SHA-256d speed"}
pathlib.Path("spice/m30_binary_metrics.json").write_text(json.dumps(r,indent=2)+"\n")
print(json.dumps(r,indent=2))
print("PASS: M30 binary CMOS reference characterized")
