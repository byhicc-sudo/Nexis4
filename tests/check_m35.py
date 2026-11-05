#!/usr/bin/env python3
"""M35 output transition characterization; ideal decoder/reference rails remain."""
import json
import pathlib
import re
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[1]
source = (root / "spice/m33_regenerator.cir").read_text()
folder = root / "results/m35"
folder.mkdir(parents=True, exist_ok=True)
records = []
# Input changes at 5.01, 15.01, 25.01 ns.
edges = [(5.01, 1.1), (15.01, 2.2), (25.01, 3.3)]
for load in (20, 100, 500):
    deck, count = re.subn(r"(?im)^CLOAD\s+out\s+0\s+20f\s*$", f"CLOAD out 0 {load}f", source)
    if count != 1:
        sys.exit("FAIL: expected exactly one CLOAD in M33")
    # Export ngspice transient waveform, preserving the M33 measurements.
    deck = deck.replace("set noaskquit", "set noaskquit\nset wr_singlescale\nset wr_vecnames")
    deck = deck.replace("\nquit\n.endc", f"\nwrdata results/m35/load_{load}f_wave.txt v(out)\nquit\n.endc")
    path = folder / f"load_{load}f.cir"
    log = folder / f"load_{load}f.log"
    path.write_text(deck)
    with log.open("w") as fh:
        proc = subprocess.run(["ngspice", "-b", str(path)], cwd=root, stdout=fh, stderr=subprocess.STDOUT)
    if proc.returncode:
        sys.exit(f"FAIL: ngspice at {load} fF; see {log}")
    wave = folder / f"load_{load}f_wave.txt"
    if not wave.exists():
        sys.exit(f"FAIL: waveform not exported for {load} fF; see {log}")
    samples = []
    for line in wave.read_text().splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            samples.append((float(parts[0]) * 1e9, float(parts[-1])))
        except ValueError:
            continue
    if len(samples) < 100:
        sys.exit(f"FAIL: insufficient waveform samples at {load} fF")
    transitions = []
    for edge, target in edges:
        # Settling: earliest point inside +/-50 mV for the rest of this level's
        # observation window. The last edge is observed until 35 ns.
        stop = min(edge + 8.0, 35.0)
        segment = [(t, v) for t, v in samples if edge <= t <= stop]
        if not segment:
            sys.exit(f"FAIL: no samples for transition at {edge} ns")
        last_bad = -1
        for i, (_, v) in enumerate(segment):
            if abs(v - target) > 0.05:
                last_bad = i
        if last_bad >= len(segment) - 1:
            settle = None
        else:
            settle = max(0.0, segment[last_bad + 1][0] - edge)
        transitions.append({"edge_ns": edge, "target_V": target, "settling_ns": settle})
    records.append({"load_fF": load, "transitions": transitions})
    print(f"M35 {load} fF: " + ", ".join(
        f"{t['target_V']:.1f}V settle={t['settling_ns']:.4f}ns" if t["settling_ns"] is not None else f"{t['target_V']:.1f}V NOT_SETTLED"
        for t in transitions))
report = {
    "test": "M35 nominal output settling under capacitive load",
    "criterion": "within +/-50 mV and stays there for remaining observation window",
    "input_edge_ns": [e for e, _ in edges],
    "ideal_components": ["decoder", "voltage references"],
    "not_measured": ["energy per transition", "realistic input-decoder delay", "SHA256d H/s"],
    "results": records,
}
(folder / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
if any(t["settling_ns"] is None for r in records for t in r["transitions"]):
    sys.exit("FAIL M35: at least one transition did not settle")
print("PASS M35: all 9 nominal settling observations")
