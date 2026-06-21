import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Configure
api_key = os.environ.get("GEMINI_API_KEY")
print(f"API Key (first 6 chars): {api_key[:6]}...")
genai.configure(api_key=api_key)

try:
    print("Available models:")
    for m in genai.list_models():
        print(f"- {m.name} (supports: {m.supported_generation_methods})")
except Exception as e:
    print(f"Error listing models: {e}")
