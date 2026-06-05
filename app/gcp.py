import os
import json
from datetime import datetime

from google.cloud import storage, bigquery, secretmanager


# ── Secret Manager ──────────────────────────────────────────────────────────
# Secret Manager stores secrets as versioned blobs. 
# This code fetches the latest version of a secret and loads it into an environment variable at startup.
# This way, API keys and other secrets are never hardcoded or stored in plaintext in your codebase.
# Response comes back as bytes, so decode it to a string before returning.

def get_secret(secret_id: str) -> str:
    """Fetch a secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ["GCP_PROJECT_ID"]
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def load_secrets_to_env():
    """Call once at startup to load API keys from Secret Manager into env vars."""
    try:
        os.environ["ANTHROPIC_API_KEY"] = get_secret("anthropic-api-key")
    except Exception as e:
        print(f"Warning: Could not load secrets from Secret Manager: {e}")
        print("Falling back to environment variables.")


# ── Cloud Storage ────────────────────────────────────────────────────────────

# This function uploads a string (like a JSON summary) to GCS and returns the gs:// URI.

def upload_to_gcs(blob_path: str, content: str) -> str:
    """Upload a string to GCS and return the public-ish gs:// URI."""
    bucket_name = os.environ["GCS_BUCKET_NAME"]
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_string(content, content_type="application/json")
    return f"gs://{bucket_name}/{blob_path}"


# ── BigQuery ─────────────────────────────────────────────────────────────────

BQ_DATASET = "research_agent"
BQ_TABLE = "runs"

# BigQuery uses streaming inserts via insert_rows_json
# Pass a list of dicts, where each dict is a row to insert.
# Streaming inserts appear in the table within seconds but have a small cost per GB inserted
def log_to_bigquery(row: dict):
    """Insert a research run record into BigQuery."""
    project_id = os.environ["GCP_PROJECT_ID"]
    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.{BQ_DATASET}.{BQ_TABLE}"

    errors = client.insert_rows_json(table_id, [row])
    if errors:
        print(f"BigQuery insert errors: {errors}")

# SQL query to fetch recent runs, ordered by timestamp. Limit is parameterized.
def query_bigquery(limit: int = 20) -> list[dict]:
    """Fetch recent research runs from BigQuery."""
    project_id = os.environ["GCP_PROJECT_ID"]
    client = bigquery.Client(project=project_id)

    query = f"""
        SELECT run_id, company, timestamp, summary, sentiment, topics_count, artifact_url
        FROM `{project_id}.{BQ_DATASET}.{BQ_TABLE}`
        ORDER BY timestamp DESC
        LIMIT {limit}
    """

    rows = client.query(query).result()
    return [dict(row) for row in rows]
