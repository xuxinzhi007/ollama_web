
from transformers import AutoTokenizer

model_name = "Qwen/Qwen2.5-1.5B-Instruct"
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
except Exception as e:
    print(f"Error loading tokenizer: {e}")
    exit(1)

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
]

formatted = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
print("--- Formatted Output ---")
print(formatted)
print("--- End Formatted Output ---")

print("\n--- Expected Output Pattern (ChatML) ---")
print("<|im_start|>system\n...<|im_end|>\n<|im_start|>user\n...<|im_end|>\n<|im_start|>assistant\n...<|im_end|>")
