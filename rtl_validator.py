import subprocess
import tempfile
import os
import re


# ==============================
# 1. Extract RTL Modules
# ==============================
def extract_modules(code):
    return re.findall(r"module[\s\S]*?endmodule", code)


# ==============================
# 2. Compilation Check (Icarus)
# ==============================
def compile_rtl(code):
    modules = extract_modules(code)

    if not modules:
        return False, "❌ Invalid RTL: No module found."

    combined_code = "\n\n".join(modules)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".v", mode="w") as f:
        f.write(combined_code)
        filename = f.name

    try:
        result = subprocess.run(
            ["iverilog", filename],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return True, "✅ RTL compiled successfully"

        return False, result.stderr

    finally:
        os.remove(filename)

# ==============================
# 3. Icarus Linter (-Wall)
# ==============================
def run_linter(code):
    modules = extract_modules(code)

    if not modules:
        return ""

    combined_code = "\n\n".join(modules)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".v", mode="w") as f:
        f.write(combined_code)
        filename = f.name

    try:
        result = subprocess.run(
            ["iverilog", "-Wall", "-tnull", filename],
            capture_output=True,
            text=True
        )

        return result.stderr + result.stdout

    finally:
        os.remove(filename)


# ==============================
# 4. Verilator Linter
# ==============================
def run_verilator_lint(code):
    modules = extract_modules(code)

    if not modules:
        return ""

    combined_code = "\n\n".join(modules)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".v", mode="w") as f:
        f.write(combined_code)
        filename = f.name

    try:
        result = subprocess.run(
            ["verilator", "--lint-only", filename],
            capture_output=True,
            text=True
        )

        return result.stderr + result.stdout

    except FileNotFoundError:
        return "⚠️ Verilator not installed."

    finally:
        os.remove(filename)


# ==============================
# 5. Detect Issues
# ==============================
def detect_lint_errors(lint_output):
    keywords = [
        "out of range",
        "out-of-range",
        "width mismatch",
        "truncated",
        "overflow",
        "bit select",
        "implicit",
        "unused",
        "undriven"
    ]

    issues = []

    for line in lint_output.lower().split("\n"):
        if any(k in line for k in keywords):
            issues.append(line.strip())

    return list(set(issues))  # remove duplicates


# ==============================
# 6. Severity Classification
# ==============================
def classify_severity(issues):
    classified = []

    for issue in issues:
        issue_lower = issue.lower()

        if any(k in issue_lower for k in [
            "out of range",
            "width mismatch",
            "truncated",
            "overflow",
            "bit select"
        ]):
            classified.append(("CRITICAL", issue))

        elif any(k in issue_lower for k in [
            "unused",
            "implicit",
            "undriven"
        ]):
            classified.append(("WARNING", issue))

        else:
            classified.append(("INFO", issue))

    return classified


# ==============================
# 7. Build Correction Prompt
# ==============================
def build_correction_prompt(original_prompt, rtl_code, issues):
    issues_text = "\n".join(issues)

    return f"""
You are an expert Verilog RTL designer.

Task:
{original_prompt}

The following RTL has hardware-critical issues detected by linters:

=== LINTER WARNINGS ===
{issues_text}

=== INCORRECT RTL ===
{rtl_code}

=== FIXING RULES ===
- Do NOT access out-of-range bits
- Fix all width mismatches
- Do NOT truncate carry bits
- Remove unused signals
- For adders, ALWAYS use:
  {{cout, sum}} = a + b + cin;
- Ensure bit-width correctness everywhere
- Output ONLY corrected Verilog code
- Do NOT add explanations

=== CORRECTED RTL ===
"""


# ==============================
# 8. Combined Validation (FINAL)
# ==============================
def validate_rtl_full(code):
    # Compile Check
    compile_ok, compile_msg = compile_rtl(code)

    # Run both linters
    iverilog_out = run_linter(code)
    verilator_out = run_verilator_lint(code)

    combined_output = iverilog_out + "\n" + verilator_out

    # Detect issues
    issues = detect_lint_errors(combined_output)

    # Classify severity
    classified = classify_severity(issues)

    # Check critical
    has_critical = any(level == "CRITICAL" for level, _ in classified)

    return {
        "compile_success": compile_ok,
        "compile_message": compile_msg,
        "lint_output": combined_output,
        "lint_issues": issues,
        "severity": classified,
        "has_critical": has_critical,
        "is_clean": compile_ok and not has_critical
    }


# ==============================
# 9. Backward Compatibility
# ==============================
def validate_rtl(code):
    result = validate_rtl_full(code)

    if result["compile_success"]:
        if result["lint_issues"]:
            return "⚠️ LINT Issues:\n" + "\n".join(result["lint_issues"])
        return "✅ RTL compiled successfully"

    return f"❌ Compilation Error:\n{result['compile_message']}"
