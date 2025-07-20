import os
import asyncio
import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL_ASYNCPG")

CREATE_ATTEMPTS_TABLE = """
CREATE TABLE IF NOT EXISTS attempts (
    id BIGSERIAL PRIMARY KEY,
    user_id_hash TEXT NOT NULL,
    question_id TEXT,
    answer TEXT,
    is_correct BOOLEAN,
    course TEXT,
    topic TEXT,
    ts TIMESTAMPTZ DEFAULT NOW(),
    fecha TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_attempts_user_course ON attempts(user_id_hash, course);
CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts(user_id_hash);
CREATE INDEX IF NOT EXISTS idx_attempts_course ON attempts(course);
"""

async def main():
    print("[init_attempts_table] Conectando a la base de datos...")
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(CREATE_ATTEMPTS_TABLE)
    await conn.close()
    print("[init_attempts_table] Tabla 'attempts' verificada/creada correctamente.")

if __name__ == "__main__":
    asyncio.run(main()) 