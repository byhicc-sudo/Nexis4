#!/usr/bin/env python3
"""M36: validate 4-level output with MOSFET complementary gate drivers."""
import pathlib,re,subprocess,sys,json
root=pathlib.Path(__file__).resolve().parents[1]
out=root/"results/m36"
out.mkdir(parents=True,exist_ok=True)
deck=(root/"spice/m36_mos_gate_drivers.cir").read_text()
if len(re.findall(r"(?m)^M\w+\s",deck))!=16:sys.exit("FAIL expected 16 MOSFETs")
records=[]
for load in (20,100,500):
    modified,count=re.subn(r"(?m)^CLOAD out 0 20f$",f"CLOAD out 0 {load}f",deck)
    if count!=1:sys.exit("FAIL CLOAD not found")
    circuit=out/f"load_{load}f.cir"
    log=out/f"load_{load}f.log"
    circuit.write_text(modified)
    with log.open("w") as fh:
        result=subprocess.run(["ngspice","-b",str(circuit)],cwd=root,stdout=fh,stderr=subprocess.STDOUT)
    if result.returncode:sys.exit(f"FAIL ngspice {load}f; inspect {log}")
    s=log.read_text(errors="replace")
    vals=[]
    for i in range(4):
        m=re.search(rf"(?im)^\s*out{i}\s*=\s*([-+\d.eE]+)",s)
        if not m:sys.exit(f"FAIL missing out{i} at {load}f; inspect {log}")
        vals.append(float(m.group(1)))
    err=max(abs(x-y) for x,y in zip(vals,(0,1.1,2.2,3.3)))
    passed=err<=0.05
    print(f"M36 load={load} fF: outputs={[round(x,6) for x in vals]} max_error={err:.6f}V {'PASS' if passed else 'FAIL'}")
    records.append({"load_fF":load,"outputs_V":vals,"max_error_V":err,"passed":passed})
(out/"metrics.json").write_text(json.dumps({"transistors":16,"ideal_remaining":["BSEL0..3 decoder","reference voltage rails"],"scope":"nominal sampled output voltages, not full transistor logic or speed","results":records},indent=2)+"\n")
if not all(r["passed"] for r in records):sys.exit("FAIL M36 voltage tolerance")
print("PASS M36: CMOS complement drivers, 3/3 loads")
