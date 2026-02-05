import pytesseract
from pdf2image import convert_from_path
import os


# CONFIGURATION


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Path to Poppler bin
POPPLER_PATH = r"D:\poppler-25.07.0\Library\bin"

# Input & Output folders
INPUT_FOLDER = r"C:\Users\user\Desktop\dataset creation\acts"
OUTPUT_FOLDER = r"C:\Users\user\Desktop\dataset creation\actsoutput"

# OCR language (Sinhala = sin)
LANG = "sin"


def pdf_to_text(input_pdf, output_txt, lang="sin"):
    pages = convert_from_path(
        input_pdf,
        dpi=300,
        poppler_path=POPPLER_PATH
    )

    all_text = []
    for page in pages:
        text = pytesseract.image_to_string(page, lang=lang)
        all_text.append(text)

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_text))

    print(f"✔ Extracted: {os.path.basename(input_pdf)}")


def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    for filename in os.listdir(INPUT_FOLDER):
        if filename.lower().endswith(".pdf"):
            input_pdf_path = os.path.join(INPUT_FOLDER, filename)

            # Same name, just change extension to .txt
            output_txt_name = os.path.splitext(filename)[0] + ".txt"
            output_txt_path = os.path.join(OUTPUT_FOLDER, output_txt_name)

            pdf_to_text(input_pdf_path, output_txt_path, LANG)

    print("\n✅ All PDFs processed successfully.")

if __name__ == "__main__":
    main()
