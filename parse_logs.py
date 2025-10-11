import json
import re

# --- CONFIGURATION ---
# Update this to the name of your chat history file.
INPUT_FILENAME = "chat_001.txt"
# This will be the name of the structured output file.
OUTPUT_FILENAME = "parsed_log.jsonl"

def parse_chat_history(input_file, output_file):
    """
    Parses a raw text chat log into a structured JSONL file.
    Each line in the output file is a JSON object representing a turn.
    """
    print(f"--> Starting parsing of '{input_file}'...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split the content by the role delimiters ('user' or 'model')
        # The regex keeps the delimiters in the resulting list.
        turns = re.split(r'^(user|model)$', content, flags=re.MULTILINE)

        parsed_entries = []
        # Start from the first actual turn (the list will have an empty string at the beginning)
        for i in range(1, len(turns), 2):
            role = turns[i].strip()
            # Clean up the content by removing leading/trailing whitespace from each line and joining.
            message_content = "\n".join(line.strip() for line in turns[i+1].strip().split('\n')).strip()
            
            if message_content: # Only add if there is actual content
                parsed_entries.append({
                    "role": role,
                    "content": message_content
                })

        # Write the structured data to a JSONL file
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in parsed_entries:
                f.write(json.dumps(entry) + '\n')
        
        print(f"--> SUCCESS: Parsing complete. {len(parsed_entries)} entries written to '{output_file}'.")

    except FileNotFoundError:
        print(f"--> ERROR: The file '{input_file}' was not found. Please check the filename.")
    except Exception as e:
        print(f"--> ERROR: An unexpected error occurred: {e}")

if __name__ == "__main__":
    parse_chat_history(INPUT_FILENAME, OUTPUT_FILENAME)