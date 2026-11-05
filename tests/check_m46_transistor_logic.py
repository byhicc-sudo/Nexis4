#!/usr/bin/env python3
"""M46: actual MOS threshold sensing and CMOS logic network for 4-level arithmetic.
Python generates *fixed circuit topology* from truth tables; never supplies
case-dependent output-select signals. All decisions are transistor networks.
Simplified LEVEL=1 MOS models, ideal reference rails, DC only.
"""
import json,pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"results/m46_transistor_logic";OUT.mkdir(parents=True,exist_ok=True)
VDD=3.3
# CMOS inverter and NAND2 are built from MOSFETs; NOR2 likewise.
class Net:
 def __init__(self):
  self.lines=[];self.n=0
 def add(self,s):self.lines.append(s)
 def inv(self,x):
  self.n+=1;y=f"iv{self.n}"
  self.add(f"MI{self.n}N {y} {x} 0 0 NLOG W=10u L=1u")
  self.add(f"MI{self.n}P {y} {x} vdd vdd PLOG W=20u L=1u")
  return y
 def nand(self,x,y):
  self.n+=1;k=self.n;z=f"nd{k}";m=f"nm{k}"
  self.add(f"MN{k}A {z} {x} {m} 0 NLOG W=10u L=1u")
  self.add(f"MN{k}B {m} {y} 0 0 NLOG W=10u L=1u")
  self.add(f"MP{k}A {z} {x} vdd vdd PLOG W=20u L=1u")
  self.add(f"MP{k}B {z} {y} vdd vdd PLOG W=20u L=1u")
  return z
 def and2(self,x,y):return self.inv(self.nand(x,y))
 def or2(self,x,y):return self.nand(self.inv(x),self.inv(y))
 def or_many(self,terms):
  if not terms:return "0"
  v=terms[0]
  for x in terms[1:]:v=self.or2(v,x)
  return v
 def decode(self,prefix,inp):
  # Three physically sensed thresholds, raw outputs pulled up by resistors.
  t=[]
  for j,threshold in enumerate((0.55,1.65,2.75),1):
   raw=f"{prefix}raw{j}"
   self.add(f"R{prefix}{j} vdd {raw} 10k")
   self.add(f"MS{prefix}{j} {raw} {inp} 0 0 NTH{j} W=10u L=1u")
   t.append(self.inv(raw))
  u,v,w=t
  return [self.inv(u),self.and2(u,self.inv(v)),self.and2(v,self.inv(w)),w]
def logic(a,b,cin,op):
 if op=="XOR":return a^b,0
 if op=="AND":return a&b,0
 if op=="NOT":return a^3,0
 s=a+b+cin
 return s&3,s>>2
def circuit(op):
 n=Net()
 n.add("* M46: full MOSFET decision logic, fixed topology across all test cases")
 n.add("VDD vdd 0 3.3\nVR1 ref1 0 1.1\nVR2 ref2 0 2.2")
 n.add("VA ain 0 {VA}\nVB bin 0 {VB}\nVC ci 0 {VC}")
 da=n.decode("a","ain");db=n.decode("b","bin")
 # Carry-in is physically sensed with CMOS inverter; input 0/3.3V.
 c0=n.inv("ci");c1=n.inv(c0)
 groups=[[],[],[],[]];carry_terms=[]
 for a in range(4):
  for b in range(4):
   base=n.and2(da[a],db[b])
   for cin in ((0,1) if op=="ADD" else (0,)):
    term=n.and2(base,(c0 if cin==0 else c1)) if op=="ADD" else base
    digit,co=logic(a,b,cin,op)
    groups[digit].append(term)
    if co:carry_terms.append(term)
 sel=[n.or_many(g) for g in groups]
 cout=n.or_many(carry_terms)
 # Complementary transmission-gate controls generated with MOS inverters.
 for k,rail in enumerate(("0","ref1","ref2","vdd")):
  comp=n.inv(sel[k])
  n.add(f"MOUT{k}N out {sel[k]} {rail} 0 NLOG W=10u L=1u")
  n.add(f"MOUT{k}P out {comp} {rail} vdd PLOG W=20u L=1u")
 n.add("RLEAK out 0 1G\nCLOAD out 0 20f")
 n.add(".model NTH1 NMOS (LEVEL=1 VTO=0.55 KP=0.001 LAMBDA=0.02)")
 n.add(".model NTH2 NMOS (LEVEL=1 VTO=1.65 KP=0.001 LAMBDA=0.02)")
 n.add(".model NTH3 NMOS (LEVEL=1 VTO=2.75 KP=0.001 LAMBDA=0.02)")
 n.add(".model NLOG NMOS (LEVEL=1 VTO=0.55 KP=0.001 LAMBDA=0.02)")
 n.add(".model PLOG PMOS (LEVEL=1 VTO=-0.55 KP=0.0005 LAMBDA=0.02)")
 n.add(f"RCO cout_probe {cout} 1m")
 n.add(".control\nset noaskquit\nop\nprint v(out) v(cout_probe)\nquit\n.endc\n.end")
 return "\n".join(n.lines)+"\n",cout
pat=re.compile(r"v\((out|[a-z0-9_]+)\)\s*=\s*([-+\d.eE]+)",re.I)
results=[];fail=[]
for op in ("XOR","AND","NOT","ADD"):
 template,cout=circuit(op)
 (OUT/f"{op.lower()}_topology.cir").write_text(template.replace("{VA}","0").replace("{VB}","0").replace("{VC}","0"))
 for a in range(4):
  for b in range(4):
   for ci in ((0,1) if op=="ADD" else (0,)):
    text=template.replace("{VA}",str(a*1.1)).replace("{VB}",str(b*1.1)).replace("{VC}",str(ci*3.3))
    idx=len(results);path=OUT/f"case_{idx:03d}.cir";path.write_text(text)
    try:
     p=subprocess.run(["ngspice","-b",str(path)],cwd=ROOT,capture_output=True,text=True,timeout=25)
     vals={k.lower():float(v) for k,v in pat.findall(p.stdout+"\n"+p.stderr)}
     measured=vals.get("out");carry_v=vals.get("cout_probe")
     digit,co=logic(a,b,ci,op)
     ok=p.returncode==0 and measured is not None and abs(measured-digit*1.1)<0.18 and carry_v is not None and abs(carry_v-co*3.3)<0.3
     entry={"op":op,"a":a,"b":b,"cin":ci,"expected_v":digit*1.1,"out_v":measured,"expected_carry_v":co*3.3,"carry_v":carry_v,"pass":ok}
     if not ok:entry["ngspice_tail"]=(p.stdout+p.stderr)[-700:]
    except (OSError,subprocess.TimeoutExpired) as e:
     entry={"op":op,"a":a,"b":b,"cin":ci,"pass":False,"error":str(e)}
    results.append(entry)
    if not entry["pass"]:fail.append(entry)
report={"cases":len(results),"pass":len(results)-len(fail),"fail":fail,"model":"MOS threshold sensors + CMOS NAND/inverters + MOS output TG; no ideal truth-table output controls","limits":["LEVEL=1 idealized models","ideal reference voltage rails","DC only","not a full SHA256d physical chip","no PDK, timing, power or noise margin verification"]}
(OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
print(f"M46 transistor decision logic SPICE {report['pass']}/{report['cases']} PASS")
for x in fail[:6]:print("FAIL",x)
print("MOS truth-table network topology is fixed per operation; input voltages are only case-dependent.")
sys.exit(bool(fail))
