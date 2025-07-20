from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid # Importar uuid para generar passwords aleatorias
from typing import Optional # Para placeholders opcionales

from app.models.profesor import Profesor
from app.schemas.profesor_schemas import ProfesorCreate
from app.core.security import get_password_hash

async def get_profesor_by_email(db: AsyncSession, *, email: str) -> Profesor | None:
    """Obtiene un profesor por su email."""
    result = await db.execute(select(Profesor).filter(Profesor.email == email))
    return result.scalars().first()

async def create_profesor(db: AsyncSession, *, profesor_in: ProfesorCreate) -> Profesor:
    """Crea un nuevo profesor."""
    hashed_password = get_password_hash(profesor_in.password)
    db_profesor = Profesor(
        email=profesor_in.email,
        hashed_password=hashed_password,
        nombre=profesor_in.nombre,
        apellido=profesor_in.apellido,
        is_active=True  # Por defecto, los profesores se crean activos
    )
    db.add(db_profesor)
    await db.commit()
    await db.refresh(db_profesor)
    return db_profesor

async def get_or_create_profesor_by_email(
    db: AsyncSession, 
    *, 
    email: str, 
    nombre_placeholder: Optional[str] = None, 
    apellido_placeholder: Optional[str] = None
) -> Profesor:
    """
    Obtiene un profesor por su email. Si no existe, lo crea con datos mínimos
    y una contraseña aleatoria (no utilizable para login directo).
    """
    profesor = await get_profesor_by_email(db, email=email)
    if profesor:
        return profesor
    
    # Generar una contraseña aleatoria y fuerte que no se usará para login directo
    # El acceso será vía OAuth Team y la vinculación por email.
    random_password = str(uuid.uuid4())
    
    profesor_create_data = ProfesorCreate(
        email=email,
        password=random_password,
        nombre=nombre_placeholder, # Puede ser None si el esquema lo permite y el modelo también
        apellido=apellido_placeholder # Puede ser None
    )
    
    new_profesor = await create_profesor(db, profesor_in=profesor_create_data)
    return new_profesor

# Podríamos añadir más funciones CRUD aquí más adelante (get_by_id, update, delete) 