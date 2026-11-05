#!/usr/bin/env python3
"""Create an encrypted Electrum SegWit wallet entirely on the user's machine.

No seed, private key or password is sent to the pool or GitHub.
"""
import getpass,os,pathlib,shutil,sys
def main():
 os.umask(0o077)
 home=pathlib.Path.home()
 wallet_dir=home/".electrum"/"wallets"
 wallet_dir.mkdir(mode=0o700,parents=True,exist_ok=True)
 wallet_path=wallet_dir/"NEXIS4_POOL"
 if wallet_path.exists():
  print("WALLET_EXISTS:",wallet_path)
  print("No new wallet was created; existing wallet will not be overwritten.")
  return 2
 try:
  from electrum.simple_config import SimpleConfig
  from electrum.wallet import create_new_wallet
  from electrum.util import create_and_start_event_loop
 except ImportError as e:
  print("ELECTRUM_IMPORT_ERROR:",e,file=sys.stderr);return 3
 password=getpass.getpass("Yeni cüzdan şifresi (en az 16 karakter): ")
 confirm=getpass.getpass("Şifreyi tekrar gir: ")
 if len(password)<16 or password!=confirm:
  print("ERROR: Şifreler eşleşmiyor veya 16 karakterden kısa.",file=sys.stderr);return 4
 confirm=None
 try:
  create_and_start_event_loop()
  config=SimpleConfig({"electrum_path":str(home/".electrum")})
  result=create_new_wallet(path=str(wallet_path),passphrase=None,password=password,
    encrypt_file=True,seed_type="segwit",config=config)
  wallet=result["wallet"]
  addresses=wallet.get_receiving_addresses()
  if not addresses:raise RuntimeError("No receiving addresses generated")
  address=addresses[0]
  if not address.startswith("bc1q"):raise RuntimeError("Unexpected address type: not mainnet native SegWit")
  os.chmod(wallet_path,0o600)
  backup_dir=home/"NEXIS4_WALLET_BACKUP"
  backup_dir.mkdir(mode=0o700,exist_ok=True);os.chmod(backup_dir,0o700)
  backup=backup_dir/"NEXIS4_POOL.electrum"
  if backup.exists():raise RuntimeError("Backup already exists; refusing overwrite")
  shutil.copy2(wallet_path,backup);os.chmod(backup,0o600)
  print("WALLET_CREATED:",wallet_path)
  print("BTC_RECEIVE_ADDRESS:",address)
  print("ENCRYPTED_BACKUP:",backup)
  print("POOL_WORKER:",address+".NEXIS4")
  print("POOL_TEST_COMMAND:")
  print('cd "$HOME/Masaüstü/nexis4" && bash scripts/TEST_M49_POOL.sh --host stratum.ckpool.org --port 3333 --user "'+address+'.NEXIS4" --seconds 45 --max-jobs 3')
  print("IMPORTANT: Save recovery seed offline using Electrum GUI before depositing funds; an encrypted backup alone is not enough if password is lost.")
  return 0
 except Exception as e:
  print("WALLET_SETUP_ERROR:",type(e).__name__,str(e),file=sys.stderr)
  print("Do not retry by deleting any created wallet. Inspect it first.",file=sys.stderr)
  return 1
if __name__=="__main__":sys.exit(main())
