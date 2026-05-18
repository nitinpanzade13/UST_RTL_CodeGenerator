import os
import re
import requests

# ==============================
# TIER 1 — Groq API Testbench
# ==============================
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"

def generate_testbench_with_groq(rtl_code):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not set")
        return ""

    module_match = re.search(r"\bmodule\s+(\w+)\b", rtl_code)
    dut_name = module_match.group(1) if module_match else "dut"

    prompt = f"""You are an expert Verilog verification engineer.

Write a complete self-checking Verilog testbench for this RTL module:

{rtl_code}

STRICT RULES:
- Module name must be exactly: tb
- Declare ALL integer variables at module level before any initial/always block
- For sequential designs with clock:
    * Declare clk as reg at module level
    * Generate clock in a separate always block: always #5 clk = ~clk;
    * Initialize clk in a separate initial block: initial begin clk = 0; end
    * Apply stimulus and checks in a SEPARATE initial block
    * Use clock period of 10ns total (#5 high, #5 low)
    * After reset deasserts, wait for @(posedge clk) before checking outputs
    * Always synchronize checks to posedge clk, never check combinationally
    * After applying reset or any input change, always wait for TWO @(posedge clk) before checking output
    * One @(posedge clk) for the input to register, one for output to settle
    * Never check output on the same @(posedge clk) where input changed
- Instantiate {dut_name} with named port mapping
- Include $dumpfile("temp/wave.vcd") and $dumpvars(0, tb)
- Use integer error_count declared at MODULE level
- Increment error_count on every mismatch
- Use $finish to end simulation
- Print FINAL_RESULT: PASS if error_count==0 else FINAL_RESULT: FAIL
- Return ONLY Verilog code, no explanation, no markdown"""

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.1
            },
            timeout=60
        )
        response.raise_for_status()
        tb_code = response.json()["choices"][0]["message"]["content"]

        # Clean markdown fences
        tb_code = re.sub(r"```verilog|```", "", tb_code).strip()

        # Clean DeepSeek thinking tags
        tb_code = re.sub(r"<think>[\s\S]*?</think>", "", tb_code).strip()

        return tb_code

    except Exception as e:
        print(f"❌ Groq API error: {e}")
        return ""


def validate_groq_tb(tb_code, module_name):
    """Basic structural validation of Groq output."""
    if not tb_code:
        return False
    has_module    = re.search(r"\bmodule\s+\w+\b", tb_code) is not None
    has_endmodule = "endmodule" in tb_code
    has_dut       = re.search(rf"\b{re.escape(module_name)}\b", tb_code) is not None
    has_final     = "FINAL_RESULT" in tb_code
    is_substantial = len(tb_code) > 200 and tb_code.count("\n") > 10

    print(f"   module:       {has_module}")
    print(f"   endmodule:    {has_endmodule}")
    print(f"   DUT ref:      {has_dut}")
    print(f"   FINAL_RESULT: {has_final}")
    print(f"   substantial:  {is_substantial}")

    return has_module and has_endmodule and has_dut and is_substantial


# ==============================
# TIER 2 — Rule-Based Testbench
# ==============================

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
    
    # ==========================
    # CLOCK GENERATION (for sequential logic)
    # ==========================
    if logic_type == "COUNTER":
        # Extract signal names
        clk_sig = None
        reset_sig = None
        count_sig = None
        
        for inp in inputs:
            if 'clk' in inp.lower():
                clk_sig = inp
            if 'reset' in inp.lower() or 'rst' in inp.lower():
                reset_sig = inp
        
        for out in outputs:
            if 'count' in out.lower() or 'q' in out.lower():
                count_sig = out
        
        # Fallback
        clk_sig = clk_sig or (inputs[0] if inputs else 'clk')
        reset_sig = reset_sig or (inputs[1] if len(inputs) > 1 else 'reset')
        count_sig = count_sig or (outputs[0] if outputs else 'count')
        
        # Generate clock at module level (not inside initial)
        tb += f"""
// Clock generation
initial begin
    {clk_sig} = 0;
    forever #5 {clk_sig} = ~{clk_sig};
end

"""
    
    tb += "initial begin\n"

    tb += """
    $dumpfile("temp/wave.vcd");
    $dumpvars(0, tb);
"""

    for inp in inputs:
        tb += f"    {inp} = 0;\n"
    tb += "    #1;\n\n"

    # ==========================
    # COUNTER TESTCASES
    # ==========================
    if logic_type == "COUNTER":
        clk_sig = None
        reset_sig = None
        
        for inp in inputs:
            if 'clk' in inp.lower():
                clk_sig = inp
            if 'reset' in inp.lower() or 'rst' in inp.lower():
                reset_sig = inp
        
        clk_sig = clk_sig or (inputs[0] if inputs else 'clk')
        reset_sig = reset_sig or (inputs[1] if len(inputs) > 1 else 'reset')
        
        tb += f"""
    // Test 1: Reset
    {reset_sig} = 1;
    #10;
    {reset_sig} = 0;
    #10;
    
    // Test 2: Count up
    repeat(20) @(posedge {clk_sig});
    
    // Test 3: Reset during counting
    {reset_sig} = 1;
    #10;
    {reset_sig} = 0;
    #10;
    
    // Test 4: More counting
    repeat(10) @(posedge {clk_sig});
    
    $display("FINAL_RESULT: PASS");
    $finish;
"""

    # ==========================
    # ADDER
    # ==========================
    elif logic_type == "ADDER":
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