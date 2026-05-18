"""
🧪 TEST SUITE: Demonstrate Tier-Based Testbench Generation
Tests various RTL designs to show how each tier handles different complexity levels
"""

import time
import json
import re
from dataset_matcher import DatasetMatcher, select_testbench_source

# Test cases representing different design complexities
TEST_CASES = [
    {
        "name": "Simple OR Gate (Combinational)",
        "prompt": "Design a 2-input OR gate",
        "rtl": """
        module or_gate(
            input a,
            input b,
            output y
        );
        assign y = a | b;
        endmodule
        """
    },
    {
        "name": "4-bit Counter (Sequential)",
        "prompt": "Design a 4-bit counter with reset and enable signals",
        "rtl": """
        module counter_4bit(
            input clk,
            input rst_n,
            input enable,
            output [3:0] count
        );
        
        reg [3:0] count_reg;
        
        always @(posedge clk) begin
            if (!rst_n)
                count_reg <= 0;
            else if (enable)
                count_reg <= count_reg + 1;
        end
        
        assign count = count_reg;
        endmodule
        """
    },
    {
        "name": "2:1 Multiplexer",
        "prompt": "Design a 2-to-1 multiplexer",
        "rtl": """
        module mux_2to1(
            input [1:0] in,
            input sel,
            output out
        );
        assign out = sel ? in[1] : in[0];
        endmodule
        """
    },
    {
        "name": "Accumulator (Complex Sequential)",
        "prompt": "Design an 8-bit accumulator with data_in and data_out",
        "rtl": """
        module accumulator(
            input clk,
            input rst,
            input [7:0] data_in,
            input valid_in,
            output [9:0] data_out,
            output valid_out
        );
        
        reg [9:0] acc_reg;
        
        always @(posedge clk) begin
            if (rst)
                acc_reg <= 0;
            else if (valid_in)
                acc_reg <= acc_reg + data_in;
        end
        
        assign data_out = acc_reg;
        assign valid_out = valid_in;
        endmodule
        """
    },
    {
        "name": "8-bit Comparator",
        "prompt": "Design an 8-bit equality comparator",
        "rtl": """
        module comparator_8bit(
            input [7:0] a,
            input [7:0] b,
            output equal,
            output greater,
            output less
        );
        
        assign equal = (a == b) ? 1'b1 : 1'b0;
        assign greater = (a > b) ? 1'b1 : 1'b0;
        assign less = (a < b) ? 1'b1 : 1'b0;
        endmodule
        """
    }
]


def analyze_testbench_source(prompt, rtl_code, matcher):
    """Analyze which tier would handle this design"""
    print(f"\n{'='*70}")
    print(f"📋 RTL Analysis")
    print(f"{'='*70}")
    
    # Analyze design characteristics
    has_sequential = bool(re.search(r"\balways\s*@\s*\(posedge", rtl_code))
    has_clk = bool(re.search(r"\b(clk|clock)\b", rtl_code))
    gate_count = len(re.findall(r"\b(and|or|xor|not|nand|nor|xnor)\b", rtl_code, re.I))
    assign_count = len(re.findall(r"\bassign\b", rtl_code))
    module_match = re.search(r"module\s+(\w+)\s*\((.*?)\)", rtl_code, re.DOTALL)
    
    if module_match:
        module_name = module_match.group(1)
        port_str = module_match.group(2)
        input_count = len(re.findall(r"\binput\b", port_str))
        output_count = len(re.findall(r"\boutput\b", port_str))
    else:
        module_name = "Unknown"
        input_count = output_count = 0
    
    design_type = "Sequential" if (has_sequential and has_clk) else "Combinational"
    complexity = "Simple" if gate_count + assign_count <= 5 else "Complex"
    
    print(f"\n🔍 Design Characteristics:")
    print(f"   Module: {module_name}")
    print(f"   Type: {design_type}")
    print(f"   Complexity: {complexity}")
    print(f"   Inputs: {input_count} | Outputs: {output_count}")
    print(f"   Gates: {gate_count} | Assignments: {assign_count}")
    
    # Get testbench source recommendation
    print(f"\n🎯 Testbench Source Analysis:")
    source, tb_code, metadata = select_testbench_source(prompt, rtl_code, matcher)
    
    if source:
        print(f"\n   ✅ Match Found!")
        print(f"   Source: {source}")
        print(f"   Problem ID: {metadata.get('problem_id')}")
        print(f"   Similarity: {metadata.get('similarity', 'N/A')}")
        print(f"   Quality: {metadata.get('quality', 'N/A')}")
        if 'source' in metadata:
            print(f"   Dataset: {metadata.get('source')}")
    else:
        print(f"\n   ❌ No dataset match")
        print(f"   Will use: TIER 3 (Generic Generation)")
        print(f"   Reason: {design_type} {complexity} design, no matching patterns in datasets")
    
    return {
        'design_type': design_type,
        'complexity': complexity,
        'testbench_source': source,
        'metadata': metadata
    }


