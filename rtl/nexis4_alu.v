// NEXIS-4: two-bit quaternary digit ALU. Binary carry in/out.
// Synthesizable LOGIC only; no multi-voltage physical implementation.
module nexis4_digit_alu(
 input wire [1:0] a,b,
 input wire cin,
 input wire [1:0] op, // 0=ADD, 1=XOR, 2=AND, 3=NOT_A
 output reg [1:0] y,
 output reg cout
);
 reg [2:0] sum;
 always @* begin
   sum={1'b0,a}+{1'b0,b}+cin;
   cout=1'b0;
   case(op)
     2'd0: begin y=sum[1:0]; cout=sum[2]; end
     2'd1: y=a^b;
     2'd2: y=a&b;
     default: y=~a;
   endcase
 end
endmodule

module nexis4_add32(input wire [31:0] a,b,output wire [31:0] y);
 wire [16:0] carry;
 assign carry[0]=1'b0;
 genvar i;
 generate for(i=0;i<16;i=i+1) begin:digits
   nexis4_digit_alu digit(.a(a[2*i+:2]),.b(b[2*i+:2]),
     .cin(carry[i]),.op(2'd0),.y(y[2*i+:2]),.cout(carry[i+1]));
 end endgenerate
endmodule
