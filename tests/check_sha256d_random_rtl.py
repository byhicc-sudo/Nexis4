#!/usr/bin/env python3
"""Deterministic full SHA-256d RTL regression against independent hashlib.
Generates Verilog stimulus and checks raw 32-byte digests, no manual vectors.
"""
import hashlib,json,pathlib,random,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"results"/"sha256d_random_rtl";OUT.mkdir(parents=True,exist_ok=True)
rng=random.Random(20261105)
genesis=bytes.fromhex("01000000"+"00"*32+"3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a"+"29ab5f49"+"ffff001d"+"1dac2b7c")
assert len(genesis)==80
headers=[genesis,genesis[:76]+(int.from_bytes(genesis[76:],"little")+1).to_bytes(4,"little")]
headers += [rng.randbytes(80) for _ in range(32)]
# Include realistic nonce-only changes, plus randomized version/time/nonce.
headers += [genesis[:76]+i.to_bytes(4,"little") for i in range(16)]
headers += [rng.randbytes(4)+genesis[4:68]+rng.randbytes(4)+genesis[72:76]+rng.randbytes(4) for _ in range(16)]
tb=['`timescale 1ns/1ps','module tb_random;',
    'reg [639:0] header; wire [255:0] digest;',
    'integer errors;','nexis4_sha256d80 dut(header,digest);',
    'initial begin errors=0;']
for i,h in enumerate(headers):
    expected=hashlib.sha256(hashlib.sha256(h).digest()).digest()
    tb += [f"header=640'h{h.hex()}; #10;",
           f"if(digest !== 256'h{expected.hex()}) begin",
           f' $display("FAIL case={i} got=%h expected={expected.hex()}",digest); errors=errors+1;',
           f' end else $display("PASS case={i}");']
tb += ['if(errors) $fatal(1,"SHA256d RTL mismatch");',
       f'$display("PASS SHA256d randomized regression {len(headers)}/{len(headers)}");',
       '$finish; end endmodule']
(OUT/"tb_random.v").write_text("\n".join(tb)+"\n")
(OUT/"vectors.json").write_text(json.dumps([{"index":i,"header_hex":h.hex(),"sha256d_raw":hashlib.sha256(hashlib.sha256(h).digest()).hexdigest()} for i,h in enumerate(headers)],indent=2)+"\n")
steps=[
 ["iverilog","-g2012","-s","tb_random","-o",str(OUT/"tb_random.vvp"),"rtl/nexis4_sha256d80.v",str(OUT/"tb_random.v")],
 ["vvp",str(OUT/"tb_random.vvp")]
]
start=time.monotonic()
for cmd in steps:
    try:
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=180)
    except (OSError,subprocess.TimeoutExpired) as e:
        print("FAIL",e);sys.exit(1)
    (OUT/("compile.log" if cmd[0]=="iverilog" else "run.log")).write_text(p.stdout+p.stderr)
    if p.returncode:
        print("FAIL",cmd[0],p.returncode)
        print((p.stdout+p.stderr)[-4000:])
        sys.exit(p.returncode)
    if cmd[0]=="vvp":
        passes=sum(line.startswith("PASS case=") for line in p.stdout.splitlines())
        if passes!=len(headers):
            print(f"FAIL incomplete verification {passes}/{len(headers)}")
            sys.exit(1)
        print(f"PASS SHA256d RTL {passes}/{len(headers)} cases in {time.monotonic()-start:.2f}s")
        print("Vectors and logs: results/sha256d_random_rtl/")
print("NOTE: binary RTL functional equivalence only; no physical quaternary PDK, timing, power or H/s claim.")
