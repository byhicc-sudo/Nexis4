#!/usr/bin/env python3
"""M52 SHA256d physical four-voltage implementation gap audit.
Evidence-based: no binary RTL or Python SHA result counts as transistor SHA.
"""
import json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"results"/"m52_architecture";OUT.mkdir(parents=True,exist_ok=True)
p=ROOT/"results"/"m46_transistor_logic"/"report.json"
report=json.loads(p.read_text()) if p.exists() else None
ops={
 "symbol_decode":{"physical_evidence":"M46 MOS threshold sensors","validated":bool(report and report.get("cases")==80 and report.get("pass")==80)},
 "symbol_xor":{"physical_evidence":"M46 fixed MOS network, 4x4 DC","validated":bool(report and report.get("pass")==80)},
 "symbol_and":{"physical_evidence":"M46 fixed MOS network, 4x4 DC","validated":bool(report and report.get("pass")==80)},
 "symbol_not":{"physical_evidence":"M46 fixed MOS network, 4x4 DC","validated":bool(report and report.get("pass")==80)},
 "symbol_add_with_carry":{"physical_evidence":"M46 fixed MOS network, 4x4x2 DC","validated":bool(report and report.get("pass")==80)},
 "word_add32":{"physical_evidence":"No cascaded 16-symbol transistor carry-chain simulation","validated":False},
 "word_rotate32":{"physical_evidence":"No routed four-level MOS 32-bit rotate network","validated":False},
 "word_shift32":{"physical_evidence":"No routed four-level MOS 32-bit shift network","validated":False},
 "sha_ch_maj":{"physical_evidence":"No physically interconnected 32-bit Ch/Maj network","validated":False},
 "sha_message_schedule":{"physical_evidence":"No transistor-level W0-W63 schedule","validated":False},
 "sha_round64":{"physical_evidence":"No transistor-level 64-round compression","validated":False},
 "sha256d_80byte":{"physical_evidence":"No 192-round physical four-level SHA256d integration","validated":False},
 "pvt_noise_power":{"physical_evidence":"No foundry PDK/PVT/noise/power qualification","validated":False},
}
out={"architecture":"four-voltage MOS data path; binary only for protocol I/O and independent reference","operations":ops,
"validated_count":sum(x["validated"] for x in ops.values()),"total_count":len(ops),
"physical_sha256d_complete":False,
"warning":"Passing software M51 or binary RTL cannot close physical transistor-level gaps"}
(OUT/"report.json").write_text(json.dumps(out,indent=2)+"\n")
for name,entry in ops.items():print(("PASS " if entry["validated"] else "OPEN ")+name+" — "+entry["physical_evidence"])
print(f'M52 PHYSICAL COVERAGE {out["validated_count"]}/{out["total_count"]}; physical SHA256d NOT IMPLEMENTED')
sys.exit(0 if report and report.get("pass")==80 else 2)
