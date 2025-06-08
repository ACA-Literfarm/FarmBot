CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- USERS (LiteFarm users who can chat from multiple Telegram accounts)
CREATE TABLE users (
    litefarm_user_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- CHAT_SESSIONS (one LiteFarm user can have multiple Telegram conversations)
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    telegram_chat_id BIGINT NOT NULL UNIQUE, -- Each Telegram chat is unique
    litefarm_user_id UUID REFERENCES users(litefarm_user_id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- TOKENS (each token is valid for a specific chat session, with expiration)
CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    chat_session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for performance
CREATE INDEX idx_chat_sessions_telegram_chat_id ON chat_sessions (telegram_chat_id);
CREATE INDEX idx_chat_sessions_litefarm_user_id ON chat_sessions (litefarm_user_id);
CREATE INDEX idx_tokens_chat_session_id ON tokens (chat_session_id);
CREATE INDEX idx_tokens_expires_at ON tokens (expires_at);
CREATE INDEX idx_tokens_token ON tokens (token); -- For token lookup
