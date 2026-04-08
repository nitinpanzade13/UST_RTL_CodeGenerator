
# import torch
# import re

# from rtl_validator import (
#     validate_rtl_full,
#     build_correction_prompt
# )


# # ==============================
# # 1. Core Generation Function
# # ==============================
# def _generate_once(model, tokenizer, prompt):
#     formatted_prompt = f"""
# You are an expert Verilog RTL engineer.

# Generate COMPLETE Verilog code.

# Rules:
# - Return ONLY Verilog code
# - Output must start with 'module'
# - Output must end with 'endmodule'
# - If submodules are used, include their module definitions
# - Remove any unused wires or redundant signals

# Instruction:
# {prompt}

# Verilog:
# """

#     inputs = tokenizer(
#         formatted_prompt,
#         return_tensors="pt"
#     ).to(model.device)

#     with torch.no_grad():
#         outputs = model.generate(
#             **inputs,
#             max_new_tokens=600,
#             do_sample=False,
#             temperature=0.1
#         )

#     decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

#     # Clean tokenizer artifacts
#     decoded = decoded.replace("Ġ", " ")
#     decoded = decoded.replace("Ċ", "\n")

#     # Remove prompt part
#     if "Verilog:" in decoded:
#         decoded = decoded.split("Verilog:")[-1]

#     # Extract valid modules
#     modules = re.findall(r"module\s+\w+\s*[\(#;][\s\S]*?endmodule", decoded)

#     if modules:
#         unique = {}
#         for m in modules:
#             name = re.match(r"module\s+(\w+)", m).group(1)
#             if name not in unique or len(m) > len(unique[name]):
#                 unique[name] = m
#         decoded = "\n\n".join(unique.values())

#     return decoded.strip()


# # ==============================
# # 2. Smart Self-Correcting Generator
# # ==============================
# def generate_rtl(model, tokenizer, prompt, max_iters=3):
#     rtl_code = _generate_once(model, tokenizer, prompt)

#     prev_critical_issues = None

#     for i in range(max_iters):
#         validation = validate_rtl_full(rtl_code)

#         # Debug info (very useful)
#         print(f"\n🔍 Iteration {i+1} Validation:")
#         print("Compile:", validation["compile_success"])
#         print("Severity:", validation["severity"])

#         # ✅ If clean → stop
#         if validation["is_clean"]:
#             print(f"✅ RTL clean at iteration {i+1}")
#             return rtl_code

#         # Extract severity levels
#         severity = validation["severity"]

#         critical_issues = [msg for level, msg in severity if level == "CRITICAL"]
#         warning_issues = [msg for level, msg in severity if level == "WARNING"]

#         # ==============================
#         # 🔴 Case 1: CRITICAL Issues
#         # ==============================
#         if critical_issues:
#             print(f"🚨 Critical Issues Detected ({len(critical_issues)}):")
#             for issue in critical_issues:
#                 print("  -", issue)

#             # STOP if same issue repeating
#             if prev_critical_issues == critical_issues:
#                 print("⛔ Same critical issues repeating → stopping retry")
#                 return rtl_code

#             prev_critical_issues = critical_issues

#             correction_prompt = build_correction_prompt(
#                 original_prompt=prompt,
#                 rtl_code=rtl_code,
#                 issues=critical_issues
#             )

#             # Strong enforcement
#             correction_prompt += """
# STRICT REQUIREMENTS:
# - ALL critical issues MUST be fixed
# - Ensure synthesizable and correct RTL
# """

#             rtl_code = _generate_once(model, tokenizer, correction_prompt)
#             continue

#         # ==============================
#         # 🟡 Case 2: Only WARNING Issues
#         # ==============================
#         if warning_issues:
#             print(f"🟡 Only warnings detected ({len(warning_issues)}), skipping retry")
#             return rtl_code

#         # ==============================
#         # 🔵 Case 3: Compilation Failure
#         # ==============================
#         if not validation["compile_success"]:
#             print("❌ Compilation failed, attempting fix")

#             correction_prompt = build_correction_prompt(
#                 original_prompt=prompt,
#                 rtl_code=rtl_code,
#                 issues=[validation["compile_message"]]
#             )

#             rtl_code = _generate_once(model, tokenizer, correction_prompt)
#             continue

#         # ==============================
#         # 🧠 Fallback (rare case)
#         # ==============================
#         print("⚠️ Unknown issue, stopping retry")
#         return rtl_code

#     print("⚠️ Max iterations reached, returning best attempt")
#     return rtl_code

import torch
import re

from rtl_validator import (
    validate_rtl_full,
    build_correction_prompt
)


