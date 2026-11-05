// M57: exact SHA256 header second-block round-3 nonce merge; no mining speed claim.
#define main m55_embedded_main
#include "m55_cpp_benchmark.cpp"
#undef main
#include <cassert>
template<class T> static bool check57(const std::array<uint8_t,80>& header,U& invariant){
 U mid[8];std::copy(IV,IV+8,mid);
 compress<T>(mid,header.data());
 U a=mid[0],b=mid[1],c=mid[2],d=mid[3],e=mid[4],f=mid[5],g=mid[6],h=mid[7];
 uint8_t chunk[64]={0};std::copy(header.begin()+64,header.end(),chunk);chunk[16]=0x80;chunk[62]=0x02;chunk[63]=0x80; // 80 bytes = 640 bits
 for(int t=0;t<4;t++){
  U w=(U(chunk[4*t])<<24)|(U(chunk[4*t+1])<<16)|(U(chunk[4*t+2])<<8)|chunk[4*t+3];
  U s1=T::xr(T::xr(T::rr(e,6),T::rr(e,11)),T::rr(e,25));
  U ch=T::xr(T::an(e,f),T::an(T::nt(e),g));
  U base=plus4<T>(h,s1,ch,K[t]);
  U s0=T::xr(T::xr(T::rr(a,2),T::rr(a,13)),T::rr(a,22));
  U maj=T::xr(T::xr(T::an(a,b),T::an(a,c)),T::an(b,c));
  U t2=T::add(s0,maj);
  if(t==3){
   U merge=T::add(base,w);
   U na=T::add(merge,t2),ne=T::add(d,merge);
   U recovered=T::add(merge,~base+1u);
   U recovered_a=T::add(na,~t2+1u);
   U recovered_e=T::add(ne,~d+1u);
   U delta=T::add(na,~ne+1u);
   invariant=delta;
   if(recovered!=w||recovered_a!=merge||recovered_e!=merge||
      delta!=T::add(t2,~d+1u))return false;
  }
  U t1=T::add(base,w);
  h=g;g=f;f=e;e=T::add(d,t1);d=c;c=b;b=a;a=T::add(t1,t2);
 }
 return true;
}
int main(int argc,char**argv){
 int n=argc>1?std::atoi(argv[1]):2048;
 if(n<1||n>100000){std::cerr<<"iterations 1..100000\n";return 2;}
 std::array<uint8_t,80> header{};
 uint32_t seed=0x579abc12u;
 for(int i=0;i<n;i++){
  for(auto&x:header){seed=1664525u*seed+1013904223u;x=uint8_t(seed>>24);}
  U db=0,dq=0;
  if(!check57<Binary>(header,db)||!check57<Quat>(header,dq)||db!=dq||
     sha2<Binary>(header)!=sha2<Quat>(header)){
   std::cerr<<"M57_FAIL index="<<i<<"\n";return 1;
  }
 }
 std::cout<<"M57_ROUND3_MERGE_RECOVERY PASS "<<n<<"/"<<n<<"\n";
 std::cout<<"M57_NONCE_FREE_DELTA PASS "<<n<<"/"<<n<<"\n";
 std::cout<<"M57_BINARY_QUAT_HASH_MATCH PASS "<<n<<"/"<<n<<"\n";
 std::cout<<"NOTE: exact round-3 identities, not early 90-LZ rejection or mining speedup.\n";
}
