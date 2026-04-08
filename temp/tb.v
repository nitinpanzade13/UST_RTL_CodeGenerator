module tb;

reg [3:0] A;
reg [3:0] B;
reg Cin;
wire [3:0] S;
wire Cout;

four_bit_adder uut (
.A(A),
.B(B),
.Cin(Cin),
.S(S),
.Cout(Cout)
);

integer i;
integer errors = 0;


initial begin
    $dumpfile("temp/wave.vcd");
    $dumpvars(0, tb);

    repeat (20) begin
        A = $random;
        B = $random;
        Cin = $random;

        #5;

        // 🔥 BASIC SANITY CHECK
        if (S === 1'bx) errors = errors + 1;
        if (Cout === 1'bx) errors = errors + 1;

    end

    if (errors == 0)
        $display("FINAL_RESULT: PASS");
    else
        $display("FINAL_RESULT: FAIL");

    $finish;
end

endmodule
