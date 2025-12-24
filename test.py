import requests
import json
import os

def query_gemini_api(prompt_text, api_key):
    """
    Sends a prompt to the Gemini API using a direct HTTP POST request.
    """

    gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"

    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ]
    }

    try:
        # 3. Make the POST request
        print(f"Sending request to gemini 2.5 pro...")
        response = requests.post(
            gemini_api_url, 
            headers=headers, 
            json=payload, 
            timeout=30
        )
        
        
        response.raise_for_status() 
        
        
        result = response.json()
        
        if 'candidates' in result and result['candidates']:
            generated_text = result['candidates'][0]['content']['parts'][0]['text']
            return generated_text
        else:
            return "No content generated. Check safety settings or prompt."

    except requests.exceptions.RequestException as e:
        return f"API Request Error: {e}"
    except (KeyError, IndexError) as e:
        return f"Response Parsing Error: {e} - Raw Response: {response.text}"


if __name__ == "__main__":

    API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBC7-w6LUFDxTUIQGZh34p4c3exuJpuQQY")

    if API_KEY == "YOUR_ACTUAL_API_KEY_HERE":
        print("Please set your GEMINI_API_KEY before running.")
    else:
        user_prompt = "Explain about list and tuples."
        
        response_text = query_gemini_api(user_prompt, API_KEY)
        
        print("-" * 30)
        print("Gemini Response:")
        print(response_text)
        print("-" * 30)