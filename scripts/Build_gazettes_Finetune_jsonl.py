import json, re
from pathlib import Path

# ==========================
# INPUT / OUTPUT
# ==========================
IN_PATH = Path("../Dataset_Gazettes_Stage_1\gazette_chunks.jsonl")  # <-- change this
OUT_DIR = Path("../Dataset_Gazettes_Finetune")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ==========================
# HELPERS: FILTERING
# ==========================

# Gazette front-matter / publication meta noise (common in OCR/text extracts)
GAZETTE_META_PAT = re.compile(
    r"(ගැසට්|අතිරේක|අති විශේෂ|extraordinary|gazette|පත්‍රයේ|මුද්‍රණය|මුද්‍රණ දෙපාර්තමේන්තුව|"
    r"government printer|printed|ප්‍රකාශයට පත්|පළ කරන ලදී|අංක\s*\d+\/\d+|No\.\s*\d+\/\d+)",
    re.IGNORECASE
)

# Very common footer/header lines in gazettes
HEADER_FOOTER_PAT = re.compile(
    r"(ශ්‍රී ලංකා ප්‍රජාතාන්ත්‍රික සමාජවාදී ජනරජය|democratic socialist republic|"
    r"gazz?ette of the democratic socialist republic|the gazette of sri lanka)",
    re.IGNORECASE
)

# Detect page-number-ish lines
PAGE_NO_PAT = re.compile(r"^\s*(\d+|page\s*\d+)\s*$", re.IGNORECASE)

# Detect mostly-symbol / mostly-numeric lines
NUMSYM_LINE_PAT = re.compile(r"^[\d\W_]+$")

# Gazette tables/lists often have many short numeric lines
def is_table_like(text: str) -> bool:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) < 5:
        return False

    numericish = sum(1 for ln in lines if NUMSYM_LINE_PAT.fullmatch(ln) is not None)
    very_short = sum(1 for ln in lines if len(ln) <= 3 or PAGE_NO_PAT.fullmatch(ln))
    # “table-like” if too many numeric/symbol-only lines OR too many ultra-short lines
    return (numericish / len(lines) >= 0.45) or (very_short / len(lines) >= 0.35)

def looks_like_pure_metadata(text: str) -> bool:
    """
    Returns True when the chunk is mostly publication/printing info and not real content.
    We allow some meta, but if it is dominated by meta keywords and has no meaningful
    sentences, we drop it.
    """
    t = re.sub(r"\s+", " ", (text or "")).strip()
    if not t:
        return True

    # too short -> likely noise
    if len(t) < 160:
        # if it is short AND contains gazette meta keywords -> drop
        if GAZETTE_META_PAT.search(t):
            return True

    # If it contains many meta keywords and little "sentence" structure -> drop
    meta_hits = len(GAZETTE_META_PAT.findall(t)) + len(HEADER_FOOTER_PAT.findall(t))
    # sentence markers in Sinhala/English
    sentence_marks = len(re.findall(r"[။\.]\s", t))

    # If meta hits are high and sentence_marks are very low, drop
    if meta_hits >= 2 and sentence_marks <= 1 and len(t) < 350:
        return True

    return False

def too_noisy(text: str) -> bool:
    t = text or ""
    # OCR garbage ratio check: lots of replacement chars / junk
    bad = sum(t.count(ch) for ch in ["�", "�", "�"])
    return (bad >= 3 and len(t) < 400)

# ==========================
# FINETUNE ROWS
# ==========================

def make_summary_row(chunk_id, text):
    return {
        "id": chunk_id,
        "task": "simplify_summary",
        "instruction": (
            "පහත නීතිමය/රාජ්‍ය දැනුම්දීමේ පෙළ සරල සිංහලෙන් සාරාංශ කරන්න. "
            "එය අදාළ වන්නේ කාටද, මොන ක්‍රියාවක්/තීරණයක්/දැනුම්දීමක්ද කියලා පැහැදිලි කරන්න. "
            "කාලසීමා හෝ දඩ/දඬුවම් තිබේ නම් සාරාංශයේ සඳහන් කරන්න."
        ),
        "input": text,
        "output": ""
    }

def make_extract_row(chunk_id, text):
    return {
        "id": chunk_id,
        "task": "extract_obligations",
        "instruction": (
            "පහත පෙළෙන් වගකීම් (කළ යුතු දේ), කාලසීමා/අවසන් දිනයන්, සහ දඩ/දඬුවම් තිබේනම් "
            "JSON ලෙස වෙන් කර දෙන්න. නොමැති දේවල් null කරන්න."
        ),
        "input": text,
        "output": "{\"obligations\": null, \"deadlines\": null, \"penalties\": null}"
    }

# ==========================
# MAIN
# ==========================

rows = []
kept = 0
dropped = {
    "too_short": 0,
    "table_like": 0,
    "pure_metadata": 0,
    "too_noisy": 0
}

with IN_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        text = r.get("text", "") or ""
        text_stripped = text.strip()

        if len(text_stripped) < 120:
            dropped["too_short"] += 1
            continue

        if too_noisy(text_stripped):
            dropped["too_noisy"] += 1
            continue

        if is_table_like(text_stripped):
            dropped["table_like"] += 1
            continue

        if looks_like_pure_metadata(text_stripped):
            dropped["pure_metadata"] += 1
            continue

        rows.append(r)
        kept += 1

finetune = []
for r in rows:
    # supports either "chunk_id" or "id" depending on your stage output
    cid = r.get("chunk_id") or r.get("id")
    if cid is None:
        # fallback: create a stable id from doc_id + index if present
        doc_id = r.get("doc_id", "unknown_doc")
        idx = r.get("index", r.get("chunk_index", "0"))
        cid = f"{doc_id}_{idx}"

    txt = r["text"]
    finetune.append(make_summary_row(cid, txt))
    finetune.append(make_extract_row(cid, txt))

out_path = OUT_DIR / "finetune.jsonl"
with out_path.open("w", encoding="utf-8") as f:
    for x in finetune:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")

print("Saved:", out_path)
print("Kept chunks:", kept)
print("Dropped:", dropped)
print("Finetune rows:", len(finetune))
