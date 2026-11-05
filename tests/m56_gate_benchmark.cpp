#include <array>
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>
using U=uint32_t;
using Digest=std::array<uint8_t,32>;
static constexpr U K[64]={
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,
0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,
0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,
0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,
0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,
0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,
0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static constexpr U IV[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
struct Binary {
 static inline U add(U a,U b){return a+b;}
 static inline U xr(U a,U b){return a^b;}
 static inline U an(U a,U b){return a&b;}
 static inline U nt(U a){return ~a;}
 static inline U rr(U a,unsigned n){return (a>>n)|(a<<(32-n));}
 static inline U sr(U a,unsigned n){return a>>n;}
};
struct Quat {
 static inline U add(U a,U b){
  U out=0,carry=0;
  for(unsigned i=0;i<16;i++){U t=((a>>(i*2))&3)+((b>>(i*2))&3)+carry;out|=(t&3)<<(i*2);carry=t>>2;}
  return out;
 }
 static inline U xr(U a,U b){
  U out=0;for(unsigned i=0;i<16;i++){unsigned s=i*2;out|=(((a>>s)&3)^((b>>s)&3))<<s;}return out;
 }
 static inline U an(U a,U b){
  U out=0;for(unsigned i=0;i<16;i++){unsigned s=i*2;out|=(((a>>s)&3)&((b>>s)&3))<<s;}return out;
 }
 static inline U nt(U a){U out=0;for(unsigned i=0;i<16;i++){unsigned s=i*2;out|=(3^((a>>s)&3))<<s;}return out;}
 static inline U rr(U a,unsigned n){
  U out=0;for(unsigned i=0;i<16;i++){unsigned s=(2*i+n)&31;U digit=((a>>s)&3);if(s==31)digit=((a>>31)|((a&1)<<1));out|=digit<<(2*i);}return out;
 }
 static inline U sr(U a,unsigned n){
  U out=0;for(unsigned i=0;i<16;i++){unsigned s=2*i+n;U digit=s>=32?0:((a>>s)&3);out|=digit<<(2*i);}return out;
 }
};
template<class T> static inline U plus4(U a,U b,U c,U d){return T::add(T::add(T::add(a,b),c),d);}
template<class T> static bool compress(U state[8],const uint8_t*block,bool gate=false,unsigned*rounds=nullptr){
 U w[64];
 for(int i=0;i<16;i++)w[i]=(U(block[4*i])<<24)|(U(block[4*i+1])<<16)|(U(block[4*i+2])<<8)|block[4*i+3];
 for(int i=16;i<64;i++){
  U x=w[i-15],y=w[i-2];
  U s0=T::xr(T::xr(T::rr(x,7),T::rr(x,18)),T::sr(x,3));
  U s1=T::xr(T::xr(T::rr(y,17),T::rr(y,19)),T::sr(y,10));
  w[i]=plus4<T>(w[i-16],s0,w[i-7],s1);
 }
 U a=state[0],b=state[1],c=state[2],d=state[3],e=state[4],f=state[5],g=state[6],h=state[7];
 for(int i=0;i<64;i++){
  U s1=T::xr(T::xr(T::rr(e,6),T::rr(e,11)),T::rr(e,25));
  U ch=T::xr(T::an(e,f),T::an(T::nt(e),g));
  U t1=T::add(plus4<T>(h,s1,ch,K[i]),w[i]);
  U s0=T::xr(T::xr(T::rr(a,2),T::rr(a,13)),T::rr(a,22));
  U maj=T::xr(T::xr(T::an(a,b),T::an(a,c)),T::an(b,c));
  U t2=T::add(s0,maj);
  h=g;g=f;f=e;e=T::add(d,t1);d=c;c=b;b=a;a=T::add(t1,t2);
  if(rounds) ++*rounds;
  if(gate && ((i==60 && e!=0xA41F32E7u) || (i==61 && e!=0xE07C2655u) || (i==62 && ((e+IV[5])&0xC0FFFFFFu)!=0))) return false;
 }
 U v[8]={a,b,c,d,e,f,g,h};
 for(int i=0;i<8;i++)state[i]=T::add(state[i],v[i]);
 return true;
}
template<class T> static Digest sha(const uint8_t*data,size_t n){
 U st[8];std::copy(IV,IV+8,st);
 size_t total=((n+9+63)/64)*64;
 std::vector<uint8_t> buf(total,0);
 std::copy(data,data+n,buf.begin());buf[n]=0x80;
 uint64_t bits=uint64_t(n)*8;
 for(int i=0;i<8;i++)buf[total-1-i]=uint8_t(bits>>(8*i));
 for(size_t i=0;i<total;i+=64)compress<T>(st,buf.data()+i);
 Digest out{};for(int i=0;i<8;i++)for(int j=0;j<4;j++)out[4*i+j]=uint8_t(st[i]>>(24-8*j));return out;
}
template<class T> static Digest sha2(const std::array<uint8_t,80>&data){
 Digest first=sha<T>(data.data(),data.size());return sha<T>(first.data(),first.size());
}
static std::string hex(const Digest&d){static const char* h="0123456789abcdef";std::string s;for(auto b:d){s+=h[b>>4];s+=h[b&15];}return s;}
static volatile uint64_t sink=0;
template<class T> static double bench(std::array<uint8_t,80> data,int n){
 auto start=std::chrono::steady_clock::now();
 uint64_t checksum=0;
 for(int i=0;i<n;i++){
  data[76]=uint8_t(i);data[77]=uint8_t(i>>8);data[78]=uint8_t(i>>16);data[79]=uint8_t(i>>24);
  Digest d=sha2<T>(data);checksum+=d[i&31];
 }
 auto end=std::chrono::steady_clock::now();sink=sink+checksum;
 return std::chrono::duration<double>(end-start).count();
}
int m55_original_main(int argc,char**argv){
 int n=argc>1?std::atoi(argv[1]):1000;if(n<1||n>1000000){std::cerr<<"iterations must be 1..1000000\n";return 2;}
 std::array<uint8_t,80> data{};for(int i=0;i<80;i++)data[i]=uint8_t(i);
 const std::string known="852c98044fb00507122ff63bda7b529566348fc204f72b00dff1afd7b40501e4";
 auto b=sha2<Binary>(data),q=sha2<Quat>(data);
 if(hex(b)!=known||b!=q){std::cerr<<"FAIL known vector binary="<<hex(b)<<" quaternary="<<hex(q)<<"\n";return 1;}
 uint32_t x=0x12345678;
 for(int i=0;i<32;i++){
  x=x*1664525u+1013904223u;
  for(int j=0;j<80;j++){x=x*1664525u+1013904223u;data[j]=uint8_t(x>>24);}
  if(sha2<Binary>(data)!=sha2<Quat>(data)){std::cerr<<"FAIL randomized vector "<<i<<"\n";return 1;}
 }
 std::cout<<"HASH_CORRECTNESS PASS (1 known + 32 deterministic randomized)\n";
 double bt=bench<Binary>(data,n),qt=bench<Quat>(data,n);
 std::cout<<std::fixed<<std::setprecision(3);
 std::cout<<"BINARY_CPP seconds="<<bt<<" H/s="<<n/bt<<"\n";
 std::cout<<"NEXIS4_QUAT_CPP seconds="<<qt<<" H/s="<<n/qt<<"\n";
 std::cout<<"QUAT_TO_BINARY_TIME_RATIO="<<qt/bt<<"\n";
 std::cout<<"NOTE: C++ radix-4 symbol simulation, NOT physical four-voltage MOS performance.\n";
 return 0;
}

template<class T> static bool gated90(const std::array<uint8_t,80>&header,unsigned &rounds){
 Digest first=sha<T>(header.data(),header.size());
 uint8_t block[64]={0};
 std::copy(first.begin(),first.end(),block);block[32]=0x80;block[62]=1;
 U state[8];std::copy(IV,IV+8,state);
 return compress<T>(state,block,true,&rounds);
}
static bool target90(const Digest&d){
 return d[31]==0&&d[30]==0&&d[29]==0&&d[28]==0&&
 d[27]==0&&d[26]==0&&d[25]==0&&d[24]==0&&
 d[23]==0&&d[22]==0&&((d[21]&0xC0)==0);
}
template<class T> static void run56(const char*name,std::array<uint8_t,80> data,int n){
 unsigned long long rounds=0,pass=0;uint64_t checksum=0;
 auto start=std::chrono::steady_clock::now();
 for(int i=0;i<n;i++){
  data[76]=uint8_t(i);data[77]=uint8_t(i>>8);data[78]=uint8_t(i>>16);data[79]=uint8_t(i>>24);
  unsigned r=0;bool ok=gated90<T>(data,r);rounds+=r;pass+=ok;checksum+=r+(ok?1:0);
 }
 double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
 sink=sink+checksum;
 std::cout<<name<<"_GATED seconds="<<sec<<" H/s="<<n/sec<<" last_sha_rounds_per_candidate="<<double(rounds)/n<<" passed="<<pass<<"\n";
}
int main(int argc,char**argv){
 int n=argc>1?std::atoi(argv[1]):10000;
 if(n<100||n>1000000){std::cerr<<"iterations 100..1000000\n";return 2;}
 std::array<uint8_t,80> data{};for(int i=0;i<80;i++)data[i]=uint8_t(i);
 int matched=0;
 for(int i=0;i<1024;i++){
  data[76]=uint8_t(i);data[77]=uint8_t(i>>8);
  auto b=sha2<Binary>(data),q=sha2<Quat>(data);
  if(b!=q){std::cerr<<"HASH_MISMATCH "<<i<<"\n";return 1;}
  unsigned rb=0,rq=0;
  bool gb=gated90<Binary>(data,rb),gq=gated90<Quat>(data,rq);
  if(gb!=target90(b)||gq!=target90(q)||gb!=gq){
   std::cerr<<"GATE_MISMATCH "<<i<<" binary="<<gb<<" quat="<<gq<<" expected="<<target90(b)<<"\n";return 1;
  }
  matched++;
 }
 std::cout<<"M56_HASH_AND_GATE_CHECK PASS "<<matched<<"/"<<matched<<" (no positive 90-LZ witness in test)\n";
 std::cout<<std::fixed<<std::setprecision(3);
 run56<Binary>("BINARY",data,n);
 run56<Quat>("QUAT",data,n);
 std::cout<<"LIMITATIONS: 90-LZ only; never use gate to reject pool-difficulty shares. Full hash and pool target must be checked separately.\n";
 return 0;
}
