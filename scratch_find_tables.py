with open("MyProject_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

lines = text.split("\n")
for i, line in enumerate(lines):
    if "Table 3." in line:
        print(f"Line {i+1}: {line.strip()}")
        # Print surrounding lines
        for j in range(max(0, i-5), min(len(lines), i+15)):
            print(f"  {j+1}: {lines[j]}")
        print("="*40)
