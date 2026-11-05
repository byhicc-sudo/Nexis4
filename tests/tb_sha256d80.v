`timescale 1ns/1ps
module tb_sha256d;
reg [639:0] header;
wire [255:0] digest;
integer i,errors;
reg [255:0] expected;
nexis4_sha256d80 dut(header,digest);
initial begin
 errors=0;
 // Bitcoin genesis header bytes in network-display order (actual wire order).
 header=640'h0100000000000000000000000000000000000000000000000000000000000000000000003ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a29ab5f49ffff001d1dac2b7c;
 // Raw digest byte order, reverse of conventional Bitcoin block hash display.
 expected=256'h6fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000;
 #10;
 if(digest !== expected) begin
   $display("FAIL genesis got=%h expected=%h",digest,expected); errors=errors+1;
 end else $display("PASS genesis SHA256d raw=%h",digest);
 header[31:0]=32'h1eac2b7c;
 expected=256'h1c1ba47149063b3bebadce0a323e51d097774b5d4c4187eaba0caa5d4a7a229b;
 #10;
 if(digest !== expected) begin
   $display("FAIL nonce+1 got=%h expected=%h",digest,expected); errors=errors+1;
 end else $display("PASS nonce+1 SHA256d raw=%h",digest);
 if(errors) $fatal(1,"SHA256d RTL mismatch");
 $display("PASS full SHA256d RTL 2/2; 3 compression blocks x 64 rounds");
 $finish;
end
endmodule
