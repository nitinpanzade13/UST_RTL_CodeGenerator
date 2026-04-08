module four_bit_adder (
    input [3:0] A,
    input [3:0] B,
    input Cin,
    output [3:0] S,
    output Cout
);

    wire [3:0] sum;
    wire [3:0] carry;

    assign sum = A + B + Cin;
    assign Cout = carry[3];

    assign carry[0] = (A[0] & B[0]) | (A[0] & Cin) | (B[0] & Cin);
    assign carry[1] = (A[1] & B[1]) | (A[1] & carry[0]) | (B[1] & carry[0]);
    assign carry[2] = (A[2] & B[2]) | (A[2] & carry[1]) | (B[2] & carry[1]);
    assign carry[3] = (A[3] & B[3]) | (A[3] & carry[2]) | (B[3] & carry[2]);

    assign S = sum;

endmodule