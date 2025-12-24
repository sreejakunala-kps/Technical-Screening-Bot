import requests
import json

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"

def query_gemini(prompt: str, api_key: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    response = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    data = response.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]
