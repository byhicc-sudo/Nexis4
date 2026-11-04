#!/usr/bin/env python3
"""Check nominal M28 MOS-resistor threshold sensor levels."""
import pathlib, re, sys
s=pathlib.Path(sys.argv[1]).read_text(errors="replace")
expected=((0,0,0),(1,0,0),(1,1,0),(1,1,1))
for level, exp in enumerate(expected):
    got=[]
    for t in range(1,4):
        key=f"l{level}t{t}"
        m=re.search(rf"(?im)^\s*{key}\s*=\s*([-+\d.eE]+)",s)
        if not m: sys.exit(f"FAIL: missing measurement {key}")
        v=float(m.group(1))
        if not -0.1<=v<=3.4: sys.exit(f"FAIL: {key}={v}")
        got.append(int(v<1.65))
    print(f"input level {level}: measured MOS decisions {tuple(got)} expected {exp}")
    if tuple(got)!=exp: sys.exit(f"FAIL: wrong MOS threshold sensing at level {level}")
print("PASS: nominal M28 MOS-resistor sensing 4/4")
print("LIMIT: LEVEL=1 idealized device models, uncharacterized delay/power/process/noise")
