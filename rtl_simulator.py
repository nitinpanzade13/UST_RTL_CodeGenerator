
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
        # 2. COMPILE
        # ==========================
        compile_cmd = ["iverilog", "-o", output_file, rtl_path, tb_path]
        compile_proc = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True
        )

        if compile_proc.returncode != 0:
            return {
                "success": False,
                "stage": "compile",
                "error": compile_proc.stderr
            }

        # ==========================
        # 3. RUN SIMULATION
        # ==========================
        run_proc = subprocess.run(
            ["vvp", output_file],
            capture_output=True,
            text=True
        )

        output = run_proc.stdout + run_proc.stderr

        # ==========================
        # 4. DETECT PASS/FAIL
        # ==========================
        if "FINAL_RESULT: PASS" in output:
            status = "PASS"
        elif "FINAL_RESULT: FAIL" in output:
            status = "FAIL"
        else:
            status = "UNKNOWN"

        # ==========================
        # 5. CHECK VCD FILE (ROBUST)
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