"""
Benchmark script for the KIU Student Segmentation and Academic Monitoring System.
Profiles:
  1. Data Ingestion Speed (CSV vs Excel).
  2. Clustering Engine Scaling (Execution Time and Memory Footprint across subsets).
  3. Database Insertion Performance (Sequential vs Bulk write speeds).
  4. Model Generalizability (Train/Test splits, Silhouette gaps, and overfit checks).

Usage:
  python scripts/benchmark.py --dataset KIU_Student_Dataset_20000.xlsx --output-dir app/static/benchmarks
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import tracemalloc

import numpy as np
import pandas as pd

# Add the project root to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.clustering.engine import ClusteringEngine, clean_missing_and_duplicates
from app.extensions import db
from app import create_app
from app.models import Student, ClusterResult, Dataset, User

# Try importing matplotlib for offline plotting support
try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive background renderer
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def benchmark_ingestion(filepath: str) -> dict:
    """Measures file reading time."""
    start_time = time.perf_counter()
    filename_lower = filepath.lower()
    
    if filename_lower.endswith(".csv"):
        df = pd.read_csv(filepath)
        file_type = "CSV"
    elif filename_lower.endswith(".xlsx"):
        df = pd.read_excel(filepath)
        file_type = "Excel"
    else:
        raise ValueError("Unsupported file format. Must be .csv or .xlsx")
        
    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000
    
    return {
        "file_type": file_type,
        "records": len(df),
        "latency_ms": latency_ms
    }


def benchmark_clustering_scaling(df: pd.DataFrame) -> dict:
    """Profiles execution time and peak memory footprint across subsets of data."""
    # Filter returning students to have a realistic sample with cgpa
    returning_df = df[df["student_type"] == "Returning"].copy()
    returning_df = clean_missing_and_duplicates(returning_df, ["cgpa", "attendance_rate", "assessment_score"])
    
    subset_sizes = [100, 500, 1000, 5000, 10000, 20000]
    results = []
    
    for size in subset_sizes:
        if size > len(returning_df):
            # If we don't have enough rows, use the maximum available rows
            size = len(returning_df)
            
        subset = returning_df.iloc[:size].copy()
        
        # Instantiate clustering engine
        engine = ClusteringEngine(
            student_type="returning",
            min_dataset_size=5,  # Relaxed for benchmarks
        )
        
        # Profile execution time and memory footprint
        tracemalloc.start()
        tracemalloc.reset_peak()
        
        start_time = time.perf_counter()
        engine.fit(subset, run_diagnostics=False)
        end_time = time.perf_counter()
        
        _, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        latency_ms = (end_time - start_time) * 1000
        peak_memory_mb = peak_memory / (1024 * 1024)
        
        results.append({
            "size": size,
            "latency_ms": latency_ms,
            "memory_mb": peak_memory_mb
        })
        
        if size == len(returning_df):
            break
            
    return {"scaling": results}


def benchmark_database_persistence(df: pd.DataFrame, app) -> dict:
    """Compares sequential row-by-row insertion speed vs bulk insertion speed."""
    returning_df = df[df["student_type"] == "Returning"].copy()
    returning_df = clean_missing_and_duplicates(returning_df, ["cgpa", "attendance_rate", "assessment_score"])
    
    # We will test with a fixed benchmark size of 2000 records
    test_size = min(2000, len(returning_df))
    subset = returning_df.iloc[:test_size].copy()
    
    # Run fit first to get labels
    engine = ClusteringEngine(student_type="returning", min_dataset_size=5)
    result = engine.fit(subset, run_diagnostics=False)
    
    # Set up in-memory SQLite DB for clean benchmark context
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    
    # Sequential Test
    with app.app_context():
        db.create_all()
        # Seed dummy user & dataset
        user = User(username="benchmarker", role="Admin")
        user.set_password("benchpass")
        db.session.add(user)
        db.session.commit()
        
        dataset = Dataset(filename="benchmark.csv", record_count=test_size, uploaded_by=user.user_id)
        db.session.add(dataset)
        db.session.commit()
        
        # Create students in DB first
        students = []
        for i, row in result.cleaned_df.iterrows():
            s = Student(
                student_type="Returning",
                matric_number=str(row["matric_number"]),
                full_name=row["full_name"],
                level=int(row["level"]),
                cgpa=float(row["cgpa"]),
                attendance_rate=float(row["attendance_rate"]),
                assessment_score=float(row["assessment_score"]),
                dataset_id=dataset.dataset_id
            )
            db.session.add(s)
            students.append(s)
        db.session.commit()
        
        # Test sequential insert latency
        start_time = time.perf_counter()
        for i, row in result.cleaned_df.iterrows():
            cr = ClusterResult(
                dataset_id=dataset.dataset_id,
                student_id=students[i].student_id,
                cluster_label=result.cluster_names[i],
                action_flag=result.action_flags[i],
                wcss=result.wcss,
                silhouette_score=result.silhouette
            )
            db.session.add(cr)
        db.session.commit()
        end_time = time.perf_counter()
        sequential_ms = (end_time - start_time) * 1000

    # Bulk Test
    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(username="benchmarker", role="Admin")
        user.set_password("benchpass")
        db.session.add(user)
        db.session.commit()
        
        dataset = Dataset(filename="benchmark.csv", record_count=test_size, uploaded_by=user.user_id)
        db.session.add(dataset)
        db.session.commit()
        
        students = []
        for i, row in result.cleaned_df.iterrows():
            s = Student(
                student_type="Returning",
                matric_number=str(row["matric_number"]),
                full_name=row["full_name"],
                level=int(row["level"]),
                cgpa=float(row["cgpa"]),
                attendance_rate=float(row["attendance_rate"]),
                assessment_score=float(row["assessment_score"]),
                dataset_id=dataset.dataset_id
            )
            db.session.add(s)
            students.append(s)
        db.session.commit()
        
        # Test bulk insert latency
        start_time = time.perf_counter()
        mappings = [
            {
                "dataset_id": dataset.dataset_id,
                "student_id": students[i].student_id,
                "cluster_label": result.cluster_names[i],
                "action_flag": result.action_flags[i],
                "wcss": result.wcss,
                "silhouette_score": result.silhouette
            }
            for i in range(len(result.cleaned_df))
        ]
        db.session.bulk_insert_mappings(ClusterResult, mappings)
        db.session.commit()
        end_time = time.perf_counter()
        bulk_ms = (end_time - start_time) * 1000
        
    return {
        "records_written": test_size,
        "sequential_ms": sequential_ms,
        "bulk_ms": bulk_ms,
        "speedup_factor": sequential_ms / bulk_ms if bulk_ms > 0 else 0
    }


def benchmark_model_quality(df: pd.DataFrame) -> dict:
    """Evaluates model silhouette, WCSS, and train/test overfit statistics."""
    returning_df = df[df["student_type"] == "Returning"].copy()
    new_df = df[df["student_type"] == "New"].copy()
    
    quality_report = {}
    
    for type_name, subset in [("Returning", returning_df), ("New", new_df)]:
        features = ["cgpa", "attendance_rate", "assessment_score"] if type_name == "Returning" else ["attendance_rate", "assessment_score"]
        cleaned = clean_missing_and_duplicates(subset, features)
        
        if len(cleaned) < 30:
            quality_report[type_name] = {"error": f"Insufficient data (only {len(cleaned)} rows after cleaning)"}
            continue
            
        engine = ClusteringEngine(student_type=type_name.lower())
        eval_report = engine.evaluate_train_test(cleaned)
        
        # Full set run for base metrics
        res = engine.fit(cleaned, run_diagnostics=False)
        
        quality_report[type_name] = {
            "silhouette": res.silhouette,
            "wcss": res.wcss,
            "train_silhouette": eval_report.train_silhouette,
            "test_silhouette": eval_report.test_silhouette,
            "silhouette_gap": eval_report.silhouette_gap,
            "possible_overfit": bool(eval_report.possible_overfit),
            "outliers_flagged": int(res.outlier_mask.sum()),
            "outliers_percentage": (res.outlier_mask.sum() / len(cleaned)) * 100
        }
        
    return quality_report


def generate_plots(scaling_results: list, output_dir: str):
    """Generates execution speed and memory footprint plots."""
    if not HAS_MATPLOTLIB:
        print("Matplotlib is not installed. Skipping plot generation.")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    sizes = [x["size"] for x in scaling_results]
    latencies = [x["latency_ms"] for x in scaling_results]
    memories = [x["memory_mb"] for x in scaling_results]
    
    # 1. Execution Speed Plot
    plt.figure(figsize=(7, 4))
    plt.plot(sizes, latencies, marker="o", color="#6366f1", linewidth=2)
    plt.title("Model In-Memory Training Scale Curve", color="#111827", fontsize=12, fontweight="bold")
    plt.xlabel("Dataset Size (Number of Students)")
    plt.ylabel("Execution Time (milliseconds)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "scaling_time.png"), dpi=200)
    plt.close()
    
    # 2. Memory Footprint Plot
    plt.figure(figsize=(7, 4))
    plt.plot(sizes, memories, marker="s", color="#10b981", linewidth=2)
    plt.title("Peak Memory Usage Scale Curve", color="#111827", fontsize=12, fontweight="bold")
    plt.xlabel("Dataset Size (Number of Students)")
    plt.ylabel("Peak Memory Consumption (MB)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "scaling_memory.png"), dpi=200)
    plt.close()


def generate_markdown_report(ingest: dict, scaling: dict, db_perf: dict, quality: dict, output_dir: str):
    """Outputs a nice Markdown report summarizing results."""
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "benchmark_report.md")
    
    report = f"""# KIU Student Monitoring - System Performance & Model Evaluation Report

