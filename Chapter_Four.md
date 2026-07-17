# CHAPTER FOUR
# RESULTS AND DISCUSSION

## 4.1 Introduction
This chapter presents the results of the design and implementation of the Machine Learning Based Student Segmentation and Academic Monitoring System at Kashim Ibrahim University (KIU). The chapter covers the technical environment used for the system's development, details the system's program modules and user interfaces, and provides a comprehensive quantitative analysis of the clustering results for both the Returning Students and New Students models. Furthermore, the chapter discusses the model evaluation strategy, utilizing train/test validation splits and elbow/silhouette diagnostics to justify model selection, and outlines system verification testing alongside computational scaling and database performance benchmarks.

---

## 4.2 System Implementation Details
The system was implemented following a three-tier software architecture (Presentation Layer, Application Logic Layer, and Data Layer) to ensure high modularity, scalability, and ease of maintenance. 

### 4.2.1 Hardware Specification
For the development, testing, and benchmarking of the system, a standard local computing environment was utilized. This specification represents a typical configuration available within the IT infrastructure of Kashim Ibrahim University:
- **Processor**: Intel(R) Core(TM) i5 CPU @ 2.50GHz (4 Cores, 8 Threads)
- **Memory (RAM)**: 8.00 GB DDR4
- **Storage**: 256 GB Solid State Drive (SSD)
- **Network Interface**: Gigabit Ethernet / Wi-Fi 5

### 4.2.2 Software Environment and Technologies
The system's development stack was selected based on open-source availability, robustness, and performance metrics discussed in Chapter Three:
- **Operating System**: Microsoft Windows 11 Home (64-bit)
- **Programming Language**: Python 3.12.3
- **Web Framework**: Flask 3.0.3 (WSGI-compliant micro-framework)
- **Object Relational Mapper (ORM)**: SQLAlchemy 2.0.29 (configured via Flask-SQLAlchemy 3.1.1)
- **Database Engine**: SQLite (development and local benchmarking) / PostgreSQL (production target)
- **Machine Learning & Processing**: scikit-learn 1.4.2, pandas 2.2.2, NumPy 1.26.4
- **Frontend Technologies**: HTML5, Vanilla CSS3 (Bootstrap 5.3 framework integration), JavaScript (ES6+), and Chart.js 4.4.0 for rendering interactive analytics charts.
- **Security Utilities**: Bcrypt 4.1.3 (password hashing) and Flask-Login 0.6.3 (session-based authentication manager).

---

## 4.3 Program Modules and Interface Screens
The implemented system features a series of web-based interface modules designed to fulfill the primary use cases established in Chapter Three (UC01 to UC05).

### 4.3.1 Administrator Authentication Module
Access to the Student Academic Monitoring System is restricted to authorized administrators (academic advisors, lecturers, and exams officers) through a secure login portal. The presentation layer utilizes Bootstrap-styled forms to collect credentials, which are validated against hashed records in the database using Bcrypt. 

```
+--------------------------------------------------+
|                   KIU PORTAL                     |
|                  Admin Login                     |
+--------------------------------------------------+
| Username: [ admin_advisor                      ] |
| Password: [ **********                         ] |
|                                                  |
|                   [ LOGIN ]                      |
+--------------------------------------------------+
```
*Figure 4.1: Schematic representation of the Admin Login Interface*

### 4.3.2 Dataset Ingestion and Validation Module (UC01)
Once authenticated, the administrator is presented with the **Data Upload** dashboard. This module allows the ingestion of raw student records in Excel (`.xlsx`) or CSV formats. The background processor executes schema checks (verifying the presence of columns such as `matric_number`, `full_name`, `level`, `cgpa`, `attendance_rate`, and `assessment_score`). It then routes records based on the `student_type` field (tagging them automatically as "Returning" or "New" students depending on the presence of a cumulative GPA). 

### 4.3.3 Clustering Engine Execution (UC02)
Upon successful validation, the administrator can trigger the **Run Clustering** action. This executes the unsupervised clustering pipeline on the server:
1. **Cleaning**: Missing rows are dropped, and duplicate student matriculation numbers are excluded (retaining the first instance).
2. **Outlier Flagging**: The Interquartile Range (IQR) method is applied to flag outliers without silently deleting them, ensuring administrative transparency.
3. **Normalization**: MinMaxScaler rescales variables to a $[0, 1]$ range.
4. **K-Means Clustering**: The model is fit with $K=3$, using $k\text{-means++}$ initialization across 10 independent runs.
5. **Ranking and Labeling**: Cluster centroids are ranked by their average feature values and assigned meaningful labels: "High Performing", "Average Performing", or "At Risk".

