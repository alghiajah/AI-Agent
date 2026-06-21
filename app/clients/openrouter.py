from openai import AsyncOpenAI
import asyncio
from app.config import settings

# Initialize AsyncOpenAI client with OpenRouter's base URL and headers
openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openrouter_api_key,
    default_headers={
        "HTTP-Referer": "https://github.com/fastapi-multi-agent-orchestrator",
        "X-Title": "FastAPI Multi-Agent Orchestrator",
    }
)

async def openrouter_completion_with_fallback(
    messages: list,
    model: str,
    temperature: float = 0.2,
    max_tokens: int = 1000,
    timeout: float = 120.0
) -> tuple[str, str]:
    """
    Executes a chat completion on OpenRouter. If the primary model fails
    (due to rate limits, credits, or other API issues), it falls back
    to a list of free models.
    Returns a tuple of (completed_text, model_name_used).
    """
    # Primary model followed by free fallback models
    models_to_try = [
        model,
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemma-4-31b-it:free",
        "openrouter/free"
    ]
    
    # De-duplicate while preserving order
    seen = set()
    unique_models = []
    for m in models_to_try:
        if m and m not in seen:
            seen.add(m)
            unique_models.append(m)
            
    last_err = None
    for i, current_model in enumerate(unique_models):
        try:
            print(f"[OpenRouter Fallback] Mencoba model: {current_model}")
            # Gunakan timeout yang lebih pendek untuk model fallback agar tidak menggantung terlalu lama
            current_timeout = timeout if i == 0 else min(timeout, 20.0)
            response = await asyncio.wait_for(
                openrouter_client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
                timeout=current_timeout
            )
            if response.choices and response.choices[0].message.content:
                content = response.choices[0].message.content.strip()
                print(f"[OpenRouter Fallback] Berhasil menggunakan model: {current_model}")
                return content, current_model
        except Exception as e:
            last_err = e
            print(f"[OpenRouter Fallback Warning] Model '{current_model}' gagal: {e}")
            continue
            
    # Final fallback: Jika semua model OpenRouter gagal (misalnya karena saldo habis),
    # coba gunakan API direct Gemini sebagai penyelamat akhir.
    try:
        print("[OpenRouter Fallback] Mencoba direct Gemini API sebagai penyelamat terakhir...")
        import google.generativeai as genai
        system_instruction = ""
        user_content = ""
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                user_content = msg["content"]
        
        gemini_model_name = "gemini-2.5-flash"
        model_inst = genai.GenerativeModel(
            model_name=gemini_model_name,
            system_instruction=system_instruction
        )
        response = await asyncio.wait_for(
            model_inst.generate_content_async(contents=user_content),
            timeout=timeout
        )
        if response.text:
            content = response.text.strip()
            print(f"[OpenRouter Fallback] Sukses menggunakan direct Gemini API ({gemini_model_name})!")
            return content, f"direct-{gemini_model_name}"
    except Exception as gemini_err:
        print(f"[OpenRouter Fallback Warning] Direct Gemini API gagal: {gemini_err}")
            
    if last_err:
        raise last_err
    raise Exception("Semua model OpenRouter gagal tanpa error spesifik.")

