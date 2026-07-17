import sqlite3
import pandas as pd
from app.clustering.engine import ClusteringEngine

conn = sqlite3.connect("kiu_monitoring.db")

# Load students from the first dataset
query = "SELECT * FROM students WHERE dataset_id = 1"
df = pd.read_sql_query(query, conn)
print(f"Loaded {len(df)} records from dataset 1")

# Returning students in dataset 1
df_ret = df[df['student_type'] == 'Returning'].copy()
# New students in dataset 1
df_new = df[df['student_type'] == 'New'].copy()

print(f"Returning students count: {len(df_ret)}")
print(f"New students count: {len(df_new)}")

# Evaluate Returning model
engine_ret = ClusteringEngine(student_type="returning", min_dataset_size=30)
result_ret = engine_ret.fit(df_ret)
report_ret = engine_ret.evaluate_train_test(df_ret)

print("\n=== Returning Students Model Evaluation ===")
print(f"Train WCSS: {report_ret.train_wcss:.4f}")
print(f"Test WCSS: {report_ret.test_wcss:.4f}")
print(f"Train Silhouette Score: {report_ret.train_silhouette:.4f}")
print(f"Test Silhouette Score: {report_ret.test_silhouette:.4f}")
print(f"Silhouette Gap: {report_ret.silhouette_gap:.4f}")
print(f"Possible Overfit: {report_ret.possible_overfit}")

# Evaluate New model
engine_new = ClusteringEngine(student_type="new", min_dataset_size=30)
result_new = engine_new.fit(df_new)
report_new = engine_new.evaluate_train_test(df_new)

print("\n=== New Students Model Evaluation ===")
print(f"Train WCSS: {report_new.train_wcss:.4f}")
print(f"Test WCSS: {report_new.test_wcss:.4f}")
print(f"Train Silhouette Score: {report_new.train_silhouette:.4f}")
print(f"Test Silhouette Score: {report_new.test_silhouette:.4f}")
print(f"Silhouette Gap: {report_new.silhouette_gap:.4f}")
print(f"Possible Overfit: {report_new.possible_overfit}")

# Print diagnostics for K=2..8 for Returning
print("\n=== Diagnostics (Returning) ===")
for k, metrics in result_ret.diagnostics.items():
    print(f"K={k}: WCSS={metrics['wcss']:.4f}, Silhouette={metrics['silhouette']:.4f}")

# Print diagnostics for K=2..8 for New
print("\n=== Diagnostics (New) ===")
for k, metrics in result_new.diagnostics.items():
    print(f"K={k}: WCSS={metrics['wcss']:.4f}, Silhouette={metrics['silhouette']:.4f}")

conn.close()
