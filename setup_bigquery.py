"""
Run once to create the BigQuery dataset and table.
Usage: python setup_bigquery.py
"""
import os
from google.cloud import bigquery

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
DATASET_ID = "research_agent"
TABLE_ID = "runs"

client = bigquery.Client(project=PROJECT_ID)

# Create dataset
dataset = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
dataset.location = "US"
try:
    dataset = client.create_dataset(dataset)
    print(f"Created dataset {DATASET_ID}")
except Exception:
    print(f"Dataset {DATASET_ID} already exists")

# Create table with schema
schema = [
    bigquery.SchemaField("run_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("company", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("summary", "STRING"),
    bigquery.SchemaField("sentiment", "STRING"),
    bigquery.SchemaField("topics_count", "INTEGER"),
    bigquery.SchemaField("artifact_url", "STRING"),
]

table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
table = bigquery.Table(table_ref, schema=schema)

try:
    table = client.create_table(table)
    print(f"Created table {TABLE_ID}")
except Exception:
    print(f"Table {TABLE_ID} already exists")

print("BigQuery setup complete.")
