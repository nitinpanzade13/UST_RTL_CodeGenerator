import json
from tqdm import tqdm

from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

from rtl_generator import generate_rtl
from rtl_validator import validate_rtl


BASE_MODEL = "deepseek-ai/deepseek-coder-6.7b-instruct"
LORA_PATH = "./deepseek_rtl_model"
DATASET_PATH = "rtl_dataset.jsonl"


print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

print("Loading base model...")
model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    device_map="auto",
    load_in_4bit=True
)

print("Loading LoRA adapter...")
model = PeftModel.from_pretrained(model, LORA_PATH)

print("Model ready.")


dataset = []
with open(DATASET_PATH) as f:
    for line in f:
        dataset.append(json.loads(line))


# Use only a test subset
test_data = dataset[:200]


success = 0

for sample in tqdm(test_data):

    prompt = sample["instruction"]

    rtl_code = generate_rtl(model, tokenizer, prompt)

    result = validate_rtl(rtl_code)

    if "successfully" in result:
        success += 1


accuracy = success / len(test_data)

print("\n========================")
print("Total Samples:", len(test_data))
print("Compiled Successfully:", success)
print("Compile Accuracy:", round(accuracy*100,2), "%")
print("========================")
