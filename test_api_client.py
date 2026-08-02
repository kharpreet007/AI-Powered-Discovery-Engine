import httpx
import json

def test_api():
    # 1. Health check
    print("--- 1. Testing /api/health ---")
    r = httpx.get("http://127.0.0.1:8000/api/health")
    print(r.json())
    
    # 2. Stats
    print("\n--- 2. Testing /api/stats ---")
    r = httpx.get("http://127.0.0.1:8000/api/stats")
    print(r.json())
    
    # 3. Chat (Streaming)
    print("\n--- 3. Testing /api/chat ---")
    print("Streaming RAG Response:")
    with httpx.stream("POST", "http://127.0.0.1:8000/api/chat", json={"question": "What is the most common frustration?"}, timeout=30.0) as r:
        for line in r.iter_lines():
            if line:
                print(line)

if __name__ == "__main__":
    test_api()