This report was automatically generated on the dataset: **{ingest.get('records', 0)} records**.

---

## 1. Data Ingestion Performance
- **File Format Ingested**: {ingest.get('file_type')}
- **Parse Duration**: {ingest.get('latency_ms', 0):.2f} ms
- **Throughput Rate**: {ingest.get('records', 0) / (ingest.get('latency_ms', 1) / 1000):.0f} rows/second

---

## 2. Clustering Model Quality & Generalizability

"""
    
    for model_name, info in quality.items():
        if "error" in info:
            report += f"### {model_name} Model\n- **Status**: {info['error']}\n\n"
            continue
            
        fit_rating = "Strong Structure" if info["silhouette"] > 0.5 else ("Moderate Structure" if info["silhouette"] > 0.25 else "Weak Structure")
        overfit_status = "Overfitting Risk (Review Feature Noise)" if info["possible_overfit"] else "Healthy (Generalizes Well)"
        
        report += f"""### {model_name} Students Model
- **Silhouette Coefficient**: `{info['silhouette']:.4f}` ({fit_rating})
- **Train/Test Generalization**:
  - Training Split Silhouette: `{info['train_silhouette']:.4f}`
  - Test Split Silhouette: `{info['test_silhouette']:.4f}`
  - Generalization Gap: `{info['silhouette_gap']:.4f}`
  - Status: **{overfit_status}**
