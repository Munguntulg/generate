from ollama import chat

EXTRACT_PROMPT = """
Extract all action items and decisions from the text below. 
Output in strict JSON array format like:
[{"who":"", "action":"", "due":"", "confidence":0.0}]
"""

def extract_actions(text: str):
    response = chat(model="mistral", messages=[
        {"role": "system", "content": EXTRACT_PROMPT},
        {"role": "user", "content": text}
    ])
    return response["message"]["content"]
