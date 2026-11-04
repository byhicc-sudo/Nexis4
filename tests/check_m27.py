#!/usr/bin/env python3
"""Fail the workflow if ngspice M27 measurements do not decode all four levels."""
import pathlib
import re
import sys

log = pathlib.Path(sys.argv[1]).read_text(errors="replace")
expected = ((0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 1, 1))
observed = []
for level in range(4):
    bits = []
    for threshold in range(1, 4):
        key = f"l{level}t{threshold}"
        match = re.search(rf"(?im)^\s*{key}\s*=\s*([-+\d.eE]+)", log)
        if not match:
            raise SystemExit(f"FAIL: missing measurement {key}; inspect SPICE log")
        voltage = float(match.group(1))
        if not (-0.1 <= voltage <= 3.4):
            raise SystemExit(f"FAIL: {key} voltage out of bounds: {voltage}")
        bits.append(int(voltage > 1.65))
    observed.append(tuple(bits))
    print(f"level {level}: thresholds {tuple(bits)} expected {expected[level]}")
if tuple(observed) != expected:
    raise SystemExit(f"FAIL: decoded {observed}, expected {expected}")
print("PASS: 4/4 nominal levels decoded with ideal behavioral comparators")
print("NOTE: no transistor, delay, energy, or noise validation is claimed")
