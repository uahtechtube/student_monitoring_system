import sqlite3
import pandas as pd

conn = sqlite3.connect("kiu_monitoring.db")

# We want to see the performance profile of the clusters.
# We can join cluster_results and students, grouping by student_type and cluster_label.
query = """
SELECT 
    s.student_type,
    cr.cluster_label,
    COUNT(cr.result_id) as count,
    AVG(s.cgpa) as avg_cgpa,
    AVG(s.attendance_rate) as avg_attendance,
    AVG(s.assessment_score) as avg_assessment,
    MIN(s.cgpa) as min_cgpa, MAX(s.cgpa) as max_cgpa,
    MIN(s.attendance_rate) as min_attendance, MAX(s.attendance_rate) as max_attendance,
    MIN(s.assessment_score) as min_assessment, MAX(s.assessment_score) as max_assessment
FROM cluster_results cr
JOIN students s ON cr.student_id = s.student_id
GROUP BY s.student_type, cr.cluster_label
ORDER BY s.student_type, cr.cluster_label;
"""

df = pd.read_sql_query(query, conn)
print("=== CLUSTER PROFILES ===")
print(df.to_string(index=False))

# Let's also see the overall stats for each student type
print("\n=== OVERALL STATS BY STUDENT TYPE ===")
query_overall = """
SELECT 
    student_type,
    COUNT(*) as count,
    AVG(cgpa) as avg_cgpa,
    AVG(attendance_rate) as avg_attendance,
    AVG(assessment_score) as avg_assessment
FROM students
GROUP BY student_type;
"""
df_overall = pd.read_sql_query(query_overall, conn)
print(df_overall.to_string(index=False))

conn.close()
