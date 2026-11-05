// M68: exercise the actual live integrated_hash<Quat> and its 50-LZ gate.
// Compile: g++ -std=c++17 -O2 tests/m68_live_gate_regression.cpp -o /tmp/nexis4_m68 && /tmp/nexis4_m68
#define NEXIS4_EMBED_LIVE_ENGINE
#include "m59_live_engine.cpp"
#undef main
#include <iostream>
int main(){
 std::array<uint8_t,80> header{};
 uint32_t seed=0x20261105u;
 auto next=[&](){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed;};
 unsigned long long full=0, early_reject=0, gate50=0;
 for(int i=0;i<8192;i++){
  for(auto &b:header)b=uint8_t(next());
  bool qpass=false,bpass=false,epass=false,qdone=false,bdone=false,edone=false;
  unsigned qr=0,br=0,er=0,qs=0,bs=0,es=0;
  Digest q=integrated_hash<Quat>(header,qpass,qr,qs,false,qdone);
  Digest b=integrated_hash<Binary>(header,bpass,br,bs,false,bdone);
  if(!qdone||!bdone||q!=b||qpass!=bpass||qpass!=(lz60(q)>=50)){
   std::cerr<<"FAIL full i="<<i<<" quat="<<hex(q)<<" binary="<<hex(b)<<" qpass="<<qpass<<" lz="<<lz60(q)<<"\n";
   return 1;
  }
  Digest e=integrated_hash<Quat>(header,epass,er,es,true,edone);
  if(edone){
   if(e!=q||!epass||lz60(e)<50){std::cerr<<"FAIL early survivor i="<<i<<"\n";return 1;}
  }else{
   if(qpass||lz60(q)>=50||es!=61 && es!=62){std::cerr<<"FAIL early rejection i="<<i<<"\n";return 1;}
   ++early_reject;
  }
  ++full;gate50+=qpass;
 }
 std::cout<<"PASS M68 actual_live_engine full="<<full<<" quat_binary_equal="<<full<<" early_reject="<<early_reject<<" gate50="<<gate50<<"\n";
 return 0;
}
