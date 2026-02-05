import os
import re
import json
import unicodedata
from pathlib import Path

ACTS_OUTPUT_DIR = "../actsoutput"
ACTS_PRE_DIR = "../actspre"
MIN_YEAR = 1991


# Rule-based word fixes (edit this list as you find more)

REPLACEMENTS = [
    ("~~~", " "),
    ("~_~~", " "),
    ("_~~", " "),
    ("—", "-"),
    ("–", "-"),
    ("•", " "),
    ("�", " "),
    ("\u200b", ""),  

    ("පනන", "පනත"),
    ("ජනත", "පනත"),
    ("චාර්තා", "වාර්තා"),
    ("චාර්තාව", "වාර්තාව"),
    ("චාර්තාවික්", "වාර්තාවක්"),
    ("සනත", "පනත"),
    ("අමාතාවරසයා", "අමාත්‍යවරයා"),
    ("අමාතනාවරයාගේ", "අමාත්‍යවරයාගේ"),
    ("නියෝරිත", "නියෝජිත"),
    ("අහියාචනය", "අභියාචනය"),
    ("තිරණය", "තීරණය"),
    ("මණඩල", "මණ්ඩල"),
    ("පජිටපන්", "පිටපත්"),
    ("කිරිම", "කිරීම"),
    ("කිරිමේ", "කිරීමේ"),
    ("ලැබිමේ", "ලැබීමේ"),
    ("රජයේ", "රජයේ"),  
    ("පඊලිමේන්තූව", "පාර්ලිමේන්තුව"),
    ("ශ්‍රී ලඋංකා", "ශ්‍රී ලංකා"),
    ("ඇණ්‌ ඞුවේ", "ආණ්ඩුවේ"),
]


REMOVE_LINE_PATTERNS = [
    r"^\s*\d+\s*$",                 
    r"^\s*\(\s*[ivxIVX]+\s*\)\s*$",  
]


# Normalization + cleanup helpers

def normalize_text(text: str) -> str:

    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\b59(\d{3})\b", r"20\1", text)
    text = re.sub(r"\b52(\d{3})\b", r"20\1", text)  
    text = re.sub(r"\b5(\d{3})\b",  r"2\1",  text)  
    text = re.sub(r"\b(20\d{2})\s*\?\b", r"\1", text)
    text = re.sub(r"[=\-]{4,}", " ", text)
    text = re.sub(r"[~]{2,}", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text


def apply_replacements(text: str) -> str:
    for a, b in REPLACEMENTS:
        text = text.replace(a, b)
    return text


def drop_until_nth_newline(text: str, n: int = 4) -> str:
    if n <= 0:
        return text
    count = 0
    for i, ch in enumerate(text):
        if ch == "\n":
            count += 1
            if count == n:
                return text[i+1:]
    return text


def clean_lines(text: str) -> str:
    lines = text.splitlines()
    out = []
    for ln in lines:
        ln = ln.strip()

        if not ln:
            out.append("")
            continue

        # remove junk-only lines
        if any(re.match(pat, ln) for pat in REMOVE_LINE_PATTERNS):
            continue

        if re.fullmatch(r"[\W_]+", ln, flags=re.UNICODE):
            continue

        out.append(ln)

    cleaned = "\n".join(out)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip() + "\n"
    return cleaned


def preprocess_document(text: str) -> str:
    text = normalize_text(text)

    text = drop_until_nth_newline(text, n=4)
    text = apply_replacements(text)
    text = clean_lines(text)
    return text



def main():
    in_dir = Path(ACTS_OUTPUT_DIR)
    out_dir = Path(ACTS_PRE_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    txt_files = sorted(in_dir.glob("*.txt"))

    def extract_year_from_name(name: str) -> int | None:
        m = re.search(r"-([12]\d{3})_", name)
        return int(m.group(1)) if m else None

    txt_files = [
        fp for fp in txt_files
        if (yr := extract_year_from_name(fp.name)) is not None and yr >= MIN_YEAR
    ]

    if not txt_files:
        print(f"No .txt files (year >= {MIN_YEAR}) found in: {in_dir.resolve()}")
        return

    for fp in txt_files:
        raw = fp.read_text(encoding="utf-8", errors="replace")
        cleaned = preprocess_document(raw)


        document_id = fp.stem 
        year = extract_year_from_name(fp.name)
        doc = {
            "document_id": document_id,
            "raw_text": cleaned,
            "document_type": "Act",
            "year": year,
            "language": "si",
        }

        out_path = out_dir / f"{fp.stem}.json"
        out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ {fp.name}  ->  {out_path}")

    print("\nDone. Edit REPLACEMENTS to improve word corrections over time.")


if __name__ == "__main__":
    main()
