"""
🔥 DATASET-BASED TESTBENCH MATCHER
Efficient tier-based testbench generation using pre-tested datasets
"""

import json
import re
import os
from difflib import SequenceMatcher
from pathlib import Path


class DatasetMatcher:
    """Matches generated RTL against dataset samples for testbench reuse"""
    
    def __init__(self):
        self.tier2a_samples = []  # final_rtl_tb_dataset.jsonl
        self.tier2b_path = None   # verilog-eval path
        self._load_datasets()
    
    def _load_datasets(self):
        """Load datasets once during initialization"""
        # Load TIER 2A (final_rtl_tb_dataset.jsonl)
        dataset_path = "datasets/final_rtl_tb_dataset.jsonl"
        if os.path.exists(dataset_path):
            with open(dataset_path, 'r', encoding='utf-8') as f:
                self.tier2a_samples = [json.loads(line) for line in f]
            print(f"✓ Loaded TIER 2A: {len(self.tier2a_samples)} samples")
        
        # Set TIER 2B path
        self.tier2b_path = "datasets/verilog-eval/dataset_code-complete-iccad2023"
        if os.path.exists(self.tier2b_path):
            problems = set()
            for file in os.listdir(self.tier2b_path):
                if file.endswith("_ref.sv"):
                    problems.add(file.replace("_ref.sv", ""))
            print(f"✓ Located TIER 2B: {len(problems)} problems")
    
    # ============================================================
    # SYSTEMVERILOG COMPATIBILITY CHECK
    # ============================================================
    
    def _is_verilog_compatible(self, testbench_code):
        """
        Check if testbench uses only Verilog (not SystemVerilog).
        Returns True if compatible, False if has SystemVerilog-only features.
        
        STRICT MODE: Rejects anything that looks remotely like SystemVerilog
        """
        if not testbench_code:
            return False
        
        # Normalize for easier matching
        code_lower = testbench_code.lower()
        
        # SystemVerilog-only features that will fail in Icarus Verilog
        # STRICT PATTERNS - any match = not compatible
        systemverilog_keywords = [
            'typedef',           # typedef struct, typedef enum
            'logic',             # logic type
            'bit',               # bit type (even bit alone)
            'int ',              # int type (space after to avoid "print")
            'real ',             # real type
            'genvar',            # generate variables
            'always_ff',         # always_ff block
            'always_comb',       # always_comb block
            'always_latch',      # always_latch block
            'interface',         # interface blocks
            'modport',           # modport declarations
            'clocking',          # clocking blocks
            'constraint',        # constraint declarations
            'randomize',         # randomize function
            '::',                # scope resolution
            'import',            # import statements
            'package',           # package declarations
            'automatic',         # automatic keyword (SystemVerilog)
        ]
        
        for keyword in systemverilog_keywords:
            if keyword in code_lower:
                return False
        
        # Regex patterns for more complex SystemVerilog features
        systemverilog_patterns = [
            r'@\s*\(\s*\*\s*\)',         # @(*) sensitivity (not @(*))
            r'\.{1,}\s*[,)]',            # .* port connections
            r'\$display\s*\([^)]*\'[A-Za-z]',  # $display with format specifiers
            r'task\s+\w+\s*\([^)]*=',    # task with default arguments
            r'function\s+\w+.*=',        # function with default args
            r'typedef\s+struct',         # typedef struct (double check)
            r'input\s+\[\s*\d+:\d+\s*\]\s+\w+\s*=', # input with defaults
            r'\w+\s+#\s*\(',             # parameter instantiation (might be SV)
        ]
        
        for pattern in systemverilog_patterns:
            if re.search(pattern, testbench_code, re.IGNORECASE):
                return False
        
        return True
    
    # ============================================================
    # TIER 2A: FINAL_RTL_TB_DATASET MATCHING
    # ============================================================
    
    def _extract_ports_from_rtl(self, rtl_code):
        """Extract module name and port info from RTL"""
        module_match = re.search(r"module\s+(\w+)\s*\((.*?)\)", rtl_code, re.DOTALL)
        if not module_match:
            return None, None, None
        
        module_name = module_match.group(1)
        port_str = module_match.group(2)
        
        # Count inputs and outputs
        input_count = len(re.findall(r"\binput\b", port_str))
        output_count = len(re.findall(r"\boutput\b", port_str))
        
        return module_name, input_count, output_count
    
    def _text_similarity(self, text1, text2):
        """Calculate similarity between two text strings (0-1)"""
        if not text1 or not text2:
            return 0
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _rtl_similarity(self, rtl1, rtl2):
        """Calculate RTL code similarity based on structure"""
        # Extract line counts and module structure
        lines1 = len(rtl1.split('\n'))
        lines2 = len(rtl2.split('\n'))
        
        # Extract keywords
        always_blocks1 = len(re.findall(r"\balways\b", rtl1))
        always_blocks2 = len(re.findall(r"\balways\b", rtl2))
        
        assigns1 = len(re.findall(r"\bassign\b", rtl1))
        assigns2 = len(re.findall(r"\bassign\b", rtl2))
        
        # Simple heuristic: structural similarity
        diff_lines = abs(lines1 - lines2) / max(lines1, lines2, 1)
        diff_always = abs(always_blocks1 - always_blocks2)
        diff_assign = abs(assigns1 - assigns2)
        
        # Score: lower differences = higher similarity
        structural_score = 1.0 - (diff_lines * 0.3 + diff_always * 0.2 + diff_assign * 0.2)
        return max(0, structural_score)
    
    def find_tier2a_match(self, prompt, rtl_code, threshold=0.6):
        """
        Find best matching testbench from final_rtl_tb_dataset.jsonl
        
        Returns: (sample, similarity_score) or (None, 0)
        """
        if not self.tier2a_samples:
            return None, 0
        
        best_match = None
        best_score = 0
        
        module_name, input_count, output_count = self._extract_ports_from_rtl(rtl_code)
        
        for sample in self.tier2a_samples:
            # Multi-factor scoring
            scores = []
            
            # 1. Specification/Prompt similarity
            spec = sample.get('specification', '')
            spec_sim = self._text_similarity(prompt, spec)
            scores.append(('spec', spec_sim, 0.4))
            
            # 2. RTL structure similarity
            sample_rtl = sample.get('rtl_code', '')
            rtl_sim = self._rtl_similarity(rtl_code, sample_rtl)
            scores.append(('rtl', rtl_sim, 0.3))
            
            # 3. Port count matching
            sample_module, sample_inputs, sample_outputs = self._extract_ports_from_rtl(sample_rtl)
            port_match = (
                1.0 if (input_count == sample_inputs and output_count == sample_outputs)
                else 0.3
            )
            scores.append(('ports', port_match, 0.3))
            
            # 🔥 4. VERILOG COMPATIBILITY CHECK
            # Skip testbenches with SystemVerilog syntax
            testbench_code = sample.get('testbench', '')
            if not self._is_verilog_compatible(testbench_code):
                # Penalize SystemVerilog testbenches heavily
                total_score = 0  # Skip this match entirely
            else:
                # Weighted average
                total_score = sum(score * weight for _, score, weight in scores)
            
            if total_score > best_score:
                best_score = total_score
                best_match = sample
        
        if best_score >= threshold:
            return best_match, best_score
        return None, best_score
    
    # ============================================================
    # TIER 2B: VERILOG-EVAL MATCHING
    # ============================================================
    
    def _is_combinational(self, rtl_code):
        """Heuristic: check if RTL is combinational (no sequential blocks)"""
        has_always = bool(re.search(r"\balways\s*@\s*\(", rtl_code))
        has_clk = bool(re.search(r"\b(clk|clock|clk_in)\b", rtl_code))
        return not (has_always and has_clk)
    
    def _count_gates(self, rtl_code):
        """Count logic gates for complexity estimation"""
        gates = len(re.findall(r"\b(and|or|xor|not|nand|nor|xnor)\b", rtl_code, re.I))
        assigns = len(re.findall(r"\bassign\b", rtl_code))
        return gates + assigns
    
    def find_tier2b_match(self, rtl_code):
        """
        Find best matching testbench from verilog-eval dataset
        Uses heuristic-based matching for simple designs
        
        Returns: (problem_id, testbench_code) or (None, None)
        """
        if not os.path.exists(self.tier2b_path):
            return None, None
        
        # Strategy: prefer combinational, simple designs from verilog-eval
        is_combinational = self._is_combinational(rtl_code)
        gate_count = self._count_gates(rtl_code)
        
        # If design is sequential or complex, verilog-eval is less likely to match
        if not is_combinational or gate_count > 20:
            return None, None
        
        # List all problems
        problems = []
        for file in os.listdir(self.tier2b_path):
            if file.endswith("_ref.sv"):
                problem_id = file.replace("_ref.sv", "")
                problems.append(problem_id)
        
        # Select first available (or implement more sophisticated matching)
        if problems:
            problem_id = problems[0]  # Simple heuristic - can be improved
            test_path = os.path.join(self.tier2b_path, f"{problem_id}_test.sv")
            
            if os.path.exists(test_path):
                with open(test_path, 'r', encoding='utf-8') as f:
                    tb_code = f.read()
                return problem_id, tb_code
        
        return None, None
    
    # ============================================================
    # EXTRACTION & ADAPTATION
    # ============================================================
    
    def adapt_testbench_to_module(self, testbench_code, new_module_name, 
                                   generated_inputs=None, generated_outputs=None):
        """
        Adapt an existing testbench to work with new RTL module
        
        This replaces module names and port connections intelligently
        """
        adapted = testbench_code
        
        # Find existing module instantiation patterns
        # Replace old module names with new one
        module_patterns = [
            (r'\b(\w+)\s+uut\s*\(', f'{new_module_name} uut ('),
            (r'\b(\w+)\s+dut\s*\(', f'{new_module_name} dut ('),
            (r'\b(\w+)\s+top_module\s*\(', f'{new_module_name} top_module ('),
        ]
        
        for pattern, replacement in module_patterns:
            adapted = re.sub(pattern, replacement, adapted)
        
        return adapted.strip()
    
    def extract_testbench_from_sample(self, sample):
        """Extract and validate testbench code from dataset sample"""
        tb_code = sample.get('testbench_code', '')
        
        if not tb_code:
            return None
        
        # Validate: must have module, endmodule, and test logic
        has_module = bool(re.search(r"\bmodule\s+\w+", tb_code))
        has_endmodule = "endmodule" in tb_code
        has_dumpvars = "$dumpvars" in tb_code
        
        if has_module and has_endmodule:
            return tb_code
        
        return None
    
    def get_testbench_quality_score(self, testbench_code):
        """Score testbench quality (0-1)"""
        score = 0.0
        
        # Has self-checking logic
        if "FINAL_RESULT" in testbench_code or "$display" in testbench_code:
            score += 0.3
        
        # Has waveform capture
        if "$dumpvars" in testbench_code and "$dumpfile" in testbench_code:
            score += 0.2
        
        # Has clock generation
        if "#" in testbench_code or "forever" in testbench_code:
            score += 0.2
        
        # Has proper module structure
        if re.search(r"module\s+\w+.*endmodule", testbench_code, re.DOTALL):
            score += 0.2
        
        return min(1.0, score)


