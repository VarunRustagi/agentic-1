#!/usr/bin/env python3
"""Test available models in LiteLLM proxy"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

API_BASE = os.getenv("LITELLM_PROXY_API_BASE")
API_KEY = os.getenv("LITELLM_PROXY_GEMINI_API_KEY")

print("Fetching available models from:", API_BASE)
print()

try:
    response = requests.get(
        f"{API_BASE.rstrip('/')}/models",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("Available models:")
        if 'data' in data:
            for model in data['data']:
                print(f"  - {model.get('id', model)}")
        else:
            print(data)
    else:
        print(f"Error {response.status_code}:")
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")

# Common model names to try
print("\nTrying common model names:")
common_models = [
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
    "gpt-4",
    "gpt-3.5-turbo"
]

import litellm
litellm.use_litellm_proxy = True

for model in common_models:
    try:
        response = litellm.completion(
            model=model,
            api_base=API_BASE,
            api_key=API_KEY,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        print(f"  ✓ {model} - WORKS!")
        break
    except Exception as e:
        error_msg = str(e)[:80]
        print(f"  ✗ {model} - {error_msg}")
