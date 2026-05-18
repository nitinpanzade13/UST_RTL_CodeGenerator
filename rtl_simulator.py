
# import subprocess
# import os


# def run_simulation(rtl_path, tb_path):
#     os.makedirs("temp", exist_ok=True)

#     output_file = "temp/out.vvp"
#     vcd_file = "temp/wave.vcd"

#     try:
#         # ==========================
#         # 1. CLEAN OLD FILES
#         # ==========================
#         if os.path.exists(output_file):
#             os.remove(output_file)

#         if os.path.exists(vcd_file):
#             os.remove(vcd_file)

#         # ==========================
#         # 2. COMPILE
#         # ==========================
#         compile_cmd = ["iverilog", "-o", output_file, rtl_path, tb_path]
#         compile_proc = subprocess.run(
#             compile_cmd,
#             capture_output=True,
#             text=True
#         )

#         if compile_proc.returncode != 0:
#             return {
#                 "success": False,
#                 "stage": "compile",
#                 "error": compile_proc.stderr
#             }

#         # ==========================
#         # 3. RUN SIMULATION
#         # ==========================
#         run_proc = subprocess.run(
#             ["vvp", output_file],
#             capture_output=True,
#             text=True
#         )

#         output = run_proc.stdout

#         # ==========================
#         # 4. DETECT PASS/FAIL
#         # ==========================
#         status = "PASS" if "FINAL_RESULT: PASS" in output else "FAIL"

#         # ==========================
#         # 5. CHECK VCD FILE
#         # ==========================
#         vcd_exists = os.path.exists(vcd_file)

#         return {
#             "success": True,
#             "status": status,
#             "output": output,
#             "vcd_path": vcd_file if vcd_exists else None
#         }

#     except Exception as e:
#         return {
#             "success": False,
#             "stage": "runtime",
#             "error": str(e)
#         }

import subprocess
import os
import re


UNSUPPORTED_SV_FEATURES = [
    (r"\bclass\b", "class"),
    (r"\bvirtual\s+interface\b", "virtual interface"),
    (r"\bprogram\b", "program block"),
    (r"\buvm_\w+\b", "UVM"),
    (r"\brand(?:omize)?\b", "randomize/rand"),
    (r"\bconstraint\b", "constraint block"),
]


def _find_unsupported_features(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
    except OSError:
        return []

    hits = []
    for pattern, label in UNSUPPORTED_SV_FEATURES:
        if re.search(pattern, code, flags=re.IGNORECASE):
            hits.append(label)

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(hits))


def run_simulation(rtl_path, tb_path):
    os.makedirs("temp", exist_ok=True)

    output_file = "temp/out.vvp"
    vcd_file = "temp/wave.vcd"

    try:
        # ==========================
        # 1. CLEAN OLD FILES
        # ==========================
        if os.path.exists(output_file):
            os.remove(output_file)

        if os.path.exists(vcd_file):
            os.remove(vcd_file)

        # ==========================
        # 2. Precheck Unsupported SV Features
        # ==========================
        unsupported = _find_unsupported_features(rtl_path) + _find_unsupported_features(tb_path)
        unsupported = list(dict.fromkeys(unsupported))

        if unsupported:
            return {
                "success": False,
                "stage": "precheck",
                "error": "Unsupported SystemVerilog features for Icarus: " + ", ".join(unsupported)
            }

        # ==========================
        # 3. COMPILE (SV-2012 enabled)
        # ==========================
        compile_cmd = ["iverilog", "-g2012", "-o", output_file, rtl_path, tb_path]
        compile_proc = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True
        )

        if compile_proc.returncode != 0:
            return {
                "success": False,
                "stage": "compile",
                "error": compile_proc.stderr + "\nCommand: " + " ".join(compile_cmd)
            }

        # ==========================
        # 4. RUN SIMULATION
        # ==========================
        run_proc = subprocess.run(
            ["vvp", output_file],
            capture_output=True,
            text=True
        )

        output = run_proc.stdout + run_proc.stderr

        # ==========================
        # 5. DETECT PASS/FAIL
        # ==========================
        if "FINAL_RESULT: PASS" in output:
            status = "PASS"
        elif "FINAL_RESULT: FAIL" in output:
            status = "FAIL"
        else:
            status = "UNKNOWN"

        # ==========================
        # 6. CHECK VCD FILE (ROBUST)
        # ==========================
        vcd_exists = os.path.exists(vcd_file) and os.path.getsize(vcd_file) > 0

        return {
            "success": True,
            "status": status,
            "output": output,
            "vcd_path": vcd_file if vcd_exists else None
        }

    except Exception as e:
        return {
            "success": False,
            "stage": "runtime",
            "error": str(e)
        }