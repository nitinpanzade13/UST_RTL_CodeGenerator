# import gradio as gr
# from model_loader import load_model
# from rtl_generator import generate_rtl
# from rtl_validator import validate_rtl

# # Load model once at startup
# model, tokenizer = load_model()


# def run_rtl_pipeline(prompt):

#     rtl_code = generate_rtl(model, tokenizer, prompt)
#     validation = validate_rtl(rtl_code)

#     return rtl_code, validation


# interface = gr.Interface(
#     fn=run_rtl_pipeline,
#     inputs=gr.Textbox(
#         lines=6,
#         placeholder="Enter RTL design instruction..."
#     ),
#     outputs=[
#         gr.Textbox(lines=20, label="Generated RTL Code"),
#         gr.Textbox(lines=5, label="Validation Result")
#     ],
#     title="DeepSeek RTL Generator + Validator",
#     description="Fine-tuned DeepSeek-Coder model for Verilog RTL generation"
# )

# if __name__ == "__main__":
#     interface.launch()

import gradio as gr
from model_loader import load_model
from rtl_generator import generate_rtl
from rtl_validator import validate_rtl

print("Loading model...")

model, tokenizer = load_model()


def rtl_pipeline(prompt):

    rtl_code = generate_rtl(model, tokenizer, prompt)

    validation = validate_rtl(rtl_code)

    return rtl_code, validation


interface = gr.Interface(
    fn=rtl_pipeline,
    inputs=gr.Textbox(
        lines=4,
        placeholder="Example: Design a 4-bit adder with carry-out"
    ),
    outputs=[
        gr.Code(label="Generated RTL"),
        gr.Textbox(label="Validation Result")
    ],
    title="AI RTL Generator",
    description="DeepSeek fine-tuned model for Verilog RTL generation"
)

interface.launch()