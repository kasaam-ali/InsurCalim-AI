"""Database access layer (repository) for InsurClaim AI.

All PostgreSQL reads and writes live here so the rest of the code never writes
raw SQL. Connection settings come from environment variables (see .env.example).
Also contains the "velocity" queries (repeat claimant / repeat VIN / duplicate
photo) that power the deterministic fraud checks.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

# Load database credentials from .env so this layer works even when imported on
# its own (without going through llm.py). Safe to call once at import time.
load_dotenv()

# Path to the schema file that lives next to this module.
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _dsn() -> str:
    """Build a PostgreSQL connection string from environment variables."""
    return (
        f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
        f"port={os.getenv('POSTGRES_PORT', '5432')} "
        f"dbname={os.getenv('POSTGRES_DB', 'insurclaim')} "
        f"user={os.getenv('POSTGRES_USER', 'insurclaim')} "
        f"password={os.getenv('POSTGRES_PASSWORD', '')}"
    )


def get_connection() -> psycopg.Connection:
    """Open a new database connection. Rows are returned as dictionaries."""
    return psycopg.connect(_dsn(), row_factory=dict_row)


def init_schema() -> None:
    """Create all tables by running schema.sql. Safe to run repeatedly."""
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()


# --- Inserts -------------------------------------------------------------

def insert_policy(policy: dict[str, Any]) -> None:
    """Insert one policy row."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO policies (policy_number, holder_name, start_date, end_date, coverage_limit)
            VALUES (%(policy_number)s, %(holder_name)s, %(start_date)s, %(end_date)s, %(coverage_limit)s)
            ON CONFLICT (policy_number) DO NOTHING
            """,
            policy,
        )
        conn.commit()


def insert_claim(claim: dict[str, Any]) -> int:
    """Insert one claim and return its generated id."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO claims
                (policy_number, incident_date, report_date, location, description,
                 claimed_amount, is_fraud, fraud_type)
            VALUES
                (%(policy_number)s, %(incident_date)s, %(report_date)s, %(location)s,
                 %(description)s, %(claimed_amount)s, %(is_fraud)s, %(fraud_type)s)
            RETURNING id
            """,
            claim,
        )
        claim_id = cur.fetchone()["id"]
        conn.commit()
        return claim_id


def insert_party(claim_id: int, party: dict[str, Any]) -> None:
    """Insert one party linked to a claim."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO parties (claim_id, full_name, role, national_id, phone, email)
            VALUES (%(claim_id)s, %(full_name)s, %(role)s, %(national_id)s, %(phone)s, %(email)s)
            """,
            {"claim_id": claim_id, **party},
        )
        conn.commit()


def insert_vehicle(claim_id: int, vehicle: dict[str, Any]) -> None:
    """Insert one vehicle linked to a claim."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO vehicles (claim_id, vin, make, model, year, plate)
            VALUES (%(claim_id)s, %(vin)s, %(make)s, %(model)s, %(year)s, %(plate)s)
            """,
            {"claim_id": claim_id, **vehicle},
        )
        conn.commit()


def insert_photo_hash(claim_id: int, photo: dict[str, Any]) -> None:
    """Insert one photo hash linked to a claim."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO photo_hashes (claim_id, file_name, phash, captured_at)
            VALUES (%(claim_id)s, %(file_name)s, %(phash)s, %(captured_at)s)
            """,
            {"claim_id": claim_id, **photo},
        )
        conn.commit()


# --- Reads ---------------------------------------------------------------

def get_claim(claim_id: int) -> dict[str, Any] | None:
    """Return a claim plus its policy, parties, vehicles, and photo hashes."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM claims WHERE id = %s", (claim_id,))
        claim = cur.fetchone()
        if claim is None:
            return None

        cur.execute("SELECT * FROM parties WHERE claim_id = %s", (claim_id,))
        claim["parties"] = cur.fetchall()

        cur.execute("SELECT * FROM vehicles WHERE claim_id = %s", (claim_id,))
        claim["vehicles"] = cur.fetchall()

        cur.execute("SELECT * FROM photo_hashes WHERE claim_id = %s", (claim_id,))
        claim["photos"] = cur.fetchall()

        if claim["policy_number"]:
            cur.execute(
                "SELECT * FROM policies WHERE policy_number = %s",
                (claim["policy_number"],),
            )
            claim["policy"] = cur.fetchone()
        else:
            claim["policy"] = None

        return claim


def list_labeled_claims() -> list[dict[str, Any]]:
    """Return all claims that have a ground-truth label (for training / eval)."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, description, is_fraud, fraud_type FROM claims WHERE is_fraud IS NOT NULL"
        )
        return cur.fetchall()


def list_real_claims() -> list[dict[str, Any]]:
    """Return every row of the real-world dataset (loaded by data.load_real)."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM real_claims")
        return cur.fetchall()


