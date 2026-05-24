CREATE TABLE approval_requests (
  approval_id TEXT PRIMARY KEY,
  chat_run_id TEXT NOT NULL,
  approval_type TEXT NOT NULL,
  status TEXT NOT NULL,
  reason TEXT NOT NULL,
  requested_at TEXT NOT NULL,
  resolved_at TEXT
);
