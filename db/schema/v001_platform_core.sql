CREATE TABLE conversations (
  conversation_id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  title TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE chat_runs (
  chat_run_id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  user_message_summary TEXT NOT NULL,
  intent TEXT NOT NULL,
  status TEXT NOT NULL,
  policy_decision TEXT NOT NULL,
  target_key TEXT,
  created_at TEXT NOT NULL,
  completed_at TEXT
);
