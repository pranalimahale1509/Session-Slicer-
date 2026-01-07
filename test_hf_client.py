from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HUGGINGFACE_API_KEY")
model = "meta-llama/Llama-3.2-3B-Instruct"

print(f"Testing InferenceClient with model: {model}")

client = InferenceClient(token=api_key)

try:
    print("Sending chat_completion request...")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "when to drink water"}
    ]
    response = client.chat_completion(
        messages=messages,
        model=model,
        max_tokens=300,
        temperature=0.7
    )
    print("Response received!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
