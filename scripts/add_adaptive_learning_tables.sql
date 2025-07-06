-- Tablas para sistema Duolingo-Style Adaptive Learning

-- Tabla de sesiones de lección
CREATE TABLE IF NOT EXISTS lesson_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id_hash VARCHAR(64) NOT NULL,
    course VARCHAR(50) NOT NULL,
    topic VARCHAR(200),
    chapter_id INTEGER,
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ,
    xp INTEGER DEFAULT 0,
    accuracy NUMERIC(4,3),
    items_completed INTEGER DEFAULT 0,
    difficulty_level NUMERIC
);
CREATE INDEX IF NOT EXISTS idx_lesson_sessions_user ON lesson_sessions(user_id_hash);
CREATE INDEX IF NOT EXISTS idx_lesson_sessions_course ON lesson_sessions(course);
CREATE INDEX IF NOT EXISTS idx_lesson_sessions_user_course ON lesson_sessions(user_id_hash, course);

-- Tabla de progreso acumulado por usuario y curso
CREATE TABLE IF NOT EXISTS user_progress (
    user_id_hash VARCHAR(64) NOT NULL,
    course VARCHAR(50) NOT NULL,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    total_xp INTEGER DEFAULT 0,
    last_active TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id_hash, course)
);
CREATE INDEX IF NOT EXISTS idx_user_progress_user_course ON user_progress(user_id_hash, course);

-- Tabla de streaks globales
CREATE TABLE IF NOT EXISTS streaks (
    user_id_hash VARCHAR(64) PRIMARY KEY,
    current_days INTEGER DEFAULT 0,
    longest_days INTEGER DEFAULT 0,
    last_active TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_streaks_user_active ON streaks(user_id_hash, last_active);

-- Tabla de errores por sesión (nombre unificado)
CREATE TABLE IF NOT EXISTS errors (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES lesson_sessions(id),
    item_id VARCHAR(64) NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_errors_session ON errors(session_id);
CREATE INDEX IF NOT EXISTS idx_errors_session_resolved ON errors(session_id, resolved);

-- Tabla de unidades de progreso (mapa tipo snake path)
CREATE TABLE IF NOT EXISTS progress_units (
    user_id_hash VARCHAR(64) NOT NULL,
    unit_id INTEGER NOT NULL REFERENCES capitulos(id),
    state VARCHAR(16) DEFAULT 'LOCKED', -- LOCKED, ACTIVE, DONE
    stars INTEGER DEFAULT 0,
    PRIMARY KEY (user_id_hash, unit_id)
);

-- Tabla para spaced repetition y dificultad adaptativa
CREATE TABLE IF NOT EXISTS spaced_repetition (
    user_id_hash VARCHAR(64) NOT NULL,
    item_id INTEGER NOT NULL REFERENCES capitulos(id),
    last_seen TIMESTAMPTZ DEFAULT now(),
    times_seen INTEGER DEFAULT 1,
    times_correct INTEGER DEFAULT 0,
    times_incorrect INTEGER DEFAULT 0,
    next_due TIMESTAMPTZ DEFAULT now(),
    difficulty VARCHAR(16) DEFAULT 'normal',
    PRIMARY KEY (user_id_hash, item_id)
);
CREATE INDEX IF NOT EXISTS idx_spaced_repetition_user ON spaced_repetition(user_id_hash);
CREATE INDEX IF NOT EXISTS idx_spaced_repetition_item ON spaced_repetition(item_id);

-- Tabla de logros desbloqueados
CREATE TABLE IF NOT EXISTS achievements_log (
    id SERIAL PRIMARY KEY,
    user_id_hash VARCHAR(64) NOT NULL,
    achievement_type VARCHAR(64) NOT NULL,
    unlocked_at TIMESTAMPTZ DEFAULT now(),
    details VARCHAR(256)
);
CREATE INDEX IF NOT EXISTS idx_achievements_log_user ON achievements_log(user_id_hash); 