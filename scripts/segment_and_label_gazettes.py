import re
import json
from pathlib import Path
from typing import List, Dict


IN_DIR = Path("../extraordinary_gazettespre")   # ✅ gazette preprocessed JSONs
OUT_DIR = Path("../Dataset_Gazettes_Stage_1")    # output chunks + labels
OUT_DIR.mkdir(parents=True, exist_ok=True)





SECTION_PAT = re.compile(r"^\s*(\d+(\.\d+)*)\s*[\)\.]?\s+", re.UNICODE)   
SUBSECTION_PAT = re.compile(r"^\s*\(\s*\d+\s*\)\s+", re.UNICODE)         
LETTER_PAT = re.compile(r"^\s*\(\s*[a-zA-Z]\s*\)\s+", re.UNICODE)       


GAZETTE_HEADER_PAT = re.compile(
    r"^(අති\s*විශේෂ\s*ගැසට්\s*පත්‍රය|ගැසට්\s*පත්‍රය|THE\s+GAZETTE|EXTRAORDINARY|GAZETTE)\b",
    re.IGNORECASE | re.UNICODE,
)

GAZETTE_PART_PAT = re.compile(
    r"^(PART\s*[IVXLC]+|කොටස\s*\d+|අංශය\s*\d+|අංශ\s*\d+|SECTION\s*\d+)\b",
    re.IGNORECASE | re.UNICODE,
)

GAZETTE_NOTICE_PAT = re.compile(
    r"^(නිවේදනය|දැනුම්දීම|දැන්වීම|නියෝගය|නියෝග|රෙගුලාසි|ප්‍රකාශය|NOTIFICATION|ORDER|REGULATION)\b",
    re.IGNORECASE | re.UNICODE,
)

GAZETTE_SCHEDULE_PAT = re.compile(
    r"^(උපලේඛනය|උපලේඛන|SCHEDULE|ANNEX|ANNEXURE)\b",
    re.IGNORECASE | re.UNICODE,
)



SINHALA_OBLIG = re.compile(r"(යුතුය|යුත්තේය|කළ යුතුය|අනිවාර්ය|වගකිය)", re.UNICODE)
SINHALA_DEADLINE = re.compile(r"(දින\s*\d+|මාස\s*\d+|අවුරුදු\s*\d+|තුළ|කට පෙර|දිනට පෙර)", re.UNICODE)
SINHALA_PENALTY = re.compile(r"(දඩ|දඬුවම්|සිරදඬුවම්|නඩු|වරදක්|පනවා)", re.UNICODE)
SINHALA_PROHIB = re.compile(r"(තහනම්|නොකළ\s*යුතුය|නොහැකි|වළක්වා)", re.UNICODE)

TABLE_LIKE_PAT = re.compile(r"^(\s*[\d\.,/:\-\s]{10,}|[A-Z]{2,}\s+\d+|\d+\s+\d+\s+\d+)\s*$", re.UNICODE)

def is_table_like_paragraph(p: str) -> bool:
    lines = [ln.strip() for ln in p.splitlines() if ln.strip()]
    if len(lines) < 4:
        return False
    table_lines = sum(1 for ln in lines if TABLE_LIKE_PAT.match(ln))
    return (table_lines / max(len(lines), 1)) >= 0.65  # majority numeric-like


def is_new_section_start(p: str) -> bool:
    return bool(
        SECTION_PAT.match(p)
        or SUBSECTION_PAT.match(p)
        or LETTER_PAT.match(p)
        or GAZETTE_HEADER_PAT.match(p)
        or GAZETTE_PART_PAT.match(p)
        or GAZETTE_NOTICE_PAT.match(p)
        or GAZETTE_SCHEDULE_PAT.match(p)
    )

def split_into_chunks(text: str, max_chars: int = 1100) -> List[str]:
    """
    Gazette-friendly: split by blank lines, then merge until max_chars.
    Start new chunk when a new notice/part/schedule/section is detected.
    """
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: List[str] = []
    buff = ""

    for p in parts:
        new_clause = is_new_section_start(p)
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

    if is_table_like_paragraph(text):
        labels.append("TABLE_LIKE")

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

    if not files:
        print(f"❌ No JSON files found in {IN_DIR.resolve()}")
        return

    for fp in files:
        doc = json.loads(fp.read_text(encoding="utf-8"))
        text = doc.get("raw_text", "")
        if not text.strip():
            continue

        chunks = split_into_chunks(text)
        doc_id = doc.get("document_id", fp.stem)

        for i, ch in enumerate(chunks):
            row = {
                "doc_id": doc_id,
                "doc_type": doc.get("document_type", "ExtraordinaryGazette"),  # ✅ default changed
                "year": doc.get("year"),
                "language": doc.get("language", "si"),
                "chunk_id": f"{doc_id}::{i:04d}",
                "text": ch,
                "labels": weak_label(ch),
            }
            all_rows.append(row)

    out_path = OUT_DIR / "gazette_chunks.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Created {len(all_rows)} gazette chunks -> {out_path}")
    print("Tip: you can later filter out TABLE_LIKE chunks if they reduce summarization quality.")

if __name__ == "__main__":
    main()
