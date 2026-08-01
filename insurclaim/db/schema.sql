-- InsurClaim AI - PostgreSQL schema
-- Relational store for auto insurance claims and everything attached to a claim.
-- One claim has many parties, vehicles, and photos, so those live in separate
-- tables that reference the claim. Indexes on national_id / vin / phash make the
-- "velocity" checks (repeat claimant, reused vehicle, duplicate photo) fast.
--
-- "IF NOT EXISTS" makes this file safe to run more than once without errors.

-- Insurance policies. A claim is filed against one policy.
CREATE TABLE IF NOT EXISTS policies (
    policy_number   TEXT PRIMARY KEY,            -- human-readable policy id
    holder_name     TEXT NOT NULL,               -- name of the policy holder
    start_date      DATE NOT NULL,               -- coverage start
    end_date        DATE NOT NULL,               -- coverage end (used for "policy active?" checks)
    coverage_limit  NUMERIC(12, 2) NOT NULL,     -- max payable amount (used for "amount vs limit" checks)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- The core claim record.
CREATE TABLE IF NOT EXISTS claims (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- auto-incrementing id
    policy_number       TEXT REFERENCES policies(policy_number),          -- which policy this claim is against
    incident_date       DATE NOT NULL,           -- when the accident happened
    report_date         DATE NOT NULL,           -- when the claim was filed
    location            TEXT,                    -- where the incident happened
    description         TEXT,                    -- the described sequence of events (narrative)
    claimed_amount      NUMERIC(12, 2),          -- amount the claimant is asking for

    -- Ground-truth labels. We only have these because the data is SYNTHETIC.
    -- They feed both the fine-tuning training set and the evaluation harness.
    is_fraud            BOOLEAN,                 -- true = this claim was generated as fraud
    fraud_type          TEXT,                    -- e.g. 'staged_collision', 'duplicate_photo' (NULL if legit)

    -- Pipeline outputs, filled in after the agents run (NULL until then).
    risk_score          NUMERIC,                 -- overall risk score from the report agent
    recommended_action  TEXT,                    -- route_to_investigator / fast_track_approve / request_more_info

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- People involved in a claim (claimant, other driver, witness, ...).
CREATE TABLE IF NOT EXISTS parties (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    claim_id     BIGINT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,  -- delete parties if the claim is deleted
    full_name    TEXT NOT NULL,
    role         TEXT,                            -- 'claimant', 'other_driver', 'witness'
    national_id  TEXT,                            -- stable person id, used for repeat-claimant velocity
    phone        TEXT,
    email        TEXT
);

-- Vehicles involved in a claim.
CREATE TABLE IF NOT EXISTS vehicles (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    claim_id   BIGINT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    vin        TEXT,                              -- vehicle identification number, used for repeat-VIN velocity
    make       TEXT,                              -- e.g. 'Toyota'
    model      TEXT,                              -- e.g. 'Corolla'
    year       INTEGER,
    plate      TEXT                               -- license plate
);

-- Perceptual hashes of damage photos, used to detect the same photo
-- being reused across different claims (a common fraud signal).
CREATE TABLE IF NOT EXISTS photo_hashes (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    claim_id     BIGINT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    file_name    TEXT,                            -- original photo file name
    phash        TEXT NOT NULL,                   -- perceptual hash string (imagehash)
    captured_at  TIMESTAMPTZ                      -- capture time from EXIF metadata (NULL if missing)
);

-- Policy documents uploaded by an insurer (their own policies / rules), used by
-- the coverage engine to check whether an incoming claim is covered.
CREATE TABLE IF NOT EXISTS policy_documents (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company      TEXT,                            -- which insurer owns this document
    doc_name     TEXT,                            -- a human-readable name
    content      TEXT NOT NULL,                   -- the policy text (indexed for RAG)
    uploaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Investigator case management: status/assignee per claim and an append-only
-- notes trail (audit-defensible).
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

-- Indexes that make the cross-claim "velocity" lookups fast.
CREATE INDEX IF NOT EXISTS idx_parties_national_id  ON parties (national_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_vin         ON vehicles (vin);
CREATE INDEX IF NOT EXISTS idx_photo_hashes_phash   ON photo_hashes (phash);
CREATE INDEX IF NOT EXISTS idx_claims_policy_number ON claims (policy_number);
