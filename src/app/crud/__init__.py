from .crud_profesor import get_profesor_by_email, create_profesor
from .crud_clase import (
    create_clase,
    get_clases_by_profesor,
    get_clase_by_id,
    get_clase_by_codigo,
    add_alumno_a_clase,
    get_alumnos_in_clase,
    is_alumno_in_clase
)
from .crud_user import get_user_by_hash
from .crud_progreso_alumno import get_progreso_alumno_por_cursos
from .crud_curso import get_all_cursos
from .crud_curso import get_curso_by_nombre
from .crud_capitulo import get_capitulos_by_curso_id
from .crud_capitulo import get_random_practice_chapter_for_course_topic

# Puedes añadir más importaciones específicas si prefieres no usar el nombre del módulo completo
# por ejemplo: from .crud_associations import is_alumno_in_clase 