import sqlite3
import pandas as pd
from app.clustering.engine import ClusteringEngine

conn = sqlite3.connect("kiu_monitoring.db")
query = "SELECT * FROM students WHERE dataset_id = 1"
df = pd.read_sql_query(query, conn)
conn.close()

df_ret = df[df['student_type'] == 'Returning'].dropna(subset=["cgpa", "attendance_rate", "assessment_score"]).drop_duplicates(subset=["matric_number"]).reset_index(drop=True)
df_new = df[df['student_type'] == 'New'].dropna(subset=["attendance_rate", "assessment_score"]).drop_duplicates(subset=["matric_number"]).reset_index(drop=True)

engine_ret = ClusteringEngine(student_type="returning", min_dataset_size=30)
res_ret = engine_ret.fit(df_ret, run_diagnostics=False)
print("=== RETURNING CENTROIDS (Min-Max Scaled) ===")
print("Features:", engine_ret.features)
for idx, centroid in enumerate(res_ret.model.cluster_centers_):
    label = res_ret.centroid_rank_map[idx]
    print(f"Cluster {idx} ({label}): {centroid}")

# We can also compute the unscaled centroids (inverse transform)
unscaled_centers_ret = res_ret.scaler.inverse_transform(res_ret.model.cluster_centers_)
print("\n=== RETURNING CENTROIDS (Unscaled) ===")
for idx, centroid in enumerate(unscaled_centers_ret):
    label = res_ret.centroid_rank_map[idx]
    print(f"Cluster {idx} ({label}): CGPA={centroid[0]:.2f}, Attendance={centroid[1]:.2f}%, Assessment={centroid[2]:.2f}%")

engine_new = ClusteringEngine(student_type="new", min_dataset_size=30)
res_new = engine_new.fit(df_new, run_diagnostics=False)
print("\n=== NEW STUDENT CENTROIDS (Min-Max Scaled) ===")
print("Features:", engine_new.features)
for idx, centroid in enumerate(res_new.model.cluster_centers_):
    label = res_new.centroid_rank_map[idx]
    print(f"Cluster {idx} ({label}): {centroid}")

unscaled_centers_new = res_new.scaler.inverse_transform(res_new.model.cluster_centers_)
print("\n=== NEW STUDENT CENTROIDS (Unscaled) ===")
for idx, centroid in enumerate(unscaled_centers_new):
    label = res_new.centroid_rank_map[idx]
    print(f"Cluster {idx} ({label}): Attendance={centroid[0]:.2f}%, Assessment={centroid[1]:.2f}%")