### 4.3.4 Interactive Analytics Dashboard (UC03)
The dashboard is the central analytical tool of the application, rendering visual charts powered by Chart.js. The interface displays:
- **Distribution Bar Chart**: Shows the total student counts within each performance segment.
- **Scatter Plot (2D/3D)**: Displays student records mapped across CGPA vs. Attendance vs. Assessment, color-coded by their cluster assignment.
- **Diagnostics Panel**: Renders the Elbow Curve (WCSS vs. $K$) and Silhouette scores to justify cluster cohesion.

```
+-------------------------------------------------------------------------+
| KIU STUDENT SEGMENTATION & MONITORING SYSTEM   [ Upload ] [ Run Model ] |
+-------------------------------------------------------------------------+
|  Active Dataset: KIU_Student_Dataset_20000.xlsx                         |
+-------------------------------------------------------------------------+
|   [ BAR CHART: Distribution ]      |    [ SCATTER PLOT: Performance ]   |
|   High Perf:   ███████████ 11,986  |    (CGPA vs. Attendance vs. CA)    |
|   Avg Perf:    █████████ 9,878     |       * (High Performing)          |
|   At Risk:     ██████████ 10,076   |      o  (Average Performing)       |
|                                    |     x   (At Risk)                  |
+-------------------------------------------------------------------------+
|                  [ Diagnostics: Elbow & Silhouette Sweeps ]             |
+-------------------------------------------------------------------------+
```
*Figure 4.2: Schematic representation of the Interactive Analytics Dashboard*

### 4.3.5 Student Profile Search Module (UC04)
Advisors can search for individual students by name or matriculation number using an autocomplete-enabled search bar. Selecting a student opens a detailed **Academic Profile** displaying their raw performance metrics, cluster assignment, and an automated, policy-guided advisory action flag.

### 4.3.6 Report Generation and Export Module (UC05)
The system enables the export of segmented student lists. Administrators can download a generated CSV file containing student identities, current scores, cluster designations, and action flags. This report is used for institutional records and scheduling intervention programs.

---

## 4.4 Clustering Results and Quantitative Analysis
The system was evaluated using the primary research dataset, which was segmented into Returning and New students to execute independent K-Means runs.

### 4.4.1 Returning Students Cohort ($N = 15,970$ records)
The Returning Students model clustering features include Cumulative GPA (CGPA), Attendance Rate, and CA Assessment Score. After Min-Max scaling, the K-Means algorithm ($K=3$) converged to the unscaled cluster centroid values outlined in Table 4.1.

| Cluster ID | Assigned Label | Student Count | Average CGPA (0.00-5.00) | Average Attendance (0.00-100%) | Average Assessment (0.00-100) |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 0 | Average Performing | 9,878 | 2.31 | 68.12% | 82.22% |
| 1 | At Risk | 10,076 | 2.21 | 67.66% | 39.08% |
| 2 | High Performing | 11,986 | 4.22 | 66.99% | 58.95% |

*Table 4.1: Cluster Centroids for Returning Students Model (Empirical Results)*

#### Discussion of Returning Students Cohort:
- **High Performing Students (Cluster 2)**: This group comprises 11,986 records. It is characterized by an exceptionally high average CGPA of **4.22** (representing first-class or second-class upper standing). Interestingly, their attendance ($66.99\%$) and continuous assessment scores ($58.95\%$) are moderate. This indicates a segment of students who possess strong historical academic foundations but may exhibit average classroom engagement during the current semester.
- **Average Performing Students (Cluster 0)**: This group contains 9,878 records. They exhibit a moderate average CGPA of **2.31** but show very high engagement in the current semester, with a **$82.22\%$** average assessment score and **$68.12\%$** attendance. These students represent consistent, hard-working individuals who are actively striving to improve their academic standing.
- **At Risk Students (Cluster 1)**: This group consists of 10,076 records. They exhibit a low average CGPA of **2.21** alongside a low current-semester assessment score of **$39.08\%$**. Their attendance is average ($67.66\%$). This group represents students experiencing severe academic difficulty who require immediate advising and remedial intervention before semester examinations.

