`timescale 1ns/1ps
module tb;
 reg [1:0] a,b,op;
 reg cin;
 wire [1:0] y;
 wire cout;
 reg [31:0] x32,z32;
 wire [31:0] out32;
 integer i,j,k,errors;
 reg [2:0] expected;
 nexis4_digit_alu dut(.a(a),.b(b),.cin(cin),.op(op),.y(y),.cout(cout));
 nexis4_add32 adder(.a(x32),.b(z32),.y(out32));
 initial begin
   errors=0; a=0;b=0;cin=0;op=0;x32=0;z32=0;
   for(i=0;i<4;i=i+1) for(j=0;j<4;j=j+1) for(k=0;k<2;k=k+1) begin
     a=i;b=j;cin=k;op=0;expected=i+j+k;#1;
     if ({cout,y} !== expected) begin $display("FAIL ADD %d %d %d",i,j,k);errors=errors+1;end
     op=1;#1;if(y !== (a^b) || cout !== 0) errors=errors+1;
     op=2;#1;if(y !== (a&b) || cout !== 0) errors=errors+1;
     op=3;#1;if(y !== (~a) || cout !== 0) errors=errors+1;
   end
   for(i=0;i<10000;i=i+1) begin
     x32=$random;z32=$random;#1;
     if(out32 !== (x32+z32)) begin
       $display("FAIL ADD32 i=%0d x=%h z=%h got=%h",i,x32,z32,out32);
       errors=errors+1;
     end
   end
   if(errors==0) $display("PASS RTL: 128 digit op checks + 10000 32-bit adds");
   else $display("FAIL RTL errors=%0d",errors);
   if(errors!=0) $fatal(1,"RTL failed");
   $finish;
 end
endmodule
