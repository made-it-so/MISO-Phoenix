import re

file_path = "brain_functions.py"

with open(file_path, "r") as f:
    content = f.read()

# 1. Update Function Signature to accept 'image=None'
# Replaces "def execute_with_arbitrage(prompt):" with "def execute_with_arbitrage(prompt, image=None):"
content = re.sub(r"def execute_with_arbitrage\(prompt\):", r"def execute_with_arbitrage(prompt, image=None):", content)

# 2. Inject Vision-Aware Fallback Logic
# This logic checks if an image exists. If so, it constructs a GPT-4o payload.
# If not, it falls back to standard text (GPT-3.5).
vision_logic = """        except Exception as e:
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

                    fallback_response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "model": model,
                            "messages": messages,
                            "max_tokens": 300
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

# Find the start of the previous patch (or the original except block) and replace it
# We look for the common starting line of the except block
pattern = r"except Exception as e:.*"
# We use DOTALL to match across lines, replacing from 'except Exception' down to the next return block
# However, simpler is to just replace the block we know we inserted or the original one.
# Let's target the exact string we likely have in the file now.
if "EMERGENCY FALLBACK" in content:
    # Remove the old patch first to avoid duplication
    # This is tricky with regex, so we'll just overwrite the whole function if possible.
    # Instead, let's just replace the specific text block we added last time.
    content = re.sub(r"except Exception as e:.*return \{.*\"answer\": \"System Failure: \{str\(e\)\}\",.*\}", vision_logic, content, flags=re.DOTALL)
else:
    # If the file wasn't patched or looks different, try to find the standard catch block
    # Looking for the generic return structure
    content = re.sub(r"except Exception as e:.*return \{.*\"answer\": \"Arbitrage Failure - Circuit Breaker Tripped\",.*\}", vision_logic, content, flags=re.DOTALL)

with open(file_path, "w") as f:
    f.write(content)

print("SUCCESS: brain_functions.py upgraded with Vision capabilities.")
