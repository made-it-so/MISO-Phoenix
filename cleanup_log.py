import re

# --- CONFIGURATION ---
INPUT_FILENAME = "chat_001.txt"
OUTPUT_FILENAME = f"{INPUT_FILENAME.split('.')[0]}_cleaned.txt"

def cleanup_chat_log(input_file, output_file):
    """
    Cleans the specific 'chat 1.txt' format and converts it to the
    simple 'user'/'model' delimited format.
    """
    print(f"--> Starting automatic cleanup of '{input_file}'...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Define the correct regular expression to find source tags.
        source_tag_regex = "\\"
        
        # 2. Remove the source tags.
        cleaned_content = re.sub(source_tag_regex, '', content)

        # 3. Heuristic: Split content by "Show thinking" which separates user/model turns
        turns = cleaned_content.split('Show thinking')

        # 4. Process the turns to reconstruct the conversation
        output_lines = []
        for i, turn in enumerate(turns):
            # The first block contains the header and first user prompt
            if i == 0:
                # Find the start of the actual conversation
                first_prompt_start = turn.find("I want this to be used for a CEO.")
                if first_prompt_start != -1:
                    user_prompt = turn[first_prompt_start:].strip()
                    output_lines.append("user")
                    output_lines.append(user_prompt)
            else:
                # Subsequent blocks contain a model answer, then the next user prompt
                # We assume a significant gap of newlines separates them
                parts = turn.split('\n\n\n')
                model_response = parts[0].strip()
                
                output_lines.append("model")
                output_lines.append(model_response)
                
                if len(parts) > 1:
                    next_user_prompt = "\n".join(part.strip() for part in parts[1:]).strip()
                    if next_user_prompt:
                        output_lines.append("user")
                        output_lines.append(next_user_prompt)

        # 5. Write the cleaned content to the new file, separated by double newlines
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(output_lines))

        print(f"--> SUCCESS: Cleanup complete. Clean file saved as '{output_file}'.")

    except FileNotFoundError:
        print(f"--> ERROR: The file '{input_file}' was not found.")
    except Exception as e:
        print(f"--> ERROR: An unexpected error occurred: {repr(e)}")

if __name__ == "__main__":
    cleanup_chat_log(INPUT_FILENAME, OUTPUT_FILENAME)