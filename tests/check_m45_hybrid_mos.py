#!/usr/bin/env python3
"""NEXIS-4 hybrid SPICE truth-table test: MOS transmission gates + ideal selectors.
NOT an all-MOS four-level logic gate, PDK or ASIC timing characterization.
"""
import json,pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"results"/"m45_hybrid_mos";OUT.mkdir(parents=True,exist_ok=True)
MODEL="""
.model NLOG NMOS (LEVEL=1 VTO=0.55 KP=0.001 LAMBDA=0.02)
.model PLOG PMOS (LEVEL=1 VTO=-0.55 KP=0.0005 LAMBDA=0.02)
"""
# Ideal 0/3.3V selectors encode the logic truth table. Output is an actual
# CMOS transmission-gate network, each path using 2 LEVEL=1 MOSFETs.
def deck(a,b,cin,op):
    if op=="XOR": y=a^b;carry=0
    elif op=="AND": y=a&b;carry=0
    elif op=="NOT": y=a^3;carry=0
    else:
        total=a+b+cin;y=total&3;carry=total>>2
    lines=[
        "* NEXIS-4 hybrid gate: ideal input decode + MOS output selection",
        "VDD vdd 0 3.3",
        "VR1 r1 0 1.1",
        "VR2 r2 0 2.2",
        f"* inputs: a={a}, b={b}, carry_in={cin}, op={op}, expected={y}, cout={carry}",
        f"VA ain 0 {a*1.1:.8f}",
        f"VB bin 0 {b*1.1:.8f}",
        f"VC cin 0 {cin*3.3:.8f}",
    ]
    rails=["0","r1","r2","vdd"]
    for k in range(4):
        s=3.3 if k==y else 0
        c=0 if k==y else 3.3
        lines += [
            f"VS{k} s{k} 0 {s}",
            f"VC{k} c{k} 0 {c}",
            f"MN{k} out s{k} {rails[k]} 0 NLOG W=10u L=1u",
            f"MP{k} out c{k} {rails[k]} vdd PLOG W=20u L=1u",
        ]
    lines += [
        f"VCO cout 0 {carry*3.3:.8f}",
        "RLEAK out 0 1G",
        "CLOAD out 0 20f",
        MODEL,
        ".control",
        "set noaskquit",
        "op",
        "print v(out) v(cout)",
        "quit",
        ".endc",
        ".end",
    ]
    return "\n".join(lines)+"\n",y,carry
pattern=re.compile(r"v\((out|cout)\)\s*=\s*([-+\d.eE]+)",re.I)
cases=[]
for op in ("XOR","AND","NOT","ADD"):
    for a in range(4):
        for b in range(4):
            for cin in ((0,1) if op=="ADD" else (0,)):
                cases.append((op,a,b,cin))
failures=[];results=[]
for idx,(op,a,b,cin) in enumerate(cases):
    circuit,expected,carry=deck(a,b,cin,op)
    path=OUT/f"case_{idx:03d}.cir";path.write_text(circuit)
    try:
        proc=subprocess.run(["ngspice","-b",str(path)],cwd=ROOT,capture_output=True,text=True,timeout=15)
    except (OSError,subprocess.TimeoutExpired) as e:
        failures.append({"case":idx,"error":str(e)});continue
    output=proc.stdout+"\n"+proc.stderr
    found={k.lower():float(v) for k,v in pattern.findall(output)}
    got=found.get("out")
    gotcarry=found.get("cout")
    passed=proc.returncode==0 and got is not None and abs(got-expected*1.1)<0.15 and gotcarry is not None and abs(gotcarry-carry*3.3)<0.15
    item={"op":op,"a":a,"b":b,"cin":cin,"expected_v":expected*1.1,"measured_v":got,"expected_carry_v":carry*3.3,"measured_carry_v":gotcarry,"pass":passed}
    results.append(item)
    if not passed:failures.append({"case":idx,**item,"ngspice_tail":output[-500:]})
report={"model":"hybrid ideal selectors + MOS transmission gates, not physical MOS arithmetic","count":len(cases),"passed":sum(x["pass"] for x in results),"failed":failures,"cases":results,
"remaining":["Transistor-only 4-level input decoding and XOR/AND/ADD logic","MOS-based carry generation","Noise margins, PVT, transition overlap","Measured power, delay, physical area and H/s"]}
(OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
print(f"M45 hybrid SPICE: {report['passed']}/{len(cases)} PASS")
for e in failures[:5]:print("FAIL",e)
print("LIMITATION: ideal truth-table selection; MOSFETs implement output switching only.")
sys.exit(bool(failures))
