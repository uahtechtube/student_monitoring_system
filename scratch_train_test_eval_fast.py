import sqlite3
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

conn = sqlite3.connect("kiu_monitoring.db")
query = "SELECT * FROM students WHERE dataset_id = 1"
df = pd.read_sql_query(query, conn)
conn.close()

print(f"Loaded {len(df)} records from dataset 1")

# Clean and filter
df_ret = df[df['student_type'] == 'Returning'].dropna(subset=["cgpa", "attendance_rate", "assessment_score"]).drop_duplicates(subset=["matric_number"]).reset_index(drop=True)
df_new = df[df['student_type'] == 'New'].dropna(subset=["attendance_rate", "assessment_score"]).drop_duplicates(subset=["matric_number"]).reset_index(drop=True)

print(f"Cleaned Returning: {len(df_ret)}")
print(f"Cleaned New: {len(df_new)}")

# Returning Students Model Evaluation
train_ret, test_ret = train_test_split(df_ret, test_size=0.20, random_state=42)
scaler_ret = MinMaxScaler()
features_ret = ["cgpa", "attendance_rate", "assessment_score"]
X_train_ret = scaler_ret.fit_transform(train_ret[features_ret].values)
X_test_ret = scaler_ret.transform(test_ret[features_ret].values)

km_ret = KMeans(n_clusters=3, init="k-means++", n_init=10, max_iter=300, random_state=42)
train_labels_ret = km_ret.fit_predict(X_train_ret)
test_labels_ret = km_ret.predict(X_test_ret)

train_wcss_ret = km_ret.inertia_
test_wcss_ret = np.sum((X_test_ret - km_ret.cluster_centers_[test_labels_ret])**2)

train_sil_ret = silhouette_score(X_train_ret, train_labels_ret, sample_size=1000, random_state=42)
test_sil_ret = silhouette_score(X_test_ret, test_labels_ret, sample_size=1000, random_state=42)

print("\n=== Returning Students Model Evaluation (Fast) ===")
print(f"Train WCSS: {train_wcss_ret:.4f}")
print(f"Test WCSS: {test_wcss_ret:.4f}")
print(f"Train Silhouette Score (sample=1000): {train_sil_ret:.4f}")
print(f"Test Silhouette Score (sample=1000): {test_sil_ret:.4f}")
print(f"Silhouette Gap: {abs(train_sil_ret - test_sil_ret):.4f}")

# New Students Model Evaluation
train_new, test_new = train_test_split(df_new, test_size=0.20, random_state=42)
scaler_new = MinMaxScaler()
features_new = ["attendance_rate", "assessment_score"]
X_train_new = scaler_new.fit_transform(train_new[features_new].values)
X_test_new = scaler_new.transform(test_new[features_new].values)

km_new = KMeans(n_clusters=3, init="k-means++", n_init=10, max_iter=300, random_state=42)
train_labels_new = km_new.fit_predict(X_train_new)
test_labels_new = km_new.predict(X_test_new)

train_wcss_new = km_new.inertia_
test_wcss_new = np.sum((X_test_new - km_new.cluster_centers_[test_labels_new])**2)

train_sil_new = silhouette_score(X_train_new, train_labels_new, sample_size=1000, random_state=42)
test_sil_new = silhouette_score(X_test_new, test_labels_new, sample_size=1000, random_state=42)

print("\n=== New Students Model Evaluation (Fast) ===")
print(f"Train WCSS: {train_wcss_new:.4f}")
print(f"Test WCSS: {test_wcss_new:.4f}")
print(f"Train Silhouette Score (sample=1000): {train_sil_new:.4f}")
print(f"Test Silhouette Score (sample=1000): {test_sil_new:.4f}")
print(f"Silhouette Gap: {abs(train_sil_new - test_sil_new):.4f}")

# Diagnostics (Elbow / Silhouette sweeps)
print("\n=== Diagnostics (Returning) ===")
for k in range(2, 9):
    km = KMeans(n_clusters=k, init="k-means++", n_init=10, max_iter=300, random_state=42)
    labels = km.fit_predict(X_train_ret)
    sil = silhouette_score(X_train_ret, labels, sample_size=1000, random_state=42)
    print(f"K={k}: WCSS={km.inertia_:.4f}, Silhouette={sil:.4f}")

print("\n=== Diagnostics (New) ===")
for k in range(2, 9):
    km = KMeans(n_clusters=k, init="k-means++", n_init=10, max_iter=300, random_state=42)
    labels = km.fit_predict(X_train_new)
    sil = silhouette_score(X_train_new, labels, sample_size=1000, random_state=42)
    print(f"K={k}: WCSS={km.inertia_:.4f}, Silhouette={sil:.4f}")
