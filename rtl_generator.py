# import torch


# def generate_rtl(model, tokenizer, prompt):

#     formatted_prompt = f"""You are an expert RTL Verilog designer.

# ### Instruction:
# {prompt}

# ### Response:
# """

#     inputs = tokenizer(
#         formatted_prompt,
#         return_tensors="pt"
#     ).to(model.device)

#     with torch.no_grad():
#         outputs = model.generate(
#             **inputs,
#             max_new_tokens=300,
#             temperature=0.2,
#             top_p=0.95,
#             do_sample=True,
#             repetition_penalty=1.1
#         )
    

#     decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

#     # remove prompt
#     if "### Response:" in decoded:
#         decoded = decoded.split("### Response:")[-1]

#     # clean tokenizer artifacts
#     decoded = decoded.replace("Ġ", " ")
#     decoded = decoded.replace("Ċ", "\n")

#     return decoded.strip()

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