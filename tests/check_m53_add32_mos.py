#!/usr/bin/env python3
"""M53: instantiate sixteen M46 transistor ADD circuits in one ngspice netlist.
Inputs are voltages; all carries and sum symbols are transistor-generated.
This is a DC feasibility experiment, not PVT/timing/silicon qualification.
"""
import ast,json,pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"results"/"m53_add32";OUT.mkdir(parents=True,exist_ok=True)
source=(ROOT/"tests"/"check_m46_transistor_logic.py").read_text()
tree=ast.parse(source)
nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and getattr(n,"name","") in ("Net","logic","circuit")]
namespace={"VDD":3.3}
exec(compile(ast.Module(body=nodes,type_ignores=[]),"<m46-definitions>","exec"),namespace)
template,carry=namespace["circuit"]("ADD")
lines=template.splitlines()
internal=[]
for line in lines:
 if line.startswith(("VDD ","VR1 ","VR2 ","VA ","VB ","VC ","RCO ",".model ",".control","set noaskquit","op","print ","quit",".endc",".end")):continue
 if line.startswith("*"):continue
 internal.append(line)
subckt=[".subckt QADD ain bin ci out cout_probe"]+internal+[f"RCO cout_probe {carry} 1m",".ends QADD"]
models=[
".model NTH1 NMOS (LEVEL=1 VTO=0.55 KP=0.001 LAMBDA=0.02)",
".model NTH2 NMOS (LEVEL=1 VTO=1.65 KP=0.001 LAMBDA=0.02)",
".model NTH3 NMOS (LEVEL=1 VTO=2.75 KP=0.001 LAMBDA=0.02)",
".model NLOG NMOS (LEVEL=1 VTO=0.55 KP=0.001 LAMBDA=0.02)",
".model PLOG PMOS (LEVEL=1 VTO=-0.55 KP=0.0005 LAMBDA=0.02)"]
vectors=[(0,0),(0xffffffff,1),(0x55555555,0xaaaaaaaa),(0x12345678,0x87654321)]
def simulate(a,b,index):
 circuit=["* M53 16-stage transistor-coupled quaternary 32-bit adder",
 "VDD vdd 0 3.3","VR1 ref1 0 1.1","VR2 ref2 0 2.2","VC0 c0 0 0"]+models+subckt
 for i in range(16):
  circuit += [f"VA{i} a{i} 0 {((a>>(2*i))&3)*1.1:.9g}",
   f"VB{i} b{i} 0 {((b>>(2*i))&3)*1.1:.9g}",
   f"XADD{i} a{i} b{i} c{i} s{i} c{i+1} QADD"]
 circuit+=[".control","set noaskquit","op"]
 for i in range(16):circuit.append(f"print v(s{i})")
 circuit+=["print v(c16)","quit",".endc",".end"]
 path=OUT/f"vector_{index:02d}.cir";path.write_text("\n".join(circuit)+"\n")
 try:
  p=subprocess.run(["ngspice","-b",str(path)],cwd=ROOT,text=True,capture_output=True,timeout=150)
 except (OSError,subprocess.TimeoutExpired) as e:return {"a":a,"b":b,"pass":False,"error":str(e)}
 values={int(i):float(v) for i,v in re.findall(r"v\(s(\d+)\)\s*=\s*([-+\d.eE]+)",p.stdout+"\n"+p.stderr,re.I)}
 cm=re.search(r"v\(c16\)\s*=\s*([-+\d.eE]+)",p.stdout+"\n"+p.stderr,re.I)
 expected=(a+b)&0xffffffff
 bad=[{"stage":i,"measured":values.get(i),"expected":((expected>>(2*i))&3)*1.1}
  for i in range(16) if i not in values or abs(values[i]-((expected>>(2*i))&3)*1.1)>0.18]
 carry_expected=(a+b)>>32
 carry_measured=float(cm.group(1)) if cm else None
 ok=p.returncode==0 and not bad and carry_measured is not None and abs(carry_measured-carry_expected*3.3)<0.3
 return {"a":f"{a:08x}","b":f"{b:08x}","expected":f"{expected:08x}",
 "carry_expected":carry_expected,"carry_measured_v":carry_measured,"bad_stages":bad,
 "pass":ok,"ngspice_exit":p.returncode,"log_tail":(p.stdout+p.stderr)[-400:] if not ok else ""}
results=[]
for i,(a,b) in enumerate(vectors):
 r=simulate(a,b,i);results.append(r)
 print(f"M53 vector {i+1}/{len(vectors)} {'PASS' if r['pass'] else 'FAIL'}",flush=True)
report={"topology":"16 physically cascaded M46 MOS ADD subcircuits; carry output directly feeds next carry input",
 "models":"LEVEL=1 idealized MOS and ideal voltage rails; DC only","results":results,
 "pass":sum(r["pass"] for r in results),"total":len(results),
 "physical_sha256d_complete":False}
(OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
print(f"M53 MOS ADD32 {report['pass']}/{report['total']} PASS")
sys.exit(0 if report["pass"]==report["total"] else 1)
