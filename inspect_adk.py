
from google.adk.models.lite_llm import LiteLlm
import os
from dotenv import load_dotenv

load_dotenv()

try:
    model = LiteLlm(
        model="hackathon-gemini-2.5-flash", 
        api_base=os.getenv("LITELLM_PROXY_API_BASE"), 
        api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
    )
    print("LiteLlm instance methods:", dir(model))
except Exception as e:
    print(f"Instantiation failed: {e}")
