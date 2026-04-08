import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

BASE_MODEL = "deepseek-ai/deepseek-coder-6.7b-instruct"
LORA_MODEL = "nitinpanzade13/deepseek-rtl-lora"  

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def load_model():

    # Check CUDA availability at startup
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

    print("Loading LoRA adapter...")
    model = PeftModel.from_pretrained(model, LORA_MODEL)

    model.eval()

    print("Model loaded successfully!")
    return model, tokenizer