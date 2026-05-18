import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

BASE_MODEL = "deepseek-ai/deepseek-coder-6.7b-instruct"
RTL_ADAPTER = "nitinpanzade13/deepseek-rtl-lora"
TB_ADAPTER = "nitinpanzade13/deepseek-tb-lora"


def load_model():
    print("Checking for CUDA availability...")
    if torch.cuda.is_available():
        print("CUDA is available. Using GPU.")
    else:
        print("CUDA is not available. Using CPU.")

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token

    print("Loading base model (4-bit)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        llm_int8_enable_fp32_cpu_offload=True
    )

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        max_memory={0: "5GB", "cpu": "16GB"}
    )

    print("Loading RTL LoRA adapter...")
    model = PeftModel.from_pretrained(
        model,
        RTL_ADAPTER,
        adapter_name="rtl"
    )

    print("Loading TB LoRA adapter...")
    model.load_adapter(TB_ADAPTER, adapter_name="testbench")

    # Start with RTL adapter active
    model.set_adapter("rtl")

    model.eval()
    print("Model loaded successfully!")
    return model, tokenizer


def use_rtl_adapter(model):
    model.set_adapter("rtl")


def use_tb_adapter(model):
    model.set_adapter("testbench")