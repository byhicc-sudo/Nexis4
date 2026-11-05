// Build: g++ -std=c++17 -O2 tests/babm_staged_gate_test.cpp -o /tmp/babm_gate_test
#define main m56_embedded_main
#include "m56_gate_benchmark.cpp"
#undef main
#include "babm_staged_gate.h"
#include <iostream>
int main(){
 std::array<uint8_t,80> h{};
 uint32_t seed=0x31415926u;
 unsigned long long stopped61=0,stopped62=0,stopped63=0,pass=0;
 for(int i=0;i<1024;i++){
  for(auto &b:h){seed=seed*1664525u+1013904223u;b=uint8_t(seed>>24);}
  unsigned rounds=0;
  bool gate=babm_target90_staged<Binary>(h,rounds);
  bool full=target90(sha2<Binary>(h));
  if(gate!=full){std::cerr<<"FAIL gate mismatch at "<<i<<"\n";return 1;}
  if(rounds==61)++stopped61;
  else if(rounds==62)++stopped62;
  else if(rounds==63)++stopped63;
  else {std::cerr<<"FAIL round count "<<rounds<<"\n";return 1;}
  pass+=gate;
 }
 // Test the 90-bit conditions directly on synthetic post-round states,
 // including an exact hit and one-bit mutations. This avoids the
 // vacuous all-negative-only randomized hash test.
 U e61=U(0)-IV[7],e62=U(0)-IV[6],e63=U(0)-IV[5];
 auto condition=[](U x,U y,U z){
  return x==0xA41F32E7u&&y==0xE07C2655u&&((z+IV[5])&0xC0FFFFFFu)==0;
 };
 if(!condition(e61,e62,e63)){std::cerr<<"FAIL positive synthetic state\n";return 1;}
 for(int bit=0;bit<32;bit++){
  if(condition(e61^(U(1)<<bit),e62,e63)||
     condition(e61,e62^(U(1)<<bit),e63)){std::cerr<<"FAIL first 64 bits\n";return 1;}
  if((U(0xC0FFFFFFu)&(U(1)<<bit))&&condition(e61,e62,e63^(U(1)<<bit))){
   std::cerr<<"FAIL last 26 bits\n";return 1;
  }
 }
 std::cout<<"PASS samples=1024 stage61="<<stopped61
          <<" stage62="<<stopped62<<" stage63="<<stopped63
          <<" target90="<<pass<<" synthetic_positive=1 bit_mutations=90\n";
}
