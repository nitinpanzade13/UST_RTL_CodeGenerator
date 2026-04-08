
# import os
# import re

# from rtl_generator import generate_rtl
# from testbench_generator import generate_testbench
# from rtl_simulator import run_simulation


# # ==============================
# # 1. Extract IO + Logic Type
# # ==============================
# def extract_io_from_prompt(prompt):
#     prompt = prompt.lower()

#     # 🔥 ADDER DETECTION
#     if "4-bit adder" in prompt:
#         inputs = ["A", "B", "Cin"]
#         outputs = ["S", "Cout"]
#         logic = "ADDER"

#         bit_widths = {
#             "A": 4,
#             "B": 4,
#             "Cin": 1,
#             "S": 4,
#             "Cout": 1
#         }

#         return inputs, outputs, logic, bit_widths

#     # 🔹 BASIC LOGIC GATES
#     if "2 input" in prompt:
#         inputs = ["a", "b"]
#     else:
#         inputs = ["a"]

#     outputs = ["y"]

#     if "and" in prompt:
#         logic = "AND"
#     elif "or" in prompt:
#         logic = "OR"
#     elif "xor" in prompt:
#         logic = "XOR"
#     else:
#         logic = "UNKNOWN"

#     bit_widths = {sig: 1 for sig in inputs + outputs}

#     return inputs, outputs, logic, bit_widths


# # ==============================
# # 2. Extract Module Name
# # ==============================
# def extract_module_name(rtl_code):
#     match = re.search(r"module\s+(\w+)", rtl_code)
#     return match.group(1) if match else "top_module"


# # ==============================
# # 3. Main Pipeline (🔥 UPDATED)
# # ==============================
# def run_pipeline(model, tokenizer, prompt):
#     os.makedirs("temp", exist_ok=True)

#     # ==========================
#     # 1. Generate RTL
#     # ==========================
#     rtl_code = generate_rtl(model, tokenizer, prompt)

#     rtl_path = "temp/rtl.v"
#     with open(rtl_path, "w") as f:
#         f.write(rtl_code)

#     # ==========================
#     # 2. Extract Info
#     # ==========================
#     module_name = extract_module_name(rtl_code)
#     inputs, outputs, logic, bit_widths = extract_io_from_prompt(prompt)

#     # ==========================
#     # 3. Generate Testbench (SELF-CHECKING)
#     # ==========================
#     tb_code = generate_testbench(
#         module_name,
#         inputs,
#         outputs,
#         bit_widths,
#         logic  # 🔥 IMPORTANT
#     )

#     tb_path = "temp/tb.v"
#     with open(tb_path, "w") as f:
#         f.write(tb_code)

#     # ==========================
#     # 4. Run Simulation
#     # ==========================
#     sim_result = run_simulation(rtl_path, tb_path)

#     if not sim_result["success"]:
#         return {
#             "status": "❌ Simulation Failed",
#             "stage": sim_result.get("stage", "unknown"),
#             "error": sim_result.get("error", ""),
#             "rtl": rtl_code
#         }

#     sim_output = sim_result["output"]

#     # ==========================
#     # 5. FINAL RESULT (FROM TESTBENCH)
#     # ==========================
#     status = sim_result["status"]  # PASS / FAIL

#     return {
#         "status": "✅ PASS" if status == "PASS" else "❌ FAIL",
#         "functional_accuracy": 100 if status == "PASS" else 0,
#         "correct_cases": 1 if status == "PASS" else 0,
#         "total_cases": 1,
#         "rtl": rtl_code,
#         "simulation_output": sim_output
#     }


import os
import re

from rtl_generator import generate_rtl, generate_testbench_with_ai
from testbench_generator import generate_testbench, generate_generic_testbench
from rtl_simulator import run_simulation