# ==============================
# 1. Core RTL Generation
# ==============================
def _generate_once(model, tokenizer, prompt):

    formatted_prompt = f"""
You are an expert Verilog RTL engineer.

Generate COMPLETE Verilog code.

Rules:
- Return ONLY Verilog code
- Output must start with 'module'
- Output must end with 'endmodule'
- Ensure synthesizable RTL
- Remove unused wires
- Avoid width mismatch issues

Instruction:
{prompt}

Verilog:
"""

    inputs = tokenizer(
        formatted_prompt,
        return_tensors="pt"
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=600,
            do_sample=False
        )

    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Clean artifacts
    decoded = decoded.replace("Ġ", " ")
    decoded = decoded.replace("Ċ", "\n")

    # Remove prompt part
    if "Verilog:" in decoded:
        decoded = decoded.split("Verilog:")[-1]

    # Extract valid modules
    modules = re.findall(r"module\s+\w+\s*[\(#;][\s\S]*?endmodule", decoded)

    if modules:
        unique = {}
        for m in modules:
            name = re.match(r"module\s+(\w+)", m).group(1)
            if name not in unique or len(m) > len(unique[name]):
                unique[name] = m
        decoded = "\n\n".join(unique.values())

    return decoded.strip()


# ==============================
# 2. Smart Self-Correcting RTL Generator
# ==============================
def generate_rtl(model, tokenizer, prompt, max_iters=3):

    rtl_code = _generate_once(model, tokenizer, prompt)

    prev_critical_issues = None

    for i in range(max_iters):

        validation = validate_rtl_full(rtl_code)

        print(f"\n🔍 Iteration {i+1} Validation:")
        print("Compile:", validation["compile_success"])
        print("Severity:", validation["severity"])

        # ✅ CLEAN → RETURN
        if validation["is_clean"]:
            print(f"✅ RTL clean at iteration {i+1}")
            return rtl_code

        severity = validation["severity"]

        critical = [msg for lvl, msg in severity if lvl == "CRITICAL"]
        warnings = [msg for lvl, msg in severity if lvl == "WARNING"]

        # ==========================
        # 🔴 CRITICAL FIX LOOP
        # ==========================
        if critical:
            print(f"🚨 Critical Issues: {len(critical)}")

            if prev_critical_issues == critical:
                print("⛔ Repeating issues → stop")
                return rtl_code

            prev_critical_issues = critical

            correction_prompt = build_correction_prompt(
                original_prompt=prompt,
                rtl_code=rtl_code,
                issues=critical
            )

            correction_prompt += """
STRICT:
- Fix ALL critical issues
- Ensure correct bit-widths
- No truncation or overflow
"""

            rtl_code = _generate_once(model, tokenizer, correction_prompt)
            continue

        # ==========================
        # 🟡 WARNINGS → ACCEPT
        # ==========================
        if warnings:
            print("🟡 Only warnings → accept RTL")
            return rtl_code

        # ==========================
        # 🔵 COMPILATION FAIL
        # ==========================
        if not validation["compile_success"]:
            print("❌ Compile fail → retry")

            correction_prompt = build_correction_prompt(
                original_prompt=prompt,
                rtl_code=rtl_code,
                issues=[validation["compile_message"]]
            )

            rtl_code = _generate_once(model, tokenizer, correction_prompt)
            continue

        print("⚠️ Unknown issue → stop")
        return rtl_code

    print("⚠️ Max iterations reached")
    return rtl_code


# ==============================
# 3. 🔥 AI TESTBENCH GENERATOR (NEW)
# ==============================
def generate_testbench_with_ai(model, tokenizer, prompt, rtl_code):

    tb_prompt = f"""
You are an expert Verilog verification engineer.

Given the RTL design:

{rtl_code}

Task:
Generate a COMPLETE self-checking Verilog testbench.

Rules:
- Instantiate the DUT correctly
- Generate input stimulus (random or loop)
- Compute expected output using behavioral logic
- Compare DUT output with expected
- Print ONLY:
    FINAL_RESULT: PASS
    or
    FINAL_RESULT: FAIL
- Include:
    $dumpfile("temp/wave.vcd");
    $dumpvars(0, tb);
- Use delays (#1 or #5)
- Do NOT include explanations
- Return ONLY Verilog code

Testbench:
"""

    inputs = tokenizer(
        tb_prompt,
        return_tensors="pt"
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=600,
            do_sample=False
        )

    tb_code = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Clean artifacts
    tb_code = tb_code.replace("Ġ", " ")
    tb_code = tb_code.replace("Ċ", "\n")

    # Extract module tb
    match = re.search(r"module\s+tb[\s\S]*?endmodule", tb_code)

    if match:
        tb_code = match.group(0)

    return tb_code.strip()