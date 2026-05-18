import torch
import os
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
    module_match = re.search(r"\bmodule\s+(\w+)\b", rtl_code)
    dut_module_name = module_match.group(1) if module_match else "dut"

    tb_prompt = f"""You are an expert Verilog verification engineer.

Given the RTL design:

{rtl_code}

Task:
Generate a COMPLETE, multiline, self-checking Verilog testbench.

REQUIRED:
1. Module name MUST be tb
2. Use valid Verilog syntax with real newlines and indentation
3. Instantiate DUT with explicit named port mapping (no placeholders)
    - DUT module name MUST be: {dut_module_name}
    - Do NOT use module name 'dut' unless DUT is actually named dut
4. Declare all DUT-connected signals before instantiation
5. Generate deterministic stimulus in an initial block
6. Compute expected output and compare with DUT output
7. Include integer error counter and increment on mismatch
8. MUST include BOTH:
    - module tb ... endmodule
    - FINAL_RESULT: PASS or FINAL_RESULT: FAIL print
9. MUST include:
    - $dumpfile("temp/wave.vcd");
    - $dumpvars(0, tb);
10. Use delays and proper timing
11. Do NOT output placeholders like output_correct, dut_instance, // test logic here

STRICT FAIL CONDITIONS (avoid these):
- Single-line testbench with no newlines
- Undeclared identifiers
- Missing endmodule
- Placeholder text

REQUIRED OUTPUT FORMAT:
module tb;
    // declarations
    dut_instance (.port(signal), ...);
    
    initial begin
        $dumpfile("temp/wave.vcd");
        $dumpvars(0, tb);
        // test logic here
        
        if (output_correct)
            $display("FINAL_RESULT: PASS");
        else
            $display("FINAL_RESULT: FAIL");
        $finish;
    end
endmodule

IMPORTANT: Return ONLY the testbench code between START_TB and END_TB.

START_TB
module tb;
    // declarations
    {dut_module_name} dut_instance (.port(signal), ...);
    
    initial begin
        $dumpfile(\"temp/wave.vcd\");
        $dumpvars(0, tb);
        // test logic here
        
        if (output_correct)
            $display(\"FINAL_RESULT: PASS\");
        else
            $display(\"FINAL_RESULT: FAIL\");
        $finish;
    end
endmodule
END_TB

Testbench code:
"""

    def extract_best_module(raw_text):
        tb_code = raw_text.replace("Ġ", " ").replace("Ċ", "\n")
        # Normalize missing whitespace from some decodes (e.g., "moduletb").
        tb_code = re.sub(r"\bmodule(?=\w)", "module ", tb_code)
        tb_code = re.sub(r"\bendmodule\b", "endmodule\n", tb_code)
        tb_code = tb_code.replace("START_TB", "START_TB\n").replace("END_TB", "\nEND_TB")
        tb_code = tb_code.replace("```verilog", "").replace("```", "")

        # Remove direct prompt echo of the DUT RTL when present.
        if rtl_code.strip() and rtl_code.strip() in tb_code:
            tb_code = tb_code.replace(rtl_code.strip(), "")

        if "Testbench code:" in tb_code:
            tb_code = tb_code.split("Testbench code:")[-1]
        if "Testbench:" in tb_code:
            tb_code = tb_code.split("Testbench:")[-1]
        if "### Response:" in tb_code:
            tb_code = tb_code.split("### Response:")[-1]
        if "Response:" in tb_code:
            tb_code = tb_code.split("Response:")[-1]

        if "START_TB" in tb_code and "END_TB" in tb_code:
            tb_code = tb_code.split("START_TB", 1)[-1]
            tb_code = tb_code.split("END_TB", 1)[0]
        elif "START_TB" in tb_code:
            tb_code = tb_code.split("START_TB", 1)[-1]

        modules = re.findall(r"module\s+\w+\s*[\(#;][\s\S]*?endmodule", tb_code)
        if not modules:
            # If model emitted prose before code, trim to the first module token.
            first_module = re.search(r"\bmodule\s+\w+\b", tb_code)
            if first_module:
                return tb_code[first_module.start():].strip()
            return ""

        # Strong preference: actual testbench module names only.
        tb_named_modules = []
        for mod in modules:
            name_match = re.search(r"module\s+(\w+)", mod)
            name = name_match.group(1).lower() if name_match else ""
            if name in {"tb", "testbench", "tb_module"} or "tb" in name:
                tb_named_modules.append(mod)

        if not tb_named_modules:
            # If the model only echoed the DUT module, ignore it and force regeneration.
            for mod in modules:
                name_match = re.search(r"module\s+(\w+)", mod)
                name = name_match.group(1) if name_match else ""
                if name.lower() == dut_module_name.lower():
                    return ""
            # Otherwise, avoid non-testbench modules to reduce false positives.
            return ""

        candidate_modules = tb_named_modules

        def module_score(mod):
            name_match = re.search(r"module\s+(\w+)", mod)
            name = name_match.group(1).lower() if name_match else ""
            score = 0
            if name in {"tb", "testbench"}:
                score += 3
            if "FINAL_RESULT" in mod:
                score += 2
            if "$dumpvars" in mod and "$dumpfile" in mod:
                score += 1
            return (score, len(mod))

        return max(candidate_modules, key=module_score).strip()

    def is_good_tb(tb_code):
        has_module = re.search(r"\bmodule\s+\w+\b", tb_code) is not None
        has_endmodule = "endmodule" in tb_code
        first_name_match = re.search(r"\bmodule\s+(\w+)\b", tb_code)
        first_module_name = first_name_match.group(1).lower() if first_name_match else ""
        is_tb_named = first_module_name in {"tb", "testbench", "tb_module"} or "tb" in first_module_name
        has_checks = (
            "FINAL_RESULT" in tb_code
            or "$display" in tb_code
            or "assert" in tb_code
            or "if (" in tb_code
        )
        has_dump = "$dumpfile" in tb_code and "$dumpvars" in tb_code
        avoids_dut_module_decl = re.search(rf"\bmodule\s+{re.escape(dut_module_name)}\b", tb_code, re.IGNORECASE) is None
        no_placeholders = all(
            x not in tb_code.lower()
            for x in [
                "testlogichere",
                "placeholder",
            ]
        )
        substantial = len(tb_code) > 150 and tb_code.count("\n") > 5

        return (
            has_module
            and has_endmodule
            and is_tb_named
            and has_checks
            and has_dump
            and avoids_dut_module_decl
            and no_placeholders
            and substantial
        )

    attempt_prompt = tb_prompt
    best_good_tb = ""
    best_candidate_tb = ""

    debug_tb = os.environ.get("TB_DEBUG", "0") == "1"

    for attempt in range(3):
        inputs = tokenizer(
            attempt_prompt,
            return_tensors="pt"
        ).to(model.device)

        with torch.no_grad():
            gen_kwargs = {
                "max_new_tokens": 900,
                "do_sample": (attempt > 0),
            }
            if attempt > 0:
                gen_kwargs["temperature"] = 0.4
                gen_kwargs["top_p"] = 0.9

            outputs = model.generate(
                **inputs,
                **gen_kwargs
            )

        raw = tokenizer.decode(outputs[0], skip_special_tokens=True)
        tb_code = extract_best_module(raw)
        if debug_tb:
            print(f"\n[TB_DEBUG] Attempt {attempt + 1} raw output (first 500 chars):\n{raw[:500]}\n")
            print(f"[TB_DEBUG] Attempt {attempt + 1} extracted TB (first 500 chars):\n{tb_code[:500]}\n")
        if tb_code and len(tb_code) > len(best_candidate_tb):
            best_candidate_tb = tb_code
        if is_good_tb(tb_code):
            best_good_tb = tb_code if len(tb_code) > len(best_good_tb) else best_good_tb
            return best_good_tb

        attempt_prompt = f"""The previous testbench was invalid or too short.

Previous output:
{tb_code}

Regenerate a COMPLETE multiline Verilog testbench using module name tb.
It must include:
- explicit signal declarations
- DUT instantiation with named ports
- stimulus initial block
- expected-value check logic
- integer error counter
- $dumpfile and $dumpvars
- FINAL_RESULT PASS/FAIL prints
- Do NOT output the DUT RTL module declaration ({dut_module_name})

Return only the testbench between START_TB and END_TB.
Use DUT module name exactly: {dut_module_name}
START_TB
module tb;
    // declarations
    {dut_module_name} dut_instance (.port(signal), ...);
    initial begin
        $dumpfile(\"temp/wave.vcd\");
        $dumpvars(0, tb);
        // test logic here
        if (output_correct)
            $display(\"FINAL_RESULT: PASS\");
        else
            $display(\"FINAL_RESULT: FAIL\");
        $finish;
    end
endmodule
END_TB
"""

    if debug_tb:
        print("[TB_DEBUG] No valid TB produced; returning best candidate (if any).")
    # If no strict-valid testbench was produced, return the best candidate so Tier 1 can still evaluate it.
    return best_candidate_tb
