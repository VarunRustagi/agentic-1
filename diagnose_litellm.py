#!/usr/bin/env python3
"""
LiteLLM Diagnostic Script
Tests the LiteLLM configuration and identifies BadGateway errors
"""

import os
from dotenv import load_dotenv
import litellm

# Load environment variables
load_dotenv()

print("="*70)
print("LiteLLM Configuration Diagnostic")
print("="*70)

# Check environment variables
print("\n1. Checking Environment Variables:")
API_BASE = os.getenv("LITELLM_PROXY_API_BASE")
API_KEY = os.getenv("LITELLM_PROXY_GEMINI_API_KEY")

print(f"   LITELLM_PROXY_API_BASE: {'✓ Set' if API_BASE else '✗ Missing'}")
if API_BASE:
    print(f"     → {API_BASE}")
    
print(f"   LITELLM_PROXY_GEMINI_API_KEY: {'✓ Set' if API_KEY else '✗ Missing'}")
if API_KEY:
    print(f"     → {API_KEY[:10]}...{API_KEY[-4:] if len(API_KEY) > 14 else ''}")

# Check litellm proxy configuration
print("\n2. Checking LiteLLM Proxy Configuration:")
litellm.use_litellm_proxy = True
print(f"   litellm.use_litellm_proxy: {litellm.use_litellm_proxy}")

# Test API call
print("\n3. Testing API Connection:")
if not API_BASE or not API_KEY:
    print("   ✗ Cannot test - missing environment variables")
    print("\n" + "="*70)
    print("SOLUTION:")
    print("="*70)
    print("Add the following to your .env file:")
    print("")
    print("LITELLM_PROXY_API_BASE=<your_litellm_proxy_url>")
    print("LITELLM_PROXY_GEMINI_API_KEY=<your_api_key>")
    print("")
    print("Example:")
    print("LITELLM_PROXY_API_BASE=https://your-proxy.com/v1")
    print("LITELLM_PROXY_GEMINI_API_KEY=sk-...")
    print("="*70)
else:
    try:
        print(f"   Attempting to call: {API_BASE}")
        response = litellm.completion(
            model="gemini-2.5-flash",
            api_base=API_BASE,
            api_key=API_KEY,
            messages=[
                {"role": "user", "content": "Say 'test successful' if you can read this."}
            ],
            max_tokens=10
        )
        print("   ✓ API call successful!")
        print(f"   Response: {response.choices[0].message.content}")
    except litellm.BadGatewayError as e:
        print(f"   ✗ BadGatewayError: {str(e)[:100]}")
        print("\n" + "="*70)
        print("DIAGNOSIS:")
        print("="*70)
        print("The LiteLLM proxy is unreachable or misconfigured.")
        print("Possible causes:")
        print("  1. Incorrect API_BASE URL")
        print("  2. Proxy server is down")
        print("  3. Network connectivity issues")
        print("  4. API key is invalid")
        print("\nRECOMMENDATION:")
        print("  - Verify the LITELLM_PROXY_API_BASE URL is correct")
        print("  - Check if the proxy server is running")
        print("  - Test with curl:")
        print(f"    curl -X POST {API_BASE}/chat/completions \\")
        print(f"      -H 'Authorization: Bearer {API_KEY[:10]}...' \\")
        print("      -H 'Content-Type: application/json'")
        print("="*70)
    except Exception as e:
        print(f"   ✗ Unexpected error: {type(e).__name__}")
        print(f"   {str(e)[:200]}")

print("\n" + "="*70)
print("FALLBACK SOLUTION:")
print("="*70)
print("The agents can work WITHOUT LiteLLM by using template-based summaries.")
print("To disable LLM calls, the agents will show metric-based insights only.")
print("="*70)
