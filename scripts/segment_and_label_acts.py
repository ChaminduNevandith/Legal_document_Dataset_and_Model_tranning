import os
import re
import json
from pathlib import Path
from typing import List, Dict

IN_DIR = Path("../actspre")          # your output JSONs
OUT_DIR = Path("../Dataset_Acts_Stage_1")  # chunks + labels
OUT_DIR.mkdir(parents=True, exist_ok=True)


# 1) Chunking: split into clauses/paras

SECTION_PAT = re.compile(r"^\s*(\d+(\.\d+)*)\s*[\)\.]?\s+", re.UNICODE)  
SUBSECTION_PAT = re.compile(r"^\s*\(\s*\d+\s*\)\s+", re.UNICODE)       
LETTER_PAT = re.compile(r"^\s*\(\s*[a-zA-Z]\s*\)\s+", re.UNICODE)       
SINHALA_OBLIG = re.compile(r"(යුතුය|යුත්තේය|කළ යුතුය|අනිවාර්ය|වගකිය)", re.UNICODE)
SINHALA_DEADLINE = re.compile(r"(දින\s*\d+|මාස\s*\d+|අවුරුදු\s*\d+|තුළ|කට පෙර|දිනට පෙර)", re.UNICODE)
SINHALA_PENALTY = re.compile(r"(දඩ|දඬුවම්|සිරදඬුවම්|නඩු|වරදක්|පනවා)", re.UNICODE)
SINHALA_PROHIB = re.compile(r"(තහනම්|නොකළ\s*යුතුය|නොහැකි|වළක්වා)", re.UNICODE)

def split_into_chunks(text: str, max_chars: int = 900) -> List[str]:
    """
    Keep structure: split by blank lines, then merge until max_chars.
    """
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    buff = ""
    for p in parts:
        new_clause = bool(SECTION_PAT.match(p) or SUBSECTION_PAT.match(p) or LETTER_PAT.match(p))
        if buff and (len(buff) + len(p) > max_chars or new_clause):
            chunks.append(buff.strip())
            buff = p
        else:
            buff = (buff + "\n" + p).strip() if buff else p
    if buff:
        chunks.append(buff.strip())
    return chunks

def weak_label(text: str) -> List[str]:
    labels = []
    if SINHALA_OBLIG.search(text):
        labels.append("OBLIGATION")
    if SINHALA_DEADLINE.search(text):
        labels.append("DEADLINE")
    if SINHALA_PENALTY.search(text):
        labels.append("PENALTY")
    if SINHALA_PROHIB.search(text):
        labels.append("PROHIBITION")
    if not labels:
        labels.append("OTHER")
    return labels

def main():
    files = sorted(IN_DIR.glob("*.json"))
    all_rows: List[Dict] = []

    for fp in files:
        doc = json.loads(fp.read_text(encoding="utf-8"))
        text = doc.get("raw_text", "")
        if not text.strip():
            continue

        chunks = split_into_chunks(text)
        for i, ch in enumerate(chunks):
            row = {
                "doc_id": doc.get("document_id", fp.stem),
                "doc_type": doc.get("document_type", "Act"),
                "year": doc.get("year"),
                "language": doc.get("language", "si"),
                "chunk_id": f"{doc.get('document_id', fp.stem)}::{i:04d}",
                "text": ch,
                "labels": weak_label(ch),
            }
            all_rows.append(row)

    out_path = OUT_DIR / "chunks.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Created {len(all_rows)} chunks -> {out_path}")

if __name__ == "__main__":
    main()
