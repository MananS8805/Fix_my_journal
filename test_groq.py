import os
import sys
import traceback
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('GROQ_API_KEY')
print(f"GROQ_API_KEY found: {bool(api_key)}")

# Test 1: plain groq client
print("\n--- Test 1: Plain Groq client ---")
try:
    from groq import Groq
    client = Groq(api_key=api_key)
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "say hi"}],
        max_tokens=10,
    )
    print("SUCCESS:", r.choices[0].message.content)
except Exception as e:
    print("FAILED:", e)
    traceback.print_exc()

# Test 2: httpx with verify=False
print("\n--- Test 2: Groq with httpx verify=False ---")
try:
    import httpx
    from groq import Groq
    client2 = Groq(
        api_key=api_key,
        http_client=httpx.Client(
            timeout=httpx.Timeout(60.0),
            verify=False,
        )
    )
    r2 = client2.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "say hi"}],
        max_tokens=10,
    )
    print("SUCCESS:", r2.choices[0].message.content)
except Exception as e:
    print("FAILED:", e)
    traceback.print_exc()

# Test 3: raw httpx request
print("\n--- Test 3: Raw httpx request ---")
try:
    import httpx
    with httpx.Client(verify=False, timeout=30) as client3:
        resp = client3.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": "say hi"}],
                "max_tokens": 10,
            }
        )
        print("Status:", resp.status_code)
        print("Response:", resp.text[:200])
except Exception as e:
    print("FAILED:", e)
    traceback.print_exc()

# Test 4: proxy check
print("\n--- Test 4: Proxy / env check ---")
for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "NO_PROXY"]:
    val = os.getenv(key)
    print(f"{key} = {val if val else '(not set)'}")