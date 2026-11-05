#!/usr/bin/env python3
"""NEXIS4 integrated verification runner. Never submits pool shares."""
import argparse,datetime,json,os,pathlib,shutil,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
SPECS=[
 ("M38","scripts/TEST_M38.sh",["ngspice","python3"],"four-level regeneration"),
 ("M43","scripts/TEST_M43.sh",["python3"],"quaternary SHA-256d reference"),
 ("M45","scripts/TEST_M45.sh",["ngspice","python3"],"ideal-selected MOS switching"),
 ("M46","scripts/TEST_M46.sh",["ngspice","python3"],"transistor-derived CMOS logic DC"),
 ("M47","scripts/TEST_M47.sh",["ngspice","python3"],"transistor transient endpoints"),
 ("RTL-SHA","scripts/TEST_SHA256D_RTL.sh",["iverilog","vvp"],"SHA-256d RTL genesis vectors"),
 ("RTL-RANDOM","scripts/TEST_SHA256D_RANDOM.sh",["iverilog","vvp","python3"],"independent randomized RTL SHA-256d"),
 ("RTL-QUAT","scripts/TEST_QUATERNARY_GATE_AUDIT.sh",["iverilog","vvp","ngspice"],"quaternary symbol gate and MOS audit"),
 ("STRATUM-OFFLINE","scripts/TEST_STRATUM_OFFLINE.sh",["python3"],"offline Stratum framing, job and difficulty"),
]
def run():
 p=argparse.ArgumentParser();p.add_argument("--include-slow",action="store_true");p.add_argument("--stop-on-fail",action="store_true");args=p.parse_args()
 out=ROOT/"results"/"integration";out.mkdir(parents=True,exist_ok=True)
 records=[]
 for name,script,tools,description in SPECS:
  path=ROOT/script
  missing=[x for x in tools if shutil.which(x) is None]
  if not path.exists():record={"name":name,"status":"NOT_IMPLEMENTED","description":description,"script":script}
  elif missing:record={"name":name,"status":"BLOCKED_DEPENDENCY","missing":missing,"script":script}
  elif name in ("M45","M46","M47") and not args.include_slow:
   record={"name":name,"status":"NOT_RUN_SLOW","script":script}
  else:
   start=time.monotonic()
   try:
    r=subprocess.run(["bash",str(path)],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=900)
    status="PASS" if r.returncode==0 else "FAIL"
    log=out/(name.lower().replace("-","_")+".log");log.write_text(r.stdout)
    record={"name":name,"status":status,"seconds":round(time.monotonic()-start,3),"returncode":r.returncode,"log":str(log.relative_to(ROOT))}
   except subprocess.TimeoutExpired as e:
    record={"name":name,"status":"TIMEOUT","seconds":round(time.monotonic()-start,3)}
  records.append(record)
  print(f"{name:18} {record['status']}",flush=True)
  if args.stop_on_fail and record["status"] in ("FAIL","TIMEOUT"):break
 gates={"binary_rtl_validated":all(x["status"]=="PASS" for x in records if x["name"] in ("RTL-SHA","RTL-RANDOM")),
 "four_voltage_dc_validated":any(x["name"]=="M46" and x["status"]=="PASS" for x in records),
 "physical_four_voltage_sha256d_validated":False,
 "live_pool_share_accepted":False}
 report={"created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"tests":records,"gates":gates,"notes":["Missing, skipped and failed tests never count as PASS","Binary RTL and MOS four-voltage logic are separate implementations","Live pool mining and full physical SHA-256d not included","No silicon PDK, PVT or silicon measurements"]}
 (out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
 failures=[x for x in records if x["status"] in ("FAIL","TIMEOUT","BLOCKED_DEPENDENCY","NOT_IMPLEMENTED")]
 print(f"\nTESTS {sum(x['status']=='PASS' for x in records)}/{len(records)} PASS; OPEN ITEMS {len(failures)}")
 print("REPORT results/integration/report.json")
 return bool(failures)
if __name__=="__main__":sys.exit(run())
