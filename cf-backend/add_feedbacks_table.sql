CREATE TABLE IF NOT EXISTS feedbacks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unread',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS feedbacks_user_idx ON feedbacks (user_id, created_at);
CREATE INDEX IF NOT EXISTS feedbacks_status_idx ON feedbacks (status);