# ============================================================
# TIER-BASED TESTBENCH SELECTION
# ============================================================

def select_testbench_source(prompt, rtl_code, matcher):
    """
    Tier-based selection of testbench source
    
    Returns: (source_name, testbench_code, metadata) or (None, None, None)
    """
    
    # TIER 2A: Try dataset matching (final_rtl_tb_dataset.jsonl)
    print("\n📊 TIER 2A: Searching final_rtl_tb_dataset.jsonl...")
    match, score = matcher.find_tier2a_match(prompt, rtl_code, threshold=0.55)
    
    if match and score > 0.55:
        module_name = matcher._extract_ports_from_rtl(rtl_code)[0] or "top"
        tb_code = matcher.extract_testbench_from_sample(match)
        
        if tb_code:
            quality = matcher.get_testbench_quality_score(tb_code)
            print(f"✅ TIER 2A Match found!")
            print(f"   Problem: {match.get('problem_id')}")
            print(f"   Similarity: {score:.2%}")
            print(f"   Quality: {quality:.2%}")
            print(f"   Source: {match.get('source')}")
            
            return "TIER_2A_DATASET", tb_code, {
                'problem_id': match.get('problem_id'),
                'similarity': score,
                'quality': quality,
                'source': match.get('source')
            }
    
    # TIER 2B: Try verilog-eval matching
    print("📊 TIER 2B: Searching verilog-eval dataset...")
    problem_id, tb_code = matcher.find_tier2b_match(rtl_code)
    
    if tb_code:
        quality = matcher.get_testbench_quality_score(tb_code)
        print(f"✅ TIER 2B Match found!")
        print(f"   Problem: {problem_id}")
        print(f"   Quality: {quality:.2%}")
        
        return "TIER_2B_VERILOG_EVAL", tb_code, {
            'problem_id': problem_id,
            'quality': quality,
            'source': 'VerilogEval'
        }
    
    # TIER 3: Fall back to generation (handled by caller)
    print("❌ No dataset match → Will use TIER 3 (Generic Generation)")
    return None, None, None


if __name__ == "__main__":
    # Test the matcher
    matcher = DatasetMatcher()
    
    print("\n" + "="*60)
    print("DATASET MATCHER TEST")
    print("="*60)
    
    # Example RTL
    test_rtl = """
    module counter(
        input clk,
        input rst,
        input enable,
        output [3:0] count
    );
    
    reg [3:0] count_reg;
    
    always @(posedge clk) begin
        if (rst)
            count_reg <= 0;
        else if (enable)
            count_reg <= count_reg + 1;
    end
    
    assign count = count_reg;
    endmodule
    """
    
    test_prompt = "Design a 4-bit counter with reset and enable"
    
    source, tb_code, metadata = select_testbench_source(test_prompt, test_rtl, matcher)
    
    if source:
        print(f"\n🎯 Selected: {source}")
        print(f"📋 Metadata: {metadata}")
        print(f"\n📝 Testbench Preview (first 500 chars):")
        print(tb_code[:500])
