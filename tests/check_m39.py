#!/usr/bin/env python3
"""M39: dynamic characterization of the integrated M38 circuit.
Reports overlap, rail currents and settling; never silently passes an unsafe transient.
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "m39"
OUT.mkdir(parents=True, exist_ok=True)
source = (ROOT / "spice" / "m38_integrated.cir").read_text()
source, n1 = re.subn(r"(?m)^VIN in 0 0$", "VIN in 0 PWL(0n 0 5n 0 5.01n 1.1 15n 1.1 15.01n 2.2 25n 2.2 25.01n 3.3 40n 3.3)", source)
source, n2 = re.subn(r"(?m)^\.dc VIN 0 3\.31 0\.01$", ".tran 0.002n 40n", source)
if (n1, n2) != (1, 1):
    sys.exit("FAIL: M38 source structure changed")
start = source.index(".control\n")
source = source[:start] + """.control
set noaskquit
set wr_singlescale
set wr_vecnames
run
wrdata results/m39/wave.txt v(in) v(out) v(s0) v(s1) v(s2) v(t3) i(VDD) i(VREF1) i(VREF2)
quit
.endc
.end
"""
deck = OUT / "m39_transient.cir"
log = OUT / "ngspice.log"
deck.write_text(source)
with log.open("w") as f:
    proc = subprocess.run(["ngspice", "-b", str(deck)], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
if proc.returncode:
    sys.exit(f"FAIL: ngspice exit {proc.returncode}; inspect {log}")
wave = OUT / "wave.txt"
if not wave.exists():
    sys.exit(f"FAIL: missing waveform; inspect {log}")
samples = []
for line in wave.read_text().splitlines():
    try:
        nums = [float(x) for x in line.split()]
    except ValueError:
        continue
    if len(nums) != 10:
        continue
    samples.append(nums)
if len(samples) < 1000:
    sys.exit(f"FAIL: insufficient waveform samples ({len(samples)}); inspect {wave}")
# wrdata: time, in, out, s0, s1, s2, t3, I(VDD), I(VREF1), I(VREF2)
overlap = 0
max_selected = 0
peak_currents = [0.0, 0.0, 0.0]
for row in samples:
    selects = row[3:7]
    selected = sum(v > 1.65 for v in selects)
    max_selected = max(max_selected, selected)
    if selected > 1:
        overlap += 1
    for i, amp in enumerate(row[7:10]):
        peak_currents[i] = max(peak_currents[i], abs(amp))
edges = [(5.01, 1.1), (15.01, 2.2), (25.01, 3.3)]
settling = []
for edge, target in edges:
    window = [(row[0] * 1e9, row[2]) for row in samples if edge <= row[0] * 1e9 <= edge + 8.0]
    if not window:
        sys.exit(f"FAIL: no samples after {edge} ns")
    last_bad = -1
    for i, (_, voltage) in enumerate(window):
        if abs(voltage - target) > 0.05:
            last_bad = i
    settle_ns = None if last_bad == len(window)-1 else max(0.0, window[last_bad+1][0]-edge)
    settling.append({"transition_at_ns": edge, "target_V": target, "settling_ns": settle_ns})
metrics = {
    "test": "M39 integrated dynamic transitions",
    "samples": len(samples),
    "overlap_samples_above_1_65V": overlap,
    "max_simultaneously_selected": max_selected,
    "peak_absolute_source_current_mA": {
        "VDD": peak_currents[0]*1000,
        "VREF1": peak_currents[1]*1000,
        "VREF2": peak_currents[2]*1000
    },
    "settling": settling,
    "notes": [
        "Nominal LEVEL=1 models and ideal voltage references",
        "Overlap detection is sample-based, not a proof of absence between samples",
        "Source currents include supply and reference loads; no processor power or H/s claim"
    ]
}
(OUT / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))
if any(x["settling_ns"] is None for x in settling):
    sys.exit("FAIL M39: output did not settle within observation window")
if overlap:
    sys.exit(f"FAIL M39: {overlap} sampled periods have multiple active selects")
print("PASS M39: no sampled selection overlap and all transitions settled")
