`timescale 1ns/1ps
module tb_nexis4_exhaustive;
reg [1:0] a,b,op;
reg cin;
wire [1:0] y;
wire cout;
integer i,j,k,errors,checks;
reg [2:0] expected;
nexis4_digit_alu dut(.a(a),.b(b),.cin(cin),.op(op),.y(y),.cout(cout));
initial begin
 errors=0;checks=0;a=0;b=0;cin=0;op=0;
 for(i=0;i<4;i=i+1) for(j=0;j<4;j=j+1) for(k=0;k<2;k=k+1) begin
  a=i;b=j;cin=k;
  op=0;expected=i+j+k;#1;checks=checks+1;
  if({cout,y} !== expected) begin $display("FAIL ADD a=%0d b=%0d carry=%0d",i,j,k);errors=errors+1;end
  op=1;#1;checks=checks+1;
  if(y !== (a^b) || cout !== 0) begin $display("FAIL XOR");errors=errors+1;end
  op=2;#1;checks=checks+1;
  if(y !== (a&b) || cout !== 0) begin $display("FAIL AND");errors=errors+1;end
  op=3;#1;checks=checks+1;
  if(y !== (~a) || cout !== 0) begin $display("FAIL NOT");errors=errors+1;end
 end
 if(errors) $fatal(1,"exhaustive ALU mismatch");
 $display("PASS four-symbol RTL truth tables %0d/%0d",checks,checks);
 $display("LIMITATION: encoded binary RTL; NOT four-voltage transistor logic");
 $finish;
end
endmodule
