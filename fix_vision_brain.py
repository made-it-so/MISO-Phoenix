import re
import os

file_path = "brain_functions.py"

with open(file_path, "r") as f:
    content = f.read()

# 1. FIX THE SIGNATURE (Handle 'async def')
# Change: async def execute_with_arbitrage(prompt): 
# To:     async def execute_with_arbitrage(prompt, image=None):
if "image=None" not in content:
    content = re.sub(
        r"(async\s+)?def\s+execute_with_arbitrage\s*\(\s*prompt\s*\):", 
        r"async def execute_with_arbitrage(prompt, image=None):", 
        content
    )
    print("Fixed function signature.")

# 2. INJECT VISION LOGIC
# We will look for the start of the function and inject the logic at the top of the try/except block
# or replace the old fallback logic if present.

vision_logic_block = """        except Exception as e:
            # [PATCHED] VISION + TEXT FALLBACK
            import os
            try:
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    # Decide Model & Payload based on Image presence
                    if image:
                        model = "gpt-4o"
                        messages = [
                            {
                                "role": "user", 
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}}
                                ]
                            }
                        ]
                        logic_msg = "Vision Circuit Breaker: Rerouted to GPT-4o"
                    else:
                        model = "gpt-3.5-turbo"
                        messages = [{"role": "user", "content": prompt}]
                        logic_msg = "Circuit Breaker: Rerouted to OpenAI"

                    # Direct call to OpenAI
                    fallback_response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "model": model,
                            "messages": messages,
                            "max_tokens": 500
                        },
                        timeout=30.0
                    )
                    
                    if fallback_response.status_code == 200:
                        return {
                            "answer": fallback_response.json()["choices"][0]["message"]["content"],
                            "confidence": 1.0,
                            "provider": f"openai-{model}",
                            "cost": 0.0,
                            "logic": logic_msg
                        }
            except Exception as fallback_error:
                print(f"Fallback failed: {fallback_error}")

            return {
                "answer": f"Arbitrage Failure: {str(e)}",
"""

# Find the old exception block and replace it entirely
# We search for the pattern "except Exception as e:" ... down to the return
pattern = r"except Exception as e:.*return\s+\{.*\"answer\":.*?\}"
content = re.sub(pattern, vision_logic_block, content, flags=re.DOTALL)

with open(file_path, "w") as f:
    f.write(content)

print("SUCCESS: brain_functions.py has been fully patched.")
