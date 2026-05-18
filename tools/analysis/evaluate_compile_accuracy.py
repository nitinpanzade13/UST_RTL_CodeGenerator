import json
import os
from tqdm import tqdm

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

from rtl_generator import generate_rtl
from rtl_validator import validate_rtl


# ======================================
# Configuration
# ======================================

BASE_MODEL = "deepseek-ai/deepseek-coder-6.7b-instruct"
LORA_PATH = "nitinpanzade13/deepseek-rtl-lora"
DATASET_PATH = "rtl_dataset.jsonl"

# HuggingFace cache location (Windows)
HF_CACHE = r"C:\Users\nitin\.cache\huggingface\hub"

TEST_SIZE = 50


# ======================================
# Check if model exists locally
# ======================================

def model_exists_locally():

    if not os.path.exists(HF_CACHE):
        return False

    for folder in os.listdir(HF_CACHE):
        if "deepseek-coder-6.7b-instruct" in folder:
            return True

    return False


print("Checking HuggingFace cache...")

LOCAL_ONLY = model_exists_locally()

if LOCAL_ONLY:
    print("✓ DeepSeek model found in cache")
else:
    print("Model not found locally → will download")


# ======================================
# Load Tokenizer
# ======================================

print("\nLoading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    BASE_MODEL,
    local_files_only=LOCAL_ONLY
)


# ======================================
# Quantization Configuration
# ======================================

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype="float16",
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True
)


# ======================================
# Load Base Model
# ======================================

print("Loading base model...")

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    quantization_config=bnb_config,
    device_map="auto",
    local_files_only=LOCAL_ONLY
)


# ======================================
# Load LoRA Adapter
# ======================================

print("Loading LoRA adapter...")

model = PeftModel.from_pretrained(
    model,
    LORA_PATH
)

print("✓ Model loaded successfully")


# ======================================
# Load Dataset
# ======================================

dataset = []

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    for line in f:
        dataset.append(json.loads(line))

print("\nTotal dataset size:", len(dataset))


# Use unseen prompts for testing
test_data = dataset[-TEST_SIZE:]

print("Evaluation samples:", len(test_data))


# ======================================
# Compile Accuracy Evaluation
# ======================================

success = 0
fail = 0

results = []

print("\nRunning compile accuracy evaluation...\n")

for sample in tqdm(test_data):

    prompt = sample["instruction"]

    # Generate RTL
    rtl_code = generate_rtl(model, tokenizer, prompt)

    # Validate RTL using Icarus Verilog
    result = validate_rtl(rtl_code)

    compiled = "successfully" in result.lower()

    if compiled:
        success += 1
    else:
        fail += 1

    results.append({
        "prompt": prompt,
        "compiled": compiled
    })


# ======================================
# Accuracy Calculation
# ======================================

accuracy = success / len(test_data)

print("\n================================")
print("Compile Accuracy Results")
print("================================")

print("Total Samples:", len(test_data))
print("Compiled Successfully:", success)
print("Compilation Failed:", fail)
print("Compile Accuracy:", round(accuracy * 100, 2), "%")

print("================================")


# ======================================
# Save Detailed Results
# ======================================

with open("compile_accuracy_results.json", "w") as f:
    json.dump(results, f, indent=4)

print("\nDetailed results saved to compile_accuracy_results.json")
