import os
import re
import json
from datetime import datetime

from rtl_generator import generate_rtl
from testbench_generator import (
    generate_testbench_with_groq,
    validate_groq_tb,
    generate_testbench,
    generate_generic_testbench
)
from rtl_simulator import run_simulation
from dataset_matcher import DatasetMatcher, select_testbench_source

# Initialize dataset matcher (singleton-like)
_dataset_matcher = None

def get_dataset_matcher():
    global _dataset_matcher
    if _dataset_matcher is None:
        _dataset_matcher = DatasetMatcher()
    return _dataset_matcher


# ==============================
# 1. Extract IO + Logic Type
# ==============================
def extract_io_from_prompt(prompt):
    prompt = prompt.lower()

    if "4-bit adder" in prompt:
        return (
            ["A", "B", "Cin"],
            ["S", "Cout"],
            "ADDER",
            {"A": 4, "B": 4, "Cin": 1, "S": 4, "Cout": 1}
        )
    if "mux" in prompt or "multiplexer" in prompt:
        return (
            ["A", "B", "S"],
            ["Y"],
            "MUX",
            {"A": 1, "B": 1, "S": 1, "Y": 1}
        )
    if "demux" in prompt:
        return (
            ["D", "S"],
            ["Y0", "Y1"],
            "DEMUX",
            {"D": 1, "S": 1, "Y0": 1, "Y1": 1}
        )
    if "decoder" in prompt:
        return (
            ["A"],
            ["Y"],
            "DECODER",
            {"A": 2, "Y": 4}
        )
    if "encoder" in prompt:
        return (
            ["A"],
            ["Y"],
            "ENCODER",
            {"A": 4, "Y": 2}
        )
    if "comparator" in prompt:
        return (
            ["A", "B"],
            ["GT", "EQ", "LT"],
            "COMPARATOR",
            {"A": 1, "B": 1, "GT": 1, "EQ": 1, "LT": 1}
        )

    if "2 input" in prompt:
        inputs = ["a", "b"]
    else:
        inputs = ["a"]

    outputs = ["y"]

    if "and" in prompt:
        logic = "AND"
    elif "or" in prompt:
        logic = "OR"
    elif "xor" in prompt:
        logic = "XOR"
    else:
        logic = "UNKNOWN"

    widths = {sig: 1 for sig in inputs + outputs}
    return inputs, outputs, logic, widths


# ==============================
# 2. Extract Module Name
# ==============================
def extract_module_name(rtl_code):
    match = re.search(r"module\s+(\w+)", rtl_code)
    return match.group(1) if match else "top_module"


# ==============================
# 2B. Save Testbench Record
# ==============================
def save_testbench_record(prompt, rtl_code, tb_code, testbench_source, sim_status, output_file="generated_testbenches.jsonl"):
    """Save generated testbench with prompt to JSONL file"""
    os.makedirs("generated", exist_ok=True)
    filepath = os.path.join("generated", output_file)
    
    record = {
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
        "rtl_code": rtl_code,
        "testbench_code": tb_code,
        "testbench_source": testbench_source,
        "sim_status": sim_status,
        "module_name": extract_module_name(rtl_code)
    }
    
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    
    print(f"💾 Testbench saved to {filepath}")


# ==============================
# 3. RTL Port Parser
# ==============================
def parse_rtl_ports(rtl_code):
    inputs = []
    outputs = []
    widths = {}

    for line in rtl_code.split("\n"):
        line = line.strip()

        if line.startswith("input"):
            line = line.replace("input", "").replace("wire", "").replace("reg", "").replace(";", "").strip()
            if "[" in line:
                width = int(line.split(":")[0][1:]) + 1
                names = line.split("]")[1].split(",")
                for name in names:
                    name = name.strip()
                    if name:
                        inputs.append(name)
                        widths[name] = width
            else:
                for name in line.split(","):
                    name = name.strip()
                    if name:
                        inputs.append(name)
                        widths[name] = 1

        elif line.startswith("output"):
            line = line.replace("output", "").replace("wire", "").replace("reg", "").replace(";", "").strip()
            if "[" in line:
                width = int(line.split(":")[0][1:]) + 1
                names = line.split("]")[1].split(",")
                for name in names:
                    name = name.strip()
                    if name:
                        outputs.append(name)
                        widths[name] = width
            else:
                for name in line.split(","):
                    name = name.strip()
                    if name:
                        outputs.append(name)
                        widths[name] = 1

    return inputs, outputs, widths


