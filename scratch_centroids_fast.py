import sqlite3
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler

conn = sqlite3.connect("kiu_monitoring.db")
query = "SELECT * FROM students WHERE dataset_id = 1"
df = pd.read_sql_query(query, conn)
conn.close()

df_ret = df[df['student_type'] == 'Returning'].dropna(subset=["cgpa", "attendance_rate", "assessment_score"]).drop_duplicates(subset=["matric_number"]).reset_index(drop=True)
df_new = df[df['student_type'] == 'New'].dropna(subset=["attendance_rate", "assessment_score"]).drop_duplicates(subset=["matric_number"]).reset_index(drop=True)

# Returning Students
features_ret = ["cgpa", "attendance_rate", "assessment_score"]
X_ret_raw = df_ret[features_ret].values
scaler_ret = MinMaxScaler()
X_ret = scaler_ret.fit_transform(X_ret_raw)

km_ret = KMeans(n_clusters=3, init="k-means++", n_init=10, max_iter=300, random_state=42)
labels_ret = km_ret.fit_predict(X_ret)

# Rank clusters
centroids_ret = km_ret.cluster_centers_
scores_ret = centroids_ret.mean(axis=1)
ranked_ret_idx = np.argsort(-scores_ret)
ranks_ret = ["High Performing", "Average Performing", "At Risk"]
rank_map_ret = {ranked_ret_idx[i]: ranks_ret[i] for i in range(3)}

unscaled_ret = scaler_ret.inverse_transform(centroids_ret)
print("=== RETURNING STUDENT CENTROIDS ===")
for idx in range(3):
    label = rank_map_ret[idx]
    c = unscaled_ret[idx]
    print(f"Cluster {idx} ({label}): CGPA={c[0]:.2f}, Attendance={c[1]:.2f}%, Assessment={c[2]:.2f}%")

# New Students
features_new = ["attendance_rate", "assessment_score"]
X_new_raw = df_new[features_new].values
scaler_new = MinMaxScaler()
X_new = scaler_new.fit_transform(X_new_raw)

km_new = KMeans(n_clusters=3, init="k-means++", n_init=10, max_iter=300, random_state=42)
labels_new = km_new.fit_predict(X_new)

# Rank clusters
centroids_new = km_new.cluster_centers_
scores_new = centroids_new.mean(axis=1)
ranked_new_idx = np.argsort(-scores_new)
ranks_new = ["High Performing", "Average Performing", "At Risk"]
rank_map_new = {ranked_new_idx[i]: ranks_new[i] for i in range(3)}

unscaled_new = scaler_new.inverse_transform(centroids_new)
print("\n=== NEW STUDENT CENTROIDS ===")
for idx in range(3):
    label = rank_map_new[idx]
    c = unscaled_new[idx]
    print(f"Cluster {idx} ({label}): Attendance={c[0]:.2f}%, Assessment={c[1]:.2f}%")
