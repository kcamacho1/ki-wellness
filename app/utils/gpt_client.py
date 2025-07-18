# app/utils/gpt_client.py
import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")  # Use OpenRouter if you prefer

async def basic_nutrition_prompt(prompt: str) -> dict:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()
        return eval(content) if content.startswith("{") else {}
    except Exception as e:
        print(f"[OpenAI] Error: {e}")
        return {}
