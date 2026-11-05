// BABM staged exact target90 constraints, evaluated after header SHA.
// This is an actual early stop in second SHA (rounds 61/62/63), not a
// pre-header-hash filter. Never use the result as a score or full digest.
#pragma once
template<class T> static bool babm_target90_staged(const std::array<uint8_t,80>&header,unsigned&rounds){
 Digest first=sha<T>(header.data(),header.size());
 uint8_t block[64]={};
 std::copy(first.begin(),first.end(),block);
 block[32]=0x80;block[62]=1;
 U w[64];
 for(int i=0;i<16;i++)w[i]=(U(block[4*i])<<24)|(U(block[4*i+1])<<16)|(U(block[4*i+2])<<8)|block[4*i+3];
 for(int i=16;i<64;i++){
  U x=w[i-15],y=w[i-2];
  U s0=T::xr(T::xr(T::rr(x,7),T::rr(x,18)),T::sr(x,3));
  U s1=T::xr(T::xr(T::rr(y,17),T::rr(y,19)),T::sr(y,10));
  w[i]=plus4<T>(w[i-16],s0,w[i-7],s1);
 }
 U a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
 rounds=0;
 for(int i=0;i<63;i++){
  U s1=T::xr(T::xr(T::rr(e,6),T::rr(e,11)),T::rr(e,25));
  U ch=T::xr(T::an(e,f),T::an(T::nt(e),g));
  U t1=T::add(plus4<T>(h,s1,ch,K[i]),w[i]);
  U s0=T::xr(T::xr(T::rr(a,2),T::rr(a,13)),T::rr(a,22));
  U maj=T::xr(T::xr(T::an(a,b),T::an(a,c)),T::an(b,c));
  U t2=T::add(s0,maj);
  h=g;g=f;f=e;e=T::add(d,t1);d=c;c=b;b=a;a=T::add(t1,t2);
  ++rounds;
  if(i==60 && e!=0xA41F32E7u)return false;
  if(i==61 && e!=0xE07C2655u)return false;
  if(i==62 && ((e+IV[5])&0xC0FFFFFFu)!=0)return false;
 }
 return true;
}