# ==============================
# 4. Main Pipeline
# ==============================
def run_pipeline(model, tokenizer, prompt):
    os.makedirs("temp", exist_ok=True)

    # ==========================
    # 1. Generate RTL
    # ==========================
    rtl_code = generate_rtl(model, tokenizer, prompt)

    rtl_path = "temp/rtl.v"
    with open(rtl_path, "w", encoding="utf-8") as f:
        f.write(rtl_code)

    # ==========================
    # 2. Extract Info
    # ==========================
    module_name = extract_module_name(rtl_code)
    _, _, logic_type, _ = extract_io_from_prompt(prompt)

    # ==========================
    # 2C. Detect Sequential Designs
    # ==========================
    prompt_lower = prompt.lower()
    is_sequential = (
        logic_type == "COUNTER" or
        "counter" in prompt_lower or
        "fsm" in prompt_lower or
        "sequential" in prompt_lower or
        "flip flop" in prompt_lower or
        "register" in prompt_lower
    )

    if is_sequential:
        print("\n⏱️  Sequential design detected - skipping TIER 1, going to TIER 2...")
        tb_code = ""
        testbench_source = "TIER_2_RULEBASED"
    else:
        # ==========================
        # TIER 1: Groq API Testbench
        # ==========================
        print("\n🌐 TIER 1: Groq API testbench generation...")
        tb_code = generate_testbench_with_groq(rtl_code)
        testbench_source = "TIER_1_GROQ"

    if not is_sequential:
        if validate_groq_tb(tb_code, module_name):
            print("✅ TIER 1 passed")
        else:
            print("⚠️ TIER 1 failed → TIER 2 (Dataset Matching)...")
            tb_code = ""
            testbench_source = ""

    if not tb_code:
        # ==========================
        # TIER 2: Rule-Based or Dataset
        # ==========================
        print("⚠️ TIER 2: Attempting rule-based/dataset testbench...")

        # skip Tier 2 dataset for complex MUX
        skip_tier2_dataset = (
            ("4:1" in prompt or "4 to 1" in prompt or "4-to-1" in prompt)
            and ("mux" in prompt.lower() or "multiplexer" in prompt.lower())
        )

        source, matched_tb, metadata = None, None, None

        if not skip_tier2_dataset:
            matcher = get_dataset_matcher()
            source, matched_tb, metadata = select_testbench_source(
                prompt, rtl_code, matcher
            )

        if matched_tb:
            tb_code = matched_tb
            testbench_source = source
            print(f"✅ TIER 2 passed — {source}")
            print(f"   Details: {metadata}")
        else:
            # ==========================
            # TIER 3: Generic Fallback
            # ==========================
            print("⚠️ TIER 2 failed → TIER 3 (Generic)...")
            testbench_source = "TIER_3_GENERIC"

            inputs, outputs, widths = parse_rtl_ports(rtl_code)

            if logic_type != "UNKNOWN" and len(inputs) <= 4:
                try:
                    tb_code = generate_testbench(
                        module_name, inputs, outputs, widths, logic_type
                    )
                except Exception:
                    tb_code = generate_generic_testbench(
                        module_name, inputs, outputs, widths
                    )
            else:
                tb_code = generate_generic_testbench(
                    module_name, inputs, outputs, widths
                )

    # ==========================
    # Save Testbench
    # ==========================
    tb_path = "temp/tb.v"
    with open(tb_path, "w", encoding="utf-8") as f:
        f.write(tb_code)

    # ==========================
    # Run Simulation
    # ==========================
    sim_result = run_simulation(rtl_path, tb_path)

    if not sim_result["success"]:
        save_testbench_record(prompt, rtl_code, tb_code, testbench_source, "SIM_ERROR")
        return {
            "status": "❌ Simulation Failed",
            "stage": sim_result.get("stage", "unknown"),
            "error": sim_result.get("error", ""),
            "rtl": rtl_code
        }

    sim_output = sim_result.get("output", "")
    status     = sim_result.get("status", "FAIL")
    vcd_path   = sim_result.get("vcd_path", None)

    # ==========================
    # Save Testbench Record
    # ==========================
    save_testbench_record(prompt, rtl_code, tb_code, testbench_source, status)

    return {
        "status": "✅ PASS" if status == "PASS" else "❌ FAIL",
        "functional_accuracy": 100 if status == "PASS" else 0,
        "correct_cases": 1 if status == "PASS" else 0,
        "total_cases": 1,
        "rtl": rtl_code,
        "simulation_output": sim_output,
        "vcd_path": vcd_path,
        "testbench_source": testbench_source
    }