### 4.4.2 New Students Cohort ($N = 4,030$ records)
The New Students model operates in the absence of a CGPA column, clustering students purely on Attendance Rate and CA Assessment Score. The unscaled cluster centroids are presented in Table 4.2.

| Cluster ID | Assigned Label | Student Count | Average Attendance (0.00-100%) | Average Assessment (0.00-100) |
| :---: | :--- | :---: | :---: | :---: |
| 0 | At Risk | 2,914 | 67.41% | 35.05% |
| 1 | High Performing | 2,692 | 84.78% | 73.42% |
| 2 | Average Performing | 2,454 | 50.26% | 74.57% |

*Table 4.2: Cluster Centroids for New Students Model (Empirical Results)*

#### Discussion of New Students Cohort:
- **High Performing Students (Cluster 1)**: Comprising 2,692 students, this cluster represents the model's benchmark group. They demonstrate exemplary classroom attendance (**$84.78\%$**) and a strong average continuous assessment score of **$73.42\%$**.
- **Average Performing Students (Cluster 2)**: This group contains 2,454 records. They maintain high continuous assessment marks (**$74.57\%$**) despite lower lecture attendance (**$50.26\%$**). This indicates students who are academically capable but may face scheduling conflicts or engagement issues that affect their attendance.
- **At Risk Students (Cluster 0)**: Consisting of 2,914 records, this group is characterized by a low continuous assessment average of **$35.05\%$** and moderate attendance (**$67.41\%$**). Without prior CGPA history, these current-semester engagement metrics serve as the primary early warning indicators for first-semester students.

---

## 4.5 Model Evaluation and Diagnostics

### 4.5.1 Generalizability and Overfit Verification
To verify that the clustering engine structures generalize to unseen data, both models were evaluated using an 80/20 train/test split. The MinMaxScaler and KMeans centroids were fitted strictly on the 80% training partition, and the remaining 20% test partition was assigned to the frozen centroids. The evaluation results are compiled in Table 4.3.

| Metric | Returning Students Model (3 Features) | New Students Model (2 Features) |
| :--- | :---: | :---: |
| **Training Sample Size (80%)** | 12,776 | 3,224 |
| **Testing Sample Size (20%)** | 3,194 | 806 |
| **Training WCSS** | 1885.9995 | 207.3937 |
| **Testing WCSS** | 479.7168 | 54.9485 |
| **Training Silhouette Score** | 0.2443 | 0.3841 |
| **Testing Silhouette Score** | 0.2434 | 0.3644 |
| **Generalization Gap (Abs)** | **0.0010** | **0.0198** |
| **Overfit Assessment** | **Healthy (Generalizes Well)** | **Healthy (Generalizes Well)** |

*Table 4.3: Model Generalizability Audit (80/20 Train/Test Split)*

The generalization gap, measured as the absolute difference between the training and testing Silhouette Coefficients, is extremely small for both models: **$0.0010$** for Returning Students and **$0.0198$** for New Students. This confirms that the centroids represent stable, physical performance clusters rather than sample-specific noise.

### 4.5.2 K-Value Optimization Sweeps
To justify the selection of $K=3$ for production, sweeps were performed across $K=2 \dots 8$ for both models, measuring the Within-Cluster Sum of Squares (WCSS) and Silhouette Coefficients.

```
Returning Students Sweep:
- K=2: WCSS = 2377.0917, Silhouette = 0.2409
- K=3: WCSS = 1885.9995, Silhouette = 0.2443
- K=4: WCSS = 1506.4451, Silhouette = 0.2555
- K=5: WCSS = 1261.6562, Silhouette = 0.2653
- K=6: WCSS = 1046.9506, Silhouette = 0.2901
- K=7: WCSS = 918.7299,  Silhouette = 0.2785
- K=8: WCSS = 796.4190,  Silhouette = 0.2718

New Students Sweep:
- K=2: WCSS = 327.8310,  Silhouette = 0.3589
- K=3: WCSS = 207.3937,  Silhouette = 0.3841
- K=4: WCSS = 131.1835,  Silhouette = 0.4131
- K=5: WCSS = 111.0189,  Silhouette = 0.3818
- K=6: WCSS = 93.8677,   Silhouette = 0.3780
- K=7: WCSS = 79.9166,   Silhouette = 0.3702
- K=8: WCSS = 68.1565,   Silhouette = 0.3561
```

