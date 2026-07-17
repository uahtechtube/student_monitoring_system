with open("MyProject_text.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(1126, min(1180, len(lines))):
    print(f"{idx+1}: {lines[idx].strip()}")
