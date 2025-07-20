from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.adaptive import UserProgress # UserProgress usa user_id_hash como PK
import uuid # Para generar user_id_hash si no se provee o como ejemplo
from typing import List # Importar List

async def get_user_by_hash(db: AsyncSession, *, user_id_hash: str) -> UserProgress | None:
    """
    Obtiene un registro de UserProgress por user_id_hash.
    Esto sirve para verificar la existencia de un usuario/alumno.
    NOTA: Dado que UserProgress tiene una clave primaria compuesta (user_id_hash, course),
    esta función devolverá solo UNO de los posibles registros si el usuario está en múltiples cursos.
    Considerar get_all_user_progress_by_hash para obtener todos los registros.
    """
    result = await db.execute(
        select(UserProgress).filter(UserProgress.user_id_hash == user_id_hash)
    )
    return result.scalars().first()

async def get_all_user_progress_by_hash(db: AsyncSession, *, user_id_hash: str) -> List[UserProgress]:
    """
    Obtiene TODOS los registros de UserProgress para un user_id_hash dado.
    Útil porque UserProgress tiene una clave primaria (user_id_hash, course).
    """
    result = await db.execute(
        select(UserProgress).filter(UserProgress.user_id_hash == user_id_hash)
    )
    return result.scalars().all()

async def create_user_progress(db: AsyncSession, *, user_id_hash: str, course: str) -> UserProgress: # Se añade 'course' como requerido
    """
    Crea un nuevo registro de UserProgress con el user_id_hash y course proporcionados.
    Los demás campos de UserProgress tomarán sus valores por defecto o serán None.
    """
    # Aquí podríamos añadir lógica para asegurar que el user_id_hash es único si la BD no lo hace,
    # pero dado que es PK, la BD debería manejarlo.
    # Si user_id_hash no se generara externamente, aquí sería un buen lugar:
    # if not user_id_hash:
    #     user_id_hash = str(uuid.uuid4()) # Ejemplo de generación
        
    new_user_progress = UserProgress(user_id_hash=user_id_hash, course=course) # Se añade 'course'
    # Aquí se podrían inicializar otros campos de UserProgress si fuera necesario,
    # por ejemplo: new_user_progress.total_xp = 0, etc.
    
    db.add(new_user_progress)
    await db.commit()
    await db.refresh(new_user_progress)
    return new_user_progress 