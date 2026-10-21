import os
import httpx
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL")
print(f"Testing model: {model}")

r = httpx.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "model": model,
        "messages": [{"role": "user", "content": "respond JSON: {\"status\": \"ok\"}"}],
        "response_format": {"type": "json_object"}
    },
    timeout=10.0
)
print("HTTP status:", r.status_code)
print("Response:", r.text[:300])

# Also list models to see available models
r_models = httpx.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {api_key}"})
print("Models status:", r_models.status_code)
if r_models.status_code == 200:
    models_data = r_models.json().get("data", [])
    model_ids = [m["id"] for m in models_data]
    print("Available Groq models:", [m for m in model_ids if "llama" in m or "mixtral" in m or "qwen" in m or "gemma" in m][:10])
