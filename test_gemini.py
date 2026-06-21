import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

test_models = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash",
]

for model_name in test_models:
    try:
        print(f"Testing model: {model_name}...")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say hello in one word.")
        print(f"-> Success: {response.text.strip()}\n")
        break  # If one succeeds, we can use it!
    except Exception as e:
        print(f"-> Failed: {e}\n")
