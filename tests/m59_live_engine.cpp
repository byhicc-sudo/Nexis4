// M60 integrated live engine: NEXIS4 radix-4, exact round-3 audit,
// exact 90-LZ final SHA gate, single-pass digest, independent Python audit.
// Unproven BABM/GF(2) candidate filters are NOT enabled.
#define main m56_embedded_main
#include "m56_gate_benchmark.cpp"
#undef main
#include <sstream>
static int lz60(const Digest&d){int n=0;for(int i=31;i>=0;--i){if(!d[i])n+=8;else {for(int j=7;j>=0;--j){if(d[i]&(1u<<j))return n;++n;}}}return n;}
static int digit60(char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;if(c>='A'&&c<='F')return c-'A'+10;return -1;}
template<class T> static bool round3_audit(const std::array<uint8_t,80>& header){
 U mid[8];std::copy(IV,IV+8,mid);compress<T>(mid,header.data());
 U a=mid[0],b=mid[1],c=mid[2],d=mid[3],e=mid[4],f=mid[5],g=mid[6],h=mid[7];
 for(int t=0;t<4;t++){
  U w=(U(header[64+4*t])<<24)|(U(header[65+4*t])<<16)|(U(header[66+4*t])<<8)|header[67+4*t];
  U s1=T::xr(T::xr(T::rr(e,6),T::rr(e,11)),T::rr(e,25));
  U ch=T::xr(T::an(e,f),T::an(T::nt(e),g));
  U base=plus4<T>(h,s1,ch,K[t]);
  U s0=T::xr(T::xr(T::rr(a,2),T::rr(a,13)),T::rr(a,22));
  U maj=T::xr(T::xr(T::an(a,b),T::an(a,c)),T::an(b,c));
  U t2=T::add(s0,maj);
  U merge=T::add(base,w),na=T::add(merge,t2),ne=T::add(d,merge);
  if(t==3 && (T::add(merge,~base+1u)!=w || T::add(na,~t2+1u)!=merge ||
      T::add(ne,~d+1u)!=merge || T::add(na,~ne+1u)!=T::add(t2,~d+1u)))return false;
  U t1=merge;h=g;g=f;f=e;e=ne;d=c;c=b;b=a;a=na;
 }
 return true;
}
template<class T> static Digest integrated_hash(const std::array<uint8_t,80>&header,bool&gate_pass,unsigned&rounds){
 Digest first=sha<T>(header.data(),header.size());
 uint8_t block[64]={0};std::copy(first.begin(),first.end(),block);
 block[32]=0x80;block[62]=1; // 32-byte second SHA = 256 bits
 U state[8];std::copy(IV,IV+8,state);
 U w[64];
 for(int i=0;i<16;i++)w[i]=(U(block[4*i])<<24)|(U(block[4*i+1])<<16)|(U(block[4*i+2])<<8)|block[4*i+3];
 for(int i=16;i<64;i++){
  U x=w[i-15],y=w[i-2];
  U s0=T::xr(T::xr(T::rr(x,7),T::rr(x,18)),T::sr(x,3));
  U s1=T::xr(T::xr(T::rr(y,17),T::rr(y,19)),T::sr(y,10));
  w[i]=plus4<T>(w[i-16],s0,w[i-7],s1);
 }
 U a=state[0],b=state[1],c=state[2],d=state[3],e=state[4],f=state[5],g=state[6],h=state[7];
 gate_pass=true;rounds=0;
 for(int i=0;i<64;i++){
  U s1=T::xr(T::xr(T::rr(e,6),T::rr(e,11)),T::rr(e,25));
  U ch=T::xr(T::an(e,f),T::an(T::nt(e),g));
  U t1=T::add(plus4<T>(h,s1,ch,K[i]),w[i]);
  U s0=T::xr(T::xr(T::rr(a,2),T::rr(a,13)),T::rr(a,22));
  U maj=T::xr(T::xr(T::an(a,b),T::an(a,c)),T::an(b,c));
  U t2=T::add(s0,maj);
  h=g;g=f;f=e;e=T::add(d,t1);d=c;c=b;b=a;a=T::add(t1,t2);
  ++rounds;
  if((i==60 && e!=0xA41F32E7u)||(i==61 && e!=0xE07C2655u)||
     (i==62 && ((e+IV[5])&0xC0FFFFFFu)!=0))gate_pass=false;
 }
 U v[8]={a,b,c,d,e,f,g,h};
 for(int i=0;i<8;i++)state[i]=T::add(state[i],v[i]);
 Digest out{};for(int i=0;i<8;i++)for(int j=0;j<4;j++)out[4*i+j]=uint8_t(state[i]>>(24-8*j));
 return out;
}
int main(){
 std::cout<<"M59_READY M60_INTEGRATED_QUAT_SHA256D ROUND3_AUDIT GATE90 SINGLE_PASS\n"<<std::flush;
 std::string line;uint64_t checked=0;
 while(std::getline(std::cin,line)){
  if(line=="QUIT")break;
  std::istringstream in(line);std::string h;uint64_t start=0,count=0;in>>h>>start>>count;
  if(h.size()!=152||start>0xffffffffULL||count==0||count>8192||start+count>0x100000000ULL){std::cout<<"ERROR bad_request\n"<<std::flush;continue;}
  std::array<uint8_t,80> data{};bool good=true;
  for(int i=0;i<76;i++){int a=digit60(h[2*i]),b=digit60(h[2*i+1]);if(a<0||b<0){good=false;break;}data[i]=uint8_t((a<<4)|b);}
  if(!good){std::cout<<"ERROR hex\n"<<std::flush;continue;}
  int best=-1;uint64_t best_nonce=0;Digest best_digest{};unsigned long long total_rounds=0;unsigned gate_pass=0;
  for(uint64_t j=0;j<count;j++){
   uint32_t nonce=uint32_t(start+j);
   for(int k=0;k<4;k++)data[76+k]=uint8_t(nonce>>(8*k));
   if(j==0 && (!round3_audit<Quat>(data)||!round3_audit<Binary>(data))){std::cout<<"ERROR round3_audit\n"<<std::flush;return 1;}
   bool pass=false;unsigned rounds=0;Digest d=integrated_hash<Quat>(data,pass,rounds);
   total_rounds+=rounds;gate_pass+=pass;int score=lz60(d);
   if(pass!=target90(d)){std::cout<<"ERROR gate_mismatch nonce="<<nonce<<"\n"<<std::flush;return 1;}
   if(score>best){best=score;best_nonce=nonce;best_digest=d;}
   if(score>45)std::cout<<"HIT "<<score<<" "<<nonce<<" "<<hex(d)<<"\n";
  }
  checked+=count;
  std::cout<<"BATCH "<<count<<" "<<best<<" "<<best_nonce<<" "<<hex(best_digest)<<" "<<gate_pass<<" "<<total_rounds<<" "<<checked<<"\n"<<std::flush;
 }
}
