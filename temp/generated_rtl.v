module a2_1_4_mux(
    input [1:0] a,
    input [3:0] b,
    input sel,
    output reg [3:0] out
);

always @(*) begin
    if(sel == 1'b0) begin
        out = {a, 2'b00};
    end else begin
        out = b;
    end
end

endmodule