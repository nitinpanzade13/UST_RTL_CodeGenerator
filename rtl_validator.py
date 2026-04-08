# import re


# def validate_rtl(code):

#     issues = []

#     if "module" not in code:
#         issues.append("Missing 'module' declaration.")

#     if "endmodule" not in code:
#         issues.append("Missing 'endmodule'.")

#     if re.search(r"\balways\b", code) is None:
#         issues.append("No always block detected.")

#     if re.search(r";\s*$", code, re.MULTILINE) is None:
#         issues.append("Possible missing semicolons.")

#     if len(issues) == 0:
#         return "✅ RTL looks syntactically reasonable."

#     return "⚠ Issues detected:\n" + "\n".join(issues)
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