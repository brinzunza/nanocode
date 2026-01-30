import requests

url = "http://localhost:11434/api/generate"

payload = {
    "model": "llama3.2",
    "prompt": "Give me a trading strategy idea.",
    "stream": False
}

res = requests.post(url, json=payload)
print(res.json()["response"])

