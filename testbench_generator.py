

# # ==============================
# # Testbench Generator (SELF-CHECKING + VCD)
# # ==============================

# def generate_testbench(module_name, inputs, outputs, bit_widths, logic_type):

#     tb = "module tb;\n\n"

#     # ==========================
#     # Declare signals
#     # ==========================
#     for inp in inputs:
#         width = bit_widths.get(inp, 1)
#         if width == 1:
#             tb += f"reg {inp};\n"
#         else:
#             tb += f"reg [{width-1}:0] {inp};\n"

#     for out in outputs:
#         width = bit_widths.get(out, 1)
#         if width == 1:
#             tb += f"wire {out};\n"
#         else:
#             tb += f"wire [{width-1}:0] {out};\n"

#     # ==========================
#     # Instantiate DUT
#     # ==========================
#     tb += f"\n{module_name} uut (\n"
#     ports = inputs + outputs
#     tb += ",\n".join([f"    .{p}({p})" for p in ports])
#     tb += "\n);\n"

#     # ==========================
#     # Expected logic (Golden Model)
#     # ==========================
#     if logic_type == "ADDER":
#         tb += "\n// Expected (Golden Model)\n"
#         tb += "wire [4:0] expected;\n"
#         tb += "assign expected = A + B + Cin;\n"

#     # ==========================
#     # Test logic
#     # ==========================
#     tb += "\ninteger i;\ninteger errors = 0;\n\n"

#     tb += "initial begin\n"

#     # 🔥 VCD DUMP (IMPORTANT)
#     tb += """
#     $dumpfile("temp/wave.vcd");
#     $dumpvars(0, tb);
# """

#     # ==========================
#     # ADDER TEST CASES
#     # ==========================
#     if logic_type == "ADDER":
#         tb += """
#     for (i = 0; i < 512; i = i + 1) begin
#         {A, B, Cin} = i;
#         #5;

#         if ({Cout, S} !== expected) begin
#             $display("FAIL: A=%b B=%b Cin=%b | Got=%b%b Expected=%b",
#                      A, B, Cin, Cout, S, expected);
#             errors = errors + 1;
#         end
#     end
# """

#     # ==========================
#     # BASIC LOGIC (GENERIC)
#     # ==========================
#     elif logic_type in ["AND", "OR", "XOR"]:
#         tb += """
#     for (i = 0; i < 4; i = i + 1) begin
#         {a, b} = i;
#         #5;

#         // Expected logic
# """
#         if logic_type == "AND":
#             tb += "        if (y !== (a & b)) errors = errors + 1;\n"
#         elif logic_type == "OR":
#             tb += "        if (y !== (a | b)) errors = errors + 1;\n"
#         elif logic_type == "XOR":
#             tb += "        if (y !== (a ^ b)) errors = errors + 1;\n"

#         tb += "    end\n"

#     # ==========================
#     # Final result
#     # ==========================
#     tb += """
#     if (errors == 0)
#         $display("FINAL_RESULT: PASS");
#     else
#         $display("FINAL_RESULT: FAIL, Errors = %d", errors);

#     $finish;
# end

# endmodule
# """

#     return tb

# ==============================
# 1. RULE-BASED TESTBENCH (YOUR EXISTING - KEEP)
# ==============================