- **Outlier Density (IQR 1.5x)**: `{info['outliers_flagged']} rows ({info['outliers_percentage']:.2f}%)`
- **Model Inherent Cohesion (WCSS)**: `{info['wcss']:.2f}`

"""
        
    report += f"""---

## 3. Computational Scaling (K-Means Fit Time & Memory)
The table below charts performance as dataset size scales:

| Student Count | Fit Time (ms) | Peak RAM usage (MB) |
|---------------|---------------|---------------------|
"""
    
    for row in scaling["scaling"]:
        report += f"| {row['size']:,} | {row['latency_ms']:.2f} ms | {row['memory_mb']:.4f} MB |\n"
        
    report += f"""
---

## 4. Database Persistence Overhead
Compares inserting `{db_perf['records_written']:,}` student labels to the database using sequential transactions vs bulk insert:
- **Sequential Write Speed**: `{db_perf['sequential_ms']:.2f} ms`
- **Bulk Write Speed**: `{db_perf['bulk_ms']:.2f} ms`
- **Database Speedup Factor**: **{db_perf['speedup_factor']:.2f}x faster** using Bulk Writes

---

*End of Performance Audit Report.*
"""
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Benchmark report generated successfully at: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Run KIU Student Monitoring Performance Benchmark")
    parser.add_argument("--dataset", required=True, help="Path to raw CSV or Excel dataset")
    parser.add_argument("--output-dir", default="app/static/benchmarks", help="Output folder for plots and report")
    args = parser.parse_args()
    
    print(f"Initializing benchmark on file: {args.dataset}")
    
    # 1. Ingestion Benchmark
    ingest_stats = benchmark_ingestion(args.dataset)
    print(f"Data ingestion successful: parsed {ingest_stats['records']} records in {ingest_stats['latency_ms']:.2f} ms.")
    
    # Load DF for downstream benchmarks
    df = pd.read_excel(args.dataset) if args.dataset.lower().endswith(".xlsx") else pd.read_csv(args.dataset)
    
    # Create Flask App Context for DB benchmarks
    app = create_app("testing")
    
    # 2. Scaling Benchmarks
    print("Running Clustering fit scalability benchmarks...")
    scaling_stats = benchmark_clustering_scaling(df)
    
    # 3. DB Benchmarks
    print("Running Database insertion benchmarks...")
    db_stats = benchmark_database_persistence(df, app)
    
    # 4. Model Quality Benchmarks
    print("Evaluating model segmentation quality...")
    quality_stats = benchmark_model_quality(df)
    
    # 5. Output Generation
    print("Saving plots and compiling markdown audit report...")
    generate_plots(scaling_stats["scaling"], args.output_dir)
    generate_markdown_report(ingest_stats, scaling_stats, db_stats, quality_stats, args.output_dir)
    
    # Save a JSON file as well for Web UI consumption
    json_path = os.path.join(args.output_dir, "benchmark_metrics.json")
    with open(json_path, "w") as f:
        json.dump({
            "ingestion": ingest_stats,
            "scaling": scaling_stats,
            "db_perf": db_stats,
            "quality": quality_stats
        }, f, indent=2)


if __name__ == "__main__":
    main()
