"""Load a real-world auto-insurance fraud dataset into PostgreSQL.

Source: a public, widely used educational dataset of 1000 auto-insurance claims
labeled with a `fraud_reported` (Y/N) target. It is downloaded on demand (not
committed to the repo) and loaded into a `real_claims` table.

This gives the project real, labeled data for training and evaluating the fraud
classifier, alongside the synthetic narratives used by the LLM agents.

Run as a script:  python -m insurclaim.data.load_real
"""

from __future__ import annotations

import csv
import urllib.request
from pathlib import Path

from insurclaim.db import repo

SOURCE_URL = (
    "https://raw.githubusercontent.com/mwitiderrick/insurancedata/master/"
    "insurance_claims.csv"
)
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "real"
CSV_PATH = DATA_DIR / "insurance_claims.csv"
TABLE = "real_claims"


def _download_if_missing() -> Path:
    """Download the dataset once; reuse the local copy afterwards."""
    if CSV_PATH.exists():
        return CSV_PATH
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading dataset from {SOURCE_URL} ...")
    urllib.request.urlretrieve(SOURCE_URL, CSV_PATH)
    return CSV_PATH


def _column_name(raw: str) -> str:
    """Make a CSV header safe to use as a SQL column name."""
    return raw.strip().lower().replace("-", "_").replace(" ", "_")


def load() -> int:
    """Create the real_claims table and load every row. Returns the row count."""
    path = _download_if_missing()

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        raw_headers = [h for h in reader.fieldnames or [] if h and h.strip()]
        columns = [_column_name(h) for h in raw_headers]
        rows = list(reader)

    # Every source column is stored as TEXT (the data mixes numbers, dates, and
    # '?' placeholders); we add a clean boolean label derived from fraud_reported.
    column_defs = ",\n    ".join(f'"{c}" TEXT' for c in columns)
    create_sql = f"""
    DROP TABLE IF EXISTS {TABLE};
    CREATE TABLE {TABLE} (
        id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        {column_defs},
        is_fraud BOOLEAN
    );
    """

    insert_columns = ", ".join(f'"{c}"' for c in columns) + ", is_fraud"
    placeholders = ", ".join(["%s"] * len(columns)) + ", %s"
    insert_sql = f"INSERT INTO {TABLE} ({insert_columns}) VALUES ({placeholders})"

    records = []
    for row in rows:
        values = [row.get(h) for h in raw_headers]
        is_fraud = (row.get("fraud_reported") or "").strip().upper() == "Y"
        records.append((*values, is_fraud))

    with repo.get_connection() as conn, conn.cursor() as cur:
        cur.execute(create_sql)
        cur.executemany(insert_sql, records)
        conn.commit()

    return len(records)


if __name__ == "__main__":
    count = load()
    print(f"Loaded {count} real claims into the '{TABLE}' table.")
