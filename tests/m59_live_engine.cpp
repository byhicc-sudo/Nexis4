// M59: live-job NEXIS4 radix-4 processor + exact 90-LZ gate; independent Python audit.
#define main m56_embedded_main
#include "m56_gate_benchmark.cpp"
#undef main
#include <sstream>
static int lz59(const Digest&d){int n=0;for(int i=31;i>=0;--i){if(!d[i])n+=8;else {for(int j=7;j>=0;--j){if(d[i]&(1u<<j))return n;++n;}}}return n;}
static int digit(char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;if(c>='A'&&c<='F')return c-'A'+10;return -1;}
int main(){
 std::cout<<"M59_READY QUAT_SHA256D GATE90 FULL_HASH\n"<<std::flush;
 std::string line;uint64_t checked=0;
 while(std::getline(std::cin,line)){
  if(line=="QUIT")break;
  std::istringstream in(line);std::string h;uint64_t start=0,count=0;in>>h>>start>>count;
  if(h.size()!=152||start>0xffffffffULL||count==0||count>8192||start+count>0x100000000ULL){std::cout<<"ERROR bad_request\n"<<std::flush;continue;}
  std::array<uint8_t,80> data{};
  bool good=true;for(int i=0;i<76;i++){int a=digit(h[2*i]),b=digit(h[2*i+1]);if(a<0||b<0){good=false;break;}data[i]=uint8_t((a<<4)|b);}
  if(!good){std::cout<<"ERROR hex\n"<<std::flush;continue;}
  int best=-1;uint64_t best_nonce=0;Digest best_digest{};unsigned long long total_rounds=0;unsigned gate_pass=0;
  for(uint64_t j=0;j<count;j++){
   uint32_t nonce=uint32_t(start+j);
   for(int k=0;k<4;k++)data[76+k]=uint8_t(nonce>>(8*k));
   unsigned rounds=0;bool pass=gated90<Quat>(data,rounds);total_rounds+=rounds;gate_pass+=pass;
   Digest d=sha2<Quat>(data);int score=lz59(d);
   if(pass!=target90(d)){std::cout<<"ERROR gate_mismatch nonce="<<nonce<<"\n"<<std::flush;return 1;}
   if(score>best){best=score;best_nonce=nonce;best_digest=d;}
   if(score>45)std::cout<<"HIT "<<score<<" "<<nonce<<" "<<hex(d)<<"\n";
  }
  checked+=count;
  std::cout<<"BATCH "<<count<<" "<<best<<" "<<best_nonce<<" "<<hex(best_digest)<<" "<<gate_pass<<" "<<total_rounds<<" "<<checked<<"\n"<<std::flush;
 }
}
