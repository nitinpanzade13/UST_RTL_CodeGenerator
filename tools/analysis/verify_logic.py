#!/usr/bin/env python3
"""Verify skip_tier2 logic for MUX designs."""

import re

# Test the skip_tier2 condition
prompts_to_test = [
    ("design a 4:1 multiplexer", True),  # Should skip TIER 2
    ("design a 4 to 1 multiplexer", True),  # Should skip TIER 2
    ("design a 4-to-1 mux", True),  # Should skip TIER 2
    ("design a 2:1 multiplexer", False),  # Should NOT skip
    ("design a 8:1 mux", False),  # Should NOT skip (only 4:1 is special)
    ("design an adder", False),  # Should NOT skip
]

print("=" * 80)
print("Testing skip_tier2 logic for MUX patterns")
print("=" * 80)

for prompt, should_skip in prompts_to_test:
    skip_tier2 = ("4:1" in prompt or "4 to 1" in prompt or "4-to-1" in prompt) and ("mux" in prompt.lower() or "multiplexer" in prompt.lower())
    
    status = "✅ CORRECT" if skip_tier2 == should_skip else "❌ WRONG"
    print(f"\n{status}")
    print(f"  Prompt: {prompt}")
    print(f"  Skip TIER 2: {skip_tier2} (expected: {should_skip})")

print("\n" + "=" * 80)

# Test SystemVerilog detection
print("\nTesting SystemVerilog detection:")
print("=" * 80)

test_codes = [
    ("""
module tb();
    wire clk;
    reg [7:0] a;
    reg [7:0] b;
    initial begin
        a = 8'h0;
        b = 8'h0;
    end
endmodule
    """, False, "Pure Verilog"),
    
    ("""
module tb();
    logic [7:0] a;
    bit b;
endmodule
    """, True, "SystemVerilog - logic/bit keywords"),
    
    ("""
module tb();
    typedef struct {
        int errors;
    } stats;
endmodule
    """, True, "SystemVerilog - typedef/int"),
    
    ("""
module tb();
    initial begin
        always_ff @(posedge clk) begin
        end
    end
endmodule
    """, True, "SystemVerilog - always_ff"),
]

systemverilog_keywords = [
    'typedef', 'logic', 'bit', 'int ', 'real ', 'genvar', 'always_ff',
    'always_comb', 'always_latch', 'interface', 'modport', 'clocking',
    'constraint', 'randomize', '::', 'import', 'package', 'automatic'
]

systemverilog_patterns = [
    r'@\(\s*\*\s*\)',  # @(*)
    r'\.\*',  # .*
    r'task\s+\w+\s*\([^)]*=',  # task with default args
    r'function\s+\w+\s*\([^)]*=',  # function with default args
    r'parameter\s+\w+\s*=\s*\d+\s*\'',  # parameter with size
]

for code, should_be_sv, description in test_codes:
    code_lower = code.lower()
    
    # Check keywords
    has_sv_keyword = any(keyword in code_lower for keyword in systemverilog_keywords)
    
    # Check patterns
    has_sv_pattern = any(re.search(pattern, code, re.IGNORECASE) for pattern in systemverilog_patterns)
    
    is_sv = has_sv_keyword or has_sv_pattern
    
    status = "✅ CORRECT" if is_sv == should_be_sv else "❌ WRONG"
    print(f"\n{status}")
    print(f"  Description: {description}")
    print(f"  Is SystemVerilog: {is_sv} (expected: {should_be_sv})")

print("\n" + "=" * 80)
