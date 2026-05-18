module tb;
    integer error_count;
    reg clk;
    reg [1:0] a;
    reg [3:0] b;
    reg sel;
    wire [3:0] out;

    a2_1_4_mux uut (
        .a(a),
        .b(b),
        .sel(sel),
        .out(out)
    );

    initial begin
        $dumpfile("temp/wave.vcd");
        $dumpvars(0, tb);
        clk = 0;
        a = 0;
        b = 0;
        sel = 0;
        error_count = 0;
        #10;
        // Test case 1: sel = 0
        sel = 0;
        a = 2'b11;
        b = 4'b1010;
        #10;
        @(posedge clk);
        @(posedge clk);
        if (out !== {a, 2'b00}) begin
            error_count++;
            $display("Error: out = %b, expected = %b", out, {a, 2'b00});
        end
        // Test case 2: sel = 1
        sel = 1;
        a = 2'b11;
        b = 4'b1010;
        #10;
        @(posedge clk);
        @(posedge clk);
        if (out !== b) begin
            error_count++;
            $display("Error: out = %b, expected = %b", out, b);
        end
        // Test case 3: sel = 0, a = 0
        sel = 0;
        a = 2'b00;
        b = 4'b1010;
        #10;
        @(posedge clk);
        @(posedge clk);
        if (out !== {a, 2'b00}) begin
            error_count++;
            $display("Error: out = %b, expected = %b", out, {a, 2'b00});
        end
        // Test case 4: sel = 1, b = 0
        sel = 1;
        a = 2'b11;
        b = 4'b0000;
        #10;
        @(posedge clk);
        @(posedge clk);
        if (out !== b) begin
            error_count++;
            $display("Error: out = %b, expected = %b", out, b);
        end
        if (error_count == 0) begin
            $display("FINAL_RESULT: PASS");
        end else begin
            $display("FINAL_RESULT: FAIL");
        end
        $finish;
    end

    always #5 clk = ~clk;
endmodule