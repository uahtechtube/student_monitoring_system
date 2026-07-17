import os

log_path = r"C:\Users\MAI MAGE COMPUTERS\.gemini\antigravity\brain\c5c6a37d-39e3-4efe-aec1-b36da8a543a8\.system_generated\tasks\task-234.log"
if os.path.exists(log_path):
    print("Log file exists! Size:", os.path.getsize(log_path))
    with open(log_path, "r", encoding="utf-8") as f:
        print(f.read())
else:
    print("Log file does not exist")
