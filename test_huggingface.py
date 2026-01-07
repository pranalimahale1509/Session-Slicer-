"""
Quick test script to verify Hugging Face API is working
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HUGGINGFACE_API_KEY")
model = "meta-llama/Llama-3.2-3B-Instruct"
api_url = f"https://api-inference.huggingface.co/models/{model}"

print(f"🧪 Testing Hugging Face API...")
print(f"  - API Key: {'✅ Found' if api_key else '❌ Missing'}")
print(f"  - Model: {model}")
print(f"  - URL: {api_url}")
print()

if not api_key:
    print("❌ No API key found! Check your .env file.")
    exit(1)

# Test request
headers = {"Authorization": f"Bearer {api_key}"}
payload = {
    "inputs": "Hello! Can you tell me a short productivity tip?",
    "parameters": {
        "max_new_tokens": 100,
        "temperature": 0.7,
        "return_full_text": False
    }
}

print("📡 Sending test request...")
try:
    response = requests.post(api_url, headers=headers, json=payload, timeout=60)
    print(f"  - Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"  - Response Type: {type(result)}")
        print()
        print("✅ SUCCESS! API is working!")
        print()
        print("Response:")
        print("-" * 50)
        if isinstance(result, list) and len(result) > 0:
            print(result[0].get("generated_text", result))
        elif isinstance(result, dict):
            print(result.get("generated_text", result))
        else:
            print(result)
        print("-" * 50)
    elif response.status_code == 503:
        print("⏳ Model is loading... This is normal for the first request.")
        print("   Wait 20-30 seconds and try again in the app!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
        
except requests.exceptions.Timeout:
    print("⏳ Request timed out - model is probably loading.")
    print("   This is normal! Wait a minute and try again.")
except Exception as e:
    print(f"❌ Error: {e}")
