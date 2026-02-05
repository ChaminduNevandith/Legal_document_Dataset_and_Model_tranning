import re
import unicodedata

def clean_sinhala_legal_text(text):
    """
    Cleans Sinhala legal text by normalizing, removing non-content text,
    segmenting, deduplicating, and normalizing spacing.
    Args:
        text (str): Raw Sinhala legal text
    Returns:
        str: Cleaned text
    """

    # 1. Unicode normalization + remove invisible characters
    text = unicodedata.normalize('NFC', text)
    text = text.replace("\u200d", "").replace("\u200b", "")  # remove ZWJ & ZWSP

    # 2. Remove non-content text (headers, footers, page numbers)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)  # page numbers
    text = re.sub(r'\b(අනුපිටපත්|පිටුව|PAGE|Page|අංකය|Number)\b.*', '', text)  # header/footer keywords
    text = re.sub(r'(ශ්‍රී ලංකා ප්‍රජාතාන්ත්‍රික සමාජවාදී ජනරජය|Democratic Socialist Republic of Sri Lanka)', '', text)

    # 3. Normalize punctuation
    replacements = {
        "–": "-", "—": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
        "•": "-", "●": "-", "▪": "-"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # 4. Sentence/clause segmentation
    # Split on danda (।), full stop, question, exclamation, or colon
    sentences = re.split(r'[\.।:;!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # 5. Remove duplicates while preserving order
    seen = set()
    unique_sentences = []
    for s in sentences:
        if s not in seen:
            unique_sentences.append(s)
            seen.add(s)

    # 6. Normalize spacing
    cleaned = "\n".join(unique_sentences)
    cleaned = re.sub(r'\s+', ' ', cleaned)  # collapse spaces
    cleaned = re.sub(r' *\n *', '\n', cleaned)  # tidy newlines
    cleaned = cleaned.strip()

    return cleaned


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python sinhala_text_cleaner.py input.txt output.txt")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, encoding="utf-8") as f:
        raw_text = f.read()

    cleaned_text = clean_sinhala_legal_text(raw_text)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cleaned_text)

    print(f"✅ Cleaned text written to {output_path}")
