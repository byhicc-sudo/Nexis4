// Full SHA-256d combinational reference RTL for 80-byte Bitcoin headers.
// Header is packed in wire byte order, earliest byte at bits [639:632].
// Binary RTL baseline: not a physical quaternary implementation.
module nexis4_sha256_compress(
  input wire [255:0] initial_state,
  input wire [511:0] block,
  output reg [255:0] final_state
);
  reg [31:0] w [0:63];
  reg [31:0] a,b,c,d,e,f,g,h,t1,t2,s0,s1;
  reg [31:0] state [0:7];
  integer i;
  function [31:0] rotr;
    input [31:0] x;
    input integer n;
    begin rotr=(x>>n)|(x<<(32-n)); end
  endfunction
  function [31:0] constant_k;
    input integer idx;
    begin
      case(idx)
        0: constant_k=32'h428a2f98;
        1: constant_k=32'h71374491;
        2: constant_k=32'hb5c0fbcf;
        3: constant_k=32'he9b5dba5;
        4: constant_k=32'h3956c25b;
        5: constant_k=32'h59f111f1;
        6: constant_k=32'h923f82a4;
        7: constant_k=32'hab1c5ed5;
        8: constant_k=32'hd807aa98;
        9: constant_k=32'h12835b01;
        10: constant_k=32'h243185be;
        11: constant_k=32'h550c7dc3;
        12: constant_k=32'h72be5d74;
        13: constant_k=32'h80deb1fe;
        14: constant_k=32'h9bdc06a7;
        15: constant_k=32'hc19bf174;
        16: constant_k=32'he49b69c1;
        17: constant_k=32'hefbe4786;
        18: constant_k=32'h0fc19dc6;
        19: constant_k=32'h240ca1cc;
        20: constant_k=32'h2de92c6f;
        21: constant_k=32'h4a7484aa;
        22: constant_k=32'h5cb0a9dc;
        23: constant_k=32'h76f988da;
        24: constant_k=32'h983e5152;
        25: constant_k=32'ha831c66d;
        26: constant_k=32'hb00327c8;
        27: constant_k=32'hbf597fc7;
        28: constant_k=32'hc6e00bf3;
        29: constant_k=32'hd5a79147;
        30: constant_k=32'h06ca6351;
        31: constant_k=32'h14292967;
        32: constant_k=32'h27b70a85;
        33: constant_k=32'h2e1b2138;
        34: constant_k=32'h4d2c6dfc;
        35: constant_k=32'h53380d13;
        36: constant_k=32'h650a7354;
        37: constant_k=32'h766a0abb;
        38: constant_k=32'h81c2c92e;
        39: constant_k=32'h92722c85;
        40: constant_k=32'ha2bfe8a1;
        41: constant_k=32'ha81a664b;
        42: constant_k=32'hc24b8b70;
        43: constant_k=32'hc76c51a3;
        44: constant_k=32'hd192e819;
        45: constant_k=32'hd6990624;
        46: constant_k=32'hf40e3585;
        47: constant_k=32'h106aa070;
        48: constant_k=32'h19a4c116;
        49: constant_k=32'h1e376c08;
        50: constant_k=32'h2748774c;
        51: constant_k=32'h34b0bcb5;
        52: constant_k=32'h391c0cb3;
        53: constant_k=32'h4ed8aa4a;
        54: constant_k=32'h5b9cca4f;
        55: constant_k=32'h682e6ff3;
        56: constant_k=32'h748f82ee;
        57: constant_k=32'h78a5636f;
        58: constant_k=32'h84c87814;
        59: constant_k=32'h8cc70208;
        60: constant_k=32'h90befffa;
        61: constant_k=32'ha4506ceb;
        62: constant_k=32'hbef9a3f7;
        63: constant_k=32'hc67178f2;
        default: constant_k=32'h0;
      endcase
    end
  endfunction
  always @* begin
    for(i=0;i<8;i=i+1) state[i]=initial_state[255-32*i -:32];
    for(i=0;i<16;i=i+1) w[i]=block[511-32*i -:32];
    for(i=16;i<64;i=i+1) begin
      s0=rotr(w[i-15],7)^rotr(w[i-15],18)^(w[i-15]>>3);
      s1=rotr(w[i-2],17)^rotr(w[i-2],19)^(w[i-2]>>10);
      w[i]=w[i-16]+s0+w[i-7]+s1;
    end
    a=state[0];b=state[1];c=state[2];d=state[3];
    e=state[4];f=state[5];g=state[6];h=state[7];
    for(i=0;i<64;i=i+1) begin
      t1=h+(rotr(e,6)^rotr(e,11)^rotr(e,25))+((e&f)^((~e)&g))+constant_k(i)+w[i];
      t2=(rotr(a,2)^rotr(a,13)^rotr(a,22))+((a&b)^(a&c)^(b&c));
      h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
    end
    final_state={
      state[0]+a,state[1]+b,state[2]+c,state[3]+d,
      state[4]+e,state[5]+f,state[6]+g,state[7]+h
    };
  end
endmodule

module nexis4_sha256d80(
  input wire [639:0] header,
  output wire [255:0] digest
);
  localparam [255:0] IV=256'h6a09e667bb67ae853c6ef372a54ff53a510e527f9b05688c1f83d9ab5be0cd19;
  wire [255:0] first_state,first_digest;
  wire [511:0] block0=header[639:128];
  wire [511:0] block1={header[127:0],8'h80,312'b0,64'd640};
  nexis4_sha256_compress c0(IV,block0,first_state);
  nexis4_sha256_compress c1(first_state,block1,first_digest);
  nexis4_sha256_compress c2(IV,{first_digest,8'h80,184'b0,64'd256},digest);
endmodule
