#pragma once
// BABM R199/R200 runtime witness: exact second-SHA schedule and 64-round inversion.
// Requires m56_gate_benchmark.cpp primitives (U, Binary, K, IV, Digest, sha).
// This is a correctness witness, NOT a pre-hash nonce filter.
static bool babm_live_witness(const std::array<uint8_t,80>& header, const Digest& expected) {
 const Digest first=sha<Binary>(header.data(),header.size());
 uint8_t block[64]={};std::copy(first.begin(),first.end(),block);
 block[32]=0x80;block[62]=1;
 U w[64]{};
 for(int i=0;i<16;i++)w[i]=(U(block[4*i])<<24)|(U(block[4*i+1])<<16)|(U(block[4*i+2])<<8)|U(block[4*i+3]);
 for(int i=16;i<64;i++){
  U x=w[i-15],y=w[i-2];
  U s0=Binary::rr(x,7)^Binary::rr(x,18)^Binary::sr(x,3);
  U s1=Binary::rr(y,17)^Binary::rr(y,19)^Binary::sr(y,10);
  w[i]=w[i-16]+s0+w[i-7]+s1;
 }
 U a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
 for(int i=0;i<64;i++){
  U s1=Binary::rr(e,6)^Binary::rr(e,11)^Binary::rr(e,25);
  U ch=(e&f)^((~e)&g);
  U t1=h+s1+ch+K[i]+w[i];
  U s0=Binary::rr(a,2)^Binary::rr(a,13)^Binary::rr(a,22);
  U maj=(a&b)^(a&c)^(b&c);
  U t2=s0+maj;
  h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
 }
 U final_state[8]={a,b,c,d,e,f,g,h};
 for(int i=0;i<8;i++){
  U v=final_state[i]+IV[i];
  for(int j=0;j<4;j++)if(uint8_t(v>>(24-8*j))!=expected[4*i+j])return false;
 }
 for(int i=63;i>=0;i--){
  U pa=b,pb=c,pc=d,pe=f,pf=g,pg=h;
  U s0=Binary::rr(pa,2)^Binary::rr(pa,13)^Binary::rr(pa,22);
  U maj=(pa&pb)^(pa&pc)^(pb&pc);
  U t2=s0+maj;
  U t1=a-t2;
  U pd=e-t1;
  U s1=Binary::rr(pe,6)^Binary::rr(pe,11)^Binary::rr(pe,25);
  U ch=(pe&pf)^((~pe)&pg);
  U ph=t1-s1-ch-K[i]-w[i];
  a=pa;b=pb;c=pc;d=pd;e=pe;f=pf;g=pg;h=ph;
 }
 return a==IV[0]&&b==IV[1]&&c==IV[2]&&d==IV[3]&&e==IV[4]&&f==IV[5]&&g==IV[6]&&h==IV[7];
}
