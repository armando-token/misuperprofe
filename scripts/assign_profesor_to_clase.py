import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Asegurarse de que el PYTHONPATH esté configurado para que la app pueda ser importada
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings
from app.models.associations import profesor_grupo_clase_association

PROFESOR_ID_TO_ASSIGN = 4
GRUPO_CLASE_ID_TO_ASSIGN = 4

async def assign_profesor():
    if not settings.DATABASE_URL or not settings.DATABASE_URL.startswith("postgresql+asyncpg"):
        print(f"Error: DATABASE_URL no está configurada correctamente para asyncpg. Valor actual: {settings.DATABASE_URL}")
        return

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionFactory() as session:
        async with session.begin(): # Inicia una transacción
            try:
                # Comprobar si la asociación ya existe para evitar errores de duplicados
                stmt_check = text(f"""
                    SELECT 1 FROM profesor_grupo_clase_association
                    WHERE profesor_id = :p_id AND grupo_clase_id = :gc_id
                """)
                result_check = await session.execute(stmt_check, {"p_id": PROFESOR_ID_TO_ASSIGN, "gc_id": GRUPO_CLASE_ID_TO_ASSIGN})
                exists = result_check.scalar_one_or_none()

                if exists:
                    print(f"La asignación del profesor ID {PROFESOR_ID_TO_ASSIGN} a la clase ID {GRUPO_CLASE_ID_TO_ASSIGN} ya existe.")
                else:
                    # Usar el objeto Table directamente para la inserción
                    stmt_insert = profesor_grupo_clase_association.insert().values(
                        profesor_id=PROFESOR_ID_TO_ASSIGN,
                        grupo_clase_id=GRUPO_CLASE_ID_TO_ASSIGN
                    )
                    await session.execute(stmt_insert)
                    # El commit es manejado por session.begin() al salir del bloque sin errores.
                    print(f"Profesor ID {PROFESOR_ID_TO_ASSIGN} asignado a GrupoClase ID {GRUPO_CLASE_ID_TO_ASSIGN} exitosamente.")
            except Exception as e:
                # El rollback es manejado por session.begin() si ocurre una excepción.
                print(f"Error al asignar profesor a clase: {e}")
                # Podrías querer re-lanzar la excepción si necesitas que el script falle con un código de error
                # raise

if __name__ == "__main__":
    print(f"Iniciando script para asignar profesor ID {PROFESOR_ID_TO_ASSIGN} a clase ID {GRUPO_CLASE_ID_TO_ASSIGN}...")
    asyncio.run(assign_profesor())
    print("Script finalizado.") 