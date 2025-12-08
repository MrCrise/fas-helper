"""
Файл для локального тестирования работоспособности API.
"""

import requests
import json

url = "http://localhost:8000/api/chat"
payload = {
    "query": "Реклама на фасадах зданий",
    "history": [],
}

print(f"Sending query to {url}")

try:
    with requests.post(url, json=payload, stream=True) as r:
        r.raise_for_status()
        
        for line in r.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    
                    if data['type'] == 'sources':
                        items = data['data']['items']
                        print(f"\n[DOCS]: Found {len(items)} documents.")
                        for doc in items:
                            print(f"- {doc.get('doc_id')} (score: {doc.get('score'):.2f})")
                            print(f"  url: {doc.get('url')}")
                        print("\n[LLM Answer]: ", end="")
                        
                    elif data['type'] == 'token':
                        print(data['data'], end="", flush=True)
                        
                    elif data['type'] == 'error':
                        print(f"\n[ERROR]: {data['data']}")
                        
                except json.JSONDecodeError:
                    print(f"JSON parsing error: {line}")
                    
    print("\n--- END ---")

except Exception as e:
    print(f"\nCritical error: {e}")