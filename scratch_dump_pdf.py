import pypdf

pdf_path = "MyProject.pdf"
txt_path = "MyProject_text.txt"

reader = pypdf.PdfReader(pdf_path)
print(f"Total pages: {len(reader.pages)}")

with open(txt_path, "w", encoding="utf-8") as f:
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        f.write(f"=== PAGE {i+1} ===\n")
        f.write(text)
        f.write("\n\n")

print(f"Dumped text to {txt_path}")
