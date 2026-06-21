import asyncio
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    print(f"OpenRouter Key (first 6 chars): {api_key[:6]}...")
    
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    
    print("Testing DeepSeek on OpenRouter...")
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[
                    {"role": "user", "content": "Say hello in one word."}
                ],
                temperature=0.2
            ),
            timeout=30.0
        )
        print(f"DeepSeek Success: {response.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"DeepSeek Failed: {e}")
        
    print("\nTesting GPT-4o on OpenRouter...")
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="openai/gpt-4o",
                messages=[
                    {"role": "user", "content": "Say hello in one word."}
                ],
                temperature=0.2
            ),
            timeout=30.0
        )
        print(f"GPT-4o Success: {response.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"GPT-4o Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
