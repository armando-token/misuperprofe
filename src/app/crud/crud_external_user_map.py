from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
import uuid

from app.models.external_user_map import ExternalUserMap
from app.models.role_enums import MisuperprofeRole
from app.crud.crud_user import create_user_progress
# Asumiremos que tenemos un esquema Pydantic para la creación, ej. ExternalUserMapCreate
# from app.schemas.external_user_map_schemas import ExternalUserMapCreate # Lo crearemos después si es necesario

async def get_external_user_map_entry_by_external_id(
    db: AsyncSession, *, external_user_identifier: str
) -> Optional[ExternalUserMap]:
    result = await db.execute(
        select(ExternalUserMap).filter(ExternalUserMap.external_user_identifier == external_user_identifier)
    )
    return result.scalars().first()

async def get_external_user_map_entry_by_internal_id(
    db: AsyncSession, *, internal_user_id_hash: str
) -> Optional[ExternalUserMap]:
    result = await db.execute(
        select(ExternalUserMap).filter(ExternalUserMap.internal_user_id_hash == internal_user_id_hash)
    )
    return result.scalars().first()

async def create_external_user_map_entry_direct(
    db: AsyncSession, 
    *, 
    external_user_identifier: str, 
    assigned_role: MisuperprofeRole,
    internal_user_id_hash: str
) -> ExternalUserMap:
    """Crea una entrada directamente. Usado internamente por get_or_create."""
    db_obj = ExternalUserMap(
        external_user_identifier=external_user_identifier,
        assigned_misuperprofe_role=assigned_role,
        internal_user_id_hash=internal_user_id_hash
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_or_create_external_user_map_entry(
    db: AsyncSession,
    *, 
    external_user_identifier: str,
    default_role: MisuperprofeRole = MisuperprofeRole.ALUMNO
) -> ExternalUserMap:
    """
    Obtiene una entrada ExternalUserMap por external_user_identifier.
    Si no existe, crea un nuevo UserProgress y luego la entrada ExternalUserMap.
    """
    entry = await get_external_user_map_entry_by_external_id(db, external_user_identifier=external_user_identifier)
    if entry:
        return entry

    # No existe, crear UserProgress primero para obtener/asignar un internal_user_id_hash
    new_internal_user_id_hash = str(uuid.uuid4())
    # La función create_user_progress ya maneja la creación en la tabla UserProgress
    await create_user_progress(db, user_id_hash=new_internal_user_id_hash)
    
    # Ahora crear la entrada ExternalUserMap con el hash vinculado
    new_entry = await create_external_user_map_entry_direct(
        db,
        external_user_identifier=external_user_identifier,
        assigned_role=default_role, # El rol se refinará en Tarea 0.3
        internal_user_id_hash=new_internal_user_id_hash
    )
    return new_entry

async def update_external_user_map_entry(
    db: AsyncSession, 
    *, 
    db_obj: ExternalUserMap, 
    external_user_identifier: Optional[str] = None,
    assigned_role: Optional[MisuperprofeRole] = None,
    internal_user_id_hash: Optional[str] = None
) -> ExternalUserMap:
    update_data = {}
    if external_user_identifier is not None:
        db_obj.external_user_identifier = external_user_identifier
    if assigned_role is not None:
        db_obj.assigned_misuperprofe_role = assigned_role
    if internal_user_id_hash is not None:
        # Asegurarse que si se actualiza, se mantenga la unicidad (o manejar error)
        db_obj.internal_user_id_hash = internal_user_id_hash
    
    db.add(db_obj) # SQLAlchemy maneja el estado del objeto
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

# La función create_external_user_map_entry original fue renombrada a create_external_user_map_entry_direct
# para diferenciarla de la lógica get_or_create.

# Podríamos añadir una función de "get_or_create" o más específicas según se necesiten. 