# ==============================
# 1. Extract IO + Logic Type (🔥 FULL SUPPORT)
# ==============================
def extract_io_from_prompt(prompt):
    prompt = prompt.lower()

    # ==========================
    # ADDER
    # ==========================
    if "4-bit adder" in prompt:
        return (
            ["A", "B", "Cin"],
            ["S", "Cout"],
            "ADDER",
            {"A": 4, "B": 4, "Cin": 1, "S": 4, "Cout": 1}
        )

    # ==========================
    # MUX
    # ==========================
    if "mux" in prompt or "multiplexer" in prompt:
        return (
            ["A", "B", "S"],
            ["Y"],
            "MUX",
            {"A": 1, "B": 1, "S": 1, "Y": 1}
        )

    # ==========================
    # DEMUX
    # ==========================
    if "demux" in prompt:
        return (
            ["D", "S"],
            ["Y0", "Y1"],
            "DEMUX",
            {"D": 1, "S": 1, "Y0": 1, "Y1": 1}
        )

    # ==========================
    # DECODER
    # ==========================
    if "decoder" in prompt:
        return (
            ["A"],
            ["Y"],
            "DECODER",
            {"A": 2, "Y": 4}
        )

    # ==========================
    # ENCODER
    # ==========================
    if "encoder" in prompt:
        return (
            ["A"],
            ["Y"],
            "ENCODER",
            {"A": 4, "Y": 2}
        )

    # ==========================
    # COMPARATOR
    # ==========================
    if "comparator" in prompt:
        return (
            ["A", "B"],
            ["GT", "EQ", "LT"],
            "COMPARATOR",
            {"A": 1, "B": 1, "GT": 1, "EQ": 1, "LT": 1}
        )

    # ==========================
    # BASIC GATES
    # ==========================
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
# 🔥 RTL PORT PARSER (ADD THIS)
# ==============================
def parse_rtl_ports(rtl_code):
    inputs = []
    outputs = []
    widths = {}

    lines = rtl_code.split("\n")

    for line in lines:
        line = line.strip()

        # Remove keywords
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
# 3. Main Pipeline (🔥 FINAL)
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
    # 2. Extract Module Name
    # ==========================
    module_name = extract_module_name(rtl_code)

    # ==========================
    # 3. AI Testbench (Primary)
    # ==========================
    print("\n🧠 Generating AI testbench...")
    tb_code = generate_testbench_with_ai(
        model,
        tokenizer,
        prompt,
        rtl_code
    )

    # ==========================
    # FALLBACK
    # ==========================
    if "FINAL_RESULT" not in tb_code or "module tb" not in tb_code:
        print("⚠️ AI testbench invalid → using parsed RTL fallback")

        inputs, outputs, widths = parse_rtl_ports(rtl_code)

        # Try rule-based only if recognizable
        if len(inputs) <= 3:
            try:
                tb_code = generate_testbench(
                    module_name,
                    inputs,
                    outputs,
                    widths,
                    logic_type  # keep same
                )
            except:
                tb_code = generate_generic_testbench(
                    module_name,
                    inputs,
                    outputs,
                    widths
                )
        else:
            tb_code = generate_generic_testbench(
                module_name,
                inputs,
                outputs,
                widths
            )

    # Save testbench
    tb_path = "temp/tb.v"
    with open(tb_path, "w", encoding="utf-8") as f:
        f.write(tb_code)

    # ==========================
    # 5. Run Simulation
    # ==========================
    sim_result = run_simulation(rtl_path, tb_path)

    if not sim_result["success"]:
        return {
            "status": "❌ Simulation Failed",
            "stage": sim_result.get("stage", "unknown"),
            "error": sim_result.get("error", ""),
            "rtl": rtl_code
        }

    # ==========================
    # 6. Results
    # ==========================
    sim_output = sim_result.get("output", "")
    status = sim_result.get("status", "FAIL")
    vcd_path = sim_result.get("vcd_path", None)

    # ==========================
    # 7. Final Output
    # ==========================
    return {
        "status": "✅ PASS" if status == "PASS" else "❌ FAIL",
        "functional_accuracy": 100 if status == "PASS" else 0,
        "correct_cases": 1 if status == "PASS" else 0,
        "total_cases": 1,
        "rtl": rtl_code,
        "simulation_output": sim_output,
        "vcd_path": vcd_path
    }