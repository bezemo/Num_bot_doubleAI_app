# run_deepseek.py  – FastAPI-обёртка над моделью
import os
from fastapi import FastAPI
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_PATH = os.getenv("MODEL_PATH", "/app")   # папка с весами
DEVICE = os.getenv("DEVICE", "cpu")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2000))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))

app = FastAPI()

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16 if "cuda" in DEVICE else torch.float32,
    trust_remote_code=True
).to(DEVICE)
model.eval()


@app.post("/v1/chat/completions")
def chat_completions(req: dict):
    """
    OpenAI-совместимый энд-поинт.
    Пример запроса:
    {
      "model": "deepseek-chat",
      "messages": [{"role": "user", "content": "Ты нумеролог. Расскажи о числе 5"}],
      "max_tokens": 2000,
      "temperature": 0.7
    }
    """
    messages = req.get("messages", [])
    max_tokens = req.get("max_tokens", MAX_TOKENS)
    temperature = req.get("temperature", TEMPERATURE)

    prompt = "\n".join([m["content"] for m in messages])
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    full_text = tokenizer.decode(out[0], skip_special_tokens=True)
    answer = full_text[len(tokenizer.decode(inputs.input_ids[0], skip_special_tokens=True)) :].strip()

    return {
        "choices": [{"message": {"content": answer, "role": "assistant"}}],
        "model": "deepseek-chat",
        "usage": {}
    }