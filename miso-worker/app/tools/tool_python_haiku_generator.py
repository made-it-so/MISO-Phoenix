import random
import re
import collections

def solve(input_str):
    """
    Generates a haiku (5-7-5 syllables) from a given input string.

    The function tokenizes the input text, counts syllables for each unique word
    using a combination of a dictionary and a fallback heuristic, and then
    constructs three lines with the required 5, 7, and 5 syllables.
    """

    # A dictionary of common words and their syllable counts for accuracy.
    # This helps overcome the limitations of the heuristic syllable counter.
    SYLLABLE_DICT = {
        'the': 1, 'a': 1, 'of': 1, 'to': 1, 'in': 1, 'it': 1, 'is': 1, 'be': 1,
        'as': 1, 'at': 1, 'so': 1, 'we': 1, 'he': 1, 'she': 1, 'by': 1, 'or': 1,
        'on': 1, 'do': 1, 'if': 1, 'me': 1, 'my': 1, 'up': 1, 'an': 1, 'go': 1,
        'no': 1, 'us': 1, 'am': 1, 'are': 1, 'was': 1, 'were': 1, 'has': 1, 
        'have': 1, 'had': 1, 'will': 1, 'would': 1, 'shall': 1, 'should': 1,
        'can': 1, 'could': 1, 'may': 1, 'might': 1, 'must': 1, 'and': 1, 'but': 1,
        'for': 1, 'not': 1, 'yet': 1, 'sun': 1, 'sky': 1, 'moon': 1, 'tree': 1,
        'wind': 1, 'rain': 1, 'snow': 1, 'day': 1, 'night': 1, 'red': 1, 'blue': 1,
        'green': 1, 'white': 1, 'dark': 1, 'light': 1, 'cold': 1, 'warm': 1,
        'soft': 1, 'hard': 1, 'small': 1, 'big': 1, 'old': 1, 'new': 1, 'love': 1,
        'hate': 1, 'life': 1, 'death': 1, 'time': 1, 'world': 1, 'one': 1, 'all': 1,
        'see': 1, 'know': 1, 'think': 1, 'feel': 1, 'say': 1, 'make': 1, 'come': 1,
        'like': 1, 'look': 1, 'find': 1, 'work': 1, 'call': 1, 'try': 1, 'ask': 1,
        'need': 1, 'use': 1, 'way': 1, 'leaf': 1, 'leaves': 1, 'fire': 1, 'ice': 1,
        'water': 2, 'river': 2, 'ocean': 2, 'mountain': 2, 'forest': 2, 'winter': 2,
        'summer': 2, 'autumn': 2, 'morning': 2, 'evening': 2, 'yellow': 2, 'orange': 2,
        'purple': 2, 'silver': 2, 'golden': 2, 'quiet': 2, 'silent': 2, 'happy': 2,
        'always': 2, 'never': 2, 'about': 2, 'above': 2, 'after': 2, 'again': 2,
        'away': 2, 'because': 2, 'before': 2, 'below': 2, 'beside': 2, 'between': 2,
        'beyond': 2, 'during': 2, 'inside': 2, 'into': 2, 'over': 2, 'under': 2,
        'until': 2, 'upon': 2, 'without': 2, 'hello': 2, 'goodbye': 2, 'shadow': 2,
        'beautiful': 3, 'wonderful': 3, 'together': 3, 'forever': 3, 'remember': 3,
        'tomorrow': 3, 'yesterday': 3, 'happiness': 3, 'another': 3, 'example': 3,
        'melancholy': 4, 'information': 4, 'interesting': 4,
        'understanding': 5, 'serendipity': 5, 'imagination': 5
    }

    def count_syllables(word):
        word = word.lower().strip(".,!?;:")
        if not word:
            return 0
        if word in SYLLABLE_DICT:
            return SYLLABLE_DICT[word]

        # Heuristic for words not in the dictionary
        vowels = "aeiouy"
        count = 0
        if word[0] in vowels:
            count += 1
        for i in range(1, len(word)):
            if word[i] in vowels and word[i - 1] not in vowels:
                count += 1
        
        if word.endswith("e"):
            if len(word) > 2 and word.endswith("le") and word[-3] not in vowels:
                pass
            elif count > 1:
                count -= 1
        
        return max(1, count)

    def generate_line(target_syllables, syllable_map, used_words):
        patterns = {
            5: [[5], [1, 4], [4, 1], [2, 3], [3, 2], [1, 1, 3], [1, 3, 1], [3, 1, 1], 
                [2, 2, 1], [1, 2, 2], [2, 1, 2], [1, 1, 1, 2], [1, 2, 1, 1], [2, 1, 1, 1], 
                [1,1,1,1,1]],
            7: [[7], [5, 2], [2, 5], [4, 3], [3, 4], [6, 1], [1, 6], [3, 3, 1], [3, 1, 3], 
                [1, 3, 3], [2, 2, 3], [2, 3, 2], [3, 2, 2], [4, 2, 1], [1, 2, 4], [4, 1, 2]]
        }

        if target_syllables not in patterns:
            return None, None
            
        shuffled_patterns = random.sample(patterns[target_syllables], len(patterns[target_syllables]))
        
        for pattern in shuffled_patterns:
            line_words = []
            temp_used_words = set(used_words)
            possible = True
            for syl_count in pattern:
                available_words = [w for w in syllable_map.get(syl_count, []) if w not in temp_used_words]
                if not available_words:
                    possible = False
                    break
                chosen_word = random.choice(available_words)
                line_words.append(chosen_word)
                temp_used_words.add(chosen_word)
            
            if possible:
                return " ".join(line_words), temp_used_words
        
        return None, None

    # 1. Clean and tokenize input
    words = re.findall(r'\b[a-zA-Z]+\b', input_str)
    if not words:
        return "Not enough words to generate a haiku."
        
    unique_words = sorted(list(set([w.lower() for w in words])))
    
    # 2. Categorize words by syllable count
    syllable_map = collections.defaultdict(list)
    for word in unique_words:
        s_count = count_syllables(word)
        if 0 < s_count <= 7:
            syllable_map[s_count].append(word)

    # 3. Generate haiku lines
    haiku_lines = []
    used_words = set()
    
    line1, used_words_after_1 = generate_line(5, syllable_map, used_words)
    if not line1:
        return "Could not generate a haiku from the given text."
    haiku_lines.append(line1.capitalize())
    used_words.update(used_words_after_1)
        
    line2, used_words_after_2 = generate_line(7, syllable_map, used_words)
    if not line2:
        return "Could not generate a haiku from the given text."
    haiku_lines.append(line2)
    used_words.update(used_words_after_2)

    line3, _ = generate_line(5, syllable_map, used_words)
    if not line3:
        return "Could not generate a haiku from the given text."
    haiku_lines.append(line3)
    
    return "\n".join(haiku_lines)
