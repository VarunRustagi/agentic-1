
import os
import litellm
from dotenv import load_dotenv

load_dotenv()
litellm.use_litellm_proxy = True
litellm._turn_on_debug()

api_base = os.getenv("LITELLM_PROXY_API_BASE")
api_key = os.getenv("LITELLM_PROXY_GEMINI_API_KEY")

print(f"API Base: {api_base}")
print(f"API Key: {api_key[:5]}...")

try:
    response = litellm.completion(
        model="hackathon-gemini-2.5-flash", 
        api_base=api_base,
        api_key=api_key,
        messages=[{"role": "user", "content": "Hello, are you working?"}]
    )
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
