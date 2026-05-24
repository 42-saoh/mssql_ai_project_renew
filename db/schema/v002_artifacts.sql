CREATE TABLE artifacts (
  artifact_id TEXT PRIMARY KEY,
  chat_run_id TEXT NOT NULL,
  codex_run_id TEXT,
  artifact_type TEXT NOT NULL,
  title TEXT NOT NULL,
  content_ref TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  production_ready INTEGER NOT NULL DEFAULT 0,
  review_required INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE artifact_validations (
  validation_id TEXT PRIMARY KEY,
  artifact_id TEXT NOT NULL,
  schema_valid INTEGER NOT NULL,
  policy_valid INTEGER NOT NULL,
  static_valid INTEGER NOT NULL,
  blocker_codes TEXT NOT NULL,
  review_markers TEXT NOT NULL,
  created_at TEXT NOT NULL
);
