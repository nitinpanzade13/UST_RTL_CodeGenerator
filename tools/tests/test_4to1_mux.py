#!/usr/bin/env python3
"""Test 4:1 MUX with updated skip_tier2 logic and enhanced detector."""

import sys
sys.path.insert(0, '.')

from evaluate_pipeline import run_pipeline
from model_loader import load_model_and_tokenizer

print("=" * 80)
print("🧪 Testing 4:1 Multiplexer with Updated Code")
print("=" * 80)

# Load model
print("\n📦 Loading model and tokenizer...")
try:
    model, tokenizer = load_model_and_tokenizer()
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    sys.exit(1)

# Test prompt
prompt = "design a 4:1 multiplexer"

print(f"\n🎯 Test Prompt: {prompt}")
print("\n" + "=" * 80)

# Run pipeline
result = run_pipeline(model, tokenizer, prompt)

# Report results
print("\n" + "=" * 80)
print("📊 TEST RESULTS:")
print("=" * 80)

print(f"\nStatus: {result.get('status', 'UNKNOWN')}")
print(f"Testbench Source: {result.get('testbench_source', 'UNKNOWN')}")
print(f"Functional Accuracy: {result.get('functional_accuracy', 0)}%")

# Check for SystemVerilog indicators
tb_code = result.get("rtl", "")  # This is actually simulation output in the result
print("\n🔍 RTL Compilation Check:")
if "error" in result or "Error" in result or "SystemVerilog" in str(result):
    print("❌ Compilation errors detected")
else:
    print("✅ No obvious errors")

# Show simulation output excerpt
sim_output = result.get("simulation_output", "")
if "FINAL_RESULT: PASS" in sim_output:
    print("\n✅ FINAL_RESULT: PASS")
elif "FINAL_RESULT: FAIL" in sim_output:
    print("\n❌ FINAL_RESULT: FAIL")
else:
    print("\n⚠️ FINAL_RESULT not found in simulation output")

print("\n" + "=" * 80)
