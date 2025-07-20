import os
from sqlalchemy import create_engine, text

# Configuración desde variables de entorno Docker Compose
DB_USER = os.getenv('POSTGRES_USER', 'ntid_user')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'change_me_in_production')
DB_HOST = os.getenv('POSTGRES_HOST', 'db')
DB_NAME = os.getenv('POSTGRES_DB', 'ntid')

DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}'
engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    # Buscar registros problemáticos
    result = conn.execute(text("""
        SELECT user_id_hash, item_id, difficulty FROM spaced_repetition
        WHERE difficulty::text = '0.0' OR difficulty::text = '0';
    """))
    rows = result.fetchall()
    print(f"Registros a limpiar: {len(rows)}")
    for row in rows:
        print(f"Corrigiendo: user_id_hash={row.user_id_hash}, item_id={row.item_id}, difficulty={row.difficulty}")
    # Actualizar los valores numéricos a 'normal'
    conn.execute(text("""
        UPDATE spaced_repetition SET difficulty = 'normal'
        WHERE difficulty::text = '0.0' OR difficulty::text = '0';
    """))
    print("Limpieza completada. Todos los valores numéricos de 'difficulty' han sido corregidos a 'normal'.") 