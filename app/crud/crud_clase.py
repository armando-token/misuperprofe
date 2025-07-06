import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload

from app.models.clase import GrupoClase
from app.models.profesor import Profesor
from app.models.curso import Curso
from app.models.associations import GrupoClaseAlumnoAssociation, profesor_grupo_clase_association
from app.schemas.clase_schemas import GrupoClaseCreate

def generar_codigo_clase_unico(length: int = 8) -> str:
    """Genera un código de clase único y corto."""
    # Se puede mejorar para asegurar unicidad consultando la BBDD, pero para empezar es suficiente.
    return str(uuid.uuid4().hex[:length].upper())

async def create_clase(db: AsyncSession, *, clase_in: GrupoClaseCreate, profesor_id: int) -> GrupoClase:
    """Crea una nueva clase, la asocia con el profesor creador y los cursos especificados."""
    db_profesor = await db.get(Profesor, profesor_id)
    if not db_profesor:
        # Esto no debería suceder si el profesor_id viene de un token válido
        return None 

    codigo_clase = generar_codigo_clase_unico()
    # Podríamos añadir un bucle para asegurar que el código es realmente único en la BD si hay colisión

    db_clase = GrupoClase(
        nombre_clase=clase_in.nombre_clase,
        descripcion=clase_in.descripcion,
        codigo_clase=codigo_clase
    )
    db_clase.profesores.append(db_profesor) # Asociar el profesor a la clase

    # Asociar cursos si se proporcionan IDs
    if clase_in.curso_ids:
        cursos_a_asociar = await db.execute(
            select(Curso).filter(Curso.id.in_(clase_in.curso_ids))
        )
        for curso_obj in cursos_a_asociar.scalars().all():
            db_clase.cursos.append(curso_obj)

    db.add(db_clase)
    await db.commit()
    await db.refresh(db_clase)
    # Refrescar también las relaciones para que estén disponibles inmediatamente
    await db.refresh(db_clase, attribute_names=["profesores", "cursos"])
    return db_clase

async def get_clases_by_profesor(db: AsyncSession, *, profesor_id: int, skip: int = 0, limit: int = 100) -> list[GrupoClase]:
    """Obtiene las clases asociadas a un profesor específico, incluyendo sus cursos."""
    result = await db.execute(
        select(GrupoClase)
        .join(profesor_grupo_clase_association)
        .filter(profesor_grupo_clase_association.c.profesor_id == profesor_id)
        .options(selectinload(GrupoClase.cursos)) # Eager load cursos
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())

async def get_clase_by_id(db: AsyncSession, *, clase_id: int) -> GrupoClase | None:
    """Obtiene una clase por su ID, con profesores, asociaciones de alumnos y cursos cargados."""
    result = await db.execute(
        select(GrupoClase)
        .where(GrupoClase.id == clase_id)
        .options(
            selectinload(GrupoClase.profesores), 
            selectinload(GrupoClase.alumnos_association),
            selectinload(GrupoClase.cursos) # Eager load cursos
        )
    )
    return result.scalars().first()

async def get_clase_by_codigo(db: AsyncSession, *, codigo_clase: str) -> GrupoClase | None:
    """Obtiene una clase por su código."""
    result = await db.execute(
        select(GrupoClase).filter(GrupoClase.codigo_clase == codigo_clase)
    )
    return result.scalars().first()

async def add_alumno_a_clase(db: AsyncSession, *, clase_id: int, user_id_hash: str) -> GrupoClaseAlumnoAssociation | None:
    """Añade un alumno a una clase. Retorna la asociación o None si la clase no existe."""
    print(f"[DEBUG] crud_clase.add_alumno_a_clase: Intentando añadir alumno {user_id_hash} a clase ID {clase_id}")
    try:
        # Verificar si la clase existe
        print(f"[DEBUG] crud_clase.add_alumno_a_clase: Verificando existencia de clase ID {clase_id}")
        clase = await db.get(GrupoClase, clase_id)
        if not clase:
            print(f"[DEBUG] crud_clase.add_alumno_a_clase: Clase ID {clase_id} no encontrada.")
            return None
        print(f"[DEBUG] crud_clase.add_alumno_a_clase: Clase ID {clase_id} encontrada.")

        # Verificar si el alumno ya está en la clase (esta lógica ya está en el endpoint, pero una doble verificación aquí es segura)
        print(f"[DEBUG] crud_clase.add_alumno_a_clase: Verificando si alumno {user_id_hash} ya tiene asociación con clase ID {clase_id}")
        existing_association_stmt = select(GrupoClaseAlumnoAssociation).filter_by(grupo_clase_id=clase_id, user_id_hash=user_id_hash)
        existing_association_result = await db.execute(existing_association_stmt)
        existing_association = existing_association_result.scalars().first()
        
        if existing_association:
            print(f"[DEBUG] crud_clase.add_alumno_a_clase: Alumno {user_id_hash} ya está asociado. Retornando asociación existente.")
            return existing_association
        print(f"[DEBUG] crud_clase.add_alumno_a_clase: Alumno {user_id_hash} no está asociado aún. Creando nueva asociación.")

        db_association = GrupoClaseAlumnoAssociation(
            grupo_clase_id=clase_id,
            user_id_hash=user_id_hash
            # fecha_inscripcion se establece por defecto en el modelo/DB
        )
        print(f"[DEBUG] crud_clase.add_alumno_a_clase: Objeto GrupoClaseAlumnoAssociation creado en memoria.")
        db.add(db_association)
        print(f"[DEBUG] crud_clase.add_alumno_a_clase: Asociación añadida a la sesión de DB.")
        await db.commit()
        print(f"[DEBUG] crud_clase.add_alumno_a_clase: DB commit realizado.")
        await db.refresh(db_association)
        print(f"[DEBUG] crud_clase.add_alumno_a_clase: DB refresh realizado sobre la asociación.")
        return db_association
    except Exception as e:
        print(f"[ERROR] crud_clase.add_alumno_a_clase: Excepción durante la adición de alumno: {e}")
        # import traceback
        # print(traceback.format_exc())
        await db.rollback() # Asegurar rollback en caso de error en el CRUD
        print(f"[DEBUG] crud_clase.add_alumno_a_clase: DB rollback realizado debido a excepción.")
        return None # O podríamos relanzar el error para que el endpoint lo maneje

async def get_alumnos_in_clase(db: AsyncSession, *, clase_id: int) -> list[GrupoClaseAlumnoAssociation]:
    """Obtiene las asociaciones de alumnos para una clase específica."""
    result = await db.execute(
        select(GrupoClaseAlumnoAssociation)
        .filter(GrupoClaseAlumnoAssociation.grupo_clase_id == clase_id)
        # Aquí podríamos querer cargar info del alumno si tuviéramos un modelo Alumno
        # .options(selectinload(GrupoClaseAlumnoAssociation.alumno_user_progress)) # Ejemplo
    )
    return list(result.scalars().all())

async def is_alumno_in_clase(db: AsyncSession, *, clase_id: int, user_id_hash: str) -> bool:
    """Verifica si un alumno (user_id_hash) está inscrito en una clase (clase_id)."""
    existing_association_stmt = (
        select(GrupoClaseAlumnoAssociation)
        .filter_by(grupo_clase_id=clase_id, user_id_hash=user_id_hash)
    )
    existing_association_result = await db.execute(existing_association_stmt)
    existing_association = existing_association_result.scalars().first()
    return existing_association is not None 