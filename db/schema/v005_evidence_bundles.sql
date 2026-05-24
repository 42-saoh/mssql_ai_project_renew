CREATE TABLE evidence_bundles (
  evidence_bundle_id TEXT PRIMARY KEY,
  db_profile_id TEXT NOT NULL,
  target_key TEXT NOT NULL,
  evidence_hash TEXT NOT NULL,
  content_ref TEXT NOT NULL,
  collected_at TEXT NOT NULL
);
