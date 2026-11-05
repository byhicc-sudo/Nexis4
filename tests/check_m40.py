#!/usr/bin/env python3
"""M40: sampled waveform timing, contention proxies and supply-energy audit."""
import json, pathlib, re, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"results/m40"
OUT.mkdir(parents=True,exist_ok=True)
base=(ROOT/"spice/m38_integrated.cir").read_text()
def crossing(points, level):
    for (t0,v0),(t1,v1) in zip(points,points[1:]):
        if v0 < level <= v1 and v1 != v0:
            return t0+(level-v0)*(t1-t0)/(v1-v0)
    return None
def energy(rows,idx,a,b):
    z=[r for r in rows if a<=r[0]<=b]
    return sum(((-z[k][idx])*3.3 if idx==7 else (-z[k][idx])*(1.1 if idx==8 else 2.2) + (-z[k+1][idx])*(1.1 if idx==8 else 2.2))*(z[k+1][0]-z[k][0])/2 for k in range(len(z)-1)) if idx!=7 else sum((-z[k][idx]-z[k+1][idx])*3.3*(z[k+1][0]-z[k][0])/2 for k in range(len(z)-1))
results=[]
for load in (20,500):
    src,n=re.subn(r"(?m)^VIN in 0 0$", "VIN in 0 PWL(0n 0 5n 0 5.01n 1.1 15n 1.1 15.01n 2.2 25n 2.2 25.01n 3.3 40n 3.3)",base)
    src,m=re.subn(r"(?m)^CLOAD out 0 20f$",f"CLOAD out 0 {load}f",src)
    src,q=re.subn(r"(?m)^\.dc VIN 0 3\.31 0\.01$", ".tran 0.001n 40n",src)
    if (n,m,q)!=(1,1,1):sys.exit("FAIL: source structure changed")
    src=src[:src.index(".control\n")]+f""".control
set noaskquit
set wr_singlescale
set wr_vecnames
run
wrdata results/m40/wave_{load}f.txt v(in) v(out) v(s0) v(s1) v(s2) v(t3) i(VDD) i(VREF1) i(VREF2)
quit
.endc
.end
"""
    deck=OUT/f"deck_{load}f.cir"
    deck.write_text(src)
    log=OUT/f"ngspice_{load}f.log"
    with log.open("w") as fh:
        p=subprocess.run(["ngspice","-b",str(deck)],cwd=ROOT,stdout=fh,stderr=subprocess.STDOUT)
    if p.returncode:sys.exit(f"FAIL ngspice load={load}f: {log}")
    rows=[]
    for line in (OUT/f"wave_{load}f.txt").read_text().splitlines():
        try: nums=[float(x) for x in line.split()]
        except ValueError:continue
        if len(nums)==10:rows.append(nums)
    if len(rows)<1000:sys.exit(f"FAIL waveform parsing load={load}f")
    events=[]
    for edge,target in ((5.0,1.1),(15.0,2.2),(25.0,3.3)):
        prev=target-1.1
        w=[r for r in rows if edge-0.1<=r[0]*1e9<=edge+5]
        inp=[(r[0]*1e9,r[1]) for r in w]
        out=[(r[0]*1e9,r[2]) for r in w]
        tin=crossing(inp,prev+0.5*1.1)
        t10=crossing(out,prev+0.1*1.1)
        t50=crossing(out,prev+0.5*1.1)
        t90=crossing(out,prev+0.9*1.1)
        after=[r for r in rows if edge<=r[0]*1e9<=edge+5]
        lastbad=max((k for k,r in enumerate(after) if abs(r[2]-target)>0.05),default=-1)
        settled=None if lastbad>=len(after)-1 else after[lastbad+1][0]*1e9
        events.append({"edge_ns":edge,"target_V":target,
          "input_mid_ns":tin,"output_mid_ns":t50,
          "propagation_ns":None if tin is None or t50 is None else t50-tin,
          "output_10_90_ns":None if t10 is None or t90 is None else t90-t10,
          "settle_from_input_mid_ns":None if settled is None or tin is None else settled-tin})
    overlap=sum(sum(r[j]>1.65 for j in (3,4,5,6))>1 for r in rows)
    # Positive delivered energy; negative denotes net energy returned to a source.
    energy_j={}
    for idx,name,volt in ((7,"VDD",3.3),(8,"VREF1",1.1),(9,"VREF2",2.2)):
        energy_j[name]=sum(-0.5*(rows[k][idx]+rows[k+1][idx])*volt*(rows[k+1][0]-rows[k][0]) for k in range(len(rows)-1))
    metrics={"load_fF":load,"samples":len(rows),"sampled_overlaps":overlap,
      "peak_source_current_mA":{name:max(abs(r[idx]) for r in rows)*1000 for idx,name in ((7,"VDD"),(8,"VREF1"),(9,"VREF2"))},
      "signed_source_energy_pJ":{k:v*1e12 for k,v in energy_j.items()},
      "net_delivered_energy_pJ":sum(energy_j.values())*1e12,
      "transitions":events}
    results.append(metrics)
    print(f"M40 load={load}fF samples={len(rows)} overlaps={overlap} energy={metrics['net_delivered_energy_pJ']:.4f}pJ")
    for e in events:
        print(f"  {e['target_V']:.1f}V propagation={e['propagation_ns']}ns rise10_90={e['output_10_90_ns']}ns settle={e['settle_from_input_mid_ns']}ns")
(OUT/"metrics.json").write_text(json.dumps({"results":results,"limitations":["LEVEL=1 and ideal reference rails","sampled threshold overlap does not exclude simultaneous partial conduction","signed rail energy is not equivalent to isolated logic-cell energy","no physical chip timing or SHA256d H/s"]},indent=2)+"\n")
if any(x["sampled_overlaps"] for x in results):sys.exit("FAIL M40 sampled selection overlap")
if any(any(e["propagation_ns"] is None or e["output_10_90_ns"] is None or e["settle_from_input_mid_ns"] is None for e in x["transitions"]) for x in results):sys.exit("FAIL M40 missing timing crossings")
print("PASS M40 waveform metrics computed; inspect energy and timings before performance claims")
