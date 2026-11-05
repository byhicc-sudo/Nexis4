#!/usr/bin/env python3
"""Parse and sanity-check ngspice M29 delay and power measurements."""
import json
import pathlib
import re
import sys

log = pathlib.Path(sys.argv[1]).read_text(errors="replace")
def measure(name):
    m = re.search(rf"(?im)^\s*{re.escape(name)}\s*=\s*([-+\d.eE]+)", log)
    if not m:
        raise SystemExit(f"FAIL: missing {name} measurement")
    return float(m.group(1))

fall = measure("fall_delay")
rise = measure("rise_delay")
current = measure("avg_supply_current")
high = measure("output_high")
low = measure("output_low")
power = -3.3 * current
if not (0 < fall < 20e-9 and 0 < rise < 20e-9):
    raise SystemExit(f"FAIL: invalid delays fall={fall}, rise={rise}")
if not (high > 3.0 and low < 0.5):
    raise SystemExit(f"FAIL: output did not switch: high={high}, low={low}")
if not (0 < power < 0.01):
    raise SystemExit(f"FAIL: implausible supply power {power}")
report = {
    "model": "LEVEL=1 NMOS resistor-load inverter",
    "fall_delay_ns": round(fall*1e9, 6),
    "rise_delay_ns": round(rise*1e9, 6),
    "mean_supply_power_mW": round(power*1e3, 6),
    "output_high_V": round(high, 6),
    "output_low_V": round(low, 6),
    "load_fF": 20,
    "supply_V": 3.3,
    "scope": "one illustrative switching cell; not SHA-256d H/s",
}
print(json.dumps(report, indent=2))
pathlib.Path("spice/m29_metrics.json").write_text(json.dumps(report, indent=2)+"\n")
print("PASS: M29 delay and power sanity checks")
