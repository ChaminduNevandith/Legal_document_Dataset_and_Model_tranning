import json, re
from pathlib import Path

IN_PATH = Path("../Dataset_Acts_Stage_1/chunks.jsonl")  # or your local path
OUT_DIR = Path("../Dataset_Acts_Finetune")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# detect table-like chunks (many numbers/symbols)
def is_table_like(text: str) -> bool:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) < 4:
        return False
    numericish = sum(1 for ln in lines if re.fullmatch(r"[\d\W_]+", ln))
    return numericish / len(lines) >= 0.6

def make_summary_row(chunk_id, text):
    return {
        "id": chunk_id,
        "task": "simplify_summary",
        "instruction": "පහත නීතිමය පෙළ සරල සිංහලෙන් සාරාංශ කරන්න. (අදාළ වන්නේ කාටද, මොනවා කරන්නද කියලා පැහැදිලි කරන්න.)",
        "input": text,
        "output": ""   # you will fill manually
    }

def make_extract_row(chunk_id, text):
    return {
        "id": chunk_id,
        "task": "extract_obligations",
        "instruction": "පහත පෙළෙන් වගකීම්, කාලසීමා, සහ දඩ/දඬුවම් තිබේනම් JSON ලෙස වෙන් කර දෙන්න. නොමැති දේවල් null කරන්න.",
        "input": text,
        "output": "{\"obligations\": null, \"deadlines\": null, \"penalties\": null}"
    }

rows = []
with IN_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        text = r.get("text","")
        if len(text) < 120:
            continue
        if is_table_like(text):
            continue
        rows.append(r)

finetune = []
for r in rows:
    cid = r["chunk_id"]
    txt = r["text"]
    finetune.append(make_summary_row(cid, txt))
    finetune.append(make_extract_row(cid, txt))

out_path = OUT_DIR / "finetune.jsonl"
with out_path.open("w", encoding="utf-8") as f:
    for x in finetune:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")

print("Saved:", out_path, "rows:", len(finetune))
