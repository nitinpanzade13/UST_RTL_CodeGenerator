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
