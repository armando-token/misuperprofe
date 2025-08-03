"""sync_misuperproferole_enum

Revision ID: e084d62e3314
Revises: 0ee49cca1552
Create Date: 2025-07-28 19:42:07.411132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e084d62e3314'
down_revision: Union[str, None] = '0ee49cca1552'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Definición de los ENUMs
old_enum = sa.Enum('ALUMNO', 'PROFESOR', name='misuperproferole')
new_enum = sa.Enum('STUDENT', 'PROFESSOR', 'ADMIN', name='misuperproferole')

def upgrade() -> None:
    # 1. Cambiar a VARCHAR para eliminar la restricción del ENUM
    op.alter_column('external_user_map', 'assigned_misuperprofe_role',
               type_=sa.String(length=50),
               existing_type=old_enum,
               postgresql_using='assigned_misuperprofe_role::character varying(50)')

    # 2. Actualizar los datos de texto
    op.execute("""
        UPDATE external_user_map
        SET assigned_misuperprofe_role = CASE
            WHEN assigned_misuperprofe_role = 'ALUMNO' THEN 'STUDENT'
            WHEN assigned_misuperprofe_role = 'PROFESOR' THEN 'PROFESSOR'
            ELSE assigned_misuperprofe_role
        END
        WHERE assigned_misuperprofe_role IN ('ALUMNO', 'PROFESOR');
    """)

    # 3. Eliminar el ENUM antiguo
    old_enum.drop(op.get_bind(), checkfirst=False)

    # 4. Crear el ENUM nuevo
    new_enum.create(op.get_bind(), checkfirst=False)

    # 5. Volver a cambiar la columna al nuevo tipo ENUM
    op.alter_column('external_user_map', 'assigned_misuperprofe_role',
               type_=new_enum,
               existing_type=sa.String(length=50),
               postgresql_using='assigned_misuperprofe_role::misuperproferole')


def downgrade() -> None:
    # 1. Cambiar a VARCHAR para eliminar la restricción del ENUM
    op.alter_column('external_user_map', 'assigned_misuperprofe_role',
               type_=sa.String(length=50),
               existing_type=new_enum,
               postgresql_using='assigned_misuperprofe_role::character varying(50)')

    # 2. Actualizar los datos de texto a los valores antiguos
    op.execute("""
        UPDATE external_user_map
        SET assigned_misuperprofe_role = CASE
            WHEN assigned_misuperprofe_role = 'STUDENT' THEN 'ALUMNO'
            WHEN assigned_misuperprofe_role = 'PROFESSOR' THEN 'PROFESOR'
            ELSE assigned_misuperprofe_role
        END
        WHERE assigned_misuperprofe_role IN ('STUDENT', 'PROFESSOR');
    """)

    # 3. Eliminar el ENUM nuevo
    new_enum.drop(op.get_bind(), checkfirst=False)

    # 4. Crear el ENUM antiguo
    old_enum.create(op.get_bind(), checkfirst=False)

    # 5. Volver a cambiar la columna al tipo ENUM antiguo
    op.alter_column('external_user_map', 'assigned_misuperprofe_role',
               type_=old_enum,
               existing_type=sa.String(length=50),
               postgresql_using='assigned_misuperprofe_role::misuperproferole')
