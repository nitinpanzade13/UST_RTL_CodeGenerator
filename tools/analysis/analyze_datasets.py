import json
import os

# Analyze final_rtl_tb_dataset.jsonl
print("=" * 60)
print("FINAL_RTL_TB_DATASET.JSONL ANALYSIS")
print("=" * 60)

dataset_path = "datasets/final_rtl_tb_dataset.jsonl"
samples = []

with open(dataset_path, 'r') as f:
    for line in f:
        samples.append(json.loads(line))

print(f"\n✓ Total samples: {len(samples)}")

# Group by source
sources = {}
for s in samples:
    source = s.get('source', 'Unknown')
    sources[source] = sources.get(source, 0) + 1

print(f"\nSamples by source:")
for source, count in sources.items():
    print(f"  - {source}: {count}")

# Check what fields each sample has
if samples:
    print(f"\nFields in each sample:")
    for field in samples[0].keys():
        print(f"  - {field}")
    
    # Show first sample structure
    print(f"\nFirst sample keys and content preview:")
    s = samples[0]
    for key in s.keys():
        val = s[key]
        if isinstance(val, str):
            preview = val[:100] + "..." if len(val) > 100 else val
            print(f"  - {key}: {preview}")
        else:
            print(f"  - {key}: {val}")

# Analyze verilog-eval dataset
print("\n" + "=" * 60)
print("VERILOG-EVAL DATASET ANALYSIS")
print("=" * 60)

verilog_eval_path = "datasets/verilog-eval/dataset_code-complete-iccad2023"
problems = set()

for file in os.listdir(verilog_eval_path):
    if file.endswith("_ref.sv"):
        problem_id = file.replace("_ref.sv", "")
        problems.add(problem_id)

print(f"\n✓ Total problems: {len(problems)}")
print(f"\nFirst 10 problems:")
for problem in sorted(problems)[:10]:
    print(f"  - {problem}")

print("\n" + "=" * 60)
print("DATASET COMPATIBILITY ASSESSMENT")
print("=" * 60)

print("""
✅ FINAL_RTL_TB_DATASET.JSONL:
   - Contains: Problem ID, RTL Code, Testbench Code, Specification
   - Size: ~{} samples
   - Best for: Sequential/Complex designs, Behavioral verification
   - Contains testbenches: YES ✓
   - Can directly provide testbenches: YES ✓

✅ VERILOG-EVAL DATASET:
   - Contains: Problem ID, Prompt, Reference RTL, Test files
   - Size: ~{} problems
   - Best for: Combinational/Simple designs
   - Contains complete testbenches: YES ✓
   - Can directly provide testbenches: YES ✓

📊 RECOMMENDED PIPELINE USAGE:
   1. Try AI generation (current approach)
   2. TIER 2A: Match RTL against final_rtl_tb_dataset using:
      - Semantic similarity of problem description
      - RTL code structure comparison
      - If match found → use existing testbench
   3. TIER 2B: Match against verilog-eval using:
      - Problem complexity heuristics
      - Signal pattern matching
   4. TIER 3: Generate generic testbench
""".format(len(samples), len(problems)))
