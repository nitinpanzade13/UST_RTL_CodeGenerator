# # import gradio as gr
# # from model_loader import load_model
# # from rtl_generator import generate_rtl
# # from rtl_validator import validate_rtl

# # # Load model once at startup
# # model, tokenizer = load_model()


# # def run_rtl_pipeline(prompt):

# #     rtl_code = generate_rtl(model, tokenizer, prompt)
# #     validation = validate_rtl(rtl_code)

# #     return rtl_code, validation


# # interface = gr.Interface(
# #     fn=run_rtl_pipeline,
# #     inputs=gr.Textbox(
# #         lines=6,
# #         placeholder="Enter RTL design instruction..."
# #     ),
# #     outputs=[
# #         gr.Textbox(lines=20, label="Generated RTL Code"),
# #         gr.Textbox(lines=5, label="Validation Result")
# #     ],
# #     title="DeepSeek RTL Generator + Validator",
# #     description="Fine-tuned DeepSeek-Coder model for Verilog RTL generation"
# # )

# # if __name__ == "__main__":
# #     interface.launch()

# import gradio as gr
# from model_loader import load_model
# from rtl_generator import generate_rtl
# from rtl_validator import validate_rtl

# print("Loading model...")

# model, tokenizer = load_model()


# def rtl_pipeline(prompt):

#     rtl_code = generate_rtl(model, tokenizer, prompt)

#     validation = validate_rtl(rtl_code)

#     return rtl_code, validation


# interface = gr.Interface(
#     fn=rtl_pipeline,
#     inputs=gr.Textbox(
#         lines=4,
#         placeholder="Example: Design a 4-bit adder with carry-out"
#     ),
#     outputs=[
#         gr.Code(label="Generated RTL"),
#         gr.Textbox(label="Validation Result")
#     ],
#     title="AI RTL Generator",
#     description="DeepSeek fine-tuned model for Verilog RTL generation"
# )

# interface.launch()
import gradio as gr
from model_loader import load_model
from evaluate_pipeline import run_pipeline
import matplotlib.pyplot as plt
import os
from waveform_viewer import parse_vcd


# ==============================
# Load Model (ONLY ONCE)
# ==============================
print("Loading model...")
model, tokenizer = load_model()
print("Model loaded successfully!")


# ==============================
# Chart Generator
# ==============================
def create_chart(correct, total):
    try:
        correct = int(correct)
        total = int(total)
    except:
        correct, total = 0, 1

    wrong = max(total - correct, 0)

    fig = plt.figure()
    plt.bar(["Pass", "Fail"], [correct, wrong])
    plt.title("Verification Result")

    return fig


# ==============================
# Waveform Chart
# ==============================
def create_waveform_chart(vcd_path):
    import matplotlib.pyplot as plt
    import os

    if not vcd_path or not os.path.exists(vcd_path):
        return None

    signals = parse_vcd(vcd_path)

    if not signals:
        return None

    fig = plt.figure(figsize=(12, 5))

    offset = 0

    for name, values in signals.items():
        if not values:
            continue

        times = [t for t, v in values]

        # 🔥 normalize values to 0/1 (for clean digital look)
        vals = [(1 if v > 0 else 0) + offset for t, v in values]

        plt.step(times, vals, where="post")

        if times:
            plt.text(times[-1], offset, name, fontsize=9)

        offset += 2

    plt.title("📉 Digital Waveform")
    plt.xlabel("Time")
    plt.yticks([])

    return fig


# ==============================
# Save RTL
# ==============================
def save_rtl_to_file(rtl):
    os.makedirs("temp", exist_ok=True)
    path = "temp/generated_rtl.v"

    with open(path, "w") as f:
        f.write(rtl)

    return path


# ==============================
# Process Function
# ==============================
def process(prompt):
    result = run_pipeline(model, tokenizer, prompt)

    rtl = result.get("rtl", "")
    sim_output = result.get("simulation_output", result.get("error", ""))
    vcd_path = result.get("vcd_path", None)

    status = result.get("status", "Unknown")

    correct = 1 if "PASS" in status else 0
    total = 1

    accuracy_percent = 100 if correct == 1 else 0

    # Status badge
    if "PASS" in status:
        status_html = "<div class='status pass'>✅ PASS</div>"
        stats = "All tests passed successfully"
    else:
        status_html = "<div class='status fail'>❌ FAIL</div>"
        stats = "Some tests failed"

    chart = create_chart(correct, total)
    waveform_chart = create_waveform_chart(vcd_path)

    file_path = save_rtl_to_file(rtl)

    return (
        rtl,
        sim_output,
        status_html,
        accuracy_percent,
        stats,
        chart,
        waveform_chart,
        file_path
    )


# ==============================
# UI
# ==============================
with gr.Blocks(title="AI RTL Generator") as demo:

    gr.HTML("""
    <style>
    body {
        background: linear-gradient(135deg, #0f172a, #020617);
        font-family: 'Segoe UI', sans-serif;
    }

    .container {
        max-width: 1000px;
        margin: auto;
    }

    .card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(12px);
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    .title {
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        color: white;
    }

    .subtitle {
        text-align: center;
        color: #94a3b8;
        margin-bottom: 25px;
    }

    .status {
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        padding: 10px;
        border-radius: 10px;
    }

    .pass {
        color: #22c55e;
    }

    .fail {
        color: #ef4444;
    }

    button {
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
        color: white;
        font-weight: bold;
        border-radius: 12px !important;
        padding: 14px;
        font-size: 16px;
    }

    textarea {
        background: #020617 !important;
        color: #e2e8f0 !important;
    }
    </style>
    """)

    with gr.Column(elem_classes="container"):

        # Header
        gr.Markdown("""
        <div class="title">🚀 AI RTL Generator</div>
        <div class="subtitle">
        AI-powered hardware design + verification + waveform visualization
        </div>
        """)

        # Input
        with gr.Column(elem_classes="card"):
            prompt = gr.Textbox(
                label="🧠 Enter Prompt",
                placeholder="Design a 4-bit adder with carry-out",
                lines=2
            )
            run_btn = gr.Button("⚡ Generate & Verify")

        # Results
        with gr.Column(elem_classes="card"):
            status_html = gr.HTML()
            accuracy_bar = gr.Slider(0, 100, label="🎯 Accuracy (%)", interactive=False)
            stats_box = gr.Textbox(label="📊 Summary")
            chart = gr.Plot()

        # Waveform
        with gr.Column(elem_classes="card"):
            waveform_plot = gr.Plot(label="📉 Waveform Viewer")

        # Outputs
        with gr.Column(elem_classes="card"):
            rtl_output = gr.Textbox(label="🧾 Generated RTL", lines=15)
            sim_output = gr.Textbox(label="🧪 Simulation Output", lines=15)
            download_file = gr.File(label="⬇️ Download RTL")

        # Button action
        run_btn.click(
            process,
            inputs=prompt,
            outputs=[
                rtl_output,
                sim_output,
                status_html,
                accuracy_bar,
                stats_box,
                chart,
                waveform_plot,
                download_file
            ]
        )


# ==============================
# Launch
# ==============================
demo.launch(theme=gr.themes.Soft())