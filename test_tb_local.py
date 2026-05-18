import torch
from model_loader import load_model, use_tb_adapter, use_rtl_adapter

model, tokenizer = load_model()

rtl_code = """module mux4to1(
    input [3:0] in,
    input [1:0] sel,
    output reg out
);
always @(*) begin
    case(sel)
        2'b00: out = in[0];
        2'b01: out = in[1];
        2'b10: out = in[2];
        2'b11: out = in[3];
    endcase
end
endmodule"""

prompt = f"""### Instruction:
Write a complete self-checking Verilog testbench for the following RTL module:

{rtl_code}

### Response:
module tb;"""

# Switch to TB adapter
use_tb_adapter(model)

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=600,
        do_sample=False,
        repetition_penalty=1.1
    )

# Switch back to RTL
use_rtl_adapter(model)

decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
decoded = decoded.replace("Ġ", " ").replace("Ċ", "\n")

if "### Response:" in decoded:
    decoded = "module tb;" + decoded.split("### Response:")[-1]

print("=" * 60)
print(decoded)
print("=" * 60)
