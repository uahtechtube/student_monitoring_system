with open("MyProject_text.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "chapter" in line.lower() or "table of contents" in line.lower():
        print(f"Line {i+1}: {line.strip()}")
