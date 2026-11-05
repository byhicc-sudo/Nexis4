#!/usr/bin/env python3
"""Integrated regression and honest gap audit. Runs existing verified tests."""
import json,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"results/full_sha_audit";OUT.mkdir(parents=True,exist_ok=True)
tests=[
 ("M38 nominal MOS DC",["python3","tests/check_m38.py"]),
 ("M40 MOS transient loads",["python3","tests/check_m40.py"]),
 ("M42 independent SHA256d",["python3","tests/check_m42_sha256d.py"]),
 ("M43 full quaternary SHA256d",["python3","tests/check_m43_quaternary_sha.py"]),
 ("RTL compile",["iverilog","-g2012","-s","tb","-o",str(OUT/"alu_test.vvp"),"rtl/nexis4_alu.v","tests/tb_nexis4_alu.v"]),
 ("RTL exhaustive + 32bit random",["vvp",str(OUT/"alu_test.vvp")]),
]
records=[]
for name,cmd in tests:
    start=time.monotonic()
    try:
        p=subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
        rc=p.returncode;output=p.stdout
    except (OSError,subprocess.TimeoutExpired) as e:
        rc=127;output=str(e)
    log=OUT/("test_%02d.log"%len(records))
    log.write_text(output)
    status="PASS" if rc==0 else "FAIL"
    print(f"{status} {name} ({time.monotonic()-start:.2f}s) log={log.relative_to(ROOT)}",flush=True)
    records.append({"name":name,"status":status,"returncode":rc,"log":str(log.relative_to(ROOT))})
    if rc!=0:
        print("\n".join(output.splitlines()[-12:]),flush=True)
gaps=[
 {"id":"G1","item":"Full SHA-256d implemented as physical four-level MOS transistor netlist","status":"NOT_IMPLEMENTED"},
 {"id":"G2","item":"Quaternary XOR/AND/NOT/ADD fabricated or PDK-verified at four voltage levels","status":"NOT_IMPLEMENTED"},
 {"id":"G3","item":"Full 192-round SHA256d RTL datapath, synthesis and timing closure","status":"NOT_IMPLEMENTED"},
 {"id":"G4","item":"MOS logic noise/process/temperature corners and contention-current audit","status":"NOT_VERIFIED"},
 {"id":"G5","item":"Whole SHA256d processor area, power, energy/hash and H/s","status":"NOT_MEASURED"},
 {"id":"G6","item":"Physical 1.1V/2.2V reference generation, distribution and rail losses","status":"NOT_IMPLEMENTED"}
]
report={"test_results":records,"gaps":gaps,"distinction":"RTL ALU is binary voltage implementation of two-bit symbols; not four-voltage hardware"}
(OUT/"audit.json").write_text(json.dumps(report,indent=2)+"\n")
print(f"\nRESULT {sum(r['status']=='PASS' for r in records)}/{len(records)} suites PASS")
print("UNRESOLVED PHYSICAL / FULL RTL GAPS:")
for g in gaps:print(f"  {g['id']} {g['status']}: {g['item']}")
if any(r["status"]!="PASS" for r in records):sys.exit(1)
