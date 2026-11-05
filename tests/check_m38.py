#!/usr/bin/env python3
"""M38 nominal DC end-to-end MOS-level four-state buffer verification."""
import json,pathlib,re,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
folder=root/"results/m38"
folder.mkdir(parents=True,exist_ok=True)
deck=(root/"spice/m38_integrated.cir").read_text()
transistors=len(re.findall(r"(?m)^M[A-Za-z0-9]+\s",deck))
log=folder/"m38.log"
with log.open("w") as f:
    p=subprocess.run(["ngspice","-b",str(root/"spice/m38_integrated.cir")],cwd=root,stdout=f,stderr=subprocess.STDOUT)
if p.returncode:sys.exit(f"FAIL ngspice exit={p.returncode}; inspect {log}")
data=log.read_text(errors="replace")
def measure(name):
    m=re.search(rf"(?im)^\s*{re.escape(name)}\s*=\s*([-+\d.eE]+)",data)
    if not m:sys.exit(f"FAIL missing {name}; inspect {log}")
    return float(m.group(1))
records=[]
for i in range(4):
    output=measure(f"out{i}")
    selects=[measure(f"s{j}{i}") for j in range(4)]
    bits=[int(v>1.65) for v in selects]
    onehot=bits==[int(j==i) for j in range(4)]
    rail=all(v<=0.4 or v>=2.9 for v in selects)
    error=abs(output-i*1.1)
    ok=onehot and rail and error<=0.05
    print(f"M38 input={i*1.1:.1f}V output={output:.6f}V select={bits} error={error:.6f}V {'PASS' if ok else 'FAIL'}")
    records.append({"input_V":i*1.1,"output_V":output,"select_V":selects,"onehot":onehot,"rail":rail,"error_V":error,"passed":ok})
(folder/"metrics.json").write_text(json.dumps({"test":"M38 integrated nominal DC transistor-level signal path","mosfet_count":transistors,"ideal_remaining":["reference rails 1.1V/2.2V","simplified LEVEL=1 MOS models with tailored thresholds"],"not_tested":["transition contention","noise/process corners","power","speed"],"results":records},indent=2)+"\n")
if not all(x["passed"] for x in records):sys.exit("FAIL M38")
print(f"PASS M38 nominal integrated 4/4; MOSFET count={transistors}")
