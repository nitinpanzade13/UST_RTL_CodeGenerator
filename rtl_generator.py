
import torch
import re


def generate_rtl(model, tokenizer, prompt):

    formatted_prompt = f"""
You are an expert Verilog RTL engineer.

Generate COMPLETE Verilog code.

Rules:
- Return ONLY Verilog code
- Output must start with 'module'
- Output must end with 'endmodule'
- If submodules are used, include their module definitions.

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
            do_sample=False,
            temperature=0.1
        )

    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # remove tokenizer artifacts
    decoded = decoded.replace("Ġ", " ")
    decoded = decoded.replace("Ċ", "\n")

    # Strip prompt: only keep text after the last "Verilog:" delimiter
    if "Verilog:" in decoded:
        decoded = decoded.split("Verilog:")[-1]

    # Extract all modules (match only valid Verilog module declarations)
    modules = re.findall(r"module\s+\w+\s*[\(#;][\s\S]*?endmodule", decoded)

    # Deduplicate by module name, keeping the longest version
    if modules:
        unique = {}
        for m in modules:
            name = re.match(r"module\s+(\w+)", m).group(1)
            if name not in unique or len(m) > len(unique[name]):
                unique[name] = m
        decoded = "\n\n".join(unique.values())

    return decoded.strip()
