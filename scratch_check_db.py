import sqlite3
import pandas as pd

conn = sqlite3.connect("kiu_monitoring.db")
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables: {tables}")

# Check count of records in each table
for table in tables:
    name = table[0]
    cursor.execute(f"SELECT COUNT(*) FROM {name};")
    count = cursor.fetchone()[0]
    print(f"Table '{name}' has {count} rows")

# If there are datasets, let's see them
cursor.execute("SELECT * FROM datasets LIMIT 5;")
print("Datasets samples:", cursor.fetchall())

# Check how many students by student_type
try:
    cursor.execute("SELECT student_type, COUNT(*) FROM students GROUP BY student_type;")
    print("Students by type:", cursor.fetchall())
except Exception as e:
    print("Error querying students:", e)

# Check cluster results count
try:
    cursor.execute("SELECT cluster_label, COUNT(*) FROM cluster_results GROUP BY cluster_label;")
    print("Cluster results by label:", cursor.fetchall())
except Exception as e:
    print("Error querying cluster_results:", e)

conn.close()
