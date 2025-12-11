import re
import random

def solve(input_str):
    """
    Generates a haiku (5-7-5 syllables) from a given input string.
    The code is self-contained and uses a heuristic for syllable counting.
    """

    def count_syllables(word):
        """A heuristic-based function to count syllables in a word."""
        word = word.lower().strip()
        if not word:
            return 0

        # Simple cases and exceptions
        if len(word) <= 3:
            return 1
        
        # Remove silent 'e' at the end, but not for 'le' endings
        if word.endswith('e') and not word.endswith('le'):
            word = word[:-1]

        vowel_groups = re.findall('[aeiouy]+', word)
        count = len(vowel_groups)
        
        # A word must have at least one syllable
        return max(1, count)

    def generate_line(target_syllables, syllable_map, used_words):
        """Tries to generate a single line of the haiku with a target syllable count."""
        max_retries = 200
        for _ in range(max_retries):
            line = []
            line_used_words = set()
            syllables_remaining = target_syllables

            max_words_in_line = 5 # Prevent lines with too many small words
            while syllables_remaining > 0 and len(line) < max_words_in_line:
                possible_counts = sorted(
                    [c for c in syllable_map if c <= syllables_remaining],
                    reverse=True
                )

                if not possible_counts:
                    break # Dead end, this attempt fails

                word_found_this_step = False
                for count in possible_counts:
                    available_words = [
                        w for w in syllable_map.get(count, [])
                        if w not in used_words and w not in line_used_words
                    ]
                    
                    if available_words:
                        chosen_word = random.choice(available_words)
                        line.append(chosen_word)
                        line_used_words.add(chosen_word)
                        syllables_remaining -= count
                        word_found_this_step = True
                        break # Word found, move to next step in the line
                
                if not word_found_this_step:
                    break # Dead end for this attempt
            
            if syllables_remaining == 0:
                return line # Success!

        return None # Failed to generate a line after all retries

    # 1. Preprocess the input text
    clean_text = re.sub(r'[^a-zA-Z\s]', '', input_str).lower()
    words = list(set(w for w in clean_text.split() if len(w) > 0))

    if len(words) < 5:
        return "Input text is too short. Please provide more words."

    # 2. Build a map of syllable counts to words
    syllable_map = {}
    for word in words:
        s_count = count_syllables(word)
        if 0 < s_count <= 7: # Ignore words too long for any line
            if s_count not in syllable_map:
                syllable_map[s_count] = []
            syllable_map[s_count].append(word)

    if not syllable_map or 1 not in syllable_map:
        return "Could not find enough usable words (especially 1-syllable words) to form a haiku."

    # 3. Generate the haiku line by line
    haiku_lines = []
    used_words = set()
    syllable_pattern = [5, 7, 5]

    for count in syllable_pattern:
        line_words = generate_line(count, syllable_map, used_words)
        
        if line_words is None:
            return "Failed to generate a complete haiku from the provided text. Try a different text."
        
        # Format the line and update used words
        line_str = " ".join(line_words)
        haiku_lines.append(line_str[0].upper() + line_str[1:])
        used_words.update(line_words)
        
    return "\n".join(haiku_lines)