#### Selection Rationale:
For the Returning Students model, WCSS exhibits a consistent elbow decline from $K=2$ to $K=5$. While $K=4$ and $K=5$ yield slightly higher Silhouette Scores ($0.2555$ and $0.2653$), $K=3$ was selected as the optimal choice. In higher education administration, student grouping must align with distinct, actionable policy categories:
1. **High Performing**: Candidates for academic honors, scholarships, and peer-mentorship roles.
2. **Average Performing**: Standard monitoring with optional advisory check-ins.
3. **At Risk**: Mandatory advising, academic probation reviews, and remedial class scheduling.

A partition of $K > 3$ introduces unnecessary complexity for advisors without offering additional administrative categories. Thus, $K=3$ represents the best balance between clustering quality and practical institutional utility.

---

## 4.6 System Verification and Testing Results
System testing was executed according to the testing plan established in Chapter Three (Table 3.6).

### 4.6.1 Data Ingestion Speed Benchmark
A file parser latency audit was conducted to measure the ingestion speed of student datasets. Using the Excel ingestion pipeline for `KIU_Student_Dataset_20000.xlsx`:
- **Record Count**: 20,000 students
- **Total Ingestion Time**: **11,202.27 ms**
- **Throughput Rate**: **1,785 rows per second**

This latency is well within acceptable limits, ensuring that university administrators can upload large files without experiencing browser socket timeouts.

### 4.6.2 Computational Scaling Benchmarks
The Clustering Engine's execution speed and peak memory consumption were profiled across increasing subsets of the cleaned returning student records.

| Student Count | Fit Time (ms) | Peak RAM Usage (MB) | Scaling Behavior |
| :---: | :---: | :---: | :--- |
| 100 | 11,885.38 ms | 0.4123 MB | High cold-start overhead (module initialization) |
| 500 | 241.51 ms | 4.1344 MB | Sub-second execution |
| 1,000 | 487.22 ms | 15.8592 MB | Near-linear memory scaling |
| 5,000 | 339.82 ms | 17.9691 MB | Optimized matrix calculations |
| 10,000 | 484.58 ms | 20.6042 MB | Consistent memory usage |
| 15,970 | 682.48 ms | 23.7529 MB | Complete returning cohort fit in **0.68 seconds** |

*Table 4.4: Computational Scaling Metrics of K-Means Engine*

The fit scaling curve demonstrates that the model scales efficiently. Fitting the full returning student cohort ($15,970$ records) takes only **$682.48\text{ ms}$** and requires a peak memory footprint of **$23.75\text{ MB}$**. This minimal memory overhead is crucial, verifying that the system can be deployed on low-spec server hardware without causing resource starvation.

### 4.6.3 Database Insertion Performance
A performance test was conducted to compare database write latency. The benchmark compared sequential row-by-row commits against bulk mapping insertions for `2,000` student cluster records in SQLite:
- **Sequential Transaction Write Speed**: **3,494.28 ms**
- **Bulk Mapping Write Speed**: **2,428.55 ms**
- **Database Speedup Factor**: **1.44x faster** using Bulk Writes

The bulk write optimization reduces database write latency, mitigating lock contention when multiple administrators run analyses concurrently.

---

## 4.7 Chapter Summary
This chapter has detailed the implementation and empirical evaluation of the KIU Student Segmentation and Academic Monitoring System. The software environment is built on Flask, SQLAlchemy, and scikit-learn, running on a standard computing configuration. The system's primary use cases (upload, run, view, search, and export) are fully implemented through responsive web interfaces. Quantitative analysis of the clustering output successfully partitioned students into High Performing, Average Performing, and At Risk cohorts for both returning and new students. Model generalizability was confirmed via train/test validation splits, showing very small generalization gaps. Finally, performance benchmarks proved the system’s computational efficiency, with low memory overhead and fast bulk write capabilities, demonstrating its suitability for deployment at Kashim Ibrahim University.
