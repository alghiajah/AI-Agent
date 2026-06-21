import google.generativeai as genai
from app.config import settings

# Configure Google Generative AI SDK with the direct API key
genai.configure(api_key=settings.gemini_api_key)

def get_gemini_model(model_name: str = None) -> genai.GenerativeModel:
    """
    Initializes and returns a Gemini GenerativeModel instance.
    By default, uses the RESEARCHER_MODEL configured in settings.
    """
    name = model_name or settings.researcher_model
    return genai.GenerativeModel(name)
