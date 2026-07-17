import re

with open("MyProject_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Let's search for lines that look like section headings (e.g. 1.1, 1.2, 3.1, etc.)
lines = text.split("\n")
heading_pattern = re.compile(r'^\s*([1-3]\.[0-9]+(?:\.[0-9]+)?\s+[A-Z][a-zA-Z0-9\s,:\-\(\)/&]+)')

headings = []
for i, line in enumerate(lines):
    match = heading_pattern.match(line)
    if match:
        headings.append((i+1, line.strip()))
    elif "CHAPTER" in line:
        headings.append((i+1, f"--- {line.strip()} ---"))

for line_num, heading in headings:
    print(f"Line {line_num}: {heading}")
