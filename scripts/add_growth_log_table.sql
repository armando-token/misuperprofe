-- Tabla para registrar growth prompts y nudges
CREATE TABLE IF NOT EXISTS growth_log (
    id SERIAL PRIMARY KEY,
    user_id_hash VARCHAR(64) NOT NULL,
    prompt_type VARCHAR(32) NOT NULL, -- PUSH_OPT_IN, PHONE_ADD, CONTACTS, etc.
    shown_at TIMESTAMPTZ DEFAULT now(),
    action VARCHAR(16), -- ACCEPT, DECLINE, IGNORE
    cooldown_until TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_growth_log_user ON growth_log(user_id_hash);
CREATE INDEX IF NOT EXISTS idx_growth_log_type ON growth_log(prompt_type); 