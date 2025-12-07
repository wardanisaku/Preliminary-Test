# Preliminary-Test

## Project Execution Guide

This project consists of four sequential stages. Run them in order:

### 1. Data Generation

| File | Description | Execution |
| :--- | :--- | :--- |
| `1_generate_database/generate_data.py` | Creates initial data files (e.g., `orders.csv`). **Run first.** | `python 1_generate_database/generate_data.py` |

### 2. Database & SQL Analysis

| File | Description | Execution |
| :--- | :--- | :--- |
| `2_database_and_SQL/create_db.sql` | Sets up the database schema. | Run in SQL Client. |
| `2_database_and_SQL/*.sql` | SQL queries for best-seller, delivery, and new user analysis. | Run in SQL Client. |

### 3. Statistics

| File | Description | Execution |
| :--- | :--- | :--- |
| `3_statistics/statistics.ipynb` | Performs statistical analysis on data like `kulina_data.csv`. | `jupyter notebook 3_statistics/statistics.ipynb` |

### 4. Data Visualization

| File | Description | Execution |
| :--- | :--- | :--- |
| `4_data_visualization/visualization.py` | Generates final visualizations and reports. | `python 4_data_visualization/visualization.py` |

***

### 📝 Key Outputs

Final business recommendations are found in the `.txt` files within the `3_statistics` and `4_data_visualization` directories.
