with open("MyProject_text.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines in MyProject_text.txt: {len(lines)}")
print("--- Last 20 lines ---")
for line in lines[-20:]:
    print(line.strip())
