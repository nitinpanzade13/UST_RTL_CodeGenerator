
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
