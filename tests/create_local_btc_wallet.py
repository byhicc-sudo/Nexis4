#!/usr/bin/env python3
"""Create encrypted Bitcoin Core mainnet descriptor wallet locally.
No private keys or passphrases are written to project/GitHub.
Requires a running Bitcoin Core node with local cookie RPC.
"""
import base64,getpass,json,os,pathlib,sys,urllib.error,urllib.request,urllib.parse
HOME=pathlib.Path.home();WALLET="NEXIS4_POOL"
def rpc(method,params=None,wallet=None):
 cookie=HOME/".bitcoin"/".cookie"
 if not cookie.is_file():raise RuntimeError("Bitcoin Core RPC cookie missing; start bitcoind/Bitcoin Core first")
 userpass=cookie.read_text().strip()
 path="/wallet/"+urllib.parse.quote(wallet,safe="") if wallet else "/"
 req=urllib.request.Request("http://127.0.0.1:8332"+path,
  data=json.dumps({"jsonrpc":"1.0","id":"nexis4-local","method":method,"params":params or []}).encode(),
  headers={"Content-Type":"application/json","Authorization":"Basic "+base64.b64encode(userpass.encode()).decode()})
 with urllib.request.urlopen(req,timeout=15) as resp:reply=json.load(resp)
 if reply.get("error"):raise RuntimeError(str(reply["error"]))
 return reply["result"]
def main():
 print("NEXIS4: local Bitcoin Core encrypted wallet; no keys uploaded")
 try:
  info=rpc("getblockchaininfo")
  if info.get("chain")!="main":raise RuntimeError("Bitcoin Core is not on mainnet")
  existing=rpc("listwalletdir")["wallets"]
  names={w["name"] for w in existing}
  if WALLET not in names:
   pw=getpass.getpass("New wallet encryption passphrase (not displayed): ")
   confirm=getpass.getpass("Repeat passphrase: ")
   if len(pw)<16 or pw!=confirm:raise RuntimeError("Passphrases must match and be at least 16 characters")
   # RPC request remains on localhost; password never in shell args or project.
   rpc("createwallet",{"wallet_name":WALLET,"disable_private_keys":False,"blank":False,"passphrase":pw,"descriptors":True})
   pw=confirm=None
  elif WALLET not in rpc("listwallets"):
   rpc("loadwallet",[WALLET])
  walletinfo=rpc("getwalletinfo",wallet=WALLET)
  if "unlocked_until" not in walletinfo:raise RuntimeError("Existing wallet is not encrypted; refusing to proceed")
  address=rpc("getnewaddress",["NEXIS4 mining","bech32"],wallet=WALLET)
  validation=rpc("validateaddress",[address])
  if not validation.get("isvalid") or not address.startswith("bc1"):raise RuntimeError("Invalid mainnet address")
  backup_dir=HOME/"NEXIS4_WALLET_BACKUP"
  backup_dir.mkdir(mode=0o700,exist_ok=True);os.chmod(backup_dir,0o700)
  backup=backup_dir/"NEXIS4_POOL_wallet_backup.dat"
  if backup.exists():raise RuntimeError(f"Backup already exists; refusing overwrite: {backup}")
  rpc("backupwallet",[str(backup)],wallet=WALLET)
  os.chmod(backup,0o600)
  print("WALLET_CREATED_OR_LOADED:",WALLET)
  print("BTC_RECEIVE_ADDRESS:",address)
  print("BACKUP:",backup)
  print("WARNING: Move backup to encrypted offline storage. Losing passphrase/backup can lose funds.")
  print("POOL_WORKER:",address+".NEXIS4")
  print("POOL_TEST_COMMAND:")
  print(f'bash scripts/TEST_M49_POOL.sh --host stratum.ckpool.org --port 3333 --user "{address}.NEXIS4" --seconds 45 --max-jobs 3')
  return 0
 except (RuntimeError,OSError,urllib.error.URLError,ValueError,KeyError) as e:
  print("SETUP_NOT_COMPLETE:",e,file=sys.stderr)
  print("Bitcoin Core mainnet with wallet RPC must be installed and running. No wallet is claimed created.",file=sys.stderr)
  return 1
if __name__=="__main__":sys.exit(main())