def get_real_claim(claim_id: int) -> dict[str, Any] | None:
    """Return a single row from the real-world dataset by its id."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM real_claims WHERE id = %s", (claim_id,))
        return cur.fetchone()


# --- Policy documents (an insurer uploads their own policies/rules) -------

def _ensure_policy_documents_table() -> None:
    """Create the policy_documents table on demand (safe to call repeatedly)."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS policy_documents (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                company TEXT,
                doc_name TEXT,
                content TEXT NOT NULL,
                uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.commit()


def insert_policy_document(company: str, doc_name: str, content: str) -> int:
    """Store an uploaded policy document and return its id."""
    _ensure_policy_documents_table()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO policy_documents (company, doc_name, content) "
            "VALUES (%s, %s, %s) RETURNING id",
            (company, doc_name, content),
        )
        doc_id = cur.fetchone()["id"]
        conn.commit()
        return doc_id


def list_policy_documents() -> list[dict[str, Any]]:
    """List uploaded policy documents (with a short preview of each)."""
    _ensure_policy_documents_table()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, company, doc_name, LEFT(content, 160) AS preview, uploaded_at "
            "FROM policy_documents ORDER BY id"
        )
        return cur.fetchall()


def get_policy_document(doc_id: int) -> dict[str, Any] | None:
    """Return a single policy document (including its full content)."""
    _ensure_policy_documents_table()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, company, doc_name, content, uploaded_at "
            "FROM policy_documents WHERE id = %s",
            (doc_id,),
        )
        return cur.fetchone()


def delete_policy_document(doc_id: int) -> None:
    """Delete an uploaded policy document by id."""
    _ensure_policy_documents_table()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM policy_documents WHERE id = %s", (doc_id,))
        conn.commit()


# --- Case management (investigator status + notes per claim) --------------

def _ensure_case_tables() -> None:
    """Create the case status + notes tables on demand."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS case_status (
                claim_ref   TEXT PRIMARY KEY,
                status      TEXT NOT NULL DEFAULT 'open',
                assignee    TEXT,
                updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS case_notes (
                id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                claim_ref   TEXT NOT NULL,
                note        TEXT NOT NULL,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        )
        conn.commit()


def set_case_status(claim_ref: str, status: str, assignee: str | None) -> None:
    """Upsert the investigation status / assignee for a claim."""
    _ensure_case_tables()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO case_status (claim_ref, status, assignee, updated_at)
            VALUES (%s, %s, %s, now())
            ON CONFLICT (claim_ref) DO UPDATE
                SET status = EXCLUDED.status, assignee = EXCLUDED.assignee, updated_at = now()
            """,
            (claim_ref, status, assignee),
        )
        conn.commit()


def get_case_status(claim_ref: str) -> dict[str, Any] | None:
    """Return the case status row for a claim, if any."""
    _ensure_case_tables()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT status, assignee, updated_at FROM case_status WHERE claim_ref = %s",
                    (claim_ref,))
        return cur.fetchone()


def add_case_note(claim_ref: str, note: str) -> None:
    """Append an investigator note to a claim."""
    _ensure_case_tables()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO case_notes (claim_ref, note) VALUES (%s, %s)", (claim_ref, note))
        conn.commit()


def list_case_notes(claim_ref: str) -> list[dict[str, Any]]:
    """Return all notes for a claim, newest last."""
    _ensure_case_tables()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT note, created_at FROM case_notes WHERE claim_ref = %s ORDER BY id",
                    (claim_ref,))
        return cur.fetchall()


# --- Velocity / duplicate checks (used by deterministic fraud rules) -----

def count_claims_by_national_id(national_id: str, exclude_claim_id: int | None = None) -> int:
    """How many other claims involve a party with this national id?"""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(DISTINCT claim_id) AS n
            FROM parties
            WHERE national_id = %s AND claim_id <> COALESCE(%s, -1)
            """,
            (national_id, exclude_claim_id),
        )
        return cur.fetchone()["n"]


def count_claims_by_vin(vin: str, exclude_claim_id: int | None = None) -> int:
    """How many other claims involve this VIN?"""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(DISTINCT claim_id) AS n
            FROM vehicles
            WHERE vin = %s AND claim_id <> COALESCE(%s, -1)
            """,
            (vin, exclude_claim_id),
        )
        return cur.fetchone()["n"]


def find_duplicate_photos(phash: str, exclude_claim_id: int | None = None) -> list[dict[str, Any]]:
    """Return photo rows from other claims that share this perceptual hash."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT claim_id, file_name FROM photo_hashes
            WHERE phash = %s AND claim_id <> COALESCE(%s, -1)
            """,
            (phash, exclude_claim_id),
        )
        return cur.fetchall()


# --- Writes for pipeline output ------------------------------------------

def update_claim_result(claim_id: int, risk_score: float, recommended_action: str) -> None:
    """Store the pipeline's final risk score and recommended action on the claim."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE claims SET risk_score = %s, recommended_action = %s WHERE id = %s",
            (risk_score, recommended_action, claim_id),
        )
        conn.commit()
