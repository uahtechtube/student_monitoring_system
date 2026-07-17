# KIU Student Monitoring - System Performance & Model Evaluation Report

This report was automatically generated on the dataset: **20000 records**.

---

## 1. Data Ingestion Performance
- **File Format Ingested**: Excel
- **Parse Duration**: 11202.27 ms
- **Throughput Rate**: 1785 rows/second

---

## 2. Clustering Model Quality & Generalizability

### Returning Students Model
- **Silhouette Coefficient**: `0.2359` (Weak Structure)
- **Train/Test Generalization**:
  - Training Split Silhouette: `0.2443`
  - Test Split Silhouette: `0.2434`
  - Generalization Gap: `0.0010`
  - Status: **Healthy (Generalizes Well)**
- **Outlier Density (IQR 1.5x)**: `0 rows (0.00%)`
- **Model Inherent Cohesion (WCSS)**: `2364.24`

### New Students Model
- **Silhouette Coefficient**: `0.3912` (Moderate Structure)
- **Train/Test Generalization**:
  - Training Split Silhouette: `0.3841`
  - Test Split Silhouette: `0.3644`
  - Generalization Gap: `0.0198`
  - Status: **Healthy (Generalizes Well)**
- **Outlier Density (IQR 1.5x)**: `0 rows (0.00%)`
- **Model Inherent Cohesion (WCSS)**: `260.37`

---

## 3. Computational Scaling (K-Means Fit Time & Memory)
The table below charts performance as dataset size scales:

| Student Count | Fit Time (ms) | Peak RAM usage (MB) |
|---------------|---------------|---------------------|
| 100 | 11885.38 ms | 0.4123 MB |
| 500 | 241.51 ms | 4.1344 MB |
| 1,000 | 487.22 ms | 15.8592 MB |
| 5,000 | 339.82 ms | 17.9691 MB |
| 10,000 | 484.58 ms | 20.6042 MB |
| 15,970 | 682.48 ms | 23.7529 MB |

---

## 4. Database Persistence Overhead
Compares inserting `2,000` student labels to the database using sequential transactions vs bulk insert:
- **Sequential Write Speed**: `3494.28 ms`
- **Bulk Write Speed**: `2428.55 ms`
- **Database Speedup Factor**: **1.44x faster** using Bulk Writes

---

*End of Performance Audit Report.*
