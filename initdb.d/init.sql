CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- USERS
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    chatbot_id BIGINT UNIQUE NOT NULL,
    litefarm_user_id UUID NOT NULL,
    deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- TOKENS
CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    chatbot_id BIGINT NOT NULL REFERENCES users(chatbot_id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_tokens_chatbot_id ON tokens (chatbot_id);
CREATE INDEX idx_tokens_created_at ON tokens (created_at);
CREATE INDEX idx_tokens_expires_at ON tokens (expires_at);

-- FARMS
CREATE TABLE farms (
    id SERIAL PRIMARY KEY,
    litefarm_farm_id UUID NOT NULL UNIQUE,
    deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- JOIN TABLE: USER ↔ FARM (Many-to-Many)
CREATE TABLE user_farms (
    user_chatbot_id BIGINT NOT NULL REFERENCES users(chatbot_id) ON DELETE CASCADE,
    litefarm_farm_id UUID NOT NULL REFERENCES farms(litefarm_farm_id) ON DELETE CASCADE,
    PRIMARY KEY (user_chatbot_id, litefarm_farm_id)
);