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


def validate_rtl(code):

    # Extract ALL modules
    modules = re.findall(r"module[\s\S]*?endmodule", code)

    if not modules:
        return "❌ Invalid RTL: No module found."

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
            return "✅ RTL compiled successfully"

        return f"❌ Compilation Error:\n{result.stderr}"

    finally:
        os.remove(filename)