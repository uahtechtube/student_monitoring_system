with open("MyProject_text.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(34, min(80, len(lines))):
    print(f"{idx+1}: {lines[idx].strip()}")