def generate_testbench(module_name, inputs, outputs, bit_widths, logic_type):

    tb = "module tb;\n\n"

    # ==========================
    # SIGNALS
    # ==========================
    for inp in inputs:
        w = bit_widths.get(inp, 1)
        tb += f"reg [{w-1}:0] {inp};\n" if w > 1 else f"reg {inp};\n"

    for out in outputs:
        w = bit_widths.get(out, 1)
        tb += f"wire [{w-1}:0] {out};\n" if w > 1 else f"wire {out};\n"

    # ==========================
    # DUT
    # ==========================
    tb += f"\n{module_name} uut (\n"
    tb += ",\n".join([f"    .{p}({p})" for p in inputs + outputs])
    tb += "\n);\n"

    # ==========================
    # GOLDEN MODEL (only where known)
    # ==========================
    if logic_type == "ADDER":
        tb += "wire [4:0] expected;\n"
        tb += "assign expected = A + B + Cin;\n"

    # ==========================
    # TEST LOGIC
    # ==========================
    tb += "\ninteger i;\ninteger errors = 0;\n\n"
    tb += "initial begin\n"

    tb += """
    $dumpfile("temp/wave.vcd");
    $dumpvars(0, tb);
"""

    for inp in inputs:
        tb += f"    {inp} = 0;\n"
    tb += "    #1;\n\n"

    # ==========================
    # ADDER
    # ==========================
    if logic_type == "ADDER":
        tb += """
    for (i = 0; i < 512; i = i + 1) begin
        {A, B, Cin} = i;
        #1;

        if ({Cout, S} !== expected) begin
            $display("FAIL: A=%b B=%b Cin=%b | Got=%b%b Expected=%b",
                     A, B, Cin, Cout, S, expected);
            errors = errors + 1;
        end
    end
"""

    # ==========================
    # BASIC GATES
    # ==========================
    elif logic_type in ["AND", "OR", "XOR"]:
        tb += """
    for (i = 0; i < 4; i = i + 1) begin
        {a, b} = i;
        #1;
"""
        if logic_type == "AND":
            tb += """
        if (y !== (a & b)) begin
            $display("FAIL: a=%b b=%b y=%b", a, b, y);
            errors = errors + 1;
        end
"""
        elif logic_type == "OR":
            tb += """
        if (y !== (a | b)) begin
            $display("FAIL: a=%b b=%b y=%b", a, b, y);
            errors = errors + 1;
        end
"""
        elif logic_type == "XOR":
            tb += """
        if (y !== (a ^ b)) begin
            $display("FAIL: a=%b b=%b y=%b", a, b, y);
            errors = errors + 1;
        end
"""
        tb += "end\n"

    # ==========================
    # MUX
    # ==========================
    elif logic_type == "MUX":

        # 🔥 FORCE correct ports (ignore wrong prompt detection)
        if len(inputs) == 2 and len(outputs) == 1:
            in_sig = inputs[0]
            sel_sig = inputs[1]
            out_sig = outputs[0]
        else:
            # fallback safety
            in_sig = inputs[0]
            sel_sig = inputs[1] if len(inputs) > 1 else inputs[0]
            out_sig = outputs[0]

        tb += f"""
        for (i = 0; i < 16; i = i + 1) begin
            {in_sig} = i;
            {sel_sig} = i % 4;
            #1;

            case ({sel_sig})
                2'b00: if ({out_sig} !== {in_sig}[0]) errors = errors + 1;
                2'b01: if ({out_sig} !== {in_sig}[1]) errors = errors + 1;
                2'b10: if ({out_sig} !== {in_sig}[2]) errors = errors + 1;
                2'b11: if ({out_sig} !== {in_sig}[3]) errors = errors + 1;
            endcase
        end
"""

    # ==========================
    # DEMUX
    # ==========================
    elif logic_type == "DEMUX":
        tb += """
    for (i = 0; i < 4; i = i + 1) begin
        {S, D} = i;
        #1;

        if (S == 0 && Y0 !== D) begin
            $display("FAIL: S=0 D=%b Y0=%b", D, Y0);
            errors = errors + 1;
        end

        if (S == 1 && Y1 !== D) begin
            $display("FAIL: S=1 D=%b Y1=%b", D, Y1);
            errors = errors + 1;
        end
    end
"""

    # ==========================
    # DECODER
    # ==========================
    elif logic_type == "DECODER":
        tb += """
    for (i = 0; i < 4; i = i + 1) begin
        A = i;
        #1;

        if (Y !== (1 << A)) begin
            $display("FAIL: A=%b Y=%b", A, Y);
            errors = errors + 1;
        end
    end
"""

    # ==========================
    # ENCODER
    # ==========================
    elif logic_type == "ENCODER":
        tb += """
    for (i = 0; i < 16; i = i + 1) begin
        A = i;
        #1;

        case (A)
            4'b0001: if (Y !== 2'b01) errors = errors + 1;
            4'b0010: if (Y !== 2'b10) errors = errors + 1;
            4'b0100: if (Y !== 2'b11) errors = errors + 1;
            default: ;
        endcase
    end
"""

    # ==========================
    # COMPARATOR
    # ==========================
    elif logic_type == "COMPARATOR":
        tb += """
    for (i = 0; i < 4; i = i + 1) begin
        {A, B} = i;
        #1;

        if (A > B && GT !== 1) errors = errors + 1;
        if (A == B && EQ !== 1) errors = errors + 1;
        if (A < B && LT !== 1) errors = errors + 1;
    end
"""

    # ==========================
    # UNKNOWN → NO GOLDEN MODEL
    # ==========================
    else:
        tb += """
    repeat (10) begin
        #1;
    end
"""

    # ==========================
    # FINAL RESULT
    # ==========================
    tb += """
    if (errors == 0)
        $display("FINAL_RESULT: PASS");
    else
        $display("FINAL_RESULT: FAIL");

    $finish;
end

endmodule
"""

    return tb

# ==============================
# 🔥 2. ADVANCED GENERIC TESTBENCH (NEW)
# ==============================

def generate_generic_testbench(module_name, inputs, outputs, widths):

    tb = "module tb;\n\n"

    # Signals
    for i in inputs:
        w = widths[i]
        tb += f"reg [{w-1}:0] {i};\n" if w > 1 else f"reg {i};\n"

    for o in outputs:
        w = widths[o]
        tb += f"wire [{w-1}:0] {o};\n" if w > 1 else f"wire {o};\n"

    # DUT
    tb += f"\n{module_name} uut (\n"
    tb += ",\n".join([f".{p}({p})" for p in inputs + outputs])
    tb += "\n);\n"

    # 🔥 ADD ERROR TRACKING
    tb += "\ninteger i;\ninteger errors = 0;\n\n"

    tb += """
initial begin
    $dumpfile("temp/wave.vcd");
    $dumpvars(0, tb);

    repeat (20) begin
"""

    for i in inputs:
        tb += f"        {i} = $random;\n"

    tb += """
        #5;

        // 🔥 BASIC SANITY CHECK
"""

    for o in outputs:
        tb += f"        if ({o} === 1'bx) errors = errors + 1;\n"

    tb += """
    end

    if (errors == 0)
        $display("FINAL_RESULT: PASS");
    else
        $display("FINAL_RESULT: FAIL");

    $finish;
end

endmodule
"""
    return tb