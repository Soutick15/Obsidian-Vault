"""
Day 1 Exercise — Text Stats Tool
=================================
Given a hardcoded multi-line passage, compute and print:
  - Total line count
  - Total word count
  - Longest word
  - Count of words starting with each letter (A-Z, case-insensitive),
    but only print letters that actually appear.

"""

PASSAGE = """
Python is a high-level general-purpose programming language.
Its design philosophy emphasises code readability with the use of significant indentation.
Python is dynamically typed and garbage-collected.
It supports multiple programming paradigms including structured functional and object-oriented programming.
It is often described as a batteries included language due to its comprehensive standard library.
""".strip()


def count_lines(text):
    list = text.split("\n")
    return len(list)



def count_words(text):
    words = text.split()
    return len(words)


def find_longest_word(text):
    """Return the longest word in text (lowercase, no punctuation)."""
    longest = ""
    for word in text.split():
        clean = word.strip(".,;:\"'()-")
        if len(clean) > len(longest):
            longest = clean
    return longest.lower()


def letter_frequency(text):
    """Return a dict mapping each starting letter (upper) to its word count."""
    freq = {}
    for word in text.split():
        first = word[0].upper()
        if first.isalpha():
            freq[first] = freq.get(first, 0) + 1
    return freq


def main():
    lines  = count_lines(PASSAGE)
    words  = count_words(PASSAGE)
    longest = find_longest_word(PASSAGE)
    freq   = letter_frequency(PASSAGE)

    print("=== Text Stats ===")

    # TODO: print line count using an f-string
    print (f"lines count : {lines}")

    # TODO: print word count using an f-string
    print (f"words count : {words}")

    # TODO: print longest word using an f-string
    print (f"longest word : {longest}")

    print("\nWords per starting letter:")
    for letter, count in sorted(freq.items()):
        print(f"  {letter} : {count}")



if __name__ == "__main__":
    main()