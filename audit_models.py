import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load keys from .env
load_dotenv()

KEYS = {
    "google": os.getenv("GEMINI_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "deepseek": os.getenv("DEEPSEEK_API_KEY"),
    "grok": os.getenv("GROK_API_KEY"),
}

async def check_google():
    key = KEYS["google"]
    if not key: return "Google", "Skipped (No Key)", "⚪"
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        async with httpx.AsyncClient() as client:
            res = await client.get(url)
            if res.status_code == 200:
                models = [m['name'].replace('models/', '') for m in res.json().get('models', []) if 'flash' in m['name'] or 'pro' in m['name']]
                return "Google", f"Success ({len(models)} models found: {', '.join(models[:3])}...)", "🟢"
            return "Google", f"Error {res.status_code}: {res.text[:100]}", "🔴"
    except Exception as e: return "Google", str(e), "🔴"

async def check_openai():
    key = KEYS["openai"]
    if not key: return "OpenAI", "Skipped (No Key)", "⚪"
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {key}"})
            if res.status_code == 200:
                models = [m['id'] for m in res.json()['data'] if 'gpt-4' in m['id']]
                return "OpenAI", f"Success ({len(models)} models found: {', '.join(models[:3])}...)", "🟢"
            return "OpenAI", f"Error {res.status_code}", "🔴"
    except Exception as e: return "OpenAI", str(e), "🔴"

async def check_anthropic():
    key = KEYS["anthropic"]
    if not key: return "Anthropic", "Skipped (No Key)", "⚪"
    # Anthropic doesn't have a simple public 'list models' endpoint that is widely open, 
    # but we can test a generation to prove access.
    return "Anthropic", "Manual Check Required (Check Dashboard)", "🟡"

async def check_deepseek():
    key = KEYS["deepseek"]
    if not key: return "DeepSeek", "Skipped (No Key)", "⚪"
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://api.deepseek.com/models", headers={"Authorization": f"Bearer {key}"})
            if res.status_code == 200:
                models = [m['id'] for m in res.json()['data']]
                return "DeepSeek", f"Success: {', '.join(models)}", "🟢"
            return "DeepSeek", f"Error {res.status_code}", "🔴"
    except Exception as e: return "DeepSeek", str(e), "🔴"

async def main():
    print(f"{'PROVIDER':<15} | {'STATUS':<50} | {'ACCESS'}")
    print("-" * 80)
    tasks = [check_google(), check_openai(), check_deepseek(), check_anthropic()]
    results = await asyncio.gather(*tasks)
    for provider, msg, icon in results:
        print(f"{provider:<15} | {msg:<50} | {icon}")

if __name__ == "__main__":
    asyncio.run(main())