def run_test_suite():
    """Run complete test suite"""
    print("\n" + "="*70)
    print("🧪 TIER-BASED TESTBENCH GENERATION TEST SUITE")
    print("="*70)
    
    matcher = DatasetMatcher()
    results = []
    
    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n\n{'#'*70}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'#'*70}")
        print(f"Prompt: {test['prompt']}")
        
        analysis = analyze_testbench_source(test['prompt'], test['rtl'], matcher)
        analysis['test_name'] = test['name']
        results.append(analysis)
    
    # Summary statistics
    print(f"\n\n{'='*70}")
    print("📊 TEST SUITE SUMMARY")
    print(f"{'='*70}")
    
    tier2a_matches = sum(1 for r in results if 'TIER_2A' in str(r.get('testbench_source')))
    tier2b_matches = sum(1 for r in results if 'TIER_2B' in str(r.get('testbench_source')))
    tier3_fallback = sum(1 for r in results if not r.get('testbench_source'))
    
    print(f"\n🎯 Testbench Source Breakdown:")
    print(f"   TIER 2A (Dataset Match): {tier2a_matches}/{len(results)}")
    print(f"   TIER 2B (VerilogEval): {tier2b_matches}/{len(results)}")
    print(f"   TIER 3 (Generic Fallback): {tier3_fallback}/{len(results)}")
    
    print(f"\n📈 Design Complexity Distribution:")
    combinational = sum(1 for r in results if r['design_type'] == 'Combinational')
    sequential = sum(1 for r in results if r['design_type'] == 'Sequential')
    print(f"   Combinational: {combinational}")
    print(f"   Sequential: {sequential}")
    
    simple = sum(1 for r in results if r['complexity'] == 'Simple')
    complex_designs = sum(1 for r in results if r['complexity'] == 'Complex')
    print(f"   Simple: {simple}")
    print(f"   Complex: {complex_designs}")
    
    # Recommendations
    print(f"\n💡 Insights & Recommendations:")
    print(f"""
   1. Dataset Coverage:
      - TIER 2A matches {tier2a_matches} out of {len(results)} designs ({tier2a_matches/len(results)*100:.0f}%)
      - TIER 2B is effective for combinational designs
      
   2. Tier Performance:
      - Sequential designs (clk-based) → Better with TIER 2A
      - Combinational designs → Can match TIER 2B or TIER 2A
      - Novel designs → Fall back to TIER 3
      
   3. Quality Expectations:
      - TIER 2A: High quality (tested), ~{tier2a_matches/len(results)*100:.0f}% coverage
      - TIER 2B: Good quality (reference), ~{tier2b_matches/len(results)*100:.0f}% coverage
      - TIER 3: Basic quality, {tier3_fallback/len(results)*100:.0f}% fallback rate
      
   4. Pipeline Optimization:
      - Current dataset has {matcher.tier2a_samples.__len__()} TIER 2A samples
      - Consider adding more sequential/complex designs to improve coverage
      - TIER 2B works best for designs with ≤5 simple gates
    """)
    
    # Save results
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to test_results.json")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    run_test_suite()
