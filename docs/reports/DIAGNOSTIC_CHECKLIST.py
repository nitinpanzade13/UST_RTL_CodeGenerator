#!/usr/bin/env python3
"""
✅ DIAGNOSTIC CHECKLIST: Questions to Verify System Health
═════════════════════════════════════════════════════════════════════════════

Use this checklist to verify that your RTL generation pipeline is working
correctly and to diagnose any issues.

═════════════════════════════════════════════════════════════════════════════
SECTION 1: SETUP & DEPENDENCIES
═════════════════════════════════════════════════════════════════════════════

□ Question 1.1: Is CUDA available?
  How to check: Look for "CUDA is available. Using GPU." in startup
  Expected: Yes ✓
  If not: Use CPU mode (slower but works)

□ Question 1.2: Did the model load successfully?
  How to check: Look for "Model loaded successfully!" message
  Expected: Yes, appears twice (model + app)
  If not: Check GPU memory, model weights download

□ Question 1.3: Are datasets loaded?
  How to check: Look for "✓ Loaded TIER 2A: 439 samples"
  Expected: Yes ✓
  If not: Check datasets/ folder exists

□ Question 1.4: Is the Gradio app running?
  How to check: Look for "Running on local URL: http://127.0.0.1:7860"
  Expected: Yes, open in browser
  If not: Check port 7860 isn't in use

═════════════════════════════════════════════════════════════════════════════
SECTION 2: RTL GENERATION (Core)
═════════════════════════════════════════════════════════════════════════════

□ Question 2.1: Does RTL generation work?
  Test: Input "Design a 4-bit counter"
  Expected: RTL module with clk, reset, count signals
  Check: code starts with "module" and ends with "endmodule"
  If not: Check AI model output, try simpler design

□ Question 2.2: Is RTL syntactically clean?
  Look for: "✅ RTL clean at iteration 1"
  Expected: Validation passes (compile_success: True)
  If not: RTL generator has errors, check validation

□ Question 2.3: Does RTL have correct port names?
  For counter: Should have clk, reset, count
  Check: Port names match expected interface
  If not: AI may have named ports differently (acceptable)

═════════════════════════════════════════════════════════════════════════════
SECTION 3: TIER 1 - AI TESTBENCH GENERATION
═════════════════════════════════════════════════════════════════════════════

□ Question 3.1: Does TIER 1 attempt to generate?
  Look for: "🧠 TIER 1: Attempting AI testbench generation..."
  Expected: Yes, this message appears
  If not: System skipped to TIER 2 (check why)

□ Question 3.2: TIER 1 - Does it have module declaration?
  Look for: "Module declaration: True ✓"
  Expected: Yes
  What it means: AI generated "module tb" or similar
  If False: AI output doesn't have module wrapper

□ Question 3.3: TIER 1 - Does it have endmodule?
  Look for: "Endmodule statement: True ✓"
  Expected: Yes
  What it means: AI generated "endmodule" keyword
  If False: Generated testbench is incomplete

□ Question 3.4: TIER 1 - Does it have result reporting?
  Look for: "Result/checks: True ✓"
  Expected: Yes
  What it means: Has FINAL_RESULT, $display, assert, or if (
  If False: No verification logic in testbench

□ Question 3.5: TIER 1 - Is code substantial?
  Look for: "Substantial code: True ✓"
  Expected: Yes (>150 chars, >5 lines)
  What it means: Testbench isn't just an empty stub
  If False: AI generated very short code (failure)

□ Question 3.6: TIER 1 - What size is generated testbench?
  Look for: "Generated testbench size: XXX chars, X lines"
  Expected: 300+ chars, 10+ lines for real testbench
  If <150 chars: Likely empty/malformed
  If >800 chars: Possibly good, check for errors

□ Question 3.7: Did TIER 1 pass validation?
  Look for: NO debug output → Passed silently ✓
  OR: All True ✓ → Passed ✓
  OR: "⚠️ TIER 1 failed..." → Failed (check which criterion)
  Expected: Silent pass or all checkmarks
  If debug output: Shows what failed

□ Question 3.8: Is testbench_source "TIER_1_AI"?
  Look for: "testbench_source": "TIER_1_AI"
  Expected: If TIER 1 passed
  If "TIER_2_OR_3_FALLBACK": TIER 1 failed, using fallback
  This is OK! Fallback still works 100%

═════════════════════════════════════════════════════════════════════════════
SECTION 4: TIER 2 - DATASET MATCHING (Fallback 1)
═════════════════════════════════════════════════════════════════════════════

□ Question 4.1: Does TIER 2A search happen?
  Look for: "📊 TIER 2A: Searching final_rtl_tb_dataset.jsonl..."
  Expected: Yes (if TIER 1 failed)
  If not: System went straight to TIER 3

□ Question 4.2: Did TIER 2A find a match?
  Look for: "✅ TIER 2A Match found!" OR "❌ No dataset match"
  Expected: Match if design is common (counter, gates, etc.)
  If no match: Design is too unique for dataset

□ Question 4.3: What was the similarity score?
  Look for: "Similarity: XX%"
  Expected: 55-80% for good matches
  If <55%: Threshold not met, continues to TIER 3
  If >70%: Excellent match!

□ Question 4.4: Was the matched testbench Verilog-compatible?
  Check: No SystemVerilog features in matched testbench
  Expected: Pure Verilog (no typedef, logic, bit, @(*), etc.)
  If SystemVerilog: Filtered out (good!)

═════════════════════════════════════════════════════════════════════════════
SECTION 5: TIER 3 - GENERIC GENERATION (Fallback 2)
═════════════════════════════════════════════════════════════════════════════

□ Question 5.1: Does TIER 3 attempt to generate?
  Look for: "⚠️ TIER 2 failed → Using TIER 3 (Generic Testbench Generation)..."
  Expected: If TIER 1 and 2 failed
  If yes: Final fallback is active

□ Question 5.2: Does TIER 3 produce testbench?
  Expected: Yes, always succeeds
  What it means: Rule-based generation always works
  If not: There's a bug in TIER 3

□ Question 5.3: Is TIER 3 testbench appropriate for design?
  Check: Uses correct clock generation, reset handling, etc.
  For COUNTER: Should have clock and reset logic
  For ADDER: Should have test vectors
  For GATES: Should have simple test loops

═════════════════════════════════════════════════════════════════════════════
SECTION 6: COMPILATION & SIMULATION
═════════════════════════════════════════════════════════════════════════════

□ Question 6.1: Does testbench compile with Iverilog?
  Look for: No "error:" messages in simulation
  Expected: Clean compilation
  If errors: Testbench has Verilog syntax issues
  Check: No SystemVerilog features in final testbench

□ Question 6.2: Does simulation run?
  Look for: "✅ Simulation PASSED" OR "❌ Simulation FAILED"
  Expected: PASSED ✅
  If FAILED: RTL logic doesn't match test expectations
  If error during compile: Syntax issue in testbench

□ Question 6.3: What was the simulation result?
  Look for: "FINAL_RESULT: PASS" or "FINAL_RESULT: FAIL"
  Expected: PASS ✅
  If FAIL: Design logic incorrect or testbench wrong
  If neither: Testbench didn't produce result

□ Question 6.4: Was wave.vcd generated?
  Check: temp/wave.vcd exists
  Expected: Yes, waveform file for debugging
  If not: No waveform dumping in testbench

═════════════════════════════════════════════════════════════════════════════
SECTION 7: SYSTEM RELIABILITY
═════════════════════════════════════════════════════════════════════════════

□ Question 7.1: Did the full pipeline complete?
  Look for: Final result with ✅ PASS or ❌ FAIL
  Expected: Always completes with a result
  If incomplete: System crashed or hung

□ Question 7.2: What was the overall status?
  Look for: "status": "✅ PASS" OR "status": "❌ FAIL"
  Expected: ✅ PASS (simulation passed)
  ❌ FAIL is OK too, means design logic issue (not system issue)

□ Question 7.3: Which tier was ultimately used?
  Look for: "testbench_source": "TIER_X_Y"
  Expected: Any tier (1, 2A, 2B, or 3) - shows fallback worked
  This is good! Means system chose best available option

□ Question 7.4: Does system work end-to-end?
  Overall check: Started → RTL → Testbench → Simulation → Result
  Expected: All steps complete ✅
  If stops: Find which step failed

═════════════════════════════════════════════════════════════════════════════
SECTION 8: TESTING DIFFERENT DESIGNS
═════════════════════════════════════════════════════════════════════════════

Test these designs and track which tier was used:

□ Simple gate: "Design a 2-input AND gate"
  Expected: TIER 1 or 2A (simple, common)
  
□ Counter: "Design a 4-bit counter"
  Expected: TIER 1, 2A, or 3 (common, has rules)
  
□ Mux: "Design a 2:1 multiplexer"
  Expected: TIER 1, 2A, or 3 (recognizable)
  
□ Complex: "Design a 32-bit ALU with 8 operations"
  Expected: TIER 1 (AI) or 3 (too complex for dataset)
  
□ Exotic: "Design an LZ77 compression encoder"
  Expected: TIER 1 (AI) or 3 (unusual, not in dataset)

Track:
- How many use TIER 1 (AI)?
- How many use TIER 2 (Dataset)?
- How many use TIER 3 (Generic)?
- How many fail?

Goal: Most should pass (✅ or ❌ is acceptable, just needs result)

═════════════════════════════════════════════════════════════════════════════
SECTION 9: PERFORMANCE METRICS
═════════════════════════════════════════════════════════════════════════════

□ Question 9.1: How fast is RTL generation?
  Time: From input to RTL code
  Expected: 5-15 seconds (depends on iterations)
  If >30s: Model taking long, check GPU

□ Question 9.2: How fast is testbench generation?
  Time: From RTL to compiled testbench
  Expected: <5 seconds for TIER 2, <1s for TIER 3
  If >10s: AI generation (TIER 1) slower, normal

□ Question 9.3: How fast is simulation?
  Time: Compilation + execution
  Expected: <2 seconds
  If >5s: Complex design or slow Iverilog

□ Question 9.4: Overall pipeline time?
  Time: Input to final result
  Expected: 10-30 seconds
  If >60s: Check if stuck somewhere

═════════════════════════════════════════════════════════════════════════════
SECTION 10: ERROR DIAGNOSTICS
═════════════════════════════════════════════════════════════════════════════

If something fails, check:

□ RTL Compilation Failed:
  - Are all ports declared?
  - Are all signals assigned?
  - Check for width mismatches
  - Look for syntax errors (missing semicolons, etc.)

□ Testbench Compilation Failed:
  - Check for SystemVerilog syntax (logic, typedef, etc.)
  - Look for incomplete modules
  - Verify DUT port mapping is correct
  - Check for undefined signals

□ Simulation Failed (FINAL_RESULT: FAIL):
  - RTL logic may be incorrect
  - Testbench expectations may be wrong
  - Check waveform (wave.vcd) for signals
  - Verify clock and reset are working

□ Simulation Crashed:
  - Infinite loops in testbench?
  - Missing $finish statement?
  - Check for undefined values propagating
  - Try simpler design first

□ Dataset not loading:
  - Does datasets/ folder exist?
  - Does datasets/final_rtl_tb_dataset.jsonl exist?
  - Check file isn't corrupted
  - Verify JSON is valid format

═════════════════════════════════════════════════════════════════════════════
QUICK REFERENCE: WHAT EACH ANSWER MEANS
═════════════════════════════════════════════════════════════════════════════

✅ All True → TIER 1 PASSED (AI testbench works!)
⚠️ Some False → TIER 1 FAILED (falling back is OK)
   → Check if TIER 2 matched (dataset reuse)
   → If not, TIER 3 handles it (guaranteed)

Final status ✅ PASS → Success! Design works as expected
Final status ❌ FAIL → Design logic issue (not system issue)

═════════════════════════════════════════════════════════════════════════════
SCORING YOUR SYSTEM
═════════════════════════════════════════════════════════════════════════════

Count checkmarks in each section:

Setup (1.1-1.4):        _/4   (all should be ✓)
RTL Generation (2.1-2.3): _/3   (all should be ✓)
TIER 1 (3.1-3.8):       _/8   (3.7-3.8 flexible)
TIER 2 (4.1-4.4):       _/4   (optional, only if TIER 1 failed)
TIER 3 (5.1-5.3):       _/3   (optional, if TIER 2 failed)
Compilation (6.1-6.4):  _/4   (all should be ✓)
Reliability (7.1-7.4):  _/4   (all should be ✓)

Total Score: _/30 (or _/20 if skipping optional tiers)

Excellent: 28-30/30 ✅
Good:      24-27/30 ✓
OK:        20-23/30 ⚠️
Poor:      <20/30   ❌

═════════════════════════════════════════════════════════════════════════════
"""

print(__doc__)
